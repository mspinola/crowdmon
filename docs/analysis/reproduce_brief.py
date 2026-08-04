"""Reproducer for §3 of `docs/handoffs/2026-08-03-report-layer.md`, the market-week brief.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_brief.py

Deterministic: no sampling, no seeds, no fitting. Regenerates every figure in
`docs/design/amendments-2026-08-03.md` §C25-§C27, and prints one real brief end to end.

**Nothing here measures anything new**, which is §6 of the handoff applied rather than
described. The two derivations it exercises (`add_score_state`, `add_unwind_state`) are a
classification and a first difference of columns the composite already returns, and both
live in `composite.py` because that module owns `D`.

The market is LIVE CATTLE, the same one appendix §A.2 works through (`2026-08-02 §B37`), so
a reader can carry one market across the fragility arithmetic and the composite.
"""
import warnings

import pandas as pd

from crowdmon.futures import (
    ContractMaster,
    VintageCotSource,
    add_commonality,
    add_composite,
    add_extremity,
    add_notional,
    add_risk_units,
    add_score_state,
    add_unwind_state,
    add_volume,
    commonality_betas,
    coverage_ladder,
    decompose,
    from_current_store,
    illiquidity_panel,
    market_fragility,
    rank_markets,
)
from crowdmon.futures.brief import (
    NOT_CARRIED,
    READING_INSTRUCTIONS,
    format_brief,
    market_brief,
)

#: Appendix §A.2's worked market, carried forward so one market spans both documents.
MARKET = "057642"


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def build():
    """The composite chain plus both caveat carriers, as `test_brief_live.py` runs it."""
    master = ContractMaster.load()
    panel = from_current_store()
    per_category = add_volume(add_extremity(add_risk_units(add_notional(
        master.annotate(panel)))))
    volume = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
              .max().reset_index())
    per_market = master.annotate(market_fragility(panel).merge(
        volume, on=["report_date", "market_code"], how="left"))
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    scored = add_score_state(add_composite(ranked, per_category))
    return per_category, add_unwind_state(scored, decompose(panel))


def with_beta(scored: pd.DataFrame) -> pd.DataFrame:
    """The same frame with §A.6's commonality attached, which nothing in `build` does.

    Deliberately a second step. `add_commonality` is not part of the composite chain and
    never will be (`2026-08-02 §B2`: with a constant `beta_bar`, `pct(T_eff)` is
    bit-identical to `pct(T)`), so a caller assembling a brief the obvious way has no
    `beta` and the ledger has to say so.
    """
    cot = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    specs = (cot.dropna(subset=["symbol", "point_value"])[["symbol", "point_value"]]
             .drop_duplicates("symbol").itertuples(index=False, name=None))
    return add_commonality(scored, commonality_betas(
        illiquidity_panel(specs, start="2015-01-01")))


def c25_the_ledger_over_the_five(scored: pd.DataFrame, ladder: pd.DataFrame) -> None:
    """§C25. How many of README's five reading instructions a brief can actually carry."""
    rule("C25. Two of the five are carryable at best, and the default chain carries one")
    week = pd.to_datetime(scored["report_date"]).max()
    for label, frame in (("the composite chain as `build` assembles it", scored),
                         ("the same frame after `add_commonality`", with_beta(scored))):
        brief = market_brief(frame, MARKET, report_date=week, ladder=ladder)
        named = [e for e in brief["caveats"] if e["status"] == NOT_CARRIED]
        print(f"\n{label}:")
        for entry in brief["caveats"]:
            print(f"  {entry['ref']:<18} {entry['status']:<14} {entry['misreading'][:50]}")
        print(f"  carried or indeterminate {len(brief['caveats']) - len(named)} "
              f"of {len(READING_INSTRUCTIONS)}, named as not carried {len(named)}")
    print("\n  -> §5's negative #4 is met by the escape clause, not by prevention: the")
    print("     brief states its own gaps rather than carrying everything. The §B2 gap")
    print("     closes with one extra call that the composite chain does not make.")


def c26_a_third_of_briefs_have_no_number(scored: pd.DataFrame) -> None:
    """§C26. How often the headline is a state rather than a value, and why that matters."""
    rule("C26. A third of market-weeks cannot print a D at all, and now say which kind")
    states = scored["score_state_sell"].value_counts()
    print(states.to_string())
    null = scored["damage_sell_pct"].isna()
    print(f"\nrows with no headline number: {null.sum():,} of {len(scored):,} "
          f"({null.mean():.1%})")
    print("  before the state column, every one of these rendered as a blank cell, which")
    print("  reads as a low value. Two causes, opposite meanings, one rendering.")

    latest = scored[scored["report_date"] == scored["report_date"].max()]
    print(f"\nlatest week ({pd.Timestamp(latest['report_date'].iloc[0]).date()}):")
    print(latest["score_state_sell"].value_counts().to_string())


def c27_indeterminate_is_two_states(scored: pd.DataFrame) -> None:
    """§C27. The `§A17` marker is silent for two unrelated reasons, not one."""
    rule("C27. `indeterminate` has two causes and §C21 measured only one of them")
    ind = scored[scored["unwind_state_sell"] == "indeterminate"]
    no_delta = ind["d_damage_sell_pct"].isna()
    print(f"indeterminate rows: {len(ind):,} of {len(scored):,}")
    print(f"  no prior scored week (no ΔD to read): {int(no_delta.sum()):,} "
          f"({no_delta.mean():.1%})")
    print(f"  ΔD exists, flow state carries nothing: {int((~no_delta).sum()):,} "
          f"({(~no_delta).mean():.1%})")
    silent = ind[~no_delta]
    print(f"    all falling: {int((silent['d_damage_sell_pct'] < 0).sum()):,}")
    print("    by flow state:")
    print(silent["flow_state"].value_counts(dropna=False).to_string())
    print("\n  -> a reader acts differently on the two. One says the series is too young to")
    print("     difference; the other says this week's move cannot be interpreted.")

    print("\nthe full marker, over every row:")
    print(scored["unwind_state_sell"].value_counts().to_string())


def worked_brief(scored: pd.DataFrame, ladder: pd.DataFrame) -> None:
    """One real brief, printed whole. House style: the artifact, not a description of it."""
    rule("The brief itself, LIVE CATTLE, latest week")
    week = pd.to_datetime(scored["report_date"]).max()
    print(format_brief(market_brief(scored, MARKET, report_date=week, ladder=ladder)))


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 240)
    per_category, scored = build()
    scored["report_date"] = pd.to_datetime(scored["report_date"])
    ladder = coverage_ladder(per_category, scored)

    c25_the_ledger_over_the_five(scored, ladder)
    c26_a_third_of_briefs_have_no_number(scored)
    c27_indeterminate_is_two_states(scored)
    worked_brief(scored, ladder)


if __name__ == "__main__":
    main()
