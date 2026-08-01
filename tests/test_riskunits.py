"""Risk units: notional x volatility, and the two price series it refuses.

Offline. `cotdata.get_prices` is patched so the arithmetic is checkable by eye; the claims
about real price series are asserted in `test_riskunits_live.py`.
"""
import numpy as np
import pandas as pd
import pytest

DATES = pd.bdate_range("2026-01-01", "2026-07-31")


def _bars(closes, index=DATES):
    return pd.DataFrame({"Open": closes, "High": closes, "Low": closes, "Close": closes,
                         "Volume": [1.0] * len(closes)},
                        index=pd.DatetimeIndex(index, name="Date"))


@pytest.fixture()
def prices(monkeypatch):
    """GC alternating +/-1% daily, so daily sigma is a known 1% and notional stays near 100.

    A deterministic alternating series has an exact standard deviation, which lets the risk
    arithmetic be checked against a closed form rather than a recorded number.
    """
    import cotdata

    n = len(DATES)
    # 100, 101, 99.99, ... : strictly positive, |return| == 1% every day after the first.
    closes = [100.0]
    for i in range(1, n):
        closes.append(closes[-1] * (1.01 if i % 2 else 0.99))
    prop = _bars(closes)

    def fake(symbol, adjustment="backadj", **kw):
        if symbol != "GC":
            return pd.DataFrame()
        if adjustment == "propadj":
            return prop
        # Anything else must be visibly different, so an accidental use of the wrong
        # series shows up as a wrong number rather than a coincidence.
        return prop * 3.0

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return prop


def _with_notional(**over):
    """A row as `add_notional` would leave it. Built directly rather than by calling
    add_notional, so a failure here localises to riskunits."""
    row = {
        "report_date": pd.Timestamp("2026-07-21"),
        "release_date": pd.Timestamp("2026-07-24"),
        "market_code": "088691", "report_type": "disaggregated", "combined": False,
        "category": "managed_money", "symbol": "GC", "point_value": 100.0,
        "currency": "USD",
        "net_notional_usd": 6_000_000.0, "long_notional_usd": 10_000_000.0,
        "short_notional_usd": 4_000_000.0, "gross_notional_usd": 15_000_000.0,
        "oi_notional_usd": 50_000_000.0,
    }
    row.update(over)
    return pd.DataFrame([row])


def test_risk_is_notional_times_daily_sigma(prices):
    from crowdmon.futures import add_risk_units

    got = add_risk_units(_with_notional()).iloc[0]
    # Alternating +1%/-1% has a daily sigma very close to 1%.
    assert got.sigma_daily == pytest.approx(0.01, rel=0.02)
    assert got.net_risk_usd == pytest.approx(6_000_000.0 * got.sigma_daily)
    assert got.long_risk_usd == pytest.approx(10_000_000.0 * got.sigma_daily)
    assert got.short_risk_usd == pytest.approx(4_000_000.0 * got.sigma_daily)
    assert got.gross_risk_usd == pytest.approx(15_000_000.0 * got.sigma_daily)
    assert got.oi_risk_usd == pytest.approx(50_000_000.0 * got.sigma_daily)


def test_annualised_sigma_is_the_daily_one_scaled_by_root_252(prices):
    from crowdmon.futures import add_risk_units

    got = add_risk_units(_with_notional()).iloc[0]
    assert got.sigma_annual == pytest.approx(got.sigma_daily * np.sqrt(252))


def test_a_back_adjusted_series_is_refused_outright(prices):
    """The guard this module exists for. Back-adjusted percent returns inflate soybean vol
    by 201x, and UNDERSTATE gold by half while never going negative, so no implausibility
    screen catches the second case."""
    from crowdmon.futures import RiskUnitsError, add_risk_units

    with pytest.raises(RiskUnitsError, match="201x"):
        add_risk_units(_with_notional(), adjustment="backadj")


def test_an_unadjusted_series_is_refused_outright(prices):
    """Unadjusted returns carry a fabricated jump at every roll: crude's worst is a 130.7%
    move that never happened. Full-sample vol barely notices, which is what makes it
    dangerous for the short windows this module uses."""
    from crowdmon.futures import RiskUnitsError, add_risk_units

    with pytest.raises(RiskUnitsError, match="130.7"):
        add_risk_units(_with_notional(), adjustment="unadj")


def test_the_sign_of_risk_follows_the_sign_of_notional(prices):
    """sigma is non-negative, so net_risk is DIRECTIONAL daily dollars at risk. That is what
    keeps a forced-seller and a forced-buyer separable downstream."""
    from crowdmon.futures import add_risk_units

    short_book = add_risk_units(_with_notional(net_notional_usd=-6_000_000.0)).iloc[0]
    assert short_book.net_risk_usd < 0
    assert short_book.gross_risk_usd > 0        # gross is unsigned on both legs


def test_a_negative_notional_from_a_negative_price_still_produces_risk(prices):
    """WTI settled at -37.63 on 2020-04-20 and a long genuinely had negative notional.
    Nothing here may clip or reject it: sigma is a property of returns, not of the level."""
    from crowdmon.futures import add_risk_units

    got = add_risk_units(_with_notional(net_notional_usd=-1_000_000.0,
                                        long_notional_usd=-1_000_000.0)).iloc[0]
    assert got.net_risk_usd < 0 and not pd.isna(got.net_risk_usd)


def test_a_short_history_yields_null_sigma_not_a_sigma_from_three_points(prices):
    """min_periods is a refusal, not a preference. A sigma from a handful of observations
    would feed straight into a cross-market ranking looking exactly like a real one."""
    from crowdmon.futures import add_risk_units

    early = _with_notional(report_date=pd.Timestamp("2026-01-05"))   # only days into series
    got = add_risk_units(early).iloc[0]
    assert pd.isna(got.sigma_daily) and pd.isna(got.net_risk_usd)


def test_min_periods_greater_than_window_is_refused(prices):
    from crowdmon.futures import RiskUnitsError, add_risk_units

    with pytest.raises(RiskUnitsError, match="never be satisfied"):
        add_risk_units(_with_notional(), window=20, min_periods=40)


def test_a_stale_sigma_beyond_the_bound_gives_null_not_a_stale_number(prices):
    from crowdmon.futures import add_risk_units

    far = _with_notional(report_date=pd.Timestamp("2026-12-15"))     # long past the series
    got = add_risk_units(far).iloc[0]
    assert pd.isna(got.sigma_daily) and pd.isna(got.net_risk_usd)


def test_staleness_is_reported_rather_than_assumed(prices):
    from crowdmon.futures import add_risk_units

    got = add_risk_units(_with_notional(report_date=pd.Timestamp("2026-07-26"))).iloc[0]
    assert got.sigma_date == pd.Timestamp("2026-07-24")     # the preceding Friday
    assert got.sigma_staleness_days == 2


def test_rows_without_notional_keep_their_place_with_null_risk(prices):
    """Same rule as every other module in this layer: never silently shorten a panel."""
    from crowdmon.futures import add_risk_units, risk_coverage_report

    frame = pd.concat([_with_notional(),
                       _with_notional(net_notional_usd=float("nan"),
                                      long_notional_usd=float("nan"),
                                      short_notional_usd=float("nan"),
                                      gross_notional_usd=float("nan"))],
                      ignore_index=True)
    got = add_risk_units(frame)
    assert len(got) == 2
    rep = risk_coverage_report(got)
    assert rep["with_risk_units"] == 1 and rep["no_notional"] == 1 and rep["total"] == 2


def test_a_symbol_with_no_price_series_is_reported_not_dropped(prices):
    from crowdmon.futures import add_risk_units, risk_coverage_report

    got = add_risk_units(_with_notional(symbol="NOPRICE"))
    assert len(got) == 1 and pd.isna(got["net_risk_usd"].iloc[0])
    assert risk_coverage_report(got)["no_volatility"] == 1


def test_a_single_negative_close_masks_its_returns_and_keeps_the_market(monkeypatch):
    """WTI settled at -37.63 on 2020-04-20, so a ratio-adjusted series CAN be negative:
    scaling by a positive factor preserves the underlying sign. An earlier version of this
    module raised on any non-positive close and so refused to compute crude's volatility at
    all, over one real day in 2020. Only the returns touching it are undefined."""
    import cotdata

    from crowdmon.futures import add_risk_units

    closes = [100.0] * len(DATES)
    closes[10] = -5.0                                    # one real negative settlement
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(closes))
    got = add_risk_units(_with_notional()).iloc[0]
    assert not pd.isna(got.sigma_daily), "one negative day must not discard the market"


def test_a_mostly_negative_series_raises_because_it_is_the_wrong_one(monkeypatch):
    """The separation is rate, not presence. Across the real store propadj has exactly one
    non-positive close anywhere (0.009% of crude) while backadj runs 52.3% for soybeans, so
    anything above 1% is a series that is not what it claims to be."""
    import cotdata

    from crowdmon.futures import RiskUnitsError, add_risk_units

    closes = [100.0 - i for i in range(len(DATES))]      # crosses zero partway through
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(closes))
    with pytest.raises(RiskUnitsError, match="non-positive"):
        add_risk_units(_with_notional())


def test_missing_prerequisite_columns_name_the_step_that_provides_them(prices):
    from crowdmon.futures import RiskUnitsError, add_risk_units

    with pytest.raises(RiskUnitsError, match="add_notional"):
        add_risk_units(_with_notional().drop(columns=["net_notional_usd"]))


def test_an_empty_frame_still_gains_the_risk_columns(prices):
    from crowdmon.futures import RISK_COLUMNS, add_risk_units

    got = add_risk_units(_with_notional().iloc[0:0])
    assert all(c in got.columns for c in RISK_COLUMNS)


def test_a_wider_window_gives_a_smoother_sigma(prices):
    """Not a tautology worth skipping: it confirms `window` is actually threaded through to
    the rolling call rather than silently defaulted."""
    from crowdmon.futures import add_risk_units

    rows = pd.concat([_with_notional(report_date=d)
                      for d in pd.bdate_range("2026-05-01", "2026-07-31")],
                     ignore_index=True)
    narrow = add_risk_units(rows, window=21, min_periods=15)["sigma_daily"]
    wide = add_risk_units(rows, window=63, min_periods=42)["sigma_daily"]
    assert narrow.std() >= wide.std()
