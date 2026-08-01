"""The composite `D = C x I x Phi`, appendix §A.9.

The arithmetic is trivial and the readings are not, so most of what is asserted here is that
the three settled interpretations stayed settled: `C` is the percentile of `z` and not of
`x`, `Phi` enters raw and not as a percentile, and a missing factor nulls `D` rather than
being quietly treated as 1.0. Each of those would produce plausible numbers if it drifted.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import add_composite, damage_report, top_damage
from crowdmon.futures.composite import CompositeError

WEEKS = 260  # five years, enough for a three-year window plus warm-up


def _frames(n: int = WEEKS, *, phi: float = 0.4, seed: int = 0):
    """A minimal (fragility, extremity) pair at the two grains `add_composite` joins."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-02", periods=n, freq="7D")
    base = {"market_code": "TEST01", "report_type": "disaggregated", "combined": False}
    fragility = pd.DataFrame([{
        **base, "report_date": d, "market_name": "TEST MARKET", "phi": phi,
        "dtl_sell": v, "dtl_buy": v * 0.5,
    } for d, v in zip(dates, rng.uniform(1, 20, n))])
    extremity = pd.DataFrame([{
        **base, "report_date": d, "category": "managed_money", "net_risk_usd_z": z,
    } for d, z in zip(dates, rng.normal(size=n))])
    return fragility, extremity


# ── The formula, taken literally ────────────────────────────────────────────
def test_damage_is_the_product_of_its_three_factors():
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52).dropna(subset=["damage_sell"])
    assert not out.empty
    expected = out["crowding_long"] * out["illiquidity_sell"] * out["fragility"]
    assert out["damage_sell"].to_numpy() == pytest.approx(expected.to_numpy())


def test_phi_is_percentile_ised_by_default_and_the_literal_form_is_reachable():
    """§A.9's preamble says every term is a percentile; its formula writes `Phi` out in full.
    The preamble is followed, because the literal form left `Phi` correlating 0.145 with `D`
    against 0.86 and 0.80 for the other two (amendments §A15).

    `fragility` is whichever reading `D` actually used, and both `phi` and `phi_pct` are
    always emitted, so the output says which produced the number.

    Note what a CONSTANT `Phi` percentile-ises to: about 0.5, not 1.0. Every value in the
    window ties, and ties take their average rank, so a market whose participant mix never
    changes sits in the middle of its own distribution. That is the right answer and it is
    not the obvious one.
    """
    fragility, extremity = _frames(phi=0.25)

    default = add_composite(fragility, extremity, min_periods=52).dropna(
        subset=["damage_sell"])
    assert default["fragility"].equals(default["phi_pct"])
    assert default["fragility"].between(0.4, 0.6).all(), "a constant Phi ranks mid-window"
    assert default["damage_sell"].to_numpy() == pytest.approx(
        (default["crowding_long"] * default["illiquidity_sell"]
         * default["fragility"]).to_numpy())

    literal = add_composite(fragility, extremity, phi_percentile=False,
                            min_periods=52).dropna(subset=["damage_sell"])
    assert (literal["fragility"] == 0.25).all()
    assert literal["damage_sell"].to_numpy() == pytest.approx(
        (literal["crowding_long"] * literal["illiquidity_sell"] * 0.25).to_numpy())

    for frame in (default, literal):
        assert frame["phi"].notna().all() and frame["phi_pct"].notna().all()


def test_percentile_ising_phi_costs_a_warm_up_the_raw_reading_does_not():
    """`Phi` raw is never missing, since it needs only COT. Its percentile needs history.

    On the real panel that costs **nothing**, which is not obvious and was worth measuring:
    coverage is 77.0% under both readings, because `C = pct(z)` already needs two stacked
    three-year windows and is the binding constraint. `pct(Phi)` needs one and finishes
    warming up well inside it. The warm-up below is visible only because this fixture is
    shorter than the real panel.
    """
    fragility, extremity = _frames()
    default = add_composite(fragility, extremity, min_periods=52)
    literal = add_composite(fragility, extremity, phi_percentile=False, min_periods=52)
    assert literal["fragility"].notna().all()
    assert default["fragility"].isna().sum() == 51


def test_crowding_is_the_percentile_of_z_not_of_the_raw_position():
    """`C = pct(z_t)`, and the two differ. `z` is already standardised against a trailing
    window, so its percentile is a second standardisation and does not track `pct(x)`."""
    from crowdmon.core.aggregate import rolling_percentile

    fragility, extremity = _frames(seed=7)
    out = add_composite(fragility, extremity, min_periods=52)

    z_series = extremity.set_index("report_date")["net_risk_usd_z"]
    pct_of_z = rolling_percentile(z_series, min_periods=52).to_numpy()
    assert out["crowding_long"].to_numpy() == pytest.approx(pct_of_z, nan_ok=True)

    # And it is genuinely a different series from the percentile of the underlying value.
    pct_of_x = rolling_percentile(z_series.cumsum(), min_periods=52).to_numpy()
    both = ~np.isnan(pct_of_z) & ~np.isnan(pct_of_x)
    assert not np.allclose(pct_of_z[both], pct_of_x[both])


def test_the_two_directions_mirror_each_other_in_crowding():
    """`z` is signed, so a high `pct(z)` is a crowded long and a low one a crowded short.
    Using `pct(z)` for both sides would score an extreme short as safe."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52).dropna(
        subset=["crowding_long"])
    assert out["crowding_short"].to_numpy() == pytest.approx(
        1.0 - out["crowding_long"].to_numpy())


# ── Multiplicative, which is the argument ───────────────────────────────────
def test_any_factor_near_zero_collapses_the_damage():
    """"A large position in a liquid market held by unconstrained hedgers is safe." An
    additive score would let one extreme term carry a market into the danger zone alone."""
    fragility, extremity = _frames(phi=0.0)
    out = add_composite(fragility, extremity, phi_percentile=False,
                        min_periods=52).dropna(subset=["damage_sell"])
    assert (out["damage_sell"] == 0.0).all()
    assert (out["damage_buy"] == 0.0).all()


def test_every_factor_and_product_stays_in_the_unit_interval():
    fragility, extremity = _frames(seed=3)
    out = add_composite(fragility, extremity, min_periods=52)
    for column in ("crowding_long", "crowding_short", "illiquidity_sell",
                   "illiquidity_buy", "damage_sell", "damage_buy"):
        values = out[column].dropna()
        assert values.between(0.0, 1.0).all(), column


def test_a_phi_outside_the_unit_interval_is_caught():
    """All three factors are bounded by construction, so a breach means one stopped being
    what it claims. The check runs on every computation, not only here."""
    fragility, extremity = _frames(phi=1.4)
    with pytest.raises(CompositeError, match=r"left \[0, 1\]"):
        add_composite(fragility, extremity, phi_percentile=False, min_periods=52)


# ── Missing factors ─────────────────────────────────────────────────────────
def test_a_missing_factor_nulls_the_damage_rather_than_being_treated_as_one():
    """A composite computed from two of three factors is not the composite, and would rank a
    market with no volume data above one with a genuinely low reading."""
    fragility, extremity = _frames()
    fragility.loc[fragility.index[-20:], "dtl_sell"] = np.nan
    out = add_composite(fragility, extremity, min_periods=52)
    tail = out.iloc[-20:]
    assert tail["damage_sell"].isna().all()
    assert tail["damage_buy"].notna().any(), "the other direction must be unaffected"


def test_damage_report_separates_the_three_causes():
    fragility, extremity = _frames()
    fragility.loc[fragility.index[-10:], "dtl_sell"] = np.nan
    report = damage_report(add_composite(fragility, extremity, min_periods=52))
    assert report.loc["no_illiquidity", "rows"] >= 10
    assert report.loc["no_fragility", "rows"] == 51  # pct(Phi) warm-up
    assert report.loc["total", "rows"] == WEEKS


# ── No lookahead, inherited but asserted here too ───────────────────────────
def test_a_damage_score_never_changes_when_later_data_arrives():
    """Inherited from `core.aggregate`, asserted again at this level because the composite
    adds two more rolling passes (`pct(z)` and `pct(D)`) and either could break it."""
    fragility, extremity = _frames(n=300, seed=11)
    full = add_composite(fragility, extremity, min_periods=52)
    early = add_composite(fragility.iloc[:200].copy(), extremity.iloc[:200].copy(),
                          min_periods=52)
    for column in ("crowding_long", "illiquidity_sell", "damage_sell", "damage_sell_pct"):
        pd.testing.assert_series_equal(
            early[column], full[column].iloc[:200], check_names=False)


# ── Refusals ────────────────────────────────────────────────────────────────
def test_a_frame_spanning_report_types_is_refused():
    fragility, extremity = _frames()
    mixed = pd.concat([fragility, fragility.assign(report_type="tff")], ignore_index=True)
    with pytest.raises(CompositeError, match="report types"):
        add_composite(mixed, extremity, min_periods=52)


def test_an_absent_crowding_category_is_named():
    fragility, extremity = _frames()
    with pytest.raises(CompositeError, match="swap"):
        add_composite(fragility, extremity, category="swap", min_periods=52)


def test_a_fragility_frame_without_durations_is_refused():
    fragility, extremity = _frames()
    with pytest.raises(CompositeError, match="dtl_sell"):
        add_composite(fragility.drop(columns=["dtl_sell"]), extremity, min_periods=52)


def test_top_damage_shows_every_factor_beside_the_score():
    """A composite that does not show its terms is unauditable: `D` near zero because the
    market is liquid and `D` near zero because nobody fragile holds it are different."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    top = top_damage(out, n=3)
    for column in ("crowding_long", "illiquidity_sell", "fragility", "phi", "damage_sell"):
        assert column in top.columns
    with pytest.raises(CompositeError, match="'sell' or 'buy'"):
        top_damage(out, side="both")
