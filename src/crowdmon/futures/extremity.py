"""Positioning extremity: how unusual is this position, against its own history?

Module spec §6.1 and appendix §A.4, the last piece of the spec's step 3. Given the
normalisation ladder complete through rung 4:

    x_t = P_t . M_t . F_t . sigma_t          (net_risk_usd, from `riskunits`)
    z_t = (x_t - mu_W) / s_W                 over a trailing 3-year window
    pct = rank of x_t within the same window

**Why risk units and not contracts.** Appendix §A.4 puts vol-scaled notional at the top of
the ladder because risk limits are denominated in risk, and a vol-targeting book sizes at
`target_vol / sigma`. Measured on the real store, the choice reorders the cross-section
substantially: in the latest week, Managed Money's largest net position in CONTRACTS
(soybeans) is only sixth in risk units, while silver climbs from 17th to 7th and corn falls
from 2nd to 12th. Standardising contract counts would be standardising the wrong quantity.

**Extremity is not direction.** A 99th-percentile long is a statement about the size of the
position relative to what this market has carried before, and says nothing about the next
return. Module spec §11 item 7: positioning extremes persist for quarters. This module
produces the `C` term of the appendix's `D = C x I x Phi` and nothing more.

**The universe is 27 markets, not 279, and that is a data fact rather than a choice.** A
three-year window needs three years, and the vintage store begins 2025-01-07, so it holds
about nineteen months. Only `io.from_current_store` reaches back far enough (2006, 27
markets). Breadth and depth remain in different places: `fragility` and `flow` run across
the full 279-market cross-section, and extremity cannot.
"""
from __future__ import annotations

import pandas as pd

from ..core.aggregate import (
    DEFAULT_MIN_PERIODS,
    DEFAULT_WINDOW,
    DEFAULT_WINSOR,
    standardise,
)

#: The series key. Extremity is per market AND per category: Managed Money's history in gold
#: is a different distribution from Producer/Merchant's in gold, and pooling them would
#: compare a levered fund against a hedger's seasonal book.
SERIES_KEY = ["market_code", "report_type", "combined", "category"]

#: The quantity standardised, from `riskunits.add_risk_units`.
EXTREMITY_INPUT = "net_risk_usd"

EXTREMITY_COLUMNS = ["net_risk_usd_z", "net_risk_usd_pct"]


class ExtremityError(ValueError):
    """The panel cannot support an extremity calculation."""


def add_extremity(with_risk: pd.DataFrame, *, column: str = EXTREMITY_INPUT,
                  window: str | int = DEFAULT_WINDOW,
                  min_periods: int = DEFAULT_MIN_PERIODS,
                  winsor: float = DEFAULT_WINSOR) -> pd.DataFrame:
    """Add trailing z-score and percentile of vol-scaled net notional, per market-category.

    Input is the output of `riskunits.add_risk_units`, which is itself the output of
    `notional.add_notional` over a `ContractMaster.annotate`d panel. Rows without risk units
    keep their place with null scores rather than being dropped, for the same reason the
    contract master never inner-joins: a market silently absent from a ranking is worse than
    one visibly unscored.

    Nulls do not poison a window. A market with a price gap contributes fewer observations to
    its own trailing three years, and `min_periods` decides whether what remains is enough.
    """
    if with_risk.empty:
        return with_risk.assign(**{c: pd.NA for c in EXTREMITY_COLUMNS})
    missing = [c for c in [*SERIES_KEY, "report_date", column] if c not in with_risk.columns]
    if missing:
        raise ExtremityError(
            f"missing columns for extremity: {missing}. Expected the output of "
            f"`add_risk_units`; extremity standardises {column!r}, which is rung 4 of the "
            f"normalisation ladder and does not exist before it.")
    _warn_if_history_is_too_short(with_risk, window, min_periods)

    return standardise(with_risk, column, by=SERIES_KEY, date_column="report_date",
                       window=window, min_periods=min_periods, winsor=winsor)


def extremity_report(scored: pd.DataFrame, *, column: str = EXTREMITY_INPUT) -> pd.DataFrame:
    """Coverage: how much of the panel actually got a score, and why the rest did not.

    Three reasons, kept apart because they have different fixes. `no_risk_units` is a price
    or contract-spec question and belongs to `riskunits.coverage_report`; `short_history` is
    a data-availability fact that no code change will alter; `scored` is the answer.
    """
    z = f"{column}_z"
    if z not in scored.columns:
        raise ExtremityError(f"{z!r} not present; run `add_extremity` first")
    has_input = pd.to_numeric(scored[column], errors="coerce").notna()
    has_score = pd.to_numeric(scored[z], errors="coerce").notna()
    return pd.Series({
        "scored": int(has_score.sum()),
        "short_history": int((has_input & ~has_score).sum()),
        "no_risk_units": int((~has_input).sum()),
        "total": len(scored),
    }).to_frame("rows")


def latest_extremes(scored: pd.DataFrame, *, category: str = "managed_money",
                    n: int = 10, column: str = EXTREMITY_INPUT) -> pd.DataFrame:
    """The most extreme readings in the newest week, both tails, one category.

    Both tails on purpose. The 1st percentile is a short position as extreme as the 99th is a
    long one, and a ranking that sorted on the percentile alone would fill with one side and
    call it the answer.
    """
    pct = f"{column}_pct"
    rows = scored[(scored["category"] == category)
                  & (scored["report_date"] == scored["report_date"].max())
                  & scored[pct].notna()]
    if rows.empty:
        return rows
    ordered = rows.reindex(
        (rows[pct] - 0.5).abs().sort_values(ascending=False).index).head(n)
    cols = ["market_name", "market_code", "net_contracts", "net_notional_usd",
            column, f"{column}_z", pct]
    return ordered[[c for c in cols if c in ordered.columns]].reset_index(drop=True)


def _warn_if_history_is_too_short(panel: pd.DataFrame, window, min_periods: int) -> None:
    """Refuse a panel that cannot possibly satisfy `min_periods`, rather than return nulls.

    The failure this prevents is a silent all-null column. Running extremity on the vintage
    store (which begins 2025-01-07, about nineteen months) returns nothing scored, and
    nothing about that result says why. Raising names the cause.
    """
    dates = pd.to_datetime(panel["report_date"])
    span_days = (dates.max() - dates.min()).days
    weeks = panel.groupby(SERIES_KEY, dropna=False, sort=False)["report_date"].size().max()
    if weeks is None or weeks >= min_periods:
        return
    raise ExtremityError(
        f"no series in this panel has {min_periods} observations (the longest has "
        f"{int(weeks)}, spanning {span_days} days), so every score would be null. A "
        f"{window} window needs history the vintage store does not have: it begins "
        f"2025-01-07. Use `io.from_current_store` (27 markets, 2006 onward), or lower "
        f"min_periods deliberately and say so.")
