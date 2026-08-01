"""Seasonality: the crop calendar, and how much of an extremity reading it explains.

Module spec §5.4. "Commercial and producer-merchant positioning in agricultural markets is
strongly seasonal — hedging follows the crop calendar, not sentiment. Raw z-scores on those
categories are dominated by seasonality and will produce spurious extremes every year at the
same time. Apply a seasonal decomposition (or compare year-over-year within week-of-year)
before z-scoring commercial categories in ags. Managed Money is less affected but not
immune."

**Measured across twenty years, most of that paragraph does not hold**, which is why this
module leads with measurement and leaves the adjustment off by default. Week-of-year variance
share of extremity `z`:

| category | ag | non-ag | ratio |
|---|---|---|---|
| other_reportable | 0.0074 | 0.0028 | 2.65x |
| swap | 0.0141 | 0.0065 | 2.17x |
| nonreportable | 0.0059 | 0.0056 | 1.04x |
| **producer_merchant** | **0.0046** | **0.0049** | **0.95x** |
| managed_money | 0.0016 | 0.0042 | 0.39x |

- "Dominated by seasonality" is false everywhere. The largest share anywhere is **1.4%**.
- Producer/Merchant, the category §5.4 names, is **not** more seasonal in ags than elsewhere.
- Managed Money is indeed less affected, and least of all in ags.
- The categories that are genuinely more seasonal in ags are Swap and Other Reportable,
  neither of which §5.4 mentions.

So deseasonalising by default would trade a visible caveat for an invisible transformation
that removes at most 1.4% of the variation. `deseasonalise` exists for anyone who wants it on
a specific series. See `docs/design/amendments-2026-08-02.md` §B3-B6.

## The lookahead this module exists to avoid

A seasonal profile estimated from the whole sample knows what week 34 looks like in years
that have not happened yet, and subtracting it from an early observation is a straightforward
use of future data. Published seasonal adjustments do this constantly, because the profile
feels like a property of the calendar rather than an estimate from data. It is an estimate.

So the profile here is **trailing and excludes the current observation**: the estimate for
week 34 of 2015 is the mean of week 34 in 2006 through 2014 and nothing else. That is why
`min_years` exists, why the first years of every series are null, and why
`test_seasonal.py`'s central test is the same growing-window check `core.aggregate` uses.

The cost is real: at `min_years=3` a weekly series produces nothing for its first three
years, on top of whatever warm-up the measure being adjusted already needs.
"""
from __future__ import annotations

import pandas as pd

#: The series key. Seasonality is per market AND per category: a producer's crop calendar and
#: a fund's are different shapes even in the same market, which is the distinction §5.4 draws.
SERIES_KEY = ["market_code", "report_type", "combined", "category"]

#: Prior observations of the SAME week of year required before a profile value is produced.
#: Three is the smallest number from which a mean is not simply the previous year, and it
#: costs three years of every series.
DEFAULT_MIN_YEARS = 3


class SeasonalError(ValueError):
    """The panel cannot support a seasonal estimate."""


def week_of_year(dates: pd.Series) -> pd.Series:
    """ISO week, 1-53.

    ISO rather than `dayofyear // 7` because it is the standard weekly bucket and handles
    year boundaries without a 53rd stub week of one or two days.

    **It does not pin a seasonal moment, and no week-of-year scheme does.** The third Tuesday
    of August falls in ISO week 34, 33, 33, 33, 34 over 2020-2024; `dayofyear // 7` gives 33,
    32, 32, 32, 33. A fixed point in the crop calendar drifts by plus or minus one week
    against any weekly index, because 52 weeks is not 365 days. That smears the profile by
    about one week in each direction and is a floor on how sharply this can resolve
    seasonality, not something a better bucket would fix.
    """
    return pd.to_datetime(dates).dt.isocalendar().week.astype("int64")


def seasonal_profile(panel: pd.DataFrame, column: str, *,
                     by: list[str] | None = None,
                     min_years: int = DEFAULT_MIN_YEARS) -> pd.Series:
    """The trailing week-of-year mean of `column`, aligned to `panel`'s index.

    For each row, the mean of every EARLIER observation of the same series in the same ISO
    week. The current observation is excluded, so the profile never contains the value it is
    about to be subtracted from, and no later observation is used at all.

    Null until `min_years` prior observations of that week exist.
    """
    keys = list(by or SERIES_KEY)
    missing = [c for c in [*keys, "report_date", column] if c not in panel.columns]
    if missing:
        raise SeasonalError(f"missing columns for a seasonal profile: {missing}")

    frame = panel.copy()
    frame["_woy"] = week_of_year(frame["report_date"])
    frame = frame.sort_values([*keys, "report_date"], kind="mergesort")
    values = pd.to_numeric(frame[column], errors="coerce")

    grouped = values.groupby([frame[k] for k in [*keys, "_woy"]], dropna=False, sort=False)
    # shift(1) is what makes it trailing: the estimate at t sees t-1 backwards and no more.
    prior = grouped.shift(1)
    prior_grouped = prior.groupby([frame[k] for k in [*keys, "_woy"]],
                                  dropna=False, sort=False)
    mean = prior_grouped.expanding().mean().reset_index(level=list(range(len(keys) + 1)),
                                                        drop=True)
    count = prior_grouped.expanding().count().reset_index(level=list(range(len(keys) + 1)),
                                                          drop=True)
    profile = mean.where(count >= min_years)
    return profile.reindex(panel.index).rename(f"{column}_seasonal")


def deseasonalise(panel: pd.DataFrame, column: str, *,
                  by: list[str] | None = None,
                  min_years: int = DEFAULT_MIN_YEARS) -> pd.DataFrame:
    """Add `<column>_seasonal` and `<column>_deseasonalised = column - seasonal`.

    Rows without a profile keep the raw value in `_deseasonalised` rather than becoming null,
    and `_seasonal` stays null so the two cases are distinguishable. The alternative, nulling
    three years of every series to remove a component worth 0.5% of variance, would cost far
    more than it buys.
    """
    profile = seasonal_profile(panel, column, by=by, min_years=min_years)
    out = panel.copy()
    out[f"{column}_seasonal"] = profile
    out[f"{column}_deseasonalised"] = (
        pd.to_numeric(out[column], errors="coerce") - profile.fillna(0.0))
    return out


def seasonality_report(panel: pd.DataFrame, column: str, *,
                       by: list[str] | None = None,
                       group: str = "category") -> pd.DataFrame:
    """How seasonal is this series, per group? The measurement §5.4 asserts without one.

    Three numbers, because they say different things and only the third settles anything:

    - `variance_share` — the between-week variance as a fraction of the total. **The one to
      draw conclusions from.** How much of what you actually observe the calendar explains.
    - `mean_spread` — max minus min of the week-of-year means, in the units of `column`.
      Descriptive, and **badly biased upward by noise**: it is the range of ~53 noisy
      estimates, so it grows with the noise and shrinks with observations per week. On a
      synthetic pair with identical true seasonal amplitude, adding noise moved it from 20.7
      to 64.2 while `variance_share` correctly fell from 0.98 to 0.13. Never compare
      `mean_spread` across groups with different sample sizes.
    - `n`, `weeks`, `per_week` — the sample behind it, so the bias above is visible.

    A large `mean_spread` with a tiny `variance_share` is the interesting case and is what the
    real data shows: a systematic seasonal shift that is nonetheless swamped by week-to-week
    variation. It biases a comparison across a complex at one point in the crop year and does
    not much move any single market's own percentile.

    Computed on the FULL sample deliberately, unlike `seasonal_profile`. This is a descriptive
    question about how seasonal a history was, not an input to anything, so using all of it is
    correct and using only a trailing window would understate the early years for no reason.
    """
    keys = list(by or SERIES_KEY)
    missing = [c for c in [*keys, "report_date", column, group] if c not in panel.columns]
    if missing:
        raise SeasonalError(f"missing columns for a seasonality report: {missing}")

    frame = panel.copy()
    frame["_woy"] = week_of_year(frame["report_date"])
    frame["_value"] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["_value"])
    if frame.empty:
        return pd.DataFrame()

    rows = []
    for name, part in frame.groupby(group, dropna=False, sort=False):
        weekly = part.groupby("_woy")["_value"].mean()
        total = part["_value"].var()
        between = part.groupby("_woy")["_value"].transform("mean").var()
        weeks = int(part["_woy"].nunique())
        rows.append({
            group: name,
            "n": len(part),
            "weeks": weeks,
            "per_week": round(len(part) / weeks, 1) if weeks else float("nan"),
            "variance_share": float(between / total) if total and total > 0 else float("nan"),
            "mean_spread": float(weekly.max() - weekly.min()),
        })
    return pd.DataFrame(rows).sort_values("variance_share", ascending=False).reset_index(
        drop=True)
