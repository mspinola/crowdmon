"""Triggers: where the signal flips, what volatility forces, and the invariant between them.

Offline. Prices are constructed so every trigger is known by hand.
"""
import numpy as np
import pandas as pd
import pytest

DATES = pd.bdate_range("2024-01-01", "2026-07-31")


def _series(values):
    return pd.Series(values, index=DATES[-len(values):], dtype="float64")


def _ramp(n=400, start=100.0, step=0.25):
    """A monotonically rising series: every lookback is below spot, so `s = +1`."""
    return _series([start + step * i for i in range(n)])


# ── the trigger price ───────────────────────────────────────────────────────
def test_the_trigger_is_the_price_k_bars_ago():
    """§A.7: `F* = F_{t-k}`. The price at which a large pool of capital becomes a forced
    seller is simply the price of k days ago."""
    from crowdmon.futures import trigger_prices

    prices = _ramp()
    got = trigger_prices(prices, lookbacks=(20, 60, 250))
    for k in (20, 60, 250):
        assert got[k] == pytest.approx(prices.iloc[-1 - k])


def test_the_trigger_is_consistent_with_the_signal_it_derives_from():
    """The invariant that catches an off-by-one, and did.

    `s > 0` means spot is above the median lookback price, so the blended trigger must sit
    BELOW spot, and vice versa. A one-bar error in either function breaks this while leaving
    both outputs individually plausible.
    """
    from crowdmon.futures import blended_trigger, trend_signal

    rng = np.random.default_rng(0)
    for seed_shift in range(6):
        walk = _series(100 * np.exp(np.cumsum(
            rng.normal(0.0002 * (seed_shift - 3), 0.01, 400))))
        signal = trend_signal(walk).iloc[-1]
        trigger = blended_trigger(walk)
        if signal == 0:
            continue
        assert np.sign(walk.iloc[-1] - trigger) == np.sign(signal), (
            f"spot {walk.iloc[-1]:.2f}, trigger {trigger:.2f}, signal {signal:+.2f}")


def test_the_blended_trigger_is_the_median_of_the_individual_ones():
    """Closed form. §A.7 says to solve `s(F*) = 0` numerically; for an odd, equally
    weighted sign blend `s` steps by 2/n at each `F_{t-k}` and crosses exactly at their
    median, so there is nothing to solve."""
    from crowdmon.futures import blended_trigger, trigger_prices

    rng = np.random.default_rng(1)
    walk = _series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))))
    assert blended_trigger(walk) == pytest.approx(
        np.median(list(trigger_prices(walk).values())))


def test_an_even_number_of_lookbacks_is_refused():
    """`s` passes through zero on a flat step rather than crossing it, so the trigger is an
    interval and not a price."""
    from crowdmon.futures import TriggerError, blended_trigger

    with pytest.raises(TriggerError, match="interval"):
        blended_trigger(_ramp(), lookbacks=(20, 60))


def test_a_rising_series_is_fully_long_and_a_falling_one_fully_short():
    from crowdmon.futures import trend_signal

    assert trend_signal(_ramp()).iloc[-1] == pytest.approx(1.0)
    falling = _series(list(reversed(_ramp().tolist())))
    assert trend_signal(falling).iloc[-1] == pytest.approx(-1.0)


def test_too_short_a_history_is_refused_rather_than_padded():
    from crowdmon.futures import TriggerError, trigger_prices

    with pytest.raises(TriggerError, match="longest lookback"):
        trigger_prices(_ramp(n=100), lookbacks=(20, 60, 250))


def test_solve_trigger_finds_the_same_answer_by_bisection():
    """The general path, for a squash where the median closed form does not hold."""
    from crowdmon.futures import blended_trigger, solve_trigger, trigger_prices

    walk = _series(100 * np.exp(np.cumsum(np.random.default_rng(2).normal(0, 0.01, 400))))
    levels = list(trigger_prices(walk).values())

    def signal_at(price):
        return float(np.mean([np.sign(price - level) for level in levels]))

    assert solve_trigger(walk, signal_at, lo=min(levels) - 1, hi=max(levels) + 1,
                         tolerance=1e-9) == pytest.approx(blended_trigger(walk), abs=1e-6)


def test_solve_trigger_refuses_a_bracket_with_no_sign_change():
    from crowdmon.futures import TriggerError, solve_trigger

    with pytest.raises(TriggerError, match="does not change sign"):
        solve_trigger(_ramp(), lambda p: 1.0, lo=1.0, hi=2.0)


# ── the volatility trigger ──────────────────────────────────────────────────
def test_a_doubling_of_volatility_forces_exactly_half_the_position():
    """Unit elasticity, and the number §A.7 quotes. No capital estimate, no target
    volatility, no portfolio scaling: they all cancel."""
    from crowdmon.futures import vol_trigger

    assert vol_trigger(0.025, 0.05) == pytest.approx(0.5)
    assert vol_trigger(0.02, 0.06) == pytest.approx(2 / 3)


def test_the_volatility_trigger_has_no_reference_to_price_direction():
    """§A.7's formal content for "a violent up-day can force liquidation just as a down-day
    can". The function takes two volatilities and nothing else."""
    import inspect

    from crowdmon.futures import vol_trigger
    assert list(inspect.signature(vol_trigger).parameters) == ["sigma_now", "sigma_stressed"]


def test_falling_volatility_returns_a_negative_response_rather_than_zero():
    """The same mechanism runs both ways: a vol collapse forces BUYING. Clipping it would
    hide half the phenomenon."""
    from crowdmon.futures import vol_trigger

    assert vol_trigger(0.05, 0.025) == pytest.approx(-1.0)


def test_a_non_positive_volatility_is_refused():
    from crowdmon.futures import TriggerError, vol_trigger

    with pytest.raises(TriggerError, match="positive"):
        vol_trigger(0.02, 0.0)


# ── the frame join ──────────────────────────────────────────────────────────
@pytest.fixture()
def prices(monkeypatch):
    import cotdata

    ramp = _ramp()
    bars = pd.DataFrame({"Open": ramp, "High": ramp, "Low": ramp, "Close": ramp,
                         "Volume": [1_000.0] * len(ramp)}, index=ramp.index)

    def fake(symbol, adjustment="backadj", **kw):
        return bars if symbol == "GC" else pd.DataFrame()

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return bars


def _frame(**over):
    row = {"symbol": "GC", "market_code": "088691", "category": "managed_money",
           "report_date": pd.Timestamp("2026-07-21"),
           "long_contracts": 100_000.0, "short_contracts": 40_000.0}
    row.update(over)
    return pd.DataFrame([row])


def test_add_triggers_populates_the_block_inputs(prices):
    from crowdmon.futures import add_triggers

    got = add_triggers(_frame()).iloc[0]
    assert got.net_contracts == 60_000.0
    assert got.signal == pytest.approx(1.0)             # a ramp is long on every lookback
    assert got.trigger_blend < got.spot                 # and so the trigger is below spot
    assert got.flow_to_flat == 60_000.0
    assert got.vol_double_flow == pytest.approx(30_000.0)


def test_a_back_adjusted_series_is_refused(prices):
    """Signal SIGN agrees 99.4% across series, so this guard is not about the sign. It is
    about the DISTANCE, which is wrong by up to 420 percentage points on cocoa at 250 days."""
    from crowdmon.futures import TriggerError, add_triggers

    with pytest.raises(TriggerError, match="420"):
        add_triggers(_frame(), adjustment="backadj")


def test_a_symbol_with_no_prices_keeps_its_place(prices):
    from crowdmon.futures import add_triggers

    got = add_triggers(pd.concat([_frame(), _frame(symbol="NOPE")], ignore_index=True))
    assert len(got) == 2
    assert pd.isna(got["trigger_blend"].iloc[1])


def test_missing_prerequisite_columns_name_the_step_that_provides_them(prices):
    from crowdmon.futures import TriggerError, add_triggers

    with pytest.raises(TriggerError, match="ContractMaster.annotate"):
        add_triggers(_frame().drop(columns=["symbol"]))


def test_an_empty_frame_still_gains_the_trigger_columns(prices):
    from crowdmon.futures import TRIGGER_COLUMNS, add_triggers

    got = add_triggers(_frame().iloc[0:0])
    assert all(c in got.columns for c in TRIGGER_COLUMNS)


def test_the_output_block_says_the_flows_are_upper_bounds(prices):
    """Spec §11.2: Managed Money blends CTAs, discretionary macro and risk parity, so
    applying a trend response to the whole category overstates it. The block has to say so,
    because a reader will otherwise take the figure as a point estimate."""
    from crowdmon.futures import add_triggers, trigger_block

    row = add_triggers(_frame()).assign(adv=5_000.0, sigma_daily=0.02).iloc[0]
    text = trigger_block(row)
    assert "upper bounds" in text
    assert "trend-following fraction" in text
    assert "independent of price" in text
