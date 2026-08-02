"""Macro-book PCA arithmetic on constructed panels.

`test_macro_pca_live.py` checks the claims against the real store. This file pins the
properties that make the number mean anything, and the one that made it lie:

- **PC1's sign is not identified**, so rotation must be sign-invariant or it reports `numpy`
  flips as the book being redefined
- **a variance share is floored at `1/n`**, so it looks plausible on noise
- **the panel is differenced**, because §7 says changes and levels are a different object
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures.macro_pca import (
    MacroPcaError,
    absorption_ratio,
    loading_rotation,
    positioning_panel,
    rolling_absorption,
    select_markets,
    shuffled_null,
    window_sensitivity,
)

WEEKS = pd.date_range("2015-01-06", periods=300, freq="7D")


def _panel(n_markets=10, *, weeks=WEEKS, common=0.8, seed=7):
    """`n_markets` columns sharing a single factor with weight `common`."""
    rng = np.random.default_rng(seed)
    factor = rng.standard_normal(len(weeks))
    data = {f"m{j:02d}": common * factor + (1 - common) * rng.standard_normal(len(weeks))
            for j in range(n_markets)}
    return pd.DataFrame(data, index=weeks)


def _frame(panel, category="managed_money", column="net_risk_usd_z", report_type="disaggregated"):
    """Long-form `add_extremity`-shaped frame from a wide panel."""
    long = panel.stack().rename(column).reset_index()
    long.columns = ["report_date", "market_code", column]
    long["category"] = category
    long["report_type"] = report_type
    return long


# ── the defect that made rotation lie ───────────────────────────────────────
def test_rotation_is_blind_to_the_sign_of_pc1():
    """**The measured defect.** An eigenvector's sign is not identified: PC1 and -PC1 are the
    same axis and the same book. A signed cosine reports a pin flip as a 180-degree rotation.

    On the real 24-market panel this produced **8 of 843 weeks reading ~1.99 against a median
    of 0.0004**, 200x the p95, every one an artifact. Under `1 - |cos|` they read ~0.002.
    """
    a = pd.Series([0.3, 0.5, -0.2, 0.4], index=list("abcd"))
    assert loading_rotation(a, a) == pytest.approx(0.0, abs=1e-12)
    assert loading_rotation(a, -a) == pytest.approx(0.0, abs=1e-12), (
        "a sign flip is the SAME axis and must read as no rotation")
    assert 0.0 <= loading_rotation(a, pd.Series([0.4, -0.3, 0.5, 0.2], index=list("abcd"))) <= 1.0


def test_rotation_is_bounded_and_orthogonal_reads_one():
    a = pd.Series([1.0, 0.0], index=["x", "y"])
    b = pd.Series([0.0, 1.0], index=["x", "y"])
    assert loading_rotation(a, b) == pytest.approx(1.0)


def test_rotation_needs_two_shared_markets():
    a = pd.Series([1.0], index=["x"])
    assert np.isnan(loading_rotation(a, a))


# ── the ratio itself ────────────────────────────────────────────────────────
def test_a_single_common_factor_gives_a_high_absorption():
    got = absorption_ratio(_panel(common=0.95))
    assert got["absorption"] > 0.8, f"one dominant factor should absorb most, got {got}"
    assert got["n_markets"] == 10


def test_independent_markets_land_near_the_one_over_n_floor():
    """**A variance share is bounded below by `1/n` and is always positive**, which is why it
    looks plausible on noise and why `shuffled_null` is not optional."""
    got = absorption_ratio(_panel(common=0.0, seed=11))
    assert got["absorption"] < 0.25, f"independent columns should sit near 1/n, got {got}"
    assert got["absorption"] > 1 / 10


def test_absorption_exceeds_its_shuffled_null_only_when_there_is_structure():
    structured = _panel(common=0.9, seed=3)
    noise = _panel(common=0.0, seed=3)
    for frame, expect_above in ((structured, True), (noise, False)):
        obs = absorption_ratio(frame)["absorption"]
        null = shuffled_null(frame, draws=40)
        p = float((null >= obs).mean())
        assert (p < 0.05) is expect_above, f"p={p:.3f} for expect_above={expect_above}"


def test_the_null_is_deterministic_given_a_seed():
    frame = _panel(common=0.5)
    a = shuffled_null(frame, draws=15, seed=1)
    b = shuffled_null(frame, draws=15, seed=1)
    assert np.allclose(a.to_numpy(), b.to_numpy())
    assert not np.allclose(a.to_numpy(), shuffled_null(frame, draws=15, seed=2).to_numpy())


def test_eigenvalues_sum_to_the_market_count_on_a_correlation_matrix():
    got = absorption_ratio(_panel(n_markets=12))
    assert float(got["eigenvalues"].sum()) == pytest.approx(12.0, rel=1e-9)
    assert got["loadings"].sum() >= 0, "PC1 is pinned to sum positive"


# ── market selection ────────────────────────────────────────────────────────
def test_selection_prefers_the_set_that_yields_the_most_complete_weeks():
    """**The measured motivation.** The real 26-market panel is 95.7% covered and yields ZERO
    complete weeks, because the holes are spread across markets rather than concentrated in
    weeks. Dropping two buys 947 weeks."""
    panel = _panel(n_markets=10)
    panel.iloc[::2, 9] = np.nan          # one market missing half its weeks
    chosen = select_markets(panel, min_markets=5)
    assert "m09" not in chosen, "the holed market must be dropped"
    assert len(chosen) == 9
    assert len(panel[chosen].dropna()) == len(panel)


def test_selection_breaks_ties_toward_more_markets():
    panel = _panel(n_markets=6)
    chosen = select_markets(panel, min_markets=3)
    assert len(chosen) == 6, "no market needs dropping, so none should be"


def test_selection_of_an_empty_panel_is_empty():
    assert select_markets(pd.DataFrame()) == []


# ── the panel ───────────────────────────────────────────────────────────────
def test_the_panel_is_differenced_because_section_7_says_changes():
    wide = _panel(n_markets=8)
    frame = _frame(wide)
    changes = positioning_panel(frame, category="managed_money")
    levels = positioning_panel(frame, category="managed_money", difference=False)
    assert changes.iloc[0].isna().all(), "the first row of a difference has no predecessor"
    assert np.allclose(levels.iloc[1] - levels.iloc[0], changes.iloc[1])


def test_the_book_category_is_inferred_from_the_report_type():
    frame = _frame(_panel(n_markets=8), category="leveraged", report_type="tff")
    got = positioning_panel(frame)
    assert got.shape[1] == 8


def test_an_unknown_report_type_raises_rather_than_returning_an_empty_panel():
    frame = _frame(_panel(n_markets=8), report_type="legacy")
    with pytest.raises(MacroPcaError, match="no book category configured"):
        positioning_panel(frame)


def test_a_missing_extremity_column_raises_and_says_where_it_comes_from():
    frame = _frame(_panel(n_markets=8)).drop(columns=["net_risk_usd_z"])
    with pytest.raises(MacroPcaError, match="add_extremity"):
        positioning_panel(frame)


# ── the point-in-time form ──────────────────────────────────────────────────
def test_rolling_absorption_uses_no_future_data():
    """The property that separates it from `absorption_ratio` over a whole panel.

    Truncating the panel after week `t` must not change the reading at `t`. A full-sample
    PCA fails this by construction, which is why it is offered as descriptive only.
    """
    panel = _panel(n_markets=8, common=0.6)
    full = rolling_absorption(panel, window=60, min_periods=40, min_markets=5)
    cut = len(panel) - 30
    truncated = rolling_absorption(panel.iloc[:cut], window=60, min_periods=40, min_markets=5)
    merged = full.merge(truncated, on="report_date", suffixes=("_full", "_cut"))
    assert len(merged) > 10
    assert np.allclose(merged["absorption_full"], merged["absorption_cut"]), (
        "a reading changed when later weeks were removed, so it was using them")


def test_rolling_emits_nothing_before_min_periods():
    panel = _panel(n_markets=8)
    got = rolling_absorption(panel, window=60, min_periods=50, min_markets=5)
    assert got["report_date"].min() >= panel.index[49]


def test_rolling_on_an_empty_panel_is_an_empty_frame():
    assert rolling_absorption(pd.DataFrame()).empty


def test_too_few_markets_raises():
    with pytest.raises(MacroPcaError, match="min_markets"):
        rolling_absorption(_panel(n_markets=4), min_markets=8)


def test_a_zero_variance_market_raises_rather_than_producing_a_nan():
    panel = _panel(n_markets=8)
    panel["m07"] = 1.0
    with pytest.raises(MacroPcaError, match="zero variance"):
        absorption_ratio(panel, min_markets=5)


def test_window_sensitivity_reports_each_window():
    got = window_sensitivity(_panel(n_markets=8, common=0.5),
                             windows=(40, 60), markets=None)
    assert len(got) == 2
    assert set(got["window"]) == {40, 60}
