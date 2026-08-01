"""Cascade amplification, appendix §A.8.

The arithmetic is three lines. What carries the risk is everything around it: the two
directions must never merge, the cohort split must reproduce the observed net, and the
amplification must refuse rather than print a negative when `l.g` passes 1.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import reflexivity as rx
from crowdmon.futures.reflexivity import ReflexivityError


def triggers(*rows) -> pd.DataFrame:
    """`(lookback, signal, move_from_spot)` triples, shaped like `trigger_prices` output."""
    return pd.DataFrame([
        {"lookback_days": k, "signal": s, "flip_price": 100.0 * (1 + m),
         "move_from_spot": m, "as_of": pd.Timestamp("2026-07-31")}
        for k, s, m in rows])


GOLD_LIKE = triggers((20, -1, 0.0194), (60, -1, 0.1371), (250, 1, -0.1344))
UNANIMOUS = triggers((20, -1, 0.05), (60, -1, 0.15), (250, -1, 0.30))


# ── The cohort split must reproduce the observed net ────────────────────────
def test_mixed_signals_imply_a_gross_pool_three_times_the_net():
    """The observed net is the SUM of the cohorts. One dissenter out of three means
    `sum(s) = ±1`, so the gross that nets to it is 3x."""
    assert rx.implied_gross_pool([-1, -1, 1], 100_000.0) == pytest.approx(300_000.0)
    assert rx.implied_gross_pool([1, -1, 1], 100_000.0) == pytest.approx(300_000.0)


def test_unanimous_signals_imply_a_gross_pool_equal_to_the_net():
    assert rx.implied_gross_pool([-1, -1, -1], 100_000.0) == pytest.approx(100_000.0)


def test_the_per_cohort_pool_cuts_unanimous_markets_and_leaves_mixed_ones():
    """The consequence that reorders the cross-market ranking rather than rescaling it.
    Against naively using `|net|` at every step: mixed unchanged, unanimous cut by 3x."""
    net = 90_000.0
    mixed = rx.implied_gross_pool([-1, -1, 1], net) / 3
    unanimous = rx.implied_gross_pool([-1, -1, -1], net) / 3
    assert mixed == pytest.approx(net)
    assert unanimous == pytest.approx(net / 3)


def test_signals_summing_to_zero_are_refused_rather_than_infinite():
    with pytest.raises(ReflexivityError, match="sum to zero"):
        rx.implied_gross_pool([1, -1, 1, -1], 100_000.0)


def test_the_zero_sum_guard_is_reachable_without_touching_the_config():
    """The parity argument for "this cannot happen" protects the count of CONTRIBUTING
    signals, not the length of `DEFAULT_LOOKBACKS`. A flat lookback and an unresolved one both
    drop out of that count, leaving two signals that can cancel.

    Both cases below arose by accident while writing these tests, which is the evidence that
    they are ordinary rather than adversarial.
    """
    with pytest.raises(ReflexivityError, match="sum to zero"):
        rx.implied_gross_pool([0, -1, 1], 100_000.0)          # one flat lookback
    with pytest.raises(ReflexivityError, match="sum to zero"):
        rx.implied_gross_pool([-1, None, 1], 100_000.0)       # one short history


def test_a_flat_signal_contributes_no_position_and_no_pool():
    """A cohort with `s = 0` holds `w.P.s = 0`. It must not silently become a direction, which
    is the renderer bug the flat-signal fix in `trigger.py` addressed."""
    stairs = rx.staircase(triggers((20, 0, 0.0), (60, -1, 0.10), (250, -1, 0.20)),
                          net_contracts=60_000.0, sigma_daily=0.012, volume=200_000.0)
    assert "flat" not in set(stairs["direction"])
    assert set(stairs["lookback_days"]) == {60, 250}


def test_an_unresolved_lookback_is_dropped_not_counted_as_flat():
    stairs = rx.staircase(triggers((20, -1, 0.02), (60, None, np.nan), (250, -1, 0.13)),
                          net_contracts=60_000.0, sigma_daily=0.012, volume=200_000.0)
    assert set(stairs["lookback_days"]) == {20, 250}
    assert stairs.attrs["implied_gross_multiple"] == pytest.approx(1.0), \
        "two unanimous signals imply gross == net, the count being 2 not 3"


# ── The two directions are separate cascades ────────────────────────────────
def test_up_and_down_are_separate_and_neither_is_summed():
    """Gold today: the 20d and 60d shorts cover on a rally, the 250d long liquidates on a
    selloff. Two cascades, opposite directions, from different slices of one pool."""
    stairs = rx.staircase(GOLD_LIKE, net_contracts=119_795.0,
                          sigma_daily=0.011, volume=180_000.0)
    up = stairs[stairs["direction"] == "up"]
    down = stairs[stairs["direction"] == "down"]
    assert set(up["lookback_days"]) == {20, 60}, "the shorts cover on a rally"
    assert set(down["lookback_days"]) == {250}, "the long liquidates on a selloff"
    assert up["cum_pool"].max() != pytest.approx(stairs["step_pool"].sum()), \
        "the up staircase must not carry the down cohort's pool"


def test_a_market_with_two_live_cascades_is_not_reported_as_quieter_than_one_with_none():
    """The netting error `flow.decompose` exists to avoid, in a new place. If the directions
    were netted, gold's two-up-one-down would partially cancel."""
    stairs = rx.staircase(GOLD_LIKE, net_contracts=119_795.0,
                          sigma_daily=0.011, volume=180_000.0)
    assert len(stairs.groupby("direction")) == 2
    assert (stairs["cum_pool"] > 0).all()


def test_a_unanimous_market_has_only_one_staircase():
    stairs = rx.staircase(UNANIMOUS, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    assert set(stairs["direction"]) == {"up"}


# ── The staircase itself ────────────────────────────────────────────────────
def test_the_pool_accumulates_with_distance_rather_than_arriving_at_once():
    stairs = rx.staircase(UNANIMOUS, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    assert list(stairs["distance"]) == sorted(stairs["distance"]), "steps in distance order"
    assert list(stairs["cum_pool"]) == sorted(stairs["cum_pool"]), "pool only accumulates"
    assert stairs["cum_pool"].iloc[-1] == pytest.approx(stairs["step_pool"].sum())


def test_well_spaced_triggers_put_the_worst_step_nearest():
    """`l.g ~ sqrt(Q_cum)/d`, so step `i` beats step `i+1` when `d_(i+1)/d_i` exceeds
    `sqrt(Q_(i+1)/Q_i)`, which is 1.414 at the first gap under a uniform split. UNANIMOUS is
    spaced 0.05 / 0.15 / 0.30, ratios 3.0 and 2.0, so the near step wins comfortably."""
    stairs = rx.staircase(UNANIMOUS, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    amps = stairs["amplification"].tolist()
    assert amps == sorted(amps, reverse=True)
    head = rx.headline(stairs)
    assert head["is_nearest"].all()


def test_clustered_triggers_put_the_worst_step_PAST_the_nearest():
    """The case that breaks "report the nearest step", and it is not a corner: measured
    within-direction across 33 markets, 6 of 33 multi-step staircases peak past their nearest.
    6E holds two up-triggers at a distance ratio of 1.005, far inside the 1.414 needed.

    The ORDERING is net-independent (`lg_2/lg_1 = sqrt(2).d_1/d_2`), which is why it can be
    counted across the universe without a real position for each market. The amplification
    levels are not, and are deliberately not quoted anywhere.

    Here 0.050 and 0.052 give a ratio of 1.04, far below the 1.414 the near step needs.
    """
    clustered = triggers((20, -1, 0.050), (60, -1, 0.052))
    stairs = rx.staircase(clustered, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    amps = stairs["amplification"].tolist()
    assert amps[1] > amps[0], "the pool nearly doubles across almost no distance"

    head = rx.headline(stairs)
    assert not head["is_nearest"].iloc[0]
    assert head["amplification"].iloc[0] == pytest.approx(max(amps))


def test_the_dominance_threshold_is_sqrt_of_the_pool_ratio():
    """The exact condition, pinned at the boundary rather than asserted in prose. With two
    equal cohorts `Q_2/Q_1 = 2`, so the near step wins iff `d_2/d_1 > sqrt(2)`."""
    def near_wins(ratio: float) -> bool:
        st = rx.staircase(triggers((20, -1, 0.05), (60, -1, 0.05 * ratio)),
                          net_contracts=100_000.0, sigma_daily=0.011, volume=180_000.0)
        return st["lg"].iloc[0] > st["lg"].iloc[1]

    assert near_wins(2 ** 0.5 + 0.01)
    assert not near_wins(2 ** 0.5 - 0.01)


def test_g_is_flat_when_distance_grows_in_proportion_to_the_pool():
    """The boundary case for `g` itself. Equally spaced triggers give a constant `g`, so
    `l.g` then falls only through `l`, once and by sqrt(3) across three steps."""
    even = triggers((20, -1, 0.10), (60, -1, 0.20), (250, -1, 0.30))
    stairs = rx.staircase(even, net_contracts=100_000.0, sigma_daily=0.011, volume=180_000.0)
    g = stairs["g_secant"].tolist()
    assert g[0] == pytest.approx(g[1]) == pytest.approx(g[2])
    assert stairs["lg"].iloc[0] / stairs["lg"].iloc[-1] == pytest.approx(3 ** 0.5)


def test_the_worst_step_race_is_run_within_a_direction_never_across():
    """Pooling `up` and `down` into one distance-sorted ladder manufactures counterexamples
    that are artifacts of the pooling, because adjacent steps then belong to different
    cascades. ZC in the latest week looks like a middle-step market exactly that way: its
    three steps sorted by distance are 250d-up, 20d-down, 60d-up, and it is monotone once
    separated.
    """
    zc_like = triggers((20, 1, -0.0403), (60, -1, 0.1114), (250, -1, 0.0370))
    stairs = rx.staircase(zc_like, net_contracts=126_776.0,
                          sigma_daily=0.014, volume=120_000.0)
    up = stairs[stairs["direction"] == "up"]["amplification"].tolist()
    assert up == sorted(up, reverse=True), "the up cascade alone is monotone"
    assert rx.headline(stairs)["is_nearest"].all()


def test_lambda_falls_as_the_cumulative_pool_grows():
    """`l = I(Q)/Q` is a secant on a square-root law, so it is not a constant of the market.
    Quoting one without the `Q` it was taken at is meaningless."""
    stairs = rx.staircase(UNANIMOUS, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    lam = stairs["lambda_eff"].tolist()
    assert lam[0] > lam[-1]
    assert stairs["lg"].iloc[0] == pytest.approx(
        stairs["lambda_eff"].iloc[0] * stairs["g_secant"].iloc[0])


# ── Refusing rather than printing a plausible wrong number ──────────────────
def test_lg_past_one_is_refused_rather_than_printed_as_a_negative():
    """The naive formula returns a NEGATIVE amplification for `l.g > 1`, which reads as mild
    damping rather than as a blow-up. That is the failure mode worth guarding."""
    assert np.isnan(rx._amplification(1.4))
    assert np.isnan(rx._amplification(rx.LG_CEILING))
    assert rx._amplification(0.5) == pytest.approx(2.0)


def test_the_trend_fraction_scales_lg_as_a_square_root_not_linearly():
    """B8: attributing the whole net to trend cohorts is an upper bound. `l.g` does NOT scale
    linearly in `f`, because `l = I(Q)/Q` falls as `Q^-1/2` while `g` rises as `Q`. Halving
    `f` cuts `l.g` by sqrt(2), not 2.

    This is pinned because the linear reading was written down first, in both a handoff and
    this module's own docstring, and it overstated the effect of the cohort constraint badly
    enough to claim gold had no equilibrium when its worst reading is 0.602.
    """
    full = rx.staircase(UNANIMOUS, net_contracts=100_000.0, sigma_daily=0.011,
                        volume=180_000.0, trend_fraction=1.0)
    half = rx.staircase(UNANIMOUS, net_contracts=100_000.0, sigma_daily=0.011,
                        volume=180_000.0, trend_fraction=0.5)
    assert half.attrs["gross_pool"] == pytest.approx(full.attrs["gross_pool"] / 2)
    assert half["lg"].iloc[-1] < full["lg"].iloc[-1]
    assert half["lg"].iloc[-1] == pytest.approx(full["lg"].iloc[-1] / (2 ** 0.5))


def test_an_out_of_range_trend_fraction_is_refused():
    for bad in (0.0, -0.5, 1.5):
        with pytest.raises(ReflexivityError, match="trend_fraction"):
            rx.implied_gross_pool([-1, -1, -1], 100_000.0, trend_fraction=bad)


def test_no_resolved_trigger_is_an_error_not_an_empty_frame():
    with pytest.raises(ReflexivityError, match="no resolved"):
        rx.staircase(triggers((20, None, np.nan)), net_contracts=1.0,
                     sigma_daily=0.01, volume=1000.0)


def test_weights_that_do_not_sum_to_one_are_refused():
    with pytest.raises(ReflexivityError, match="sum to 1"):
        rx.staircase(UNANIMOUS, net_contracts=100_000.0, sigma_daily=0.011,
                     volume=180_000.0, weights=(0.5, 0.3, 0.1))


# ── The bracket, which is what the horizon argument actually was ────────────
def test_the_bracket_puts_the_whole_side_pool_on_the_near_and_far_triggers():
    stairs = rx.staircase(UNANIMOUS, net_contracts=100_000.0,
                          sigma_daily=0.011, volume=180_000.0)
    br = rx.bracket(stairs)
    fast = br[br["endpoint"] == "all_fast"].iloc[0]
    slow = br[br["endpoint"] == "all_slow"].iloc[0]
    assert fast["pool"] == pytest.approx(slow["pool"]) == pytest.approx(
        stairs["step_pool"].sum())
    assert fast["distance"] < slow["distance"]
    assert fast["lg"] > slow["lg"], "all-fast is the upper bound on l.g"


# ── Rendering ───────────────────────────────────────────────────────────────
def test_the_block_prints_the_three_unmeasurable_terms():
    stairs = rx.staircase(GOLD_LIKE, net_contracts=119_795.0,
                          sigma_daily=0.011, volume=180_000.0)
    text = rx.format_block(stairs, symbol="GC")
    for expected in ("observed net:", "trend fraction (f):", "implied gross pool:",
                     "forced sell", "forced buy", "never summed"):
        assert expected in text, expected
    assert "—" not in text, "house style: no em dashes in output"
