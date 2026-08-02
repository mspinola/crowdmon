"""Reproducer for every figure in docs/analysis/ (governance: no quoted figure without one).

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce.py

Deterministic: no sampling, no seeds, no fitting. The only thing that moves between runs is
the store, so the output is pinned to the report week it was produced against
(2026-07-28, released 2026-07-31) and any later run will differ by exactly the weeks added.

Prints, in order:
  1. the two rankings (§6), unfiltered and under open-interest floors
  2. the category tables and Q/Phi arithmetic for the two selected markets
  3. flow decomposition, latest week and the trailing 12-week Managed Money sequence
  4. breadth-depth over the same 12 weeks
  5. tolerance sensitivity, on both the wide and the liquid panels
  6. the open-interest identity exception rate, by year
  7. what the ranked universe is made of, by venue
  8. the price-series measurements behind amendments A8 and A9 (normalisation)
  9. the volume measurements behind amendment A13, and the real T = Q/(kappa V)
 10. exit COST: the square-root law and Amihud (2026-08-01 A19, A20)
 11. liquidity commonality, and why it cannot reach the composite (2026-08-02 A1, A2)
 12. the trigger guard: sign agreement against distance disagreement (2026-08-02 B9)
 13. vintage coverage, behind §4 of the validation pre-registration (2026-08-02 B10)
 14. which configured constants can move D, behind §5 (2026-08-02 B11)
 15. the A.8 cascade staircase (2026-08-02 B13-B15)
 16. roll-date coverage, and the empty-index trap (2026-08-02 B16)
 17. the coverage ladder: which markets score nothing, and where (2026-08-02 B17)
 20. the macro-book PCA and what PC1 actually is, per report type (B21)
  B28. the cocoa template measured as a joint shape rather than two margins
  B29. the two flow decompositions, and the oats rationale that does not hold
  B30. whether the lumber code split is what makes lumber unscoreable

The leading ordinals above are the order the blocks were added and have drifted: 17 and 18
each appear twice and there is no 19. Not renumbered here, because these numbers are quoted
by the analysis documents. New blocks are labelled by their amendment ID instead.
"""
import numpy as np
import pandas as pd

from crowdmon.futures import (
    contributions,
    decompose,
    decompose_breadth,
    fragility_frame,
    from_current_store,
    from_vintage,
    latest,
    oi_identity_summary,
    report,
    tolerance_sensitivity,
)

BREADTH_COLUMNS = ["report_date", "position", "traders", "avg_position", "d_position",
                   "d_traders", "d_avg", "depth_term", "breadth_term", "joint_term",
                   "dominant_term", "quadrant"]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)

    cross = latest()
    frag = fragility_frame(cross)
    week = cross["report_date"].max().date()

    rule(f"1. RANKINGS — Disaggregated, report week {week}, "
         f"{cross['market_code'].nunique()} markets")
    for column in ("q_sell_over_oi", "q_buy_over_oi"):
        print(f"\n--- top 10 by {column}, no floor (the published ranking) ---")
        print(report.to_markdown(report.ranking_table(frag, column)))
        for floor in (100_000, 250_000):
            print(f"\n--- top 3 by {column}, open interest >= {floor:,} ---")
            print(report.to_markdown(report.ranking_table(frag, column, n=3,
                                                         min_open_interest=floor)))

    # Selected by the ranking, not by hand: the top row of each table above.
    picks = [report.ranking_table(frag, c, n=1)["market_code"].iloc[0]
             for c in ("q_sell_over_oi", "q_buy_over_oi")]

    wide = from_vintage()
    flows = decompose(wide)

    for code in picks:
        arith = report.q_arithmetic(cross, code)
        rule(f"2-4. WALKTHROUGH — {arith['market_name']} ({code})")
        print(report.to_markdown(report.category_table(cross, code)))
        print()
        print(report.format_q_block(arith))
        print(f"\n    Q_sell / OI = {arith['q_sell_over_oi']:.4f}"
              f"    Q_buy / OI = {arith['q_buy_over_oi']:.4f}")

        print("\n--- flow decomposition, latest week, every category ---")
        last = flows[(flows["market_code"] == code)
                     & (flows["report_date"] == flows["report_date"].max())]
        print(report.to_markdown(last[["category", "long_contracts", "short_contracts",
                                       "d_long", "d_short", "d_net", "d_oi", "flow_state",
                                       "fuel_remaining", "oi_corroborates"]]))

        print("\n--- Managed Money, trailing 12 weeks ---")
        print(report.to_markdown(report.flow_sequence(flows, code, "managed_money")))

        mm = cross[(cross["market_code"] == code) & (cross["category"] == "managed_money")]
        side = "long" if mm["long_contracts"].iloc[0] >= mm["short_contracts"].iloc[0] \
            else "short"
        print(f"\n--- breadth-depth, Managed Money {side} side, trailing 12 weeks ---")
        breadth = decompose_breadth(wide[wide["market_code"] == code], side=side)
        print(report.to_markdown(
            breadth[breadth["category"] == "managed_money"][BREADTH_COLUMNS].tail(12)))

    rule("5. TOLERANCE SENSITIVITY (handoff §3)")
    print(f"\n--- wide panel: {wide['market_code'].nunique()} markets, "
          f"{len(flows):,} transitions ---")
    print(report.to_markdown(tolerance_sensitivity(wide).reset_index()))

    liquid = from_current_store()
    print(f"\n--- liquid panel: {liquid['market_code'].nunique()} markets, "
          f"{liquid['report_date'].min().date()} to {liquid['report_date'].max().date()} ---")
    print(report.to_markdown(tolerance_sensitivity(liquid).reset_index()))

    print("\n--- does the tolerance ever change the DIRECTION, or only the commitment? ---")
    pure = {"new_longs", "short_covering", "new_shorts", "long_liquidation"}
    tight = decompose(liquid, tolerance=0.15)["flow_state"].to_numpy()
    loose = decompose(liquid, tolerance=0.40)["flow_state"].to_numpy()
    changed = tight != loose
    flips = sum(1 for t, ls in zip(tight[changed], loose[changed])
                if t in pure and ls in pure)
    print(f"    {changed.mean():.2%} of {len(tight):,} weeks change label between "
          f"0.15 and 0.40")
    print(f"    of those, {flips} are pure -> a DIFFERENT pure state")

    rule("6. OPEN-INTEREST IDENTITY (handoff §2, §8)")
    print(f"\n--- liquid panel, by year ({liquid['market_code'].nunique()} markets) ---")
    print(report.to_markdown(oi_identity_summary(liquid, by_year=True).reset_index()))
    print(f"\n--- wide panel, all ({wide['market_code'].nunique()} markets) ---")
    print(report.to_markdown(oi_identity_summary(wide).reset_index(drop=True)))

    rule("7. CONTEXT — what the ranked universe is made of")
    venue = frag.assign(venue=frag["market_name"].str.split(" - ").str[-1])
    print("\nmarkets by venue:")
    print(venue["venue"].value_counts().to_string())
    print("\ntop Phi contributor, across all markets:")
    print(frag["top_phi_category"].value_counts().to_string())
    print("\nwhere the classic outrights rank on q_sell/OI:")
    ordered = frag.sort_values("q_sell_over_oi", ascending=False).reset_index(drop=True)
    for code, name in [("088691", "GOLD"), ("084691", "SILVER"), ("005602", "SOYBEANS"),
                       ("002602", "CORN"), ("067651", "CRUDE OIL"),
                       ("001602", "WHEAT-SRW"), ("023651", "NAT GAS")]:
        row = ordered[ordered["market_code"] == code]
        if not row.empty:
            print(f"  {name:<10} rank {row.index[0] + 1:>3}/{len(ordered)}   "
                  f"q_sell/OI={row['q_sell_over_oi'].iloc[0]:.4f}   "
                  f"phi={row['phi'].iloc[0]:.3f}")


def _ann_vol(s: pd.Series) -> float:
    r = s.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    return float(r.std() * np.sqrt(252))


def normalisation() -> None:
    """Amendments A8 and A9: which price series volatility needs, and why not the other two.

    Independent of the COT store: these are claims about `cotdata`'s three price adjustments.
    """
    import cotdata

    rule("8. NORMALISATION: the price series volatility needs (A8, A9)")

    print("\n--- A8: annualised vol by adjustment. `backadj` percent returns are not vol ---")
    rows = []
    for sym in ["DC", "ZS", "ZN", "CT", "CL", "NG", "GC", "SI", "HG", "ES", "6E", "ZC", "LE"]:
        b = cotdata.get_prices(sym, adjustment="backadj")["Close"].dropna()
        p = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        if b.empty or p.empty:
            continue
        vb, vp = _ann_vol(b), _ann_vol(p)
        rows.append({"symbol": sym, "vol_backadj": f"{vb:.4g}", "vol_propadj": f"{vp:.4g}",
                     "inflation": f"{vb / vp:.3g}x",
                     "backadj_nonpos": f"{(b <= 0).mean() * 100:.1f}%"})
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nGOLD is the case that makes this a refusal: never negative, so it passes every")
    print("implausibility screen, and still wrong by ~2x in the UNDERSTATING direction.")

    print("\n--- A8: `unadj` hides its damage in the full sample and wrecks short windows ---")
    rows = []
    for sym in ["GC", "CL", "NG", "ZS", "ZN", "ES", "DC", "LE"]:
        u = cotdata.get_prices(sym, adjustment="unadj")["Close"].dropna()
        p = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        idx = u.index.intersection(p.index)
        if len(idx) < 200:
            continue
        u, p = u.loc[idx], p.loc[idx]
        ru = u.pct_change().replace([np.inf, -np.inf], np.nan)
        rp = p.pct_change().replace([np.inf, -np.inf], np.nan)
        ratio = (ru.rolling(63).std() / rp.rolling(63).std()) \
            .replace([np.inf, -np.inf], np.nan).dropna()
        # Restricted to actual roll dates. Taking the max over ALL days would pick up
        # crude's 2020-04-21 move off a negative settlement (306%), which is a real price
        # crossing zero and not a roll artifact at all. This column is about rolls.
        try:
            roll_days = idx.intersection(cotdata.roll_dates(sym))
        except Exception:                                          # noqa: BLE001
            roll_days = idx[:0]
        worst = ru.loc[roll_days].abs().max() if len(roll_days) else float("nan")
        rows.append({"symbol": sym,
                     "full_sample": f"{_ann_vol(u) / _ann_vol(p):.2f}x",
                     "worst_63d": f"{ratio.max():.2f}x",
                     "on": str(ratio.idxmax().date()),
                     "windows_over_1.25x": f"{(ratio > 1.25).mean() * 100:.1f}%",
                     "rolls": len(roll_days),
                     "worst_roll_day": f"{worst * 100:.1f}%"})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n--- A8 cross-check: dollar vol two independent ways, mid-history ---")
    print("(a) unadj price x sigma_pct(propadj)   (b) std(diff(backadj))")
    rows = []
    for sym in ["GC", "CL", "ZS", "ZN", "DC", "ES", "6E", "KC"]:
        p = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        b = cotdata.get_prices(sym, adjustment="backadj")["Close"].dropna()
        u = cotdata.get_prices(sym, adjustment="unadj")["Close"].dropna()
        idx = p.index.intersection(b.index).intersection(u.index)
        if len(idx) < 200:
            continue
        p, b, u = p.loc[idx], b.loc[idx], u.loc[idx]
        a = (u * p.pct_change().replace([np.inf, -np.inf], np.nan)
             .rolling(63).std()).dropna()
        bb = b.diff().rolling(63).std().dropna()
        both = a.index.intersection(bb.index)
        at = both[len(both) // 3]
        rows.append({"symbol": sym, "date": str(at.date()), "path_a": f"{a.loc[at]:.4f}",
                     "path_b": f"{bb.loc[at]:.4f}", "a/b": f"{a.loc[at] / bb.loc[at]:.3f}"})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n--- A9: `propadj` is NOT strictly positive. Rate separates event from artifact ---")
    import json
    import os
    import pathlib
    man = json.loads(
        (pathlib.Path(os.environ["COTDATA_STORE"]) / "manifests" / "prices.json").read_text())
    syms = sorted({k.rsplit("_", 1)[0] for k in man.get("prices", man)})
    hits = []
    for sym in syms:
        try:
            p = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        except Exception:                                          # noqa: BLE001
            continue
        n = int((p <= 0).sum())
        if n:
            hits.append({"symbol": sym, "non_positive": n, "bars": len(p),
                         "rate": f"{n / len(p) * 100:.5f}%",
                         "first": str(p[p <= 0].index.min().date()),
                         "min_close": f"{p.min():.2f}"})
    print(f"{len(syms)} symbols scanned; {len(hits)} with any non-positive propadj close")
    print(pd.DataFrame(hits).to_string(index=False) if hits else "  (none)")
    print("\nAgainst backadj, for the same question:")
    print(pd.DataFrame([
        {"symbol": s,
         "rate": f"{(cotdata.get_prices(s, adjustment='backadj')['Close'].dropna() <= 0).mean() * 100:.1f}%"}
        for s in ["ZS", "DC", "ZN", "CT", "CL"]]).to_string(index=False))
    print("\nMAX_NONPOSITIVE_RATE = 1% sits in the empty gap between those two tables.")


def volume_and_exit_capacity() -> None:
    """Amendment A10: that `volume="front"` is whole-market, and the T it produces."""
    import json
    import os
    import pathlib

    import cotdata

    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_volume,
        fragility_frame,
        rank_markets,
        volume_coverage,
    )

    rule("9. VOLUME: whole-market, and the real T = Q/(kappa V) (A10, A11)")

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    week = panel["report_date"].max()
    panel = panel[panel["report_date"] == week]

    print(f"\n--- A10 proof 1: price-file open interest vs the CFTC, {week.date()} ---")
    rows = []
    for _, r in (panel.dropna(subset=["symbol"])
                 .groupby("symbol", as_index=False)["open_interest"].max()).iterrows():
        px = cotdata.get_prices(r["symbol"], adjustment="unadj")
        if px.empty:
            continue
        oi = pd.to_numeric(px["Open Interest"], errors="coerce").replace(0, np.nan).dropna()
        asof = oi.index[oi.index <= week]
        if len(asof) == 0 or not r["open_interest"]:
            continue
        rows.append({"symbol": r["symbol"], "cot_oi": int(r["open_interest"]),
                     "price_file_oi": int(oi.loc[asof[-1]]),
                     "ratio": round(float(oi.loc[asof[-1]]) / r["open_interest"], 4)})
    oi_df = pd.DataFrame(rows).sort_values("ratio")
    print(oi_df.to_string(index=False))
    print(f"exact matches: {(oi_df['ratio'] == 1.0).sum()} of {len(oi_df)}   "
          f"median {oi_df['ratio'].median():.4f}")

    print("\n--- A10 proof 2: first-two-contract share of Volume, trailing 500d ---")
    root = pathlib.Path(os.environ["COTDATA_STORE"]) / "prices"
    rows = []
    for sym in ["NG", "CL", "HO", "RB", "LE", "HE", "ZM", "ZL", "CC", "ZS", "SB", "KC",
                "ZC", "ZW", "CT", "HG", "GC", "SI", "PL", "6E", "ES", "ZN"]:
        p = root / f"{sym}_unadj.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        if not {"FirstVolume", "SecondVolume", "Volume"} <= set(d.columns):
            continue
        d = d.dropna(subset=["FirstVolume", "SecondVolume"]).tail(500)
        d = d[d["Volume"] > 0]
        if len(d) < 100:
            continue
        rows.append({"symbol": sym, "adv_total": f"{d['Volume'].mean():,.0f}",
                     "adv_first2": f"{(d['FirstVolume'] + d['SecondVolume']).mean():,.0f}",
                     "first2_share": round(float(((d["FirstVolume"] + d["SecondVolume"])
                                                  / d["Volume"]).mean()), 3)})
    print(pd.DataFrame(rows).sort_values("first2_share").to_string(index=False))
    print("A front-month series would read 1.00 everywhere. It orders by curve depth.")

    print("\n--- A10: coverage. Every symbol, essentially every bar ---")
    man = json.loads((pathlib.Path(os.environ["COTDATA_STORE"]) / "manifests"
                      / "prices.json").read_text())
    cov = {}
    for sym in sorted({k.rsplit("_", 1)[0] for k in man.get("prices", man)}):
        try:
            d = cotdata.get_prices(sym, adjustment="unadj")
        except Exception:                                          # noqa: BLE001
            continue
        if d.empty or "Volume" not in d:
            continue
        v = pd.to_numeric(d["Volume"], errors="coerce").replace(0, np.nan).dropna()
        cov[sym] = len(v) / len(d)
    c = pd.Series(cov)
    print(f"symbols with volume: {len(c)}   median coverage {c.median():.1%}   "
          f"worst {c.idxmin()} {c.min():.1%}")

    print("\n--- A10: T = Q/(kappa V), and how far it moves the Q/OI proxy ---")
    frag = add_volume(fragility_frame(panel).merge(
        panel[["market_code", "symbol"]].drop_duplicates(), on="market_code", how="left"))
    print(volume_coverage(frag).to_string())
    ranked = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"])
    live = ranked.dropna(subset=["dtl_sell"]).copy()
    live["stress_over_calm"] = (live["adv_stress"] / live["adv"]).round(2)
    show = live.nlargest(12, "dtl_sell")[
        ["market_name", "q_sell", "adv", "adv_stress", "stress_over_calm",
         "q_sell_over_oi", "dtl_sell", "dtl_sell_stress"]].copy()
    show["market_name"] = show["market_name"].str.slice(0, 26)
    print(show.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    corr = live["q_sell_over_oi"].rank(ascending=False).corr(
        live["dtl_sell"].rank(ascending=False))
    print(f"\nrank corr, Q/OI proxy vs real T : {corr:.3f}   (1.0 would make T redundant)")
    print(f"T range: {live['dtl_sell'].min():.2f} to {live['dtl_sell'].max():.2f} days, "
          f"median {live['dtl_sell'].median():.2f}")
    more = int((live["adv_stress"] > live["adv"]).sum())
    print(f"markets trading MORE under stress: {more} of {len(live)}  "
          f"-> T_stress is SHORTER there, so stress is not reliably the conservative case")

    print("\n--- A11: what the 254 unjoined markets are ---")
    venue = panel.assign(v=panel["market_name"].str.split(" - ").str[-1])
    unjoined = venue[venue["symbol"].isna()].drop_duplicates("market_code")
    print(unjoined["v"].value_counts().head(6).to_string())
    print(f"\n{len(unjoined)} markets have no contract spec. They are not a missing 91%: "
          f"they are\nmarkets that are not traded (cost, liquidity, access). The {len(live)} "
          f"that join are the\ntradeable universe, so a ranking over them is the population, "
          f"not a sample.")


def exit_cost() -> None:
    """Amendments A19 and A20: cost is not duration, and Amihud needs the multiplier."""
    import cotdata

    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_impact,
        add_volume,
        fragility_frame,
        impact_coverage,
        rank_markets,
    )
    from crowdmon.futures.impact import _dollar_volume

    rule("10. EXIT COST: the square-root law and Amihud (A19, A20)")

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel[panel["report_date"] == panel["report_date"].max()]
    spec = panel[["market_code", "symbol", "point_value"]].drop_duplicates("market_code")
    frag = add_volume(fragility_frame(panel).merge(spec, on="market_code", how="left"))
    frag = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"])
    scored = add_impact(frag)
    print(impact_coverage(scored).to_string())

    live = scored.dropna(subset=["impact_sell"]).copy()
    print("\n--- A18: exit cost, and how little it tracks exit duration ---")
    show = live.nlargest(10, "impact_sell")[
        ["market_name", "q_sell", "adv", "sigma_daily", "dtl_sell", "impact_sell_bps"]].copy()
    show["market_name"] = show["market_name"].str.slice(0, 24)
    print(show.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    corr = live["dtl_sell"].rank(ascending=False).corr(
        live["impact_sell"].rank(ascending=False))
    print(f"\nrank corr, T vs impact : {corr:.3f}   (near zero: they are different questions)")
    print(f"cost range: {live['impact_sell_bps'].min():.0f} to "
          f"{live['impact_sell_bps'].max():.0f} bps, median "
          f"{live['impact_sell_bps'].median():.0f}")
    print(f"Q/V range : {(live['q_sell'] / live['adv']).min():.2f} to "
          f"{(live['q_sell'] / live['adv']).max():.2f} days of total volume")

    print("\n--- A20: Amihud with and without the contract multiplier ---")
    rows = []
    for _, r in live.dropna(subset=["symbol", "point_value"]).drop_duplicates(
            "symbol").iterrows():
        sym, pv = r["symbol"], float(r["point_value"])
        px = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
        nonpos = px <= 0
        ret = px.pct_change().replace([np.inf, -np.inf], np.nan) \
                .where(~(nonpos | nonpos.shift(fill_value=False)))
        ok, no = _dollar_volume(sym, pv), _dollar_volume(sym, 1.0)
        if ok.empty:
            continue
        rows.append({"symbol": sym, "multiplier": pv,
                     "adv_usd_m": round(float(ok.tail(252).mean()) / 1e6),
                     "correct": (ret.abs() / ok.reindex(ret.index)).tail(252).mean(),
                     "without": (ret.abs() / no.reindex(ret.index)).tail(252).mean()})
    df = pd.DataFrame(rows).dropna()
    df["rank_correct"] = df["correct"].rank(ascending=False).astype(int)
    df["rank_without"] = df["without"].rank(ascending=False).astype(int)
    df["moved"] = (df["rank_correct"] - df["rank_without"]).abs()
    df["amihud_e12"] = (df["correct"] * 1e12).round(2)
    print(df.nsmallest(8, "rank_correct")[
        ["symbol", "multiplier", "adv_usd_m", "amihud_e12",
         "rank_correct", "rank_without", "moved"]].to_string(index=False))
    print(f"\nrank corr, with vs without the multiplier : "
          f"{df['rank_correct'].corr(df['rank_without']):.3f}")
    print(f"markets moving more than 5 places        : {int(df['moved'].gt(5).sum())} "
          f"of {len(df)}")
    print(f"multiplier spread                        : {df['multiplier'].min():g} to "
          f"{df['multiplier'].max():g}")


def commonality() -> None:
    """2026-08-02 A1 and A2: the own-market identity, and the percentile no-op."""
    from crowdmon.core.aggregate import rolling_percentile
    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        commonality_betas,
        gamma_sensitivity,
        illiquidity_panel,
        rolling_betas,
        t_effective,
    )

    rule("11. COMMONALITY: do the exits go through the same door? (2026-08-02 A1, A2)")

    cot = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    specs = (cot.dropna(subset=["symbol", "point_value"])[["symbol", "point_value"]]
             .drop_duplicates("symbol").itertuples(index=False, name=None))
    panel = illiquidity_panel(specs, start="2015-01-01")
    print(f"\n{panel.shape[1]} markets, {panel.shape[0]} days, "
          f"{panel.index.min().date()} to {panel.index.max().date()}")

    excl = commonality_betas(panel)
    incl = commonality_betas(panel, exclude_own=False)
    out = pd.DataFrame({"excl_own": excl, "incl_own": incl})
    out["inflation"] = (out["incl_own"] / out["excl_own"]).round(2)
    print("\n--- A1: beta by market, with and without the own market in the basket ---")
    print(out.round(3).sort_values("excl_own").to_string())
    print(f"\nbeta_bar excluding own : {excl.mean():.4f}   <- a measurement")
    print(f"beta_bar including own : {incl.mean():.4f}   <- an ALGEBRAIC IDENTITY, always 1")
    print("The identity: sum_i cov(y_i, ybar) = cov(N.ybar, ybar) = N.var(ybar), so the mean")
    print("beta is exactly 1 for ANY data, including independent series.")

    print("\n--- A2: a constant beta_bar cannot move a percentile ---")
    # Any strictly positive series demonstrates the invariance; the claim is about the
    # transform, not the data. Scaled to day-like magnitudes so the table reads sensibly.
    raw = panel.iloc[:, 0].dropna()
    durations = (raw / raw.median() * 4.0).rename("t")
    base = rolling_percentile(durations, window="1095D", min_periods=104)
    for gamma in (0.25, 0.5, 2.0):
        scaled = rolling_percentile(t_effective(durations, excl.mean(), gamma=gamma),
                                    window="1095D", min_periods=104)
        both = base.to_frame("a").join(scaled.rename("b")).dropna()
        print(f"  gamma={gamma:<5} max |pct(T_eff) - pct(T)| = "
              f"{(both['a'] - both['b']).abs().max():.2e}")
    print("\ngamma sensitivity on a constant beta_bar (every rank corr is 1.000, which IS")
    print("the finding, reported rather than argued):")
    print(gamma_sensitivity(durations, excl.mean()).round(4).to_string(index=False))

    print("\n--- A2: only a time-varying beta_bar reaches the composite ---")
    bt = rolling_betas(panel).mean(axis=1).dropna()
    mult = 1 + 0.5 * bt
    print(f"  rolling beta_bar : {bt.min():.3f} to {bt.max():.3f}  (sd {bt.std():.3f})")
    print(f"  1 + 0.5*beta_bar : {mult.min():.3f} to {mult.max():.3f}  "
          f"-> {mult.max() / mult.min():.2f}x spread")
    print("  by year:")
    print(bt.groupby(bt.index.year).mean().round(3).to_string())


def trigger_guard() -> None:
    """2026-08-02 B9: why `trigger_prices` refuses anything but propadj."""
    import cotdata

    rule("12. THE TRIGGER GUARD: sign versus distance (2026-08-02 B9)")
    rows = []
    for symbol in ("GC", "CL", "ZS", "ZW", "CC", "NG", "DC"):
        back = cotdata.get_prices(symbol, adjustment="backadj")["Close"].dropna()
        prop = cotdata.get_prices(symbol, adjustment="propadj")["Close"].dropna()
        shared = back.index.intersection(prop.index)
        back, prop = back.loc[shared], prop.loc[shared]
        for k in (20, 60, 250):
            sb = np.sign(back - back.shift(k)).dropna()
            sp = np.sign(prop - prop.shift(k)).dropna()
            both = sb.index.intersection(sp.index)
            db = (back.shift(k) / back - 1).dropna()
            dp = (prop.shift(k) / prop - 1).dropna()
            shared_d = db.index.intersection(dp.index)
            rows.append({"symbol": symbol, "k": k,
                         "sign_agree": round(float((sb.loc[both] == sp.loc[both]).mean()), 4),
                         "distance_p95_pp": round(float((db.loc[shared_d] - dp.loc[shared_d])
                                                        .abs().quantile(0.95) * 100), 1)})
    out = pd.DataFrame(rows)
    print("\n" + out.pivot(index="symbol", columns="k",
                            values="sign_agree").to_string())
    print(f"\nsign agreement: min {out.sign_agree.min():.4f}  mean {out.sign_agree.mean():.4f}")
    print("\ntrigger DISTANCE disagreement, percentage points at p95:")
    print(out.pivot(index="symbol", columns="k", values="distance_p95_pp").to_string())
    print("\nThe sign barely cares which series it reads. The distance is wrong by hundreds")
    print("of points on backadj, which is why trigger_prices refuses it.")


def vintage_coverage() -> None:
    """What the vintage store can and cannot support, for pre-registration §4.

    The question is not "how far back do report dates go", which is what both sessions
    had been quoting. It is "how many keys carry more than one observation", because a
    key observed once has no as-published value to replay against, whatever its report
    date says.
    """
    rule("13. VINTAGE COVERAGE (validation pre-registration §4)")
    from cotdata import vintage_ingest as vi

    obs = vi.read_observations()
    if obs.empty:
        print("no vintage observations in this store")
        return
    obs = obs.assign(report_date=pd.to_datetime(obs["report_date"]))

    key = ["report_date", "market_code", "report_type", "combined", "category"]
    per_key = obs.groupby(key, observed=True)["observed_at"].nunique()

    print(f"observations          {len(obs):,}")
    print(f"distinct keys         {len(per_key):,}")
    print(f"keys observed twice+  {int((per_key > 1).sum()):,}   <- the replayable ones")
    print(f"report dates          {obs.report_date.min():%Y-%m-%d} .. "
          f"{obs.report_date.max():%Y-%m-%d}  ({obs.report_date.nunique()} weeks)")
    print(f"observed_at           {obs.observed_at.min()} .. {obs.observed_at.max()}")

    print("\nreport weeks captured per capture date (a backfill spans many weeks at once):")
    print(obs.assign(_o=pd.to_datetime(obs["observed_at"]).dt.date)
             .groupby("_o")["report_date"].agg(["min", "max", "nunique"]).to_string())

    print("\nrelease-date provenance, by REPORT WEEK (the index a PIT replay joins on):")
    by_week = obs.groupby("report_date")["release_date_source"].agg(
        lambda s: "/".join(sorted(set(s))))
    print(by_week.value_counts().to_string())
    print("\n`derived` is report_date + 3d weekend-adjusted, a guess: cotdata's own "
          "vintage_schedule\ndocstring says strict PIT evaluation must be able to exclude it.")

    strict = int((by_week == "published").sum())
    print(f"\nreport weeks with an OBSERVED release date: {strict} of {len(by_week)}")
    print("report weeks with a replayable revision:     "
          f"{obs.loc[per_key[per_key > 1].index.get_level_values(0).unique()].report_date.nunique() if (per_key > 1).any() else 0}"
          f" of {len(by_week)}")


def constant_invariance() -> None:
    """Which of the three configured constants can move `D`, for pre-registration §5.

    `gamma` was already shown unable to reach the composite (`2026-08-02 §B2`). The same
    argument applies to `kappa`, and it had not been made: `T = Q / (kappa . V)` with a
    global `kappa`, and `I = pct(T)` taken WITHIN a market, so `kappa` is a positive scalar
    under a monotonic transform and cancels exactly. Asserting that is cheap; measuring it
    costs one build and closes the question an evaluator would otherwise spend a day on.
    """
    rule("14. CAN THE CONFIGURED CONSTANTS MOVE D? (pre-registration §5)")
    from reproduce_composite import build

    from crowdmon.futures import composite as cmp

    pct_by_market = cmp._percentile_by_market
    win, minp = cmp.DEFAULT_WINDOW, cmp.DEFAULT_MIN_PERIODS

    panel = build()
    print(f"panel: {len(panel):,} market-weeks, {panel.market_code.nunique()} markets")
    base = pct_by_market(panel, "dtl_sell", window=win, min_periods=minp)

    print("\nkappa enters as T = Q / (kappa . V), so changing it scales dtl by a constant:")
    for kappa in (0.05, 0.4, 1.0):
        scaled = panel.assign(_s=panel["dtl_sell"] * (0.2 / kappa))
        got = pct_by_market(scaled, "_s", window=win, min_periods=minp)
        print(f"  kappa 0.2 -> {kappa:<5} max |change in I| = "
              f"{(got - base).abs().max():.2e}")

    print("\nY does not appear in add_composite at all: the square-root law feeds the exit")
    print("COST, and D's I term is the exit DURATION. They are orthogonal (2026-08-01 §A19).")
    print("\nSo none of kappa, Y or gamma can move D by any amount. What moves D is the")
    print("weights' ORDERING (2026-08-01 §A22) and the phi_percentile reading (§A15).")


def reflexivity() -> None:
    """2026-08-02 B13-B15: the cascade staircase, and three claims that did not survive it."""
    from crowdmon.futures import reflexivity as rx
    from crowdmon.futures import trigger as trig

    rule("15. CASCADE AMPLIFICATION: the staircase (2026-08-02 B13, B14, B15)")

    print("\nB13. l.g grows as sqrt(pool), not linearly.")
    sigma, vol, net = 0.011, 180_000.0, 119_795.0
    for label, q, d in (("60d, pool = |net|", net, 0.137087),
                        ("20d, pool = |net|", net, 0.019376),
                        ("20d, whole 3x gross", 3 * net, 0.019376)):
        lam = rx.effective_lambda(sigma, q, vol)
        lg = lam * q / d
        amp = rx._amplification(lg)
        print(f"  {label:22s} l.g = {lg:.3f}   amp = {amp:.2f}x")
    ratio = ((rx.effective_lambda(sigma, 3 * net, vol) * (3 * net))
             / (rx.effective_lambda(sigma, net, vol) * net))
    print(f"  tripling the pool multiplies l.g by {ratio:.4f}  (sqrt(3) = {3 ** 0.5:.4f})")
    print("  The linear reading put the third row at 1.231, 'no equilibrium'. It is 0.602.")

    print("\nB14. Trigger distance is NOT monotonic in lookback.")
    for symbol in ("GC", "ZC", "CL"):
        out = trig.trigger_prices(symbol, lookbacks=(20, 60, 250))
        dist = {int(r.lookback_days): abs(r.move_from_spot) for r in out.itertuples()}
        nearest = min(dist, key=dist.get)
        print(f"  {symbol}: " + "  ".join(f"{k}d {v:.2%}" for k, v in dist.items())
              + f"   nearest = {nearest}d")

    print("\n  Worst step per direction, across the universe:")
    syms = ("GC SI HG PL PA CL NG HO RB ZC ZS ZW ZM ZL KC CC SB CT LE HE "
            "ZN ZF ZT ZB 6E 6J 6B 6A 6C 6S ES NQ YM").split()
    multi = past = 0
    for symbol in syms:
        try:
            stairs = rx.staircase(trig.trigger_prices(symbol, lookbacks=(20, 60, 250)),
                                  net_contracts=100_000.0, sigma_daily=0.015,
                                  volume=150_000.0)
        except Exception:
            continue
        for _, side in stairs.groupby("direction"):
            if len(side) < 2:
                continue
            multi += 1
            ranked = side.sort_values("distance")
            if ranked["lg"].idxmax() != ranked.index[0]:
                past += 1
    print(f"  multi-step direction-staircases: {multi};  peaking PAST the nearest: {past}")
    print("  Net-independent: lg_2/lg_1 = sqrt(2).d_1/d_2, so the count needs no real position.")

    print("\nB15. sum(s) == 0 is reachable without a config change.")
    for label, signals in (("flat lookback", [0, -1, 1]),
                           ("short history", [-1, None, 1]),
                           ("fourth lookback", [1, -1, 1, -1])):
        try:
            rx.implied_gross_pool(signals, 100_000.0)
            print(f"  {label:18s} -> NOT refused (unexpected)")
        except rx.ReflexivityError:
            print(f"  {label:18s} -> refused, as it must be")
    print("  Parity protects the count of CONTRIBUTING signals, not len(DEFAULT_LOOKBACKS).")


def roll_dates_coverage() -> None:
    """2026-08-02 B16: roll congestion is not blocked, and the wrong argument type is silent."""
    import cotdata

    rule("16. ROLL DATES: coverage, and the silent wrong-argument case (2026-08-02 B16)")

    symbols = cotdata.all_symbols()
    rows = []
    for sym in symbols:
        dates = cotdata.roll_dates(sym.internal)
        rows.append({"symbol": sym.internal, "rolls": len(dates),
                     "first": dates[0].date() if len(dates) else None,
                     "last": dates[-1].date() if len(dates) else None,
                     "norgate": sym.norgate, "yahoo": sym.yahoo})
    frame = pd.DataFrame(rows)
    ok = frame[frame["rolls"] > 0]

    print(f"\n  registry symbols : {len(frame)}")
    print(f"  non-empty        : {len(ok)}")
    print(f"  empty            : {int((frame['rolls'] == 0).sum())}")
    print(f"  rolls per symbol : min {ok['rolls'].min()}  "
          f"median {int(ok['rolls'].median())}  max {ok['rolls'].max()}")
    print(f"  span             : {ok['first'].min()} to {ok['last'].max()}")

    print("\n  deepest:")
    print(ok.sort_values("rolls", ascending=False)
            .head(3)[["symbol", "rolls", "first", "last"]].to_string(index=False))

    print("\n  the empties, and why they are not a gap:")
    print(frame[frame["rolls"] == 0][["symbol", "norgate", "yahoo"]].to_string(index=False))
    print("  norgate=None, sourced from Yahoo: equity ETF proxies, so no Delivery Month.")

    # The trap. all_symbols() yields Symbol namedtuples, and roll_dates returns an empty
    # index rather than raising when handed one, so the obvious one-liner reports zero
    # coverage across the whole universe and reads like missing data.
    wrong = sum(len(cotdata.roll_dates(sym)) for sym in symbols)
    right = sum(len(cotdata.roll_dates(sym.internal)) for sym in symbols)
    print(f"\n  passing Symbol objects : {wrong} rolls across {len(symbols)} symbols")
    print(f"  passing s.internal     : {right} rolls across {len(symbols)} symbols")
    print("  Same store, same function, 0% and 100%. A universe-wide zero is a bug in the")
    print("  call before it is a fact about the data.")

    # A ladder rather than one step: the field is `internal`, not `symbol`, so the obvious
    # correction to the silent case is the loud one and rescues by accident.
    try:
        symbols[0].symbol
        guess = "no error (unexpected)"
    except AttributeError as exc:
        guess = f"AttributeError: {exc}"
    print(f"\n  s.symbol   -> {guess}")
    print("  s.internal -> correct. The silent call is the one written first.")

    # The adjustment argument, which is the one place in this package a default series is safe.
    identical = differing = 0
    for sym in symbols:
        series = [cotdata.roll_dates(sym.internal, adj)
                  for adj in ("backadj", "unadj", "propadj")]
        if all(len(s) == 0 for s in series):
            continue
        if series[0].equals(series[1]) and series[0].equals(series[2]):
            identical += 1
        else:
            differing += 1
    print(f"\n  roll dates identical across backadj/unadj/propadj : {identical}")
    print(f"  differing                                         : {differing}")
    print("  Rolls come from the Delivery Month column changing, and adjustment rescales")
    print("  bars without moving a delivery month. Safe by construction, not by luck, and")
    print("  only while rolls are derived that way rather than inferred from price gaps.")


def coverage_ladder_report() -> None:
    """Which markets can be scored at all, and where the others drop out (B17).

    The gap the §10 evaluator found: every other coverage helper answers one rung, and none
    of them answers whether a market can appear in a cross-market result. Two of 27 score
    nothing, ever, and they die at different rungs.
    """
    rule("17. THE COVERAGE LADDER (2026-08-02 B17)")
    from reproduce_composite import build

    from crowdmon.futures import (
        ContractMaster,
        add_extremity,
        add_notional,
        add_risk_units,
        add_volume,
        coverage_ladder,
        coverage_summary,
        format_coverage,
    )

    panel = from_current_store()
    per_category = add_volume(add_extremity(add_risk_units(
        add_notional(ContractMaster.load().annotate(panel)))))
    per_market = build()

    print("markets surviving each rung:")
    print(coverage_summary(per_category, per_market).to_string())

    ladder = coverage_ladder(per_category, per_market)
    print("\nthe markets that score nothing, and the rung that bites:")
    print(format_coverage(ladder, only_unscoreable=True))
    print("\n058643 is starved of prices; 058644 has a COMPLETE exit duration in every one")
    print("of its weeks and still scores nothing, because the percentile windows stack.")
    print("A report saying only '0 scoreable weeks' sends a maintainer to prices for both,")
    print("and for one of them there is nothing wrong with the prices.")
    print("\nTwo things B18 corrected in the first cut of this ladder:")
    print("  - both markets TERMINATE at `crowding`, for unrelated reasons, so the label")
    print("    alone is insufficient and the full ladder has to be printed beside it")
    print("  - the ladder is NOT monotonic. `holder_fragility` is price-free, so 058643")
    print("    carries 880 weeks of it against 24 of `dtl_sell`, a 36x rise mid-ladder.")
    print("    Price-free rungs are starred above.")

    by_code = per_market.groupby("market_code")["damage_sell_pct"].apply(
        lambda s: s.notna().sum())
    by_pair = per_market.groupby(["market_code", "market_name"])["damage_sell_pct"].apply(
        lambda s: s.notna().sum())
    names = per_category.groupby("market_code")["market_name"].nunique()
    print("\nwhy the key is market_code and not market_name:")
    print(f"  codes carrying more than one name : {int((names > 1).sum())} of {len(names)}")
    print(f"  zero-scoring, keyed on code       : {int((by_code == 0).sum())}")
    print(f"  zero-scoring, keyed on code+name  : {int((by_pair == 0).sum())}")
    for (code, name), v in by_pair[by_pair == 0].items():
        if by_code[code] > 0:
            print(f"    PHANTOM {code} {name[:46]:<46} code scores {by_code[code]}")
    print("  the invented markets outnumber the real ones. And string normalisation is not")
    print("  the alternative: heating oil carries NY HARBOR ULSD and NY HARBOR USLD, a")
    print("  transposition, so one of the two is a typo in the CFTC source.")


def roll_windows() -> None:
    """2026-08-02 B19: the roll-window volume effect, and how much of it reaches `T`."""
    from crowdmon.futures import roll as rl

    rule("17. ROLL WINDOWS: the roll-day ratio is not the bias in T (2026-08-02 B21)")

    syms = "GC SI CL NG HO RB ZC ZS ZW HG KC CT LE ZN 6E ES".split()
    rows = []
    for symbol in syms:
        try:
            rows.append(rl.roll_window_stats(symbol, lookback_bars=252 * 4))
        except Exception:
            continue
    frame = pd.DataFrame(rows)

    print("\n" + frame[["symbol", "share_in_window", "roll_day_ratio",
                         "adv_inflation", "t_bias"]].round(4).to_string(index=False))
    print(f"\n  median roll-day ratio : {frame['roll_day_ratio'].median():.3f}")
    print(f"  median ADV inflation  : {frame['adv_inflation'].median():.4f}")
    print(f"  median T bias         : {frame['t_bias'].median():+.2%}")
    print("\n  The ratio is a fact about roll DAYS. `T` is driven by a trailing MEAN, so the")
    print("  effect is diluted by how few days those are. Quoting the ratio as the bias in")
    print("  `T` overstates it by an order of magnitude.")

    pess = frame.loc[frame["adv_inflation"] < 1.0, "symbol"].tolist()
    print(f"\n  markets where T is PESSIMISTIC, not optimistic: {pess}")
    print("  So \"optimistic by construction for every market\" is false.")

    # Pick the divergence case from the data rather than naming a market: which one it is
    # depends on the lookback, and hardcoding HO gave an example that showed no divergence
    # over four years even though it does over full history.
    split = frame[(frame["roll_day_ratio"] > 1.0) & (frame["adv_inflation"] < 1.0)]
    if not split.empty:
        r = split.iloc[0]
        print(f"\n  {r['symbol']}: roll-day ratio {r['roll_day_ratio']:.3f} "
              f"(MORE volume on roll days, by median)")
        print(f"      ADV inflation    {r['adv_inflation']:.3f} "
              f"(and yet excluding them RAISES the mean)")
        print("      The ratio is a median and the ADV is a mean. One does not predict the")
        print("      other, even in sign, so neither can stand in for the other.")
        print(f"      All such markets here: {split['symbol'].tolist()}")

    dense = frame.loc[frame["share_in_window"] > 0.4, "symbol"].tolist()
    print(f"\n  monthly rollers, >40% of bars inside a window: {dense}")
    print("  A roll-excluded ADV there uses about half the sample: a different estimator")
    print("  rather than a cleaner one, which is why the share is always reported beside it.")


def trend_alignment() -> None:
    """2026-08-02 B20: the alignment ceiling, and why the raw score is not comparable."""
    import cotdata

    from crowdmon.futures import (
        alignment_series,
        blend_sensitivity,
        from_current_store,
        momentum_panel,
    )

    rule("18. TREND ALIGNMENT: the score cannot reach 1 (2026-08-02 B20)")

    registry = {s.cftc_code: s.internal for s in cotdata.all_symbols()}
    panel = from_current_store()
    money = panel[panel["category"] == "managed_money"].assign(
        net=lambda d: d["long_contracts"] - d["short_contracts"])
    positioning = (money.groupby(["report_date", "market_code"])["net"].sum()
                   .unstack("market_code").sort_index())
    mapping = {c: registry[c] for c in positioning.columns if c in registry}

    equal = momentum_panel(mapping)
    scores = alignment_series(positioning, equal)

    print(f"\n  weeks: {len(scores):,}  "
          f"{scores['report_date'].min().date()} to {scores['report_date'].max().date()}")
    print("\n" + scores[["alignment", "alignment_ceiling", "alignment_vs_ceiling",
                          "momentum_strength"]]
          .describe(percentiles=[0.05, 0.5, 0.95]).round(3).to_string())

    lo, hi = scores["alignment_ceiling"].min(), scores["alignment_ceiling"].max()
    print(f"\n  The ceiling runs {lo:.3f} to {hi:.3f}, so the raw score is not comparable")
    print("  across weeks. 0.30 against a 0.34 ceiling is an expressed book; 0.30 against")
    print("  a 0.97 ceiling is not. alignment_vs_ceiling is the comparable figure.")

    print("\n  blend weights, swept rather than fitted:")
    panels = {"equal": equal,
              "fast": momentum_panel(mapping, weights=(0.6, 0.3, 0.1)),
              "slow": momentum_panel(mapping, weights=(0.1, 0.3, 0.6))}
    print(blend_sensitivity(positioning, panels).round(4).to_string(index=False))
    print("\n  Level moves more than ordering, the same shape 2026-08-01 §A22 found for the")
    print("  fragility weights.")
    print("\n  NOT sliced by any named episode, deliberately. See the module docstring.")
def macro_book_pca() -> None:
    """§7's absorption ratio, and the finding that PC1 is not the same object on both panels.

    Disaggregated PC1 is the grain complex; TFF PC1 is risk appetite. §7 says PC1
    approximates the aggregate systematic book, which is true of one panel and false of the
    other.
    """
    rule("18. THE MACRO-BOOK PCA (2026-08-02 B21)")
    from crowdmon.futures import (
        ContractMaster,
        absorption_ratio,
        add_extremity,
        add_notional,
        add_risk_units,
        positioning_panel,
        rolling_absorption,
        select_markets,
        shuffled_null,
        window_sensitivity,
    )

    for report_type in ("disaggregated", "tff"):
        raw = from_current_store(report_type=report_type)
        per_category = add_extremity(add_risk_units(
            add_notional(ContractMaster.load().annotate(raw))))
        panel = positioning_panel(per_category)
        cols = select_markets(panel)
        complete = panel[cols].dropna()
        print(f"\n--- {report_type} ---")
        print(f"  raw panel        {panel.shape[0]} weeks x {panel.shape[1]} markets, "
              f"{panel.notna().mean().mean():.1%} of cells present")
        print(f"  complete weeks   {panel.dropna().shape[0]} at full width, "
              f"{len(complete)} on the {len(cols)} selected")
        if len(cols) < 8:
            print("  too narrow for a PCA")
            continue
        result = absorption_ratio(panel[cols])
        null = shuffled_null(panel[cols], draws=60)
        print(f"  absorption       {result['absorption']:.3f}   "
              f"shuffled null {null.mean():.3f} (p95 {null.quantile(0.95):.3f})")
        symbols = per_category.drop_duplicates("market_code").set_index("market_code")["symbol"]
        top = result["loadings"].abs().sort_values(ascending=False).head(6).index
        print("  PC1              " + ", ".join(
            f"{symbols.get(c)} {result['loadings'][c]:+.2f}" for c in top))

        if report_type == "disaggregated":
            roll = rolling_absorption(panel, markets=cols)
            print(f"  rolling          {len(roll)} readings, "
                  f"{roll.report_date.min().date()} to {roll.report_date.max().date()}")
            print(f"  rotation         median {roll.rotation.median():.5f}  "
                  f"p95 {roll.rotation.quantile(0.95):.5f}  max {roll.rotation.max():.5f}")
            print("  (a value near 2 would mean the sign convention leaked back in; "
                  "1 - |cos| is bounded in [0, 1])")
            print("\n  window sensitivity:")
            print(window_sensitivity(panel, markets=cols).to_string(index=False))

    print("\nPC1 is the GRAIN COMPLEX on Disaggregated and RISK APPETITE on TFF, so §7's")
    print("'aggregate systematic book' is true of one panel and false of the other. And the")
    print("nulls differ (0.077 vs 0.054) only because a variance share is floored at 1/n and")
    print("TFF is narrower, so absorption is comparable to its own null and never across.")


def correlation_clustering() -> None:
    """2026-08-02 B25: §369's thesis holds, its example does not."""
    import cotdata

    from crowdmon.futures import (
        cluster_sweep,
        clusters_at,
        correlation_distance,
        cross_class_pairs,
        return_panel,
    )

    rule("19. CORRELATION CLUSTERING: the yen carry, not energy (2026-08-02 B25)")

    classes = {s.internal: s.asset_class for s in cotdata.all_symbols() if s.norgate}
    returns = return_panel(list(classes), start="2016").dropna(axis=1, thresh=1000)
    corr = returns.corr()
    print(f"\n  markets: {returns.shape[1]}  days: {returns.shape[0]:,}")

    print("\n  section 369's own illustration, JPY against energy:")
    for symbol in ("CL", "HO", "RB", "NG"):
        if symbol in corr.columns and "6J" in corr.columns:
            print(f"    6J vs {symbol:<3} {corr.loc['6J', symbol]:+.3f}")
    print("    Essentially nothing, and the wrong sign for the phrasing.")

    print("\n  what is actually there, JPY against the US rates complex:")
    for symbol in ("ZF", "ZN", "ZT", "ZB", "NKD"):
        if symbol in corr.columns:
            print(f"    6J vs {symbol:<3} {corr.loc['6J', symbol]:+.3f}")

    within, across = [], []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            value = corr.iloc[i, j]
            if not np.isfinite(value):
                continue
            same = classes.get(cols[i]) == classes.get(cols[j])
            (within if same else across).append(value)
    print(f"\n  mean correlation within an asset class: {np.mean(within):.3f} "
          f"({len(within)} pairs)")
    print(f"  mean correlation across asset classes : {np.mean(across):.3f} "
          f"({len(across)} pairs)")
    print("  Sector taxonomy is mostly right. Clustering earns its keep on the exceptions.")

    distance = correlation_distance(returns)
    print("\n  the partition, and how much of it the taxonomy already explains:")
    print(cluster_sweep(distance, ks=(2, 4, 6, 8, 10),
                        asset_class=classes).round(3).to_string(index=False))
    print("\n  Agreement is LOWEST at small k, not highest: average linkage gives one large")
    print("  cluster, so the partition says 'together' where the taxonomy says 'apart'.")

    labels = clusters_at(distance, 8)
    carry = sorted(labels[labels == labels.get("6J")].index) if "6J" in labels else []
    print(f"\n  at k=8, the cluster containing 6J: {carry}")

    print("\n  strongest cross-class pairs:")
    print(cross_class_pairs(returns, classes, min_corr=0.40)
          .head(6).round(3).to_string(index=False))
    print("\n  NOT sliced by any named episode, deliberately.")


def template_shape() -> None:
    """Amendment B28: the cocoa template is a JOINT claim, so measure the pair, not two margins.

    The 2026-07-28 ranking document answers "does real data match the cocoa template" with
    the marginal sign distribution per category. The template asserts Producer/Merchant
    short AND Managed Money long at the same time, which the margins cannot address: two
    categories can each be short half the time while rarely being opposed at all.
    """
    rule("THE COCOA TEMPLATE AS A JOINT SHAPE (2026-08-02 B28)")

    cross = latest()
    week = cross["report_date"].max().date()
    # `latest()` does not filter `combined`, and `combined` is part of fragility.MARKET_KEY.
    # Today the vintage store holds futures-only alone, but if futures-and-options rows ever
    # land, grouping without it would sum two different series into one bogus net and every
    # figure below would move with nothing raising. Fail loudly instead.
    if cross["combined"].nunique() != 1 or cross["report_type"].nunique() != 1:
        raise ValueError(
            f"section mixes series: combined={sorted(cross['combined'].unique())}, "
            f"report_type={sorted(cross['report_type'].unique())}. Filter before grouping.")
    net = (cross.groupby(["market_code", "category"])
                .apply(lambda g: g["long_contracts"].sum() - g["short_contracts"].sum(),
                       include_groups=False)
                .unstack("category"))
    print(f"\nreport week {week}, {len(net)} markets\n")

    print("--- the MARGINS, as published in 2026-07-28-first-rankings.md §2 ---")
    rows = []
    for cat in ["managed_money", "producer_merchant", "swap",
                "other_reportable", "nonreportable"]:
        s = net[cat].dropna()
        rows.append({"category": cat, "n": len(s),
                     "net long": int((s > 0).sum()), "net short": int((s < 0).sum()),
                     "flat": int((s == 0).sum()),
                     "long %": f"{(s > 0).mean():.1%}", "short %": f"{(s < 0).mean():.1%}",
                     "flat %": f"{(s == 0).mean():.1%}"})
    print(report.to_markdown(pd.DataFrame(rows)))

    pair = pd.concat([net["producer_merchant"].rename("pm"),
                      net["managed_money"].rename("mm")], axis=1).dropna()
    shapes = {
        "template  (PM short, MM long)": (pair.pm < 0) & (pair.mm > 0),
        "inverted  (PM long,  MM short)": (pair.pm > 0) & (pair.mm < 0),
        "same side (both short)": (pair.pm < 0) & (pair.mm < 0),
        "same side (both long)": (pair.pm > 0) & (pair.mm > 0),
        "MM net flat (no DIRECTIONAL fund net)": pair.mm == 0,
    }
    live = pair[pair.mm != 0]
    print("\n--- the JOINT shape, which the margins cannot show ---")
    out = []
    for name, mask in shapes.items():
        n = int(mask.sum())
        of_live = "n/a" if name.startswith("MM net flat") else f"{n / len(live):.1%}"
        out.append({"shape": name, "markets": n,
                    f"of {len(pair)}": f"{n / len(pair):.1%}",
                    f"of {len(live)} with a directional MM net": of_live})
    print(report.to_markdown(pd.DataFrame(out)))

    same_mask = ((pair.pm < 0) & (pair.mm < 0)) | ((pair.pm > 0) & (pair.mm > 0))
    same = int(same_mask.sum())
    tmpl = int(shapes["template  (PM short, MM long)"].sum())
    print(f"\n  hedger and fund on the SAME side: {same} of {len(pair)} "
          f"= {same / len(pair):.1%} of all markets, "
          f"{same / len(live):.1%} of the {len(live)} with a directional MM net")
    print(f"  a rule assuming PM short AND MM long is wrong in "
          f"{len(pair) - tmpl} of {len(pair)} = {(len(pair) - tmpl) / len(pair):.1%} "
          f"of all markets,")
    print(f"  and {len(live) - tmpl} of {len(live)} = {(len(live) - tmpl) / len(live):.1%} "
          f"of those with a directional MM net.")

    # "MM net flat" is NOT "no fund position". Nets are not a holding, which is the whole
    # reason Phi uses gross over 2*OI. Print the counterexamples rather than assert the label.
    gross = (cross.groupby(["market_code", "category"])
                  .apply(lambda g: g["long_contracts"].sum() + g["short_contracts"].sum(),
                         include_groups=False)
                  .unstack("category"))
    flat = pair.index[pair.mm == 0]
    held = gross.loc[flat, "managed_money"]
    held = held[held > 0]
    print(f"\n  of the {len(flat)} MM net-flat markets, {len(held)} hold a real GROSS book:")
    for code in held.index:
        row = cross[(cross["market_code"] == code)
                    & (cross["category"] == "managed_money")]
        print(f"    {code}  {row['market_name'].iloc[0]:<42s} "
              f"long {int(row['long_contracts'].sum()):,} / "
              f"short {int(row['short_contracts'].sum()):,} = gross {int(held[code]):,}")

    # B28 claims the Q axis SHIFTS on same-side markets. Print it rather than assert it.
    print("\n--- which category tops the Q contribution, same-side against template ---")
    contrib = contributions(cross)
    tally = []
    for label, idx in [("same side", pair.index[same_mask]),
                       ("template", pair.index[shapes["template  (PM short, MM long)"]])]:
        for side in ["sell", "buy"]:
            s = contrib[contrib["market_code"].isin(idx) & (contrib["q_side"] == side)]
            top = s.loc[s.groupby("market_code")["q_contribution"].idxmax()]
            counts = top["category"].value_counts()
            tally.append({"shape": label, "side": f"Q_{side}", "markets": len(top),
                          **{c: int(counts.get(c, 0)) for c in
                             ["managed_money", "producer_merchant", "swap",
                              "other_reportable", "nonreportable"]}})
    print(report.to_markdown(pd.DataFrame(tally)))
    print("\n  On template markets the axis is clean: MM tops Q_sell in 51/76, PM tops")
    print("  Q_buy in 43/76. On same-side markets it is a plurality, not a takeover:")
    print("  swap+other_reportable top Q_sell in 52/94 (55%) and Q_buy in 48/94 (51%),")
    print("  and MM is still the single largest Q_buy contributor in 32/94.")


def flow_equivalence() -> None:
    """Amendment B29: cotdata's decompose is this one at tolerance=1.0, and the oats rationale.

    The 2026-08-01 handoff closed leaving the two flow-decomposition implementations as its
    one open decision, characterised as "slightly different questions". They are the same
    function; only the refusals differ.

    **This block is historical once `cotdata` drops its copy**, which it did in cotdata#93,
    the change this measurement argued for. It then has nothing to compare and says so
    rather than raising: the figures B29 quotes were true of the code as it stood, and a
    reproducer that crashes would read as a broken measurement rather than a completed one.
    Run it against `cotdata<=0.2.0` to regenerate them.
    """
    from cotdata import vintage_flow as vf

    from crowdmon.futures import flow as cflow
    from crowdmon.futures.io import SERIES_KEY

    rule("THE TWO FLOW DECOMPOSITIONS (2026-08-02 B29)")
    if not hasattr(vf, "decompose"):
        print("\n  cotdata.vintage_flow.decompose is GONE, removed as a duplicate in")
        print("  cotdata#93, which is the outcome this measurement argued for. There is")
        print("  nothing left to compare, so the figures below are historical:")
        print("\n    135,835 transitions, 27 markets, 2006-2026")
        print("    at tolerance=1.0 with gaps off : 100.000000% label agreement, 0 mismatches")
        print("    d_long / d_short / d_net       : identical on every row")
        print("    at the default tolerance       : 38.07% agreement, every disagreement")
        print("                                     mine=mixed or mine=gap, never opposite")
        print("\n  Regenerate against cotdata<=0.2.0. The copy staying gone is asserted by")
        print("  cotdata/tests/test_vintage_flow.py::test_decompose_is_gone_and_stays_gone,")
        print("  and crowdmon/tests/test_flow_equivalence.py skips for this same reason.")
        return

    panel = from_current_store(report_type="disaggregated")
    key = SERIES_KEY + ["report_date"]
    print(f"\npanel: {panel['market_code'].nunique()} markets, "
          f"{panel['report_date'].min().date()} to {panel['report_date'].max().date()}")

    def join(**kw):
        mine, theirs = cflow.decompose(panel, **kw), vf.decompose(panel)
        return mine[key + ["flow_state", "days_elapsed", "d_net"]].merge(
            theirs[vf.SERIES_KEY + ["report_date", "state", "d_net"]],
            on=key, how="outer", suffixes=("_mine", "_theirs"), indicator=True)

    equal = join(tolerance=1.0, gap_days_tolerance=100_000)
    agree = (equal["flow_state"] == equal["state"]).mean()
    print("\n--- at tolerance=1.0 with gaps off: THE SAME FUNCTION ---")
    print(f"  rows {len(equal):,}, merge {equal['_merge'].value_counts().to_dict()}")
    print(f"  label agreement {agree:.6%}, mismatches "
          f"{int((equal['flow_state'] != equal['state']).sum())}")
    for col in ("d_net",):
        ident = (equal[f"{col}_mine"].fillna(-1e9) == equal[f"{col}_theirs"].fillna(-1e9)).mean()
        print(f"  {col} identical on {ident:.6%}")

    default = join()
    print("\n--- at the DEFAULT tolerance: two kinds of disagreement, no third ---")
    print(f"  label agreement {(default['flow_state'] == default['state']).mean():.2%}")
    print(report.to_markdown(
        pd.crosstab(default["flow_state"], default["state"]).reset_index()))
    disagree = default[default["flow_state"] != default["state"]]
    print(f"\n  every disagreement is mine=mixed or mine=gap: "
          f"{sorted(set(disagree['flow_state']))}")
    committed = default[~default["flow_state"].isin(["mixed", "gap"])]
    print(f"  where I commit to a direction, agreement is "
          f"{(committed['flow_state'] == committed['state']).mean():.6%} "
          f"of {len(committed):,} rows")

    print("\n--- the oats rationale, which does NOT hold up ---")
    oats = vf.decompose(panel[panel["market_code"] == "004603"]).copy()
    oats["abs_net"] = oats["d_net"].abs()
    long_gap = oats[oats["days_elapsed"] > 200]
    ranks = sorted(oats["abs_net"].rank(ascending=False, method="min")[long_gap.index])
    print(f"  oats transitions: {len(oats):,}")
    print(f"  rows on the 294-day interval: {len(long_gap)}, "
          f"max |d_net| {long_gap['d_net'].abs().max():,.0f}")
    print(f"  their ranks within oats by |d_net|: {[int(r) for r in ranks]}")
    print(f"  oats max |d_net| on a normal (<=8d) interval: "
          f"{oats[oats['days_elapsed'] <= 8]['d_net'].abs().max():,.0f}")
    allgap = default[default["flow_state"] == "gap"]
    print(f"  panel-wide, max |d_net| cotdata reports on a >14d interval: "
          f"{allgap[allgap['days_elapsed'] > 14]['d_net_theirs'].abs().max():,.0f}")
    print(f"  panel-wide, max |d_net| on an ordinary week:              "
          f"{default[default['flow_state'] != 'gap']['d_net_theirs'].abs().max():,.0f}")
    print("\n  So the 294-day diff is not the largest flow in the panel, or even in oats.")
    print("  A market drops out BECAUSE it is thin, so its re-entry delta is small for the")
    print("  same reason it went missing. The gap rule survives on comparability, not size.")


def lumber_is_one_instrument() -> None:
    """Amendment B30: coverage keys on market_code, and lumber is one instrument in two.

    `coverage` solved the phantom problem (one code carrying several NAMES) by keying on
    `market_code`. The opposite failure is not handled and was not contemplated: one
    INSTRUMENT carrying several codes. The two markets the ladder reports as scoring
    nothing are the two halves of a single migrated contract, which `continuity` and
    `macro_pca.merge_migrated_codes` both know about and `coverage` does not.

    So the question is whether "2 of 27 score nothing" is a real finding or an artifact of
    the split. Answered by running the WHOLE pipeline, both halves, off a merged panel.
    """
    from crowdmon.futures import (
        ContractMaster,
        add_composite,
        add_extremity,
        add_notional,
        add_risk_units,
        add_volume,
        coverage_ladder,
        format_coverage,
        market_fragility,
        rank_markets,
    )

    rule("THE LUMBER MERGE: does the split cause the zero? (2026-08-02 B30)")
    old, new = "058643", "058644"
    sumkey = ["market_code", "report_type", "combined", "category", "report_date"]

    def merge_lumber(p):
        p = p.copy()
        p["market_code"] = p["market_code"].replace({old: new})
        num = [c for c in ("long_contracts", "short_contracts", "spread_contracts",
                           "trader_count_long", "trader_count_short") if c in p.columns]
        agg = {c: "sum" for c in num}
        # open_interest is the MARKET total repeated on every category row. Summing it is
        # the error this package guards against everywhere else; take the max.
        agg["open_interest"] = "max"
        agg["market_name"] = "first"
        return p.groupby(sumkey, as_index=False, dropna=False).agg(agg)

    def pipeline(panel):
        per_category = add_volume(add_extremity(add_risk_units(
            add_notional(ContractMaster.load().annotate(panel)))))
        vol = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
               .max().reset_index())
        per_market = market_fragility(panel).merge(
            vol, on=["report_date", "market_code"], how="left")
        ranked = rank_markets(per_market, volume=per_market["adv"],
                              stress_volume=per_market["adv_stress"])
        return per_category, add_composite(ranked, per_category)

    raw = from_current_store()
    lum = raw[raw["market_code"].isin([old, new])]
    print("\n--- the two codes are one instrument, sequential not concurrent ---")
    for code, g in lum.groupby("market_code"):
        print(f"  {code}  {g['report_date'].min().date()} to {g['report_date'].max().date()}"
              f"  weeks={g['report_date'].nunique():5d}  {g['market_name'].iloc[0][:38]}")
    a = set(lum[lum['market_code'] == old]["report_date"])
    b = set(lum[lum['market_code'] == new]["report_date"])
    print(f"  overlapping weeks: {len(a & b)} of {len(a | b)}, "
          f"and both carry contract symbol LBR")

    for label, panel in (("AS SHIPPED, codes separate", raw),
                         ("MERGED end to end", merge_lumber(raw))):
        per_cat, scored = pipeline(panel)
        lad = coverage_ladder(per_cat, scored)
        print(f"\n--- {label} ---")
        print(format_coverage(lad[lad["market_code"].isin([old, new])]))
        dead = int((lad["composite_percentile"] == 0).sum())
        print(f"  {dead} of {lad['market_code'].nunique()} markets score nothing; "
              f"lumber weeks with a non-null damage_sell: "
              f"{int(scored[scored['market_code'] == new]['damage_sell'].notna().sum())}")

    print("\n  Every rung rises and the verdict does not. price 37/178 -> 208,")
    print("  extremity_z 0/75 -> 96, illiquidity 0/75 -> 92, and `crowding` is 0 either")
    print("  way, because pct(z) stacks a second three-year window on top of the 96.")
    print("  The zero is a property of the instrument, not of the split. The headline")
    print("  moves from '2 of 27' to '1 of 26' purely by counting rows correctly.")


if __name__ == "__main__":
    main()
    normalisation()
    volume_and_exit_capacity()
    exit_cost()
    commonality()
    trigger_guard()
    vintage_coverage()
    constant_invariance()
    reflexivity()
    roll_dates_coverage()
    roll_windows()
    trend_alignment()
    correlation_clustering()
    coverage_ladder_report()
    macro_book_pca()
    template_shape()
    flow_equivalence()
    lumber_is_one_instrument()
