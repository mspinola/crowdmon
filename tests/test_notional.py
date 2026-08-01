"""Notional: contracts to USD, and the price series it refuses to use.

Offline. `cotdata.get_prices` is patched so the arithmetic is checked against known
numbers; the real-data behaviour is asserted in `test_notional_live.py`.
"""
import pandas as pd
import pytest


def _bars(dates, closes):
    return pd.DataFrame({"Open": closes, "High": closes, "Low": closes, "Close": closes,
                         "Volume": [1.0] * len(closes)},
                        index=pd.DatetimeIndex(pd.to_datetime(dates), name="Date"))


@pytest.fixture()
def prices(monkeypatch):
    """GC at a round 100.0 through July, so notional arithmetic is checkable by eye."""
    import cotdata
    series = {"GC": _bars(pd.bdate_range("2026-07-01", "2026-07-31"),
                          [100.0] * len(pd.bdate_range("2026-07-01", "2026-07-31")))}

    def fake(symbol, adjustment="backadj", **kw):
        got = series.get(symbol, pd.DataFrame())
        if adjustment != "unadj" and not got.empty:
            # A back-adjusted series would differ. Doubling it makes any accidental use
            # of the wrong adjustment show up as an exact 2x rather than a subtle drift.
            got = got * 2
        return got

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return series


def _annotated(**over):
    row = {
        "report_date": pd.Timestamp("2026-07-21"),
        "release_date": pd.Timestamp("2026-07-24"),
        "market_code": "088691", "report_type": "disaggregated", "combined": False,
        "category": "managed_money", "symbol": "GC", "point_value": 100.0,
        "long_contracts": 1000.0, "short_contracts": 400.0, "spread_contracts": 50.0,
        "open_interest": 5000.0, "currency": "USD",
    }
    row.update(over)
    return pd.DataFrame([row])


def test_net_notional_is_contracts_times_multiplier_times_price(prices):
    from crowdmon.futures import add_notional
    got = add_notional(_annotated()).iloc[0]
    assert got.price == 100.0
    assert got.net_contracts == 600.0                    # 1000 long - 400 short
    assert got.net_notional_usd == 600.0 * 100.0 * 100.0     # 6,000,000
    assert got.long_notional_usd == 1000.0 * 100.0 * 100.0
    assert got.short_notional_usd == 400.0 * 100.0 * 100.0
    assert got.oi_notional_usd == 5000.0 * 100.0 * 100.0


def test_spreading_is_excluded_from_net_and_included_in_gross(prices):
    """A spread is a matched long and short held by one trader, so it cancels
    directionally but is still real exposure that has to be rolled and margined."""
    from crowdmon.futures import add_notional
    got = add_notional(_annotated()).iloc[0]
    assert got.net_contracts == 600.0                          # spreading absent
    assert got.gross_notional_usd == (1000 + 400 + 2 * 50) * 100.0 * 100.0


def test_a_back_adjusted_series_is_refused_outright(prices):
    """The guard this module exists for. Measured error: +294% for gold in 2002, and
    EXACTLY ZERO today, so no spot check on recent data would ever catch it."""
    from crowdmon.futures import NotionalError, add_notional
    with pytest.raises(NotionalError, match="294"):
        add_notional(_annotated(), adjustment="backadj")
    with pytest.raises(NotionalError, match="tradeable price LEVELS"):
        add_notional(_annotated(), adjustment="propadj")


def test_the_price_is_taken_as_of_the_report_date_not_the_release_date(prices):
    """The positions were held on the Tuesday, so that is what values them. Using the
    Friday price silently turns notional into a three-day mark-to-market."""
    from crowdmon.futures import add_notional
    assert add_notional(_annotated())["price_date"].iloc[0] == pd.Timestamp("2026-07-21")
    on_release = add_notional(_annotated(), price_on="release_date")
    assert on_release["price_date"].iloc[0] == pd.Timestamp("2026-07-24")


def test_a_holiday_report_date_reaches_back_and_says_how_far(prices):
    """A Tuesday can be a market holiday, so some tolerance is needed. How far it reached
    is reported rather than assumed, because a large value means a hole in the series."""
    from crowdmon.futures import add_notional
    got = add_notional(_annotated(report_date=pd.Timestamp("2026-07-26"))).iloc[0]  # Sunday
    assert got.price_date == pd.Timestamp("2026-07-24")       # the preceding Friday
    assert got.price_staleness_days == 2


def test_a_price_beyond_the_staleness_bound_gives_null_not_a_stale_number(prices):
    """Valuing a position at last month's price is worse than declining to value it."""
    from crowdmon.futures import add_notional
    far = _annotated(report_date=pd.Timestamp("2026-09-15"))   # long past the series
    got = add_notional(far).iloc[0]
    assert pd.isna(got.price) and pd.isna(got.net_notional_usd)


def test_rows_without_a_contract_spec_keep_their_place_with_null_notional(prices):
    """Same rule as the contract master: never silently shorten a panel."""
    from crowdmon.futures import add_notional, coverage_report
    frame = pd.concat([_annotated(),
                       _annotated(symbol=None, point_value=None, market_code="999999")],
                      ignore_index=True)
    got = add_notional(frame)
    assert len(got) == 2
    assert got["net_notional_usd"].notna().sum() == 1
    rep = coverage_report(got)
    assert rep["with_notional"] == 1 and rep["no_contract_spec"] == 1 and rep["total"] == 2


def test_missing_prerequisite_columns_name_the_step_that_provides_them(prices):
    from crowdmon.futures import NotionalError, add_notional
    with pytest.raises(NotionalError, match="ContractMaster.annotate"):
        add_notional(_annotated().drop(columns=["point_value"]))


def test_an_empty_frame_still_gains_the_notional_columns(prices):
    from crowdmon.futures import NOTIONAL_COLUMNS, add_notional
    got = add_notional(_annotated().iloc[0:0])
    assert all(c in got.columns for c in NOTIONAL_COLUMNS)


def test_a_symbol_with_no_price_series_at_all_is_reported_not_dropped(prices):
    from crowdmon.futures import add_notional, coverage_report
    got = add_notional(_annotated(symbol="NOPRICE"))
    assert len(got) == 1 and pd.isna(got["net_notional_usd"].iloc[0])
    assert coverage_report(got)["no_price_within_tolerance"] == 1
