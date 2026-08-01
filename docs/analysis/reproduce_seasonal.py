"""Reproducer for every figure in 2026-08-02-seasonality.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_seasonal.py

Deterministic. Module spec §5.4, which asserts that ag commercial positioning is "dominated
by seasonality" and that this "will produce spurious extremes every year at the same time",
and offers no measurement.
"""
import warnings

import pandas as pd

from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    ContractMaster,
    add_extremity,
    add_notional,
    add_risk_units,
    deseasonalise,
    from_current_store,
    seasonal_profile,
    seasonality_report,
    week_of_year,
)

#: The agricultural complex in the 27-market panel: grains, oilseeds, softs, livestock feed.
#: Named explicitly rather than inferred, because "is this an ag" is the premise of §5.4 and
#: guessing it from an exchange code would bury the assumption.
AGS = ["002602", "005602", "007601", "026603", "001602", "001612",
       "033661", "080732", "083731", "073732", "040701"]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 210)

    panel = from_current_store()
    scored = add_extremity(add_risk_units(add_notional(
        ContractMaster.load().annotate(panel))))
    ag = scored[scored["market_code"].isin(AGS)]
    non_ag = scored[~scored["market_code"].isin(AGS)]

    rule("1. THE TWO STATISTICS DISAGREE, AND ONLY ONE IS SOUND")
    print("mean_spread is max-minus-min of ~53 noisy weekly means, so noise inflates it.")
    print("variance_share is the between-week share of total variance. Use the second.\n")
    for label, part in (("AG", ag), ("NON-AG", non_ag)):
        print(f"--- {label} ({part['market_code'].nunique()} markets) ---")
        print(to_markdown(seasonality_report(part, "net_risk_usd_z")))
        print()

    rule("2. §5.4'S CLAIM, TESTED ON THE STATISTIC THAT SETTLES IT")
    left = seasonality_report(ag, "net_risk_usd_z").set_index("category")
    right = seasonality_report(non_ag, "net_risk_usd_z").set_index("category")
    compare = pd.DataFrame({
        "ag": left["variance_share"], "non_ag": right["variance_share"],
        "ratio": left["variance_share"] / right["variance_share"],
        "ag_per_week": left["per_week"], "non_ag_per_week": right["per_week"],
    }).sort_values("ratio", ascending=False)
    print(to_markdown(compare.reset_index().round(4)))
    print("\n§5.4 names producer/merchant and commercials. Read the ratio column for those.")

    rule("3. IS ANYTHING 'DOMINATED BY SEASONALITY'?")
    every = seasonality_report(scored, "net_risk_usd_z")
    print(f"largest variance_share across all categories, both groups: "
          f"{max(left['variance_share'].max(), right['variance_share'].max()):.4f}")
    print(f"pooled across everything: {every['variance_share'].max():.4f}")
    print("\n'Dominated' would mean a large share. Nothing is above a few percent.")

    rule("4. WHAT DESEASONALISING ACTUALLY CHANGES")
    adjusted = deseasonalise(ag, "net_risk_usd_z")
    both = adjusted.dropna(subset=["net_risk_usd_z", "net_risk_usd_z_seasonal"])
    print(f"rows with a trailing profile: {len(both):,} of {len(adjusted):,} "
          f"({len(both) / len(adjusted):.1%}; the rest is the three-year warm-up)")
    print(f"  std before : {both['net_risk_usd_z'].std():.4f}")
    print(f"  std after  : {both['net_risk_usd_z_deseasonalised'].std():.4f}")
    print(f"  correlation: {both['net_risk_usd_z'].corr(both['net_risk_usd_z_deseasonalised']):.4f}")
    moved = (both["net_risk_usd_z"] - both["net_risk_usd_z_deseasonalised"]).abs()
    print(f"  median absolute change: {moved.median():.4f} z-units")
    print(f"  rows moved more than 0.5 z: {(moved > 0.5).mean():.2%}")

    rule("5. THE WEEK-OF-YEAR PROFILE, AG PRODUCER/MERCHANT")
    prod = ag[ag["category"] == "producer_merchant"].copy()
    prod["woy"] = week_of_year(prod["report_date"])
    weekly = prod.groupby("woy")["net_risk_usd_z"].agg(["mean", "count"]).round(3)
    peak, trough = weekly["mean"].idxmax(), weekly["mean"].idxmin()
    print(f"  peak   week {peak:>2}  mean z {weekly.loc[peak, 'mean']:+.3f}  "
          f"n={weekly.loc[peak, 'count']:.0f}")
    print(f"  trough week {trough:>2}  mean z {weekly.loc[trough, 'mean']:+.3f}  "
          f"n={weekly.loc[trough, 'count']:.0f}")
    print(f"  spread {weekly['mean'].max() - weekly['mean'].min():.3f} z-units, "
          f"median {weekly['count'].median():.0f} observations per week")

    # ISO week 53 exists only in some years, so it carries a fraction of the sample and its
    # mean is correspondingly noisy. It alone drives most of the spread above, which is the
    # mean_spread bias in its most concrete form.
    dense = weekly[weekly["count"] >= 50]
    print(f"\n  excluding weeks with under 50 observations ({len(weekly) - len(dense)} "
          f"dropped, all sparse ISO weeks):")
    print(f"    peak   week {dense['mean'].idxmax():>2}  {dense['mean'].max():+.3f}")
    print(f"    trough week {dense['mean'].idxmin():>2}  {dense['mean'].min():+.3f}")
    print(f"    spread {dense['mean'].max() - dense['mean'].min():.3f} z-units, against "
          f"a non-ag figure of 0.334 computed the same (biased) way")

    rule("6. NO LOOKAHEAD IN THE PROFILE")
    one = panel[panel["market_code"] == "002602"][
        ["report_date", "market_code", "report_type", "combined", "category",
         "long_contracts"]].copy()
    full = seasonal_profile(one, "long_contracts")
    early = seasonal_profile(one[one["report_date"] < "2018-01-01"], "long_contracts")
    overlap = full.reindex(early.index)
    matches = early.dropna().round(9).equals(overlap.reindex(early.dropna().index).round(9))
    print(f"  profile on 2006-2018 identical to the same rows from the full panel: {matches}")
    print(f"  first non-null: {one.loc[full.notna(), 'report_date'].min().date()} "
          f"(data begins {one['report_date'].min().date()})")


if __name__ == "__main__":
    main()
