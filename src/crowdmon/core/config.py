"""Configured judgement: fragility weights, the impact constant, classification tolerances.

Everything in this module is **configured, not fitted**. That distinction is the whole
point of the file existing. A weight here is a statement about how a category behaves
under stress, argued from what the category is, and it must never be tuned until an
output looks better. If it were fitted, every downstream number would be a restatement of
whatever period it was fitted on, and the monitor would be describing its own calibration
window rather than the market.

The consequence is that sensitivity analysis is not optional. A result that survives the
weights moving is a result about positioning; one that does not is a result about this
file. `fragility.contributions` exists so that a reader can see which category is actually
carrying a headline number, and `flow.tolerance_sensitivity` exists so that the same
question can be asked of the classification tolerance.

Module spec §6.3 (weights, with the rationale per category) and §6.4 (flow states).
"""
from __future__ import annotations

# ── Fragility weights (module spec §6.3) ────────────────────────────────────
# "How much of the open interest sits with holders who face forced-exit functions." A
# weight is a *propensity to be forced out*, not a size and not a directional view.
#
# Futures are zero-sum, so "everyone is long" is impossible and net imbalance on its own
# says almost nothing: every long is somebody's short. What differs between the two sides
# is who is holding, and whether their exit is discretionary. A producer hedging physical
# crop can stand for delivery and has no margin call that forces a buy-back; a levered
# fund running a vol target has an exit function written into its mandate.
DISAGGREGATED_WEIGHTS: dict[str, float] = {
    # Vol targets, margin, drawdown limits, monthly redemptions. The reference 1.0: every
    # other weight is "how much less forced than a levered fund".
    "managed_money": 1.0,
    # Retail. Small in aggregate but the least resilient per unit of position, and the
    # first to be liquidated by a broker rather than by a decision.
    "nonreportable": 0.6,
    # A genuine mixture (family offices, prop, smaller institutions), so the weight is
    # deliberately mid-range and carries the most uncertainty of the five.
    "other_reportable": 0.5,
    # Hedged against OTC exposure, so not directionally motivated, but balance-sheet and
    # capital constrained, which is a real forcing channel at the wrong moment.
    "swap": 0.4,
    # Hedging physical. Can stand for delivery, and the position exists to offset a cash
    # exposure rather than to express a view. The least forceable holder in the report.
    "producer_merchant": 0.1,
}

# TFF covers the financial futures (rates, FX, equity index) that the Disaggregated report
# does not. Same reasoning, different category names, taken from module spec §6.3. Present
# so that nothing downstream has to special-case a report type, not because TFF has been
# exercised here: this session's analysis is Disaggregated only.
TFF_WEIGHTS: dict[str, float] = {
    "leveraged": 1.0,
    "nonreportable": 0.6,
    "other_reportable": 0.5,
    "dealer": 0.4,
    # Unlevered, longer horizon, and mandated to hold. The lowest forced-exit propensity
    # among the financial categories.
    "asset_manager": 0.3,
}

# Legacy has three categories and is deliberately absent. Its "noncommercial" bucket mixes
# levered funds with everything else non-commercial, which is exactly the distinction the
# weights exist to make, so a Legacy fragility number would be a weighted average of a
# thing this file says should not be averaged. Legacy also drops non-commercial spreading
# entirely (module spec §4), so its open-interest denominator holds contracts its numerator
# cannot see. Asking for Legacy weights raises rather than returning a plausible number.
WEIGHTS_BY_REPORT: dict[str, dict[str, float]] = {
    "disaggregated": DISAGGREGATED_WEIGHTS,
    "tff": TFF_WEIGHTS,
}

# ── Flow classification (module spec §6.4) ──────────────────────────────────
#: A leg counts as "~0" when its move is at most this fraction of the larger leg's move.
#: The spec's table is written as "ΔLong +, ΔShort ~0", and against real data neither leg
#: is ever exactly zero, so "~0" has to become a number. 0.25 is the starting value the
#: handoff specifies; `flow.tolerance_sensitivity` reports what 0.15 and 0.40 would do
#: instead, because a tolerance that changes the answer is doing the data's job.
DOMINANCE_TOLERANCE = 0.25

#: Tolerances to sweep when reporting how much work the tolerance is doing.
SENSITIVITY_TOLERANCES = (0.15, 0.25, 0.40)

#: The nominal COT reporting interval, in days.
REPORT_INTERVAL_DAYS = 7

#: How far from `REPORT_INTERVAL_DAYS` an interval may fall and still be differenced.
#: **Zero by default**, which is the strict reading: difference only across consecutive
#: report dates exactly one week apart, and label anything else `gap` with null deltas.
#:
#: Measured cost of that strictness, on the real Disaggregated store (27 markets, 2006 to
#: 2026, 27,167 transitions): 26,574 are 7-day, 285 are 6-day and 285 are 8-day, and 24
#: are longer. The 6/8-day pairs are holiday shifts, which are real weeks of flow that the
#: strict rule discards. Setting this to 1 admits them at the cost of comparing a 6-day
#: move against an 8-day one, roughly a 30% span difference. Neither choice is free, so it
#: is a parameter rather than a constant, and `flow.decompose` always emits `days_elapsed`
#: so the caller can see the span behind any number.
GAP_DAYS_TOLERANCE = 0

# ── Exit capacity (module spec §8) ──────────────────────────────────────────
#: Participation rate in `T = Q / (kappa * V)`: the share of daily volume a forced seller
#: can realistically take without the impact assumption collapsing. 0.2 is the
#: conventional figure and is judgement of the same kind as the weights above.
#:
#: `pressure.exit_pressure` returns `T` only when a volume is passed and `None` otherwise.
#: There is no per-contract volume source in this workspace today (ADR-0007 step 2 is on
#: ice), so today it is always `None`, and the alternative — estimating a volume — would
#: put a fabricated denominator under the headline number of the whole system.
KAPPA = 0.2


class ConfigError(ValueError):
    """A category or report type this file has no configured judgement for."""


def weights_for(report_type: str) -> dict[str, float]:
    """The weight map for a report type, or raise.

    Raising is the point. A missing report type returning `{}` would give
    `Q_sell = Q_buy = Phi = 0` for every market in it, which reads as "nothing fragile
    here" rather than as "this was never configured".
    """
    try:
        return dict(WEIGHTS_BY_REPORT[report_type])
    except KeyError:
        raise ConfigError(
            f"no fragility weights configured for report_type {report_type!r}; "
            f"have {sorted(WEIGHTS_BY_REPORT)}. Legacy is deliberately absent: its "
            f"'noncommercial' bucket merges levered funds with everything else "
            f"non-commercial, which is the distinction these weights exist to make."
        ) from None


def check_vocabulary(categories, report_type: str) -> None:
    """Every category present must have a weight. Unknown label raises.

    This is the check the handoff calls for by name, and the failure it prevents is not
    hypothetical: a category that is silently dropped does not produce an error anywhere
    downstream, it produces a `Q_sell` that is too small and a `Phi` that is too low, on
    every market, forever. Under-reported fragility from a monitor whose entire job is to
    report fragility is the worst available failure mode, and it is invisible.

    Deliberately one-directional: a category in the vocabulary but absent from the data is
    fine (a market where nobody is a swap dealer is a market, not a parse failure), while
    a category in the data but absent from the vocabulary is not.
    """
    weights = weights_for(report_type)
    unknown = sorted(set(categories) - set(weights))
    if unknown:
        raise ConfigError(
            f"categories {unknown} have no fragility weight under report_type "
            f"{report_type!r} (known: {sorted(weights)}). Refusing to continue: an "
            f"unmapped category is silently dropped from every sum it belongs in, which "
            f"under-reports exit pressure without failing anywhere.")
