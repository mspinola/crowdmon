"""Commonality: the basket regression, and the two reasons §A.6 cannot feed §A.9 as written.

Offline and mostly synthetic, because both findings are about the ALGEBRA of the measure
rather than about markets. A synthetic panel with a known answer is the right instrument for
that; `test_commonality_live.py` then checks the real universe behaves as claimed.
"""
import numpy as np
import pandas as pd
import pytest

DATES = pd.bdate_range("2015-01-01", "2026-07-31")


def _panel(n_markets=8, *, loading=1.0, seed=0):
    """A panel with a controllable common factor. `loading=0` gives independent markets."""
    rng = np.random.default_rng(seed)
    common = rng.normal(0, 0.1, len(DATES))
    cols = {}
    for i in range(n_markets):
        noise = rng.normal(0, 0.1, len(DATES))
        cols[f"M{i}"] = np.exp(np.cumsum(loading * common + noise)) * 1e-9
    return pd.DataFrame(cols, index=DATES)


# ── finding 1: the own-market identity ──────────────────────────────────────
def test_including_the_own_market_makes_beta_bar_exactly_one(_=None):
    """The identity that makes the literal reading of §A.6 vacuous.

        sum_i cov(y_i, ybar) = cov(N.ybar, ybar) = N.var(ybar)

    so `mean_i beta_i = 1` for ANY data. Checked here on INDEPENDENT markets, where the true
    commonality is zero and the measure still reports 1.
    """
    from crowdmon.futures import commonality_betas

    independent = _panel(loading=0.0, seed=1)
    betas = commonality_betas(independent, exclude_own=False)
    assert betas.mean() == pytest.approx(1.0, abs=1e-9)

    # And with a strong common factor it is still exactly 1, which is the point: the number
    # carries no information about the data at all.
    betas = commonality_betas(_panel(loading=3.0, seed=1), exclude_own=False)
    assert betas.mean() == pytest.approx(1.0, abs=1e-9)


def test_excluding_the_own_market_recovers_the_real_signal():
    """With the market excluded, independent panels give beta near zero and a common factor
    gives beta near one. That is a measurement rather than an identity."""
    from crowdmon.futures import commonality_betas

    independent = commonality_betas(_panel(loading=0.0, seed=2)).mean()
    common = commonality_betas(_panel(loading=5.0, seed=2)).mean()
    assert abs(independent) < 0.25
    assert common > 0.7
    assert common > independent


def test_exclusion_is_the_default():
    """Because the alternative is vacuous, and a default that silently returns 1.0 for
    everything is the worst kind of wrong: plausible, stable, and meaningless."""
    from crowdmon.futures import commonality_betas

    panel = _panel(loading=0.0, seed=3)
    assert commonality_betas(panel).mean() == pytest.approx(
        commonality_betas(panel, exclude_own=True).mean())


def test_a_basket_of_two_is_refused():
    from crowdmon.futures import CommonalityError, commonality_betas

    with pytest.raises(CommonalityError, match="at least 3 markets"):
        commonality_betas(_panel(n_markets=2))


# ── finding 2: a constant beta cannot move a percentile ─────────────────────
def test_a_constant_beta_bar_leaves_the_percentile_bit_identical():
    """§A.9 defines `I = pct(T_eff)`. A positive scalar multiple is a monotonic transform, so
    the percentile does not move, for any gamma. This is the reason this module does not wire
    itself into `composite.py`."""
    from crowdmon.core.aggregate import rolling_percentile
    from crowdmon.futures import t_effective

    rng = np.random.default_rng(0)
    t = pd.Series(np.abs(rng.lognormal(1.0, 0.6, len(DATES))), index=DATES)
    base = rolling_percentile(t, window="1095D", min_periods=104)
    for gamma in (0.25, 0.5, 2.0, 10.0):
        scaled = rolling_percentile(t_effective(t, 0.634, gamma=gamma),
                                    window="1095D", min_periods=104)
        both = pd.concat([base.rename("a"), scaled.rename("b")], axis=1).dropna()
        assert len(both) > 100
        assert np.allclose(both["a"], both["b"]), f"gamma={gamma} moved the percentile"


def test_a_time_varying_beta_bar_does_move_it_but_not_much():
    """The only form that reaches the composite. Reported rather than assumed, because "it
    has an effect" and "it has an effect worth having" are different claims."""
    from crowdmon.core.aggregate import rolling_percentile
    from crowdmon.futures import t_effective

    rng = np.random.default_rng(0)
    t = pd.Series(np.abs(rng.lognormal(1.0, 0.6, len(DATES))), index=DATES)
    beta_t = pd.Series(0.634 + 0.2 * np.sin(np.arange(len(DATES)) / 200), index=DATES)
    base = rolling_percentile(t, window="1095D", min_periods=104)
    moved = rolling_percentile(t_effective(t, beta_t, gamma=0.5),
                               window="1095D", min_periods=104)
    both = pd.concat([base.rename("a"), moved.rename("b")], axis=1).dropna()
    assert not np.allclose(both["a"], both["b"])
    assert both["a"].rank().corr(both["b"].rank()) > 0.9      # moved, but only a little


# ── the transform and its guards ────────────────────────────────────────────
def test_t_effective_is_t_times_one_plus_gamma_beta():
    from crowdmon.futures import t_effective

    assert t_effective(10.0, 0.6, gamma=0.5) == pytest.approx(10.0 * 1.3)
    assert t_effective(10.0, 0.6, gamma=0.0) == pytest.approx(10.0)   # reduces to T exactly


def test_a_negative_gamma_is_refused():
    """It would make co-moving liquidity SHORTEN the exit, inverting the whole argument."""
    from crowdmon.futures import CommonalityError, t_effective

    with pytest.raises(CommonalityError, match="non-negative"):
        t_effective(10.0, 0.6, gamma=-0.5)


def test_gamma_sensitivity_reports_the_constant_rather_than_defending_it():
    """`gamma` has no sanctioned range anywhere in the appendix, unlike kappa and Y. The
    same treatment `flow.tolerance_sensitivity` gives its dominance tolerance."""
    from crowdmon.futures import gamma_sensitivity

    t = pd.Series([1.0, 4.0, 9.0, 16.0])
    out = gamma_sensitivity(t, 0.634)
    assert list(out["gamma"]) == [0.0, 0.25, 0.5, 1.0, 2.0]
    assert out.loc[0, "multiplier"] == pytest.approx(1.0)
    # A constant beta_bar cannot reorder, so every rank correlation is exactly 1. That IS
    # the finding, stated in the output rather than buried in a docstring.
    assert out["rank_corr_vs_gamma_0"].tolist() == pytest.approx([1.0] * len(out))


def test_rolling_betas_are_time_varying_and_trailing():
    from crowdmon.futures import rolling_betas

    out = rolling_betas(_panel(loading=2.0, seed=4), window=252)
    assert out.shape[1] == 8
    assert out.iloc[:251].isna().all().all()      # no value before the window fills
    assert out.dropna(how="all").std().max() > 0  # and it actually moves


# ── the frame join ──────────────────────────────────────────────────────────
def test_add_commonality_attaches_beta_and_t_eff():
    from crowdmon.futures import add_commonality

    betas = pd.Series({"GC": 0.55, "ZW": 1.02})
    frame = pd.DataFrame([{"symbol": "GC", "dtl_sell": 4.0, "dtl_buy": 2.0},
                          {"symbol": "ZW", "dtl_sell": 6.0, "dtl_buy": 1.0}])
    got = add_commonality(frame, betas, gamma=0.5)
    assert got["beta"].tolist() == [0.55, 1.02]
    assert got["beta_bar"].iloc[0] == pytest.approx(0.785)
    assert got["t_eff_sell"].iloc[0] == pytest.approx(4.0 * (1 + 0.5 * 0.785))


def test_a_market_with_no_beta_gets_null_not_the_basket_mean():
    """Substituting the average would hide exactly the markets whose liquidity behaviour is
    least well known, which are the ones a reader most needs flagged."""
    from crowdmon.futures import add_commonality

    got = add_commonality(
        pd.DataFrame([{"symbol": "NOPE", "dtl_sell": 4.0, "dtl_buy": 2.0}]),
        pd.Series({"GC": 0.55, "ZW": 1.02}))
    assert pd.isna(got["beta"].iloc[0])


def test_missing_prerequisite_columns_name_the_steps_that_provide_them():
    from crowdmon.futures import CommonalityError, add_commonality

    with pytest.raises(CommonalityError, match="rank_markets"):
        add_commonality(pd.DataFrame([{"symbol": "GC"}]), pd.Series({"GC": 0.5}))
