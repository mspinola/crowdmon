"""Flow decomposition: the four states, the gap rule, and key integrity.

The classification tests use synthetic panels, because the states are definitions and a
definition deserves an unambiguous case. The gap and shutdown tests use the committed real
panels, because those are claims about what the data actually does.
"""
import pandas as pd
import pytest

from crowdmon.futures import decompose, tolerance_sensitivity
from crowdmon.futures.flow import (
    GAP,
    LONG_LIQUIDATION,
    MIXED,
    NEW_LONGS,
    NEW_SHORTS,
    QUIET,
    SHORT_COVERING,
    FlowError,
)
from crowdmon.futures.io import PanelError

PURE = (NEW_LONGS, SHORT_COVERING, NEW_SHORTS, LONG_LIQUIDATION)


# ── The four pure states (handoff §7, "Classification") ─────────────────────
@pytest.mark.parametrize("legs, expected", [
    # ΔLong +5000, ΔShort +50: the short leg is 1% of the long leg, well inside any
    # tolerance, so the long leg names the state.
    ([(10_000, 5_000), (15_000, 5_050)], NEW_LONGS),
    ([(10_000, 5_000), (10_050, 1_000)], SHORT_COVERING),
    ([(10_000, 5_000), (10_050, 9_000)], NEW_SHORTS),
    ([(10_000, 5_000), (6_000, 5_050)], LONG_LIQUIDATION),
])
def test_each_pure_state(make_panel, legs, expected):
    flows = decompose(make_panel({"managed_money": legs}))
    assert list(flows["flow_state"]) == [expected]


def test_both_legs_moving_is_mixed_not_a_direction(make_panel):
    """`mixed` is an answer, not a failure to decide.

    A category adding 5,000 longs and 4,800 shorts is two sets of traders doing opposite
    things. Calling it `new_longs` because the long leg is marginally larger would be the
    single most misleading thing this module could do, since the label is what a reader
    uses to decide whether a move has fuel behind it.
    """
    flows = decompose(make_panel({"managed_money": [(10_000, 5_000), (15_000, 9_800)]}))
    assert flows["flow_state"].iloc[0] == MIXED


def test_neither_leg_moving_is_quiet_not_liquidation(make_panel):
    """Zero is the absence of a change, not a small change, so it needs no threshold.

    Without the explicit case this falls through the sign tests and lands on `mixed`,
    which is a plain misstatement: nothing was mixed and nothing happened.
    """
    flows = decompose(make_panel({"managed_money": [(10_000, 5_000), (10_000, 5_000)]}))
    assert flows["flow_state"].iloc[0] == QUIET


def test_short_covering_carries_its_fuel_and_nothing_else_does(make_panel):
    """`fuel_remaining` is the hard bound on how far a covering rally can still run.

    Populated only on `short_covering`. On any other state the outstanding short position
    is not fuel for anything, and a number in that cell would invite being read as though
    it were.
    """
    flows = decompose(make_panel({"managed_money": [
        (10_000, 5_000), (10_050, 1_000), (15_050, 1_050)]}))
    covering = flows[flows["flow_state"] == SHORT_COVERING]
    assert covering["fuel_remaining"].iloc[0] == 1_000
    assert flows[flows["flow_state"] != SHORT_COVERING]["fuel_remaining"].isna().all()


def test_first_observation_of_a_series_is_dropped_not_labelled(make_panel):
    """No predecessor means no weekly change. A row of nulls labelled `gap` would suggest
    a missing week where there is only a start."""
    flows = decompose(make_panel({"managed_money": [(10_000, 5_000), (11_000, 5_010)]}))
    assert len(flows) == 1


# ── Gap handling (handoff §7, "Gap handling" and "Shutdown window") ─────────
def test_a_long_gap_is_labelled_and_its_deltas_are_null(make_panel):
    """A 28-day interval must not produce a delta.

    Nulling the deltas rather than merely labelling them is the point: a `gap` row with a
    populated `d_net` is one careless `.sum()` away from being counted anyway, and the
    label exists precisely because the number is not comparable to a week.
    """
    panel = make_panel({"managed_money": [(10_000, 5_000), (40_000, 5_010)]},
                       dates=["2026-01-06", "2026-02-03"])
    flows = decompose(panel)
    assert flows["flow_state"].iloc[0] == GAP
    assert flows["days_elapsed"].iloc[0] == 28
    assert flows[["d_long", "d_short", "d_net", "d_oi"]].isna().all(axis=None)


def test_gap_tolerance_admits_holiday_shifts_when_asked(make_panel):
    """The 6/8-day holiday weeks are real flow, and the strict rule discards them.

    Measured on the real Disaggregated store, 2,850 of 2,965 gap-labelled rows in the
    liquid universe are these. Neither choice is free — admitting them compares a 6-day
    move against an 8-day one — so it is a parameter, and both settings are exercised.
    """
    panel = make_panel({"managed_money": [(10_000, 5_000), (15_000, 5_010)]},
                       dates=["2026-01-06", "2026-01-14"])  # 8 days
    assert decompose(panel)["flow_state"].iloc[0] == GAP
    assert decompose(panel, gap_days_tolerance=1)["flow_state"].iloc[0] == NEW_LONGS


def test_oats_long_absences_are_all_gaps(history_panel):
    """The thin-market case, which is what the gap rule is actually for.

    Oats falls below the reporting threshold, drops out of the report, and comes back. The
    longest interval in the committed fixture is 294 days. Without the rule, that single
    diff would enter every ranking as the largest weekly flow in the sample.
    """
    oats = history_panel[history_panel["market_code"] == "004603"]
    flows = decompose(oats)
    long_intervals = flows[flows["days_elapsed"] > 8]
    assert not long_intervals.empty, "fixture no longer exercises the long-gap path"
    assert long_intervals["days_elapsed"].max() >= 200
    assert (long_intervals["flow_state"] == GAP).all()
    assert long_intervals[["d_long", "d_short", "d_net"]].isna().all(axis=None)


def test_the_2025_shutdown_window_produces_no_anomalous_flow(history_panel):
    """Oct-Nov 2025, and the premise here did not survive measurement.

    The handoff expected the shutdown to read as one enormous week of flow. It does not:
    CFTC published the backlog with the correct as-of Tuesdays, so report dates run weekly
    straight through the window and there is no hole to bridge. The only interruption is
    the 2025-11-10 / 2025-11-18 pair, which is a Veterans Day holiday shift.

    What this asserts is therefore the real property: no flow computed in the window is
    anomalous against the same market's own 2025 distribution. Where the shutdown does
    land is the RELEASE date, which is `derived` (inferred) for every week of the window,
    and that is `cot_adapter`'s problem rather than this module's.
    """
    flows = decompose(history_panel)
    window = flows[(flows["report_date"] >= "2025-09-15")
                   & (flows["report_date"] <= "2025-12-15")
                   & (flows["market_code"] != "004603")]  # oats is genuinely absent
    assert not window.empty

    # No report-date hole: every interval is a week or a holiday shift.
    assert window["days_elapsed"].between(6, 8).all()

    year = flows[(flows["report_date"].dt.year == 2025)
                 & (flows["market_code"] != "004603")]
    ceiling = year["d_net"].abs().quantile(0.99)
    assert window["d_net"].abs().max() <= ceiling, (
        "a shutdown-window flow exceeds the 99th percentile of the same year, which is "
        "what a bridged multi-week gap would look like")


# ── Key integrity (handoff §7) ──────────────────────────────────────────────
def test_deltas_never_cross_a_market_boundary(make_panel):
    """Two markets interleaved must not difference into each other.

    The failure would be silent and enormous: gold's position minus crude's, labelled as a
    week of gold flow.
    """
    a = make_panel({"managed_money": [(10_000, 5_000), (10_100, 5_010)]}, market_code="AAA")
    b = make_panel({"managed_money": [(90_000, 1_000), (90_100, 1_010)]}, market_code="BBB")
    flows = decompose(pd.concat([a, b], ignore_index=True))
    assert len(flows) == 2
    assert set(flows["d_long"]) == {100.0}


def test_deltas_never_cross_the_combined_boundary(make_panel):
    """Futures-only and futures-and-options-combined are different series (spec §3).

    Only futures-only is fetched today, so `combined` is constant-False and this asserts
    nothing about current data. It is here so that the day the combined files are added,
    mixing them is a test failure rather than a discovery in a result months later.
    """
    a = make_panel({"managed_money": [(10_000, 5_000), (10_100, 5_010)]}, combined=False)
    b = make_panel({"managed_money": [(90_000, 1_000), (90_100, 1_010)]}, combined=True)
    flows = decompose(pd.concat([a, b], ignore_index=True))
    assert len(flows) == 2
    assert set(flows["d_long"]) == {100.0}


def test_two_vintages_of_one_week_are_refused(make_panel):
    """A duplicate (key, date) is two vintages, and differencing them would call a CFTC
    revision a week of flow. There is no safe guess, so it raises."""
    panel = make_panel({"managed_money": [(10_000, 5_000), (11_000, 5_010)]})
    doubled = pd.concat([panel, panel.iloc[[1]]], ignore_index=True)
    with pytest.raises(PanelError, match="VINTAGES"):
        decompose(doubled)


def test_an_out_of_range_tolerance_is_refused(make_panel):
    with pytest.raises(FlowError, match=r"\[0, 1\]"):
        decompose(make_panel({"managed_money": [(1, 1), (2, 2)]}), tolerance=1.5)


# ── The tolerance is a parameter, so its effect is measured ─────────────────
def test_tolerance_changes_whether_we_commit_never_which_way(history_panel):
    """The finding that makes the tolerance tolerable.

    Across 0.15 to 0.40 roughly 29% of weeks change label on the real panel, which is a
    lot. But every one of those changes is `mixed` becoming pure: not one week flips from
    one direction to another. That is structural rather than lucky — the dominant leg is
    `argmax|Δ|` and does not depend on the tolerance, which only gates whether the smaller
    leg disqualifies the label — and it is asserted because an implementation that broke
    it would still produce a plausible-looking distribution.
    """
    loose = decompose(history_panel, tolerance=0.40)["flow_state"].to_numpy()
    tight = decompose(history_panel, tolerance=0.15)["flow_state"].to_numpy()
    changed = tight != loose
    assert changed.mean() > 0.05, "fixture no longer exercises the tolerance"
    flipped = [(t, ls) for t, ls in zip(tight[changed], loose[changed])
               if t in PURE and ls in PURE]
    assert not flipped, f"tolerance flipped a direction, not just a commitment: {flipped[:3]}"


def test_sensitivity_table_reports_every_tolerance_and_the_churn(history_panel):
    table = tolerance_sensitivity(history_panel)
    assert list(table.index) == [0.15, 0.25, 0.40]
    assert table.loc[0.25, "reclassified_vs_base"] == 0.0
    # The gap and quiet shares are tolerance-independent by construction: neither is
    # decided by the dominance rule. A change here means the gap rule moved.
    assert table["gap"].nunique() == 1
    assert table["quiet"].nunique() == 1
