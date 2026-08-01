"""Positioning in risk units: notional x volatility. Module spec §5.2 rung 4.

    net_risk_usd = net_notional_usd x sigma_daily

This is the rung the spec calls "the default for every cross-market comparison", and the
reason is §11 of the same spec: a vol-targeting book sizes at ``target_vol / sigma``, so its
notional is inversely proportional to volatility. **A volatility spike forces selling
regardless of price direction.** `net_notional x sigma` is the quantity that stays constant
when a vol targeter is at its target, which makes it the quantity whose deviation says how
much mechanical selling a vol move must produce.

**The volatility must come from PROPORTIONALLY (ratio) adjusted prices.**

`notional` refuses everything but ``unadj`` because only that carries tradeable price
LEVELS. This module is the mirror image: it needs correct percentage RETURNS, and it refuses
both of the other two series. The two factors of the product come from two different price
series on purpose, and neither substitutes for the other.

**Why not ``backadj``.** Additive back-adjustment preserves absolute daily price CHANGES,
not percentage returns. It accumulates roll gaps into the historical level, which both
distorts the denominator of every return and, on long-history contracts, drives the level
through zero. Annualised vol from ``backadj`` percent returns against the real store:

| Market | vol via `backadj` | vol via `propadj` | inflation | `backadj` closes <= 0 |
|---|---|---|---|---|
| DC (Class III Milk) | 9.9e13 % | 9.2% | **1.1e13 x** | 41.2% |
| ZS (soybeans) | 4366.9% | 21.7% | **201 x** | 52.3% |
| ZN (10-year note) | 1183.1% | 6.5% | **182 x** | 8.9% |
| CT (cotton) | 889.0% | 23.9% | 37 x | 2.6% |
| CL (crude) | 676.1% | 63.4% | 11 x | 0.6% |
| GC (gold) | 8.8% | 18.9% | **0.47 x** | 0.0% |

Gold is the row that makes this a guard rather than a note. It never goes negative, so it
survives every sanity check for a non-finite or absurd number, and its vol is still wrong by
a factor of two, in the *understating* direction, because additive adjustment inflates
historical levels and a fixed dollar move against an inflated level is a smaller percentage.
A markets-wide screen for "implausible volatility" would clear gold and flag nothing.

**Why not ``unadj``.** Unadjusted returns carry a fabricated jump at every roll, where the
series steps from the expiring contract to the next one. Full-sample volatility barely
notices (GC 1.01x, ZN 1.02x), which is exactly what makes it dangerous: the contamination is
concentrated on a few dozen days and any *short* window spanning one is badly wrong. On a
63-day window against the real store, peak inflation is 9.84x (DC, 2004-03-31), 2.93x (NG),
2.07x (LE), 1.57x (GC), and crude's worst single roll day fabricates a **130.7%** daily move.
For DC, 95.8% of all 63-day windows are inflated by more than 25%.

``propadj`` is derived on read by `cotdata` from ``unadj`` + ``backadj`` and preserves daily
percent returns. Module spec §5.1 asked for exactly this ("built ratio-adjusted (not
difference-adjusted) so returns are correct"); an earlier draft of `notional`'s docstring
said volatility wanted ``backadj``, which was wrong, and the measurements above are why.
See `docs/design/amendments-2026-08-01.md`.

**``propadj`` is not strictly positive, and this module used to assume it was.** Ratio
adjustment scales by a positive factor, so it preserves the sign of the underlying series
rather than imposing one. `cotdata.prices._ratio_adjust`'s own docstring says the result
"stays strictly positive", which holds only where the market did. WTI settled at **-37.63 on
2020-04-20** and crude's ``propadj`` close that day is -24.11. A first version of
`_sigma_series` raised on any non-positive close and so refused to produce a volatility for
crude at all, over one real day.

The distinction that matters is rate, and the store separates the two cases by three orders
of magnitude with nothing in between. Across all 47 symbols, ``propadj`` has exactly ONE
non-positive close anywhere (0.009% of crude's history); ``backadj`` runs 52.3% for soybeans
and 41.2% for Class III Milk. So a few are a market event, where only the returns *touching*
them are undefined and get masked, and many are a wrong series, which raises.

**Risk units do not change a duration, and must not be fed into one alone.** Appendix §A.5's
`T = Q / (kappa V)` is unit-free: `Q` and `V` merely have to be in the SAME units. Every rung
of §A.4's ladder therefore gives the identical answer, and the appendix's cocoa example
returns 19.9 days in contracts, in notional, and in risk units alike.

The failure that guards against is easy to reach and silent when reached. A vol-scaled `Q`
over a contract-denominated `V` is wrong by exactly `M x F x sigma`, which for cocoa is 750x:
the appendix's twenty days becomes **fifty-nine years**, and nothing in the units of the
answer says so, because days are still days. `test_appendix.py` pins all four cases.

**The cross-check.** Dollar volatility per contract-unit is reachable two independent ways:
``unadj_price x sigma_pct(propadj)`` and ``std(diff(backadj))``, the latter being precisely
what additive adjustment does preserve. On mid-history dates across eight markets they agree
to within 2-10% (GC 1.023, CL 0.968, ZS 0.958, ZN 0.981, ES 1.005, 6E 1.002). That is the
evidence that ``propadj`` returns and ``unadj`` levels compose into a real dollar quantity,
and it is asserted in `test_riskunits_live.py` rather than left as an assurance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Columns ``add_risk_units`` adds.
RISK_COLUMNS = ["sigma_daily", "sigma_annual", "sigma_date", "sigma_staleness_days",
                "net_risk_usd", "long_risk_usd", "short_risk_usd", "gross_risk_usd",
                "oi_risk_usd"]

#: The only adjustment whose returns are percentages. See the module docstring.
RISK_ADJUSTMENT = "propadj"

#: Trading days in the volatility window. One quarter. Long enough that a single day cannot
#: dominate, short enough to still be moving when a vol regime changes, which is the event
#: this whole rung exists to anticipate.
DEFAULT_VOL_WINDOW = 63

#: Minimum observations before a window yields a number. Two thirds of the window. A sigma
#: computed from a handful of points is noise wearing a number's clothes, and it would feed
#: straight into a cross-market ranking.
DEFAULT_MIN_PERIODS = 42

#: Trading days per year, for the reported annualised figure only. Nothing downstream
#: consumes ``sigma_annual``; it exists because humans read annualised vol and cannot read
#: daily vol.
TRADING_DAYS = 252

#: Same bound and same reasoning as ``notional.DEFAULT_MAX_STALENESS_DAYS``.
DEFAULT_MAX_STALENESS_DAYS = 5

#: Above this share of non-positive closes, the series is the wrong one rather than a market
#: that traded below zero. Measured across all 47 symbols in the store: ``propadj`` has
#: exactly ONE non-positive close anywhere (CL, 2020-04-20, 0.009%), while ``backadj`` runs
#: 52.3% for soybeans, 41.2% for Class III Milk and 8.9% for the 10-year note. One percent
#: sits in the empty space between a real settlement and a broken transformation.
MAX_NONPOSITIVE_RATE = 0.01


class RiskUnitsError(RuntimeError):
    """The inputs would produce a number that is not a risk unit."""


def _sigma_series(symbol: str, adjustment: str, price_field: str,
                  window: int, min_periods: int) -> pd.Series:
    """Rolling daily volatility of percentage returns, as a fraction."""
    import cotdata

    bars = cotdata.get_prices(symbol, adjustment=adjustment)
    if bars is None or bars.empty:
        return pd.Series(dtype="float64")
    if price_field not in bars.columns:
        raise RiskUnitsError(
            f"{symbol}: price field {price_field!r} not in {list(bars.columns)}")
    px = pd.to_numeric(bars[price_field], errors="coerce").dropna()
    # Same nanosecond coercion as notional._price_series, for the same reason: the vintage
    # store round-trips report_date through parquet as datetime64[us] while the price index
    # is [ns], and merge_asof refuses mismatched resolutions outright.
    px.index = pd.to_datetime(px.index).astype("datetime64[ns]")
    px = px.astype("float64").sort_index()

    # Ratio adjustment scales by a POSITIVE factor, so it preserves the sign of the
    # unadjusted series rather than forcing positivity. `cotdata`'s own docstring says a
    # ratio-adjusted series "stays strictly positive"; that holds only where the underlying
    # market did, and WTI settled at -37.63 on 2020-04-20. An earlier version of this
    # function raised on any non-positive close and therefore refused to compute volatility
    # for crude at all, over one real day in 2020.
    #
    # So: a few non-positive closes are a market event and only the returns TOUCHING them
    # are undefined. Many are a wrong series. Measured across the whole store, the two cases
    # are three orders of magnitude apart and nothing sits between them.
    nonpos = px <= 0
    rate = float(nonpos.mean())
    if rate > MAX_NONPOSITIVE_RATE:
        raise RiskUnitsError(
            f"{symbol}: {int(nonpos.sum())} of {len(px)} closes ({rate:.1%}) are non-positive "
            f"in an adjustment={adjustment!r} series, above the {MAX_NONPOSITIVE_RATE:.0%} "
            f"bound. Percentage returns are undefined across a sign change, so this cannot "
            f"yield a volatility. A rate this high is a wrong series, not a market that "
            f"traded below zero: across the whole store {RISK_ADJUSTMENT!r} has exactly one "
            f"non-positive close anywhere (CL 2020-04-20), while 'backadj' runs 52.3% for "
            f"soybeans.")

    ret = px.pct_change().replace([np.inf, -np.inf], np.nan)
    # A return is undefined if EITHER endpoint is non-positive: from a negative base the
    # percentage is meaningless, and to a negative close it is a sign change. Masking both
    # leaves the window short by a day or two around the event rather than discarding the
    # market, and `min_periods` decides whether what remains is enough.
    return ret.where(~(nonpos | nonpos.shift(fill_value=False))) \
              .rolling(window, min_periods=min_periods).std()


def add_risk_units(with_notional: pd.DataFrame, *,
                   adjustment: str = RISK_ADJUSTMENT,
                   price_field: str = "Close",
                   vol_on: str = "report_date",
                   window: int = DEFAULT_VOL_WINDOW,
                   min_periods: int = DEFAULT_MIN_PERIODS,
                   max_staleness_days: int = DEFAULT_MAX_STALENESS_DAYS) -> pd.DataFrame:
    """Add vol-scaled notional to a frame already carrying notional.

    ``with_notional`` needs the columns ``notional.add_notional`` emits. Rows with no
    notional, or no volatility within ``max_staleness_days``, get null risk units rather
    than being dropped, which is the rule the whole normalisation layer follows: a partial
    panel is never silently returned as a whole one. Use :func:`coverage_report` beside any
    aggregate.

    ``vol_on`` defaults to ``report_date`` to match `add_notional`. The two must agree: a
    notional struck on Tuesday and a sigma struck on Friday is a product of two different
    days, and the mismatch would be invisible in the output.
    """
    if adjustment != RISK_ADJUSTMENT:
        raise RiskUnitsError(
            f"refusing to compute volatility from adjustment={adjustment!r}. Only "
            f"{RISK_ADJUSTMENT!r} carries percentage RETURNS. Measured against the real "
            f"store: 'backadj' inflates annualised vol by 201x for soybeans and 182x for "
            f"the 10-year note (52.3% and 8.9% of their back-adjusted closes are <= 0), and "
            f"understates GOLD by half while never going negative at all, so no "
            f"implausibility screen would catch it. 'unadj' fabricates a jump at every "
            f"roll: crude's worst roll day is a 130.7% move that never happened, and a "
            f"63-day window spanning one is inflated up to 9.84x. Notional is the opposite "
            f"case and belongs in notional.py, which wants unadjusted price LEVELS.")

    required = {"net_notional_usd", "long_notional_usd", "short_notional_usd",
                "gross_notional_usd", "symbol", vol_on}
    missing = sorted(required - set(with_notional.columns))
    if missing:
        raise RiskUnitsError(
            f"missing columns {missing}. Run add_notional first: risk units are notional "
            f"scaled by volatility, and there is no way to recover notional from contract "
            f"counts here without duplicating the unadjusted-price rule this module is the "
            f"mirror image of.")
    if min_periods > window:
        raise RiskUnitsError(
            f"min_periods={min_periods} exceeds window={window}, which can never be "
            f"satisfied and would return an all-null sigma.")
    if with_notional.empty:
        return with_notional.assign(
            **{c: pd.Series(dtype="datetime64[ns]" if c == "sigma_date" else "float64")
               for c in RISK_COLUMNS})

    out = with_notional.copy()
    out[vol_on] = pd.to_datetime(out[vol_on]).astype("datetime64[ns]")

    sigma = pd.Series(float("nan"), index=out.index, dtype="float64")
    sigma_date = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    tol = pd.Timedelta(days=max_staleness_days)
    for sym, idx in out.groupby("symbol", dropna=True, sort=False).groups.items():
        series = _sigma_series(str(sym), adjustment, price_field, window, min_periods)
        series = series.dropna()
        if series.empty:
            continue
        want = out.loc[idx, [vol_on]].sort_values(vol_on)
        merged = pd.merge_asof(
            want, pd.DataFrame({"_sd": series.index, "_sig": series.to_numpy()}),
            left_on=vol_on, right_on="_sd", direction="backward", tolerance=tol)
        merged.index = want.index
        sigma.loc[merged.index] = merged["_sig"].to_numpy()
        sigma_date.loc[merged.index] = merged["_sd"].to_numpy()

    out["sigma_daily"] = sigma
    out["sigma_annual"] = sigma * np.sqrt(TRADING_DAYS)
    out["sigma_date"] = sigma_date
    out["sigma_staleness_days"] = (out[vol_on] - out["sigma_date"]).dt.days

    # Sign convention: sigma is non-negative, so every risk column inherits the sign of the
    # notional it scales. net_risk_usd is therefore DIRECTIONAL daily dollars at risk, which
    # is what makes Q_sell and Q_buy separable downstream. It is not an absolute magnitude
    # and must not be summed across markets without regard to sign.
    out["net_risk_usd"] = out["net_notional_usd"] * sigma
    out["long_risk_usd"] = out["long_notional_usd"] * sigma
    out["short_risk_usd"] = out["short_notional_usd"] * sigma
    out["gross_risk_usd"] = out["gross_notional_usd"] * sigma
    out["oi_risk_usd"] = pd.to_numeric(out.get("oi_notional_usd"), errors="coerce") * sigma
    return out


def coverage_report(with_risk: pd.DataFrame) -> pd.Series:
    """Why rows have no risk units, counted. Meant to be printed beside any aggregate.

    Distinguishes the two ways a row can arrive here already unusable (no contract spec, no
    price) from the one this module introduces (no volatility), because they are different
    problems: the first two are registry and vendor-coverage questions, the third means the
    price series is too short or too gappy to support a window.
    """
    if with_risk.empty:
        return pd.Series(dtype="int64")
    no_notional = with_risk["net_notional_usd"].isna()
    no_sigma = ~no_notional & with_risk["sigma_daily"].isna()
    return pd.Series({
        "with_risk_units": int(with_risk["net_risk_usd"].notna().sum()),
        "no_notional": int(no_notional.sum()),
        "no_volatility": int(no_sigma.sum()),
        "total": len(with_risk),
    })
