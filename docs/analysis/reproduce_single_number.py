"""Reproducer for every figure in `docs/design/amendments-2026-08-04.md` (§D1-§D7).

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_single_number.py

Deterministic: no sampling, no seeds, no fitting. Report week 2026-07-28 where a single
week is quoted; full store history otherwise.

The through-line is one question: **what single number should this package deliver, and
what does it have to be published with?** The sections split into three groups.

  §D1  the raw `T` ranking is substantially structural, so it answers a different question
       than a reader hears
  §D2  `T_sell / T_buy` IS `Q_sell / Q_buy`, so a side-ratio index cannot see joint
       congestion
  §D3  "at-risk vs not-at-risk" is degenerate, and so is the Legacy pair it is modelled on
  §D4  `Phi` is NOT inert in `D`, which refutes the suspicion that prompted the test
  §D5  `Phi`'s effect on `D_pct` is not monotone
  §D6  Legacy and TFF share exactly two quantities and nothing else
  §D7  sterling: the levered book and Legacy non-commercial point opposite ways
  §D8  the offside term: built, and beside `D` rather than inside it

Blocks are named after their section: §D1 is `d1_t_ranking_is_structural`, and so on. The
panels are expensive to build (every symbol's price history is read for the volume join),
so they are built once in `main` and passed down rather than rebuilt per block.
"""
import warnings

import pandas as pd

from crowdmon.core.aggregate import rolling_percentile
from crowdmon.futures import (
    ContractMaster,
    add_composite,
    add_extremity,
    add_notional,
    add_risk_units,
    add_volume,
    contributions,
    fragility_frame,
    from_current_store,
    market_fragility,
    rank_markets,
)

#: The two reports with configured fragility weights. Legacy is deliberately absent, and
#: §D6 is partly about why.
REPORTS = ("disaggregated", "tff")

#: Codes quoted by name in the amendments file.
STERLING, CAD, CORN, DJIA = "096742", "090741", "002602", "124603"

#: The trailing window every percentile in this file uses, matching `core.aggregate`.
#: Stated once so a reader can see that §D1's "own history" and §D4's are the same window.
WINDOW_YEARS = 3


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


# ── shared panels ───────────────────────────────────────────────────────────
def _priced(report_type: str) -> pd.DataFrame:
    """`fragility_frame` + volume + the pressure ratios, full history, one report."""
    panel = ContractMaster.load().annotate(from_current_store(report_type=report_type))
    spec = panel[["market_code", "symbol"]].drop_duplicates("market_code")
    frag = add_volume(fragility_frame(panel).merge(spec, on="market_code", how="left"))
    return rank_markets(frag, volume=frag["adv"],
                        stress_volume=frag["adv_stress"]).assign(report=report_type)


def _scored(report_type: str) -> pd.DataFrame:
    """The full composite, which needs the per-category extremity frame beside it."""
    panel = ContractMaster.load().annotate(from_current_store(report_type=report_type))
    per_cat = add_volume(add_extremity(add_risk_units(add_notional(panel))))
    vol = (per_cat.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
           .max().reset_index())
    per_market = market_fragility(panel).merge(
        vol, on=["report_date", "market_code"], how="left")
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    return add_composite(ranked, per_cat).assign(report=report_type)


def _one_instrument(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse to one row per (symbol, week). Lumber's two codes overlap for 7 weeks in
    the priced era (`2026-08-02 §B30`), and a duplicated week would double-count it in
    every correlation below."""
    return (frame.dropna(subset=["dtl_sell", "symbol"])
            .sort_values(["symbol", "report_date", "market_code"])
            .drop_duplicates(["symbol", "report_date"], keep="last"))


# ── §D1 ─────────────────────────────────────────────────────────────────────
def d1_t_ranking_is_structural(priced: pd.DataFrame) -> None:
    rule("D1. How much of the T ranking is each market's standing level?")

    h = _one_instrument(priced)
    week = h["report_date"].max()
    cur = h[h["report_date"] == week].set_index("symbol")
    hist = h.groupby("symbol")["dtl_sell"]

    tab = pd.DataFrame({"report": cur["report"], "T_now": cur["dtl_sell"],
                        "weeks": hist.count(), "T_median": hist.median()}).dropna(
        subset=["T_now"])
    tab["ratio_to_own_median"] = tab["T_now"] / tab["T_median"]
    tab["pct_3y"] = pd.Series({
        s: rolling_percentile(g.set_index("report_date")["dtl_sell"].sort_index()).iloc[-1]
        for s, g in h.groupby("symbol")})
    tab["rank_raw"] = tab["T_now"].rank(ascending=False).astype(int)
    tab["rank_pct"] = tab["pct_3y"].rank(ascending=False).astype(int)

    print(f"week {week.date()}, {len(tab)} symbols")
    print(f"rank corr, T_now vs own long-run median T : "
          f"{tab['T_now'].rank().corr(tab['T_median'].rank()):.4f}")
    print(f"weeks of T history: min {int(tab.weeks.min())}, "
          f"median {tab.weeks.median():.0f}; >= 156 ({WINDOW_YEARS}y): "
          f"{int((tab.weeks >= 156).sum())} of {len(tab)}")
    top_raw = set(tab.nlargest(10, "T_now").index)
    top_pct = set(tab.nlargest(10, "pct_3y").index)
    print(f"top-10 overlap, raw T vs {WINDOW_YEARS}y percentile: "
          f"{len(top_raw & top_pct)} of 10")
    print(f"  raw only: {sorted(top_raw - top_pct)}")
    print(f"  pct only: {sorted(top_pct - top_raw)}")

    print("\n--- the raw top ten that are BELOW their own median ---")
    quiet = tab[(tab.rank_raw <= 10) & (tab.ratio_to_own_median < 1)]
    print(quiet[["T_now", "T_median", "ratio_to_own_median", "pct_3y",
                 "rank_raw", "rank_pct"]].to_string(float_format=lambda x: f"{x:,.3f}"))

    print("\n--- at or above their own 3y p90, and where the raw table puts them ---")
    hot = tab[tab.pct_3y >= 0.90].sort_values("pct_3y", ascending=False)
    print(hot[["T_now", "T_median", "ratio_to_own_median", "pct_3y",
               "rank_raw", "rank_pct"]].to_string(float_format=lambda x: f"{x:,.3f}"))


# ── §D2 ─────────────────────────────────────────────────────────────────────
def d2_the_ratio_is_t_over_t(priced: pd.DataFrame) -> None:
    rule("D2. T_sell / T_buy IS Q_sell / Q_buy: the volume term cancels")

    st = (priced[priced.market_code == STERLING].dropna(subset=["dtl_sell"])
          .set_index("report_date").sort_index())
    st["ratio"] = st.q_sell / st.q_buy
    err = (st.dtl_sell / st.dtl_buy - st.ratio).abs().max()
    print("T_sell = Q_sell / (k*V) and T_buy = Q_buy / (k*V), so their ratio drops V.")
    print(f"checked on {len(st)} sterling weeks: max |T_sell/T_buy - Q_sell/Q_buy| = "
          f"{err:.2e}")
    print("A ratio therefore cannot see BOTH sides becoming congested at once.\n")

    cols = ["q_sell", "q_buy", "adv", "dtl_sell", "dtl_buy", "ratio"]
    pct = pd.DataFrame({c: rolling_percentile(st[c]) for c in cols})
    print(f"--- sterling, {st.index[-1].date()}: level, {WINDOW_YEARS}y percentile, "
          f"and share of the 3y median ---")
    med = st[cols].tail(156).median()
    out = pd.DataFrame({"level": st[cols].iloc[-1],
                        "pct_3y": 100 * pct[cols].iloc[-1],
                        "pct_of_3y_median": 100 * st[cols].iloc[-1] / med})
    print(out.to_string(float_format=lambda x: f"{x:,.2f}"))
    print("\nBoth weighted sides are at records and the SHORT side grew more, so the ratio")
    print("moved AGAINST the long side even as the long side set a record.")


# ── §D3 ─────────────────────────────────────────────────────────────────────
def d3_the_partition_is_degenerate(priced: pd.DataFrame) -> None:
    rule("D3. 'At-risk vs not-at-risk' is one series twice, and so is the Legacy pair")

    from cotdata import vintage_ingest as vi

    panel = ContractMaster.load().annotate(from_current_store(report_type="tff"))
    c = contributions(panel, report_type="tff")
    net = c.pivot_table(index=["market_code", "report_date"], columns="category",
                        values="net", aggfunc="first").fillna(0)
    oi = c.groupby(["market_code", "report_date"]).open_interest.max()

    at_risk = net[["leveraged", "nonreportable", "other_reportable"]].sum(axis=1)
    rest = net[["dealer", "asset_manager"]].sum(axis=1)
    both = at_risk + rest
    print(f"TFF market-weeks: {len(at_risk):,}")
    print(f"max |at_risk + not_at_risk| : {both.abs().max():,.4f}")
    print(f"corr(at_risk, not_at_risk)  : {at_risk.corr(rest):.10f}")
    print("Zero-sum makes ANY two-group partition exactly equal and opposite.\n")

    d = pd.DataFrame({"lev": net["leveraged"] / oi,
                      "dealer_am": rest / oi}).dropna()
    per = d.groupby(level=0).apply(
        lambda g: pd.Series({"corr": g.lev.corr(g.dealer_am), "n": len(g)}),
        include_groups=False)
    per = per[per.n >= 156]
    print(f"dropping the two small categories buys a little independence, {len(per)} "
          f"markets:\n  corr(leveraged, dealer+asset_manager) median "
          f"{per['corr'].median():.4f}  range {per['corr'].min():.4f} to "
          f"{per['corr'].max():.4f}")

    obs = vi.read_observations()
    lg = obs[obs.report_type == "legacy"].copy()
    for col in ("long_contracts", "short_contracts"):
        lg[col] = pd.to_numeric(lg[col], errors="coerce")
    lg["net"] = lg.long_contracts - lg.short_contracts
    ln = lg.pivot_table(index=["market_code", "report_date"], columns="category",
                        values="net", aggfunc="first").dropna()
    legacy = ln.groupby(level=0).apply(
        lambda g: pd.Series({"corr": g.commercial.corr(g.noncommercial), "n": len(g)}),
        include_groups=False)
    legacy = legacy[legacy.n >= 60]
    print(f"\nthe pair this idea is modelled on, {len(legacy)} Legacy markets:")
    print(f"  corr(commercial, noncommercial) median {legacy['corr'].median():.4f}   "
          f"90% below {legacy['corr'].quantile(0.9):.4f}")

    print("\n--- sterling: the two framings on its record week ---")
    st = (priced[priced.market_code == STERLING].dropna(subset=["dtl_sell"])
          .set_index("report_date").sort_index())
    idx = pd.DataFrame({
        "lev_idx": 100 * rolling_percentile(net.loc[STERLING, "leveraged"] / oi.loc[STERLING]),
        "notlev_idx": 100 * rolling_percentile(rest.loc[STERLING] / oi.loc[STERLING]),
        "T_sell_idx": 100 * rolling_percentile(st.dtl_sell),
        "T_buy_idx": 100 * rolling_percentile(st.dtl_buy)}).dropna()
    print(idx.tail(4).to_string(float_format=lambda x: f"{x:,.1f}"))
    print(f"\ncorr(lev_idx, notlev_idx)   : {idx.lev_idx.corr(idx.notlev_idx):.4f}  mirrors")
    print(f"corr(T_sell_idx, T_buy_idx) : "
          f"{idx.T_sell_idx.corr(idx.T_buy_idx):.4f}  not mirrors, and both can be high")


# ── §D4 and §D5 ─────────────────────────────────────────────────────────────
def _with_d2(scored: pd.DataFrame) -> pd.DataFrame:
    """Add `D2 = C x I` beside the shipped `D3 = C x I x Phi`, both percentile-ised."""
    s = scored.sort_values(["report_date", "market_code"]).copy()
    for side, crowd in (("sell", "crowding_long"), ("buy", "crowding_short")):
        s[f"d2_{side}"] = s[crowd] * s[f"illiquidity_{side}"]
    for side in ("sell", "buy"):
        parts = []
        for _, g in s.groupby("market_code", sort=False):
            g = g.sort_values("report_date")
            pct = rolling_percentile(g.set_index("report_date")[f"d2_{side}"])
            parts.append(pd.Series(pct.to_numpy(), index=g.index))
        s[f"d2_{side}_pct"] = pd.concat(parts).reindex(s.index)
    return s


def d4_phi_is_not_inert(scored: pd.DataFrame) -> None:
    rule("D4. Does Phi do any work? (the test was run expecting 'no')")

    s = _with_d2(scored)
    both = s.dropna(subset=["damage_sell_pct", "d2_sell_pct"])
    print(f"market-weeks with both: {len(both):,}   markets: "
          f"{both.market_code.nunique()}\n")
    for side in ("sell", "buy"):
        a, b = both[f"d2_{side}_pct"], both[f"damage_{side}_pct"]
        print(f"  {side}: corr(D2_pct, D3_pct) {a.corr(b):.4f}   "
              f"rank corr {a.rank().corr(b.rank()):.4f}   "
              f"median |diff| {(a - b).abs().median():.4f}   "
              f"90th pct |diff| {(a - b).abs().quantile(.9):.4f}")

    print("\n--- structural or week-to-week noise? ---")
    for col, lab in (("fragility", "pct(Phi)"), ("crowding_long", "C"),
                     ("illiquidity_sell", "I")):
        ac = (s.dropna(subset=[col]).groupby("market_code")[col]
              .apply(lambda x: x.autocorr(1)).median())
        sd = s.groupby("market_code")[col].std().median()
        print(f"  {lab:9s} median lag-1 autocorr {ac:.4f}   within-market sd {sd:.4f}")

    print("\n--- how much does it move the weekly ranking? ---")
    wk = both[both.report_date == both.report_date.max()]
    for side in ("sell", "buy"):
        r2 = set(wk.nlargest(10, f"d2_{side}_pct").market_code)
        r3 = set(wk.nlargest(10, f"damage_{side}_pct").market_code)
        print(f"  {side}: latest-week top-10 overlap {len(r2 & r3)} of 10")
    ov = both.groupby("report_date").apply(
        lambda x: len(set(x.nlargest(5, "d2_sell_pct").market_code)
                      & set(x.nlargest(5, "damage_sell_pct").market_code))
        if len(x) >= 5 else float("nan"), include_groups=False).dropna()
    print(f"  top-5 overlap across all {len(ov)} weeks: mean {ov.mean():.2f} of 5")
    print("\nPhi is NOT inert. What this cannot say is whether its influence is CORRECT:")
    print("there is no outcome to score against, and the section 10 validation is spent.")


def d5_phi_is_not_monotone(scored: pd.DataFrame) -> None:
    rule("D5. Phi's effect on D_pct is not monotone, so it cannot be described in words")

    s = _with_d2(scored)
    wk = s[s.report_date == s.report_date.max()]
    codes = {CORN: "ZC corn", STERLING: "6B sterling", CAD: "6C CAD", DJIA: "YM DJIA"}
    t = wk[wk.market_code.isin(codes)].set_index("market_code")
    cols = ["crowding_long", "illiquidity_sell", "fragility",
            "d2_sell_pct", "damage_sell_pct", "dtl_sell"]
    t = t[[c for c in cols if c in t.columns]]
    t.index = [codes[i] for i in t.index]
    t["phi_effect"] = t["damage_sell_pct"] - t["d2_sell_pct"]
    print(t.to_string(float_format=lambda x: f"{x:,.3f}"))
    print("\nCorn and sterling BOTH have below-median pct(Phi) and it moves them in")
    print("OPPOSITE directions, because the percentile of a product is not monotone in")
    print("each factor's percentile. 'More fragile means more damage' is unwriteable.")
    print(f"\nDJIA is the level trap: D_sell_pct {t.loc['YM DJIA', 'damage_sell_pct']:.3f} "
          f"on T_sell {t.loc['YM DJIA', 'dtl_sell']:.2f} days.")


# ── §D6 ─────────────────────────────────────────────────────────────────────
def d6_legacy_and_tff_share_two_things() -> None:
    rule("D6. Legacy and TFF agree on open interest and non-reportables, and nothing else")

    from cotdata import vintage_ingest as vi

    obs = vi.read_observations()
    obs = obs[obs.report_type.isin(["legacy", "tff"])].copy()
    for c in ("long_contracts", "short_contracts", "spread_contracts", "open_interest"):
        obs[c] = pd.to_numeric(obs[c], errors="coerce")

    wide = obs.pivot_table(index=["market_code", "report_date", "report_type"],
                           columns="category",
                           values=["long_contracts", "short_contracts", "open_interest"],
                           aggfunc="first")
    lg, tf = wide.xs("legacy", level="report_type"), wide.xs("tff", level="report_type")
    idx = lg.index.intersection(tf.index)
    lg, tf = lg.loc[idx], tf.loc[idx]
    L, S, OI = "long_contracts", "short_contracts", "open_interest"
    TFF = ["dealer", "asset_manager", "leveraged", "other_reportable", "nonreportable"]
    LEG = ["commercial", "noncommercial", "nonreportable"]

    print(f"overlapping market-weeks: {len(idx):,}")
    oid = (lg[(OI, "commercial")] - tf[(OI, "dealer")]).abs()
    print(f"  open interest identical    : {(oid < 1e-9).mean():.4%}  max diff {oid.max():,.0f}")
    for c, col in (("long", L), ("short", S)):
        nr = (lg[(col, "nonreportable")] - tf[(col, "nonreportable")]).abs()
        print(f"  nonreportable {c:5s} identical: {(nr < 1e-9).mean():.4%}")
    for c, col in (("long", L), ("short", S)):
        d = (sum(tf[(col, k)].fillna(0) for k in TFF)
             - sum(lg[(col, k)].fillna(0) for k in LEG))
        print(f"  {c:5s} TFF sum == Legacy sum : {(d.abs() < 1e-9).mean():.4%}   "
              f"median {d.median():,.0f}")
    for c, col in (("long", L), ("short", S)):
        d1 = (tf[(col, "dealer")] - lg[(col, "commercial")]).abs()
        buy = sum(tf[(col, k)].fillna(0)
                  for k in ["asset_manager", "leveraged", "other_reportable"])
        d2 = (buy - lg[(col, "noncommercial")]).abs()
        print(f"  {c:5s} dealer == commercial  : {(d1 < 1e-9).mean():7.3%}   "
              f"(AM+LF+OR) == noncomm : {(d2 < 1e-9).mean():7.3%}")

    print("\n--- why: spreading. Worked on Canadian dollar, latest overlapping week ---")
    wk = idx[idx.get_level_values(0) == CAD].max()
    one = obs[(obs.market_code == CAD) & (obs.report_date == wk[1])]
    for rt in ("legacy", "tff"):
        g = one[one.report_type == rt]
        lo, sp = g.long_contracts.sum(), g.spread_contracts.sum()
        oi = g.open_interest.max()
        print(f"  {rt:7s} long {lo:>9,.0f} + spread {sp:>8,.0f} = {lo + sp:>9,.0f}   "
              f"OI {oi:>9,.0f}   residual {oi - (lo + sp):>7,.0f}")
    lgs = one[(one.report_type == "legacy")]
    tfs = one[(one.report_type == "tff")]
    gap = (tfs.long_contracts.sum() - lgs.long_contracts.sum())
    print(f"  gap between the two long totals = {gap:,.0f} = "
          f"-(TFF spreading - Legacy spreading)")

    print("\n--- and the spreading does not map category-for-category either ---")
    # cotdata's `canonicalize_legacy` sets `spread_contracts` to NA on every row, so the
    # Legacy figure below is DERIVED as the identity residual rather than read. Stated
    # rather than silently summed: `.sum()` over an all-null column returns 0, which would
    # print as a real measurement of zero spreading and is not one.
    stored = pd.to_numeric(lgs["spread_contracts"], errors="coerce")
    print(f"  Legacy spreading as STORED           : "
          f"{'all null' if stored.isna().all() else f'{stored.sum():,.0f}'}"
          f"   (canonicalize_legacy drops it)")
    resid = lgs.open_interest.max() - lgs.long_contracts.sum()
    print(f"  Legacy non-commercial spreading      : {resid:,.0f}  DERIVED as the residual")
    buyside = tfs[tfs.category.isin(["asset_manager", "leveraged", "other_reportable"])]
    print(f"  TFF asset_manager+leveraged+other    : "
          f"{buyside.spread_contracts.sum():,.0f}  read directly")
    print("  If 'non-commercial' and the TFF buy side were the same traders these would")
    print("  match. They do not, so the reports put different traders in each bucket.")

    print("\n--- the identity, both reports, all market-weeks ---")
    g = obs.groupby(["report_type", "market_code", "report_date"]).agg(
        lo=("long_contracts", "sum"), sp=("spread_contracts", "sum"),
        oi=("open_interest", "max"))
    g["resid"] = g.oi - (g.lo + g.sp)
    for rt, x in g.groupby(level=0):
        print(f"  {rt:9s} long+spread == OI on {(x.resid.abs() <= 2).mean():7.3%} of "
              f"{len(x):,} market-weeks; median residual {x.resid.median():,.0f}")


# ── §D7 ─────────────────────────────────────────────────────────────────────
def d7_sterling_sign_conflict(priced: pd.DataFrame) -> None:
    rule("D7. Sterling: the levered book and Legacy non-commercial point opposite ways")

    from cotdata import vintage_ingest as vi

    obs = vi.read_observations()
    o = obs[obs.report_type.isin(["legacy", "tff"])
            & (obs.market_code == STERLING)].copy()
    for c in ("long_contracts", "short_contracts", "open_interest"):
        o[c] = pd.to_numeric(o[c], errors="coerce")
    o["net"] = o.long_contracts - o.short_contracts
    n = o.pivot_table(index="report_date", columns="category", values="net",
                      aggfunc="first").sort_index()
    n["oi"] = o.groupby("report_date").open_interest.max()

    print(n[["noncommercial", "leveraged", "asset_manager", "dealer", "oi"]].tail(12)
          .to_string(float_format=lambda x: f"{x:,.0f}"))
    conflict = (n.noncommercial * n.leveraged) < 0
    print(f"\nsign conflict in {int(conflict.sum())} of {len(n)} weeks the store holds "
          f"({conflict.mean():.1%})")
    print(f"last 12 weeks: {int(conflict.tail(12).sum())} of 12")

    print("\n--- the caveat: what actually carries sterling's record T_sell ---")
    panel = ContractMaster.load().annotate(from_current_store(report_type="tff"))
    panel = panel[(panel.market_code == STERLING)
                  & (panel.report_date == panel.report_date.max())]
    c = contributions(panel, report_type="tff")
    longs = c[c.net > 0].sort_values("q_contribution", ascending=False)
    q_sell = longs.q_contribution.sum()
    for r in longs.itertuples():
        print(f"  {r.category:<18} {r.net:>10,.0f} x {r.weight:>4} = "
              f"{r.q_contribution:>10,.1f}   {r.q_contribution / q_sell:6.1%} of Q_sell")
    print(f"  {'Q_sell':<18} {'':>10}   {'':>6} {q_sell:>10,.1f}")
    print("\nHalf the record is the DEALER book at weight 0.4, not the levered long. The")
    print("sign contradiction is unaffected; the supporting T figure needs the caveat.")


# ── §D8 ─────────────────────────────────────────────────────────────────────
def d8_offside_is_beside_not_inside() -> None:
    """§D8: the trigger distance, why it is not a fourth factor, and the identity."""
    import cotdata

    from crowdmon.futures import add_trigger_distance, trigger_prices

    rule("D8. The offside term: built, and kept beside D rather than inside it")

    def build(rt: str) -> pd.DataFrame:
        panel = ContractMaster.load().annotate(from_current_store(report_type=rt))
        per_cat = add_volume(add_extremity(add_risk_units(add_notional(panel))))
        agg = (per_cat.groupby(["report_date", "market_code"])
               .agg(adv=("adv", "max"), adv_stress=("adv_stress", "max"),
                    sigma_daily=("sigma_daily", "max"), symbol=("symbol", "first"))
               .reset_index())
        pm = market_fragility(panel).merge(agg, on=["report_date", "market_code"],
                                           how="left")
        r = rank_markets(pm, volume=pm["adv"], stress_volume=pm["adv_stress"])
        return add_trigger_distance(add_composite(r, per_cat)).assign(report=rt)

    s = pd.concat([build(rt) for rt in REPORTS], ignore_index=True)
    cur = s[(s.report_date == s.report_date.max()) & s.dtl_sell.notna()].copy()
    for c in ("trigger_sell_sigma", "trigger_buy_sigma", "trigger_sell_pct"):
        cur[c] = pd.to_numeric(cur[c], errors="coerce")

    print(f"week {cur.report_date.max().date()}, {len(cur)} markets with a live T")
    print(f"  with a forced-SELL trigger : {int(cur.trigger_sell_sigma.notna().sum())}")
    print(f"  with a forced-BUY trigger  : {int(cur.trigger_buy_sigma.notna().sum())}")
    print(f"  horizons disagree          : "
          f"{int(cur.trigger_horizons_disagree.fillna(False).sum())}")

    print("\n--- the identity: F* = F_{t-k}, so the distance IS the k-day return ---")
    for sym in ("RB", "ZC", "6B"):
        tp = trigger_prices(sym, as_of="2026-07-28").dropna(subset=["flip_price"])
        px = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        px = px[px.index <= "2026-07-28"]
        for _, r in tp.iterrows():
            k = int(r.lookback_days)
            ret = px.iloc[-1] / px.iloc[-1 - k] - 1.0
            print(f"  {sym:>4} k={k:>3}  move_from_spot {r.move_from_spot:+.6f}   "
                  f"-r_k/(1+r_k) {-ret / (1 + ret):+.6f}")
    print("  Exact on every row. So the distance carries no price information beyond")
    print("  trailing momentum; what it adds is WHICH pool is forced at that level.")

    d = cur.dropna(subset=["trigger_sell_sigma", "damage_sell_pct"])
    print(f"\n--- why it is not a fourth multiplicand, {len(d)} markets ---")
    for c in ("damage_sell_pct", "crowding_long", "illiquidity_sell", "fragility"):
        print(f"  corr(trigger_sell_sigma, {c:18s}) = "
              f"{d.trigger_sell_sigma.corr(d[c]):+.4f}   "
              f"rank {d.trigger_sell_sigma.rank().corr(d[c].rank()):+.4f}")
    print("  The -0.481 against C is the point: both are downstream of the same trend, so")
    print("  a fourth factor would compound one signal twice. A.10 is the primary reason.")
    print(f"\n  distance in sigma: median {d.trigger_sell_sigma.median():.1f}  "
          f"p10 {d.trigger_sell_sigma.quantile(.1):.1f}  "
          f"p90 {d.trigger_sell_sigma.quantile(.9):.1f}")

    d = d.copy()
    d["close"] = d.trigger_sell_sigma <= 1.5
    d["severe"] = d.damage_sell_pct >= 0.75
    print("\n--- the quadrant a product would collapse ---")
    print(pd.crosstab(d["close"], d["severe"]).to_string())
    hot = d[d.close & d.severe][["symbol", "market_name", "trigger_sell_sigma",
                                 "trigger_sell_pct", "trigger_sell_k",
                                 "damage_sell_pct", "dtl_sell"]]
    print("\nCLOSE and SEVERE:")
    print(hot.assign(market_name=hot.market_name.str.slice(0, 24)).to_string(
        index=False, float_format=lambda x: f"{x:,.3f}"))
    print("\nDJIA is in that cell on a T_sell of 0.27 days, so §D1's level floor still")
    print("binds: the quadrant ranks, the level gates.")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 40)

    priced = pd.concat([_priced(rt) for rt in REPORTS], ignore_index=True)
    scored = pd.concat([_scored(rt) for rt in REPORTS], ignore_index=True)

    d1_t_ranking_is_structural(priced)
    d2_the_ratio_is_t_over_t(priced)
    d3_the_partition_is_degenerate(priced)
    d4_phi_is_not_inert(scored)
    d5_phi_is_not_monotone(scored)
    d6_legacy_and_tff_share_two_things()
    d7_sterling_sign_conflict(priced)
    d8_offside_is_beside_not_inside()


if __name__ == "__main__":
    main()
