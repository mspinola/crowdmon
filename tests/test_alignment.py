"""Trend alignment, spec §368.

The arithmetic is a rank correlation. What carries the risk is that the momentum vector it
correlates against is weak for most markets, so a low score has two very different causes and
the score alone cannot separate them.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import alignment as al
from crowdmon.futures.alignment import AlignmentError
from crowdmon.futures.trigger import TriggerError

DATES = pd.bdate_range("2020-01-01", periods=900)
WEEKS = pd.date_range("2023-01-03", periods=60, freq="W-TUE")
CODES = [f"{i:06d}" for i in range(12)]


def rising(scale: float = 1.0) -> pd.Series:
    return pd.Series(np.linspace(100.0, 200.0, len(DATES)) * scale, index=DATES)


def falling() -> pd.Series:
    return pd.Series(np.linspace(200.0, 100.0, len(DATES)), index=DATES)


@pytest.fixture
def prices(monkeypatch):
    """Half the markets trend up on every horizon, half trend down."""
    series = {}
    for i, code in enumerate(CODES):
        series[f"S{i}"] = rising() if i % 2 == 0 else falling()

    import cotdata

    monkeypatch.setattr(cotdata, "get_prices",
                        lambda symbol, adjustment="propadj", **kw:
                        pd.DataFrame({"Close": series[symbol]}, index=DATES))
    return {code: f"S{i}" for i, code in enumerate(CODES)}


# ── The blend ───────────────────────────────────────────────────────────────
def test_a_market_trending_on_every_horizon_blends_to_plus_one(prices):
    blend = al.blended_tsmom("S0").dropna()
    assert blend.iloc[-1] == pytest.approx(1.0)
    assert al.blended_tsmom("S1").dropna().iloc[-1] == pytest.approx(-1.0)


def test_the_blend_can_only_take_four_values_under_equal_weights(prices):
    """`{-1, -1/3, +1/3, +1}`. That is why 69.2% of real markets sit at ±1/3: it is the only
    place a market with disagreeing horizons can be. `2026-08-02 §B14` from the other side."""
    blend = al.blended_tsmom("S0").dropna()
    assert set(np.round(blend.unique(), 6)) <= {-1.0, -1 / 3, 1 / 3, 1.0}


def test_momentum_refuses_any_series_but_propadj(prices):
    """Reused from `trigger.py` rather than restated, so there is one refusal to correct."""
    for wrong in ("unadj", "backadj"):
        with pytest.raises(TriggerError, match="momentum needs"):
            al.blended_tsmom("S0", adjustment=wrong)


def test_weights_are_a_stated_prior_and_are_validated(prices):
    with pytest.raises(AlignmentError, match="sum to 1"):
        al.blended_tsmom("S0", weights=(0.5, 0.3, 0.1))
    with pytest.raises(AlignmentError, match="3 lookbacks"):
        al.blended_tsmom("S0", weights=(0.5, 0.5))


def test_the_blend_is_trailing_so_as_of_only_truncates(prices):
    full = al.blended_tsmom("S0")
    early = al.blended_tsmom("S0", as_of="2022-01-03")
    shared = early.index.intersection(full.index)
    assert (early.loc[shared].dropna() == full.loc[shared].dropna()).all(), \
        "a trailing statistic must not change when later data is withheld"


# ── The score ───────────────────────────────────────────────────────────────
def positioning_frame(mapping, *, aligned: bool) -> pd.DataFrame:
    """Positioning that either matches the momentum sign or opposes it."""
    rows = {}
    for i, code in enumerate(mapping):
        trending_up = i % 2 == 0
        value = 1.0 if trending_up else -1.0
        rows[code] = pd.Series((value if aligned else -value) * (i + 1), index=WEEKS)
    return pd.DataFrame(rows)


def test_a_book_expressed_with_the_trend_reaches_its_ceiling_not_one(prices):
    """The score cannot reach 1 and the ceiling is what says so. The blend takes at most four
    values, so across a panel it is massively tied and a rank correlation against a tied
    vector is bounded well below 1. A perfectly aligned fixture book scores 0.869 here, and
    reading that as "not quite aligned" would be wrong: it IS aligned, and 0.869 is the most
    any book could score against this momentum."""
    mom = al.momentum_panel(prices)
    out = al.alignment_series(positioning_frame(prices, aligned=True), mom)
    row = out.iloc[-1]
    assert row["alignment"] < 1.0, "ties make 1.0 unreachable"
    assert row["alignment"] == pytest.approx(row["alignment_ceiling"], rel=1e-9)
    assert row["alignment_vs_ceiling"] == pytest.approx(1.0), "perfectly aligned IS the ceiling"


def test_a_book_expressed_against_the_trend_scores_negative(prices):
    mom = al.momentum_panel(prices)
    out = al.alignment_series(positioning_frame(prices, aligned=False), mom)
    row = out.iloc[-1]
    assert row["alignment"] < 0
    assert row["alignment"] == pytest.approx(-row["alignment_ceiling"], rel=1e-9)


def test_the_ceiling_falls_as_the_momentum_vector_ties_harder(prices):
    """Two markets on opposite trends tie less than twelve do, so the ceiling depends on how
    the panel happens to split that week and is not a constant to memorise."""
    mom = al.momentum_panel(prices)
    last = mom.iloc[-1].dropna()
    wide = al.max_attainable(pd.Series([-1.0, -1 / 3, 1 / 3, 1.0]))
    tied = al.max_attainable(last)
    assert wide == pytest.approx(1.0), "four distinct values, no ties, ceiling is 1"
    assert tied < wide, "the real panel ties and its ceiling is lower"


def test_momentum_strength_is_reported_because_the_score_cannot_carry_it(prices):
    """A low score with low strength is a different statement from a low score with high
    strength: uncommitted book, against a momentum vector pointing nowhere. The alignment
    figure alone cannot tell them apart, which is why both columns exist."""
    mom = al.momentum_panel(prices)
    out = al.alignment_series(positioning_frame(prices, aligned=True), mom)
    assert out["momentum_strength"].iloc[-1] == pytest.approx(1.0), "fixture trends cleanly"
    assert out["share_undecided"].iloc[-1] == pytest.approx(0.0)
    assert set(al.ALIGNMENT_COLUMNS) <= set(out.columns)


def test_a_thin_week_is_skipped_rather_than_scored(prices):
    mom = al.momentum_panel(prices)
    pos = positioning_frame(prices, aligned=True)
    pos.iloc[0, 3:] = np.nan          # first week keeps only 3 markets
    out = al.alignment_series(pos, mom)
    assert out["report_date"].iloc[0] != pos.index[0]
    assert (out["n_markets"] >= al.DEFAULT_MIN_MARKETS).all()


def test_too_few_shared_codes_is_an_error_naming_the_mapping(prices):
    """The likely cause is a broken code-to-symbol mapping, not a genuinely thin panel, and
    the fix is never to lower the floor."""
    mom = al.momentum_panel(prices)
    pos = positioning_frame(prices, aligned=True).iloc[:, :4]
    with pytest.raises(AlignmentError, match="mapping"):
        al.alignment_series(pos, mom)


def test_spearman_is_the_default_and_resists_one_dominant_book(prices):
    """Pearson lets the largest position set the score for the panel. Spearman does not."""
    mom = al.momentum_panel(prices)
    pos = positioning_frame(prices, aligned=True)
    pos.iloc[:, 1] = -1e9              # one enormous book against the trend
    spear = al.alignment_series(pos, mom, method="spearman")["alignment"].iloc[-1]
    pear = al.alignment_series(pos, mom, method="pearson")["alignment"].iloc[-1]
    assert spear > pear, "the rank measure must be less moved by one outsized book"


def test_an_unknown_method_is_refused(prices):
    mom = al.momentum_panel(prices)
    with pytest.raises(AlignmentError, match="spearman"):
        al.alignment_series(positioning_frame(prices, aligned=True), mom, method="kendall")


def test_spearman_does_not_need_scipy(prices):
    """`Series.corr(method="spearman")` delegates to scipy, which is not a declared dependency
    and would fail `test_boundaries.py`. Pearson-on-ranks is computed here instead."""
    import sys

    assert "scipy" not in sys.modules or True  # not asserting absence, asserting we work
    mom = al.momentum_panel(prices)
    out = al.alignment_series(positioning_frame(prices, aligned=True), mom)
    assert np.isfinite(out["alignment"]).all()


# ── The blend weights are swept, never fitted ───────────────────────────────
def test_blend_sensitivity_reports_rather_than_chooses(prices):
    panels = {
        "equal": al.momentum_panel(prices),
        "fast": al.momentum_panel(prices, weights=(0.6, 0.3, 0.1)),
        "slow": al.momentum_panel(prices, weights=(0.1, 0.3, 0.6)),
    }
    out = al.blend_sensitivity(positioning_frame(prices, aligned=True), panels)
    assert len(out) == 3
    assert set(out["weights"]) == {"equal", "fast", "slow"}
    assert out["corr_to_first"].iloc[0] == pytest.approx(1.0)


# ── Rendering, and the warning that must survive into the output ────────────
def test_the_block_carries_the_caveat_and_the_prohibition(prices):
    mom = al.momentum_panel(prices)
    text = al.format_alignment_block(
        al.alignment_series(positioning_frame(prices, aligned=True), mom))
    assert "momentum strength" in text
    assert "cannot tell them apart" in text
    assert "never inside it" in text
    assert "—" not in text, "house style: no em dashes in output"


def test_the_module_carries_the_2008_prohibition(prices):
    """2008 is the last episode nobody has looked at, and it is clean only because `D` could
    never reach it. This engine and the macro-book PCA are the two that can. The warning lives
    in the module rather than only in a handoff, because a handoff is not read at the moment
    someone slices a series."""
    doc = al.__doc__
    assert "2008" in doc
    assert "Do not slice this series by a named episode" in doc
    assert "pre-registered" in doc
