"""Rendering primitives. Asset-class agnostic: no COT, no categories, no positioning.

House style for this project, and the reason this module exists at all: **prefer worked
numbers over abstract restatement, everywhere.** A walkthrough carries the numbers through
each formula in sequence, shows the arithmetic rather than only its result, and ends in
prose. The point is that a reader can check it, and a formula whose inputs are never
printed is a formula nobody has ever checked.

What lives here is only the part of that with no opinion about what is being measured:
turning a frame into a markdown table a person can actually read. The COT-specific builders
(category tables, `Q`/`Phi` arithmetic, flow sequences) are in `crowdmon.futures.report`,
because they know about reporting categories and the equity monitor will not. Module spec
§12 lists the report layer as shared between the two asset classes, and this is the half of
it that genuinely is.
"""
from __future__ import annotations

import pandas as pd

#: Integer columns that are labels or small counts rather than quantities, so a thousands
#: separator would be wrong or merely noisy. `year` is the one that actually misreads:
#: without this it renders as `2,026`.
NO_SEPARATOR = frozenset({"year", "days_elapsed", "traders", "d_traders",
                          "trader_count_long", "trader_count_short", "n_categories"})

#: Columns that are IDENTIFIERS and must never be read as numbers, however numeric they look.
#: CFTC market codes are zero-padded strings: `001612` is wheat, and rendering it as a number
#: gives `1,612`, which has lost the leading zeros and gained a separator. It is no longer a
#: code anyone can look up, and nothing about the output says so.
NEVER_NUMERIC = frozenset({"market_code", "cftc_contract_market_code", "contract_code",
                           "symbol", "snapshot_id", "row_sha256"})


def to_markdown(frame: pd.DataFrame, *, decimals: int = 4) -> str:
    """Markdown table with numbers formatted for reading rather than for round-tripping.

    Format is chosen per column rather than globally, because these frames mix contract
    counts in the hundreds of thousands with ratios in the hundredths. A single format
    renders one of the two unreadable: `{:,.4g}` turns 69,007 contracts into `6.901e+04`,
    which is the sort of table a reader skips rather than checks, and the house style here
    is that the arithmetic must be checkable.

    Hand-rolled rather than `DataFrame.to_markdown`, which needs `tabulate` — an undeclared
    dependency, and `tests/test_boundaries.py` fails on those by design.
    """
    if frame.empty:
        return "_(empty)_"
    disp = frame.copy()
    for c in disp.columns:
        col = disp[c]
        if pd.api.types.is_datetime64_any_dtype(col):
            disp[c] = col.dt.date.astype(str)
            continue
        numeric = None if str(c) in NEVER_NUMERIC else as_numeric(col)
        if numeric is None:
            disp[c] = col.map(lambda v: "" if pd.isna(v) else str(v))
            continue
        disp[c] = numeric.map(formatter(numeric, decimals, str(c)))
    head = "| " + " | ".join(disp.columns) + " |"
    rule = "|" + "|".join("---" for _ in disp.columns) + "|"
    body = ["| " + " | ".join(r) + " |" for r in disp.astype(str).to_numpy()]
    return "\n".join([head, rule, *body])


def as_numeric(col: pd.Series):
    """The column as numbers, or `None` if it is not a numeric column.

    Object columns have to be tried rather than skipped: several engine outputs are object
    dtype because they carry `pd.NA` alongside their values (`fuel_remaining` is populated
    only on short-covering weeks), and rendering those through `str` loses the thousands
    separators the rest of the table has.

    Booleans are excluded in both dtypes. `oi_corroborates` is object-dtype booleans, and
    letting it through renders True/False as 1/0 — which in a table whose other columns are
    contract counts reads as a quantity rather than as an answer.
    """
    if pd.api.types.is_bool_dtype(col):
        return None
    present = col[col.notna()]
    if not present.empty and present.map(lambda v: isinstance(v, bool)).all():
        return None
    if pd.api.types.is_numeric_dtype(col):
        return pd.to_numeric(col, errors="coerce")
    converted = pd.to_numeric(col, errors="coerce")
    if not present.empty and converted[col.notna()].notna().all():
        return converted
    return None


def formatter(values: pd.Series, decimals: int, name: str):
    """Pick one format for a whole column, from what the column actually holds.

    Three cases, because these frames mix contract counts in the hundreds of thousands with
    ratios in the hundredths and small labelling integers:

    - all-integral quantity: thousands separators, no decimals (`69,007`, `1,144`)
    - all-integral label or small count (`NO_SEPARATOR`): plain, so a year reads `2026`
      and `days_elapsed` reads `7` rather than `2,026` and `7.0000`
    - anything else: fixed decimals
    """
    present = values.dropna()
    if not present.empty and (present % 1 == 0).all():
        fmt = "{:.0f}" if name in NO_SEPARATOR else "{:,.0f}"
    else:
        fmt = f"{{:,.{decimals}f}}"
    return lambda v: "" if pd.isna(v) else fmt.format(v)
