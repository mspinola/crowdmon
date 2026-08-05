"""The two caveat carriers against a REAL store. Skips when there is not one.

`test_composite.py` checks the classification rules on constructed frames, where they are
definitions and cannot be wrong. This file checks the two things a constructed frame cannot:
that the rules still say on the real panel what `2026-08-03 §C20` and `§C21` measured, and
that the brief assembles from the column names the real chain actually produces.

The second is the quieter risk. A brief is pure selection over a dozen columns from six
modules, so a rename anywhere upstream turns a carried caveat into a `not_carried` one and
the output stays perfectly well-formed while saying less. Nothing in the fixture suite would
notice, because the fixture frames are built here.

Figures pinned from `docs/analysis/reproduce_report_gate.py`, sections `§C20` and `§C21` of
[`../docs/design/amendments-2026-08-03.md`](../docs/design/amendments-2026-08-03.md).
"""
import pandas as pd
import pytest

pytestmark = pytest.mark.needs_vintage

#: `§C20`, measured on a 27,194-week current-state Disaggregated panel and re-measured on
#: **29,133 weeks** at `2026-08-05 §E4`. Historical rows, so these do not move when a new
#: WEEK lands, and the note here used to stop there: it said a change meant the store was
#: restated or backfilled. **It missed the third way, which is the one that happened.** A
#: new MARKET arrives with twenty years of its own history attached, so it moves a
#: historical count without restating a single existing row.
#:
#: `§D11`'s tranche is the whole of the difference and it reconciles exactly: rough rice
#: contributes 1,051 weeks and ICE Europe WTI 888, summing to the 1,939 the panel grew by,
#: and each contributes 103 warm-up and 206 missing-term rows. Nothing already in the panel
#: changed, which is what a restatement WOULD have done and is the reason these are still
#: exact equalities rather than bands.
WARMUP_NULLS = 2_781
MISSING_TERM_NULLS = 6_668

#: `§C21`. Falling weeks accumulate as the panel grows, so the count is a floor and the
#: share is a band. The share is the finding: the marker answers on two falling weeks in
#: five and is silent on the other three.
FALLING_WEEKS_AT_LEAST = 8_559
DECISIVE_SHARE = 0.402


@pytest.fixture(scope="module")
def scored():
    """The composite chain, then both carriers, as `reproduce_report_gate.build` runs it."""
    pytest.importorskip("cotdata")
    from crowdmon.futures import (
        ContractMaster,
        add_composite,
        add_extremity,
        add_notional,
        add_risk_units,
        add_score_state,
        add_unwind_state,
        add_volume,
        decompose,
        from_current_store,
        market_fragility,
        rank_markets,
    )

    try:
        panel = from_current_store()
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    if panel.empty or panel["market_code"].nunique() < 20:
        pytest.skip("no readable store: too few markets for a composite panel")
    try:
        master = ContractMaster.load()
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no contract_specs table: {exc}")

    per_category = add_volume(add_extremity(add_risk_units(
        add_notional(master.annotate(panel)))))
    volume = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
              .max().reset_index())
    per_market = market_fragility(panel).merge(
        volume, on=["report_date", "market_code"], how="left")
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    out = add_score_state(add_composite(ranked, per_category))
    return add_unwind_state(out, decompose(panel)), per_category


def test_the_two_null_causes_split_where_C20_measured_them(scored):
    """`§C20`'s table, reproduced by the shipped function rather than by a script."""
    out, _ = scored
    states = out["score_state_sell"].value_counts()

    assert int(states.get("warmup", 0)) == WARMUP_NULLS
    assert int(states.get("no_crowding", 0)
               + states.get("no_illiquidity", 0)
               + states.get("no_fragility", 0)) == MISSING_TERM_NULLS


def test_the_separating_rule_still_has_zero_exceptions(scored):
    """The claim that makes the state trustworthy, and the only one worth re-running.

    Every warm-up row carries all three factors and every non-warm-up null is missing one.
    If a future change to the composite let a factor go null without nulling `damage`, this
    is what would catch it, and `add_score_state` would raise before it got here.
    """
    out, _ = scored
    terms = ["crowding_long", "illiquidity_sell", "fragility"]
    warm = out["score_state_sell"] == "warmup"
    assert out.loc[warm, terms].notna().all().all()
    assert out.loc[warm, "damage_sell"].notna().all()
    assert out.loc[warm, "damage_sell_pct"].isna().all()

    scored_rows = out["score_state_sell"] == "scored"
    assert out.loc[scored_rows, "damage_sell_pct"].notna().all()
    assert (out["score_state_sell"] == "scored").sum() + WARMUP_NULLS \
        + MISSING_TERM_NULLS == len(out)


def test_the_unwind_marker_is_silent_on_three_falling_weeks_in_five(scored):
    """`§C21`. The finding is the SILENCE, so that is what is asserted, not the signal."""
    out, _ = scored
    falling = out[out["d_damage_sell_pct"] < 0]
    assert len(falling) >= FALLING_WEEKS_AT_LEAST

    states = falling["unwind_state_sell"].value_counts()
    decisive = int(states.get("mid_exit", 0) + states.get("falling_not_exit", 0))
    assert decisive / len(falling) == pytest.approx(DECISIVE_SHARE, abs=0.03), (
        "the share of falling weeks the flow state can speak to has moved. §C21 is the "
        "reason `indeterminate` is a rendered value rather than a blank, so a large move "
        "here changes what the brief should say.")
    assert int(states.get("indeterminate", 0)) == len(falling) - decisive


def test_a_real_market_week_assembles_into_a_brief_that_names_its_gaps(scored):
    """The rename guard. Every carried caveat has to still find its column."""
    from crowdmon.futures import coverage_ladder
    from crowdmon.futures.brief import (
        NOT_CARRIED,
        READING_INSTRUCTIONS,
        format_brief,
        market_brief,
    )

    out, per_category = scored
    live = out[out["score_state_sell"] == "scored"]
    week = pd.to_datetime(live["report_date"]).max()
    code = live[pd.to_datetime(live["report_date"]) == week]["market_code"].iloc[0]

    brief = market_brief(out, code, report_date=week,
                         ladder=coverage_ladder(per_category, out))
    assert brief["damage_pct"] is not None
    assert brief["phi_ceiling"] is not None, "phi_denominator_covered stopped arriving"
    assert brief["q_sell"] is not None and brief["q_buy"] is not None
    assert brief["unwind_state"] is not None, "the §A17 carrier stopped arriving"
    assert brief["coverage"] is not None

    text = format_brief(brief)
    assert {c["ref"] for c in brief["caveats"]} == {c.ref for c in READING_INSTRUCTIONS}
    for caveat in READING_INSTRUCTIONS:
        assert caveat.ref in text
    # `beta` needs a price panel this fixture does not build, so it must be DECLARED
    # missing rather than dropped. That asymmetry is the whole ship condition.
    ledger = {c["ref"]: c for c in brief["caveats"]}
    assert ledger["2026-08-02 §B2"]["status"] == NOT_CARRIED
    assert "add_commonality" in ledger["2026-08-02 §B2"]["detail"]
