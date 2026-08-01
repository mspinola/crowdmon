"""Cascade amplification. Appendix §A.8, the last link in the forced-flow chain.

A.5 says what forcing an exit costs, A.7 says where the exit gets forced, and this says what
happens when the cost of the first exit reaches the trigger of the second:

    dF_1     = -l . Q_1                initial liquidation moves price
    Q_2      =  g . |dF_1|             that move triggers further forced selling
    dF_total = -l.Q_1 / (1 - l.g)      the cascade, finite only while l.g < 1

`1/(1 - l.g)` is the output, and its reading is the section's own:

- `l.g << 1`, an orderly repricing. The fundamental news is the story.
- `l.g -> 1`, the cascade dominates. **The exit is the story.**
- `l.g >= 1`, no equilibrium. In practice limits, margin hikes or exhaustion end it, none of
  which this models, so the number is refused rather than printed.

**`g` is not a scalar, and picking a horizon is the error.** The obvious readings both divide
the WHOLE observed net by ONE horizon's trigger distance: a 60-day reading assumes every
holder runs a 60-day system, a nearest-trigger reading assumes every holder runs a 20-day one.
That assumption is what produces the order-of-magnitude disagreement (gold's 20-day trigger is
1.9% away and its 60-day is 13.7%, so `l.g` moves from ~0.06 to ~0.4), and neither is a
defensible reading of a pool the report calls "Managed Money", which spec §11.2 says blends
CTAs, discretionary macro and risk parity.

So `g` here is a **signed staircase over price distance**, evaluated where the cascade is
rather than chosen in advance. The two single-horizon numbers become the all-slow/all-fast
bracket rather than rival answers.

**`g_up` and `g_down` are separate and must never be summed or netted.** Measured across 33
markets in the latest week, **23 (69.7%) have horizons pointing in different directions**:
gold's 20- and 60-day signals are short and flip up while its 250-day is long and flips down.
A rally there forces the short slice to cover, which is buying, and a selloff forces the long
slice to liquidate, which is selling. Two cascades, opposite directions, different distances,
from different slices of one pool. Netting them would report a market with two live cascades
as quieter than one with none, the same class of error `flow.decompose` exists to avoid.

**Locations are observed, heights are not.** The staircase's step positions come from
`trigger_prices` and are measured. Its step heights are the share of the pool trading each
horizon, `w_h`, which nobody knows. A uniform split is the defensible base case precisely
because it is indefensible as an estimate: it asserts no knowledge that does not exist. State
it, sweep it, never fit it. Fitting `w_h` against realised flow would be a search and would
need a `SearchSpaceLog`.

**The heights are constrained even though they are unknown.** The cohorts must reproduce the
observed net. With cohort `h` holding `w_h . P . s_h`:

    net = P . sum(w_h . s_h)     ->     P = |net| / |sum(w_h . s_h)|

so under a uniform split `P = |net| . H / |sum(s)|`. Mixed signs therefore imply a GROSS pool
larger than the net, which is what "fast and slow systems disagree" means in position terms:

| signals | sum | gross pool | per-cohort pool |
|---|---|---|---|
| mixed, one dissenter (GC, CL) | ±1 | **3.0x \\|net\\|** | 1.0x \\|net\\| |
| unanimous (ZN) | ±3 | 1.0x \\|net\\| | **0.33x \\|net\\|** |

Against naively using `|net|` at every step this **cuts the unanimous markets by 3x and leaves
the mixed ones alone**, so it reorders the cross-market ranking rather than rescaling it. Same
class as A20's Amihud-without-the-multiplier.

Gold, computed rather than scaled by hand:

| reading | `l.g` | `1/(1-l.g)` |
|---|---|---|
| 60d, pool = \\|net\\| | 0.049 | 1.05x |
| 20d cohort under the constraint | 0.347 | 1.53x |
| whole 3x gross pool at the near distance | 0.602 | 2.51x |

**`l.g` grows as the SQUARE ROOT of the pool, not linearly**, because `l = I(Q)/Q` falls as
`Q^-1/2` while `g` rises as `Q`. Tripling the pool multiplies `l.g` by 1.7321, which is
`sqrt(3)` to four figures. An earlier hand-scaled version of this table assumed linearity and
put the third row at `l.g = 1.231`, "no equilibrium". That was wrong: nothing at gold crosses
1 today. The constraint still matters (1.53x to 2.51x is a 64% difference in the headline) but
it is not the difference between finite and infinite, and claiming otherwise oversells it.

**`sum(s) == 0` is reachable today, and the parity argument that says otherwise is wrong.**
With three horizons all resolved and non-zero the sum is odd, so it cannot vanish, and a sweep
of 45 markets in the latest week found no case. But the parity that protects it is the count
of CONTRIBUTING signals, not the length of `DEFAULT_LOOKBACKS`, and two ordinary things reduce
that count:

- a **flat** lookback returns `signal = 0`, holds no position and contributes nothing
- an **unresolved** lookback (longer than the price history) returns null

Either one leaves two contributing signals, and `(-1, +1)` sums to zero. A market shorter than
250 days of history, or one exactly flat over a lookback, reaches it without a config change.
Adding a fourth lookback reaches it directly. The guard is load-bearing rather than defensive,
and the sweep's clean result is a fact about 45 mature markets in one week, not a theorem.

**The trend fraction is the caveat this inherits from B8.** Setting `P . mean(s) = net`
attributes the ENTIRE observed net to trend cohorts, and spec §11.2 says Managed Money is not
only CTAs. If only fraction `f` of the net is trend-following, every figure here is overstated
by `1/sqrt(f)`, per the square-root scaling above: at `f = 0.5` gold's whole-gross reading
falls from `l.g = 0.602` to 0.426, and the amplification from 2.51x to 1.74x. That is a real
sensitivity and a milder one than a linear reading would suggest, which is the argument for
reporting `f` rather than assuming it away in either direction. It is an explicit multiplier
in the output rather than an implicit 1.0. Estimating it would be a fit, therefore a search,
therefore out of scope here.

**Which step is the worst is a race, and there is no shortcut for it.** Two wrong answers were
written down before the right one. The first was that amplification grows as a move extends,
because only the fastest slice of the pool is in play near the first trigger; that counts only
the numerator of a ratio. The second was the reverse, that the nearest step is always the
worst, on the reasoning that trigger distances grow faster than the pool accumulates. **That
premise is simply false**: trigger distance is not monotonic in lookback. Latest week,

| | 20d | 60d | 250d |
|---|---|---|---|
| GC | **1.94%** | 13.71% | 13.44% |
| ZC | 4.03% | 11.14% | **3.70%** |
| CL | 19.60% | **13.86%** | 29.51% |

so a 20/60/250 ladder does not sit progressively further out, and the staircase must be sorted
by distance rather than by horizon.

Since `l.g ~ sqrt(Q_cum) / d`, step `i` beats step `i+1` exactly when

    d_(i+1) / d_i  >  sqrt( Q_(i+1) / Q_i )

which under a uniform split is **1.414** at the first gap and **1.225** at the second. The
nearer step wins only when the next trigger is more than 41% further out. **Clustered triggers
are common enough that this is not a corner case**: measured within-direction across 33
markets, 6 of the 33 multi-step staircases have their worst step past the nearest. Currency
crosses are the sharpest, 6E holding two up-triggers at a distance ratio of **1.005**, far
inside the 1.414 the near step would need.

**Which step wins does not depend on the pool size**, which is what makes that countable
without a real net: `l.g ~ sqrt(Q_cum)/d`, so `lg_2/lg_1 = sqrt(2) . d_1/d_2` under a uniform
split and the net cancels. At 6E's ratio the second step's `l.g` is **41% higher** than the
first's whatever the position turns out to be. The amplification LEVELS do depend on the net
and are not quoted here for that reason.

**So the headline is `max` over steps, not the nearest step**, and `headline` computes it.

A caution on reading any of this: the race is only ever run WITHIN a direction. Pooling `up`
and `down` steps into one distance-sorted ladder manufactures counterexamples that are
artifacts of the pooling, because adjacent steps then belong to different cascades. ZC looks
like a middle-step market exactly that way, and is monotone once separated.

**What this emits is therefore not a number.** Per market and direction: the staircase, the
local `l.g` at each step, the amplification at each step, the worst step, and the bracket.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.impact import DEFAULT_Y, square_root_impact

#: Columns of the staircase frame.
STAIRCASE_COLUMNS = ["direction", "lookback_days", "signal", "flip_price", "distance",
                     "step_pool", "cum_pool", "g_secant", "lambda_eff", "lg", "amplification"]

#: The whole observed net is attributed to trend cohorts by default, which spec §11.2 says is
#: an upper bound rather than an estimate. See the module docstring: `l.g` scales linearly in
#: this, so halving it halves every figure below.
DEFAULT_TREND_FRACTION = 1.0

#: `1/(1-l.g)` is unstable approaching 1 and meaningless at or past it. Beyond this the
#: amplification is reported as null and flagged, because the things that actually end such a
#: cascade (position limits, margin hikes, exhaustion) are not modelled here.
LG_CEILING = 0.9


class ReflexivityError(ValueError):
    """The inputs cannot support a cascade estimate."""


def implied_gross_pool(signals, net_contracts: float, *,
                       trend_fraction: float = DEFAULT_TREND_FRACTION) -> float:
    """`P = |net| . H / |sum(s)|`, the gross pool a uniform cohort split implies.

    The observed net is the SUM of the cohorts, so mixed signals mean real positions on both
    sides netting down and a gross larger than the net. Unanimous signals mean gross equals
    net. Using `|net|` as the pool at every step gets the unanimous markets wrong by 3x while
    leaving the mixed ones right, which reorders rather than rescales.

    Raises when the CONTRIBUTING signals sum to zero, which makes `P` infinite. Three resolved
    non-zero signals cannot vanish, but flat and unresolved lookbacks both drop out of the
    count, so `(-1, +1)` is an ordinary two-signal case and not a configuration error.
    """
    if not 0.0 < trend_fraction <= 1.0:
        raise ReflexivityError(
            f"trend_fraction must be in (0, 1], got {trend_fraction!r}. It is the share of "
            f"the observed net that is trend-following; 1.0 attributes all of it and is an "
            f"upper bound, not an estimate.")
    s = [int(v) for v in signals if v is not None and not pd.isna(v)]
    if not s:
        raise ReflexivityError("no resolved signals: every lookback is longer than the price "
                               "history, so there are no trigger locations to build on.")
    total = sum(s)
    if total == 0:
        raise ReflexivityError(
            f"signals {tuple(s)} sum to zero, so the implied gross pool is infinite: no "
            f"uniform cohort split reproduces a non-zero net. Unreachable with an odd count "
            f"of non-zero signals, which is why {len(s)} lookbacks is not a free choice.")
    return abs(float(net_contracts)) * len(s) / abs(total) * float(trend_fraction)


def effective_lambda(sigma_daily: float, quantity: float, volume: float, *,
                     y: float = DEFAULT_Y) -> float:
    """Fractional price move per contract, linearising §A.5's square-root law at `quantity`.

    §A.8's algebra is linear (`dF = -l.Q`) and §A.5's impact is not, so `l` is a secant and
    not a constant of the market: `l = I(Q)/Q`, which FALLS as `Q` rises. Quoting an `l`
    without the `Q` it was taken at is meaningless, so both are carried in the output.
    """
    q = float(quantity)
    if q <= 0:
        return float("nan")
    impact = square_root_impact(sigma_daily, q, volume, y=y)
    return float(impact) / q


def _amplification(lg: float) -> float:
    """`1/(1 - l.g)`, or null past the ceiling. Never a negative, which is what the naive
    formula returns for `l.g > 1` and which reads as a mild damping rather than a blow-up."""
    if not np.isfinite(lg) or lg >= LG_CEILING:
        return float("nan")
    return 1.0 / (1.0 - lg)


def staircase(triggers: pd.DataFrame, net_contracts: float, *, sigma_daily: float,
              volume: float, trend_fraction: float = DEFAULT_TREND_FRACTION,
              weights=None, y: float = DEFAULT_Y) -> pd.DataFrame:
    """The signed staircase `G(F)`, one frame with the two directions kept apart.

    `triggers` is `trigger_prices` output. Each cohort holds `w_h . P . s_h`, so a LONG cohort
    (`s = +1`) flips DOWN and is forced to sell, and a SHORT cohort (`s = -1`) flips UP and is
    forced to buy. A flat cohort (`s = 0`) holds nothing and appears in neither staircase.

    `g_secant` is cumulative pool over distance travelled, not the marginal `dG/dF`. Between
    steps the marginal is zero and at a step it is a delta, neither of which is usable; the
    secant is the average forcing over the move actually made, which is what the cascade
    algebra needs. It is reported per step so the growth through successive horizons is
    visible rather than summarised.
    """
    resolved = triggers[triggers["signal"].notna()].copy()
    if resolved.empty:
        raise ReflexivityError("no resolved triggers: every lookback exceeds the price history.")

    pool = implied_gross_pool(resolved["signal"], net_contracts,
                              trend_fraction=trend_fraction)
    n = len(resolved)
    if weights is None:
        w = pd.Series(1.0 / n, index=resolved.index)
    else:
        w = pd.Series(list(weights), index=resolved.index, dtype="float64")
        if not np.isclose(w.sum(), 1.0):
            raise ReflexivityError(f"weights must sum to 1, got {w.sum():.6f}.")

    resolved["step_pool"] = w * pool * resolved["signal"].abs()
    # A long flips down and sells; a short flips up and buys. The distance is a magnitude in
    # both cases and the direction column is what carries the sign.
    resolved["direction"] = np.where(resolved["signal"] > 0, "down",
                                     np.where(resolved["signal"] < 0, "up", "flat"))
    resolved["distance"] = resolved["move_from_spot"].abs()

    out = []
    for direction in ("down", "up"):
        side = resolved[resolved["direction"] == direction].sort_values("distance")
        if side.empty:
            continue
        side = side.copy()
        side["cum_pool"] = side["step_pool"].cumsum()
        side["g_secant"] = side["cum_pool"] / side["distance"].where(side["distance"] > 0)
        side["lambda_eff"] = [effective_lambda(sigma_daily, q, volume, y=y)
                              for q in side["cum_pool"]]
        side["lg"] = side["lambda_eff"] * side["g_secant"]
        side["amplification"] = [_amplification(v) for v in side["lg"]]
        out.append(side)

    if not out:
        raise ReflexivityError("every resolved lookback is flat, so there is no trigger in "
                               "either direction and no cascade to model.")
    frame = pd.concat(out, ignore_index=True)[STAIRCASE_COLUMNS]
    frame.attrs["gross_pool"] = pool
    frame.attrs["net_contracts"] = float(net_contracts)
    frame.attrs["trend_fraction"] = float(trend_fraction)
    frame.attrs["implied_gross_multiple"] = (
        pool / abs(float(net_contracts)) if net_contracts else float("nan"))
    return frame


def headline(stairs: pd.DataFrame) -> pd.DataFrame:
    """The worst step per direction, which is NOT reliably the nearest one.

    `l.g ~ sqrt(Q_cum)/d`, so a step beats the next only when the next trigger is more than
    `sqrt(Q_(i+1)/Q_i)` further out: 41% at the first gap under a uniform split. Clustered
    triggers beat that test routinely, and 6 of 33 multi-step staircases in the latest week
    peak past their nearest step. Which step wins is independent of the pool size, so that
    count holds whatever each market's net turns out to be.

    Returns one row per direction, with `is_nearest` so a reader can see when the two differ
    rather than having to compare frames.
    """
    rows = []
    for direction, side in stairs.groupby("direction", sort=False):
        ranked = side.sort_values("distance")
        if ranked["lg"].isna().all():
            continue
        worst = ranked.loc[ranked["lg"].idxmax()]
        rows.append({
            "direction": direction,
            "lookback_days": worst["lookback_days"],
            "distance": worst["distance"],
            "cum_pool": worst["cum_pool"],
            "lg": worst["lg"],
            "amplification": worst["amplification"],
            "is_nearest": bool(worst["distance"] == ranked["distance"].iloc[0]),
            "steps": len(ranked),
        })
    return pd.DataFrame(rows)


def bracket(stairs: pd.DataFrame) -> pd.DataFrame:
    """The all-fast / all-slow endpoints per direction, which is what the horizon argument was.

    All-fast puts the whole side's pool on its nearest trigger, all-slow on its furthest.
    These are bounds over LOCATIONS. The uniform split is a separate assumption about HEIGHTS
    and is not bracketed by them, which is why `trend_fraction` and `weights` are swept rather
    than read off this.
    """
    rows = []
    for direction, side in stairs.groupby("direction", sort=False):
        total = side["step_pool"].sum()
        near, far = side["distance"].min(), side["distance"].max()
        for label, dist in (("all_fast", near), ("all_slow", far)):
            g = total / dist if dist > 0 else float("nan")
            lam = side["lambda_eff"].iloc[-1]
            lg = lam * g
            rows.append({"direction": direction, "endpoint": label, "distance": dist,
                         "pool": total, "g_secant": g, "lg": lg,
                         "amplification": _amplification(lg)})
    return pd.DataFrame(rows)


def format_block(stairs: pd.DataFrame, *, symbol: str = "") -> str:
    """Every input beside its result, per house style. A synthesis that hides its terms
    cannot be checked, and this one has three terms nobody can measure."""
    lines = [f"cascade amplification{f' — {symbol}' if symbol else ''}".replace("—", "-")]
    lines.append(f"observed net:          {stairs.attrs['net_contracts']:>12,.0f} contracts")
    lines.append(f"trend fraction (f):    {stairs.attrs['trend_fraction']:>12.2f}   "
                 f"(1.00 attributes the whole net, an upper bound)")
    lines.append(f"implied gross pool:    {stairs.attrs['gross_pool']:>12,.0f} contracts "
                 f"= {stairs.attrs['implied_gross_multiple']:.2f}x |net|")

    for direction, side in stairs.groupby("direction", sort=False):
        forced = "sell" if direction == "down" else "buy"
        lines.append(f"  on a move {direction:<4} (forced {forced}):")
        for row in side.itertuples():
            amp = "no equilibrium" if not np.isfinite(row.amplification) \
                else f"{row.amplification:.2f}x"
            lines.append(
                f"    {row.lookback_days:>3}d at {row.distance:>6.1%}: "
                f"cum pool {row.cum_pool:>10,.0f}, "
                f"l={row.lambda_eff:.3e}, g={row.g_secant:>12,.0f}, "
                f"l.g={row.lg:.3f} -> {amp}")
    for row in headline(stairs).itertuples():
        where = "nearest step" if row.is_nearest else f"step past the nearest, {row.steps} in all"
        amp = "no equilibrium" if not np.isfinite(row.amplification) \
            else f"{row.amplification:.2f}x"
        lines.append(f"  worst {row.direction:<4}: {amp} at {row.distance:.1%} "
                     f"({row.lookback_days:.0f}d, {where})")
    lines.append("  g_up and g_down are separate cascades and are never summed.")
    return "\n".join(lines)
