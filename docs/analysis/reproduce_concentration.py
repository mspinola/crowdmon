"""Reproducer for every figure in 2026-07-28-concentration.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_concentration.py

Deterministic: no sampling, no seeds, no fitting. Pinned to report week 2026-07-28.

Needs no prices, no volume and no contract master: CR4/CR8 are published in every
Disaggregated file and this reads them.
"""
import warnings

import pandas as pd

from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    add_concentration_extremity,
    concentration_vs_fragility,
    from_current_store,
    latest,
    market_concentration,
    market_fragility,
    quadrant,
)

CLASSICS = [("088691", "GOLD"), ("084691", "SILVER"), ("002602", "CORN"),
            ("005602", "SOYBEANS"), ("067651", "CRUDE OIL"), ("001602", "WHEAT-SRW"),
            ("023651", "NAT GAS")]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 235)

    cross = latest()
    concentration = market_concentration(cross)
    joined = concentration_vs_fragility(concentration, market_fragility(cross))
    joined["quadrant"] = quadrant(joined)
    joined["venue"] = joined["market_name"].str.split(" - ").str[-1]

    rule(f"1. CR4 ACROSS {len(concentration)} MARKETS, week {cross['report_date'].max().date()}")
    print(concentration["cr4_max_side"].describe(
        percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(1).to_string())
    print("\nthe more concentrated side:")
    print(concentration["cr4_side"].value_counts().to_string())

    rule("2. CONCENTRATION FALLS AS MARKETS GET LARGER")
    joined["oi_quartile"] = pd.qcut(joined["open_interest"], 4,
                                    labels=["smallest", "small", "large", "largest"])
    print(to_markdown(joined.groupby("oi_quartile", observed=True).agg(
        markets=("cr4_max_side", "size"),
        median_cr4=("cr4_max_side", "median"),
        median_phi=("phi", "median")).round(1).reset_index()))

    rule("3. THE QUADRANT — few holders versus forceable holders")
    print("thresholds are the cross-sectional medians of this week, so the split is")
    print("relative by construction and each column is about half the universe.\n")
    print(to_markdown(joined["quadrant"].value_counts().reset_index()))
    print("\nby venue:")
    venue = joined["venue"].str.replace("ICE FUTURES ENERGY DIV", "ICE ENERGY").str[:14]
    print(pd.crosstab(joined["quadrant"], venue).to_string())

    rule("4. WHERE THE CLASSIC OUTRIGHTS SIT")
    for code, name in CLASSICS:
        row = joined[joined["market_code"] == code]
        if row.empty:
            continue
        print(f"  {name:<10} CR4 {row['cr4_max_side'].iloc[0]:>5.1f} "
              f"({row['cr4_side'].iloc[0]:<5})  Phi {row['phi'].iloc[0]:.3f}  "
              f"{row['quadrant'].iloc[0]}")

    rule("5. THE CELL THAT NEEDS BOTH MEASURES — few and forceable")
    few = joined[joined["quadrant"] == "few_and_forceable"].nlargest(8, "cr4_max_side")
    print(to_markdown(few[["market_name", "cr4_max_side", "cr4_side", "phi",
                           "q_sell", "q_buy", "open_interest"]]))

    rule("6. CONCENTRATION AGAINST OWN HISTORY (27-market panel, 2006-2026)")
    history = market_concentration(from_current_store())
    scored = add_concentration_extremity(history)
    print(f"market-weeks: {len(scored):,}   scored: "
          f"{int(scored['cr4_max_side_pct'].notna().sum()):,}")
    print(f"CR columns null anywhere in twenty years: "
          f"{int(history[['cr4_net_long', 'cr4_net_short', 'cr8_net_long', 'cr8_net_short']].isna().sum().sum())}")
    latest_week = scored[scored["report_date"] == scored["report_date"].max()]
    print("\nmost concentrated against own three-year history:")
    print(to_markdown(latest_week.nlargest(6, "cr4_max_side_pct")[
        ["market_name", "cr4_max_side", "cr4_side", "cr4_max_side_z",
         "cr4_max_side_pct"]]))


if __name__ == "__main__":
    main()
