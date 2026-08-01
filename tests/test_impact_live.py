"""Exit cost against a REAL store. Skips when there is not one.

The offline tests check the formulas. These check the two claims that justify the module
existing at all: that cost is not duration, and that the contract multiplier reorders Amihud
rather than merely rescaling it.
"""
import numpy as np
import pandas as pd
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
    """The latest week, all the way through the layer."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_impact,
        add_volume,
        fragility_frame,
        rank_markets,
    )

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel[panel["report_date"] == panel["report_date"].max()]
    spec = panel[["market_code", "symbol", "point_value"]].drop_duplicates("market_code")
    frag = add_volume(fragility_frame(panel).merge(spec, on="market_code", how="left"))
    frag = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"])
    return add_impact(frag)


def test_exit_cost_is_not_exit_duration(scored):
    """The claim the module rests on, and it is stronger than expected.

    `T` and the square-root impact rank markets almost INDEPENDENTLY, because `T` carries no
    volatility and the cost is multiplicative in it. Cotton has the longest days-to-liquidate
    and ranks fourth on cost; cocoa exits in a day and a half and costs the third most. If
    these ranked together, reporting both would be redundant.
    """
    live = scored.dropna(subset=["impact_sell", "dtl_sell"])
    assert len(live) >= 20
    corr = live["dtl_sell"].rank(ascending=False).corr(
        live["impact_sell"].rank(ascending=False))
    assert abs(corr) < 0.5, (
        f"days-to-liquidate and exit cost now rank markets together (corr={corr:.3f}). "
        f"They measured 0.031 when written. If this has genuinely converged, the argument "
        f"for reporting both needs restating.")


def test_the_multiplier_reorders_amihud_rather_than_rescaling_it(cotdata_store, scored):
    """Why `amihud_series` refuses a frame with no `point_value`.

    Multipliers span four orders of magnitude across this universe (cocoa 10, RBOB 42,000),
    so dropping them is not a constant factor: it is a different ranking. Measured at rank
    correlation 0.500, with 8 of 25 markets moving more than five places.
    """
    from crowdmon.futures.impact import _dollar_volume

    rows = []
    for _, r in scored.dropna(subset=["symbol", "point_value"]).drop_duplicates(
            "symbol").iterrows():
        sym, pv = r["symbol"], float(r["point_value"])
        px = cotdata_store.get_prices(sym, adjustment="propadj")["Close"].dropna()
        nonpos = px <= 0
        ret = px.pct_change().replace([np.inf, -np.inf], np.nan) \
                .where(~(nonpos | nonpos.shift(fill_value=False)))
        correct = _dollar_volume(sym, pv)
        without = _dollar_volume(sym, 1.0)              # the multiplier dropped
        if correct.empty:
            continue
        a_ok = (ret.abs() / correct.reindex(ret.index)).tail(252).mean()
        a_no = (ret.abs() / without.reindex(ret.index)).tail(252).mean()
        rows.append({"symbol": sym, "pv": pv, "correct": a_ok, "without": a_no})

    df = pd.DataFrame(rows).dropna()
    assert len(df) >= 20
    assert df["pv"].max() / df["pv"].min() > 100, (
        "multipliers no longer span orders of magnitude; the argument rests on that")
    corr = df["correct"].rank(ascending=False).corr(df["without"].rank(ascending=False))
    assert corr < 0.9, (
        f"dropping the multiplier no longer reorders Amihud (corr={corr:.3f}); it measured "
        f"0.500. Re-measure the numbers in impact.py before relaxing the guard.")


def test_impact_on_the_real_panel_is_populated_and_plausible(scored):
    from crowdmon.futures import impact_coverage

    cov = impact_coverage(scored)
    assert cov["total"] == len(scored)                       # nothing dropped
    assert cov["with_impact"] >= 20
    assert cov["no_volatility"] == 0 and cov["no_volume"] == 0

    live = scored.dropna(subset=["impact_sell"])
    # Liquidating a large forced position costs tens to hundreds of basis points. Outside
    # that band the inputs are wrong: a percentage-quoted sigma, or Q and V in different
    # units, both of which land far outside it.
    assert live["impact_sell_bps"].between(5, 2_000).all(), (
        f"implausible exit cost: {live['impact_sell_bps'].min():.0f} to "
        f"{live['impact_sell_bps'].max():.0f} bps")
    assert (live["impact_sell"] > live["impact_buy"]).sum() > 0
    assert (live["adv_usd"] > 1e6).all(), "a futures market trading under $1m/day is suspect"


def test_amihud_orders_the_universe_the_way_dollar_volume_does(scored):
    """A sanity check on the sign and the shape: thin markets are illiquid.

    Not circular. Amihud is |return| per dollar traded, so a market could in principle be
    thin and calm, or deep and jumpy. That the two agree strongly is a property of this
    universe rather than of the formula, and it is what makes the outliers worth looking at.
    """
    live = scored.dropna(subset=["amihud", "adv_usd"]).drop_duplicates("symbol")
    assert len(live) >= 20
    corr = live["amihud"].rank(ascending=False).corr(live["adv_usd"].rank())
    assert corr > 0.5, f"Amihud no longer tracks thinness (corr={corr:.3f})"
    # Orange juice is the thinnest market that joins, and the most illiquid on this measure.
    top = live.nlargest(1, "amihud")["symbol"].iloc[0]
    assert top in {"OJ", "LBR", "DC"}, f"most-illiquid market is now {top}; re-check the docs"
