"""Risk units against a REAL store. Skips when there is not one.

The synthetic tests check the arithmetic. These check the thing the arithmetic rests on:
that `propadj` is the only one of the three price series whose returns are percentages, and
that the resulting sigma composes with an unadjusted price into a real dollar quantity.

Every number quoted in `riskunits.py`'s docstring and in its two refusal messages is
reproduced here. If cotdata's adjustment logic ever changes, these fail and the docstring
gets corrected rather than quietly becoming folklore.
"""
import numpy as np
import pytest

pytestmark = pytest.mark.needs_vintage

WINDOW = 63


@pytest.fixture(scope="module")
def cotdata_store():
    cotdata = pytest.importorskip("cotdata")
    try:
        if cotdata.get_prices("GC", adjustment="unadj").empty:
            pytest.skip("store has no GC prices")
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    return cotdata


def _ann_vol(s):
    r = s.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    return r.std() * np.sqrt(252)


def test_backadjusted_percent_returns_are_not_volatility(cotdata_store):
    """The primary guard. Two failure shapes, and the second is the dangerous one.

    Soybeans and the 10-year note go NEGATIVE under additive back-adjustment (52.3% and 8.9%
    of closes), so their percent returns are undefined and the vol is absurd. Gold never
    goes negative, passes every implausibility screen, and is still wrong by a factor of two
    in the UNDERSTATING direction, because accumulated roll gaps inflate historical levels
    and a fixed dollar move against an inflated level is a smaller percentage.
    """
    for sym, floor in (("ZS", 50.0), ("ZN", 50.0)):
        b = cotdata_store.get_prices(sym, adjustment="backadj")["Close"].dropna()
        p = cotdata_store.get_prices(sym, adjustment="propadj")["Close"].dropna()
        assert (b <= 0).any(), f"{sym}: backadj no longer goes negative; re-measure the docs"
        assert _ann_vol(b) / _ann_vol(p) > floor, (
            f"{sym}: backadj vol inflation fell below {floor}x. Re-measure the table in "
            f"riskunits.py before relaxing anything.")

    # Gold: no negatives, no absurdity, still wrong by half. This is the row that makes the
    # guard a refusal rather than a sanity check on the output.
    b = cotdata_store.get_prices("GC", adjustment="backadj")["Close"].dropna()
    p = cotdata_store.get_prices("GC", adjustment="propadj")["Close"].dropna()
    assert (b > 0).all(), "GC backadj went negative; the point of this case was that it does not"
    assert _ann_vol(b) / _ann_vol(p) < 0.6, (
        "GC backadj vol is no longer materially understated; the 'passes every screen and is "
        "still wrong' argument in riskunits.py needs re-measuring")


def test_a_negative_propadj_close_is_a_market_event_not_a_wrong_series(cotdata_store):
    """`propadj` is NOT strictly positive, and this module assumed it was until this test
    said otherwise. Ratio adjustment scales by a positive factor, so it preserves the sign of
    the underlying series: WTI settled at -37.63 on 2020-04-20 and crude's propadj close that
    day is negative too. Refusing crude over that would be absurd.

    What separates the real event from a broken transformation is RATE, and the store leaves
    three orders of magnitude between them with nothing in between. That gap is what the
    1% bound in `MAX_NONPOSITIVE_RATE` sits in.
    """
    p = cotdata_store.get_prices("CL", adjustment="propadj")["Close"].dropna()
    nonpos = p <= 0
    assert nonpos.sum() == 1, (
        f"crude's propadj series has {nonpos.sum()} non-positive closes, expected exactly "
        f"the 2020-04-20 settlement")
    assert p[nonpos].index[0].date().isoformat() == "2020-04-20"
    assert float(nonpos.mean()) < 0.001              # 0.009%, far under the bound

    # The other side of the gap: the series riskunits refuses.
    for sym, floor in (("ZS", 0.40), ("DC", 0.30)):
        b = cotdata_store.get_prices(sym, adjustment="backadj")["Close"].dropna()
        if b.empty:
            continue
        assert float((b <= 0).mean()) > floor, (
            f"{sym}: backadj non-positive rate fell below {floor:.0%}; the separation "
            f"argument in riskunits.py needs re-measuring")


def test_crude_still_gets_a_volatility_despite_its_negative_day(cotdata_store):
    """The regression this module already failed once. Only the returns touching the
    negative close are undefined; the market keeps its sigma everywhere else."""
    from crowdmon.futures import RISK_ADJUSTMENT
    from crowdmon.futures.riskunits import _sigma_series

    sig = _sigma_series("CL", RISK_ADJUSTMENT, "Close", WINDOW, 42).dropna()
    assert len(sig) > 5000, "crude lost most of its volatility history"
    assert (sig > 0).all()
    # The masked window around 2020-04-20 must recover, not leave a permanent hole.
    assert not sig.loc["2020-08-01":"2020-12-31"].empty


def test_unadjusted_returns_carry_a_fabricated_jump_at_every_roll(cotdata_store):
    """The second guard, and it fails in the opposite shape to the first: full-sample vol
    barely notices (GC 1.01x), so a whole-history check would clear it, while any SHORT
    window spanning a roll is badly wrong. Short windows are what this module uses."""
    u = cotdata_store.get_prices("CL", adjustment="unadj")["Close"].dropna()
    p = cotdata_store.get_prices("CL", adjustment="propadj")["Close"].dropna()
    idx = u.index.intersection(p.index)
    u, p = u.loc[idx], p.loc[idx]

    ru = u.pct_change().replace([np.inf, -np.inf], np.nan)
    # Restricted to actual ROLL dates. An unrestricted max would be satisfied by crude's
    # 2020-04-21 move off the negative settlement (306%), which is a real price crossing
    # zero and not a roll artifact, so this test would keep passing even if roll
    # contamination disappeared entirely. That is the claim under test, so pin it to rolls.
    rolls = idx.intersection(cotdata_store.roll_dates("CL"))
    assert len(rolls) > 100, "no roll calendar for crude; the claim cannot be checked"
    assert ru.loc[rolls].abs().max() > 1.0, (
        "crude's worst ROLL day is no longer a >100% fabricated move. The 130.7% figure in "
        "riskunits.py's refusal message needs re-measuring.")

    # Full-sample vol hides it; a 63-day window does not.
    assert _ann_vol(u) / _ann_vol(p) < 1.10, "full-sample inflation was meant to be mild"
    vu = ru.rolling(WINDOW).std()
    vp = p.pct_change().replace([np.inf, -np.inf], np.nan).rolling(WINDOW).std()
    ratio = (vu / vp).replace([np.inf, -np.inf], np.nan).dropna()
    assert ratio.max() > 1.30, (
        "a 63-day window spanning a roll is no longer materially inflated; the argument for "
        "refusing unadj rests on this")


def test_dollar_volatility_agrees_via_two_independent_paths(cotdata_store):
    """The cross-check that the whole layer rests on, and the reason to believe `propadj`
    returns and `unadj` levels compose into a real dollar quantity.

      (a) unadjusted price x sigma_pct(propadj)
      (b) std of ABSOLUTE daily changes in backadj  -- precisely what additive DOES preserve

    Two different series, two different transformations, one answer. Checked mid-history,
    where back-adjustment offsets are large and any error would be obvious.
    """
    for sym in ("GC", "CL", "ZS", "ZN", "ES", "6E"):
        p = cotdata_store.get_prices(sym, adjustment="propadj")["Close"].dropna()
        b = cotdata_store.get_prices(sym, adjustment="backadj")["Close"].dropna()
        u = cotdata_store.get_prices(sym, adjustment="unadj")["Close"].dropna()
        idx = p.index.intersection(b.index).intersection(u.index)
        if len(idx) < 3 * WINDOW:
            pytest.skip(f"{sym}: too little overlap")
        p, b, u = p.loc[idx], b.loc[idx], u.loc[idx]

        via_pct = (u * p.pct_change().replace([np.inf, -np.inf], np.nan)
                   .rolling(WINDOW).std()).dropna()
        via_diff = b.diff().rolling(WINDOW).std().dropna()
        both = via_pct.index.intersection(via_diff.index)
        at = both[len(both) // 3]
        ratio = via_pct.loc[at] / via_diff.loc[at]
        assert 0.85 < ratio < 1.15, (
            f"{sym} on {at.date()}: the two paths to dollar volatility disagree by "
            f"{abs(1 - ratio):.1%}. One of the three adjustments is not what it claims.")


def test_risk_units_on_the_real_panel_are_populated_and_plausible(cotdata_store):
    """End to end over the real vintage store: adapter, contract master, notional, risk."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_notional,
        add_risk_units,
        risk_coverage_report,
    )

    panel = VintageCotSource(report_type="disaggregated").load("2026-07-31")
    if panel.empty:
        pytest.skip("no disaggregated rows for that release")
    got = add_risk_units(add_notional(ContractMaster.load().annotate(panel)))

    rep = risk_coverage_report(got)
    assert rep["total"] == len(panel)                      # nothing dropped
    assert rep["with_risk_units"] > 0

    live = got[got["net_risk_usd"].notna()]
    assert live["sigma_staleness_days"].max() <= 5

    # Daily vol of a futures market sits roughly in 0.4%-8%; the band is set wider than the
    # observed 0.38%-7.94% so it catches an order-of-magnitude error without failing on an
    # ordinary vol regime. Outside it, the returns are not returns: a wrong series, or a
    # window spanning a data hole.
    assert live["sigma_daily"].between(0.002, 0.10).all(), (
        f"implausible daily sigma: {live['sigma_daily'].min():.5f} to "
        f"{live['sigma_daily'].max():.5f}")

    # Risk cannot exceed the notional it scales, since 0 <= sigma < 1. Equality only where
    # the position is empty: oats swap dealers hold exactly zero, so a strict `<` here fails
    # on one row out of 10,365 for a reason that has nothing to do with volatility.
    assert (live["gross_risk_usd"].abs() <= live["gross_notional_usd"].abs()).all()
    held = live[live["gross_notional_usd"] != 0]
    assert (held["gross_risk_usd"].abs() < held["gross_notional_usd"].abs()).all()

    gold = live[(live["symbol"] == "GC") & (live["category"] == "managed_money")]
    if not gold.empty:
        r = gold.sort_values("report_date")["net_risk_usd"].iloc[-1]
        # Gold Managed Money runs tens of billions notional at ~1% daily vol, so hundreds of
        # millions of daily risk. Orders of magnitude off means a broken multiplier.
        assert 1e7 < abs(r) < 1e11, f"gold managed money daily risk implausible: {r:,.0f}"


def test_risk_and_notional_rank_markets_differently(cotdata_store):
    """The reason rung 4 exists at all. If vol-scaling did not reorder the cross-section,
    rung 3 would already be the comparable unit and this module would be decoration."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import ContractMaster, VintageCotSource, add_notional, add_risk_units

    panel = VintageCotSource(report_type="disaggregated").load("2026-07-31")
    got = add_risk_units(add_notional(ContractMaster.load().annotate(panel)))
    mm = got[(got["category"] == "managed_money") & got["net_risk_usd"].notna()]
    if len(mm) < 8:
        pytest.skip("too few priced managed-money rows to rank")

    by_notional = mm.set_index("symbol")["net_notional_usd"].abs().rank(ascending=False)
    by_risk = mm.set_index("symbol")["net_risk_usd"].abs().rank(ascending=False)
    assert not by_notional.equals(by_risk), (
        "vol-scaling left the ranking unchanged, which would make rung 4 redundant")
