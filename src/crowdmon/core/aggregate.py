"""Trailing-window standardisation: rolling z-scores and percentiles.

Asset-class agnostic, and genuinely so: nothing here knows what a category, a market or a
contract is. It takes a time-indexed series and says where its latest value sits against its
own recent history. The futures-specific wrapper that knows this is COT positioning in risk
units is `crowdmon.futures.extremity`.

**Every window is trailing, and that is the whole point.** A z-score computed against
full-sample moments, or against a centred window, uses values that were not knowable at the
time and will flatter any historical result built on it. The rule this module enforces is
that the score at `t` is a function of observations at times `<= t` and nothing else. It is
the same discipline `futures.cot_adapter` applies to release dates, one layer up.

**Windows are measured in TIME, not in observations.** `"1095D"` means the trailing three
calendar years, not the trailing 156 rows. The difference is not cosmetic: COT markets drop
out of the report when they fall below the reporting threshold and come back later, and oats
has a 294-day hole in the real store. An observation-count window would quietly reach back
five calendar years to fill 156 rows there, and would report that as a three-year score. A
time window instead ends up with fewer observations, which `min_periods` then refuses.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Three calendar years, the window module spec §6.1 and appendix §A.4 both specify.
DEFAULT_WINDOW = "1095D"

#: Minimum observations required inside the window before a score is produced. Weekly data
#: gives roughly 156 in three years, so this is about two years' worth. Below it the moments
#: are estimated from too little to mean anything, and a confident-looking z-score computed
#: off twenty observations is worse than a null.
DEFAULT_MIN_PERIODS = 104

#: Fraction trimmed from EACH tail before estimating the mean and standard deviation.
#:
#: **Zero by default, which follows appendix §A.4 rather than module spec §6.1.** The
#: appendix gives the plain `z_t = (x_t - mu_W) / s_W` and is the authoritative statement of
#: every formula in this package; §6.1 adds the word "winsorised" and is not. Where they
#: disagree the appendix wins, and here the measurement agrees with it.
#:
#: **What winsorising does to positioning data, measured on the real store.** Winsorising
#: assumes the values it clips are outliers. In a positioning series they are usually the top
#: of a trend, because positions build over months rather than spiking for a week. Platinum
#: Other Reportable on 2026-01-27 is the worst case in twenty years: the trailing window's
#: six largest values are a monotone run-up (31.5m, 47.1m, 47.6m, 54.4m, 55.7m, 62.5m) ending
#: at the current point. Clipping at 5% removes the run-up, shrinks the standard deviation
#: 3.5x, and inflates the score from a defensible **z = 6.1 to z = 22.1**.
#:
#: | winsor | median abs z | 99th | max | share above 6 |
#: |---|---|---|---|---|
#: | 0.00 | 0.85 | 3.65 | 9.6 | 0.05% |
#: | 0.05 | 0.91 | 4.31 | 22.1 | 0.32% |
#: | 0.10 | 1.00 | 5.46 | 27.4 | 0.75% |
#:
#: So it is kept as a parameter, because a genuinely spiky series would benefit, and it
#: defaults off. `rolling_percentile` is unaffected either way, which is why the spec is
#: right that the percentile is the thing to report.
DEFAULT_WINSOR = 0.0


class AggregateError(ValueError):
    """The series cannot be standardised as asked."""


def winsorise(values: np.ndarray, limit: float = DEFAULT_WINSOR) -> np.ndarray:
    """Clip both tails to their `limit` quantile. NaNs are preserved, not filled.

    Winsorising rather than trimming because the window is already small: dropping the tails
    would cost observations where `min_periods` is the binding constraint, while clipping
    keeps the count and only removes the leverage.
    """
    if not 0 <= limit < 0.5:
        raise AggregateError(
            f"winsor limit must be in [0, 0.5), got {limit}. At 0.5 both tails meet at the "
            f"median and every value in the window becomes the median.")
    if limit == 0:
        return values
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return values
    lo, hi = np.quantile(finite, [limit, 1.0 - limit])
    return np.clip(values, lo, hi)


def rolling_zscore(series: pd.Series, *, window: str | int = DEFAULT_WINDOW,
                   min_periods: int = DEFAULT_MIN_PERIODS,
                   winsor: float = DEFAULT_WINSOR) -> pd.Series:
    """`z_t = (x_t - mu_W) / s_W` over a trailing window (appendix §A.4).

    **Winsorising is off by default** (see `DEFAULT_WINSOR` for the measurement that decided
    it). When it is switched on, the numerator uses the raw `x_t` and only the moments are
    clipped: the intent is that one past spike should not inflate `s_W` and thereby hide
    every later extreme. On positioning data that intent usually misfires, because the large
    values in the window are the top of a build rather than an outlier, and clipping them
    manufactures a huge score. Turn it on only for a series you have looked at.

    With `winsor > 0`, `z` stops being "standard deviations" in the textbook sense, since the
    denominator becomes a robust scale rather than the sample standard deviation.

    Prefer `rolling_percentile` for comparison across series in any case: a `z` of 2.0 in
    gold and 2.0 in natural gas are not the same statement, and the percentile is what module
    spec §6.1 asks be reported.

    `s_W == 0` yields null rather than infinity: a window in which nothing varied cannot say
    whether the current value is unusual.
    """
    _require_sorted_datetime_index(series, window)
    values = pd.to_numeric(series, errors="coerce").astype("float64")
    roll = values.rolling(window, min_periods=min_periods)

    if winsor:
        mu = roll.apply(lambda a: np.nanmean(winsorise(a, winsor)), raw=True)
        sd = roll.apply(lambda a: _nanstd(winsorise(a, winsor)), raw=True)
    else:
        mu, sd = roll.mean(), roll.std(ddof=1)

    z = (values - mu) / sd.where(sd > 0)
    return z.rename(f"{series.name}_z" if series.name else "z")


def rolling_percentile(series: pd.Series, *, window: str | int = DEFAULT_WINDOW,
                       min_periods: int = DEFAULT_MIN_PERIODS) -> pd.Series:
    """Where `x_t` ranks within its own trailing window, in `[0, 1]`.

    This is what module spec §6.1 asks be *reported* ("percentile against own history"), and
    it is the more robust of the two numbers for a reason worth stating: **it is computed on
    raw values and is therefore completely independent of the winsor level.** Ranks do not
    care about the magnitude of the tails, only their order. So the one free parameter in
    this module affects the secondary output and not the headline one.

    It is also the only form comparable across markets. A z of 2.0 in gold and a z of 2.0 in
    natural gas are not the same statement, because the two have different distributional
    shapes; a 95th percentile in each is.
    """
    _require_sorted_datetime_index(series, window)
    values = pd.to_numeric(series, errors="coerce").astype("float64")
    pct = values.rolling(window, min_periods=min_periods).rank(pct=True)
    return pct.rename(f"{series.name}_pct" if series.name else "pct")


def standardise(frame: pd.DataFrame, column: str, *, by: list[str],
                date_column: str = "report_date",
                window: str | int = DEFAULT_WINDOW,
                min_periods: int = DEFAULT_MIN_PERIODS,
                winsor: float = DEFAULT_WINSOR) -> pd.DataFrame:
    """Add `<column>_z` and `<column>_pct` per group, each trailing within its own group.

    `by` is the series key. Grouping is not optional and there is no default: standardising
    a panel without it would pool every market into one distribution, and the whole premise
    of a percentile "against own history" is that the history is the market's own.
    """
    missing = [c for c in [*by, date_column, column] if c not in frame.columns]
    if missing:
        raise AggregateError(f"missing columns for standardisation: {missing}")
    if not by:
        raise AggregateError(
            "`by` is required. Standardising a panel without a series key pools every "
            "series into one distribution, which is not what 'against own history' means.")

    out = frame.copy()
    out[date_column] = pd.to_datetime(out[date_column])
    out = out.sort_values([*by, date_column], kind="mergesort")

    z_parts, pct_parts = [], []
    for _, group in out.groupby(by, dropna=False, sort=False):
        series = group.set_index(date_column)[column]
        z_parts.append(rolling_zscore(series, window=window, min_periods=min_periods,
                                      winsor=winsor).set_axis(group.index))
        pct_parts.append(rolling_percentile(series, window=window,
                                            min_periods=min_periods).set_axis(group.index))
    out[f"{column}_z"] = pd.concat(z_parts) if z_parts else np.nan
    out[f"{column}_pct"] = pd.concat(pct_parts) if pct_parts else np.nan
    return out


# ── internals ───────────────────────────────────────────────────────────────
def _nanstd(values: np.ndarray) -> float:
    """Sample standard deviation, ddof=1, ignoring NaN.

    ddof=1 because these are samples from a market's history rather than a population, and
    the difference is not negligible at the `min_periods` floor. Returns NaN rather than 0
    for a single observation, so `rolling_zscore` nulls it instead of dividing by zero.
    """
    finite = values[np.isfinite(values)]
    if finite.size < 2:
        return np.nan
    return float(np.std(finite, ddof=1))


def _require_sorted_datetime_index(series: pd.Series, window) -> None:
    """A time-based window silently produces nonsense on an unsorted or non-datetime index.

    pandas raises on some of these and not others, so this checks explicitly. An out-of-order
    index is the dangerous one: the rolling window would look "back" over rows that are
    actually later, which is lookahead wearing the costume of a trailing window.
    """
    if not isinstance(window, str):
        return
    if not isinstance(series.index, pd.DatetimeIndex):
        raise AggregateError(
            f"a time-based window ({window!r}) needs a DatetimeIndex, got "
            f"{type(series.index).__name__}. Pass an integer window for positional rolling.")
    if not series.index.is_monotonic_increasing:
        raise AggregateError(
            "index is not sorted ascending. A trailing window over an unsorted index reaches "
            "over rows that are actually in the future, which is lookahead.")
