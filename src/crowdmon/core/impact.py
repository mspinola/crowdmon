"""What forcing the exit costs. Appendix §A.5, module spec §8 and §12.

`pressure.T` answers "how long does the forced side take to leave". This answers the other
half: **what the leaving costs in price terms**. They are different questions and neither
substitutes for the other. A position that takes ten days to exit at 20 bps a day is not the
same problem as one that takes two days at 300 bps.

This module is in `core` rather than `futures` because module spec §12 names the square-root
impact core as shared with the equity monitor, and both functions below are true of any
market with a price, a volatility and a volume. Neither knows what a contract is, what a
category is, or that the CFTC exists. **The unit conversions that DO need those things stay
in `crowdmon.futures.impact`**, and one of them is the trap in this layer (see `amihud`).

**The square-root law.**

    I = Y . sigma . sqrt(Q / V)

`sigma` is daily return volatility as a fraction, `Q` the quantity to liquidate, `V` daily
volume, and `Y` a constant the literature puts between 0.5 and 1.0. The result is a fraction
of price.

Two properties worth stating because they are what make it usable:

- **`Q/V` is unit-free**, so the law gives the same answer in contracts, in notional, or in
  risk units, exactly as `T = Q/(kappa V)` does. What it will NOT survive is a numerator and
  denominator in different units, which is the same failure `riskunits` documents for `T`.
- **Impact is multiplicative in `sigma`**, not additive. Crowding and volatility compound,
  which is the appendix's stated reason these episodes are "short and deep rather than long
  and shallow". A market whose volatility doubles while its crowding is unchanged sees its
  exit cost double.

`Y` is **configured, not fitted**, in the same spirit as §6.3's fragility weights. Fitting it
would require a sample of observed forced liquidations with known sizes, which does not exist
here, and a fitted value would carry a precision the input data cannot support.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: The square-root law's constant. The appendix gives 0.5 to 1.0 and this is the midpoint.
#: Configured rather than fitted, and exposed as an argument everywhere so that its effect on
#: any published figure is visible in the call rather than baked in here.
DEFAULT_Y = 0.75

#: The range the appendix sanctions. Anything outside it is a deliberate act.
Y_RANGE = (0.5, 1.0)


class ImpactError(ValueError):
    """The inputs cannot support an impact estimate."""


def square_root_impact(sigma, quantity, volume, *, y: float = DEFAULT_Y):
    """`I = Y . sigma . sqrt(Q/V)`, as a fraction of price. Scalars or aligned Series.

    `quantity` and `volume` must be in the SAME units. The ratio is what carries the meaning,
    so contracts over contracts and dollars over dollars both work, while contracts over
    dollars is a number with no interpretation and nothing downstream would flag it.

    A zero or negative volume yields null rather than an infinity: "no volume" is a statement
    about data coverage far more often than about a market that cannot be traded, and an
    infinity propagates silently through a later mean.
    """
    if y <= 0:
        raise ImpactError(f"Y must be positive, got {y!r}.")
    s = pd.to_numeric(pd.Series(sigma), errors="coerce") if not np.isscalar(sigma) else sigma
    q = pd.to_numeric(pd.Series(quantity), errors="coerce") if not np.isscalar(quantity) else quantity
    v = pd.to_numeric(pd.Series(volume), errors="coerce") if not np.isscalar(volume) else volume

    if np.isscalar(v):
        if v is None or not np.isfinite(v) or v <= 0:
            return float("nan")
        ratio = q / v
    else:
        ratio = (q / v.where(v > 0))
    # A negative quantity is a lost sign convention, not a short position: Q_sell and Q_buy
    # are both magnitudes. sqrt would return nan anyway, but silently.
    if np.isscalar(ratio):
        if ratio < 0:
            raise ImpactError(
                f"quantity/volume is negative ({ratio!r}). Q is a magnitude on both sides; "
                f"a negative value means a sign convention was lost upstream.")
        return y * s * np.sqrt(ratio)
    if (ratio.dropna() < 0).any():
        raise ImpactError(
            "quantity/volume is negative for at least one row. Q is a magnitude on both "
            "sides; a negative value means a sign convention was lost upstream.")
    return y * s * np.sqrt(ratio)


def amihud(returns: pd.Series, dollar_volume: pd.Series, *,
           window: int = 252, min_periods: int = 60) -> pd.Series:
    """Amihud illiquidity: the trailing mean of `|r_t| / dollar_volume_t`.

    How much the price moves per dollar traded. A structural descriptor of the market rather
    than of any position in it, which is what distinguishes it from the square-root law.

    **`dollar_volume` must be a real currency amount, which for a derivative means
    `volume x price x CONTRACT MULTIPLIER`.** Omitting the multiplier is the trap in this
    layer, because the result still looks like a plausible illiquidity series and is simply
    the wrong ordering: measured on the real panel, dropping it gives a rank correlation of
    **0.500** against the correct figure and moves 8 of 25 markets by more than five places.
    Cocoa (multiplier 10) reads 20th of 25 without it and 5th with it; RBOB gasoline
    (multiplier 42,000, a price quoted in dollars per gallon) reads illiquid without it and is
    one of the most liquid markets in the set. Nothing here can detect that, because a
    multiplier-free dollar volume is still a positive number of the right general size, which
    is why this docstring is the guard.

    Trailing by construction, like every other aggregate in this package: the value at `t`
    uses only `t` and earlier.
    """
    r = pd.to_numeric(returns, errors="coerce").abs()
    dv = pd.to_numeric(dollar_volume, errors="coerce")
    ratio = (r / dv.where(dv > 0)).replace([np.inf, -np.inf], np.nan)
    return ratio.rolling(window, min_periods=min_periods).mean()
