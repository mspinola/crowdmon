"""Flow decomposition: what kind of week was this? (appendix A.3, module spec §6.4)

A rally driven by short covering and a rally driven by fresh buying look identical on a
price chart and are entirely different setups. The first has a **finite fuel supply** —
it ends when the shorts are gone, and how many are left is a published number. The second
does not. Net position change cannot tell them apart, because `Δnet = Δlong − Δshort` is
the same either way, and that is the whole reason this module exists.

    ΔLong +,  ΔShort ~0    new longs           fresh conviction
    ΔLong ~0, ΔShort −     short covering      finite fuel, bounded by shorts remaining
    ΔLong ~0, ΔShort +     new shorts          fresh bearish conviction
    ΔLong −,  ΔShort ~0    long liquidation    position exit, not fresh selling
    both move materially   mixed

**"~0" is not a thing that happens.** Both legs always move. So the table's `~0` has to
become a number: a leg counts as quiet when its move is at most `tolerance` times the
larger leg's move (default 0.25, `config.DOMINANCE_TOLERANCE`). Below that, the larger leg
names the state; above it, the week is `mixed`. `tolerance_sensitivity` reports how much
that number is deciding, because a classification that reshuffles between 0.15 and 0.40 is
a statement about the tolerance rather than about the market.

**This is now the only flow decomposition in the workspace.** `cotdata.vintage_flow.decompose`
*was* this function at `tolerance=1.0` with the gap rule off, not a rival implementation, and
was removed as a duplicate in cotdata#93. The measurement that argued for removing it:
on 135,835 real transitions the two agreed on 100.000000% of labels under that
parameterisation, with `d_long`, `d_short` and `d_net` identical on every row. At this
module's default tolerance they disagreed on 62% of weeks, every disagreement of exactly two
kinds: this module declining to commit (`mixed`) where that one named the dominant leg, or
refusing the interval (`gap`) where that one differenced across it anyway. Neither ever named
the opposite direction. They differed in what they REFUSED, which was the whole of it.

`tests/test_flow_equivalence.py` **skips rather than compares**, and that is the intended end
state rather than a gap: there is nothing left to compare here, and the copy staying gone is
asserted from the other side in `cotdata/tests/test_vintage_flow.py`, since the dedup could
not go this way round (`cotdata` may not import `crowdmon`). `zero_sum_check` stays in
`cotdata`, being a claim about its own parse, and `cot_adapter` runs it on every load.
See `docs/design/amendments-2026-08-02.md` §B29.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg
from .io import SERIES_KEY, require_one_row_per_key

NEW_LONGS = "new_longs"
SHORT_COVERING = "short_covering"
NEW_SHORTS = "new_shorts"
LONG_LIQUIDATION = "long_liquidation"
MIXED = "mixed"
QUIET = "quiet"
GAP = "gap"

#: Every value `flow_state` can take. `gap` and `quiet` are not flow states in the spec's
#: sense; they are the two honest refusals — one where the interval is wrong, one where
#: nothing moved.
FLOW_STATES = (NEW_LONGS, SHORT_COVERING, NEW_SHORTS, LONG_LIQUIDATION, MIXED, QUIET, GAP)

OUT_COLUMNS = SERIES_KEY + [
    "report_date", "market_name", "days_elapsed",
    "long_contracts", "short_contracts", "open_interest",
    "d_long", "d_short", "d_net", "d_oi",
    "flow_state", "fuel_remaining", "oi_corroborates",
]


class FlowError(ValueError):
    """The input cannot be differenced as a time series."""


def decompose(panel: pd.DataFrame, *,
              tolerance: float = cfg.DOMINANCE_TOLERANCE,
              gap_days_tolerance: int = cfg.GAP_DAYS_TOLERANCE) -> pd.DataFrame:
    """Label each week's positioning change, per market and category.

    `panel` is the canonical long schema, one row per natural key per report date. The
    first observation of each series is dropped: there is no such thing as its weekly
    change.

    **Gap handling is not optional.** Deltas are computed only across report dates
    `7 ± gap_days_tolerance` days apart; every other interval is labelled `gap` with null
    deltas. Without it, a market that fell out of the report for ten months and came back
    would produce one delta covering the whole absence, and that number would enter every
    ranking as the largest flow in the sample. Measured on the real Disaggregated store,
    that is not hypothetical: oats (`004603`) has a 294-day interval ending 2025-09-09 and
    five more over 50 days, because a thin market drops out of the report when it falls
    below the reporting threshold and reappears when it recovers.
    """
    if not 0 <= tolerance <= 1:
        raise FlowError(f"tolerance must be in [0, 1], got {tolerance}. At 1 every week is "
                        f"pure and nothing is mixed; at 0 nothing is pure but an exactly "
                        f"unmoved leg.")
    _require_columns(panel)
    require_one_row_per_key(panel)

    df = panel.copy()
    df["report_date"] = pd.to_datetime(df["report_date"])
    df = df.sort_values(SERIES_KEY + ["report_date"], kind="mergesort")
    g = df.groupby(SERIES_KEY, dropna=False, sort=False)

    for src, dst in (("long_contracts", "d_long"), ("short_contracts", "d_short")):
        df[dst] = g[src].diff()
    df["d_oi"] = g["open_interest"].diff() if "open_interest" in df.columns else pd.NA
    df["d_net"] = df["d_long"] - df["d_short"]
    df["days_elapsed"] = g["report_date"].diff().dt.days

    # Drop the first row of each series: no predecessor, so no change, and a row of nulls
    # labelled `gap` would falsely suggest a missing week where there is simply a start.
    df = df[df["days_elapsed"].notna()].copy()

    lo = cfg.REPORT_INTERVAL_DAYS - gap_days_tolerance
    hi = cfg.REPORT_INTERVAL_DAYS + gap_days_tolerance
    is_gap = ~df["days_elapsed"].between(lo, hi)

    df["flow_state"] = _classify(df["d_long"], df["d_short"], tolerance=tolerance)
    df.loc[is_gap, "flow_state"] = GAP
    # Null the deltas rather than leaving them: a `gap` row whose `d_net` is still populated
    # is one careless `df.d_net.sum()` away from being counted anyway, and the whole purpose
    # of the label is that the number is not comparable to a week.
    df.loc[is_gap, ["d_long", "d_short", "d_net", "d_oi"]] = pd.NA

    # The hard upper bound on how much further a short-covering rally can run: you cannot
    # cover shorts that no longer exist. Emitted only where it means something — on a
    # new-longs week the outstanding short position is not fuel for anything, and putting a
    # number in that cell would invite it to be read as though it were.
    df["fuel_remaining"] = pd.NA
    covering = df["flow_state"] == SHORT_COVERING
    df.loc[covering, "fuel_remaining"] = df.loc[covering, "short_contracts"]

    df["oi_corroborates"] = _corroborate(df)
    return df.reindex(columns=[c for c in OUT_COLUMNS if c in df.columns]).reset_index(drop=True)


def _require_columns(panel: pd.DataFrame) -> None:
    need = SERIES_KEY + ["report_date", "long_contracts", "short_contracts"]
    missing = [c for c in need if c not in panel.columns]
    if missing:
        raise FlowError(f"missing columns for flow decomposition: {missing}")


def _classify(d_long: pd.Series, d_short: pd.Series, *, tolerance: float) -> pd.Series:
    """Dominant leg names the state, unless the other leg also moved materially.

    `mixed` is a real answer and not a failure to decide. A week where a category added
    30,000 longs and 28,000 shorts is not "new longs with noise"; it is two different sets
    of traders doing opposite things, and the spec's four states describe none of it.
    """
    dl = pd.to_numeric(d_long, errors="coerce").astype("float64")
    ds = pd.to_numeric(d_short, errors="coerce").astype("float64")
    mag_l, mag_s = dl.abs(), ds.abs()
    larger = pd.concat([mag_l, mag_s], axis=1).max(axis=1)
    smaller = pd.concat([mag_l, mag_s], axis=1).min(axis=1)

    long_dominates = mag_l >= mag_s  # exact ties to the long leg, so this is deterministic
    state = pd.Series(MIXED, index=dl.index, dtype="object")
    pure = smaller <= tolerance * larger

    state = state.mask(pure & long_dominates & (dl > 0), NEW_LONGS)
    state = state.mask(pure & long_dominates & (dl < 0), LONG_LIQUIDATION)
    state = state.mask(pure & ~long_dominates & (ds > 0), NEW_SHORTS)
    state = state.mask(pure & ~long_dominates & (ds < 0), SHORT_COVERING)

    # Neither leg moved at all. Unconditional, with no threshold involved: zero is not a
    # small number, it is the absence of a change. Without this the row falls through
    # `long_dominates & (dl > 0)` as False and `(dl < 0)` as False and stays `mixed`, which
    # would be a plain misstatement — nothing was mixed, nothing happened.
    state = state.mask((dl == 0) & (ds == 0), QUIET)
    state = state.mask(dl.isna() | ds.isna(), pd.NA)
    return state


def _corroborate(df: pd.DataFrame) -> pd.Series:
    """Does market open interest agree with the label?

    Contracts exist only because somebody opened them, so fresh positioning should
    coincide with rising open interest and exits with falling. Where it does not, the label
    is describing a **transfer** of an existing position between categories rather than new
    or closed risk, which is a materially different event: nobody was forced, somebody
    changed hands.

    The asymmetry this cannot escape: `open_interest` is the market total, repeated on
    every category row, because that is what CFTC publishes. So this checks a per-category
    label against a market-level quantity. It is a real check and not a proof, which is why
    it stays a separate column instead of being folded into the state.
    """
    if "d_oi" not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="object")
    d_oi = pd.to_numeric(df["d_oi"], errors="coerce")
    opening = df["flow_state"].isin([NEW_LONGS, NEW_SHORTS])
    closing = df["flow_state"].isin([SHORT_COVERING, LONG_LIQUIDATION])
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    out = out.mask(opening & d_oi.notna(), d_oi > 0)
    out = out.mask(closing & d_oi.notna(), d_oi < 0)
    return out


# ── Reporting on the classification itself ──────────────────────────────────
def state_distribution(flows: pd.DataFrame, *, by: str | None = "category") -> pd.DataFrame:
    """Share of weeks in each state, overall or split by a column."""
    if flows.empty:
        return pd.DataFrame()
    if by is None:
        counts = flows["flow_state"].value_counts()
        return pd.DataFrame({"n": counts, "share": counts / counts.sum()})
    tab = flows.groupby(by)["flow_state"].value_counts().unstack(fill_value=0)
    return tab.div(tab.sum(axis=1), axis=0)


def tolerance_sensitivity(panel: pd.DataFrame, *,
                          tolerances=cfg.SENSITIVITY_TOLERANCES,
                          gap_days_tolerance: int = cfg.GAP_DAYS_TOLERANCE) -> pd.DataFrame:
    """How the state distribution moves across tolerance values (handoff §3).

    Required, not optional. The tolerance is the one free parameter in this module, and if
    the labels reshuffle across the sweep then the classification is reporting the
    parameter rather than the data. Returns one row per tolerance, one column per state,
    plus `reclassified_vs_base`: the share of weeks whose label differs from the label at
    `config.DOMINANCE_TOLERANCE`. That last column is the one to read — a distribution can
    look stable in aggregate while individual weeks churn underneath it.
    """
    base = decompose(panel, tolerance=cfg.DOMINANCE_TOLERANCE,
                     gap_days_tolerance=gap_days_tolerance)["flow_state"]
    rows = {}
    for tol in tolerances:
        flows = decompose(panel, tolerance=tol, gap_days_tolerance=gap_days_tolerance)
        share = flows["flow_state"].value_counts(normalize=True)
        share["reclassified_vs_base"] = float((flows["flow_state"].to_numpy()
                                               != base.to_numpy()).mean())
        rows[tol] = share
    out = pd.DataFrame(rows).T.fillna(0.0)
    out.index.name = "tolerance"
    ordered = [s for s in FLOW_STATES if s in out.columns] + ["reclassified_vs_base"]
    return out[ordered]
