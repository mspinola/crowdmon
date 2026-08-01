"""Exit cost: the square-root law, Amihud, and the multiplier that Amihud needs.

Offline. `cotdata.get_prices` is patched so every figure is checkable by hand; the claims
about real markets are in `test_impact_live.py`.
"""
import numpy as np
import pandas as pd
import pytest

DATES = pd.bdate_range("2024-01-01", "2026-07-31")


def _bars(closes, volume):
    return pd.DataFrame({"Open": closes, "High": closes, "Low": closes, "Close": closes,
                         "Volume": volume, "Open Interest": [50_000.0] * len(DATES)},
                        index=pd.DatetimeIndex(DATES, name="Date"))


@pytest.fixture()
def prices(monkeypatch):
    """Alternating +/-1% on a 100.0 base at 1,000 contracts/day: sigma is a known 1%."""
    import cotdata

    closes = [100.0]
    for i in range(1, len(DATES)):
        closes.append(closes[-1] * (1.01 if i % 2 else 1 / 1.01))
    bars = _bars(closes, [1_000.0] * len(DATES))

    def fake(symbol, adjustment="backadj", volume="front", **kw):
        return bars if symbol == "GC" else pd.DataFrame()

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return bars


def _frame(**over):
    row = {"report_date": pd.Timestamp("2026-07-21"), "symbol": "GC", "point_value": 100.0,
           "market_code": "088691", "adv": 1_000.0, "q_sell": 4_000.0, "q_buy": 250.0}
    row.update(over)
    return pd.DataFrame([row])


# ── the law itself ──────────────────────────────────────────────────────────
def test_the_square_root_law_is_y_sigma_root_q_over_v():
    from crowdmon.core.impact import square_root_impact

    # Q/V = 4, sqrt = 2, so I = 0.75 * 0.02 * 2 = 3%
    assert square_root_impact(0.02, 400.0, 100.0, y=0.75) == pytest.approx(0.03)


def test_impact_is_multiplicative_in_sigma_not_additive():
    """The appendix's stated reason these episodes are short and deep rather than long and
    shallow: crowding and volatility compound. Doubling sigma doubles the exit cost with the
    position unchanged."""
    from crowdmon.core.impact import square_root_impact

    base = square_root_impact(0.02, 400.0, 100.0)
    assert square_root_impact(0.04, 400.0, 100.0) == pytest.approx(2 * base)


def test_quadrupling_the_position_only_doubles_the_cost():
    """The square root is the whole point. A linear cost model would put this at 4x."""
    from crowdmon.core.impact import square_root_impact

    assert square_root_impact(0.02, 1_600.0, 100.0) == pytest.approx(
        2 * square_root_impact(0.02, 400.0, 100.0))


def test_the_law_is_unit_free_in_q_over_v():
    """Same invariance `T = Q/(kappa V)` has, and the same failure available: converting one
    side and not the other. Contracts over contracts and dollars over dollars agree."""
    from crowdmon.core.impact import square_root_impact

    contracts = square_root_impact(0.02, 400.0, 100.0)
    scale = 250.0 * 3_000.0                       # multiplier x price
    assert square_root_impact(0.02, 400.0 * scale, 100.0 * scale) == pytest.approx(contracts)
    # And the failure, which is silent: only the numerator converted.
    assert square_root_impact(0.02, 400.0 * scale, 100.0) > 100 * contracts


def test_a_zero_volume_gives_null_not_an_infinity():
    """"No volume" is a data-coverage statement far more often than a market that cannot be
    traded, and an infinity propagates silently into a later mean."""
    from crowdmon.core.impact import square_root_impact

    assert np.isnan(square_root_impact(0.02, 400.0, 0.0))


def test_a_negative_quantity_is_refused():
    """Q_sell and Q_buy are both magnitudes, so a negative one means a lost sign convention.
    sqrt would return nan on its own, which would look like missing data instead."""
    from crowdmon.core.impact import ImpactError, square_root_impact

    with pytest.raises(ImpactError, match="magnitude"):
        square_root_impact(0.02, -400.0, 100.0)


# ── Amihud and the multiplier ───────────────────────────────────────────────
def test_amihud_is_the_trailing_mean_of_absolute_return_over_dollar_volume():
    from crowdmon.core.impact import amihud

    r = pd.Series([0.02] * 300, index=DATES[:300])
    dv = pd.Series([1e6] * 300, index=DATES[:300])
    assert amihud(r, dv).iloc[-1] == pytest.approx(2e-8)


def test_amihud_without_a_multiplier_is_refused(prices):
    """The trap in this layer. Dropping the multiplier leaves a positive series of the right
    general size and simply the wrong ordering: rank correlation 0.500 against the correct
    figure, 8 of 25 markets moving more than five places. Nothing downstream can detect it,
    so it is refused at the door."""
    from crowdmon.core.impact import ImpactError
    from crowdmon.futures import amihud_series

    with pytest.raises(ImpactError, match="MULTIPLIER"):
        amihud_series("GC", None)
    with pytest.raises(ImpactError, match="MULTIPLIER"):
        amihud_series("GC", 0.0)


def test_the_multiplier_scales_amihud_exactly(prices):
    """A 10x multiplier is 10x the dollar volume, so exactly a tenth of the illiquidity. That
    linearity is why omitting it reorders markets rather than shifting them all equally."""
    from crowdmon.futures import amihud_series

    one = amihud_series("GC", 10.0).dropna().iloc[-1]
    ten = amihud_series("GC", 100.0).dropna().iloc[-1]
    assert one == pytest.approx(10 * ten)


# ── the frame-level join ────────────────────────────────────────────────────
def test_add_impact_populates_both_directions(prices):
    from crowdmon.futures import add_impact

    got = add_impact(_frame()).iloc[0]
    assert got.sigma_daily == pytest.approx(0.01, rel=0.02)
    # Q/V = 4 for the sell side, so sqrt = 2
    assert got.impact_sell == pytest.approx(0.75 * got.sigma_daily * 2.0, rel=1e-6)
    assert got.impact_sell_bps == pytest.approx(got.impact_sell * 1e4)
    # and the buy side is smaller, because the position is
    assert got.impact_buy < got.impact_sell


def test_impact_uses_no_data_after_the_as_of_date(monkeypatch):
    """Point-in-time, like every other join in this layer."""
    import cotdata

    from crowdmon.futures import add_impact

    closes = [100.0] * len(DATES)
    for i, d in enumerate(DATES):
        closes[i] = 100.0 if d <= pd.Timestamp("2026-07-21") else 100.0 * (1 + 0.4 * (i % 2))
    monkeypatch.setattr(cotdata, "get_prices",
                        lambda *a, **k: _bars(closes, [1_000.0] * len(DATES)))
    got = add_impact(_frame()).iloc[0]
    assert got.sigma_daily == pytest.approx(0.0, abs=1e-9)     # flat up to the report date


def test_rows_without_a_symbol_keep_their_place(prices):
    from crowdmon.futures import add_impact, impact_coverage

    got = add_impact(pd.concat([_frame(), _frame(symbol=None)], ignore_index=True))
    assert len(got) == 2
    cov = impact_coverage(got)
    assert cov["with_impact"] == 1 and cov["no_symbol"] == 1 and cov["total"] == 2


def test_missing_prerequisite_columns_name_every_step_that_provides_them(prices):
    from crowdmon.core.impact import ImpactError
    from crowdmon.futures import add_impact

    with pytest.raises(ImpactError, match="volume.add_volume"):
        add_impact(_frame().drop(columns=["adv"]))


def test_an_empty_frame_still_gains_the_impact_columns(prices):
    from crowdmon.futures import IMPACT_COLUMNS, add_impact

    got = add_impact(_frame().iloc[0:0])
    assert all(c in got.columns for c in IMPACT_COLUMNS)


def test_y_is_an_argument_so_its_effect_is_visible_in_the_call(prices):
    """Configured, not fitted, in the same spirit as the fragility weights. The appendix
    sanctions 0.5 to 1.0 and the difference between the ends is 2x."""
    from crowdmon.futures import add_impact

    low = add_impact(_frame(), y=0.5)["impact_sell"].iloc[0]
    high = add_impact(_frame(), y=1.0)["impact_sell"].iloc[0]
    assert high == pytest.approx(2 * low)
