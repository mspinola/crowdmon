"""When does systematic capital become a forced seller? Appendix §A.7, module spec §9.3.

§A.7 models systematic position size as

    q_i = s_i(F) . (sigma_target / sigma_i) . lambda(Sigma) . A

and the presence of `A`, estimated aggregate CTA capital, is why the whole section was filed
as blocked on a replication model nobody has built. **Most of §A.7 does not need `A`.**

`A`, `sigma_target` and `lambda(Sigma)` are positive scalars. They do not move where the
signal crosses zero, and they cancel out of a proportional response. So:

| §A.7 output | needs | this module |
|---|---|---|
| trigger price `F* = F_{t-k}` | prices | **built** |
| volatility trigger `dq/q = 1 - sigma_0/sigma_1` | sigma | **built**, unit elasticity |
| forced flow `Q*` | `A`, **or the observed position** | **built**, from COT |

The last row is the point. The replication model exists to *estimate other people's
positions*, and COT reports them weekly. Multiplying an observed position by a proportional
response needs no capital estimate at all.

**What this module deliberately does not contain: the fitted replication model.** Choosing the
lookback blend and calibrating it is a search, and npf's governance requires every variant,
including discards, to enter a `SearchSpaceLog` whose count feeds the denominator. Nothing
here is fitted: the lookbacks are §A.7's stated `{20, 60, 250}` and the blend is unweighted.

**The one thing genuinely unavailable** is module spec §9.2's first calibration target, a
regression of modelled returns on SG Trend / BTOP50 with an R2 of 0.6-0.8. Those index returns
are not in this workspace. Target 2, reproducing the observed Managed Money panel, is available
and is the better test for this purpose anyway.

## The price series, measured

`F* = F_{t-k}` is a price LEVEL and the useful output is "how far below spot", a RATIO. Those
want different things, and the store is unforgiving about it:

| | `backadj` vs `propadj` |
|---|---|
| agreement on the signal's SIGN | **99.4%** (min 97.1%, NG at 250d) |
| disagreement on trigger distance, p95 at 250d | cocoa **420pp**, soybeans 336pp, milk 397pp, gold 31pp |

The sign barely cares which series it reads. The distance cares enormously, because additive
back-adjustment inflates historical levels and `F_{t-k}/F_t` is a ratio of them. Same failure
as `notional`, in a fourth place. This module uses `propadj` and refuses the rest.

`propadj` is anchored so the most recent segment carries actual prices (verified: its last
close equals the unadjusted last close to a ratio of 1.000000 on GC, CL, ZS and NG), so `F*`
comes out directly in tradeable terms with no conversion.

## The blended trigger has a closed form

§A.7 says "for smoothed or blended signals, solve `s_i(F*) = 0` numerically". For an ODD
number of equally weighted sign lookbacks it does not need solving: `s` steps by `2/n` at each
`F_{t-k}` and crosses zero exactly at their **median**. Verified. `blended_trigger` returns the
median and `solve_trigger` is available for a different squash where the closed form does not
hold.

## What these numbers are, and are not

The flows below are **upper bounds on trend-driven flow**, because they apply the response to
the whole Managed Money position and spec §11.2 is explicit that Managed Money blends CTAs,
discretionary macro and risk parity. The trend-following fraction is not estimated here and
would need the calibration above. A reader who treats these as point estimates will overstate
them by whatever that fraction is.

Module spec §9.4's standing caution applies to everything here: the model describes *consensus*
positioning, so trading it directly means joining the crowded trade the system exists to warn
about.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: §A.7's stated lookbacks. Configured, not fitted: changing them is a search and belongs in
#: a SearchSpaceLog rather than in a default.
TSMOM_LOOKBACKS = (20, 60, 250)

#: The only series whose price ratios are real. See the module docstring.
SIGNAL_ADJUSTMENT = "propadj"

#: Columns ``add_triggers`` adds.
TRIGGER_COLUMNS = ["spot", "signal", "trigger_blend", "trigger_blend_pct",
                   "net_contracts", "flow_to_flat", "vol_double_flow"]


class TriggerError(ValueError):
    """The inputs cannot support a trigger estimate."""


def trend_signal(prices: pd.Series, *, lookbacks=TSMOM_LOOKBACKS) -> pd.Series:
    """`s` in [-1, 1]: the unweighted mean of `sign(F_t - F_{t-k})` over the lookbacks."""
    prices = pd.to_numeric(prices, errors="coerce").dropna()
    parts = [np.sign(prices - prices.shift(k)) for k in lookbacks]
    return pd.concat(parts, axis=1).mean(axis=1)


def trigger_prices(prices: pd.Series, *, lookbacks=TSMOM_LOOKBACKS) -> dict[int, float]:
    """`F* = F_{t-k}` per lookback, as of the last observation. Price levels."""
    prices = pd.to_numeric(prices, errors="coerce").dropna()
    if len(prices) <= max(lookbacks):
        raise TriggerError(
            f"need more than {max(lookbacks)} observations for the longest lookback, "
            f"got {len(prices)}.")
    # iloc[-1 - k], NOT iloc[-k]. `trend_signal` compares against `prices.shift(k)`, whose
    # last value is `prices.iloc[-1 - k]`, so `iloc[-k]` is one bar adrift and the trigger
    # stops being the price the signal actually flips at. It is a one-bar error that reads
    # as plausible and inverts the answer: on soybeans it put the trigger 0.7% ABOVE spot
    # while the signal read +0.33, which says spot is above the median lookback price.
    # `test_the_trigger_is_consistent_with_the_signal_it_derives_from` is what caught it.
    return {int(k): float(prices.iloc[-1 - k]) for k in lookbacks}


def blended_trigger(prices: pd.Series, *, lookbacks=TSMOM_LOOKBACKS) -> float:
    """The price at which the blended signal crosses zero.

    Closed form for an odd, equally weighted sign blend: the median of the individual
    triggers. `s` steps by `2/n` at each `F_{t-k}`, so it changes sign exactly there.
    """
    triggers = trigger_prices(prices, lookbacks=lookbacks)
    if len(triggers) % 2 == 0:
        raise TriggerError(
            f"an even number of equally weighted lookbacks ({len(triggers)}) leaves `s` "
            f"passing through zero on a flat step rather than crossing it, so the trigger "
            f"is an interval and not a price. Use an odd count, or solve_trigger with a "
            f"squash that is strictly monotonic.")
    return float(np.median(list(triggers.values())))


def solve_trigger(prices: pd.Series, signal_fn, *, lo: float, hi: float,
                  tolerance: float = 1e-6, max_iter: int = 200) -> float:
    """§A.7's numerical path, for a squash where the median closed form does not hold.

    `signal_fn(price)` returns the blended signal if the last close were `price`. Bisection
    rather than a root finder, because the sign blend is a step function and a derivative
    method has nothing to work with.
    """
    f_lo, f_hi = signal_fn(lo), signal_fn(hi)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if np.sign(f_lo) == np.sign(f_hi):
        raise TriggerError(
            f"the signal does not change sign between {lo} and {hi} "
            f"(s={f_lo:+.3f} and s={f_hi:+.3f}), so there is no trigger in that bracket.")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = signal_fn(mid)
        if hi - lo < tolerance:
            return float(mid)
        if np.sign(f_mid) == np.sign(f_lo):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def vol_trigger(sigma_now: float, sigma_stressed: float) -> float:
    """`dq/q = 1 - sigma_0/sigma_1`: the fraction of a position vol targeting forces out.

    Unit elasticity, `d(log q)/d(log sigma) = -1`, so this needs no capital estimate, no
    target volatility and no portfolio scaling. **It has no reference to price direction at
    all**, which is §A.7's formal content for "a violent up-day can force liquidation just as
    a down-day can".

    Negative when volatility FALLS, which is a forced buyer rather than a forced seller and
    is returned rather than clipped: the same event runs both ways.
    """
    if sigma_now is None or sigma_stressed is None:
        return float("nan")
    if not (sigma_now > 0 and sigma_stressed > 0):
        raise TriggerError(
            f"volatilities must be positive, got {sigma_now!r} and {sigma_stressed!r}.")
    return 1.0 - (sigma_now / sigma_stressed)


def forced_flow(position, response) -> float:
    """Contracts forced by a proportional response applied to an OBSERVED position.

    This is where `A` would have been needed and is not: the position comes from COT rather
    than from a capital estimate. Returns a magnitude, since `Q_sell` and `Q_buy` are kept
    apart everywhere else in this package.
    """
    return np.abs(pd.to_numeric(pd.Series([position]), errors="coerce").iloc[0]
                  if np.isscalar(position) else position) * np.abs(response)


def add_triggers(frame: pd.DataFrame, *, lookbacks=TSMOM_LOOKBACKS,
                 vol_multiple: float = 2.0, adjustment: str = SIGNAL_ADJUSTMENT,
                 sigma_window: int = 63) -> pd.DataFrame:
    """Attach trigger prices and forced-flow bounds to a panel carrying positions.

    Needs `symbol`, `long_contracts` and `short_contracts`. Intended for the Managed Money
    rows of an annotated panel, though it imposes no category filter: applying it to
    Producer/Merchant is meaningful only if you believe hedgers run trend rules, and that is
    the caller's judgement to make explicitly.

    `vol_double_flow` is the flow a `vol_multiple`-fold rise in volatility forces. At the
    default of 2.0 that is exactly half the position, by unit elasticity.
    """
    if adjustment != SIGNAL_ADJUSTMENT:
        raise TriggerError(
            f"refusing adjustment={adjustment!r}. Only {SIGNAL_ADJUSTMENT!r} carries real "
            f"price RATIOS, and the trigger's useful form is a distance from spot. Signal "
            f"SIGN agrees 99.4% across series so it barely matters, but the distance is "
            f"wrong by up to 420 percentage points on cocoa at 250 days under 'backadj', "
            f"for the same reason notional refuses it.")
    required = {"symbol", "long_contracts", "short_contracts"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise TriggerError(f"missing columns {missing}. Run ContractMaster.annotate first.")
    if frame.empty:
        return frame.assign(**{c: pd.Series(dtype="float64") for c in TRIGGER_COLUMNS})

    import cotdata

    out = frame.copy()
    out["net_contracts"] = (pd.to_numeric(out["long_contracts"], errors="coerce")
                            - pd.to_numeric(out["short_contracts"], errors="coerce"))
    spot, signal, trig, sigma = ({} for _ in range(4))
    for sym in out["symbol"].dropna().unique():
        px = cotdata.get_prices(str(sym), adjustment=adjustment)
        if px is None or px.empty:
            continue
        close = pd.to_numeric(px["Close"], errors="coerce").dropna()
        if len(close) <= max(lookbacks):
            continue
        nonpos = close <= 0
        returns = close.pct_change().replace([np.inf, -np.inf], np.nan) \
                       .where(~(nonpos | nonpos.shift(fill_value=False)))
        spot[sym] = float(close.iloc[-1])
        signal[sym] = float(trend_signal(close, lookbacks=lookbacks).iloc[-1])
        trig[sym] = blended_trigger(close, lookbacks=lookbacks)
        sigma[sym] = float(returns.rolling(sigma_window).std().iloc[-1])

    out["spot"] = out["symbol"].map(spot)
    out["signal"] = out["symbol"].map(signal)
    out["trigger_blend"] = out["symbol"].map(trig)
    out["sigma_daily"] = out["symbol"].map(sigma)
    out["trigger_blend_pct"] = (out["trigger_blend"] / out["spot"] - 1.0) * 100.0
    # Flow to flatten the trend component. An UPPER BOUND: it assumes the whole position is
    # trend-driven, and spec §11.2 says Managed Money is not.
    out["flow_to_flat"] = out["net_contracts"].abs()
    out["vol_double_flow"] = out["net_contracts"].abs() * abs(
        vol_trigger(1.0, float(vol_multiple)))
    return out


def trigger_block(row, *, kappa: float = 0.2, y: float = 0.75) -> str:
    """Module spec §9.3's output block for one market, rendered.

    The block the spec calls "the deliverable": positioning, the trigger level, the forced
    supply, what it is in days of volume, and what it costs. Every input is now available,
    §A.5 having supplied the last two.
    """
    from ..core.impact import square_root_impact

    net = row.get("net_contracts")
    adv = row.get("adv")
    sigma = row.get("sigma_daily")
    flow = row.get("flow_to_flat")
    days = (flow / (kappa * adv)) if adv and adv > 0 and pd.notna(flow) else float("nan")
    cost = square_root_impact(sigma, flow, adv, y=y) if adv and adv > 0 else float("nan")
    vol_flow = row.get("vol_double_flow")
    return "\n".join([
        f"market: {row.get('symbol')} ({row.get('market_name', '')})".rstrip(" ("),
        f"  managed money net:      {net:+,.0f} contracts",
        f"  spot:                   {row.get('spot'):,.2f}",
        f"  blended signal:         {row.get('signal'):+.2f}",
        f"  flips at:               {row.get('trigger_blend'):,.2f} "
        f"({row.get('trigger_blend_pct'):+.1f}% from spot)",
        f"  forced supply on flip:  {flow:,.0f} contracts = {days:.1f} days ADV "
        f"at {kappa:.0%} participation",
        f"  est. impact:            {cost * 1e4:,.0f} bps",
        f"  vol-shock sensitivity:  a 2x volatility rise forces {vol_flow:,.0f} contracts, "
        f"independent of price",
        "  NOTE: flows are upper bounds. They apply the response to the whole Managed Money "
        "position,",
        "  and the trend-following fraction of that category is not estimated here.",
    ])
