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
"""
import pandas as pd

from crowdmon.futures import (
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


if __name__ == "__main__":
    main()
