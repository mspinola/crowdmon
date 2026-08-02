"""`cotdata.vintage_flow.decompose` is not a rival implementation, it is a corner of this one.

Flow decomposition exists in two packages, and the 2026-08-01 handoff closed leaving that
as its one open decision. The relationship was written down as "both are defensible and they
answer slightly different questions", which is true of the *outputs* and badly understates
what is actually going on underneath: **the two classifiers are the same function**, and
`cotdata`'s is this one evaluated at `tolerance=1.0` with gap labelling switched off.

That is not a coincidence to be admired, it is an invariant to be pinned. Two copies of one
algorithm in two repos drift, and the drift is invisible because each has its own passing
tests. These assertions fail the moment either side changes its classification rule, which
is the whole point: the duplication is now *managed* rather than merely known about.

Why the dedup cannot go the obvious way: `tests/test_boundaries.py` forbids `cotdata` from
importing `crowdmon` (a producer importing its consumer), so `cotdata` cannot delegate here.
The check therefore lives on this side, which may import `cotdata` freely.

Offline: `vintage_flow.decompose` takes a DataFrame and touches no store.
"""
import pandas as pd
import pytest

from crowdmon.futures import decompose
from crowdmon.futures.flow import GAP, MIXED
from crowdmon.futures.io import SERIES_KEY

vintage_flow = pytest.importorskip("cotdata.vintage_flow")

#: Gap labelling off. Any interval is admitted, which is `cotdata`'s behaviour: it emits
#: `days_elapsed` and leaves the judgement to the caller rather than nulling the row.
NO_GAP = 100_000


def _joined(panel: pd.DataFrame, **kwargs) -> pd.DataFrame:
    mine = decompose(panel, **kwargs)
    theirs = vintage_flow.decompose(panel)
    key = SERIES_KEY + ["report_date"]
    return mine[key + ["flow_state", "d_long", "d_short", "d_net"]].merge(
        theirs[vintage_flow.SERIES_KEY + ["report_date", "state", "d_long", "d_short", "d_net"]],
        on=key, how="outer", suffixes=("_mine", "_theirs"), indicator=True)


def test_at_tolerance_one_with_gaps_off_the_two_agree_exactly(history_panel):
    """The equivalence, on 20 years and 27 markets of real committed data.

    Measured on the full store this is 135,835 rows and 100.000000% agreement with zero
    mismatches. If this ever fails, one of the two classifiers has changed and the
    characterisation in `flow.py`'s docstring has become false.
    """
    both = _joined(history_panel, tolerance=1.0, gap_days_tolerance=NO_GAP)
    assert (both["_merge"] == "both").all(), "the two produce different row sets"
    assert not both.empty
    mismatched = both[both["flow_state"] != both["state"]]
    assert mismatched.empty, (
        f"{len(mismatched)} labels differ at tolerance=1.0, e.g.\n"
        f"{mismatched.head(5).to_string(index=False)}")


def test_the_deltas_themselves_are_identical(history_panel):
    """Same differencing, same sort, same group key. Only the LABELLING ever differed."""
    both = _joined(history_panel, tolerance=1.0, gap_days_tolerance=NO_GAP)
    for col in ("d_long", "d_short", "d_net"):
        mine, theirs = both[f"{col}_mine"], both[f"{col}_theirs"]
        assert mine.isna().equals(theirs.isna()), f"{col}: nulls differ"
        assert (mine.dropna().to_numpy() == theirs.dropna().to_numpy()).all(), f"{col} differs"


def test_the_only_two_differences_are_mixed_and_gap(history_panel):
    """At the DEFAULT tolerance, every disagreement is one of exactly two kinds.

    Either this module declined to commit (`mixed`) where `cotdata` named the dominant leg,
    or it refused the interval (`gap`) where `cotdata` differenced across it anyway. There
    is no third kind, and in particular there is never a straight contradiction: the two
    never name *different* directions for the same week.
    """
    both = _joined(history_panel)
    disagree = both[both["flow_state"] != both["state"]]
    assert not disagree.empty, "fixture no longer exercises the disagreement"
    assert set(disagree["flow_state"]) <= {MIXED, GAP}, (
        f"a disagreement that is neither mixed nor gap: "
        f"{sorted(set(disagree['flow_state']) - {MIXED, GAP})}")


def test_neither_ever_names_the_opposite_direction(history_panel):
    """The strong form, and the reason the duplication was never a correctness bug.

    Where both commit to a direction, they agree. Not "mostly agree": the dominant leg is
    `argmax(|Dlong|, |Dshort|)` in both, and the tolerance only gates whether the smaller
    leg disqualifies the label, so a pure state can become `mixed` but can never become a
    DIFFERENT pure state. Asserted rather than trusted, because an implementation that broke
    it would still produce a plausible-looking distribution.
    """
    both = _joined(history_panel)
    committed = both[~both["flow_state"].isin([MIXED, GAP])]
    assert not committed.empty
    assert (committed["flow_state"] == committed["state"]).all()
