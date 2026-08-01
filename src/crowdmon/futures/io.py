"""Canonical COT panels, and the identity that says whether the parse is still right.

`cot_adapter.VintageCotSource` answers "what was knowable on date *t*", which is the
question that matters for evaluating a rule. This module answers the two flatter questions
the analysis engines actually ask:

- **the cross-section**: every market in one report week (`latest`, `from_vintage`)
- **the history**: one market's every week, as long as the store holds (`from_current_store`)

and it reports the open-interest identity as a *number* rather than swallowing it.

**The two stores are different shapes, and the difference decides which one to use.**
Measured on this store, 2026-08-01:

| Source | Markets | Report dates | What it is |
|---|---|---|---|
| vintage observations | 346 | 2025-01-07 to 2026-07-28 | bitemporal, every code CFTC publishes |
| current-state parquet | 27 | 2006-06-13 to 2026-07-28 | the registry universe, revised in place |

So breadth and depth are in different places: a cross-market ranking wants the vintage
store, and anything needing twenty years of one market wants the current-state one. Both
are exposed, under names that say which is which, rather than one function with a flag.

**Neither is point-in-time before 2026-07-31.** Vintages accumulate forward only, so an
earlier week is the current value with revisions already applied, whichever store it came
from. That is fine for flow decomposition — a first difference on revised values is the
better input, not the worse one, because the revision is CFTC correcting itself — and it
is not fine for evaluating a rule as of a past date. `cot_adapter.VintageCotSource.load`
is the entry point for that, and it marks every row `pit_complete`.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg

#: The grouping key for a positioning series. `combined` is in it because futures-only and
#: futures-and-options-combined are different series that must never share a time series
#: (module spec §3): the same market appears in both, and a diff that straddled them would
#: read the difference between two report definitions as a week of flow.
SERIES_KEY = ["market_code", "report_type", "combined", "category"]

#: Columns every engine here depends on. Anything not in this list is a bonus.
REQUIRED_COLUMNS = ["report_date", "market_code", "market_name", "category",
                    "long_contracts", "short_contracts", "spread_contracts",
                    "open_interest"]


class PanelError(ValueError):
    """The frame is not a usable canonical panel."""


# ── Sources ─────────────────────────────────────────────────────────────────
def from_vintage(*, report_type: str = "disaggregated", as_of=None,
                 market_code: str | None = None, validate: bool = True) -> pd.DataFrame:
    """Canonical rows from the vintage store as a single consistent vintage per key.

    Routed through `vintage_ingest.asof` rather than `read_observations` deliberately:
    the raw observations table holds every captured vintage, so a market-week with a
    revision appears twice, and differencing across those two rows would label CFTC
    correcting a number as a week of flow. `asof` collapses to one row per natural key,
    which is the precondition `flow.decompose` refuses to run without.

    With no `as_of` this means "everything known now", which is still one vintage per key.
    """
    from cotdata import vintage_ingest as vi

    t = pd.Timestamp.max if as_of is None else pd.Timestamp(as_of)
    frame = vi.asof(t, market_code=market_code, report_type=report_type)
    return _finish(frame, report_type=report_type, validate=validate)


def latest(*, report_type: str = "disaggregated", validate: bool = True) -> pd.DataFrame:
    """The most recent report week the vintage store holds, every market in it.

    The cross-section §6 of the handoff ranks over. Deliberately "the latest week the
    store has" rather than a date argument, so that a ranking cannot be quietly run
    against a stale week that happened to be typed into a script.
    """
    full = from_vintage(report_type=report_type, validate=validate)
    if full.empty:
        return full
    last = full["report_date"].max()
    return full[full["report_date"] == last].reset_index(drop=True)


def from_current_store(*, report_type: str = "disaggregated",
                       market_codes=None, validate: bool = True) -> pd.DataFrame:
    """Canonical rows built from the current-state parquets: the long history.

    **Not point-in-time, at any date.** These are current values with revisions applied,
    which is why this is a separately named function rather than a flag on `from_vintage`.
    Use it for schema validation, for history, and for anything descriptive. Do not use it
    to evaluate a rule as of a past date, because it cannot answer that question and will
    not say so.
    """
    from cotdata import config as cotcfg
    from cotdata import vintage_ingest as vi

    dirs = {"disaggregated": cotcfg.cot_disagg_dir, "tff": cotcfg.cot_tff_dir}
    if report_type not in dirs:
        raise PanelError(
            f"no current-state directory for report_type {report_type!r}; have "
            f"{sorted(dirs)}. Legacy is excluded on purpose: it drops non-commercial "
            f"spreading entirely, so its open-interest identity cannot close.")
    canon = {"disaggregated": vi.canonicalize_disagg, "tff": vi.canonicalize_tff}[report_type]

    wanted = None if market_codes is None else {str(c) for c in market_codes}
    frames = []
    for path in sorted(dirs[report_type]().glob("*.parquet")):
        wide = pd.read_parquet(path)
        if wide.empty:
            continue
        rows = canon(wide)
        if wanted is not None:
            rows = rows[rows["market_code"].isin(wanted)]
        if not rows.empty:
            frames.append(rows)
    if not frames:
        raise PanelError(
            f"no {report_type} parquet found under {dirs[report_type]()}. Is "
            f"COTDATA_STORE pointed at a populated store?")
    return _finish(pd.concat(frames, ignore_index=True), report_type=report_type,
                   validate=validate)


# ── Validation (handoff §2) ─────────────────────────────────────────────────
def _finish(frame: pd.DataFrame, *, report_type: str, validate: bool) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    out["report_date"] = pd.to_datetime(out["report_date"])
    for c in ("long_contracts", "short_contracts", "spread_contracts", "open_interest",
              "trader_count_long", "trader_count_short"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    if validate:
        require_columns(out)
        cfg.check_vocabulary(out["category"].unique(), report_type)
        require_one_row_per_key(out)
        require_single_series(out)
    return out.sort_values(SERIES_KEY + ["report_date"], kind="mergesort").reset_index(drop=True)


def require_columns(frame: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise PanelError(f"canonical panel is missing {missing}")


def require_one_row_per_key(frame: pd.DataFrame) -> None:
    """One row per (series key, report date), or refuse.

    A key with two rows for one week means two vintages of that week, and every engine
    downstream would compare them: `flow` would call the revision a flow, and `fragility`
    would double-count the category in `Q_sell`. Both produce a number rather than an
    error, so this has to raise here.
    """
    dup = frame.duplicated(subset=SERIES_KEY + ["report_date"])
    if dup.any():
        sample = frame.loc[dup, SERIES_KEY + ["report_date"]].head(3).to_dict("records")
        raise PanelError(
            f"{int(dup.sum())} duplicate (series key, report_date) rows, e.g. {sample}. "
            f"Two rows for one key-week are two VINTAGES: differencing them reads a CFTC "
            f"revision as a week of flow, and summing them double-counts the category. "
            f"Pass a point-in-time slice (vintage_ingest.asof).")


def require_single_series(frame: pd.DataFrame) -> None:
    """Futures-only and combined must not be mixed, per module spec §3.

    Cheap because `combined` is in the natural key, and worth asserting anyway: only
    futures-only is fetched today, so this column is constant-False and therefore not yet
    discriminating anything. The check is here so that the day the combined files are
    added, mixing them is a failure rather than a discovery.
    """
    if "combined" in frame.columns and frame["combined"].nunique(dropna=False) > 1:
        raise PanelError(
            "panel mixes futures-only and futures-and-options-combined rows. They are "
            "different series (module spec §3) and must not share a time series. Filter "
            "on `combined` before differencing.")


# ── The open-interest identity (handoff §2, §7) ─────────────────────────────
def oi_identity(frame: pd.DataFrame) -> pd.DataFrame:
    """Per market-week: do the category rows reconcile against open interest?

    Two facts, and they are separate:

    - **`balanced`**: `Σ long == Σ short` across categories, each side including spreading.
      True by construction in a closed zero-sum market, so a break is a category-mapping
      fault and not a market event.
    - **`oi_closes`**: `Σ long + spreading == open_interest`. True for Disaggregated and
      TFF, which publish spreading per category. Legacy does not, which is why Legacy is
      not loadable through this module at all.

    `spread_contracts` is a matched long and short held by one trader, so it is added to
    **both** side totals: it cancels out of the long-versus-short comparison but still
    counts toward open interest.

    Returns the per-market-week frame rather than a bool, because the handoff asks for the
    exception *rate* — a rising rate means the parse is drifting, and that is only visible
    as a series. `oi_identity_summary` reduces it.
    """
    keys = ["report_date", "market_code", "report_type", "combined"]
    missing = [c for c in keys + ["long_contracts", "short_contracts"] if c not in frame.columns]
    if missing:
        raise PanelError(f"cannot check the OI identity, missing {missing}")
    df = frame.copy()
    if "spread_contracts" not in df.columns:
        df["spread_contracts"] = pd.NA
    for c in ("long_contracts", "short_contracts", "spread_contracts", "open_interest"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce")

    g = df.groupby(keys, dropna=False, sort=False)
    out = g.agg(long_side=("long_contracts", "sum"),
                short_side=("short_contracts", "sum"),
                spread_total=("spread_contracts", "sum"),
                # `max`, not `sum`: open interest is the MARKET total, repeated on every
                # category row, because that is the shape of the CFTC file. Summing it
                # would multiply it by the category count.
                open_interest=("open_interest", "max"),
                n_categories=("category", "size")).reset_index()
    spread = out["spread_total"].fillna(0)
    out["long_total"] = out["long_side"] + spread
    out["short_total"] = out["short_side"] + spread
    out["imbalance"] = out["long_total"] - out["short_total"]
    out["oi_gap"] = out["open_interest"] - out["long_total"]
    out["balanced"] = out["imbalance"] == 0
    out["oi_closes"] = out["oi_gap"] == 0
    # CFTC's own rounding: the TFF "Consolidated" equity index markets aggregate several
    # contract sizes into a common unit, so they involve a division and can land a contract
    # or two off. Tolerance scales with the category count for the same reason.
    out["within_tolerance"] = out["imbalance"].abs() <= out["n_categories"].map(
        _rounding_tolerance)
    return out.drop(columns=["long_side", "short_side"])


def _rounding_tolerance(n_categories: int) -> int:
    from cotdata import vintage_ingest as vi

    return vi.rounding_tolerance(n_categories)


def oi_identity_summary(frame: pd.DataFrame, *, by_year: bool = False):
    """The exception rate the handoff asks to be reported rather than suppressed.

    Reported, never raised on. The identity failing is information about the parse, and a
    monitor that refuses to load rather than telling you the rate has hidden exactly the
    signal that was worth having. `by_year` is what makes "stable over history" answerable:
    a flat zero for twenty years and a zero that started last month are different facts.
    """
    ident = oi_identity(frame)
    if ident.empty:
        return pd.DataFrame()

    def _row(g: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "market_weeks": len(g),
            "unbalanced": int((~g["balanced"]).sum()),
            "unbalanced_rate": float((~g["balanced"]).mean()),
            "oi_gap_nonzero": int((~g["oi_closes"]).sum()),
            "oi_gap_rate": float((~g["oi_closes"]).mean()),
            "worst_abs_imbalance": float(g["imbalance"].abs().max()),
            "worst_abs_oi_gap": float(g["oi_gap"].abs().max()),
        })

    if not by_year:
        return _row(ident).to_frame("all").T
    ident = ident.assign(year=pd.to_datetime(ident["report_date"]).dt.year)
    return ident.groupby("year").apply(_row, include_groups=False)
