"""Extremity: trailing windows, and the lookahead they exist to refuse.

The central test here is `test_a_score_never_changes_when_later_data_arrives`. Everything
else is arithmetic; that one is the property the measure would be worthless without, and it
is the kind of bug that produces beautiful backtests and no error message.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.core.aggregate import (
    AggregateError,
    rolling_percentile,
    rolling_zscore,
    standardise,
    winsorise,
)
from crowdmon.futures import add_extremity, extremity_report
from crowdmon.futures.extremity import ExtremityError


def series(values, start="2020-01-07", freq_days=7) -> pd.Series:
    idx = pd.date_range(start, periods=len(values), freq=f"{freq_days}D")
    return pd.Series(values, index=idx, dtype="float64", name="x")


# ── The property that matters ───────────────────────────────────────────────
def test_a_score_never_changes_when_later_data_arrives():
    """No lookahead, stated as the only test that can actually detect it.

    Score a series, then score a longer version of the same series, and every overlapping
    value must be identical. A centred window, a full-sample mean, or a `.shift(-1)` slipped
    in anywhere breaks this and breaks nothing else: the numbers still look plausible, the
    tests still pass, and every historical result built on it is flattered.
    """
    rng = np.random.default_rng(0)
    full = series(rng.normal(size=400).cumsum() + 100)
    early = full.iloc[:250]

    for fn in (rolling_zscore, rolling_percentile):
        a = fn(early, min_periods=20)
        b = fn(full, min_periods=20).iloc[:250]
        pd.testing.assert_series_equal(a, b)


def test_an_unsorted_index_is_refused_rather_than_silently_reversed():
    """A trailing window over an unsorted index reaches over rows that are actually later.
    pandas does not always complain, so this does."""
    s = series([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(AggregateError, match="lookahead"):
        rolling_zscore(s.iloc[::-1], min_periods=2)


def test_a_time_window_needs_a_datetime_index():
    with pytest.raises(AggregateError, match="DatetimeIndex"):
        rolling_zscore(pd.Series([1.0, 2.0, 3.0]), min_periods=2)


# ── The window is time, not observations ────────────────────────────────────
def test_a_gap_shrinks_the_window_rather_than_reaching_further_back():
    """The reason windows are time-based. Oats vanishes from the COT report for 294 days in
    the real store; an observation-count window would reach back five calendar years to fill
    156 rows there and call the result a three-year score."""
    idx = pd.to_datetime(["2020-01-07", "2020-01-14", "2020-01-21",
                          "2024-06-01", "2024-06-08"])
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx, name="x")
    out = rolling_zscore(s, window="1095D", min_periods=3, winsor=0.0)
    # The 2020 cluster has three observations, so it scores on the third.
    assert pd.notna(out.iloc[2])
    # After the gap only the two 2024 points are inside the trailing three years.
    assert pd.isna(out.iloc[3]) and pd.isna(out.iloc[4])


def test_min_periods_refuses_rather_than_guessing():
    s = series(np.arange(10, dtype="float64"))
    out = rolling_zscore(s, min_periods=5, winsor=0.0)
    assert out.iloc[:4].isna().all()
    assert out.iloc[4:].notna().all()


# ── Arithmetic ──────────────────────────────────────────────────────────────
def test_zscore_matches_the_appendix_formula_by_hand():
    """`z_t = (x_t - mu_W) / s_W`, appendix §A.4, computed independently."""
    s = series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = rolling_zscore(s, min_periods=2, winsor=0.0)
    window = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    expected = (5.0 - window.mean()) / window.std(ddof=1)
    assert out.iloc[-1] == pytest.approx(expected)


def test_a_flat_window_yields_null_not_infinity():
    """Nothing varied, so nothing can be said about whether today is unusual. Dividing by a
    zero standard deviation would put `inf` at the top of every ranking it entered."""
    out = rolling_zscore(series([3.0] * 6), min_periods=3, winsor=0.0)
    assert out.iloc[2:].isna().all()


def test_percentile_is_a_rank_within_the_trailing_window():
    out = rolling_percentile(series([10.0, 20.0, 30.0, 5.0]), min_periods=1)
    assert out.iloc[0] == pytest.approx(1.0)     # only value so far
    assert out.iloc[2] == pytest.approx(1.0)     # largest of three
    assert out.iloc[3] == pytest.approx(0.25)    # smallest of four


def test_percentile_is_bounded():
    """`[0, 1]` by construction, which is what makes it comparable across markets where the
    z-score is not."""
    rng = np.random.default_rng(1)
    out = rolling_percentile(series(rng.normal(size=300)), min_periods=20).dropna()
    assert out.between(0.0, 1.0).all()


# ── Winsorisation is off, and why ───────────────────────────────────────────
def test_winsorise_clips_both_tails_and_keeps_the_count():
    out = winsorise(np.array([1.0, 2, 3, 4, 5, 6, 7, 8, 9, 100.0]), 0.1)
    assert len(out) == 10
    assert out.max() < 100.0
    assert out.min() >= 1.0


def test_winsorising_is_off_by_default_because_it_inflates_a_trend():
    """The measured reason, reproduced on a synthetic version of the platinum case.

    A monotone build ending at the current value is the common shape in positioning data, and
    it is exactly what winsorising mistakes for outliers. Clipping the top removes the build,
    shrinks the scale, and manufactures a much larger score from the same data. Appendix §A.4
    specifies no winsorisation and is authoritative; module spec §6.1's "winsorised" is not.
    """
    from crowdmon.core import aggregate

    assert aggregate.DEFAULT_WINSOR == 0.0

    build = series(np.concatenate([np.full(140, 10.0), np.linspace(11, 60, 17)]))
    plain = rolling_zscore(build, min_periods=20, winsor=0.0).iloc[-1]
    clipped = rolling_zscore(build, min_periods=20, winsor=0.05).iloc[-1]
    # 1.43x here. The real case is worse (platinum Other Reportable, 2026-01-27: z goes from
    # 6.1 to 22.1, a 3.6x inflation) because its build runs for longer and so more of the
    # window's variation sits in the clipped tail. The synthetic understates the effect
    # rather than exaggerating it, which is the right direction for a guard.
    assert clipped > plain * 1.25, "the synthetic case stopped reproducing the effect"


def test_the_percentile_is_immune_to_the_winsor_choice(history_panel):
    """Ranks do not care about the magnitude of the tails, which is why the percentile is the
    headline number and the z is secondary.

    Tested through `add_extremity`, which is where a caller actually sets `winsor`, because
    `rolling_percentile` takes no winsor argument at all and comparing it with itself would
    assert nothing. The point is that the two columns move apart while one stays fixed.
    """
    rng = np.random.default_rng(3)
    panel = history_panel.assign(
        net_risk_usd=rng.normal(size=len(history_panel)).cumsum())
    plain = add_extremity(panel, min_periods=30, winsor=0.0)
    clipped = add_extremity(panel, min_periods=30, winsor=0.10)

    pd.testing.assert_series_equal(plain["net_risk_usd_pct"], clipped["net_risk_usd_pct"])
    assert not plain["net_risk_usd_z"].equals(clipped["net_risk_usd_z"])


def test_an_absurd_winsor_limit_is_refused():
    with pytest.raises(AggregateError, match=r"\[0, 0.5\)"):
        winsorise(np.array([1.0, 2.0]), 0.5)


# ── Grouping ────────────────────────────────────────────────────────────────
def test_standardise_never_pools_two_series():
    """Each market-category is standardised against its own history. Pooling would compare a
    levered fund's book against a hedger's seasonal one and call the difference extremity."""
    rows = []
    for key, level in (("A", 100.0), ("B", 1.0)):
        for i, stamp in enumerate(pd.date_range("2020-01-07", periods=30, freq="7D")):
            rows.append({"market_code": key, "report_type": "disaggregated",
                         "combined": False, "category": "managed_money",
                         "report_date": stamp, "x": level + i})
    frame = pd.DataFrame(rows)
    out = standardise(frame, "x", by=["market_code", "category"], min_periods=5)
    a = out[out["market_code"] == "A"]["x_z"].dropna().to_numpy()
    b = out[out["market_code"] == "B"]["x_z"].dropna().to_numpy()
    # Same shape, wildly different levels: identical scores prove no pooling occurred.
    assert a == pytest.approx(b)


def test_standardise_requires_a_series_key():
    frame = pd.DataFrame({"report_date": pd.date_range("2020-01-07", periods=3, freq="7D"),
                          "x": [1.0, 2.0, 3.0]})
    with pytest.raises(AggregateError, match="pools every"):
        standardise(frame, "x", by=[])


# ── The futures wrapper ─────────────────────────────────────────────────────
def test_extremity_refuses_a_panel_with_no_risk_units(history_panel):
    """`net_risk_usd` is rung 4 and does not exist before it. Naming that is more useful than
    a KeyError on a column the caller has never heard of."""
    with pytest.raises(ExtremityError, match="rung 4"):
        add_extremity(history_panel)


def test_extremity_refuses_a_panel_too_short_to_score(vintage_panel):
    """The vintage store begins 2025-01-07, so a three-year window scores nothing there. An
    all-null column that does not say why is the failure this prevents."""
    panel = vintage_panel.assign(net_risk_usd=1.0)
    with pytest.raises(ExtremityError, match="vintage store does not have"):
        add_extremity(panel)


def test_extremity_scores_the_long_panel_and_reports_its_gaps(history_panel):
    """End to end on twenty years of real fixture data, with a synthetic risk column so the
    test stays offline: the scoring is what is under test, not the price join."""
    rng = np.random.default_rng(2)
    panel = history_panel.assign(
        net_risk_usd=rng.normal(size=len(history_panel)).cumsum())
    scored = add_extremity(panel)

    assert scored["net_risk_usd_pct"].dropna().between(0.0, 1.0).all()
    report = extremity_report(scored)
    assert report.loc["scored", "rows"] > 10_000
    assert report.loc["total", "rows"] == len(history_panel)
    assert (report.loc[["scored", "short_history", "no_risk_units"], "rows"].sum()
            == len(history_panel))


def test_nulls_do_not_poison_a_window(history_panel):
    """A price gap costs a market observations inside its own trailing three years; it must
    not null the whole series."""
    panel = history_panel.assign(net_risk_usd=1.0)
    panel.loc[panel.index[::10], "net_risk_usd"] = np.nan
    scored = add_extremity(panel, min_periods=20)
    assert scored["net_risk_usd_pct"].notna().any()


# ── Rendering identifiers ───────────────────────────────────────────────────
def test_market_codes_render_as_codes_not_numbers():
    """CFTC market codes are zero-padded strings and several parse cleanly as integers.

    Rendered as numbers, wheat's `001612` becomes `1,612`: leading zeros gone, separator
    added, no longer a code anyone can look up, and nothing in the output says so. Caught in
    a published extremity table before this guard existed.
    """
    from crowdmon.core.report import to_markdown

    frame = pd.DataFrame({"market_code": ["001612", "001602"],
                          "net_contracts": [31411, -8163]})
    out = to_markdown(frame)
    assert "001612" in out and "001602" in out
    assert "1,612" not in out
    assert "31,411" in out, "real quantities must still get separators"
