"""The composite `D = C x I x Phi`, appendix §A.9.

The arithmetic is trivial and the readings are not, so most of what is asserted here is that
the three settled interpretations stayed settled: `C` is the percentile of `z` and not of
`x`, `Phi` enters raw and not as a percentile, and a missing factor nulls `D` rather than
being quietly treated as 1.0. Each of those would produce plausible numbers if it drifted.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import (
    FLOW_STATES,
    SCORE_STATES,
    UNWIND_STATES,
    add_composite,
    add_score_state,
    add_unwind_state,
    damage_block,
    damage_report,
    top_damage,
)
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


# ── The two per-row caveat carriers, `2026-08-03 §C20` and `§C21` ───────────
def test_score_state_separates_the_two_null_causes_with_no_exceptions():
    """`§C20`'s rule: all three terms present AND the percentile null means warm-up.

    The two causes mean opposite things. A young series will score later; a market missing
    a factor may never, and `coverage.drops_at` names the rung. Rendered identically they
    read the same, which is the first degenerate input the report-layer handoff lists.
    """
    fragility, extremity = _frames()
    out = add_score_state(add_composite(fragility, extremity, min_periods=52))

    assert set(out["score_state_sell"]) <= set(SCORE_STATES)
    scored = out["damage_sell_pct"].notna()
    assert (out.loc[scored, "score_state_sell"] == "scored").all()
    assert not (out.loc[~scored, "score_state_sell"] == "scored").any()

    warm = out["score_state_sell"] == "warmup"
    assert warm.any(), "260 weeks against a 52-week min_periods must warm up somewhere"
    terms = ["crowding_long", "illiquidity_sell", "fragility"]
    assert out.loc[warm, terms].notna().all().all(), (
        "a warm-up row has every factor and only lacks history; a row missing a factor is a "
        "different state and must not be labelled warm-up")


def test_a_null_percentile_with_no_missing_term_and_no_warm_up_is_refused():
    """The invariant that makes the state trustworthy: every null carries a reason."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    # `damage_sell` is the product of three factors, so it is null iff a factor is. Break
    # that and the state column would have to guess, which is what it exists not to do.
    out.loc[out["damage_sell_pct"].isna(), "damage_sell"] = pd.NA
    with pytest.raises(CompositeError, match="stopped propagating null"):
        add_score_state(out, sides=("sell",))


def test_score_state_names_the_first_missing_factor():
    """`SCORE_TERMS` order decides a row missing more than one, and crowding comes first.

    Early weeks are missing crowding anyway (`pct(z)` stacks two windows), so the label
    there is `no_crowding` even once illiquidity is knocked out too. That is the documented
    behaviour and not a tie-break to be surprised by later: the frame still carries all
    three columns for a reader who wants the rest.
    """
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    for column in ("illiquidity_sell", "damage_sell", "damage_sell_pct"):
        out[column] = np.nan
    state = add_score_state(out, sides=("sell",))["score_state_sell"]

    has_crowding = out["crowding_long"].notna()
    assert has_crowding.any() and (~has_crowding).any()
    assert (state[has_crowding] == "no_illiquidity").all()
    assert (state[~has_crowding] == "no_crowding").all()


def test_every_flow_state_is_either_decisive_or_silent():
    """A state added to `flow.py` must be classified here, not land in a bucket by luck."""
    from crowdmon.futures.composite import DECISIVE_FLOW_STATES, SILENT_FLOW_STATES

    assert DECISIVE_FLOW_STATES | SILENT_FLOW_STATES == set(FLOW_STATES)
    assert not DECISIVE_FLOW_STATES & SILENT_FLOW_STATES


def test_unwind_state_speaks_on_liquidation_and_says_indeterminate_on_mixed():
    """`§C21`: right at the extremes, silent on 3 falling weeks in 5, and it says so."""
    fragility, extremity = _frames()
    scored = add_composite(fragility, extremity, min_periods=52)

    for state, expected in (("long_liquidation", "mid_exit"),
                            ("new_longs", "falling_not_exit"),
                            ("mixed", "indeterminate"),
                            ("quiet", "indeterminate"),
                            ("gap", "indeterminate")):
        out = add_unwind_state(scored, _flow_frame(scored, state))
        falling = out["d_damage_sell_pct"] < 0
        assert falling.any(), f"no falling week to classify under {state}"
        assert (out.loc[falling, "unwind_state_sell"] == expected).all()
        rising = out["d_damage_sell_pct"] >= 0
        assert (out.loc[rising, "unwind_state_sell"] == "not_falling").all()
        assert set(out["unwind_state_sell"]) <= set(UNWIND_STATES)


def test_the_buy_side_reads_short_covering_rather_than_long_liquidation():
    """`damage_buy` is a crowded SHORT forced to buy, so its exit is the shorts covering."""
    fragility, extremity = _frames()
    scored = add_composite(fragility, extremity, min_periods=52)

    covering = add_unwind_state(scored, _flow_frame(scored, "short_covering"), side="buy")
    falling = covering["d_damage_buy_pct"] < 0
    assert falling.any()
    assert (covering.loc[falling, "unwind_state_buy"] == "mid_exit").all()

    liquidation = add_unwind_state(scored, _flow_frame(scored, "long_liquidation"),
                                   side="buy")
    assert (liquidation.loc[falling, "unwind_state_buy"] == "falling_not_exit").all()


def test_the_difference_never_crosses_a_market_boundary():
    """`ΔD` is per market. A diff taken across a concatenated frame invents a change."""
    fragility, extremity = _frames()
    other_f = fragility.assign(market_code="TEST02")
    other_e = extremity.assign(market_code="TEST02")
    scored = add_composite(pd.concat([fragility, other_f], ignore_index=True),
                           pd.concat([extremity, other_e], ignore_index=True),
                           min_periods=52)
    out = add_unwind_state(scored, _flow_frame(scored, "mixed"))

    first = out.sort_values("report_date").groupby("market_code").head(1)
    assert first["d_damage_sell_pct"].isna().all(), (
        "each market's first week has no predecessor of its own")


def test_a_flows_frame_with_two_rows_per_market_week_is_refused():
    fragility, extremity = _frames()
    scored = add_composite(fragility, extremity, min_periods=52)
    flows = _flow_frame(scored, "mixed")
    with pytest.raises(CompositeError, match="more than one"):
        add_unwind_state(scored, pd.concat([flows, flows], ignore_index=True))


def _flow_frame(scored: pd.DataFrame, state: str) -> pd.DataFrame:
    return pd.DataFrame({
        "report_date": scored["report_date"], "market_code": scored["market_code"],
        "category": "managed_money", "flow_state": state,
    })
# ── The delivered block: D_pct never travels alone ──────────────────────────
def test_damage_block_publishes_all_three_factors_beside_the_headline():
    """`D_pct` on its own is not auditable, and three separate findings say so: `D` is a
    product so its smallest term dominates, `Phi`'s effect on `D_pct` is not monotone, and
    `Phi` carries no signal independent of the weights while moving the published
    percentile by more than 0.3 in one week of ten."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    block = damage_block(out, "TEST01")

    for key in ("crowding", "illiquidity", "fragility", "damage", "damage_pct"):
        assert block[key] is not None, key
    assert block["crowding"] * block["illiquidity"] * block["fragility"] == pytest.approx(
        block["damage"])
    # The raw level travels too: a percentile cannot say whether the level is trivial.
    assert block["raw"]["dtl"] is not None
    assert block["raw"]["phi"] == pytest.approx(0.4)


def test_damage_block_takes_the_buy_side_factors_for_the_buy_side():
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    sell, buy = damage_block(out, "TEST01"), damage_block(out, "TEST01", side="buy")
    row = out[out["report_date"] == out["report_date"].max()].iloc[0]
    assert sell["crowding"] == pytest.approx(row["crowding_long"])
    assert buy["crowding"] == pytest.approx(row["crowding_short"])
    assert buy["illiquidity"] == pytest.approx(row["illiquidity_buy"])
    assert buy["raw"]["dtl"] == pytest.approx(row["dtl_buy"])
    with pytest.raises(CompositeError, match="'sell' or 'buy'"):
        damage_block(out, "TEST01", side="both")


def test_damage_block_names_an_absent_market_week_rather_than_returning_empty():
    """`add_composite` keeps unscored rows with a null D, so an empty selection means the
    market-week is absent rather than merely unscored, and the error says which."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    with pytest.raises(CompositeError, match="NOPE"):
        damage_block(out, "NOPE")


def test_damage_block_survives_a_null_factor_instead_of_hiding_it():
    """A market with too little history has a null `D`; the block must still render, with
    the missing factor visible, rather than raising or silently substituting."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    early = out["report_date"].min()
    block = damage_block(out, "TEST01", report_date=early)
    assert block["damage_pct"] is None
    assert block["crowding"] is None or block["illiquidity"] is None


def test_format_damage_block_shows_the_factors_and_refuses_the_probability_reading():
    from crowdmon.futures.report import damage_band, format_damage_block

    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    text = format_damage_block(damage_block(out, "TEST01"))
    for token in ("crowding", "illiquidity", "fragility", "D_pct"):
        assert token in text
    # The three readings a bare percentile invites, each explicitly denied.
    assert "not a probability" in text
    assert "not a forecast" in text
    assert "monotone" in text
    assert damage_band(0.95) == "top decile"
    assert damage_band(None) == "unscored"


# ── The offside term travels beside D, never inside it ──────────────────────
def test_damage_block_carries_offside_as_nulls_when_the_trigger_never_ran():
    """`add_trigger_distance` is optional, so the key must exist and be null rather than
    absent: a caller doing `block["offside"]["distance_sigma"]` should get `None`, not a
    KeyError that reads as a bug in their code."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    block = damage_block(out, "TEST01")
    assert block["offside"]["distance_sigma"] is None
    assert block["offside"]["horizons_disagree"] is None


def test_damage_block_reads_the_trigger_columns_for_the_matching_side():
    """The side convention must line up with Q_sell/T_sell/damage_sell: a signal that is
    long flips DOWN and forces SELLING. Pairing a trigger with the opposite side's severity
    is the one error here that produces entirely plausible numbers."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    latest = out["report_date"] == out["report_date"].max()
    out.loc[latest, "trigger_sell_sigma"] = 0.5
    out.loc[latest, "trigger_sell_pct"] = 0.004
    out.loc[latest, "trigger_sell_k"] = 20
    out.loc[latest, "trigger_buy_sigma"] = 7.5
    out.loc[latest, "trigger_buy_pct"] = 0.06
    out.loc[latest, "trigger_buy_k"] = 250
    out.loc[latest, "trigger_horizons_disagree"] = True

    sell = damage_block(out, "TEST01", side="sell")["offside"]
    buy = damage_block(out, "TEST01", side="buy")["offside"]
    assert sell["distance_sigma"] == pytest.approx(0.5)
    assert sell["lookback_days"] == pytest.approx(20)
    assert buy["distance_sigma"] == pytest.approx(7.5)
    assert buy["lookback_days"] == pytest.approx(250)
    assert sell["horizons_disagree"] is True


def test_the_offside_term_is_never_folded_into_the_damage_score():
    """D must be exactly C x I x Phi whether or not a trigger distance is present. A.10
    makes D a conditional severity; multiplying in a distance would make it unconditional,
    and the distance is the trailing k-day return so it would also double-count C."""
    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    before = out["damage_sell"].copy()
    out["trigger_sell_sigma"] = 0.1          # as close to firing as it gets
    out["trigger_sell_pct"] = 0.001
    out["trigger_sell_k"] = 20
    after = add_composite(fragility, extremity, min_periods=52)["damage_sell"]
    pd.testing.assert_series_equal(before, after)
    row = out[out["report_date"] == out["report_date"].max()].iloc[0]
    assert row["damage_sell"] == pytest.approx(
        row["crowding_long"] * row["illiquidity_sell"] * row["fragility"])


def test_format_offside_names_the_quadrant_and_refuses_the_forecast_reading():
    from crowdmon.futures.report import CLOSE_SIGMA, format_offside

    close_severe = format_offside(
        {"distance_sigma": 0.5, "distance_pct": 0.004, "lookback_days": 20,
         "horizons_disagree": True}, side="sell", damage_pct=0.95)
    assert "CLOSE and SEVERE" in close_severe
    assert "not a forecast" in close_severe
    assert "DISAGREE" in close_severe

    far_severe = format_offside(
        {"distance_sigma": 9.0, "distance_pct": 0.2, "lookback_days": 250,
         "horizons_disagree": False}, side="sell", damage_pct=0.95)
    assert "not close" in far_severe
    assert "DISAGREE" not in far_severe

    # The boundary is inclusive, so a market exactly at the threshold reads as close.
    edge = format_offside(
        {"distance_sigma": CLOSE_SIGMA, "distance_pct": 0.01, "lookback_days": 60,
         "horizons_disagree": False}, side="sell", damage_pct=0.95)
    assert "CLOSE and SEVERE" in edge


def test_an_unscored_row_gets_its_own_reading_rather_than_a_broken_sentence():
    """A null `D_pct` used to render "in this market,  looked less dangerous", which is not
    a sentence. Lumber is the live case: four years of prices against the six `C = pct(z)`
    needs, so `I` and `Phi` exist and the product cannot be formed."""
    from crowdmon.futures.report import format_damage_block

    fragility, extremity = _frames()
    out = add_composite(fragility, extremity, min_periods=52)
    text = format_damage_block(damage_block(out, "TEST01",
                                            report_date=out["report_date"].min()))
    assert "UNSCORED" in text
    assert "looked less" not in text
    assert "cannot be formed" in text


def test_a_trigger_whose_pool_sits_on_the_other_side_is_flagged_not_shown_plainly():
    """The signal says what a trend follower WOULD hold; COT says what levered money DOES.
    They disagree on a third of (market, horizon) pairs, and where they do the level is real
    while the book it would force is absent."""
    from crowdmon.futures.report import format_offside

    disagrees = format_offside(
        {"distance_sigma": 0.5, "distance_pct": 0.004, "lookback_days": 20,
         "pool_agrees": False, "horizons_disagree": True},
        side="sell", damage_pct=0.95)
    assert "OTHER side" in disagrees
    # The quadrant is suppressed: calling it CLOSE and SEVERE would be exactly wrong.
    assert "CLOSE and SEVERE" not in disagrees

    unknown = format_offside(
        {"distance_sigma": 0.5, "distance_pct": 0.004, "lookback_days": 20,
         "pool_agrees": None, "horizons_disagree": False},
        side="sell", damage_pct=0.95)
    assert "no pool supplied" in unknown

    agrees = format_offside(
        {"distance_sigma": 0.5, "distance_pct": 0.004, "lookback_days": 20,
         "pool_agrees": True, "horizons_disagree": False},
        side="sell", damage_pct=0.95)
    assert "CLOSE and SEVERE" in agrees
    assert "OTHER side" not in agrees
