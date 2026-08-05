"""The stratum classifier against a REAL store. Skips when there is not one.

**This file is what makes the promotion a promotion rather than a rewrite.** The
classification lived in `docs/analysis/reproduce.py::_spec_class`, and `2026-08-03 §C13` and
`§C14` are the numbers it produced. Moving logic into `src/` is only safe if the moved copy
gives the same partition, and "same" here is checkable to the individual code: `§C14` states
that the seven differentials are the complete list rather than examples, so a classifier
that finds six or eight has changed the finding.

`test_stratum.py` asserts the rules on constructed names, where they are definitions. This
asserts they still cut the real universe where they cut it, and it is the only thing that
would catch the CFTC renaming a venue.
"""
import pytest

pytestmark = pytest.mark.needs_vintage

#: `§C14`, on the vintage panel's latest report week: the whole 279-code Disaggregated
#: universe partitioned three ways. `§C13` counts the same partition from the other end.
LATEST_WEEK = {"certificate": 213, "differential": 7, "outright": 59}

#: `§C14`'s seven, and it says explicitly that this is the complete list.
DIFFERENTIAL_CODES = {"0676A5", "067A71", "022A13", "0676A6", "111A34", "86465A", "86565A"}

#: `§C23`'s two panel shapes, which are why `§C8`'s obligation cannot fire today.
VINTAGE_CERTIFICATE_MARKETS = 263

#: 27 when `§C23` measured it, **29 since `§D11`'s tranche** added rough rice and ICE Europe
#: WTI to the current-state store (`2026-08-05 §E4`). The number moved; the finding did not,
#: and the finding is the line below it: still 0 certificates and 0 differentials, so the
#: covered set remains the COMPLEMENT of what makes the vintage panel hard to reason about
#: rather than a sample of it.
CURRENT_STATE_MARKETS = 29


@pytest.fixture(scope="module")
def panels():
    pytest.importorskip("cotdata")
    from crowdmon.futures import from_current_store, from_vintage

    try:
        vintage = from_vintage(report_type="disaggregated")
        current = from_current_store()
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    if vintage.empty or current.empty:
        pytest.skip("no readable store: a panel came back empty")
    return vintage, current


def test_the_latest_week_partitions_exactly_where_C14_partitioned_it(panels):
    from crowdmon.futures import classify, stratum_summary

    vintage, _ = panels
    latest = vintage[vintage["report_date"] == vintage["report_date"].max()]
    summary = stratum_summary(classify(latest))
    got = dict(zip(summary["stratum"], summary["markets"]))

    assert {k: int(v) for k, v in got.items() if k in LATEST_WEEK} == LATEST_WEEK, (
        f"the promoted classifier no longer reproduces §C14: {got}. Either a venue was "
        f"renamed or a token stopped matching, and the amendment needs re-measuring rather "
        f"than these numbers nudging.")
    assert sum(LATEST_WEEK.values()) == int(summary["markets"].sum())


def test_the_seven_differentials_are_still_exactly_seven_and_still_those_seven(panels):
    """`§C14` says the list is complete, so an eighth is a finding and a sixth is a bug."""
    from crowdmon.futures import classify, differential_matches

    vintage, _ = panels
    latest = vintage[vintage["report_date"] == vintage["report_date"].max()]
    matches = differential_matches(classify(latest))

    assert set(matches["market_code"]) == DIFFERENTIAL_CODES
    assert matches["matched_on"].str.len().gt(0).all(), (
        "every differential must name the token that caught it, or the heuristic is not "
        "auditable and `/` in particular is broad")


def test_no_covered_market_is_a_certificate_or_a_differential(panels):
    """`§C13`: the covered set is real outright throughout, and it is the COMPLEMENT of the
    thing that made the panel hard to reason about rather than a sample of it.

    25 of 25 when `§C13` measured it, 27 of 27 at `§D11`, **29 of 29 now**. The count is the
    part that moves; the zero on both other strata is the claim.
    """
    from crowdmon.futures import classify, stratum_summary

    _, current = panels
    summary = stratum_summary(classify(current))
    got = {k: int(v) for k, v in zip(summary["stratum"], summary["markets"])}

    assert got["certificate"] == 0 and got["differential"] == 0
    assert got["outright"] == CURRENT_STATE_MARKETS


def test_the_band_obligation_has_the_markets_on_one_panel_and_the_percentile_on_the_other(
        panels):
    """`§C23` restated through the shipped classifier, which is `§C29`'s whole point.

    The classification is live on both panels. The OBLIGATION is vacuous, because the panel
    carrying the markets `§C8` names cannot produce a `pct(D)` and the panel that can
    produce one carries none of them.
    """
    from crowdmon.futures import classify, stratum_summary
    from crowdmon.futures.composite import DEFAULT_MIN_PERIODS

    vintage, current = panels
    vintage_summary = stratum_summary(classify(vintage))
    got = {k: int(v) for k, v in zip(vintage_summary["stratum"],
                                     vintage_summary["markets"])}
    assert got["certificate"] == VINTAGE_CERTIFICATE_MARKETS

    weeks = vintage["report_date"].nunique()
    assert weeks < DEFAULT_MIN_PERIODS, (
        f"the vintage panel now has {weeks} weeks against a {DEFAULT_MIN_PERIODS}-week "
        f"min_periods, so §C8's rule has stopped being vacuous and §C29 needs revisiting. "
        f"This test failing is the event it was written to announce.")
    assert current["report_date"].nunique() >= DEFAULT_MIN_PERIODS
