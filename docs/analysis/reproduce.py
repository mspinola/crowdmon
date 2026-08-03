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
  B31. the same template stratified by population and followed through all 82 weeks
  B33. Managed Money magnitude conditional on sign: absence, or symmetric swing?
  B34. the same asymmetry measured without a direction
  B35. swap-dealer share as a predictor of non-template status (it is not one)
  B36. stability, per-complex ordering, and whether the ag month profile repeats
  B37. the real market behind the appendix's replacement worked example
  B29. the two flow decompositions, and the oats rationale that does not hold
  B30. whether the lumber code split is what makes lumber unscoreable
  C12-C14. the contract-spec inventory: what is covered, whether it is usable, and what
       the 254 uncovered codes are actually made of
  C15. the head of the backlog is not a duplicate of CL and NG
  C16. why that test must use flows: positioning LEVELS correlate spuriously
  C17. prioritising the ag and dairy backlog, most of which fails the gate

The leading ordinals above are the order the blocks were added and have drifted: 17 and 18
each appear twice and there is no 19. Not renumbered here, because these numbers are quoted
by the analysis documents. New blocks are labelled by their amendment ID instead.
"""
import numpy as np
import pandas as pd

from crowdmon.core import config as cfg
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
    shape_labels,
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


#: Judgement, enumerated so it is auditable rather than asserted: contracts on a
#: deliverable physical underlying, traded as an OUTRIGHT rather than as a spread, a
#: basis, a crack or an index. This is the population appendix §A.2's cocoa example is
#: drawn from. The block below does NOT rest on it — the same finding is reproduced from
#: a venue-only split that involves no hand classification at all.
CLASSIC_OUTRIGHTS = {
    "002602": ("CORN", "grains/oilseeds"),
    "005602": ("SOYBEANS", "grains/oilseeds"),
    "005603": ("MINI SOYBEANS", "grains/oilseeds"),
    "026603": ("SOYBEAN MEAL", "grains/oilseeds"),
    "007601": ("SOYBEAN OIL", "grains/oilseeds"),
    "001602": ("WHEAT-SRW", "grains/oilseeds"),
    "001612": ("WHEAT-HRW", "grains/oilseeds"),
    "001626": ("WHEAT-HRSpring", "grains/oilseeds"),
    "004603": ("OATS", "grains/oilseeds"),
    "039601": ("ROUGH RICE", "grains/oilseeds"),
    "135731": ("CANOLA", "grains/oilseeds"),
    "073732": ("COCOA", "softs"),
    "083731": ("COFFEE C", "softs"),
    "033661": ("COTTON NO. 2", "softs"),
    "080732": ("SUGAR NO. 11", "softs"),
    "040701": ("FCOJ", "softs"),
    "057642": ("LIVE CATTLE", "livestock/dairy"),
    "061641": ("FEEDER CATTLE", "livestock/dairy"),
    "054642": ("LEAN HOGS", "livestock/dairy"),
    "052641": ("MILK CLASS III", "livestock/dairy"),
    "050642": ("BUTTER", "livestock/dairy"),
    "063642": ("CHEESE", "livestock/dairy"),
    "052642": ("NON FAT DRY MILK", "livestock/dairy"),
    "052645": ("DRY WHEY", "livestock/dairy"),
    "052644": ("CME MILK IV", "livestock/dairy"),
    "088691": ("GOLD", "metals"),
    "088695": ("MICRO GOLD", "metals"),
    "084691": ("SILVER", "metals"),
    "084694": ("MICRO SILVER", "metals"),
    "085692": ("COPPER #1", "metals"),
    "085699": ("MICRO COPPER", "metals"),
    "076651": ("PLATINUM", "metals"),
    "075651": ("PALLADIUM", "metals"),
    "191691": ("ALUMINUM", "metals"),
    "067651": ("WTI-PHYSICAL", "energy outright"),
    "06765A": ("WTI FINANCIAL", "energy outright"),
    "06765T": ("BRENT LAST DAY", "energy outright"),
    "067411": ("WTI ICE EUROPE", "energy outright"),
    "023651": ("NAT GAS NYMEX", "energy outright"),
    "03565B": ("HENRY HUB", "energy outright"),
    "022651": ("NY HARBOR ULSD", "energy outright"),
    "111659": ("GASOLINE RBOB", "energy outright"),
    "025651": ("ETHANOL", "energy outright"),
    "058644": ("LUMBER", "lumber"),
}
#: Venues whose listings are power, gas basis, carbon and RECs (2026-08-01 A5).
POWER_VENUES = {"ICE FUTURES ENERGY DIV", "NODAL EXCHANGE"}
#: Venues listing the ags and metals, used for the judgement-free robustness split.
AG_METAL_VENUES = {"CHICAGO BOARD OF TRADE", "CHICAGO MERCANTILE EXCHANGE",
                   "COMMODITY EXCHANGE INC.", "ICE FUTURES U.S.",
                   "MIAX FUTURES EXCHANGE"}


#: Display names for `fragility.SHAPE_KEYS` on the Disaggregated pair, as B28 and B31 quote
#: them. The classification itself lives in the package: it was written twice, here and in
#: `reproduce_tff.py`, which is the duplication B29 is about, so it is now one function with
#: two label maps.
DISAGG_SHAPE_LABELS = {
    "fragile_long": "template (PM short, MM long)",
    "fragile_short": "inverted (PM long, MM short)",
    "both_short": "same side (both short)",
    "both_long": "same side (both long)",
    "fragile_flat": "MM net flat",
    "no_stable_side": "no hedger side (PM flat)",
}


def _shape_labels(pm: pd.Series, mm: pd.Series) -> pd.Series:
    """The six outcomes of the Producer/Merchant x Managed Money pair, named as B28 does."""
    return shape_labels(pm, mm, labels=DISAGG_SHAPE_LABELS)


def _shape_panel() -> pd.DataFrame:
    """One row per (report_date, market_code): category nets, stratum, and shape.

    Also carries per-category GROSS (`gross_<category>`), the market's open interest, and
    the two directional Q totals, because the B33-B36 blocks need magnitudes rather than
    only signs. Open interest is taken with `max` and never `sum`: it is the market total
    repeated on every category row, so summing it multiplies it by five and silently
    divides every ratio built on it.
    """
    full = from_vintage()
    full = full.assign(net=full["long_contracts"] - full["short_contracts"],
                       gross=full["long_contracts"] + full["short_contracts"])
    n = (full.groupby(["report_date", "market_code", "category"])["net"].sum()
             .unstack("category").reset_index())
    gross = (full.groupby(["report_date", "market_code", "category"])["gross"].sum()
                 .unstack("category").rename(columns=lambda c: f"gross_{c}").reset_index())
    n = n.merge(gross, on=["report_date", "market_code"], how="left")
    n = n.merge(full.groupby(["report_date", "market_code"])["open_interest"].max()
                    .rename("oi").reset_index(),
                on=["report_date", "market_code"], how="left")
    w = cfg.weights_for("disaggregated")
    n["q_sell"] = sum(w[c] * n[c].clip(lower=0) for c in w)
    n["q_buy"] = sum(w[c] * (-n[c]).clip(lower=0) for c in w)
    n["market_name"] = n["market_code"].map(full.groupby("market_code")["market_name"].first())
    n["venue"] = n["market_name"].str.rsplit(" - ", n=1).str[-1]
    n["complex"] = n["market_code"].map(lambda c: CLASSIC_OUTRIGHTS.get(c, (None, None))[1])
    n["stratum"] = np.where(
        n["market_code"].isin(CLASSIC_OUTRIGHTS), "1 classic outright",
        np.where(n["venue"].isin(POWER_VENUES), "3 power/gas/carbon venue",
                 "2 spread/basis/regional"))
    n["venue_stratum"] = np.where(
        n["venue"].isin(AG_METAL_VENUES), "ag/metal exchange",
        np.where(n["venue"].isin(POWER_VENUES), "power/gas venue", "other venue"))
    n["shape"] = _shape_labels(n["producer_merchant"], n["managed_money"])
    return n


def _share_table(frame: pd.DataFrame, by: str) -> pd.DataFrame:
    """Row-percentage crosstab of shape, rendered as `%` strings.

    Formatted here rather than left as floats because `report.to_markdown` picks a format
    per column for contract counts, and a column of shares reads as `52.5000`.
    """
    ct = pd.crosstab(frame[by], frame["shape"])
    pct = (ct.div(ct.sum(axis=1), axis=0) * 100).map(lambda v: f"{v:.1f}%")
    return pct.assign(**{"market-weeks": ct.sum(axis=1)}).reset_index()


def template_shape_stratified() -> None:
    """Amendment B31: B28's 27.2% is a population average over a universe that is 76% power.

    B28 measured the cocoa template as a joint shape rather than two margins, which was the
    right correction, and reported it over all 279 markets of one week. Two things that
    changes: the universe it averages over is three-quarters ICE power and gas basis
    (2026-08-01 A5), which is not the population §A.2's example is drawn from, and one week
    cannot say whether a market's shape is a property of the market or of the week.

    Both are answered here over the vintage store's full 82 weeks. Nothing below rests on
    the hand-drawn `CLASSIC_OUTRIGHTS` list: the venue-only split reproduces it.
    """
    rule("THE COCOA TEMPLATE, STRATIFIED AND THROUGH TIME (2026-08-02 B31)")

    n = _shape_panel()
    weeks = sorted(n["report_date"].unique())
    last = weeks[-1]
    print(f"\n{len(weeks)} report weeks, {pd.Timestamp(weeks[0]).date()} to "
          f"{pd.Timestamp(last).date()}, {n['market_code'].nunique()} markets, "
          f"{len(n):,} market-weeks")

    print("\n--- 1. the joint shape by stratum, LATEST WEEK (B28's population, split) ---")
    print(report.to_markdown(_share_table(n[n["report_date"] == last], "stratum")))
    print("\n--- 2. the same, over all 82 weeks rather than one ---")
    print(report.to_markdown(_share_table(n, "stratum")))

    # The hand-drawn list is the obvious place for this to be leaning, so check it against
    # a split that contains no per-contract judgement whatsoever.
    print("\n--- 3. ROBUSTNESS: venue only, no hand classification of any contract ---")
    print(report.to_markdown(_share_table(n, "venue_stratum")))
    pw = n.pivot_table(index="report_date", columns="venue_stratum", values="shape",
                       aggfunc=lambda s: (s == "template (PM short, MM long)").mean())
    d = pw["ag/metal exchange"] - pw["power/gas venue"]
    print(f"\n  ag/metal template share exceeds power/gas in {int((d > 0).sum())} of "
          f"{len(d)} weeks, median gap {d.median():+.3f}, smallest gap {d.min():+.3f}.")
    print("  Paired by week, so the 82 weeks are not being treated as independent draws.")

    print("\n--- 4. inside the classic outrights, by complex, all 82 weeks ---")
    cl = n[n["market_code"].isin(CLASSIC_OUTRIGHTS)]
    print(report.to_markdown(_share_table(cl, "complex")))

    print("\n--- 5. which HALF of the template fails ---")
    rows = []
    for label, sub in [("classic outright", cl),
                       ("power/gas venue", n[n["venue"].isin(POWER_VENUES)])]:
        pm_short = (sub["producer_merchant"] < 0).mean()
        mm_long = (sub["managed_money"] > 0).mean()
        rows.append({"stratum": label, "market-weeks": len(sub),
                     "PM net short": f"{pm_short:.1%}", "MM net long": f"{mm_long:.1%}",
                     "both (the template)":
                         f"{((sub['producer_merchant'] < 0) & (sub['managed_money'] > 0)).mean():.1%}",
                     "if independent": f"{pm_short * mm_long:.1%}"})
    print(report.to_markdown(pd.DataFrame(rows)))
    print("\n  The hedged short side is the robust half. The fragile levered long side is")
    print("  the half that only holds half the time, and it is the half the thesis needs.")

    print("\n--- 6. is shape a property of the MARKET or of the WEEK? ---")
    g = n.groupby("market_code")
    mkt = pd.DataFrame({
        "stratum": g["stratum"].first(), "weeks": g.size(),
        "tf": g["shape"].apply(lambda s: (s == "template (PM short, MM long)").mean())})
    mkt = mkt[mkt["weeks"] >= 40]
    band = pd.cut(mkt["tf"], bins=[-.001, .1, .25, .5, .75, .9, 1.001],
                  labels=["never <=10%", "10-25%", "25-50%", "50-75%", "75-90%",
                          "always >=90%"])
    ct = pd.crosstab(mkt["stratum"], band)
    print(report.to_markdown((ct.div(ct.sum(axis=1), axis=0) * 100)
                             .map(lambda v: f"{v:.1f}%")
                             .assign(markets=ct.sum(axis=1)).reset_index()))
    extreme = ((mkt["tf"] <= .1) | (mkt["tf"] >= .9)).mean()
    print(f"\n  {extreme:.1%} of the {len(mkt)} markets with >=40 weeks sit at one extreme")
    print("  or the other. The universe is not 27% template-shaped; it is a mixture of")
    print("  markets that essentially always are and markets that essentially never are.")

    tfc = mkt[mkt["stratum"] == "1 classic outright"]["tf"].sort_values(ascending=False)
    print("\n  classic outrights that are ALWAYS template (>=90% of weeks):")
    for code in tfc[tfc >= .9].index:
        print(f"    {tfc[code]:.3f}  {CLASSIC_OUTRIGHTS[code][0]:<18s} "
              f"{CLASSIC_OUTRIGHTS[code][1]}")
    print("\n  classic outrights that are NEVER template (<=10% of weeks):")
    for code in tfc[tfc <= .1].sort_values().index:
        print(f"    {tfc[code]:.3f}  {CLASSIC_OUTRIGHTS[code][0]:<18s} "
              f"{CLASSIC_OUTRIGHTS[code][1]}")

    print("\n--- 7. COCOA itself, every week the store holds ---")
    c = n[n["market_code"] == "073732"].set_index("report_date").sort_index()
    cats = ["producer_merchant", "swap", "managed_money", "other_reportable",
            "nonreportable"]
    print(f"  shapes: {c['shape'].value_counts().to_dict()}")
    print(f"  PM net short in {int((c['producer_merchant'] < 0).sum())} of {len(c)} weeks; "
          f"MM net long in {int((c['managed_money'] > 0).sum())}, "
          f"net short in {int((c['managed_money'] < 0).sum())}")
    longs = c[cats].where(c[cats] > 0)
    print(f"  largest NET LONG holder, by week: {longs.idxmax(axis=1).value_counts().to_dict()}")
    print("\n  first, middle and last week (contracts, net):")
    for d0 in [c.index[0], c.index[len(c) // 2], c.index[-1]]:
        row = c.loc[d0]
        print(f"    {pd.Timestamp(d0).date()}  " +
              "  ".join(f"{k[:4]} {int(row[k]):>+8,}" for k in cats) +
              f"   [{row['shape']}]")
    print("\n  §A.2 puts Swap Dealer at +10,000 against Managed Money +90,000. Real cocoa")
    print("  in the latest week is Swap Dealer +22,894 against Managed Money -8,773: the")
    print("  long side is an index/swap book, not a levered fund.")

    print("\n--- 8. the asymmetry is bounded by the WEIGHT TABLE, not by the data ---")
    w = cfg.weights_for("disaggregated")
    ceiling = max(w.values()) / min(w.values())
    print(f"  weights {w}")
    print("  Sum_c P_c = 0, so the gross net-long total G equals the gross net-short total.")
    print("  Q_sell <= max(w)*G and Q_buy >= min(w)*G, hence Q_sell/Q_buy <= max(w)/min(w)")
    print(f"  = {ceiling:.1f}. Checked rather than argued:")
    con = contributions(from_vintage())
    q = (con.groupby(["report_date", "market_code", "q_side"])["q_contribution"].sum()
           .unstack("q_side").fillna(0.0))
    ratio = (q["sell"] / q["buy"].replace(0, np.nan)).dropna()
    print(f"    {len(ratio):,} market-weeks with both sides live, max observed "
          f"{ratio.max():.4f}, breaches of {ceiling:.1f}: "
          f"{int((ratio > ceiling + 1e-9).sum())}")
    print(f"    median {ratio.median():.3f}, p90 {ratio.quantile(.9):.3f}, "
          f"p99 {ratio.quantile(.99):.3f}")
    print(f"    at or above the appendix's 9.045: {int((ratio >= 9.045).sum())} market-weeks")
    print(f"\n  So §A.2's 9.05x is {9.045 / ceiling:.1%} of the mechanical ceiling, not an")
    print("  empirical extreme, and the median market-week is 0.993 — no asymmetry at all.")


def _spearman(a: pd.Series, b: pd.Series) -> float:
    """Rank correlation, computed as Pearson on ranks.

    Not `Series.corr(method="spearman")`, which imports `scipy`. `tests/test_boundaries.py`
    allowlists `pandas`, `numpy` and `pyarrow` only, so a reproducer that needed scipy would
    be printing figures the package itself is forbidden to compute.
    """
    return float(a.rank().corr(b.rank()))


def template_conditional_magnitude() -> None:
    """Amendment B33: the Managed Money coin flip is a coin flip in SIGN, not in size.

    B31 measured Managed Money net long in 50.0% of classic-outright market-weeks and read
    it as the half of the template that fails. A frequency admits two opposite readings:
    the fund is small and directionless (the fragility argument genuinely fails), or it
    swings between large long and large short (the market is fragile and the template
    merely names the wrong direction half the time). Magnitude conditional on sign is what
    separates them, and B31 did not measure it.
    """
    rule("MANAGED MONEY MAGNITUDE, CONDITIONAL ON SIGN (2026-08-02 B33)")

    n = _shape_panel()
    cl = n[n["stratum"] == "1 classic outright"].copy()
    w = cfg.weights_for("disaggregated")
    cl["abs_over_oi"] = cl["managed_money"].abs() / cl["oi"]
    cl["q_gross"] = cl["q_sell"] + cl["q_buy"]
    cl["mm_over_q"] = w["managed_money"] * cl["managed_money"].abs() / cl["q_gross"]
    print(f"\n{len(cl):,} classic-outright market-weeks, "
          f"{cl['market_code'].nunique()} markets, {cl['report_date'].nunique()} weeks")
    print("  `Q_total` here is `q_gross = Q_sell + Q_buy`, the name the code already gives")
    print("  the combined figure. It is a DENOMINATOR and never a flow: forced longs sell")
    print("  and forced shorts buy, so the sum describes an event that cannot happen.")

    rows = []
    for label, sub in [("P_MM > 0 (net long)", cl[cl["managed_money"] > 0]),
                       ("P_MM < 0 (net short)", cl[cl["managed_money"] < 0]),
                       ("P_MM = 0 (net flat)", cl[cl["managed_money"] == 0]),
                       ("unconditional", cl)]:
        a, m = sub["abs_over_oi"], sub["mm_over_q"]
        rows.append({
            "conditional on": label, "market-weeks": len(sub),
            "|P|/OI median": f"{a.median():.4f}",
            "|P|/OI IQR": f"{a.quantile(.25):.4f} - {a.quantile(.75):.4f}",
            "w|P|/Q_total median": f"{m.median():.4f}",
            "w|P|/Q_total IQR": f"{m.quantile(.25):.4f} - {m.quantile(.75):.4f}"})
    print("\n--- 1. |P_MM| / OI and the fragility contribution, by sign ---")
    print(report.to_markdown(pd.DataFrame(rows)))

    print("\n--- 2. how much of the book is 'directionless', at three thresholds ---")
    print("  The 0.05 cut is a judgement. It is stated rather than hidden, and the two")
    print("  neighbouring cuts are printed so the reading does not rest on it.")
    for thr in (0.02, 0.05, 0.10):
        hit = cl["abs_over_oi"] < thr
        print(f"    |P_MM|/OI < {thr:.2f}: {hit.mean():>6.1%}  ({int(hit.sum()):,} of "
              f"{len(cl):,})")

    print("\n--- 3. the same by complex, since the template rate already varies sharply ---")
    rows = []
    for cx, sub in cl.groupby("complex"):
        lo = sub[sub["managed_money"] > 0]["abs_over_oi"]
        sh = sub[sub["managed_money"] < 0]["abs_over_oi"]
        rows.append({"complex": cx, "market-weeks": len(sub),
                     "MM net long": f"{(sub['managed_money'] > 0).mean():.1%}",
                     "|P|/OI med, long": f"{lo.median():.4f}",
                     "|P|/OI med, short": f"{sh.median():.4f}",
                     "< 5% of OI": f"{(sub['abs_over_oi'] < .05).mean():.1%}",
                     "w|P|/Q_total med": f"{sub['mm_over_q'].median():.4f}"})
    print(report.to_markdown(pd.DataFrame(rows)))

    print("\n--- 4. the verdict: absence, or symmetric swing? Neither, exactly ---")
    for label, sub in [("classic outright", cl),
                       ("power/gas venue", n[n["venue"].isin(POWER_VENUES)])]:
        lo = sub.loc[sub["managed_money"] > 0, "managed_money"]
        sh = sub.loc[sub["managed_money"] < 0, "managed_money"].abs()
        print(f"    {label:<18s} weeks net long {(sub['managed_money'] > 0).mean():>6.1%}   "
              f"CONTRACTS on the long side {lo.sum() / (lo.sum() + sh.sum()):>6.1%}")
    print("  Half the weeks, but nearly two thirds of the contracts. The sign is a coin")
    print("  flip and the size is not.")

    per = cl.groupby("market_code")["managed_money"].apply(lambda s: (s > 0).mean())
    print(f"\n    per-market net-long rate over 82 weeks, {len(per)} markets: "
          f"<=10% {int((per <= .1).sum())}, middle {int(((per > .1) & (per < .9)).sum())}, "
          f">=90% {int((per >= .9).sum())}")
    print("  So the 50.0% is not a market that flips; it is a universe of markets that")
    print("  mostly do not, split roughly evenly between the two directions. Same mixture")
    print("  structure B31 found for the template itself, one level down.")


def template_direction_agnostic() -> None:
    """Amendment B34: the median asymmetry of 0.993 is direction cancelling, not symmetry.

    The template as specified encodes a direction. What the thesis needs is a levered
    concentration on SOME side that can be forced out, opposed by one that cannot; which
    side is incidental. Measured direction-agnostically, both B31's headline figures move.
    """
    rule("DIRECTION-AGNOSTIC ASYMMETRY (2026-08-02 B34)")

    w = cfg.weights_for("disaggregated")
    ceiling = max(w.values()) / min(w.values())
    con = contributions(from_vintage())
    q = (con.groupby(["report_date", "market_code", "q_side"])["q_contribution"].sum()
           .unstack("q_side").fillna(0.0))
    q = q[(q["sell"] > 0) & (q["buy"] > 0)].reset_index()
    q["a_dir"] = q["sell"] / q["buy"]
    q["a_agn"] = (np.maximum(q["sell"], q["buy"]) / np.minimum(q["sell"], q["buy"]))
    q["classic"] = q["market_code"].isin(CLASSIC_OUTRIGHTS)
    print(f"\n{len(q):,} market-weeks with both sides live. Ceiling max(w)/min(w) = "
          f"{ceiling:.1f}")
    print("    A_directional = Q_sell / Q_buy")
    print("    A_agnostic    = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)")

    rows = []
    for label, sub in [("classic outright", q[q["classic"]]),
                       ("everything else", q[~q["classic"]]),
                       ("all", q)]:
        rows.append({
            "stratum": label, "market-weeks": len(sub),
            "A_dir median": f"{sub['a_dir'].median():.4f}",
            "A_agn median": f"{sub['a_agn'].median():.4f}",
            "A_agn p90": f"{sub['a_agn'].quantile(.9):.3f}",
            "A_agn max": f"{sub['a_agn'].max():.4f}",
            "of ceiling (median)": f"{sub['a_agn'].median() / ceiling:.1%}",
            "breaches": int((sub["a_agn"] > ceiling + 1e-9).sum())})
    print("\n--- 1. the two ratios side by side ---")
    print(report.to_markdown(pd.DataFrame(rows)))

    print("\n--- 2. why the directional median sits at 1, and it is not symmetry ---")
    print(f"    Q_sell is the larger side in {(q['sell'] > q['buy']).mean():.1%} of all "
          f"market-weeks,")
    print(f"    and in {(q[q['classic']]['sell'] > q[q['classic']]['buy']).mean():.1%} of "
          f"classic outrights.")
    print(f"    market-weeks that are genuinely near-symmetric (A_agn < 1.1): "
          f"{(q['a_agn'] < 1.1).mean():.1%} of all, "
          f"{(q[q['classic']]['a_agn'] < 1.1).mean():.1%} of classic outrights.")
    print("  A median of 0.993 on the SIGNED ratio is a coin flip about which side is")
    print("  bigger, landing on 1 the way a mean of two opposite numbers does. Under 5% of")
    print("  market-weeks actually have the two sides within 10% of each other.")

    print("\n--- 3. the shape table, and what reclassifies ---")
    n = _shape_panel()
    cl = n[n["stratum"] == "1 classic outright"]
    share = cl["shape"].value_counts(normalize=True)
    # Formatted as strings for the same reason `_share_table` does it: `to_markdown` picks
    # a format per column for contract counts, and a column of shares reads as `44.7000`.
    print(report.to_markdown(share.map(lambda v: f"{v:.1%}")
                                  .rename("% of market-weeks").reset_index()))
    opposed = cl["shape"].isin(["template (PM short, MM long)",
                                "inverted (PM long, MM short)"])
    tmpl = (cl["shape"] == "template (PM short, MM long)").mean()
    print(f"\n    directional template          {tmpl:.1%}")
    print(f"    + inverted, which reclassifies {share.get('inverted (PM long, MM short)', 0):.1%}")
    print(f"    = opposed, either direction    {opposed.mean():.1%}")
    print("  Every inverted market-week reclassifies: it is the same configuration with")
    print("  the fragile fund short and the hedger long, so the forced flow is buying")
    print("  rather than selling. That is B32's TFF finding appearing inside Disaggregated.")

    print("\n--- 4. the ceiling caveat, carried as B31 carried it ---")
    print(f"    appendix §A.2 sits at 9.045 = {9.045 / ceiling:.1%} of the ceiling.")
    print(f"    percentile of 9.045 within classic outrights: "
          f"{(q[q['classic']]['a_dir'] <= 9.045).mean():.2%}, "
          f"whole universe {(q['a_dir'] <= 9.045).mean():.3%}")
    print("  A_agnostic carries exactly the same bound, since it is the same two sums with")
    print("  the larger on top, so nothing here escapes the weight table.")

    # B31 says the market-weeks reaching 9.045 are "all gas basis, power or
    # crude-differential markets rather than outrights". Enumerated rather than glanced at.
    print("\n--- 5. WHICH market-weeks reach the appendix's 9.045, enumerated ---")
    hi = q[q["a_dir"] >= 9.045].copy()
    hi["market_name"] = hi["market_code"].map(
        from_vintage().groupby("market_code")["market_name"].first())
    tally = (hi.groupby(["classic", "market_code", "market_name"]).size()
               .rename("market-weeks").reset_index()
               .sort_values(["classic", "market-weeks"], ascending=[True, False]))
    print(report.to_markdown(tally))
    print(f"\n    {len(hi)} market-weeks in {hi['market_code'].nunique()} markets; "
          f"{int(hi['classic'].sum())} of them are CLASSIC OUTRIGHTS.")
    print("  B31 says all of them are gas basis, power or crude differentials. The count is")
    print("  right and the characterisation is not: copper, RBOB, canola, coffee and spring")
    print("  wheat all reach it, and so does COMEX steel, which is none of the three.")


def template_swap_share() -> None:
    """Amendment B35: swap-dealer prominence does not predict non-template status.

    The hypothesis, from the handoff and worth testing rather than assuming: cocoa's largest
    net long is the Swap Dealer, crude and gas have heavy swap intermediation and are never
    template, so swap books may be displacing Managed Money on the long side and suppressing
    the shape. It is a clean hypothesis and the data does not support it.
    """
    rule("SWAP-DEALER SHARE AS A PREDICTOR OF NON-TEMPLATE STATUS (2026-08-02 B35)")

    n = _shape_panel()
    n["is_template"] = n["shape"] == "template (PM short, MM long)"
    n["swap_share"] = n["gross_swap"] / (2 * n["oi"])
    cl = n[n["stratum"] == "1 classic outright"]
    print("\n    swap_share = (L_SD + S_SD) / (2 . OI), the same gross-over-2.OI form Phi")
    print("    uses, averaged over each market's weeks.")

    mkt = cl.groupby("market_code").agg(
        swap_share=("swap_share", "mean"), template=("is_template", "mean"),
        weeks=("is_template", "size"), complex=("complex", "first"))
    mkt = mkt[mkt["weeks"] >= 40]
    print(f"\n--- 1. across {len(mkt)} classic-outright markets with >= 40 weeks ---")
    print(f"    pearson  {mkt['swap_share'].corr(mkt['template']):+.3f}")
    print(f"    spearman {_spearman(mkt['swap_share'], mkt['template']):+.3f}")

    print("\n--- 2. within complex, since complex is the obvious confound ---")
    rows = []
    for cx, sub in mkt.groupby("complex"):
        rows.append({"complex": cx, "markets": len(sub),
                     "swap_share mean": f"{sub['swap_share'].mean():.3f}",
                     "template mean": f"{sub['template'].mean():.3f}",
                     "pearson": "n/a" if len(sub) < 4
                     else f"{sub['swap_share'].corr(sub['template']):+.3f}",
                     "spearman": "n/a" if len(sub) < 4
                     else f"{_spearman(sub['swap_share'], sub['template']):+.3f}"})
    print(report.to_markdown(pd.DataFrame(rows)))
    print("  The sign is not stable across complexes: metals positive, livestock and energy")
    print("  negative. A relationship that reverses inside the strata is not a relationship.")

    print("\n--- 3. does it separate the always-template set from the never-template set? ---")
    always = ["088691", "084691", "085692", "057642", "061641", "083731", "111659"]
    never = ["03565B", "067651", "06765A", "067411", "052642", "052644", "001602", "039601"]
    rows = []
    for label, codes in [("always template", always), ("never template", never)]:
        for code in codes:
            if code in mkt.index:
                rows.append({"set": label, "market": CLASSIC_OUTRIGHTS[code][0],
                             "complex": CLASSIC_OUTRIGHTS[code][1],
                             "swap_share": f"{mkt.loc[code, 'swap_share']:.3f}",
                             "template rate": f"{mkt.loc[code, 'template']:.3f}"})
    print(report.to_markdown(pd.DataFrame(rows)))
    a = mkt.loc[[c for c in always if c in mkt.index], "swap_share"]
    b = mkt.loc[[c for c in never if c in mkt.index], "swap_share"]
    print(f"\n    always-template swap share: mean {a.mean():.3f}, "
          f"range {a.min():.3f} to {a.max():.3f}")
    print(f"    never-template  swap share: mean {b.mean():.3f}, "
          f"range {b.min():.3f} to {b.max():.3f}")
    print("  The two means are the same to three decimals and the ranges nest. The single")
    print("  heaviest swap book in the classic universe is HENRY HUB (never template) and")
    print("  the second is GOLD (always template).")

    print("\n--- 4. two robustness checks the hypothesis could still have survived ---")
    allm = n.groupby("market_code").agg(
        swap_share=("swap_share", "mean"), template=("is_template", "mean"),
        weeks=("is_template", "size"), stratum=("stratum", "first"))
    allm = allm[allm["weeks"] >= 40]
    print(f"    (a) all {len(allm)} markets with >= 40 weeks, not only the 39 outrights:")
    print(f"        pooled spearman {_spearman(allm['swap_share'], allm['template']):+.3f}")
    for st, sub in allm.groupby("stratum"):
        print(f"          {st:<26s} n={len(sub):>3}  "
              f"spearman {_spearman(sub['swap_share'], sub['template']):+.3f}")
    d = cl.copy()
    d["sw"] = d["swap_share"] - d.groupby("market_code")["swap_share"].transform("mean")
    d["tp"] = (d["is_template"].astype(float)
               - d.groupby("market_code")["is_template"].transform("mean"))
    print("    (b) within market, week to week (both series demeaned per market):")
    print(f"        pearson {d['sw'].corr(d['tp']):+.3f} over {len(d):,} market-weeks")
    print("  A high-swap WEEK is no less template than that market's own average either.")

    print("\n--- 5. the CIT supplemental report, which would test the index-flow reading ---")
    import os
    import pathlib

    root = pathlib.Path(os.environ["COTDATA_STORE"])
    domains = sorted(p.name for p in root.iterdir()
                     if p.is_dir() and p.name.startswith("cot_"))
    print(f"    store COT domains: {domains}")
    print("    No CIT / supplemental domain is ingested, so whether the swap book in the")
    print("    ags is index flow rather than levered flow cannot be tested here. Not")
    print("    fetched in this session, per the handoff. It would sharpen the weighting")
    print("    question and it cannot rescue the hypothesis: the correlation is absent")
    print("    before any question about what the swap book contains.")


def template_stability() -> None:
    """Amendment B36: the level is stable, the per-market classification is not, and the
    apparent ag seasonality does not repeat across the only two years available.

    B31's 82-of-82 consistency is about the GAP between ag/metal and power/gas venues. That
    is a different claim from stability of the level, of the per-complex ordering, or of a
    market's own classification, and 82 weeks is 1.6 years: enough to observe a seasonal
    pattern, not enough to separate one from a trend. This block says which of those the
    data supports.
    """
    rule("STABILITY AND SEASONALITY ACROSS THE 82 WEEKS (2026-08-02 B36)")

    n = _shape_panel()
    n["is_template"] = n["shape"] == "template (PM short, MM long)"
    cl = n[n["stratum"] == "1 classic outright"].copy()

    print("\n--- 1. the classic-outright template rate as a weekly series ---")
    wk = cl.groupby("report_date")["is_template"].mean()
    x = np.arange(len(wk))
    slope, _ = np.polyfit(x, wk.to_numpy(), 1)
    r2 = float(np.corrcoef(x, wk.to_numpy())[0, 1] ** 2)
    print(f"    {len(wk)} weeks: mean {wk.mean():.3f}, sd {wk.std():.4f}, "
          f"range {wk.min():.3f} to {wk.max():.3f}")
    print(f"    linear fit {slope:+.5f}/week = {slope * 52:+.3f}/year, R^2 {r2:.3f}")
    print(f"    first half {wk.iloc[:41].mean():.3f}  ->  second half {wk.iloc[41:].mean():.3f}")
    print("    every fourth week, so the series can be eyeballed rather than trusted:")
    for i, (d, v) in enumerate(wk.items()):
        if i % 4 == 0:
            print(f"      {pd.Timestamp(d).date()}  {v:.3f}")
    print("  A flat level with no trend worth naming. 82 points do not support more model")
    print("  than a straight line, and the straight line explains 2.6% of the variation.")

    print("\n--- 2. per-complex weekly rates, and whether the ordering holds ---")
    cw = cl.pivot_table(index="report_date", columns="complex", values="is_template",
                        aggfunc="mean")
    rows = [{"complex": c, "mean": f"{cw[c].mean():.3f}", "min": f"{cw[c].min():.3f}",
             "max": f"{cw[c].max():.3f}",
             "weeks ranked top": int((cw.rank(axis=1, ascending=False)[c] == 1).sum())}
            for c in cw.columns]
    print(report.to_markdown(pd.DataFrame(rows)))
    print(f"\n    metals > livestock/dairy in "
          f"{int((cw['metals'] > cw['livestock/dairy']).sum())} of {len(cw)} weeks")
    print(f"    metals > grains/oilseeds in "
          f"{int((cw['metals'] > cw['grains/oilseeds']).sum())} of {len(cw)} weeks")
    print("  B31's metals-first ordering holds against livestock every week and against")
    print("  grains in about four weeks in five. It is not a ranking that inverts.")

    print("\n--- 3. seasonality, which is the way this ordering could be misleading ---")
    ag = cl[cl["complex"].isin(["grains/oilseeds", "livestock/dairy", "softs"])].copy()
    nag = cl[cl["complex"].isin(["metals", "energy outright"])].copy()
    for frame in (ag, nag):
        frame["month"] = pd.to_datetime(frame["report_date"]).dt.month
        frame["year"] = pd.to_datetime(frame["report_date"]).dt.year
    bym = ag.groupby("month")["is_template"].agg(["mean", "size"])
    bym["non-ag control"] = nag.groupby("month")["is_template"].mean()
    print("    Calendar month, not week of year: B6 measured that a fixed point in the crop")
    print("    calendar drifts +/-1 week against any weekly index, so a weekly profile is")
    print("    smeared by construction. Month is the finest bucket 82 weeks can support.")
    print(report.to_markdown(
        bym.rename(columns={"mean": "ag+softs+livestock", "size": "market-weeks"})
           .round(3).reset_index()))
    print(f"    ag spread max-min {bym['mean'].max() - bym['mean'].min():.3f} "
          f"(peak month {bym['mean'].idxmax()}, trough {bym['mean'].idxmin()}), "
          f"non-ag control "
          f"{bym['non-ag control'].max() - bym['non-ag control'].min():.3f}")

    print("\n--- 4. and the check that settles it: does the profile REPEAT? ---")
    piv = ag.pivot_table(index="month", columns="year", values="is_template",
                         aggfunc="mean")
    both = piv.dropna()
    piv2 = nag.pivot_table(index="month", columns="year", values="is_template",
                           aggfunc="mean").dropna()
    print(report.to_markdown(both.round(3).rename(columns=str).reset_index()))
    print(f"    correlation across the {len(both)} months present in BOTH years: "
          f"{both[2025].corr(both[2026]):+.3f}   (non-ag control "
          f"{piv2[2025].corr(piv2[2026]):+.3f})")
    print(f"    2025 range over those months {both[2025].max() - both[2025].min():.3f}, "
          f"2026 range {both[2026].max() - both[2026].min():.3f}")
    print(f"    mean level 2025 {both[2025].mean():.3f} vs 2026 {both[2026].mean():.3f}")
    weeks = (cl.assign(month=pd.to_datetime(cl["report_date"]).dt.month,
                       year=pd.to_datetime(cl["report_date"]).dt.year)
               .pivot_table(index="month", columns="year", values="report_date",
                            aggfunc="nunique").fillna(0).astype(int))
    print("\n    report weeks per month, by year:")
    print(report.to_markdown(weeks.rename(columns=str).reset_index()))
    print("  Months 8 to 12 exist in ONE year. The apparent trough is five months of 2025")
    print("  with nothing to compare against, and where the two years do overlap they")
    print("  disagree: the correlation is negative and the whole amplitude comes from 2026.")
    print("  So the monthly profile is a single year's path wearing month labels. This is")
    print("  the coverage limit stated, not a seasonal estimate.")

    print("\n--- 5. does a market's own classification hold across the window? ---")
    mid = cl["report_date"].median()
    h1 = cl[cl["report_date"] <= mid].groupby("market_code")["is_template"].mean()
    h2 = cl[cl["report_date"] > mid].groupby("market_code")["is_template"].mean()
    per = cl.groupby("market_code")["is_template"].agg(["mean", "size"])
    per = per[per["size"] >= 40]
    halves = pd.DataFrame({"h1": h1, "h2": h2}).loc[per.index].dropna()
    halves["move"] = (halves["h2"] - halves["h1"]).abs()
    print(f"    |second half - first half| over {len(halves)} markets: "
          f"median {halves['move'].median():.3f}")
    for thr in (0.10, 0.25, 0.50):
        print(f"      moves more than {thr:.2f}: {int((halves['move'] > thr).sum())}")
    print("\n    the ten largest moves:")
    for code, row in halves.sort_values("move", ascending=False).head(10).iterrows():
        print(f"      {CLASSIC_OUTRIGHTS[code][0]:<18s} {row['h1']:.3f} -> {row['h2']:.3f} "
              f"({row['h2'] - row['h1']:+.3f})")
    stable = halves[((halves["h1"] <= .1) & (halves["h2"] <= .1))
                    | ((halves["h1"] >= .9) & (halves["h2"] >= .9))]
    full = int(((per["mean"] <= .1) | (per["mean"] >= .9)).sum())
    print(f"\n    extreme over the FULL window: {full} of {len(per)} markets")
    print(f"    extreme in BOTH halves separately: {len(stable)} of {len(halves)}")
    print("    the stable core, which is what B31's mixture reading is entitled to:")
    for code, row in stable.sort_values("h1").iterrows():
        print(f"      {CLASSIC_OUTRIGHTS[code][0]:<18s} {row['h1']:.3f} / {row['h2']:.3f}")
    print("  B31's mixture survives, smaller than it looked. Pooling 82 weeks pushes a")
    print("  market that was extreme in one half and middling in the other into an extreme")
    print("  bucket, and cocoa is the clearest case: 0.976 then 0.100.")


def appendix_a2_worked_example() -> None:
    """Amendment B37: the numbers behind §A.2's replacement worked example.

    The appendix's constructed cocoa table is retained there as an explicit extreme. This
    prints the real market that now carries the worked thread through §A.2, §A.5, §A.7 and
    §A.9, and the two measurements behind choosing it.
    """
    from crowdmon.core import impact as core_impact
    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_volume,
        exit_pressure,
        trigger_block,
    )
    from crowdmon.futures import trigger as trig

    rule("THE REAL MARKET BEHIND APPENDIX §A.2 (2026-08-02 B37)")

    code, symbol = "057642", "LE"
    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    week = panel["report_date"].max()
    cur = panel[panel["report_date"] == week]
    market = cur[cur["market_code"] == code]

    print("\n--- 1. why LIVE CATTLE and not GOLD, which the handoff also offered ---")
    for c, label in [("088691", "GOLD"), ("057642", "LIVE CATTLE")]:
        sub = cur[cur["market_code"] == c]
        con = contributions(sub).sort_values("q_contribution", ascending=False)
        buy = con[con["q_side"] == "buy"].iloc[0]
        print(f"    {label:<12s} largest Q_buy contributor: {buy['category']:<18s} "
              f"net {int(buy['net']):>+9,}  w {buy['weight']:.1f}")
    print("  Gold's immovable side is the SWAP DEALER at w=0.4, not the producer. The")
    print("  appendix's argument is a physical hedger who can stand for delivery, and gold")
    print("  does not have one of any size. Live cattle does, and its Producer/Merchant is")
    print("  net short in 82 of 82 weeks with Managed Money net long in all 82.")

    print(f"\n--- 2. §A.2, report week {week.date()} (released 2026-07-31) ---")
    print(report.to_markdown(report.category_table(cur, code)))
    arith = report.q_arithmetic(cur, code)
    print()
    print(report.format_q_block(arith))
    print(f"\n    Q_sell / Q_buy = {arith['q_sell'] / arith['q_buy']:.4f}")

    con = contributions(market)
    num = float((con["weight"] * con["gross"]).sum())
    mm = con[con["category"] == "managed_money"].iloc[0]
    print(f"    Phi numerator {num:,.1f}; Managed Money carries "
          f"{mm['weight'] * mm['gross'] / num:.1%} of it")
    buy = con[con["q_side"] == "buy"].sort_values("q_contribution", ascending=False)
    print("\n    the Q_buy side, largest contribution first. Note it is NOT the largest net:")
    print(report.to_markdown(buy[["category", "net", "weight", "q_contribution"]]))

    print("\n--- 3. §A.5 continued: T = Q / (kappa V) ---")
    frag = add_volume(fragility_frame(market).merge(
        market[["market_code", "symbol"]].drop_duplicates(), on="market_code", how="left"))
    row = frag.iloc[0]
    for side in ("sell", "buy"):
        out = exit_pressure(row[f"q_{side}"], row["open_interest"], volume=row["adv"])
        stress = exit_pressure(row[f"q_{side}"], row["open_interest"],
                              volume=row["adv_stress"])
        print(f"    T_{side:<5s} = {out['q']:>10,.1f} / (0.2 x {out['volume']:>10,.2f}) = "
              f"{out['days_to_liquidate']:>5.2f} days   "
              f"(stress volume {stress['volume']:,.0f} -> "
              f"{stress['days_to_liquidate']:.2f} days)")
    print("    Live cattle is one of the markets that trades MORE in its worst decile, so")
    print("    the stress figure is the SHORTER one. A10's caution, on the example market.")

    import cotdata
    sigma = float(cotdata.get_prices(symbol, adjustment="propadj")["Close"]
                  .pct_change().dropna().tail(63).std())
    for y in (0.5, 0.75, 1.0):
        i = core_impact.square_root_impact(sigma, row["q_sell"], row["adv"], y=y)
        print(f"    impact on Q_sell at Y={y:.2f}: {i * 1e4:.0f} bps")

    print("\n--- 4. §A.7 continued: the trigger block ---")
    block = trigger_block(symbol, market_row=row, sigma_daily=sigma, adv=row["adv"],
                          pool_contracts=float(
                              con[con["category"] == "managed_money"]["net"].iloc[0]))
    print(trig.format_block(block))
    print(f"    vol shock forces {block['vol_shock_reduction'] * 100:.0f}% of "
          f"{block['pool_contracts']:,.0f} = "
          f"{block['vol_shock_reduction'] * block['pool_contracts']:,.0f} contracts")

    print("\n--- 5. §A.9 continued: all three terms, and the product ---")
    print("    C and I need a three-year window stacked under a percentile, so they come")
    print("    from the CURRENT-state panel (27 markets back to 2006), not the vintage")
    print("    store's 82 weeks. Descriptive only: it is not point-in-time.")
    import reproduce_composite

    scored = reproduce_composite.build()
    le = scored[scored["market_code"] == code].sort_values("report_date")
    last = le.iloc[-1]
    print(f"    history {le['report_date'].min().date()} to "
          f"{le['report_date'].max().date()}, {len(le):,} weeks")
    print(f"      C  crowding_long    {last['crowding_long']:.4f}")
    print(f"      I  illiquidity_sell {last['illiquidity_sell']:.4f}")
    print(f"      Phi fragility (pct) {last['fragility']:.4f}   (raw Phi {last['phi']:.4f})")
    print(f"      D = C x I x Phi   = {last['damage_sell']:.6f}, which is the "
          f"{last['damage_sell_pct']:.1%} percentile of its own history")
    print("  The market has the template SHAPE and a low D, because the shape is about who")
    print("  holds and D is about how much. §A.9's multiplicative form is exactly what")
    print("  produces that: C near zero takes the product with it whatever Phi says.")


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


# ── C12-C14: the contract-spec inventory ────────────────────────────────────
#: A code is a differential when its name states two legs. Whole-word tokens plus the `/`
#: that separates two quoted legs. Deliberately NOT a fuzzy matcher: the point is that the
#: seven it selects are checkable by eye against the printed list, and `2026-08-02 §B30`'s
#: heating-oil case (`NY HARBOR ULSD` against `NY HARBOR USLD`, a transposition in the CFTC
#: source) is why nothing here tries to normalise a market name.
DIFF_TOKENS = (" VS ", " VS.", "/", " SPR", "CRACK", "BALMO", " PL ")
CERT_VENUES = ("ICE FUTURES ENERGY DIV", "NODAL EXCHANGE")


def _spec_class(name: str) -> str:
    """The three populations of `§C14`, from the market name alone."""
    if any(v in name for v in CERT_VENUES):
        return "environmental/power certificate"
    head = name.rsplit(" - ", 1)[0]
    return ("differential/spread/crack" if any(t in head for t in DIFF_TOKENS)
            else "real outright")


def contract_spec_inventory() -> None:
    """Amendments C12-C14: what the contract-spec table actually covers.

    Executes tasks 1a-1c of `docs/handoffs/2026-08-03-step2-contract-master.md`, and
    contradicts its §0 on the size of the covered universe: 45 markets in the latest week
    across two report types, not the 25 the handoff scopes to.

    Every figure the three amendments quote is printed here. The three that matter:

    - the spec table is fully consumed (26 Disaggregated + 21 TFF union = 47 symbols)
    - the covered set is 25 of 25 classic outright, so the gate the handoff sets passes
    - "no contract spec" is three populations, and only 34 of 254 are a backlog
    """
    from crowdmon.futures import ContractMaster, add_volume, rank_markets

    rule("CONTRACT SPEC INVENTORY (2026-08-03 C12-C14)")
    cm = ContractMaster.load()

    # ── C12: the covered universe spans two report types, and moves by week ──
    print("\n  C12. spec'd markets by report type\n")
    print(f"  {'report type':<16}{'on panel':>10}{'spec, union':>13}{'spec, latest':>14}")
    totals = [0, 0]
    for rt in ("disaggregated", "tff"):
        vp = cm.annotate(from_vintage(report_type=rt))
        ok = vp[vp["symbol"].notna()]
        last = ok["report_date"].max()
        union = ok["market_code"].nunique()
        latest_n = ok[ok["report_date"] == last]["market_code"].nunique()
        totals[0] += union
        totals[1] += latest_n
        print(f"  {rt:<16}{vp['market_code'].nunique():>10}{union:>13}{latest_n:>14}")
        if rt == "disaggregated":
            absent = set(ok["market_code"]) - set(
                ok[ok["report_date"] == last]["market_code"])
            for code in sorted(absent):
                rows = ok[ok["market_code"] == code]
                print(f"    spec'd but absent from the latest week: {code} "
                      f"{rows['market_name'].iloc[0]} ({rows['symbol'].iloc[0]}), present in "
                      f"{rows['report_date'].nunique()} of {ok['report_date'].nunique()} weeks")
    print(f"  {'TOTAL':<16}{'':>10}{totals[0]:>13}{totals[1]:>14}")
    print("\n  26 + 21 = 47 is the whole contract_specs table, so nothing in it is")
    print("  stranded. The handoff's '25 of 279' counted one report type: CFTC does not")
    print("  publish financials on Disaggregated, and they are scored on TFF today.")

    # ── the covered cross-section, and the gate ──────────────────────────────
    p = cm.annotate(latest())
    adv = (add_volume(p)[["market_code", "adv"]].dropna()
           .drop_duplicates("market_code").set_index("market_code")["adv"])
    f = fragility_frame(p)
    r = rank_markets(f, volume=f["market_code"].map(adv))     # per §C11, map first
    spec = (p[["market_code", "market_name", "symbol", "exchange", "asset_class"]]
            .drop_duplicates("market_code").set_index("market_code"))
    vp = from_vintage()
    oi = (vp[["report_date", "market_code", "open_interest"]]
          .drop_duplicates(["report_date", "market_code"])
          .groupby("market_code")["open_interest"].mean())
    inv = r.set_index("market_code")[["dtl_sell"]].join(spec).join(oi.rename("mean_oi"))
    covered = inv[inv["dtl_sell"].notna()].sort_values("mean_oi", ascending=False)
    uncov = inv[inv["dtl_sell"].isna()].copy()
    print(f"\n  covered (real dtl_sell) {len(covered)}, uncovered {len(uncov)}"
          f"  [§C5 pinned 25 / 254]")

    print("\n  C13. the gate: stratum, complex, Managed Money prominence\n")
    covered_class = covered["market_name"].map(_spec_class)
    print("  covered stratum:", dict(covered_class.value_counts()))
    print("  covered complex:", dict(covered["asset_class"].value_counts()))

    mm = vp[vp["category"] == "managed_money"].copy()
    mm = mm[mm["open_interest"] > 0]
    mm["share"] = (mm["long_contracts"] - mm["short_contracts"]).abs() / mm["open_interest"]
    med = mm.groupby("market_code")["share"].median()
    print(f"\n  median |P_MM|/OI  covered {med.reindex(covered.index).median():.4f}"
          f"   uncovered {med.reindex(uncov.index).median():.4f}")
    energy = covered.index[covered["asset_class"] == "Energies"]
    e = mm[mm["market_code"].isin(energy)]
    ne = mm[mm["market_code"].isin(covered.index.difference(energy))]
    print(f"  market-weeks with MM under 5% of OI:"
          f"  covered energy {(e['share'] < 0.05).mean():.3f} (n={len(e)}),"
          f"  other covered {(ne['share'] < 0.05).mean():.3f} (n={len(ne)})")
    template = {"088691": "gold", "084691": "silver", "085692": "copper",
                "057642": "live cattle", "061641": "feeder cattle",
                "083731": "coffee", "111659": "RBOB"}
    inside = [v for k, v in template.items() if k in covered.index]
    print(f"  always-template set (2026-08-02 B36) inside coverage: "
          f"{len(inside)} of {len(template)}")
    print("\n  The gate PASSES. 25 of 25 are classic outright and 0 are power/gas/carbon,")
    print("  against a panel that 2026-08-02 B31 measured as 76% power. Energy is thin on")
    print("  the fragility term wherever it appears, which is B33's finding arriving")
    print("  inside coverage rather than a defect in the scoping rule.")

    # ── C14: the three populations of the uncovered ──────────────────────────
    uncov["klass"] = uncov["market_name"].map(_spec_class)
    print("\n  C14. what 'no contract spec' is made of\n")
    for k, n in uncov["klass"].value_counts().items():
        print(f"    {k:<34}{n:>5}")
    for k in ("differential/spread/crack", "real outright"):
        sel = uncov[uncov["klass"] == k].sort_values("mean_oi", ascending=False)
        print(f"\n  {k} ({len(sel)}):")
        for code, row in sel.iterrows():
            print(f"    {code}  {row['market_name'][:52]:<52}{row['mean_oi']:>12,.0f}")
    out = uncov[uncov["klass"] == "real outright"]
    fam = {"Henry Hub": out.index.isin(["023A55", "023A56", "03565B", "03565C"]).sum(),
           "WTI/Brent": out.index.isin(["067411", "06765A", "06765T"]).sum(),
           "Mt Belvieu/propane/NGL": out.index.str.startswith("06665").sum()}
    print(f"\n  families inside the backlog: {fam}, leaving "
          f"{len(out) - sum(fam.values())} one-instrument codes.")
    print("  So the analytical gain is nearer 23 instruments than 34. Micro gold (088695)")
    print("  is the case to settle first: same underlying as the covered 088691 at a tenth")
    print("  the size, and 2026-08-02 B30 is the precedent for merging before ranking.")


#: The two families §C14 flagged as the head of the backlog, each against the already
#: covered flagship it looks like a variant of. Deliberately paired by hand rather than by a
#: name-prefix rule: `03565B`/`03565C` are Henry Hub and do NOT share `023651`'s prefix,
#: so a prefix rule would have silently dropped the two most interesting rows.
VARIANT_PAIRS = [
    ("067411", "ICE Europe WTI", "067651", "NYMEX WTI-PHYSICAL (CL)"),
    ("023A55", "HH last day fin", "023651", "NAT GAS NYME (NG)"),
    ("023A56", "HH penultimate fin", "023651", "NAT GAS NYME (NG)"),
    ("03565B", "HENRY HUB", "023651", "NAT GAS NYME (NG)"),
    ("03565C", "HH penultimate nat gas", "023651", "NAT GAS NYME (NG)"),
]


def variant_codes_are_not_duplicates() -> None:
    """Amendment C15: the head of the §C14 backlog is not a second copy of CL and NG.

    The objection this tests was raised against the request to spec these five, by analogy
    with micro gold (`§C14`): a code that looks like a variant of a covered market would put
    the same underlying into every cross-market ranking twice, and `2026-08-02 §B30` is the
    precedent for merging before ranking. **The analogy fails, and it fails on the measure
    that matters.** Open interest tracks (WTI at 0.771), which is what makes them look like
    duplicates, while Managed Money net positioning is consistently NEGATIVE and week-to-week
    flow is near zero. They carry independent holder information.

    Also prints the blocker: adding these needs a Norgate `contract_specs` row and both
    stored price tiers, and MME/MFS are the worked example of a registry entry without them.
    """
    from cotdata import all_symbols, store

    from crowdmon.futures import ContractMaster

    rule("VARIANT CODES ARE NOT DUPLICATES (2026-08-03 C15)")
    vp = from_vintage()
    oi = (vp.drop_duplicates(["report_date", "market_code"])
          .pivot(index="report_date", columns="market_code", values="open_interest"))
    mm = vp[vp["category"] == "managed_money"]
    net = (mm.assign(net=mm["long_contracts"] - mm["short_contracts"])
           .pivot(index="report_date", columns="market_code", values="net"))

    print(f"\n  {'code':<9}{'candidate':<25}{'against':<12}{'r(OI)':>8}"
          f"{'r(MM net)':>11}{'r(dMM)':>9}{'mean OI':>12}")
    for code, name, sib, sib_name in VARIANT_PAIRS:
        r_oi = oi[code].corr(oi[sib])
        r_mm = net[code].corr(net[sib])
        r_d = net[code].diff().corr(net[sib].diff())
        print(f"  {code:<9}{name:<25}{sib_name[:10]:<12}{r_oi:>8.3f}{r_mm:>11.3f}"
              f"{r_d:>9.3f}{oi[code].mean():>12,.0f}")
    for sib, sib_name in (("067651", "NYMEX WTI-PHYSICAL (CL)"), ("023651", "NAT GAS (NG)")):
        print(f"  {'':<9}{'(flagship) ' + sib_name:<46}{'':>28}{oi[sib].mean():>12,.0f}")

    print("\n  Every Managed Money correlation is NEGATIVE and every flow correlation is")
    print("  near zero, so these are not a second copy of the flagship's holder base. The")
    print("  micro-gold analogy does not transfer, and the objection is withdrawn.")

    # ── the blocker, and the worked example that proves it ───────────────────
    reg = {s.internal for s in all_symbols()}
    spec = set(store.read_metadata()["Symbol"])
    by_code = {s.cftc_code for s in all_symbols() if s.cftc_code}
    print(f"\n  registry symbols {len(reg)}, contract_specs rows {len(spec)}")
    print(f"  registry symbols with NO spec row: {sorted(reg - spec)}")
    missing_reg = [c for c, *_ in VARIANT_PAIRS if c not in by_code]
    print(f"  of the {len(VARIANT_PAIRS)} candidates, {len(missing_reg)} have no registry "
          f"symbol at all: {missing_reg}")
    cov = ContractMaster.load().coverage()
    print("\n  MME/MFS are the worked example: a registry entry with norgate: null is")
    print("  missing all three artifacts and is invisible to coverage, so adding YAML")
    print("  entries for the five above would reproduce exactly this and nothing more.\n")
    print(cov[~cov["joinable"]][["symbol", "cftc_code", "has_specs", "has_unadj_price",
                                 "has_backadj_price", "missing"]].to_string(index=False))


#: Cross-complex |r| on first differences, 90th percentile, from
#: `positioning_levels_are_spurious`. Used as the noise band a flow correlation must clear
#: before it counts as evidence of a shared holder base. Recomputed by that block rather
#: than trusted: it is a property of this panel's length and persistence, not a constant.
FLOW_NOISE_P90 = 0.229

#: Ag and dairy codes in the §C14 backlog, each against its nearest ECONOMIC sibling among
#: the covered 25. Paired by hand and by economics, never by best fit: §C16 is the whole
#: reason a max-correlation scan cannot be used to pick the comparison.
AG_DAIRY_SIBLING = {
    "135731": ("CANOLA", "007601"),            # vs soybean oil, substitute veg oil
    "001626": ("WHEAT-HRSpring", "001602"),    # vs wheat-SRW, third wheat class
    "005603": ("MINI SOYBEANS", "005602"),     # vs soybeans, same contract smaller
    "037021": ("Malaysian palm oil", "007601"),  # vs soybean oil
    "063642": ("CHEESE", "052641"),            # vs class III milk, its own input
    "050642": ("BUTTER", "052641"),
    "039601": ("ROUGH RICE", "002602"),        # vs corn, nearest grain
    "052642": ("NON FAT DRY MILK", "052641"),
    "052644": ("CME MILK IV", "052641"),
    "052645": ("DRY WHEY", "052641"),
}


def _mm_net_panel(report_type: str = "disaggregated") -> pd.DataFrame:
    """Managed Money net, one column per market code, indexed by report date."""
    vp = from_vintage(report_type=report_type)
    mm = vp[vp["category"] == "managed_money"]
    return (mm.assign(net=mm["long_contracts"] - mm["short_contracts"])
            .pivot(index="report_date", columns="market_code", values="net"))


def positioning_levels_are_spurious() -> None:
    """Amendment C16: correlating Managed Money LEVELS is spurious, and §C15 leaned on it.

    Positioning levels are near unit-root (lag-1 autocorrelation median 0.956), so a
    correlation between two of them is the Granger-Newbold problem in its textbook form. The
    consequence is not subtle and is measured three ways here: cross-complex pairs whose true
    correlation should be near zero, and a Monte Carlo scanning an INDEPENDENT random walk
    against the covered 25, which is exactly the "nearest holder base" scan that produced
    palm oil against lean hogs at 0.741.

    **This corrects the emphasis of `§C15`, not its conclusion.** §C15 led with negative
    level correlations as the striking evidence that the energy variant codes are a different
    holder base. Those numbers are noise. It also reported the first-differenced correlations,
    which were near zero, and those carry the finding.
    """
    from crowdmon.futures import (
        ContractMaster,
        add_volume,
        fragility_frame,
        latest,
        rank_markets,
    )

    rule("POSITIONING LEVELS ARE SPURIOUS (2026-08-03 C16)")
    cm = ContractMaster.load()
    p = cm.annotate(latest())
    adv = (add_volume(p)[["market_code", "adv"]].dropna()
           .drop_duplicates("market_code").set_index("market_code")["adv"])
    fr = fragility_frame(p)
    ranked = rank_markets(fr, volume=fr["market_code"].map(adv))
    covered = ranked[ranked["dtl_sell"].notna()]["market_code"].tolist()
    net = _mm_net_panel()[covered]
    diff = net.diff()

    ac = net.apply(lambda s: s.autocorr(1))
    acd = diff.apply(lambda s: s.autocorr(1))
    print(f"\n  lag-1 autocorrelation over {len(covered)} covered markets")
    print(f"    LEVELS       median {ac.median():.3f}   min {ac.min():.3f}   "
          f"max {ac.max():.3f}")
    print(f"    DIFFERENCES  median {acd.median():.3f}   min {acd.min():.3f}   "
          f"max {acd.max():.3f}")

    spec = (p[["market_code", "asset_class"]].drop_duplicates("market_code")
            .set_index("market_code")["asset_class"])
    pairs = [(a, b) for i, a in enumerate(covered) for b in covered[i + 1:]
             if spec.get(a) != spec.get(b)]
    lv = np.array([abs(net[a].corr(net[b])) for a, b in pairs])
    dv = np.array([abs(diff[a].corr(diff[b])) for a, b in pairs])
    print(f"\n  cross-complex pairs, true correlation should be near zero (n={len(pairs)})")
    print(f"    |r| LEVELS       median {np.median(lv):.3f}  p90 {np.percentile(lv, 90):.3f}"
          f"  max {lv.max():.3f}   share above 0.5: {(lv > 0.5).mean():.1%}")
    print(f"    |r| DIFFERENCES  median {np.median(dv):.3f}  p90 {np.percentile(dv, 90):.3f}"
          f"  max {dv.max():.3f}   share above 0.5: {(dv > 0.5).mean():.1%}")

    rng = np.random.default_rng(0)
    ml, md = [], []
    for _ in range(2000):
        x = np.cumsum(rng.standard_normal(len(net)))
        ml.append(max(abs(np.corrcoef(x, net[c].values)[0, 1]) for c in covered))
        md.append(max(abs(np.corrcoef(np.diff(x), diff[c].values[1:])[0, 1])
                      for c in covered))
    print(f"\n  scanning all {len(covered)} covered markets with an INDEPENDENT random "
          f"walk, 2000 draws, seed 0")
    print(f"    max |r| LEVELS       median {np.median(ml):.3f}  "
          f"p95 {np.percentile(ml, 95):.3f}")
    print(f"    max |r| DIFFERENCES  median {np.median(md):.3f}  "
          f"p95 {np.percentile(md, 95):.3f}")
    print("\n  A series with NO relationship to anything scores a max level correlation of")
    print(f"  {np.median(ml):.3f} half the time. Every 'nearest holder base' figure computed")
    print("  on levels is therefore uninformative, and §C15's negative level correlations")
    print("  are noise. Its conclusion stands on the differenced figures it also reported.")


def ag_dairy_backlog_priority() -> None:
    """Amendment C17: prioritising the ag and dairy codes in the §C14 backlog.

    Three criteria, in order, and the first is the one that decides most of the list:

    1. **Is there a levered holder at all?** Median `|P_MM| / OI` against the covered
       median of 0.1371. This is `§C13`'s gate applied per candidate rather than to the set.
    2. **Is the flow independent?** First-differenced correlation against the nearest
       economic sibling, judged against the noise band from `§C16`. Levels are not used.
    3. **Can it be scored?** Weeks present of 82. `2026-08-02 §B29`'s oats lesson.
    """
    rule("AG AND DAIRY BACKLOG PRIORITY (2026-08-03 C17)")
    vp = from_vintage()
    oi = (vp.drop_duplicates(["report_date", "market_code"])
          .pivot(index="report_date", columns="market_code", values="open_interest"))
    net = _mm_net_panel()
    mm = vp[vp["category"] == "managed_money"]
    q = mm[mm["open_interest"] > 0]
    prom = ((q["long_contracts"] - q["short_contracts"]).abs() / q["open_interest"]) \
        .groupby(q["market_code"]).median()
    absnet = q.assign(n=(q["long_contracts"] - q["short_contracts"]).abs()) \
        .groupby("market_code")["n"].median()
    weeks = vp.drop_duplicates(["report_date", "market_code"]).groupby("market_code").size()

    print(f"\n  {'code':<8}{'market':<24}{'mean OI':>10}{'wks':>5}{'MM share':>10}"
          f"{'MM net':>9}{'r(dMM)':>9}  verdict")
    rank = []
    for code, (name, sib) in AG_DAIRY_SIBLING.items():
        w = int(weeks.get(code, 0))
        pr = float(prom.get(code, float("nan")))
        rd = net[code].diff().corr(net[sib].diff()) if code in net else float("nan")
        if w < 40:
            v, tier = f"EXCLUDE: {w} of 82 weeks", 4
        elif pr < 0.05:
            v, tier = "EXCLUDE: no levered holder", 4
        elif pd.notna(rd) and rd > FLOW_NOISE_P90:
            v, tier = "duplicative flow", 2
        else:
            v, tier = "INDEPENDENT", 1
        rank.append((tier, -pr, code, name, v))
        print(f"  {code:<8}{name:<24}{oi[code].mean():>10,.0f}{w:>5}{pr:>10.3f}"
              f"{absnet.get(code, float('nan')):>9,.0f}{rd:>9.3f}  {v}")
    print(f"\n  covered-market median MM share 0.1371; §C16 flow noise band "
          f"p90 = {FLOW_NOISE_P90}")
    print("\n  PRIORITY ORDER")
    for i, (_, _, code, name, v) in enumerate(sorted(rank), 1):
        print(f"    {i}. {code} {name:<22} {v}")
    print("\n  Only ROUGH RICE clears every bar, and it is the SMALLEST market that does.")
    print("  Six of ten fail outright. The dairy complex minus cheese carries a Managed")
    print("  Money book an order of magnitude below the covered median, so it is the very")
    print("  thing §C13's gate exists to keep out of coverage.")


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
    template_shape_stratified()
    template_conditional_magnitude()
    template_direction_agnostic()
    template_swap_share()
    template_stability()
    appendix_a2_worked_example()
    flow_equivalence()
    lumber_is_one_instrument()
    contract_spec_inventory()
    variant_codes_are_not_duplicates()
    positioning_levels_are_spurious()
    ag_dairy_backlog_priority()
