"""Volume: the denominator of `T = Q/(kappa V)`, and the two ways to get it wrong.

Offline. `cotdata.get_prices` is patched so every aggregate is checkable by eye; the claims
about the real store are in `test_volume_live.py`.
"""
import numpy as np
import pandas as pd
import pytest

DATES = pd.bdate_range("2024-01-01", "2026-07-31")


def _bars(volume, closes=None):
    n = len(DATES)
    closes = closes if closes is not None else [100.0] * n
    return pd.DataFrame({"Open": closes, "High": closes, "Low": closes, "Close": closes,
                         "Volume": volume, "Open Interest": [50_000.0] * n},
                        index=pd.DatetimeIndex(DATES, name="Date"))


@pytest.fixture()
def prices(monkeypatch):
    """GC at a flat 1,000 contracts/day, so any average is exactly 1,000."""
    import cotdata

    def fake(symbol, adjustment="backadj", volume="front", **kw):
        if symbol != "GC":
            return pd.DataFrame()
        # The subset series is half the whole-market one, so using it shows up as an exact
        # 2x in T rather than a plausible drift.
        v = [1_000.0] * len(DATES) if volume == "front" else [500.0] * len(DATES)
        return _bars(v)

    monkeypatch.setattr(cotdata, "get_prices", fake)


def _frame(**over):
    row = {"report_date": pd.Timestamp("2026-07-21"), "symbol": "GC",
           "market_code": "088691", "q_sell": 40_000.0, "q_buy": 5_000.0,
           "open_interest": 50_000.0}
    row.update(over)
    return pd.DataFrame([row])


def test_adv_is_the_trailing_mean_of_whole_market_volume(prices):
    from crowdmon.futures import add_volume

    got = add_volume(_frame()).iloc[0]
    assert got.adv == pytest.approx(1_000.0)
    assert got.volume_date == pd.Timestamp("2026-07-21")
    assert got.volume_staleness_days == 0


def test_the_subset_volume_series_is_refused(prices):
    """`reconstructed` is FirstVolume + SecondVolume, a strict subset, despite being
    documented as "true market volume". It is 0.52 of total in natural gas and 0.54 in
    crude, so it would roughly double T in the deepest-curve markets."""
    from crowdmon.futures import VolumeError, add_volume

    with pytest.raises(VolumeError, match="whole-market"):
        add_volume(_frame(), series="reconstructed")


def test_zero_volume_is_treated_as_missing_not_as_a_quiet_day(monkeypatch):
    """Norgate publishes volume and open interest a day behind the price bar, so the most
    recent row carries 0 rather than null. Left in place a zero drags the average down and
    makes T look shorter than it is."""
    import cotdata

    from crowdmon.futures import add_volume

    v = [1_000.0] * len(DATES)
    v[-1] = 0.0
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(v))
    got = add_volume(_frame()).iloc[0]
    assert got.adv == pytest.approx(1_000.0)          # not 1000*(n-1)/n


def test_adv_uses_no_data_after_the_as_of_date(monkeypatch):
    """Point-in-time, the same discipline the adapter enforces on release dates. A volume
    average that reaches past the report date would be a lookahead in the denominator of the
    headline number, which is the least visible place to put one."""
    import cotdata

    from crowdmon.futures import add_volume

    # Volume is 1,000 up to the report date and then explodes. If the join reached forward,
    # the average would move.
    v = [1_000.0 if d <= pd.Timestamp("2026-07-21") else 500_000.0 for d in DATES]
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(v))
    got = add_volume(_frame()).iloc[0]
    assert got.adv == pytest.approx(1_000.0)


def test_stress_volume_is_the_median_on_the_worst_return_decile(monkeypatch):
    """§A.5's `V_stress`. Constructed so the answer is known: the worst 10% of days trade
    exactly 200 contracts and everything else trades 1,000."""
    import cotdata

    from crowdmon.futures import add_volume

    n = len(DATES)
    rng = np.random.default_rng(0)
    r = rng.normal(0, 0.01, n)
    bad = np.argsort(r)[: n // 10]                     # the worst decile by return
    closes = 100.0 * np.exp(np.cumsum(r))
    v = np.full(n, 1_000.0)
    v[bad] = 200.0
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(list(v), list(closes)))
    got = add_volume(_frame()).iloc[0]
    assert got.adv_stress == pytest.approx(200.0)
    assert got.adv > got.adv_stress


def test_stress_volume_may_exceed_calm_volume(monkeypatch):
    """Not a symmetric case for completeness: it is what real data does. 9 of 25 markets
    trade MORE under stress (lumber 1.62x, copper 1.35x), so nothing may assume `T_stress` is
    the conservative figure."""
    import cotdata

    from crowdmon.futures import add_volume

    n = len(DATES)
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, n)
    bad = np.argsort(r)[: n // 10]
    closes = 100.0 * np.exp(np.cumsum(r))
    v = np.full(n, 1_000.0)
    v[bad] = 5_000.0                                   # panic brings volume, as it often does
    monkeypatch.setattr(cotdata, "get_prices", lambda *a, **k: _bars(list(v), list(closes)))
    got = add_volume(_frame()).iloc[0]
    assert got.adv_stress > got.adv


def test_days_to_liquidate_is_q_over_kappa_v(prices):
    from crowdmon.futures import add_volume, rank_markets

    frag = add_volume(_frame())
    out = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"]).iloc[0]
    assert out.dtl_sell == pytest.approx(40_000.0 / (0.2 * 1_000.0))     # 200 days
    assert out.dtl_buy == pytest.approx(5_000.0 / (0.2 * 1_000.0))       # 25 days


def test_without_a_volume_the_duration_columns_are_null_not_absent(prices):
    """A caller who forgets to pass a volume gets nulls, so `.sort_values("dtl_sell")` fails
    loudly rather than silently ranking on something else."""
    from crowdmon.futures import rank_markets

    out = rank_markets(_frame())
    assert "dtl_sell" in out.columns and "dtl_sell_stress" in out.columns
    assert out["dtl_sell"].isna().all() and out["dtl_sell_stress"].isna().all()


def test_a_symbol_with_no_volume_history_is_reported_not_dropped(prices):
    from crowdmon.futures import add_volume, volume_coverage

    frame = pd.concat([_frame(), _frame(symbol="NOPRICE")], ignore_index=True)
    got = add_volume(frame)
    assert len(got) == 2
    cov = volume_coverage(got)
    assert cov["with_volume"] == 1 and cov["no_volume_within_tolerance"] == 1
    assert cov["total"] == 2


def test_rows_with_no_symbol_are_counted_separately(prices):
    """The 254 ICE power and gas markets have no Norgate symbol at all, which is a different
    problem from a symbol whose volume series is short, and gets its own count."""
    from crowdmon.futures import add_volume, volume_coverage

    got = add_volume(pd.concat([_frame(), _frame(symbol=None)], ignore_index=True))
    assert volume_coverage(got)["no_symbol"] == 1


def test_a_stale_volume_beyond_the_bound_gives_null(prices):
    from crowdmon.futures import add_volume

    got = add_volume(_frame(report_date=pd.Timestamp("2026-12-15"))).iloc[0]
    assert pd.isna(got.adv)


def test_missing_prerequisite_columns_name_the_step_that_provides_them(prices):
    from crowdmon.futures import VolumeError, add_volume

    with pytest.raises(VolumeError, match="ContractMaster.annotate"):
        add_volume(_frame().drop(columns=["symbol"]))


def test_an_empty_frame_still_gains_the_volume_columns(prices):
    from crowdmon.futures import VOLUME_COLUMNS, add_volume

    got = add_volume(_frame().iloc[0:0])
    assert all(c in got.columns for c in VOLUME_COLUMNS)
