"""Reproducer for §4 of `docs/handoffs/2026-08-03-report-layer.md`, the stratum classifier.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_stratum.py

Deterministic: no sampling, no seeds, no fitting. Regenerates every figure in
`docs/design/amendments-2026-08-03.md` §C29.

**Nothing here measures anything new.** `2026-08-03 §C13` and `§C14` already partitioned the
universe; this shows that the same partition falls out of `crowdmon.futures.stratum`, which
a consumer can reach, rather than out of `reproduce.py::_spec_class`, which one cannot. §4
of the handoff calls that the difference between a rule written down and a rule enforceable.

§4 also demands that the classifier **derive the split from the data and print what it
derived**, because the covered universe is report-week dependent and spans two report types
(`§C12`). That is what `stratum_summary` and `format_strata` do, and what this prints.
"""
import warnings

import pandas as pd

from crowdmon.futures import (
    classify,
    differential_matches,
    format_strata,
    from_current_store,
    from_vintage,
    stratum_summary,
)
from crowdmon.futures.composite import DEFAULT_MIN_PERIODS


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def c29_the_split_reproduces_from_src(vintage: pd.DataFrame,
                                      current: pd.DataFrame) -> None:
    """§C29, first half. The promoted classifier cuts where the analysis script cut."""
    rule("C29a. The promoted classifier reproduces C13 and C14 exactly")
    latest = vintage[vintage["report_date"] == vintage["report_date"].max()]
    week = pd.Timestamp(latest["report_date"].iloc[0]).date()

    print(f"vintage panel, latest report week {week}:")
    print(format_strata(stratum_summary(classify(latest))))
    print("  §C14 measured 213 certificate / 7 differential / 34 uncovered outright,")
    print("  and §C13 the 25 covered outright. 34 + 25 = 59.")

    print("\nthe seven differentials, and the token that caught each:")
    print(differential_matches(classify(latest)).to_string(index=False))
    print("  §C14 states this is the COMPLETE list rather than examples, so an eighth")
    print("  would be a finding and a sixth a bug. `/` is the broad one.")

    print("\ncurrent-state panel:")
    print(format_strata(stratum_summary(classify(current))))
    print("  §C13: the covered set is the COMPLEMENT of the thing that made the panel")
    print("  hard to reason about, not a sample of it.")


def c29_the_rule_is_vacuous_the_split_is_not(vintage: pd.DataFrame,
                                             current: pd.DataFrame) -> None:
    """§C29, second half. Why §9 said not to build this, and what that reasoning missed."""
    rule("C29b. The obligation is vacuous; the classification is not")
    v_weeks = vintage["report_date"].nunique()
    c_weeks = current["report_date"].nunique()
    v = {k: int(n) for k, n in zip(*(lambda s: (s["stratum"], s["markets"]))(
        stratum_summary(classify(vintage))))}
    c = {k: int(n) for k, n in zip(*(lambda s: (s["stratum"], s["markets"]))(
        stratum_summary(classify(current))))}

    table = pd.DataFrame([
        {"panel": "vintage", "markets": sum(v.values()), "weeks": v_weeks,
         "certificate markets": v.get("certificate", 0),
         "pct(D) computable": v_weeks >= DEFAULT_MIN_PERIODS},
        {"panel": "current-state", "markets": sum(c.values()), "weeks": c_weeks,
         "certificate markets": c.get("certificate", 0),
         "pct(D) computable": c_weeks >= DEFAULT_MIN_PERIODS},
    ])
    print(table.to_string(index=False))
    print(f"\nmin_periods for a percentile: {DEFAULT_MIN_PERIODS} weekly observations")
    print("  -> no panel holds both the markets §C8's rule names and a D percentile, so")
    print("     NOBODY has to publish a band today. That is §C23 and it still holds.")
    print("  -> but every scoreable row can still be ASKED 'does the band bind here?' and")
    print("     answered `no, this is a classic outright`, which is the question a reader")
    print("     holding one D actually has. The obligation is vacuous; the answer is not.")


def worked_rows() -> None:
    """The three readings side by side, which is what a brief now prints."""
    from crowdmon.futures.stratum import BAND_ADVICE

    rule("C8's rule as a value, one line per stratum")
    for name, advice in BAND_ADVICE.items():
        print(f"\n{name}:\n  {advice}")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 240)
    vintage = from_vintage(report_type="disaggregated")
    current = from_current_store()

    c29_the_split_reproduces_from_src(vintage, current)
    c29_the_rule_is_vacuous_the_split_is_not(vintage, current)
    worked_rows()


if __name__ == "__main__":
    main()
