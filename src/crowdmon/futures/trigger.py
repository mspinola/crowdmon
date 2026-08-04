"""The trigger block: at what price does forced flow arrive, and what does it cost?

Module spec §9.3, appendix §A.7. The spec calls this block "the deliverable", because it is
the first output that combines positioning extremity, holder fragility, a specific price
level, and a liquidity-denominated cost, rather than measuring one of them.

    market:                GC (GOLD - COMMODITY EXCHANGE INC.)
    as of:                 2026-07-31
    spot:                  4,107.00
    observed pool:         119,795 contracts   (78% pctile of own 3y)
    fragility (Phi):       0.468
     20d flips at:           4,186.58   (+1.9% from spot, currently short, flips up)
     60d flips at:           4,670.02   (+13.7% from spot, currently short, flips up)
    250d flips at:           3,554.87   (-13.4% from spot, currently long, flips down)
    flow if pool close   :    119,795 contracts = 2.5 days ADV at kappa 0.2, impact 80 bps
    flow if pool reverse :    239,590 contracts = 5.0 days ADV at kappa 0.2, impact 113 bps
    vol now:               24.0% annualised (1.51% daily)
    vol shock +5 pts:      forces -17% of the position, independent of price direction

**The horizons disagree, and that is the point.** Gold's 20- and 60-day signals are short and
flip UP; its 250-day is long and flips DOWN. "The trend book in gold" is not one pool with one
trigger, and a single-horizon reading hides that.

## The pool is OBSERVED, not modelled, and that is a deliberate departure

§A.7 estimates forced flow from a replicated CTA book,
`Q* = A . (sigma_target/sigma) . delta_s`, where `A` is aggregate systematic capital
calibrated against SG Trend or BTOP50. **Neither index is in this workspace**, so `A` would
have to be guessed, and a guessed `A` multiplies every flow and impact figure this block
prints.

This module uses the **observed Managed Money net position** from COT instead. That is
better than a calibrated estimate rather than a fallback from one: COT measures the position
directly and weekly, where the replication model infers it from index returns.

It also removes a governance problem. Module spec §9.4's standing caution is that the CTA
replication model "must not become a trading signal by drift", because it is calibrated to
reproduce consensus positioning and trading it means joining the crowded trade the system
exists to warn about. **There is no replication model here to drift.** What is printed is a
price at which an observed pool becomes a forced seller, not a view about where price goes,
and §A.10 applies unchanged: every output is a statement about tail shape.

## The trigger price, and the anchor hazard in computing it

§A.7: for a simple momentum signal `s = sign(F_t - F_{t-k})`, the flip condition is immediate,
`F* = F_{t-k}`. **The price at which a large pool becomes a forced seller is simply the price
of k days ago.** No solver, no calibration.

The subtlety is which price series, and it bites historically rather than live.

Momentum is a statement about **returns**, so the series must be `propadj`: `unadj` fabricates
a jump at every roll and would invent signal flips that never happened, and `backadj` levels
are not prices at all. But `propadj` is anchored at the **end of the series** (measured: the
`propadj`/`unadj` ratio is exactly 1.0000 on the latest bar and 1.89 for gold in 2002), so
`propadj[t-k]` is a tradeable level only when `t` is the last bar.

Computed as-of any earlier date it is not, because the anchor sits in that date's future. So
the trigger is formed as

    F* = spot_unadj[t] . propadj[t-k] / propadj[t]

which is invariant to where the anchor sits, since a common scale factor cancels in the
ratio. Live it reduces to `propadj[t-k]` exactly, which is why the naive version looks
correct until someone runs it over history.

**Only the simple sign signal is exact.** §A.7 says a smoothed or blended signal needs
`s(F*) = 0` solved numerically, and this module does not do that. What it prints is the flip
level for one lookback at a time, which is what the spec's own block shows.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg
from .impact import square_root_impact

#: §A.7's TSMOM lookbacks: "a squashed blend of time-series momentum over {20, 60, 250} days".
#: Reported separately rather than blended, because the blend needs a numerical solve and
#: because the horizons routinely disagree, which is itself informative.
DEFAULT_LOOKBACKS = (20, 60, 250)

#: The price series momentum must be computed on. See the module docstring.
TRIGGER_ADJUSTMENT = "propadj"

#: The category whose observed position is treated as the forceable pool.
DEFAULT_POOL_CATEGORY = "managed_money"


class TriggerError(ValueError):
    """The trigger block cannot be computed as asked."""


def trigger_prices(symbol: str, *, lookbacks=DEFAULT_LOOKBACKS, as_of=None,
                   adjustment: str = TRIGGER_ADJUSTMENT) -> pd.DataFrame:
    """`F* = F_{t-k}` per lookback, expressed in tradeable price units.

    Returns one row per lookback with the flip level, the move from spot required to reach
    it, and the current sign of the signal. A signal that is already long flips **down**; one
    already short flips **up**, and the sign column is what says which.
    """
    import cotdata

    if adjustment != TRIGGER_ADJUSTMENT:
        raise TriggerError(
            f"momentum needs {TRIGGER_ADJUSTMENT!r}, got {adjustment!r}. `unadj` fabricates a "
            f"jump at every roll and would invent signal flips; `backadj` levels are not "
            f"prices. See this module's docstring.")

    def _close(adj: str) -> pd.Series:
        """`Close` or a `TriggerError`, never a bare `KeyError`.

        A symbol the price store does not carry returns an empty frame with no columns, so
        the `["Close"]` access raised `KeyError('Close')` and killed the caller mid-run.
        That matters because `add_trigger_distance` iterates over whatever symbols a frame
        holds, and the coverage ladder is explicit that markets die at the price join: one
        unresolvable symbol should null one row, not abort the panel.
        """
        frame = cotdata.get_prices(symbol, adjustment=adj)
        if frame is None or frame.empty or "Close" not in frame.columns:
            raise TriggerError(
                f"no {adj!r} prices for {symbol!r}; the store has no usable Close series. "
                f"A market can reach this legitimately by having a contract spec and no "
                f"stored price tier, so callers scanning a panel should treat it as a null "
                f"row rather than a failure.")
        return frame["Close"].dropna()

    ratio_series = _close(adjustment)
    level_series = _close("unadj")
    if as_of is not None:
        stamp = pd.Timestamp(as_of)
        ratio_series = ratio_series[ratio_series.index <= stamp]
        level_series = level_series[level_series.index <= stamp]
    if ratio_series.empty or level_series.empty:
        raise TriggerError(f"no prices for {symbol!r} at or before {as_of}")

    spot = float(level_series.iloc[-1])
    ratio_now = float(ratio_series.iloc[-1])

    rows = []
    for k in lookbacks:
        if len(ratio_series) <= k:
            rows.append({"lookback_days": k, "flip_price": None, "move_from_spot": None,
                         "signal": None, "as_of": ratio_series.index[-1]})
            continue
        ratio_then = float(ratio_series.iloc[-1 - k])
        # Anchor-invariant: a common scale factor cancels in the ratio, so this is correct
        # whether `propadj` is anchored at this bar or at the end of the full series.
        flip = spot * ratio_then / ratio_now
        rows.append({
            "lookback_days": k,
            "flip_price": flip,
            "move_from_spot": flip / spot - 1.0,
            # sign of (F_t - F_{t-k}) in return space, which is the signal itself
            "signal": 1 if ratio_now > ratio_then else (-1 if ratio_now < ratio_then else 0),
            "as_of": ratio_series.index[-1],
        })
    out = pd.DataFrame(rows)
    out.attrs["spot"] = spot
    out.attrs["symbol"] = symbol
    return out


#: Trading days per year, for converting a daily sigma to the annualised units a vol shock
#: is quoted in. "+5 vol points" universally means annualised; applied to a DAILY sigma of
#: 1.5% it would be a 4x move and every market would print the same near-total liquidation,
#: which is how this was caught.
TRADING_DAYS = 252


def annualise(sigma_daily: float) -> float:
    """Daily sigma to annualised, `sigma . sqrt(252)`."""
    return float(sigma_daily) * (TRADING_DAYS ** 0.5)


def vol_shock_reduction(sigma_now: float, sigma_shocked: float) -> float:
    """§A.7: `delta_q / q = 1 - sigma_0 / sigma_1`, the forced reduction from a vol move.

    Unit-free: both arguments must be in the same units, and the ratio is what matters.
    `trigger_block` passes annualised values, because that is what a "vol point" means.

    Elasticity is exactly **-1** because a vol-targeting book sizes at `target/sigma`, so a
    doubling of volatility forces a 50% cut **with no reference to price direction at all**.
    That is the formal content of "a violent up-day can force liquidation just as a down-day
    can", and it is the channel §A.7 argues carries most of the reflexivity in modern futures.
    """
    if not sigma_now or sigma_now <= 0 or not sigma_shocked or sigma_shocked <= 0:
        raise TriggerError(
            f"volatilities must be positive, got {sigma_now!r} and {sigma_shocked!r}")
    return 1.0 - (sigma_now / sigma_shocked)


#: Columns `add_trigger_distance` adds. Named `trigger_*` rather than `offside_*` because
#: "offside" is a P&L word and this is not P&L: COT gives no entry price, so the distance to
#: a rules-based flip is all that is measurable. A holder can be deeply underwater and
#: nowhere near their trigger, and vice versa.
TRIGGER_DISTANCE_COLUMNS = [
    "trigger_sell_pct", "trigger_sell_sigma", "trigger_sell_k", "trigger_sell_pool_agrees",
    "trigger_buy_pct", "trigger_buy_sigma", "trigger_buy_k", "trigger_buy_pool_agrees",
    "trigger_horizons_disagree",
]


def nearest_trigger(symbol: str, *, sigma_daily: float, pool_net: float | None = None,
                    lookbacks=DEFAULT_LOOKBACKS, as_of=None) -> dict:
    """Distance to the nearest flip that forces flow, per side, in daily sigma.

    **The side convention matches `Q_sell` / `T_sell` / `damage_sell` exactly.** A signal
    currently LONG flips DOWN, and a pool that was long and goes flat or short is a forced
    SELLER, so it lands on the `sell` side. A signal currently SHORT flips UP and is a forced
    BUYER. Getting this backwards would pair a trigger with the opposite side's severity,
    which is the one error here that produces plausible numbers.

    **Sigma is the unit that travels.** A 3% move means nothing across markets: 3% is a
    routine day in natural gas and a large one in 2-year notes. Distance divided by daily
    sigma is "how many ordinary days of movement until the rules fire", which is comparable,
    and the raw percentage is kept beside it because it is what a reader recognises.

    **Both sides usually exist at once, and that is the module's own point rather than a
    defect.** The 20-, 60- and 250-day horizons routinely disagree in sign, measured at
    **27 of 45** markets on 2026-07-28 (`2026-08-04 §D8`). `trigger_horizons_disagree` says
    so per row, because "the trend book in gold" is not one pool with one trigger.

    **The distance carries no price information beyond trailing momentum, and that is an
    identity rather than a measurement.** Since `F* = F_{t-k}`, the move required to reach
    the flip is exactly the `k`-day return that has already happened:

        move_from_spot = F_{t-k}/F_t - 1 = -r_k / (1 + r_k)

    verified to six decimals on every lookback of every market tested (`2026-08-04 §D8`).
    So "how far to the trigger" is "how far it has already come", and this function adds
    **the mapping, not the price**: which pool, on which side, is mechanically forced at that
    level. That is the part positioning data supplies and a chart does not.

    The consequence for the composite is in `composite.damage_block`: because both this and
    `C` are downstream of the same trend, they are correlated (**-0.481** on 2026-07-28), so
    a fourth multiplicand would compound one signal twice.

    Returns nulls rather than raising when a side has no trigger: a market whose every
    horizon is long genuinely has no forced-buy level, and that is an answer.
    """
    if sigma_daily is None or pd.isna(sigma_daily) or float(sigma_daily) <= 0:
        raise TriggerError(
            f"nearest_trigger needs a positive daily sigma for {symbol!r}, got "
            f"{sigma_daily!r}. Sigma is the unit that makes the distance comparable across "
            f"markets; without it there is a percentage and no way to read it. It comes "
            f"from `riskunits.add_risk_units`, so it is not recomputed here: two "
            f"definitions of sigma in one package is how the layer-2 trap started.")

    frame = trigger_prices(symbol, lookbacks=lookbacks, as_of=as_of)
    frame = frame.dropna(subset=["flip_price"])
    sigma = float(sigma_daily)

    def _nearest(signal: int) -> tuple:
        part = frame[frame["signal"] == signal]
        if part.empty:
            return None, None, None
        move = part["move_from_spot"].abs()
        best = move.idxmin()
        pct = float(move.loc[best])
        return pct, pct / sigma, int(part.loc[best, "lookback_days"])

    # signal +1 (long now) flips down -> forced selling; -1 (short now) flips up -> buying
    sell_pct, sell_sigma, sell_k = _nearest(1)
    buy_pct, buy_sigma, buy_k = _nearest(-1)

    # **Does the OBSERVED pool actually sit on the side the signal implies?**
    #
    # This module's departure from §A.7 is that the pool is observed rather than modelled,
    # and a first version of this function then took the side from the price signal alone,
    # which quietly reintroduced the modelled logic it exists to avoid. The signal says what
    # a trend follower WOULD hold; COT says what levered money DOES hold, and measured on
    # 2026-07-28 they agree on only **65.9%** of the 135 (market, horizon) pairs: 64.4% at
    # 20d, 57.8% at 60d, 75.6% at 250d, with ZW, YM and DX opposite on every horizon
    # (`2026-08-04 §D9`).
    #
    # Where they disagree the trigger is still a real price level and the pool it would
    # force is not there. Canadian dollar on that week: the levered book is short 102,495
    # while the 20-day signal is long, so its 2.4-sigma "forced selling" level describes a
    # long book that does not exist. `None` when no pool was supplied, because unknown and
    # disagreeing are different states.
    def _agrees(signal: int) -> bool | None:
        if pool_net is None or pd.isna(pool_net) or float(pool_net) == 0:
            return None
        return (float(pool_net) > 0) == (signal > 0)

    return {
        "symbol": symbol,
        "trigger_sell_pct": sell_pct, "trigger_sell_sigma": sell_sigma,
        "trigger_sell_k": sell_k,
        "trigger_sell_pool_agrees": None if sell_pct is None else _agrees(1),
        "trigger_buy_pct": buy_pct, "trigger_buy_sigma": buy_sigma,
        "trigger_buy_k": buy_k,
        "trigger_buy_pool_agrees": None if buy_pct is None else _agrees(-1),
        "trigger_horizons_disagree": bool(sell_pct is not None and buy_pct is not None),
    }


def add_trigger_distance(frame: pd.DataFrame, *, on: str = "report_date", as_of=None,
                         pool_column: str | None = None,
                         lookbacks=DEFAULT_LOOKBACKS) -> pd.DataFrame:
    """Join `nearest_trigger` onto a frame carrying `symbol` and `sigma_daily`.

    **This is a point-in-time overlay, not a history, and the reason is cost rather than
    correctness.** `trigger_prices` is anchor-invariant and computes correctly as of any past
    date, so a full history is well defined. It is also two price-store reads per
    market-week: across 45 markets and 1,051 weeks that is roughly 95,000 reads against 90
    for one week. So rows on `as_of` get a distance and every other row gets nulls, which is
    stated here and visible in the output rather than discovered.

    `as_of` defaults to the frame's latest date. `sigma_daily` must already be present, from
    `riskunits.add_risk_units`, and is not recomputed: see `nearest_trigger`.

    `pool_column` names the observed net of the forceable category, and supplying it is
    strongly recommended: without it the `*_pool_agrees` flags are null and a reader cannot
    tell whether a trigger describes a book that is actually there. The pool and the signal
    disagree on a third of (market, horizon) pairs (`2026-08-04 §D9`).
    """
    needed = {"symbol", "sigma_daily", on}
    if pool_column:
        needed.add(pool_column)
    missing = sorted(needed - set(frame.columns))
    if missing:
        raise TriggerError(
            f"missing columns {missing}. `symbol` comes from `ContractMaster.annotate` and "
            f"`sigma_daily` from `riskunits.add_risk_units`.")
    out = frame.copy()
    for column in TRIGGER_DISTANCE_COLUMNS:
        out[column] = pd.NA
    if out.empty:
        return out

    out[on] = pd.to_datetime(out[on])
    stamp = out[on].max() if as_of is None else pd.Timestamp(as_of)
    rows = out[on] == stamp
    sigma = pd.to_numeric(out.loc[rows, "sigma_daily"], errors="coerce")

    for sym, idx in out.loc[rows].groupby("symbol", dropna=True, sort=False).groups.items():
        s = sigma.loc[idx].dropna()
        s = s[s > 0]
        if s.empty:
            continue
        pool = None
        if pool_column:
            p = pd.to_numeric(out.loc[idx, pool_column], errors="coerce").dropna()
            pool = float(p.iloc[0]) if not p.empty else None
        try:
            got = nearest_trigger(str(sym), sigma_daily=float(s.iloc[0]), pool_net=pool,
                                  lookbacks=lookbacks, as_of=stamp)
        except TriggerError:
            # A market with too little price history to reach the longest lookback has no
            # trigger, which is a null rather than a failure of the run.
            continue
        for column in TRIGGER_DISTANCE_COLUMNS:
            out.loc[idx, column] = got[column]
    return out


def trigger_block(symbol: str, *, market_row: pd.Series, sigma_daily: float,
                  adv: float, lookbacks=DEFAULT_LOOKBACKS,
                  pool_contracts: float | None = None,
                  kappa: float = cfg.KAPPA, y: float = 0.75,
                  vol_shock_points: float = 0.05,
                  as_of=None) -> dict:
    """Assemble §9.3's block for one market.

    `market_row` carries the positioning context already computed elsewhere: `market_name`,
    `phi`, and optionally `net_contracts` and `net_risk_usd_pct`. `pool_contracts` overrides
    the observed net if a caller wants a different pool.

    **Two flow figures, and neither is chosen for you.** A sign flip takes a signal from `+1`
    to `-1`, so §A.7's `delta_s` is 2 and the modelled flow is a full reversal. Closing the
    position is half that. `flow_close` and `flow_reverse` are both reported because the
    difference is a factor of two on every downstream number and the honest answer depends on
    whether the pool goes flat or goes short.
    """
    triggers = trigger_prices(symbol, lookbacks=lookbacks, as_of=as_of)
    pool = pool_contracts if pool_contracts is not None else market_row.get("net_contracts")
    if pool is None or pd.isna(pool):
        raise TriggerError(
            f"no observed pool for {symbol!r}: pass pool_contracts= or supply "
            f"`net_contracts` on market_row. This module does not model one (see docstring).")
    pool = abs(float(pool))
    spot = triggers.attrs["spot"]

    flows = {}
    for label, size in (("close", pool), ("reverse", 2.0 * pool)):
        flows[label] = {
            "contracts": size,
            "days_adv": (size / (kappa * adv)) if adv and adv > 0 else None,
            "impact_bps": (square_root_impact(sigma_daily, size, adv, y=y) * 1e4
                           if adv and adv > 0 and sigma_daily else None),
        }

    return {
        "symbol": symbol,
        "market_name": market_row.get("market_name"),
        "as_of": triggers["as_of"].iloc[0],
        "spot": spot,
        "pool_contracts": pool,
        "pool_percentile": market_row.get("net_risk_usd_pct"),
        "phi": market_row.get("phi"),
        "sigma_daily": sigma_daily,
        "adv": adv,
        "kappa": kappa,
        "triggers": triggers,
        "flows": flows,
        "sigma_annual": annualise(sigma_daily) if sigma_daily else None,
        # Quoted in ANNUALISED points, the universal convention. Applying them to a daily
        # sigma makes every market print the same near-total liquidation.
        "vol_shock_points": vol_shock_points,
        "vol_shock_reduction": vol_shock_reduction(
            annualise(sigma_daily), annualise(sigma_daily) + vol_shock_points)
        if sigma_daily else None,
    }


def format_block(block: dict) -> str:
    """The block as §9.3 prints it. House style: every input visible beside its result."""
    lines = [f"market:                {block['symbol']} ({block['market_name']})",
             f"as of:                 {pd.Timestamp(block['as_of']).date()}",
             f"spot:                  {block['spot']:,.2f}"]

    pool = f"{block['pool_contracts']:,.0f} contracts"
    if block.get("pool_percentile") is not None and pd.notna(block["pool_percentile"]):
        pool += f"   ({block['pool_percentile']:.0%} pctile of own 3y)"
    lines.append(f"observed pool:         {pool}")
    if block.get("phi") is not None and pd.notna(block["phi"]):
        lines.append(f"fragility (Phi):       {block['phi']:.3f}")

    for row in block["triggers"].itertuples():
        if row.flip_price is None:
            lines.append(f"{row.lookback_days:>3}d signal:           "
                         f"insufficient history")
            continue
        # `signal` is a three-state sign, not a boolean. An exactly flat lookback returns 0
        # and its "flip" is the spot price itself, which is not a level anything crosses.
        # Rendering it as one of the two directions reads as a live trigger 0.0% away.
        if row.signal > 0:
            direction = "long, flips down"
        elif row.signal < 0:
            direction = "short, flips up"
        else:
            direction = "flat, no trigger"
        lines.append(f"{row.lookback_days:>3}d flips at:         {row.flip_price:>10,.2f}   "
                     f"({row.move_from_spot:+.1%} from spot, currently {direction})")

    for label in ("close", "reverse"):
        flow = block["flows"][label]
        days = f"{flow['days_adv']:.1f} days ADV" if flow["days_adv"] else "no volume"
        cost = f"{flow['impact_bps']:.0f} bps" if flow["impact_bps"] else "n/a"
        lines.append(f"flow if pool {label:<8}: {flow['contracts']:>10,.0f} contracts = "
                     f"{days} at kappa {block['kappa']}, impact {cost}")

    if block.get("vol_shock_reduction") is not None:
        pts, annual = block["vol_shock_points"], block["sigma_annual"]
        lines.append(f"vol now:               {annual:.1%} annualised "
                     f"({block['sigma_daily']:.2%} daily)")
        lines.append(f"vol shock +{pts * 100:.0f} pts:      forces "
                     f"{-block['vol_shock_reduction']:.0%} of the position, "
                     f"independent of price direction")
    return "\n".join(lines)
