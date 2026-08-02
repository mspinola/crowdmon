"""Roll windows, and what they do to an exit-capacity estimate.

The arithmetic is means and medians. What carries the risk is that this module is easy to
mistake for spec §379's roll congestion, which cannot be built, and that its headline figure
is easy to quote as ten times its real size.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import roll as rl
from crowdmon.futures.roll import RollError

DATES = pd.bdate_range("2020-01-01", periods=600)
#: Rolls every 60 bars, so ~18% of bars sit in a 10-bar window: a quarterly-style roller.
ROLLS = pd.DatetimeIndex([DATES[i] for i in range(60, 600, 60)])


@pytest.fixture
def market(monkeypatch):
    """Volume 3x higher on the 10 bars before each roll, so the effect has a known sign."""
    vol = pd.Series(1_000.0, index=DATES)
    for r in ROLLS:
        pos = DATES.get_loc(r)
        vol.iloc[max(0, pos - 10):pos + 1] = 3_000.0

    import cotdata

    monkeypatch.setattr(cotdata, "roll_dates",
                        lambda symbol, adjustment="backadj": ROLLS)
    monkeypatch.setattr(cotdata, "get_prices",
                        lambda symbol, adjustment="propadj", **kw:
                        pd.DataFrame({"Close": 100.0, "Volume": vol}, index=DATES))
    return vol


# ── The module must not be mistaken for §379 ────────────────────────────────
def test_the_module_says_it_is_not_spec_379():
    """The whole reason it is named `roll` and not `congestion`. A later session reading §13
    step 4 must not mark it satisfied by finding this file."""
    doc = rl.__doc__
    assert "NOT module spec" in doc
    assert "per-expiry" in doc
    for component in ("calendar spread", "bid-ask", "OI migration"):
        assert component in doc, component


# ── The roll calendar ───────────────────────────────────────────────────────
def test_bars_to_roll_counts_down_to_zero_on_the_roll(market):
    cal = rl.roll_calendar("TEST")
    for r in ROLLS:
        assert cal.loc[r, "bars_to_roll"] == 0
    pos = DATES.get_loc(ROLLS[1])
    assert cal["bars_to_roll"].iloc[pos - 5] == 5


def test_a_market_with_no_rolls_is_refused_with_the_namedtuple_trap_named(monkeypatch):
    """`roll_dates` returns empty rather than raising on a non-string argument, so an empty
    result has two very different causes and the error must name both. `2026-08-02 §B16`."""
    import cotdata

    monkeypatch.setattr(cotdata, "roll_dates",
                        lambda symbol, adjustment="backadj": pd.DatetimeIndex([]))
    with pytest.raises(RollError, match="namedtuple"):
        rl.roll_calendar("TEST")


def test_the_window_is_measured_in_bars_not_calendar_days(market):
    """Volume is a per-session quantity, so a calendar window silently varies with holidays."""
    mask = rl.in_roll_window("TEST", window_bars=10)
    per_roll = 11  # the roll bar plus the ten before it
    assert mask.sum() == pytest.approx(len(ROLLS) * per_roll, rel=0.05)


def test_a_zero_or_negative_window_is_refused(market):
    with pytest.raises(RollError, match="at least 1"):
        rl.in_roll_window("TEST", window_bars=0)


# ── The two measures are different questions ────────────────────────────────
def test_the_roll_day_ratio_and_the_adv_effect_are_both_reported(market):
    """Reporting only one invites the other to be inferred from it, and it cannot be."""
    stats = rl.roll_window_stats("TEST")
    assert stats["roll_day_ratio"] == pytest.approx(3.0), "3x by construction in the fixture"
    assert stats["adv_inflation"] > 1.0
    assert stats["adv_inflation"] < stats["roll_day_ratio"], \
        "the ADV effect is diluted by how few days the window is"


def test_the_adv_effect_is_much_smaller_than_the_roll_day_ratio(market):
    """The correction that motivated this test: a 3x lift on ~18% of days is nowhere near a
    3x lift on the average. Quoting the ratio as the bias in `T` overstates it by an order of
    magnitude, which is what happened on the real panel (1.354x ratio, 1.048x ADV)."""
    stats = rl.roll_window_stats("TEST")
    assert stats["t_bias"] < 0.5 * (stats["roll_day_ratio"] - 1.0)


def test_the_ratio_does_not_determine_the_sign_of_the_adv_effect(monkeypatch):
    """Measured on real data: HO has MORE volume on roll days (ratio 1.088) and a LOWER ADV
    from including them (0.979), because the ratio is a median and the ADV is a mean. Anyone
    reasoning from one to the other is wrong about HO in direction.

    Reproduced here with a fat tail outside the window.
    """
    vol = pd.Series(1_000.0, index=DATES)
    for r in ROLLS:
        pos = DATES.get_loc(r)
        vol.iloc[max(0, pos - 10):pos + 1] = 1_200.0     # higher median inside
    vol.iloc[25::60] = 40_000.0                           # fatter tail well outside a window

    import cotdata

    monkeypatch.setattr(cotdata, "roll_dates", lambda symbol, adjustment="backadj": ROLLS)
    monkeypatch.setattr(cotdata, "get_prices",
                        lambda symbol, adjustment="propadj", **kw:
                        pd.DataFrame({"Close": 100.0, "Volume": vol}, index=DATES))

    stats = rl.roll_window_stats("TEST")
    assert stats["roll_day_ratio"] > 1.0, "more volume on roll days, by median"
    assert stats["adv_inflation"] < 1.0, "and yet excluding them RAISES the mean"


# ── A roll-excluded ADV is a different estimator ────────────────────────────
def test_a_monthly_roller_is_admitted_but_flagged_in_the_output(monkeypatch):
    """CL, NG, HO and RB roll monthly and put 52-53% of their days inside a 10-bar window.
    That is admitted rather than refused, because it is the real energy complex and refusing
    it would remove the markets a fuel-shock scenario cares most about. It is flagged instead.
    """
    dense = pd.DatetimeIndex([DATES[i] for i in range(20, 600, 20)])

    import cotdata

    monkeypatch.setattr(cotdata, "roll_dates", lambda symbol, adjustment="backadj": dense)
    monkeypatch.setattr(cotdata, "get_prices",
                        lambda symbol, adjustment="propadj", **kw:
                        pd.DataFrame({"Close": 100.0, "Volume": 1_000.0}, index=DATES))

    stats = rl.roll_window_stats("TEST")
    assert stats["share_in_window"] > 0.4, "monthly rolling by construction"
    assert "different estimator" in rl.format_roll_block(stats)
    rl.roll_adjusted_adv("TEST")  # admitted


def test_a_pathological_roll_density_is_refused_rather_than_returned(monkeypatch):
    """Below the floor the excluded sample stops being a sample. Distinct from the monthly
    case above, which is admitted."""
    everywhere = pd.DatetimeIndex([DATES[i] for i in range(6, 600, 6)])

    import cotdata

    monkeypatch.setattr(cotdata, "roll_dates", lambda symbol, adjustment="backadj": everywhere)
    monkeypatch.setattr(cotdata, "get_prices",
                        lambda symbol, adjustment="propadj", **kw:
                        pd.DataFrame({"Close": 100.0, "Volume": 1_000.0}, index=DATES))

    with pytest.raises(RollError, match="different estimator"):
        rl.roll_adjusted_adv("TEST")


def test_the_excluded_share_is_always_reported_beside_the_figure(market):
    out = rl.roll_adjusted_adv("TEST")
    assert 0.0 < out["excluded_share"] < 1.0
    assert out["adv"] != out["adv_roll_excluded"]


def test_the_unadjusted_adv_is_returned_alongside_never_replaced(market):
    """Moving `T` moves `I`, which moves `D`, which moves every published figure and the §9
    verdict's inputs. This module reports; it does not recalibrate."""
    out = rl.roll_adjusted_adv("TEST")
    assert "adv" in out.index and "adv_roll_excluded" in out.index


# ── Exit collision ──────────────────────────────────────────────────────────
def test_a_long_exit_collides_with_the_next_roll_and_a_short_one_does_not(market):
    cal = rl.roll_calendar("TEST")
    bars_to = cal["bars_to_roll"].iloc[-1]
    if not np.isfinite(bars_to):
        pytest.skip("fixture tail sits past the last roll")
    assert rl.exit_collision("TEST", bars_to + 5)["collides"]
    assert not rl.exit_collision("TEST", max(bars_to - 1, 0))["collides"]


def test_a_negative_exit_duration_is_refused(market):
    with pytest.raises(RollError, match="non-negative"):
        rl.exit_collision("TEST", -1.0)


def test_as_of_truncates_rather_than_reaching_forward(market):
    early = rl.exit_collision("TEST", 5.0, as_of="2021-01-04")
    assert early["as_of"] <= pd.Timestamp("2021-01-04")


# ── Rendering ───────────────────────────────────────────────────────────────
def test_the_block_names_the_trap_in_the_output_not_only_the_docstring(market):
    text = rl.format_roll_block(rl.roll_window_stats("TEST"))
    assert "roll DAYS, not about T" in text
    assert "even in sign" in text
    for expected in ("ADV all / excluded:", "ADV inflation:", "median volume in/out:"):
        assert expected in text, expected
    assert "—" not in text, "house style: no em dashes in output"
