"""Do the exits go through the same door? Appendix §A.6, module spec §7.

Per-market exit times cannot be added, because liquidity co-moves. §A.6 regresses each
market's illiquidity change on the basket average

    d(Lambda_i,t) = alpha_i + beta_i . d(Lambda_M,t) + eps_i,t

and multiplies exit pressure by the result:

    T_eff = T . (1 + gamma . beta_bar)

`beta -> 0` means independent exits and each `T_i` means what it says. `beta -> 1` means every
exit closes at once and the aggregate is worse than the sum of its parts. That distinction,
**crowded-and-liquid versus crowded-and-illiquid**, is what this module exists to measure, and
it is real: measured across the tradeable universe, livestock sits at 0.07 to 0.11 and grains
and energy at 0.95 to 1.02.

| market | beta | reading |
|---|---|---|
| DC milk, HE hogs, LE cattle | 0.07-0.11 | own supply cycle. A different door |
| OJ, NG, PL | 0.32-0.38 | |
| GC gold, CC cocoa | 0.54-0.55 | |
| CL crude, SI silver, ZC corn | 0.95-0.97 | |
| ZW wheat, KE wheat-HRW | 1.01-1.02 | the same door |

**Two findings mean §A.6 cannot feed §A.9 the way both sections read.** Both were measured
here and both are recorded in the amendments; neither is a defect in this code.

**1. The own market must be excluded from the basket, or `beta_bar` is identically 1.**
§A.6 says "the basket average" without saying whether market `i` is in its own basket. Taken
literally it is, and then `beta_bar = 1` **by algebra rather than by measurement**:

    sum_i cov(y_i, ybar) = cov(sum_i y_i, ybar) = cov(N.ybar, ybar) = N.var(ybar)

so `mean_i beta_i = 1` exactly, for any data at all. Verified numerically to twelve decimal
places on **independent** series with zero real commonality. On the real panel it produces
0.9999 against 0.6341 with the market excluded, and inflates Class III Milk from 0.070 to
0.849, a factor of **12**. `commonality_betas` therefore excludes by default, and the
`exclude_own=False` path exists only so a test can demonstrate the identity.

**2. A constant `beta_bar` cannot change `D` at all.** §A.9 defines `I = pct(T_eff)`, a
percentile of a market's own history. `T_eff = T . (1 + gamma . beta_bar)` with `beta_bar`
constant is a positive scalar multiple of `T`, percentiles are invariant under a monotonic
transform, and so `I` is **bit-identical** whatever `gamma` is. Checked: maximum difference
0.00e+00 for gamma at 0.5 and at 2.0. The same holds for a per-market constant `beta_i`, for
the same reason, since the percentile is taken within a market.

Only a **time-varying** `beta_bar_t` moves the composite, and it moves it a little: on a
rolling 252-day estimate `beta_bar` runs 0.423 to 0.780 over 2016-2026, so `1 + 0.5.beta_bar`
spans just 1.211 to 1.390, a **1.15x** modulation against a `T` that itself ranges over 13x.
Rank correlation of the resulting percentile against the unmodified one is 0.985.

So `t_effective` is offered, and this module does **not** wire it into `composite.py`. Doing
that is a decision about what §A.9's `I` should be, not a gap to be filled quietly.

**`gamma` has no sanctioned range.** `kappa` is 0.2 in §A.5 and `Y` is 0.5 to 1.0 in the same
section; the appendix gives `gamma` no value and no bounds anywhere. It is a third configured
constant with less support than the other two, which is why it is a required-looking argument
with a stated default rather than a module constant imported from `core.config` beside
`KAPPA`. If a second consumer appears, it moves there.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Columns ``add_commonality`` adds.
COMMONALITY_COLUMNS = ["beta", "beta_bar", "t_eff_sell", "t_eff_buy"]

#: Amihud window for the panel. Short, because this measures how illiquidity CHANGES together
#: and a long window smooths away the co-movement being estimated.
DEFAULT_LAMBDA_WINDOW = 21

#: Rolling window for a time-varying beta. One year, matching the calm ADV baseline.
DEFAULT_BETA_WINDOW = 252

#: Minimum overlapping observations before a beta is returned at all.
DEFAULT_MIN_OBS = 500

#: See the module docstring: the appendix gives no value and no range for this one. 0.5 is a
#: placeholder chosen to sit in the middle of "some effect" and "none", not a calibration.
DEFAULT_GAMMA = 0.5


class CommonalityError(ValueError):
    """The inputs cannot support a commonality estimate."""


def illiquidity_panel(specs, *, window: int = DEFAULT_LAMBDA_WINDOW,
                      start: str | None = None, min_obs: int = DEFAULT_MIN_OBS) -> pd.DataFrame:
    """Wide panel of Amihud illiquidity, one column per market.

    `specs` is an iterable of `(symbol, point_value)`. The multiplier is not optional: see
    `futures.impact.amihud_series`, which refuses without one because dropping it reorders
    the universe rather than rescaling it.
    """
    from .impact import amihud_series

    out = {}
    for symbol, point_value in specs:
        series = amihud_series(str(symbol), float(point_value),
                               window=window, min_periods=max(window - 6, 5)).dropna()
        if len(series) >= min_obs:
            out[str(symbol)] = series
    if not out:
        return pd.DataFrame()
    panel = pd.DataFrame(out).sort_index()
    return panel.loc[start:] if start else panel


def _log_changes(panel: pd.DataFrame) -> pd.DataFrame:
    """Proportional changes. Amihud spans orders of magnitude across markets (gold 0.12e-12,
    orange juice 1124e-12), so a raw difference would make the regression a description of
    the thinnest market and nothing else."""
    return np.log(panel.where(panel > 0)).diff().replace([np.inf, -np.inf], np.nan)


def commonality_betas(panel: pd.DataFrame, *, exclude_own: bool = True,
                      min_obs: int = DEFAULT_MIN_OBS) -> pd.Series:
    """§A.6's `beta_i`, one per market, over the whole panel.

    `exclude_own=False` reproduces the literal reading of §A.6 and is **vacuous**: it returns
    a set of betas whose mean is exactly 1 for any data whatsoever, including independent
    series. It exists so a test can demonstrate that, and for no other purpose.
    """
    if panel.empty or panel.shape[1] < 3:
        raise CommonalityError(
            f"need at least 3 markets to form a basket, got {panel.shape[1]}. A basket of "
            f"two is each market regressed on itself and its one peer.")
    changes = _log_changes(panel)
    betas = {}
    for column in changes.columns:
        basket = (changes.drop(columns=[column]) if exclude_own else changes).mean(axis=1)
        pair = pd.concat([changes[column].rename("y"), basket.rename("x")], axis=1).dropna()
        if len(pair) < min_obs:
            continue
        variance = pair["x"].var()
        if not variance > 0:
            continue
        betas[column] = float(pair["y"].cov(pair["x"]) / variance)
    return pd.Series(betas, dtype="float64").sort_values()


def rolling_betas(panel: pd.DataFrame, *, window: int = DEFAULT_BETA_WINDOW,
                  exclude_own: bool = True) -> pd.DataFrame:
    """Time-varying `beta_i`. The only form that can move `pct(T_eff)`, and it moves it by
    a rank correlation of 0.985 against the unmodified percentile."""
    changes = _log_changes(panel)
    out = {}
    for column in changes.columns:
        basket = (changes.drop(columns=[column]) if exclude_own else changes).mean(axis=1)
        pair = pd.concat([changes[column].rename("y"), basket.rename("x")], axis=1).dropna()
        variance = pair["x"].rolling(window).var()
        covariance = pair["y"].rolling(window).cov(pair["x"])
        out[column] = covariance / variance.where(variance > 0)
    return pd.DataFrame(out).sort_index()


def t_effective(t, beta_bar, *, gamma: float = DEFAULT_GAMMA):
    """`T_eff = T . (1 + gamma . beta_bar)`. Scalars or aligned Series.

    **This changes nothing downstream if `beta_bar` is constant and the consumer takes a
    percentile of it**, which is exactly what §A.9's `I = pct(T_eff)` does. See the module
    docstring. Use a rolling `beta_bar` if the intent is to affect `D`, and expect a small
    effect when you do.
    """
    if gamma < 0:
        raise CommonalityError(
            f"gamma must be non-negative, got {gamma!r}. A negative value would make "
            f"co-moving liquidity shorten the exit, which inverts the whole argument.")
    return t * (1.0 + gamma * beta_bar)


def add_commonality(frame: pd.DataFrame, betas: pd.Series, *,
                    gamma: float = DEFAULT_GAMMA) -> pd.DataFrame:
    """Attach `beta`, `beta_bar` and the two `T_eff` columns to a ranked fragility frame.

    Needs `symbol` and the `dtl_*` durations from `pressure.rank_markets`. Rows whose market
    has no beta get nulls rather than the basket mean: a market absent from the panel is
    absent because its illiquidity series was too short, and substituting the average would
    hide exactly the markets whose liquidity behaviour is least well known.
    """
    missing = sorted({"symbol", "dtl_sell", "dtl_buy"} - set(frame.columns))
    if missing:
        raise CommonalityError(
            f"missing columns {missing}. Commonality sits on top of exit capacity: run "
            f"volume.add_volume and pressure.rank_markets first.")
    out = frame.copy()
    out["beta"] = out["symbol"].map(betas)
    out["beta_bar"] = float(betas.mean()) if len(betas) else float("nan")
    for side in ("sell", "buy"):
        out[f"t_eff_{side}"] = t_effective(
            pd.to_numeric(out[f"dtl_{side}"], errors="coerce"), out["beta_bar"], gamma=gamma)
    return out


def gamma_sensitivity(t: pd.Series, beta_bar, *,
                      gammas=(0.0, 0.25, 0.5, 1.0, 2.0)) -> pd.DataFrame:
    """How much `gamma` actually changes the ranking, reported rather than assumed.

    The same pattern as `flow.tolerance_sensitivity`, and for the same reason: a constant
    nobody can calibrate should have its influence measured and printed, not defended.
    """
    base = pd.to_numeric(t, errors="coerce")
    rows = []
    for gamma in gammas:
        scaled = t_effective(base, beta_bar, gamma=gamma)
        rows.append({"gamma": gamma,
                     "mean_t_eff": float(scaled.mean()),
                     "multiplier": float((scaled / base).mean()),
                     "rank_corr_vs_gamma_0": float(base.rank().corr(scaled.rank()))})
    return pd.DataFrame(rows)
