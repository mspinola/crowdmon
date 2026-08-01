"""Seasonality, module spec §5.4.

The central test is again the lookahead one. A seasonal profile feels like a property of the
calendar rather than an estimate from data, which is exactly why full-sample seasonal
adjustment is so common and so wrong: subtracting a week-34 average that includes years that
had not happened yet is straightforward use of the future.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import (
    deseasonalise,
    seasonal_profile,
    seasonality_report,
    week_of_year,
)
from crowdmon.futures.seasonal import SeasonalError

KEY = {"market_code": "T1", "report_type": "disaggregated", "combined": False,
       "category": "producer_merchant"}


def _weekly(values, start="2010-01-05") -> pd.DataFrame:
    dates = pd.date_range(start, periods=len(values), freq="7D")
    return pd.DataFrame([{**KEY, "report_date": d, "x": v}
                         for d, v in zip(dates, values)])


def _sawtooth(years: int, amplitude: float = 10.0, level: float = 100.0) -> pd.DataFrame:
    """A series whose only structure is week-of-year, so the profile has a known answer."""
    weeks = 52 * years
    dates = pd.date_range("2010-01-05", periods=weeks, freq="7D")
    woy = dates.isocalendar().week.astype(int).to_numpy()
    return pd.DataFrame([{**KEY, "report_date": d, "x": level + amplitude * np.sin(
        2 * np.pi * w / 52.0)} for d, w in zip(dates, woy)])


# ── The property that matters ───────────────────────────────────────────────
def test_a_profile_never_changes_when_later_years_arrive():
    """No lookahead. A full-sample week-of-year mean knows what week 34 looks like in years
    that have not happened, and subtracting it from an early observation uses the future."""
    rng = np.random.default_rng(0)
    full = _sawtooth(12)
    full["x"] += rng.normal(scale=2.0, size=len(full))

    early = full[full["report_date"] < "2016-01-01"].copy()
    a = seasonal_profile(early, "x")
    b = seasonal_profile(full, "x").reindex(a.index)
    pd.testing.assert_series_equal(a, b, check_names=False)


def test_the_current_observation_is_excluded_from_its_own_profile():
    """Otherwise the profile contains the value it is about to be subtracted from, which
    shrinks every deviation toward zero by construction."""
    frame = _sawtooth(6)
    profile = seasonal_profile(frame, "x", min_years=1)
    scored = frame.assign(p=profile).dropna(subset=["p"])
    first = scored.iloc[0]
    same_week = frame[week_of_year(frame["report_date"])
                      == week_of_year(pd.Series([first["report_date"]])).iloc[0]]
    prior = same_week[same_week["report_date"] < first["report_date"]]["x"]
    assert first["p"] == pytest.approx(prior.mean())


def test_min_years_costs_the_start_of_every_series():
    """Three years of warm-up on top of whatever the measure being adjusted already needs.
    Stated because it is the real price of doing this without lookahead."""
    frame = _sawtooth(6)
    for min_years, expected_null_years in ((1, 1), (3, 3)):
        profile = seasonal_profile(frame, "x", min_years=min_years)
        first = frame.loc[profile.notna(), "report_date"].min()
        elapsed = (first - frame["report_date"].min()).days / 365.25
        assert elapsed >= expected_null_years - 0.1


# ── The profile recovers a known seasonal ───────────────────────────────────
def test_a_pure_seasonal_series_is_almost_entirely_removed():
    frame = _sawtooth(10, amplitude=10.0, level=100.0)
    out = deseasonalise(frame, "x", min_years=3)
    scored = out[out["x_seasonal"].notna()]
    assert scored["x"].std() > 5.0
    assert scored["x_deseasonalised"].std() < 0.5


def test_a_series_with_no_seasonality_is_left_alone():
    """Subtracting a profile estimated from noise must not manufacture structure."""
    rng = np.random.default_rng(1)
    frame = _weekly(rng.normal(size=52 * 10))
    out = deseasonalise(frame, "x", min_years=3)
    scored = out[out["x_seasonal"].notna()]
    ratio = scored["x_deseasonalised"].std() / scored["x"].std()
    assert 0.9 < ratio < 1.6, "a noise profile should neither remove nor add much"


def test_rows_without_a_profile_keep_their_raw_value():
    """Nulling three years of every series to remove a component worth 0.5% of variance would
    cost more than it buys, so the raw value passes through and `_seasonal` stays null to
    mark it."""
    frame = _sawtooth(6)
    out = deseasonalise(frame, "x", min_years=3)
    warm_up = out[out["x_seasonal"].isna()]
    assert not warm_up.empty
    assert (warm_up["x_deseasonalised"] == warm_up["x"]).all()


# ── Series are never pooled ─────────────────────────────────────────────────
def test_each_market_category_gets_its_own_profile():
    """A producer's crop calendar and a fund's are different shapes in the same market, which
    is the distinction §5.4 draws."""
    a = _sawtooth(6)
    b = _sawtooth(6)
    b["category"] = "managed_money"
    b["x"] = 200.0 - (b["x"] - 100.0)   # the same seasonal, inverted
    both = pd.concat([a, b], ignore_index=True)

    out = deseasonalise(both, "x", min_years=3)
    for category in ("producer_merchant", "managed_money"):
        part = out[(out["category"] == category) & out["x_seasonal"].notna()]
        assert part["x_deseasonalised"].std() < 0.5, category


# ── The report ──────────────────────────────────────────────────────────────
def test_the_report_separates_mean_shift_from_variance_explained():
    """The two rank categories differently on real data, and only the second settles whether
    seasonality matters. A large spread with a tiny share is a systematic shift swamped by
    week-to-week variation."""
    rng = np.random.default_rng(2)
    seasonal = _sawtooth(10, amplitude=10.0)
    seasonal["x"] += rng.normal(scale=1.0, size=len(seasonal))
    noisy = _sawtooth(10, amplitude=10.0)
    noisy["category"] = "managed_money"
    noisy["x"] += rng.normal(scale=30.0, size=len(noisy))

    report = seasonality_report(pd.concat([seasonal, noisy], ignore_index=True), "x")
    by_category = report.set_index("category")

    # variance_share gets it right: identical true amplitude, one drowned in noise.
    assert by_category.loc["producer_merchant", "variance_share"] > 0.9
    assert by_category.loc["managed_money", "variance_share"] < 0.2

    # mean_spread gets it BACKWARDS, and that is the point of measuring both. It is the
    # range of ~53 noisy estimates, so noise inflates it: 20.7 clean against 64.2 noisy,
    # for the same underlying seasonal amplitude of 10.
    assert (by_category.loc["managed_money", "mean_spread"]
            > 2 * by_category.loc["producer_merchant", "mean_spread"])


def test_the_report_uses_the_full_sample_on_purpose(history_panel):
    """Descriptive, not an input to anything, so all of it is the right sample. Contrast
    `seasonal_profile`, which must be trailing because its output gets subtracted."""
    report = seasonality_report(history_panel, "long_contracts")
    assert set(report["category"]) >= {"producer_merchant", "managed_money"}
    assert (report["variance_share"].dropna() >= 0).all()
    assert (report["variance_share"].dropna() <= 1).all()


def test_no_week_of_year_scheme_pins_a_seasonal_moment():
    """A floor on how sharply any of this can resolve seasonality, and not a bug to fix.

    The third Tuesday of August lands in ISO week 34, 33, 33, 33, 34 over 2020-2024, because
    52 weeks is not 365 days. A fixed point in the crop calendar therefore drifts by plus or
    minus one week against any weekly index, which smears the profile by about a week in each
    direction. Asserted so nobody "fixes" the bucketing expecting it to help.
    """
    tuesdays = pd.Series(pd.to_datetime(["2020-08-18", "2021-08-17", "2022-08-16",
                                         "2023-08-15", "2024-08-20"]))
    weeks = week_of_year(tuesdays)
    assert weeks.nunique() > 1, "if this ever pins exactly, re-read the docstring"
    assert weeks.max() - weeks.min() <= 1, "drift should be one week, not more"


def test_a_missing_column_is_named():
    with pytest.raises(SeasonalError, match="nonexistent"):
        seasonal_profile(_sawtooth(4), "nonexistent")
