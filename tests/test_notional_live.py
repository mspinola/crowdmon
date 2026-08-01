"""Notional against a REAL store. Skips when there is not one.

The synthetic tests check the arithmetic. These check the thing the arithmetic depends on:
that the back-adjusted series really is unusable for a price LEVEL, and that the error has
the shape which makes it dangerous rather than merely wrong.
"""
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


def test_the_backadjusted_error_is_zero_today_and_enormous_in_history(cotdata_store):
    """The whole reason `add_notional` refuses back-adjusted input.

    If the error were merely large, a spot check would find it. It is EXACTLY ZERO at the
    present date, because back-adjustment anchors on the most recent contract, and grows
    monotonically backwards. So every check anyone would actually run passes perfectly
    while the entire evaluation history is corrupted.
    """
    for sym, floor in (("GC", 1.5), ("CL", 1.5), ("ZC", 1.0)):
        b = cotdata_store.get_prices(sym, adjustment="backadj")["Close"]
        u = cotdata_store.get_prices(sym, adjustment="unadj")["Close"]
        joined = pd.concat([b.rename("b"), u.rename("u")], axis=1).dropna()
        assert len(joined) > 1000, f"{sym}: too little overlap to judge"

        err = (joined["b"] - joined["u"]).abs() / joined["u"]
        assert err.iloc[-1] < 0.001, (
            f"{sym}: back-adjusted and unadjusted disagree at the present date, which "
            f"breaks the anchoring assumption this test rests on")
        early = err.iloc[: len(err) // 3]
        assert early.max() > floor, (
            f"{sym}: expected the historical error to exceed {floor:.0%}, saw "
            f"{early.max():.0%}. If this has genuinely shrunk, re-measure the numbers "
            f"quoted in notional.py before relaxing the guard.")


def test_crude_goes_negative_for_two_completely_different_reasons(cotdata_store):
    """An earlier version of this test asserted the unadjusted series can never be
    negative. That is wrong, and the store says so: WTI settled at **-$37.63 on
    2020-04-20**, and the unadjusted series records it faithfully. A real price.

    The back-adjusted series is negative for an unrelated reason, in a different era:
    additive back-adjustment accumulates roll gaps until the anchored level drifts below
    zero. That one is an artifact of the transformation, not a market event.

    Both matter here. The artifact is why notional refuses back-adjusted input. The real
    negative is why nothing in this module clips or rejects a negative price: on that day a
    LONG position genuinely had negative notional.
    """
    b = cotdata_store.get_prices("CL", adjustment="backadj")["Close"]
    u = cotdata_store.get_prices("CL", adjustment="unadj")["Close"]

    assert b.min() < 0, "CL back-adjusted no longer goes negative; re-check the docs"
    assert u.min() < 0, "CL unadjusted no longer records the 2020 negative settlement"

    trough = u.idxmin()
    assert trough.year == 2020 and trough.month == 4, (
        f"the unadjusted negative should be April 2020, saw {trough.date()}")

    # The counts are what separate the event from the artifact. Crude actually traded
    # below zero on exactly ONE day. The back-adjusted series is below zero on dozens,
    # because the enormous roll gap out of the May 2020 contract is propagated backwards
    # through every earlier bar.
    assert (u < 0).sum() == 1
    assert (b < 0).sum() > 20

    # The cleanest single row in the whole store for why notional refuses back-adjustment:
    # the day AFTER the negative settlement, crude traded at a perfectly ordinary positive
    # price while the back-adjusted series reported a large negative one.
    assert u.loc["2020-04-21"] > 0
    assert b.loc["2020-04-21"] < -20


def test_notional_on_the_real_panel_is_populated_and_plausible(cotdata_store):
    """End to end over the real vintage store: adapter, contract master, notional."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon_futures.ingest import VintageCotSource
    from crowdmon_futures.normalize import ContractMaster, add_notional, coverage_report

    panel = VintageCotSource(report_type="disaggregated").load("2026-07-31")
    if panel.empty:
        pytest.skip("no disaggregated rows for that release")
    got = add_notional(ContractMaster.load().annotate(panel))

    rep = coverage_report(got)
    assert rep["total"] == len(panel)                 # nothing dropped
    assert rep["with_notional"] > 0

    priced = got[got["net_notional_usd"].notna()]
    # Every priced row must have used a same-week price. A larger gap means the as-of
    # lookup reached across a hole rather than across a holiday.
    assert priced["price_staleness_days"].max() <= 5
    assert (priced["currency"] == "USD").all()

    # Managed Money in gold is a multi-billion-dollar book. A result off by orders of
    # magnitude (a missing multiplier, a percentage-quoted price) fails this.
    gold = priced[(priced["symbol"] == "GC") & (priced["category"] == "managed_money")]
    if not gold.empty:
        net = gold.sort_values("report_date")["net_notional_usd"].iloc[-1]
        assert 1e9 < abs(net) < 1e12, f"gold managed money net notional implausible: {net:,.0f}"


def test_the_report_date_price_differs_from_the_release_date_price(cotdata_store):
    """Confirms the choice is not cosmetic: three days of price movement separate them,
    which is exactly the window the release lag covers."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon_futures.ingest import VintageCotSource
    from crowdmon_futures.normalize import ContractMaster, add_notional

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    on_report = add_notional(panel)["net_notional_usd"]
    on_release = add_notional(panel, price_on="release_date")["net_notional_usd"]
    both = on_report.notna() & on_release.notna()
    assert both.any()
    assert not on_report[both].equals(on_release[both])
