"""Commonality against a REAL store. Skips when there is not one.

The offline tests establish the algebra. These check that the real universe splits the way
§A.6 predicts it should: some markets exit through their own door and some through everyone
else's. That split is the reason the measure is worth having even though it cannot feed §A.9
as written.
"""
import pytest

pytestmark = pytest.mark.needs_vintage


@pytest.fixture(scope="module")
def panel():
    cotdata = pytest.importorskip("cotdata")
    vi = pytest.importorskip("cotdata.vintage_ingest")
    try:
        if cotdata.get_prices("GC", adjustment="unadj").empty or vi.read_observations().empty:
            pytest.skip("store not populated")
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")

    from crowdmon.futures import ContractMaster, VintageCotSource, illiquidity_panel

    cot = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    specs = (cot.dropna(subset=["symbol", "point_value"])[["symbol", "point_value"]]
             .drop_duplicates("symbol").itertuples(index=False, name=None))
    out = illiquidity_panel(specs, start="2015-01-01")
    if out.shape[1] < 15:
        pytest.skip("too few markets with a long enough illiquidity series")
    return out


def test_the_universe_splits_into_independent_and_co_moving_markets(panel):
    """§A.6's whole point: `beta -> 0` is a different door, `beta -> 1` is the same one.

    Livestock and milk trade on their own supply cycles and barely co-move with anything;
    grains and energy move together. That spread is what distinguishes crowded-and-liquid
    from crowded-and-illiquid, and it is a real feature of this universe rather than an
    artifact of the estimator.
    """
    from crowdmon.futures import commonality_betas

    betas = commonality_betas(panel)
    assert len(betas) >= 15

    low = {s for s in ("DC", "HE", "LE") if s in betas.index}
    high = {s for s in ("ZW", "KE", "CL", "ZC", "SI") if s in betas.index}
    assert low and high, "need both ends present to make the comparison"
    assert betas[list(low)].max() < 0.35, (
        f"livestock and milk no longer exit independently: {betas[list(low)].to_dict()}")
    assert betas[list(high)].min() > 0.7, (
        f"grains and energy no longer co-move: {betas[list(high)].to_dict()}")
    assert betas.max() - betas.min() > 0.5, "the spread is what carries the information"


def test_beta_bar_is_well_below_one_when_the_market_is_excluded(panel):
    """0.634 measured. If this ever reads ~1.000 exactly, the own-market exclusion has been
    lost somewhere and the number has become an identity rather than a measurement."""
    from crowdmon.futures import commonality_betas

    beta_bar = commonality_betas(panel).mean()
    assert 0.3 < beta_bar < 0.9, f"beta_bar={beta_bar:.4f}"
    assert abs(beta_bar - 1.0) > 0.05, (
        "beta_bar is suspiciously close to the algebraic identity value; check that the own "
        "market is still being excluded from the basket")


def test_including_the_own_market_reproduces_the_identity_on_real_data(panel):
    """The identity is not a synthetic curiosity. On the real panel the literal reading of
    §A.6 returns 0.9999, and inflates Class III Milk from 0.070 to 0.849, a factor of 12."""
    from crowdmon.futures import commonality_betas

    with_own = commonality_betas(panel, exclude_own=False)
    assert with_own.mean() == pytest.approx(1.0, abs=0.01)

    without = commonality_betas(panel)
    if "DC" in with_own.index and "DC" in without.index:
        assert with_own["DC"] / without["DC"] > 5, (
            "the thinnest, least co-moving market should be the most inflated by including "
            "itself in its own basket")


def test_rolling_beta_bar_moves_but_stays_in_a_narrow_band(panel):
    """The only form that can reach the composite, and the reason its effect is small.

    Measured 0.423 to 0.780 over 2016-2026, so `1 + 0.5.beta_bar` spans 1.211 to 1.390: a
    1.15x modulation against a `T` that itself ranges over 13x.
    """
    from crowdmon.futures import rolling_betas

    beta_bar = rolling_betas(panel).mean(axis=1).dropna()
    assert len(beta_bar) > 500
    assert beta_bar.std() > 0.01, "a rolling beta that never moves adds nothing at all"
    multiplier = 1 + 0.5 * beta_bar
    assert multiplier.max() / multiplier.min() < 2.0, (
        f"the T_eff multiplier now spans {multiplier.max() / multiplier.min():.2f}x; it "
        f"measured 1.15x, and the claim that this is a small correction rests on it")


def test_the_composite_would_be_unchanged_by_a_constant_beta_on_real_durations(panel):
    """End to end on the real panel: `pct(T_eff)` equals `pct(T)` exactly, so wiring this
    into `composite.py` with a constant `beta_bar` would be a no-op with a changelog entry."""
    from crowdmon.core.aggregate import rolling_percentile
    from crowdmon.futures import commonality_betas, t_effective

    beta_bar = commonality_betas(panel).mean()
    # Any positive duration series will do; the claim is about the transform, not the data.
    durations = panel.iloc[:, 0].rename("t").dropna()
    base = rolling_percentile(durations, window="1095D", min_periods=104)
    scaled = rolling_percentile(t_effective(durations, beta_bar, gamma=0.5),
                                window="1095D", min_periods=104)
    both = base.to_frame("a").join(scaled.rename("b")).dropna()
    assert len(both) > 100
    assert (both["a"] - both["b"]).abs().max() == 0.0
