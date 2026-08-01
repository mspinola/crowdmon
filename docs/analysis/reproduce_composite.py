"""Reproducer for every figure in 2026-07-28-composite.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_composite.py

Deterministic: no sampling, no seeds, no fitting.

**This script does not validate anything.** The episode windows in §5 are a descriptive look
at whether `D` moves where the module spec §10 replay list says it should, computed after the
fact on windows chosen by hand. That is not a test and must not be read as one: a real
validation is pre-registered, runs through `crucible`, and is not performed by the session
that wrote the measure. Workspace governance, and the reason the boundary test forbids
importing the judge.
"""
import warnings

import pandas as pd

from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    ContractMaster,
    add_composite,
    add_extremity,
    add_notional,
    add_risk_units,
    add_volume,
    damage_report,
    from_current_store,
    market_fragility,
    rank_markets,
    top_damage,
)

#: Windows from module spec §10's replay list that this panel can reach. 2008 is absent on
#: purpose: `C = pct(z)` needs two stacked three-year windows, so the composite produces
#: nothing before 2010-05-25 and the GFC is not testable here at all.
EPISODES = {
    "Mar 2020 lead (Oct19-Jan20)": ("2019-10-01", "2020-01-31"),
    "Mar 2020 event (Feb-Apr20)": ("2020-02-01", "2020-04-30"),
    "Mar 2020 after (May-Aug20)": ("2020-05-01", "2020-08-31"),
    "2021 ags/lumber": ("2021-03-01", "2021-08-01"),
    "2022 invasion": ("2022-02-01", "2022-06-01"),
}

FACTORS = ["crowding_long", "illiquidity_sell", "fragility", "dtl_sell", "adv"]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def build() -> pd.DataFrame:
    """The whole system, end to end: five layers into one frame."""
    panel = from_current_store()
    per_category = add_volume(add_extremity(add_risk_units(
        add_notional(ContractMaster.load().annotate(panel)))))
    # Volume is a market property; it arrives on the category frame, so lift it back.
    volume = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
              .max().reset_index())
    per_market = market_fragility(panel).merge(
        volume, on=["report_date", "market_code"], how="left")
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    return add_composite(ranked, per_category)


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 240)

    scored = build()
    week = scored["report_date"].max().date()

    rule(f"1. COVERAGE — 27 markets, through {week}")
    print(to_markdown(damage_report(scored).reset_index(names="outcome")))

    first = scored.loc[scored["damage_sell"].notna(), "report_date"].min()
    print(f"\ndata begins       : {scored['report_date'].min().date()}")
    print(f"first D           : {first.date()}")
    print(f"warm-up cost      : {(first - scored['report_date'].min()).days / 365.25:.1f} years")
    print("  because C = pct(z) stacks two three-year windows: z needs one, its percentile "
          "needs another")

    rule("2. THE LATEST WEEK — highest damage_sell, with every factor shown")
    print(to_markdown(top_damage(scored, n=8)))

    rule("3. THE OTHER DIRECTION")
    print(to_markdown(top_damage(scored, side="buy", n=5)))

    rule("4. IS D MULTIPLICATIVE IN PRACTICE, OR DOES ONE TERM CARRY IT?")
    scored_only = scored.dropna(subset=["damage_sell"])
    # `fragility` is the term D actually used; `phi` is the raw share beside it. Reporting
    # `phi` here would describe a factor the product does not contain under the default
    # reading, which is the mistake this whole section exists to catch.
    print("correlation of each factor with D_sell:")
    for factor in ("crowding_long", "illiquidity_sell", "fragility"):
        print(f"  {factor:<18} {scored_only[factor].corr(scored_only['damage_sell']):.3f}")
    print("\n  (raw phi, which D does NOT use by default: "
          f"{scored_only['phi'].corr(scored_only['damage_sell']):.3f})")
    print("\nfactor spread (a term that never varies cannot be doing any work):")
    print(scored_only[["crowding_long", "illiquidity_sell", "fragility", "phi"]]
          .describe().loc[["mean", "std", "min", "max"]].round(3).to_string())

    rule("5. EPISODE WINDOWS — DESCRIPTIVE ONLY, NOT A VALIDATION")
    print("Module spec §10 requires the composite to elevate BEFORE a drawdown rather than")
    print("coincidentally with it. These windows were chosen by hand, after the fact, on the")
    print("same data. That is a look, not a test. See this file's docstring.\n")
    baseline = scored["damage_sell"].dropna().mean()
    print(f"baseline mean D_sell across all weeks: {baseline:.4f}\n")
    rows = []
    for name, (start, end) in EPISODES.items():
        window = scored[(scored["report_date"] >= start) & (scored["report_date"] <= end)]
        damage = window["damage_sell"].dropna()
        if damage.empty:
            continue
        rows.append({"window": name, "market_weeks": len(damage),
                     "mean_D": damage.mean(), "vs_baseline": damage.mean() / baseline,
                     "C": window["crowding_long"].mean(),
                     "I": window["illiquidity_sell"].mean(),
                     "Phi": window["fragility"].mean()})
    print(to_markdown(pd.DataFrame(rows)))

    print("\nwhat moved in the Mar-2020 event window, against the 2019 mean:")
    y2019 = scored[(scored["report_date"] >= "2019-01-01")
                   & (scored["report_date"] <= "2019-12-31")]
    event = scored[(scored["report_date"] >= "2020-02-01")
                   & (scored["report_date"] <= "2020-04-30")]
    for factor in FACTORS:
        before, during = y2019[factor].mean(), event[factor].mean()
        print(f"  {factor:<18} {before:>14,.4f} -> {during:>14,.4f}   {during / before:.2f}x")

    rule("6. CROSS-SECTIONAL MEAN D_sell BY YEAR")
    yearly = (scored.assign(year=scored["report_date"].dt.year)
              .groupby("year")["damage_sell"].mean().dropna().round(3))
    print(yearly.to_string())


if __name__ == "__main__":
    main()
