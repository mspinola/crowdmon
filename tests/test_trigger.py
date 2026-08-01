"""The trigger block, module spec §9.3 and appendix §A.7.

Two things carry the risk here and neither is the arithmetic. The trigger level must be
anchor-invariant, because `propadj` is anchored at the end of the series and the naive form
looks right until someone runs it over history. And the vol shock must be in annualised
units, because applying a five-point shock to a daily sigma makes every market print the same
near-total liquidation, which is how the bug was caught.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import trigger as trig
from crowdmon.futures.trigger import TriggerError

MARKET = pd.Series({"market_name": "TEST MARKET", "phi": 0.4,
                    "net_contracts": 100_000.0, "net_risk_usd_pct": 0.9})


@pytest.fixture
def prices(monkeypatch):
    """A rising series with a known k-day-ago level, served as both series.

    `unadj` and `propadj` are deliberately given DIFFERENT anchors, so a test that passes
    only because they coincide would fail here. `propadj` is scaled by 3.0, exactly the sort
    of common factor the anchor-invariant form must cancel.
    """
    dates = pd.bdate_range("2024-01-01", periods=400)
    closes = pd.Series(np.linspace(100.0, 200.0, len(dates)), index=dates)

    def fake(symbol, adjustment="propadj", **kw):
        series = closes * (3.0 if adjustment == "propadj" else 1.0)
        return pd.DataFrame({"Close": series}, index=dates)

    import cotdata

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return closes


# ── The anchor hazard ───────────────────────────────────────────────────────
def test_the_trigger_is_invariant_to_where_propadj_is_anchored(prices):
    """`F* = spot . propadj[t-k] / propadj[t]`, so a common scale factor cancels.

    The fixture scales `propadj` by 3.0 against `unadj`. A naive `propadj[t-k]` would return
    three times the right answer; the ratio form returns the price.
    """
    out = trig.trigger_prices("TEST", lookbacks=(20,))
    spot = prices.iloc[-1]
    expected = spot * prices.iloc[-21] / prices.iloc[-1]
    assert out["flip_price"].iloc[0] == pytest.approx(expected)
    assert out.attrs["spot"] == pytest.approx(spot)


def test_the_flip_level_is_the_price_k_days_ago(prices):
    """§A.7's whole claim: no solver, no calibration. On a series with no rolls, `unadj` and
    `propadj` agree up to the scale the fixture applies, so the level is exactly `F_{t-k}`."""
    out = trig.trigger_prices("TEST", lookbacks=(20, 60))
    for row in out.itertuples():
        assert row.flip_price == pytest.approx(prices.iloc[-1 - row.lookback_days])


def test_a_rising_series_is_long_on_every_horizon_and_flips_down(prices):
    out = trig.trigger_prices("TEST", lookbacks=(20, 60, 250))
    assert (out["signal"] == 1).all()
    assert (out["move_from_spot"] < 0).all(), "a long signal flips on a fall"


def test_momentum_refuses_any_series_but_propadj(prices):
    """`unadj` fabricates a jump at every roll and would invent signal flips that never
    happened; `backadj` levels are not prices."""
    for wrong in ("unadj", "backadj"):
        with pytest.raises(TriggerError, match="momentum needs"):
            trig.trigger_prices("TEST", adjustment=wrong)


def test_a_lookback_longer_than_the_history_is_null_not_wrong(prices):
    out = trig.trigger_prices("TEST", lookbacks=(20, 5_000))
    assert out.loc[out["lookback_days"] == 5_000, "flip_price"].isna().all()
    assert out.loc[out["lookback_days"] == 20, "flip_price"].notna().all()


def test_as_of_truncates_rather_than_reaching_forward(prices):
    """The block must be computable for a past week without seeing later prices."""
    full = trig.trigger_prices("TEST", lookbacks=(20,))
    early = trig.trigger_prices("TEST", lookbacks=(20,), as_of="2025-01-01")
    assert early.attrs["spot"] < full.attrs["spot"], "a rising series must have risen since"
    assert early["as_of"].iloc[0] <= pd.Timestamp("2025-01-01")


# ── The vol shock, in the right units ───────────────────────────────────────
def test_vol_shock_elasticity_is_exactly_minus_one():
    """§A.7: a doubling of volatility forces a 50% cut with no reference to price."""
    assert trig.vol_shock_reduction(0.20, 0.40) == pytest.approx(0.5)
    assert trig.vol_shock_reduction(0.10, 0.40) == pytest.approx(0.75)
    assert trig.vol_shock_reduction(0.20, 0.20) == pytest.approx(0.0)


def test_the_shock_is_applied_in_annualised_units(prices):
    """A five-point shock means five ANNUALISED points. Applied to a daily sigma of 1.5% it
    would be a 4x move, and every market would print the same near-total liquidation, which
    is exactly what the first version did.
    """
    block = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.015,
                               adv=50_000.0, vol_shock_points=0.05)
    annual = 0.015 * (252 ** 0.5)
    assert block["sigma_annual"] == pytest.approx(annual)
    assert block["vol_shock_reduction"] == pytest.approx(1 - annual / (annual + 0.05))
    assert 0.1 < block["vol_shock_reduction"] < 0.3, "should be a sane fraction, not ~0.8"


def test_two_markets_with_different_vol_get_different_shocks(prices):
    """The bug that motivated the units fix printed the same figure for every market."""
    calm = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.010, adv=50_000.0)
    wild = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.035, adv=50_000.0)
    assert calm["vol_shock_reduction"] > wild["vol_shock_reduction"] * 1.5


def test_a_non_positive_volatility_is_refused():
    with pytest.raises(TriggerError, match="positive"):
        trig.vol_shock_reduction(0.0, 0.2)


# ── The pool is observed, and the flow convention is explicit ──────────────
def test_both_flow_conventions_are_reported_and_neither_is_chosen(prices):
    """A sign flip takes the signal from +1 to -1, so §A.7's `delta_s` is 2 and the modelled
    flow is a full reversal. Closing is half that. The difference is a factor of two on every
    downstream number, so both are printed."""
    block = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.015, adv=50_000.0)
    assert block["flows"]["close"]["contracts"] == pytest.approx(100_000.0)
    assert block["flows"]["reverse"]["contracts"] == pytest.approx(200_000.0)
    assert (block["flows"]["reverse"]["days_adv"]
            == pytest.approx(2 * block["flows"]["close"]["days_adv"]))


def test_impact_is_concave_so_doubling_the_flow_costs_less_than_double(prices):
    """§A.5's square-root law. Doubling the crowd raises the cost by sqrt(2), not 2."""
    block = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.015, adv=50_000.0)
    close, reverse = block["flows"]["close"], block["flows"]["reverse"]
    assert reverse["impact_bps"] == pytest.approx(close["impact_bps"] * (2 ** 0.5))


def test_the_pool_is_a_magnitude_so_a_short_book_is_not_negative(prices):
    short_book = MARKET.copy()
    short_book["net_contracts"] = -80_000.0
    block = trig.trigger_block("TEST", market_row=short_book, sigma_daily=0.015, adv=50_000.0)
    assert block["pool_contracts"] == pytest.approx(80_000.0)


def test_no_pool_is_refused_rather_than_modelled(prices):
    """§A.7 would estimate one from a replicated CTA book with a calibrated AUM. There is no
    such model here on purpose, so a missing pool is an error rather than a guess."""
    without = MARKET.drop("net_contracts")
    with pytest.raises(TriggerError, match="does not model one"):
        trig.trigger_block("TEST", market_row=without, sigma_daily=0.015, adv=50_000.0)


def test_missing_volume_yields_null_flow_figures_not_fabricated_ones(prices):
    block = trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.015, adv=0.0)
    assert block["flows"]["close"]["days_adv"] is None
    assert block["flows"]["close"]["impact_bps"] is None


# ── Rendering ───────────────────────────────────────────────────────────────
def test_the_block_prints_every_input_beside_its_result(prices):
    """House style, and the reason the block is worth having at all: a synthesis that hides
    its terms cannot be checked."""
    text = trig.format_block(
        trig.trigger_block("TEST", market_row=MARKET, sigma_daily=0.015, adv=50_000.0))
    for expected in ("spot:", "observed pool:", "fragility (Phi):", "20d flips at:",
                     "flow if pool close", "flow if pool reverse", "vol now:",
                     "vol shock"):
        assert expected in text, expected
    assert "annualised" in text and "daily" in text, "both vol units must be shown"
