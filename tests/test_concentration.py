"""Concentration: CR4/CR8, module spec §6.2.

The published numbers need almost no computation, so what is tested is the handling: that
market-level columns repeated on category rows are reduced rather than summed, that the
`CR8 >= CR4` identity is enforced, and that the quadrant means what it says.
"""
import pandas as pd
import pytest

from crowdmon.futures import (
    add_concentration_extremity,
    concentration_vs_fragility,
    market_concentration,
    market_fragility,
    quadrant,
)
from crowdmon.futures.concentration import ConcentrationError


def _panel(rows, *, market_code="TEST01", date="2026-01-06") -> pd.DataFrame:
    """Category rows carrying the same market-level CR values, as the real schema does."""
    return pd.DataFrame([{
        "report_date": pd.Timestamp(date), "market_code": market_code,
        "market_name": "TEST MARKET", "report_type": "disaggregated", "combined": False,
        "category": category, "long_contracts": long_, "short_contracts": short_,
        "spread_contracts": 0, "open_interest": 100_000,
        "cr4_net_long": 40.0, "cr4_net_short": 55.0,
        "cr8_net_long": 60.0, "cr8_net_short": 70.0,
    } for category, long_, short_ in rows])


ROWS = [("managed_money", 50_000, 10_000), ("producer_merchant", 20_000, 60_000),
        ("swap", 15_000, 12_000), ("other_reportable", 10_000, 13_000),
        ("nonreportable", 5_000, 5_000)]


# ── The hazard: market-level columns on category rows ───────────────────────
def test_cr_columns_are_reduced_not_summed():
    """Same failure mode as `open_interest`: CR4 is the market's value repeated on each of
    five category rows, so summing gives 200% and puts every ratio in the system wrong."""
    out = market_concentration(_panel(ROWS))
    assert len(out) == 1
    assert out["cr4_net_long"].iloc[0] == 40.0
    assert out["cr8_net_short"].iloc[0] == 70.0


def test_a_summed_cr_is_caught_by_the_bounds_check():
    """The guard that would fire if someone changed `max` to `sum`."""
    panel = _panel(ROWS)
    panel["cr4_net_long"] = 40.0 * 5  # what summing five category rows would produce
    with pytest.raises(ConcentrationError, match=r"outside \[0, 100\]"):
        market_concentration(panel)


def test_cr8_below_cr4_is_impossible_and_refused():
    """The eight largest traders include the four largest, so the gap cannot be negative."""
    panel = _panel(ROWS)
    panel["cr8_net_long"] = 30.0  # below cr4_net_long of 40
    with pytest.raises(ConcentrationError, match="impossible"):
        market_concentration(panel)


# ── The derived columns ─────────────────────────────────────────────────────
def test_the_gap_is_traders_five_through_eight():
    out = market_concentration(_panel(ROWS)).iloc[0]
    assert out["cr8_minus_cr4_long"] == pytest.approx(20.0)   # 60 - 40
    assert out["cr8_minus_cr4_short"] == pytest.approx(15.0)  # 70 - 55


def test_the_ranked_side_is_the_more_concentrated_one_and_is_labelled():
    """A market is only as robust as its thinner side, so the max is what ranks. The label
    stops it being read as a direction, which it is not."""
    out = market_concentration(_panel(ROWS)).iloc[0]
    assert out["cr4_max_side"] == 55.0
    assert out["cr4_side"] == "short"

    panel = _panel(ROWS)
    # CR8 has to move with CR4 or the identity guard fires, which it did when this fixture
    # raised CR4 alone. The guard was right and the fixture was wrong.
    panel["cr4_net_long"] = 80.0
    panel["cr8_net_long"] = 88.0
    flipped = market_concentration(panel).iloc[0]
    assert flipped["cr4_max_side"] == 80.0
    assert flipped["cr4_side"] == "long"


# ── The quadrant ────────────────────────────────────────────────────────────
def test_the_quadrant_separates_few_from_forceable():
    """Concentration and fragility are different questions, and the interesting cell needs
    both: a few holders who are all forceable."""
    frames = []
    for i, (cr, phi_shape) in enumerate([
            (90.0, [("managed_money", 90_000, 0)]),        # few + forceable
            (90.0, [("producer_merchant", 90_000, 0)]),    # few + patient
            (10.0, [("managed_money", 90_000, 0)]),        # broad + forceable
            (10.0, [("producer_merchant", 90_000, 0)])]):  # broad + patient
        rows = phi_shape + [("swap", 5_000, 95_000)]
        panel = _panel(rows, market_code=f"M{i}")
        panel[["cr4_net_long", "cr4_net_short"]] = cr
        panel[["cr8_net_long", "cr8_net_short"]] = cr
        frames.append(panel)
    panel = pd.concat(frames, ignore_index=True)

    joined = concentration_vs_fragility(market_concentration(panel),
                                        market_fragility(panel))
    labels = quadrant(joined, cr_threshold=50.0, phi_threshold=0.5)
    assert set(labels) == {"few_and_forceable", "few_and_patient",
                           "broad_and_forceable", "diffuse_and_patient"}


def test_quadrant_thresholds_default_to_the_frames_own_medians():
    """Relative by construction, so exactly half the universe is 'high CR4' in any week.
    An absolute cut nobody has justified would be worse."""
    frames = []
    for i, cr in enumerate((10.0, 30.0, 70.0, 90.0)):
        panel = _panel(ROWS, market_code=f"M{i}")
        panel[["cr4_net_long", "cr4_net_short", "cr8_net_long", "cr8_net_short"]] = cr
        frames.append(panel)
    panel = pd.concat(frames, ignore_index=True)
    joined = concentration_vs_fragility(market_concentration(panel),
                                        market_fragility(panel))
    labels = quadrant(joined)
    assert labels.str.startswith("few").sum() == 2
    assert (~labels.str.startswith("few")).sum() == 2


# ── Against the real committed panel ────────────────────────────────────────
def test_cr_is_never_null_across_the_committed_history(history_panel):
    """Module spec §6.2 calls this the metric set COT gives away free. It is: zero percent
    null over twenty years, which is why it needs no coverage report."""
    out = market_concentration(history_panel)
    assert len(out) > 3_000
    for column in ("cr4_net_long", "cr4_net_short", "cr8_net_long", "cr8_net_short"):
        assert out[column].notna().all(), column
    assert (out["cr8_net_long"] >= out["cr4_net_long"]).all()
    assert (out["cr8_net_short"] >= out["cr4_net_short"]).all()


def test_concentration_extremity_is_trailing_like_every_other_window(history_panel):
    """Concentration levels are not comparable across markets, so the same
    percentile-against-own-history argument applies. Inherits `core.aggregate`, including its
    refusal of lookahead."""
    concentration = market_concentration(history_panel)
    scored = add_concentration_extremity(concentration, min_periods=52)
    assert "cr4_max_side_pct" in scored.columns
    assert scored["cr4_max_side_pct"].dropna().between(0.0, 1.0).all()

    early = add_concentration_extremity(
        concentration[concentration["report_date"] < "2018-01-01"], min_periods=52)
    overlap = scored[scored["report_date"] < "2018-01-01"]
    assert len(early) == len(overlap)


def test_a_legacy_panel_is_refused_with_the_reason(history_panel):
    """Legacy carries no CR columns at all, so the error names that rather than raising a
    KeyError on a column the caller never asked about."""
    with pytest.raises(ConcentrationError, match="absent from Legacy"):
        market_concentration(history_panel.drop(columns=["cr4_net_long"]))
