"""Exit cost for futures: the square-root law and Amihud, joined to real markets.

`core.impact` holds the two formulas, which know nothing about contracts. This module knows
where the inputs come from, and the one thing that has to be got right is a unit conversion
the formulas cannot check for themselves.

**What this is NOT.** It is not the composite's illiquidity term. Appendix §A.9 defines
`I = pct(T_eff)`, a percentile of days-to-liquidate, and `composite.py` implements that.
The square-root law is §A.5's *cost of forcing the exit*, a different quantity answering a
different question, and it is reported beside `T` rather than inside `D`. Two markets can
share a days-to-liquidate and differ by a factor of five in what leaving costs, because the
cost carries `sigma` and the duration does not.

**The multiplier is the trap.** `square_root_impact` takes `Q/V`, contracts over contracts,
so it needs no multiplier and cannot be broken by one. `amihud` takes a real currency amount,
so it needs `volume x price x point_value`, and dropping the multiplier leaves a series that
is still positive, still the right general size, and simply the wrong ordering:

| | rank correlation to the correct figure | markets moving >5 places |
|---|---|---|
| Amihud without the multiplier | **0.500** | **8 of 25** |

Cocoa (multiplier 10) reads 20th of 25 without it and 5th with it. RBOB gasoline (multiplier
42,000, quoted in dollars per gallon) reads illiquid without it and is among the most liquid
markets in the set. This module therefore refuses to compute Amihud from a frame with no
`point_value`, rather than computing something plausible.

**Sigma comes from `riskunits.sigma_series`**, which means `propadj`, for every reason set out
there. It is reused rather than recomputed so there is one implementation of the
non-positive-close masking to correct if it is ever wrong again.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.impact import DEFAULT_Y, ImpactError, amihud, square_root_impact
from .riskunits import DEFAULT_MIN_PERIODS, DEFAULT_VOL_WINDOW, RISK_ADJUSTMENT, sigma_series
from .volume import DEFAULT_MAX_STALENESS_DAYS, VOLUME_SERIES

#: Columns ``add_impact`` adds.
IMPACT_COLUMNS = ["sigma_daily", "impact_sell", "impact_buy", "impact_sell_bps",
                  "impact_buy_bps", "adv_usd", "amihud", "impact_date"]

#: Amihud's trailing window. One year, matching the calm ADV baseline it sits beside.
DEFAULT_AMIHUD_WINDOW = 252
DEFAULT_AMIHUD_MIN_PERIODS = 60


def _dollar_volume(symbol: str, point_value: float) -> pd.Series:
    """Daily traded value: contracts x price x multiplier. All three, or the answer is wrong.

    Uses UNADJUSTED prices, because this is a currency amount and only `unadj` carries
    tradeable price levels. Same rule as `notional`, and the same reason.
    """
    import cotdata

    bars = cotdata.get_prices(symbol, adjustment="unadj", volume=VOLUME_SERIES)
    if bars is None or bars.empty or "Volume" not in bars.columns:
        return pd.Series(dtype="float64")
    v = pd.to_numeric(bars["Volume"], errors="coerce").replace(0, np.nan)
    px = pd.to_numeric(bars["Close"], errors="coerce")
    dv = (v * px.abs() * float(point_value)).dropna()
    dv.index = pd.to_datetime(dv.index).astype("datetime64[ns]")
    return dv.astype("float64").sort_index()


def amihud_series(symbol: str, point_value: float, *,
                  window: int = DEFAULT_AMIHUD_WINDOW,
                  min_periods: int = DEFAULT_AMIHUD_MIN_PERIODS) -> pd.Series:
    """Trailing Amihud illiquidity for one market. Requires the contract multiplier."""
    if point_value is None or not np.isfinite(float(point_value)) or float(point_value) <= 0:
        raise ImpactError(
            f"{symbol}: refusing to compute Amihud with point_value={point_value!r}. It "
            f"needs a real currency amount, so volume x price x MULTIPLIER. Dropping the "
            f"multiplier still produces a plausible-looking series and simply the wrong "
            f"ordering: rank correlation 0.500 against the correct figure, 8 of 25 markets "
            f"moving more than five places. Run ContractMaster.annotate first.")
    import cotdata

    px = cotdata.get_prices(symbol, adjustment=RISK_ADJUSTMENT)
    if px is None or px.empty:
        return pd.Series(dtype="float64")
    close = pd.to_numeric(px["Close"], errors="coerce").dropna()
    close.index = pd.to_datetime(close.index).astype("datetime64[ns]")
    close = close.sort_index()
    nonpos = close <= 0
    returns = close.pct_change().replace([np.inf, -np.inf], np.nan) \
                   .where(~(nonpos | nonpos.shift(fill_value=False)))
    dv = _dollar_volume(symbol, point_value)
    if dv.empty:
        return pd.Series(dtype="float64")
    return amihud(returns, dv.reindex(returns.index),
                  window=window, min_periods=min_periods)


def add_impact(frame: pd.DataFrame, *, on: str = "report_date", y: float = DEFAULT_Y,
               vol_window: int = DEFAULT_VOL_WINDOW,
               vol_min_periods: int = DEFAULT_MIN_PERIODS,
               amihud_window: int = DEFAULT_AMIHUD_WINDOW,
               max_staleness_days: int = DEFAULT_MAX_STALENESS_DAYS) -> pd.DataFrame:
    """Add exit-cost columns to a frame already carrying `q_sell`/`q_buy` and `adv`.

    Needs `symbol`, `point_value` (from `ContractMaster.annotate`), `adv` (from
    `volume.add_volume`) and the two `q_` magnitudes (from `fragility`). Rows missing any of
    them get nulls rather than being dropped, the rule the whole layer follows.

    `impact_*` are fractions of price; `*_bps` are the same numbers in basis points, because
    an exit cost is read in bps by everyone who reads one.
    """
    required = {"symbol", "point_value", "adv", "q_sell", "q_buy", on}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ImpactError(
            f"missing columns {missing}. Impact sits on top of the whole layer: "
            f"ContractMaster.annotate supplies symbol and point_value, volume.add_volume "
            f"supplies adv, and fragility supplies q_sell and q_buy.")
    if frame.empty:
        return frame.assign(**{
            c: pd.Series(dtype="datetime64[ns]" if c == "impact_date" else "float64")
            for c in IMPACT_COLUMNS})

    out = frame.copy()
    out[on] = pd.to_datetime(out[on]).astype("datetime64[ns]")
    sigma = pd.Series(float("nan"), index=out.index, dtype="float64")
    lam = pd.Series(float("nan"), index=out.index, dtype="float64")
    advusd = pd.Series(float("nan"), index=out.index, dtype="float64")
    when = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    tol = pd.Timedelta(days=max_staleness_days)

    for sym, idx in out.groupby("symbol", dropna=True, sort=False).groups.items():
        pv = pd.to_numeric(out.loc[idx, "point_value"], errors="coerce").dropna()
        if pv.empty:
            continue
        sig = sigma_series(str(sym), RISK_ADJUSTMENT, "Close",
                           vol_window, vol_min_periods).dropna()
        if sig.empty:
            continue
        lam_s = amihud_series(str(sym), float(pv.iloc[0]), window=amihud_window).dropna()
        dv_s = _dollar_volume(str(sym), float(pv.iloc[0])) \
            .rolling(DEFAULT_AMIHUD_WINDOW, min_periods=DEFAULT_AMIHUD_MIN_PERIODS).mean()
        right = pd.DataFrame({"_d": sig.index, "_sig": sig.to_numpy(),
                              "_lam": lam_s.reindex(sig.index).to_numpy(),
                              "_dv": dv_s.reindex(sig.index).to_numpy()})
        want = out.loc[idx, [on]].sort_values(on)
        merged = pd.merge_asof(want, right, left_on=on, right_on="_d",
                               direction="backward", tolerance=tol)
        merged.index = want.index
        sigma.loc[merged.index] = merged["_sig"].to_numpy()
        lam.loc[merged.index] = merged["_lam"].to_numpy()
        advusd.loc[merged.index] = merged["_dv"].to_numpy()
        when.loc[merged.index] = merged["_d"].to_numpy()

    out["sigma_daily"] = sigma
    out["adv_usd"] = advusd
    out["amihud"] = lam
    out["impact_date"] = when

    adv = pd.to_numeric(out["adv"], errors="coerce")
    for side in ("sell", "buy"):
        q = pd.to_numeric(out[f"q_{side}"], errors="coerce")
        # Q and V both in CONTRACTS. The ratio is unit-free, so this would give the same
        # answer in notional or in risk units, but only if BOTH are converted.
        out[f"impact_{side}"] = square_root_impact(sigma, q, adv, y=y)
        out[f"impact_{side}_bps"] = out[f"impact_{side}"] * 1e4
    return out


def impact_coverage(with_impact: pd.DataFrame) -> pd.Series:
    """Why rows have no exit cost, counted. Print it beside any impact table."""
    if with_impact.empty:
        return pd.Series(dtype="int64")
    no_symbol = with_impact["symbol"].isna()
    no_sigma = ~no_symbol & with_impact["sigma_daily"].isna()
    no_adv = ~no_symbol & with_impact["sigma_daily"].notna() \
        & pd.to_numeric(with_impact["adv"], errors="coerce").isna()
    return pd.Series({
        "with_impact": int(with_impact["impact_sell"].notna().sum()),
        "no_symbol": int(no_symbol.sum()),
        "no_volatility": int(no_sigma.sum()),
        "no_volume": int(no_adv.sum()),
        "with_amihud": int(with_impact["amihud"].notna().sum()),
        "total": len(with_impact),
    })
