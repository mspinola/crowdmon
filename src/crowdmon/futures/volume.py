"""Daily volume: the denominator of `T = Q / (kappa V)`. Appendix §A.5, spec §8.

`pressure.py` has carried an optional `volume` argument since it was written, and the
answer to "where does it come from" was "nowhere, and do not invent one". This module is
that argument's source. Nothing is estimated here: every figure is an aggregate of exchange
volume `cotdata` already stores.

**The volume must be WHOLE-MARKET, and the parameter that gives you that is called
`front`.** This is the trap in the layer, and it points the opposite way to intuition.

`cotdata.get_prices` takes `volume="front"` or `volume="reconstructed"`, documented as
"continuous front-month volume" and "true market volume (first + second expiring contract)"
respectively. Measured against the store, the second is a strict SUBSET of the first:
`Volume_Reconstructed = FirstVolume + SecondVolume`, two expiries, while the plain `Volume`
field spans the whole curve. Reaching for `reconstructed` because it sounds more complete
understates the denominator by up to 48% and roughly doubles `T`.

Two independent measurements establish that `front` is whole-market:

1. **Open interest matches the CFTC exactly.** The price files carry an `Open Interest`
   column sourced independently from Norgate. Against COT's total-market open interest for
   the same Tuesday, 25 of 26 joinable markets agree **to the contract**, palladium at
   0.998, median ratio 1.000. Two vendors, two collection paths, one number.
2. **Curve concentration orders exactly as contract structure predicts.** The first two
   contracts' share of `Volume`: ZN and ES 1.00, 6E 0.998, PL 0.978, GC 0.954, SI 0.956,
   HG 0.865, ags 0.67-0.80, RB 0.606, HO 0.571, CL 0.540, NG 0.522. Quarterly financials
   trade entirely in the front month, metals nearly so, ags spread across crop months, and
   energy spreads across the strip. Crude's total is nearly twice its first two contracts,
   so `Volume` cannot be front-month-only.

That matters because `Q` from COT covers **all expiries**. A front-month denominator against
an all-expiry numerator would inflate `T` by 1/0.54 in crude, and by a different factor in
every market, which is worse than a constant bias.

**Nothing here uses today's volume.** §A.5's volume-spike trap: during a selloff realised
volume rises, so a naively computed `T_t = Q/(kappa V_t)` *falls*, and the monitor reports
improving liquidity exactly as liquidity is being consumed. Both series below are trailing
aggregates ending at the as-of date, never a spot reading, so the trap is closed by
construction rather than by remembering not to.

**Two denominators, and the stress one is not always the conservative one.** §A.5 defines
`V_stress = median(V_t : t in D_10)` over the worst decile of return days. Measured on the
latest panel, 9 of 25 markets trade MORE under stress than in calm markets (lumber's stress
volume is 1.62x its calm ADV, copper's 1.35x, coffee's 1.21x), so `T_stress < T_calm` there.
Cotton (0.70), wheat (0.64) and soybean oil (0.72) go the other way. Both are emitted and
neither is labelled "the" answer, because which one is conservative is a property of the
market and not of the method.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Columns ``add_volume`` adds.
VOLUME_COLUMNS = ["adv", "adv_stress", "volume_date", "volume_staleness_days"]

#: The whole-market series. Named for the front month; is not the front month. See above.
VOLUME_SERIES = "front"

#: The series this module refuses, and why it is tempting.
SUBSET_VOLUME_SERIES = "reconstructed"

#: Calm baseline: one year of trading days.
DEFAULT_ADV_WINDOW = 252

#: Stress window: five years, long enough to contain more than one stress regime.
DEFAULT_STRESS_LOOKBACK = 1260

#: §A.5's `D_10`, the worst decile of return days.
STRESS_DECILE = 0.10

#: Minimum observations before either aggregate returns a number.
DEFAULT_MIN_PERIODS = 60
DEFAULT_STRESS_MIN_PERIODS = 20

#: Same bound and reasoning as ``notional`` and ``riskunits``.
DEFAULT_MAX_STALENESS_DAYS = 5

#: Volatility series for ranking stress days. Percentage returns, so `propadj`, for every
#: reason set out in `riskunits`.
RETURN_ADJUSTMENT = "propadj"


class VolumeError(RuntimeError):
    """The inputs would produce a denominator that is not whole-market daily volume."""


def _raw_volume(symbol: str, series: str) -> pd.Series:
    """Whole-market daily volume, zeros treated as missing.

    Norgate publishes open interest and volume a day behind the price bar, so the most
    recent row carries 0 rather than null for both. A zero volume is never a real trading
    day for a listed contract, and left in place it would drag an average down and make a
    `T` look shorter than it is.
    """
    import cotdata

    if series != VOLUME_SERIES:
        raise VolumeError(
            f"refusing volume={series!r}. Only {VOLUME_SERIES!r} is whole-market. Despite "
            f"the names, {SUBSET_VOLUME_SERIES!r} is FirstVolume + SecondVolume, a strict "
            f"subset of two expiries: it is 0.52 of total volume in natural gas and 0.54 in "
            f"crude, so it would roughly double T in exactly the markets with the deepest "
            f"curves. Q from COT covers all expiries and the denominator must match it.")

    bars = cotdata.get_prices(symbol, adjustment="unadj", volume=series)
    if bars is None or bars.empty or "Volume" not in bars.columns:
        return pd.Series(dtype="float64")
    v = pd.to_numeric(bars["Volume"], errors="coerce").replace(0, np.nan).dropna()
    v.index = pd.to_datetime(v.index).astype("datetime64[ns]")
    return v.astype("float64").sort_index()


def _returns(symbol: str) -> pd.Series:
    import cotdata

    px = cotdata.get_prices(symbol, adjustment=RETURN_ADJUSTMENT)
    if px is None or px.empty:
        return pd.Series(dtype="float64")
    s = pd.to_numeric(px["Close"], errors="coerce").dropna()
    s.index = pd.to_datetime(s.index).astype("datetime64[ns]")
    s = s.astype("float64").sort_index()
    # Mask returns touching a non-positive close, for the reason in riskunits: crude really
    # did settle below zero and a percentage return across that is undefined.
    nonpos = s <= 0
    return s.pct_change().replace([np.inf, -np.inf], np.nan) \
            .where(~(nonpos | nonpos.shift(fill_value=False)))


def adv_series(symbol: str, *, window: int = DEFAULT_ADV_WINDOW,
               min_periods: int = DEFAULT_MIN_PERIODS,
               series: str = VOLUME_SERIES) -> pd.Series:
    """Trailing average daily volume. Point-in-time: the value at `t` uses only `t` and
    earlier, so joining it as-of a report date introduces no lookahead."""
    v = _raw_volume(symbol, series)
    if v.empty:
        return v
    return v.rolling(window, min_periods=min_periods).mean()


def stress_adv_series(symbol: str, *, lookback: int = DEFAULT_STRESS_LOOKBACK,
                      decile: float = STRESS_DECILE,
                      min_periods: int = DEFAULT_STRESS_MIN_PERIODS,
                      series: str = VOLUME_SERIES) -> pd.Series:
    """§A.5's `V_stress`: median volume on the worst decile of return days.

    Both the decile threshold and the median are trailing over `lookback`, so the set of
    "worst days" at date `t` is the set that was knowable at `t`. Computing the threshold
    over the full sample would be a subtle lookahead: it would let a market's worst days be
    defined by a crash that had not happened yet.
    """
    v = _raw_volume(symbol, series)
    if v.empty:
        return v
    r = _returns(symbol).reindex(v.index)
    threshold = r.rolling(lookback, min_periods=lookback // 4).quantile(decile)
    return v.where(r <= threshold).rolling(lookback, min_periods=min_periods).median()


def add_volume(frame: pd.DataFrame, *, on: str = "report_date",
               window: int = DEFAULT_ADV_WINDOW,
               stress_lookback: int = DEFAULT_STRESS_LOOKBACK,
               max_staleness_days: int = DEFAULT_MAX_STALENESS_DAYS,
               series: str = VOLUME_SERIES) -> pd.DataFrame:
    """As-of join both denominators onto a frame carrying `symbol` and a date column.

    Rows with no symbol, no volume history, or nothing within `max_staleness_days` get null
    denominators rather than being dropped, which is the rule the whole layer follows.
    """
    required = {"symbol", on}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise VolumeError(
            f"missing columns {missing}. Volume joins on a symbol, so run "
            f"ContractMaster.annotate first.")
    if frame.empty:
        return frame.assign(**{
            c: pd.Series(dtype="datetime64[ns]" if c == "volume_date" else "float64")
            for c in VOLUME_COLUMNS})

    out = frame.copy()
    out[on] = pd.to_datetime(out[on]).astype("datetime64[ns]")
    adv = pd.Series(float("nan"), index=out.index, dtype="float64")
    stress = pd.Series(float("nan"), index=out.index, dtype="float64")
    vdate = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    tol = pd.Timedelta(days=max_staleness_days)

    for sym, idx in out.groupby("symbol", dropna=True, sort=False).groups.items():
        calm = adv_series(str(sym), window=window, series=series).dropna()
        if calm.empty:
            continue
        hot = stress_adv_series(str(sym), lookback=stress_lookback, series=series)
        right = pd.DataFrame({"_d": calm.index, "_adv": calm.to_numpy(),
                              "_stress": hot.reindex(calm.index).to_numpy()})
        want = out.loc[idx, [on]].sort_values(on)
        merged = pd.merge_asof(want, right, left_on=on, right_on="_d",
                               direction="backward", tolerance=tol)
        merged.index = want.index
        adv.loc[merged.index] = merged["_adv"].to_numpy()
        stress.loc[merged.index] = merged["_stress"].to_numpy()
        vdate.loc[merged.index] = merged["_d"].to_numpy()

    out["adv"] = adv
    out["adv_stress"] = stress
    out["volume_date"] = vdate
    out["volume_staleness_days"] = (out[on] - out["volume_date"]).dt.days
    return out


def volume_coverage(with_volume: pd.DataFrame) -> pd.Series:
    """Why rows have no denominator, counted. Meant to be printed beside any `T` table."""
    if with_volume.empty:
        return pd.Series(dtype="int64")
    no_symbol = with_volume["symbol"].isna()
    no_adv = ~no_symbol & with_volume["adv"].isna()
    return pd.Series({
        "with_volume": int(with_volume["adv"].notna().sum()),
        "no_symbol": int(no_symbol.sum()),
        "no_volume_within_tolerance": int(no_adv.sum()),
        "with_stress_volume": int(with_volume["adv_stress"].notna().sum()),
        "total": len(with_volume),
    })
