"""The market-week brief, §3 of `docs/handoffs/2026-08-03-report-layer.md`.

**Most of what is asserted here is that the brief states its own gaps**, because that is the
one thing the handoff pre-registered as a hard ship condition. §5's negative #4 names the
partial brief as the likeliest and the most dangerous outcome: four warnings carried and the
fifth silently omitted reads as complete, so the reader stops looking, where a bare frame at
least announces that it is bare.

So the load-bearing test is `test_a_frame_with_no_carriers_still_names_all_five`. A brief
built from a frame carrying none of the optional columns must still print every one of
`READING_INSTRUCTIONS` with a reason, and if that ever regresses to quiet omission the
artifact has become the thing it was built to prevent.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import add_composite, add_score_state, add_unwind_state
from crowdmon.futures.brief import (
    CARRIED,
    INDETERMINATE,
    NOT_CARRIED,
    READING_INSTRUCTIONS,
    BriefError,
    caveat_ledger,
    format_brief,
    market_brief,
)

WEEKS = 260
MARKET = "TEST01"


def _scored(n: int = WEEKS, *, seed: int = 0) -> pd.DataFrame:
    """A composite frame at the shape `add_composite` emits, plus a score state."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-02", periods=n, freq="7D")
    base = {"market_code": MARKET, "report_type": "disaggregated", "combined": False}
    fragility = pd.DataFrame([{
        **base, "report_date": d, "market_name": "TEST MARKET", "phi": 0.4,
        "phi_denominator_covered": 0.83, "q_sell": 1000.0, "q_buy": 900.0,
        "dtl_sell": v, "dtl_buy": v * 0.5,
    } for d, v in zip(dates, rng.uniform(1, 20, n))])
    extremity = pd.DataFrame([{
        **base, "report_date": d, "category": "managed_money", "net_risk_usd_z": z,
    } for d, z in zip(dates, rng.normal(size=n))])
    return add_score_state(add_composite(fragility, extremity, min_periods=52))


def _flows(scored: pd.DataFrame, state: str) -> pd.DataFrame:
    return pd.DataFrame({
        "report_date": scored["report_date"], "market_code": scored["market_code"],
        "report_type": "disaggregated", "combined": False,
        "category": "managed_money", "flow_state": state,
    })


def _latest(scored: pd.DataFrame) -> pd.Timestamp:
    return pd.to_datetime(scored["report_date"]).max()


# ── §5's negative #4, which is the whole ship condition ─────────────────────
def test_a_frame_with_no_carriers_still_names_all_five():
    """The pre-registered rule: carry every misreading, or NAME the ones you do not.

    This frame has no `beta`, no `unwind_state` and no ladder, so the brief can carry none
    of the five on its own. Every one must still appear, with a status and a reason. A
    ledger that shrank to the caveats it happened to be able to answer would be exactly the
    output that "reads as complete".
    """
    brief = market_brief(_scored(), MARKET)
    assert len(brief["caveats"]) == len(READING_INSTRUCTIONS)
    assert {c["ref"] for c in brief["caveats"]} == {c.ref for c in READING_INSTRUCTIONS}
    assert all(c["status"] == NOT_CARRIED for c in brief["caveats"])
    assert all(c["detail"] for c in brief["caveats"]), "a gap named without a reason"

    text = format_brief(brief)
    for caveat in READING_INSTRUCTIONS:
        assert caveat.ref in text, f"{caveat.ref} vanished from the rendered brief"
        assert caveat.misreading.split(",")[0] in text
        assert caveat.source in text, "a gap must be checkable, so it carries its source"


def test_every_caveat_cites_a_path_and_a_reproducer():
    """This repo's citation convention, applied to the one artifact that leaves it.

    A bare `§B34` names neither a repo nor a file, and three sessions in a row failed to
    resolve one. `tests/test_references.py` makes the bare form fail loudly; here the brief
    is held to the stricter form, because its reader is by construction someone who does
    not have the code.
    """
    for caveat in READING_INSTRUCTIONS:
        assert "docs/" in caveat.source, f"{caveat.ref} cites no path"
        assert "::" in caveat.source, f"{caveat.ref} cites no reproducer function"


def test_format_brief_cannot_be_asked_to_omit_the_ledger():
    """No `include_caveats=False`. The bare number is the thing this module exists to stop."""
    import inspect

    assert list(inspect.signature(format_brief).parameters) == ["brief"]


# ── the carriers, when they are attached ────────────────────────────────────
def test_attaching_the_carriers_moves_two_of_the_five_to_carried():
    scored = add_unwind_state(_scored(), _flows(_scored(), "long_liquidation"))
    scored["beta"] = 0.63
    ledger = {c["ref"]: c for c in market_brief(scored, MARKET)["caveats"]}

    assert ledger["2026-08-02 §B2"]["status"] == CARRIED
    assert "0.63" in ledger["2026-08-02 §B2"]["detail"]
    assert ledger["2026-08-01 §A17"]["status"] in (CARRIED, INDETERMINATE)
    # The three the gate found un-carryable stay un-carryable however rich the frame is.
    for ref in ("2026-08-01 §A21", "2026-08-01 §A22", "2026-08-03 §C3"):
        assert ledger[ref]["status"] == NOT_CARRIED


def test_indeterminate_is_spoken_rather_than_left_blank():
    """`2026-08-03 §C21` in the rendering: silence on 3 falling weeks in 5 reads as safety."""
    scored = _scored()
    scored = add_unwind_state(scored, _flows(scored, "mixed"))
    falling = scored[(scored["d_damage_sell_pct"] < 0)
                     & (scored["unwind_state_sell"] == "indeterminate")]
    assert not falling.empty, "the fixture no longer contains a falling week"

    brief = market_brief(scored, MARKET, report_date=falling["report_date"].iloc[0])
    entry = {c["ref"]: c for c in brief["caveats"]}["2026-08-01 §A17"]

    assert entry["status"] == INDETERMINATE
    assert "INDETERMINATE" in format_brief(brief)
    assert "INDETERMINATE" in entry["detail"]


def test_an_unknown_carrier_column_fails_rather_than_defaulting():
    """"Is this value present" is not "does this value answer the caveat" (`§C22`)."""
    brief = market_brief(_scored(), MARKET)
    brief["caveats"] = ()
    from crowdmon.futures import brief as module

    extra = module.Caveat(ref="2026-08-01 §A1", misreading="x", source="docs/x.md::y",
                          column="phi")
    original = module.READING_INSTRUCTIONS
    module.READING_INSTRUCTIONS = original + (extra,)
    try:
        with pytest.raises(BriefError, match="no status function"):
            caveat_ledger(brief)
    finally:
        module.READING_INSTRUCTIONS = original


# ── the degenerate inputs §2 of the handoff lists ───────────────────────────
def test_a_row_that_did_not_score_never_renders_a_number():
    """"Not yet scoreable" and "scored, and low" must not render identically."""
    scored = _scored()
    early = scored[scored["score_state_sell"] == "warmup"]
    assert not early.empty, "the fixture no longer contains a warm-up week"

    brief = market_brief(scored, MARKET, report_date=early["report_date"].iloc[0])
    assert brief["damage_pct"] is None and brief["damage"] is None

    text = format_brief(brief)
    assert "NOT SCORED (warmup)" in text
    assert "will score later" in text
    assert "percentile of its own history" not in text


def test_the_two_null_causes_render_differently():
    scored = _scored()
    states = {s: scored[scored["score_state_sell"] == s] for s in ("warmup", "no_crowding")}
    for state, rows in states.items():
        assert not rows.empty, f"the fixture no longer contains a {state} week"
    texts = {state: format_brief(market_brief(scored, MARKET,
                                              report_date=rows["report_date"].iloc[0]))
             for state, rows in states.items()}
    assert texts["warmup"] != texts["no_crowding"]
    assert "too early, not safe" in texts["warmup"]
    assert "crowding factor is null" in texts["no_crowding"]


def test_q_sell_and_q_buy_are_printed_apart_and_never_totalled():
    text = format_brief(market_brief(_scored(), MARKET))
    assert "Q_sell 1,000.0" in text and "Q_buy 900.0" in text
    assert "1,900" not in text, "the sum describes an event that cannot occur"
    assert "never added" in text


def test_a_missing_ladder_is_declared_rather_than_passed_over():
    text = format_brief(market_brief(_scored(), MARKET))
    assert "no ladder supplied" in text

    ladder = pd.DataFrame([{"market_code": MARKET, "market_name": "TEST MARKET",
                            "weeks": WEEKS, "drops_at": "crowding"}])
    text = format_brief(market_brief(_scored(), MARKET, ladder=ladder))
    assert "UNSCOREABLE" in text and "crowding" in text


def test_phi_is_never_offered_against_a_ceiling_of_one():
    text = format_brief(market_brief(_scored(), MARKET))
    assert "0.8300, not 1.0" in text


# ── refusals ────────────────────────────────────────────────────────────────
def test_a_frame_without_a_score_state_is_refused():
    """Applying it here would be a derivation in the rendering, and the state is required."""
    scored = _scored().drop(columns=["score_state_sell"])
    with pytest.raises(BriefError, match="add_score_state"):
        market_brief(scored, MARKET)


def test_two_rows_for_one_market_week_are_refused():
    scored = _scored()
    doubled = pd.concat([scored, scored.tail(1)], ignore_index=True)
    with pytest.raises(BriefError, match="A brief describes one"):
        market_brief(doubled, MARKET, report_date=_latest(scored))


def test_an_absent_market_is_refused_rather_than_returning_an_empty_brief():
    with pytest.raises(BriefError, match="no rows for market_code"):
        market_brief(_scored(), "NOPE")


def test_the_footer_states_that_the_assembly_is_mostly_convenience():
    """`2026-08-03 §C24`: `E = 1`, and a reader must not infer safety from completeness."""
    text = format_brief(market_brief(_scored(), MARKET))
    assert "convenience rather than safety" in text
    assert "§C24" in text
    assert "not a trade list" in text
