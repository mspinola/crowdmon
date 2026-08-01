"""Reproducer for every figure in 2026-07-28-extremity.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_extremity.py

Deterministic: no sampling, no seeds, no fitting. Pinned to report week 2026-07-28.

Runs the full normalisation ladder (contract master -> notional -> risk units -> extremity)
over the 27-market current-state panel, 2006 to 2026. That panel rather than the 346-market
vintage one because a three-year window needs three years and the vintage store holds about
nineteen months.
"""
import warnings

import numpy as np
import pandas as pd

from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    ContractMaster,
    add_extremity,
    add_notional,
    add_risk_units,
    extremity_report,
    from_current_store,
    latest_extremes,
    risk_coverage_report,
)

SERIES_KEY = ["market_code", "category"]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def build() -> pd.DataFrame:
    """The whole ladder, in one place, so the analysis cannot silently skip a rung."""
    panel = from_current_store()
    annotated = ContractMaster.load().annotate(panel)
    return add_risk_units(add_notional(annotated))


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 235)

    with_risk = build()
    scored = add_extremity(with_risk)
    week = scored["report_date"].max().date()

    rule(f"1. COVERAGE — 27 markets, 2006 to {week}")
    print(to_markdown(extremity_report(scored).reset_index(names="outcome")))
    # `risk_coverage_report` returns a Series where `extremity_report` returns a frame, so
    # this normalises rather than assuming they match.
    print("\nwhy rows have no risk units:")
    risk_cov = risk_coverage_report(with_risk).to_frame("rows")
    print(to_markdown(risk_cov.reset_index(names="outcome")))

    missing = with_risk[with_risk["net_notional_usd"].isna()]
    print(f"\nno-notional rows belong to market_code(s): "
          f"{sorted(missing['market_code'].unique())}")
    print(f"  name       : {missing['market_name'].iloc[0].strip()}")
    print(f"  priced to  : {missing['report_date'].max().date()}")
    print(f"  COT runs to: {with_risk[with_risk['market_code'].isin(missing['market_code'])]['report_date'].max().date()}")

    rule("2. THE SCORE DISTRIBUTION")
    z = scored["net_risk_usd_z"].dropna()
    print("absolute z quantiles:")
    print(z.abs().quantile([0.5, 0.9, 0.99, 0.999, 1.0]).round(2).to_string())
    print("\nwinsor sweep (appendix A.4 specifies none; module spec 6.1 says 'winsorised'):")
    for limit in (0.0, 0.05, 0.10):
        zz = add_extremity(with_risk, winsor=limit)["net_risk_usd_z"].dropna()
        print(f"  winsor={limit:.2f}  median |z| {zz.abs().median():.2f}   "
              f"99th {zz.abs().quantile(0.99):.2f}   max {zz.abs().max():.1f}   "
              f"share above 6: {(zz.abs() > 6).mean():.3%}")

    rule("3. THE LATEST WEEK — most extreme Managed Money readings")
    print(to_markdown(latest_extremes(scored, n=8)))

    rule("4. EXTREMITY IS AGAINST OWN HISTORY, NOT AGAINST ZERO")
    for code, name in (("001602", "WHEAT-SRW"), ("001612", "WHEAT-HRW")):
        rows = scored[(scored["market_code"] == code)
                      & (scored["category"] == "managed_money")].set_index("report_date")
        window = rows.loc["2023-07-28":, "net_risk_usd"]
        print(f"\n{name} managed money, trailing three years:")
        print(f"  window mean {window.mean():>16,.0f}")
        print(f"  window min  {window.min():>16,.0f}")
        print(f"  window max  {window.max():>16,.0f}")
        print(f"  latest      {rows['net_risk_usd'].iloc[-1]:>16,.0f}   "
              f"pct={rows['net_risk_usd_pct'].iloc[-1]:.3f}   "
              f"contracts={rows['net_contracts'].iloc[-1]:,.0f}")

    rule("5. EXTREMES PERSIST — the base rate is not what the percentile implies")
    pct = scored["net_risk_usd_pct"].dropna()
    print(f"share above the 95th percentile: {(pct > 0.95).mean():.2%}  (nominal 5%)")
    print(f"share below the  5th percentile: {(pct < 0.05).mean():.2%}  (nominal 5%)")

    runs = _run_lengths(scored)
    print(f"\nepisodes above the 95th: {len(runs):,}")
    print(f"  mean run length {runs.mean():.1f} weeks")
    print(f"  median          {np.median(runs):.0f} weeks")
    print(f"  90th percentile {np.quantile(runs, 0.9):.0f} weeks")
    print(f"  longest         {runs.max()} weeks ({runs.max() / 52:.1f} years)")
    print(f"  share of hot weeks inside runs of 8+ weeks: "
          f"{runs[runs >= 8].sum() / runs.sum():.1%}")


def _run_lengths(scored: pd.DataFrame) -> np.ndarray:
    """Consecutive-week episodes above the 95th percentile, per market-category.

    Counted per series rather than pooled, because a run is a property of one market's
    position and concatenating two markets would join unrelated episodes end to end.
    """
    runs: list[int] = []
    ordered = scored.sort_values([*SERIES_KEY, "report_date"])
    for _, group in ordered.groupby(SERIES_KEY, sort=False):
        hot = (group["net_risk_usd_pct"] > 0.95).fillna(False).to_numpy()
        length = 0
        for flag in hot:
            if flag:
                length += 1
            elif length:
                runs.append(length)
                length = 0
        if length:
            runs.append(length)
    return np.array(runs)


if __name__ == "__main__":
    main()
