"""Triggers against a REAL store. Skips when there is not one.

The offline tests pin the arithmetic. These check the claim that made this module possible:
that §A.7 is computable without an aggregate-capital estimate, and that the price series it
insists on is the one the measurement says it needs.
"""
import numpy as np
import pytest

pytestmark = pytest.mark.needs_vintage


@pytest.fixture(scope="module")
def cotdata_store():
    cotdata = pytest.importorskip("cotdata")
    try:
        if cotdata.get_prices("GC", adjustment="unadj").empty:
            pytest.skip("store has no GC prices")
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    return cotdata


@pytest.fixture(scope="module")
def scored(cotdata_store):
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import ContractMaster, VintageCotSource, add_triggers, add_volume

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel[(panel["report_date"] == panel["report_date"].max())
                  & (panel["category"] == "managed_money")].dropna(subset=["symbol"])
    return add_volume(add_triggers(panel))


def test_propadj_is_anchored_so_the_trigger_is_already_tradeable(cotdata_store):
    """`F*` is a price level a reader compares against a screen. `propadj` anchors its most
    recent segment to actual prices, so no conversion back to `unadj` is needed."""
    for symbol in ("GC", "CL", "ZS", "NG"):
        unadj = cotdata_store.get_prices(symbol, adjustment="unadj")["Close"].dropna()
        prop = cotdata_store.get_prices(symbol, adjustment="propadj")["Close"].dropna()
        shared = unadj.index.intersection(prop.index)
        assert prop.loc[shared].iloc[-1] == pytest.approx(unadj.loc[shared].iloc[-1], rel=1e-6)


def test_the_signal_sign_barely_cares_which_series_but_the_distance_does(cotdata_store):
    """Why the guard is about the DISTANCE and not the sign.

    Signal sign agrees 99.4% between back- and ratio-adjusted series, so a module that only
    needed a direction could use either. The trigger's useful output is "how far below spot",
    a ratio of levels, and additive back-adjustment inflates historical levels: the two
    disagree by hundreds of percentage points at 250 days.
    """
    agreements, gaps = [], []
    for symbol in ("GC", "CL", "ZS", "ZW", "CC", "NG"):
        back = cotdata_store.get_prices(symbol, adjustment="backadj")["Close"].dropna()
        prop = cotdata_store.get_prices(symbol, adjustment="propadj")["Close"].dropna()
        shared = back.index.intersection(prop.index)
        back, prop = back.loc[shared], prop.loc[shared]
        for k in (20, 60, 250):
            sign_back = np.sign(back - back.shift(k)).dropna()
            sign_prop = np.sign(prop - prop.shift(k)).dropna()
            both = sign_back.index.intersection(sign_prop.index)
            agreements.append((sign_back.loc[both] == sign_prop.loc[both]).mean())
            dist_back = (back.shift(k) / back - 1).dropna()
            dist_prop = (prop.shift(k) / prop - 1).dropna()
            shared_d = dist_back.index.intersection(dist_prop.index)
            gaps.append(float((dist_back.loc[shared_d]
                               - dist_prop.loc[shared_d]).abs().quantile(0.95)))

    assert min(agreements) > 0.95, f"sign agreement fell to {min(agreements):.4f}"
    assert max(gaps) > 0.5, (
        f"back- and ratio-adjusted trigger distances now agree to within "
        f"{max(gaps):.1%}; the guard in triggers.py rests on them not doing so")


def test_every_market_gets_a_trigger_with_no_capital_estimate(scored):
    """The claim that unblocked §A.7. Nothing below consulted an aggregate CTA capital
    figure, a target volatility, a portfolio scaling term or an external index."""
    live = scored.dropna(subset=["trigger_blend"])
    assert len(live) >= 20
    assert live["spot"].gt(0).all()
    assert live["signal"].between(-1, 1).all()
    # The signal is an unweighted mean of three signs, so it takes only these values.
    allowed = np.array([-1.0, -1 / 3, 0.0, 1 / 3, 1.0])
    assert np.isclose(live["signal"].to_numpy()[:, None], allowed).any(axis=1).all(), (
        f"unexpected signal values: {sorted(live['signal'].unique())}")


def test_the_trigger_sits_on_the_correct_side_of_spot_on_real_data(scored):
    """The consistency invariant, on the real panel rather than a random walk. A long signal
    means spot is above the median lookback price and so the trigger is below it."""
    live = scored.dropna(subset=["trigger_blend", "signal"])
    live = live[live["signal"] != 0]
    assert len(live) >= 15
    side = np.sign(live["spot"] - live["trigger_blend"])
    assert (side == np.sign(live["signal"])).all(), (
        live.loc[side != np.sign(live["signal"]),
                 ["symbol", "spot", "trigger_blend", "signal"]].to_string())


def test_trigger_distances_are_plausible(scored):
    """A trend trigger sits within a normal range of spot. A trigger 90% away means the
    lookback window is reading a different contract or the series has a hole."""
    live = scored.dropna(subset=["trigger_blend_pct"])
    assert live["trigger_blend_pct"].abs().max() < 80, (
        f"widest trigger is {live['trigger_blend_pct'].abs().max():.0f}% from spot")
    assert live["trigger_blend_pct"].abs().median() < 25


def test_the_volatility_trigger_is_half_the_book_at_a_doubling(scored):
    """Unit elasticity on real positions: whatever Managed Money holds, a doubling of
    volatility forces exactly half of it, with no reference to price."""
    live = scored.dropna(subset=["vol_double_flow"])
    assert len(live) >= 20
    assert np.allclose(live["vol_double_flow"].to_numpy(),
                       live["net_contracts"].abs().to_numpy() * 0.5)


def test_the_full_block_renders_for_every_priced_market(scored):
    from crowdmon.futures import trigger_block

    live = scored.dropna(subset=["trigger_blend", "adv", "sigma_daily"])
    assert len(live) >= 20
    for _, row in live.iterrows():
        text = trigger_block(row)
        assert "forced supply on flip" in text and "est. impact" in text
        assert "upper bounds" in text
        assert "nan" not in text.lower(), f"unrendered value for {row['symbol']}:\n{text}"
