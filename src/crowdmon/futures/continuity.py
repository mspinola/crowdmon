"""Is this code's history whole, and is this instrument split across more than one of them?

`coverage.py` answers "can this market produce a score at all", keyed on `market_code`, and
is emphatic that `market_name` is a display label. Both of those are right. Neither answers
the question underneath them: **a market_code is not an instrument, and a code's series can
have a hole in the middle.** Either one makes a long-lived market look like a young one, and
a young market is exactly what every stacked rolling window in this package refuses to score.

Found by the §10 evaluator, from the outside, and recorded as the third finding of
`2026-08-02 §B17`: "nothing in the panel says a market changed venue mid-history, and the
shorter series simply looks like a younger market".

---

## The case that produced this module

The Russell 2000 moved from ICE to CME. Both codes are in the TFF panel, and
`ContractMaster` already resolves both to `RTY` with `is_historical_code` set correctly, so
the information was present and nothing put it together:

| code | venue | weeks | span | longest internal gap |
|---|---|---|---|---|
| `239742` | CME | 587 | 2006-06-13 to 2026-07-28 | **3255 days, 8.9 years**, ending 2017-08-15 |
| `23977A` | ICE | 516 | 2008-07-22 to 2018-06-05 | none |

**The two are complementary, not redundant.** `23977A` covers `239742`'s hole almost exactly.
Together they are a continuous twenty-year market; apart, the CME code looks like it began in
2017, which is why `pct(D)` does not score it until 2023 and why the pre-registration's Feb
2018 unit landed on the **retiring** venue. A reader of either series alone cannot see this.

The other migration in the store is clean by comparison: lumber hands off from `058643` to
`058644` in 2023 with a two-month overlap and no holes on either side.

---

## A hole is not always a migration, which is the reason this reports both

Measured over all 51 codes in the two current-state panels: **46 have a longest inter-week gap
of 8 days**, which is a holiday shift and not a gap at all. The five that do not split into
two unrelated causes:

| code | longest gap | what it is |
|---|---|---|
| `239742` RTY | 3255 d | a venue migration, and a sibling code fills it |
| `004603` oats | 294 d | intermittent reporting. **No sibling. The absence is real** |
| `240741` NKD | 168 d | intermittent reporting. No sibling |
| `112741` NZD | 28 d | one missed month. No sibling |
| `058644` LBR | 21 d | at the tolerance, not over it |

So "this code has a hole" is not actionable on its own. **"This code has a hole and a sibling
code fills it" and "this code has a hole and nothing fills it" are opposite findings**, and
`gap_filled_by` is the column that separates them. Reporting only the first would invent
migrations for oats and the Nikkei.

## What this module does not do

It does not stitch the codes together. Concatenating `23977A` onto `239742` would produce a
continuous `RTY` series, and it would also splice two venues with different tick sizes,
different participants and a contract-size scale, which is a decision with consequences for
every rung above it. This reports the seam and leaves the splice to a caller who wants to
argue for it explicitly.
"""
from __future__ import annotations

import pandas as pd

#: A gap longer than this many days between consecutive report weeks is a hole rather than a
#: holiday shift. Measured: 46 of 51 codes never exceed 8 days, and the sixth-largest gap in
#: the store is 21. Above this and below 28 there is nothing, so the threshold is not
#: separating a continuum.
DEFAULT_TOLERANCE_DAYS = 21

CONTINUITY_COLUMNS = ["symbol", "market_code", "is_historical_code", "first", "last",
                      "weeks", "n_gaps", "longest_gap_days", "longest_gap_ends",
                      "gap_filled_by", "codes_for_symbol"]


class ContinuityError(ValueError):
    """The frame cannot support a continuity report."""


def _require(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise ContinuityError(
            f"continuity needs {missing}, which an annotated panel carries. Pass "
            f"`ContractMaster.load().annotate(panel)` rather than the raw panel.")


def _weeks(frame: pd.DataFrame, code: str) -> pd.DatetimeIndex:
    rows = frame.loc[frame["market_code"] == code, "report_date"]
    return pd.DatetimeIndex(sorted(pd.to_datetime(rows).unique()))


def _gaps(weeks: pd.DatetimeIndex, tolerance_days: int) -> list[tuple[pd.Timestamp, int]]:
    """`(ends_at, days)` for every jump longer than the tolerance. `ends_at` is the first
    week back, so the hole is the open interval before it."""
    if len(weeks) < 2:
        return []
    deltas = weeks.to_series().diff().dt.days
    return [(date, int(days)) for date, days in deltas.items()
            if pd.notna(days) and days > tolerance_days]


def continuity(annotated: pd.DataFrame, *,
               tolerance_days: int = DEFAULT_TOLERANCE_DAYS) -> pd.DataFrame:
    """One row per market_code: is its series whole, and does a sibling code fill any hole?

    `annotated` is a `ContractMaster.load().annotate(panel)` frame, which is where `symbol`
    and `is_historical_code` come from. A code with no spec keeps its row with a null symbol
    and is never grouped with another: an unresolved code is not evidence of a shared
    instrument, and treating nulls as a group would put every unmapped market in one bucket.
    """
    _require(annotated, ["report_date", "market_code", "symbol", "is_historical_code"])
    frame = annotated[["report_date", "market_code", "symbol",
                       "is_historical_code"]].copy()
    frame["report_date"] = pd.to_datetime(frame["report_date"])

    by_code = frame.drop_duplicates("market_code").set_index("market_code")
    # Siblings: same symbol, different code. Null symbols have none, by construction.
    named = frame.dropna(subset=["symbol"]).drop_duplicates(["symbol", "market_code"])
    siblings = named.groupby("symbol")["market_code"].apply(list).to_dict()

    rows = []
    for code in sorted(frame["market_code"].unique()):
        weeks = _weeks(frame, code)
        symbol = by_code.at[code, "symbol"]
        family = siblings.get(symbol, [code]) if pd.notna(symbol) else [code]
        others = [c for c in family if c != code]

        gaps = _gaps(weeks, tolerance_days)
        longest_days, longest_ends, filled_by = 0, pd.NaT, None
        if gaps:
            longest_ends, longest_days = max(gaps, key=lambda g: g[1])
            start = longest_ends - pd.Timedelta(days=longest_days)
            covering = [c for c in others
                        if ((_weeks(frame, c) > start) & (_weeks(frame, c) < longest_ends)).any()]
            filled_by = ", ".join(sorted(covering)) or None

        rows.append({
            "symbol": symbol, "market_code": code,
            "is_historical_code": bool(by_code.at[code, "is_historical_code"]),
            "first": weeks.min() if len(weeks) else pd.NaT,
            "last": weeks.max() if len(weeks) else pd.NaT,
            "weeks": len(weeks), "n_gaps": len(gaps),
            "longest_gap_days": longest_days, "longest_gap_ends": longest_ends,
            "gap_filled_by": filled_by, "codes_for_symbol": len(family),
        })
    frame = pd.DataFrame(rows, columns=CONTINUITY_COLUMNS)
    # Pin the sentinel to None rather than letting pandas choose. Constructing from dicts,
    # some pandas versions coerce a `None` in a column that also holds strings to `NaN`, and
    # **`NaN` is truthy**, so `if row["gap_filled_by"]` reads an UNFILLED gap as filled. That
    # inverts the one distinction this module exists to draw. Caught by CI on four of five
    # interpreters after passing locally on the fifth, which is the whole argument for not
    # trusting a single-environment green.
    filled = frame["gap_filled_by"]
    frame["gap_filled_by"] = filled.astype(object).where(filled.notna(), None)
    return frame


def migrations(annotated: pd.DataFrame, *,
               tolerance_days: int = DEFAULT_TOLERANCE_DAYS) -> pd.DataFrame:
    """Just the symbols served by more than one market_code, ordered so the handoff reads.

    This is the short list a cross-market result should be checked against: every row here is
    an instrument whose history is split, and whose individual codes therefore understate how
    long the market has existed.
    """
    frame = continuity(annotated, tolerance_days=tolerance_days)
    return (frame[frame["codes_for_symbol"] > 1]
            .sort_values(["symbol", "first"]).reset_index(drop=True))


def unexplained_gaps(annotated: pd.DataFrame, *,
                     tolerance_days: int = DEFAULT_TOLERANCE_DAYS) -> pd.DataFrame:
    """Codes with a hole that no sibling fills, so the absence is real rather than a seam.

    The complement of `migrations` for gap purposes, and the more dangerous list: these are
    markets that genuinely stop reporting for a stretch, so a window spanning the hole is
    built on fewer observations than its date range implies.
    """
    frame = continuity(annotated, tolerance_days=tolerance_days)
    return (frame[(frame["n_gaps"] > 0) & frame["gap_filled_by"].isna()]
            .sort_values("longest_gap_days", ascending=False).reset_index(drop=True))


def format_continuity(frame: pd.DataFrame) -> str:
    """A printable block. Pass the output of any of the three readers above."""
    if frame.empty:
        return "no rows"
    out = []
    for _, r in frame.iterrows():
        symbol = r["symbol"] if pd.notna(r["symbol"]) else "(unmapped)"
        line = (f"{r['market_code']:<7} {symbol:<6} "
                f"{r['first'].date()}..{r['last'].date()} {r['weeks']:>5} wk")
        if r["is_historical_code"]:
            line += "  HISTORICAL"
        if r["n_gaps"]:
            line += (f"  gap {r['longest_gap_days']}d "
                     f"({r['longest_gap_days'] / 365.25:.1f}y) ending "
                     f"{r['longest_gap_ends'].date()}")
            # `pd.notna`, never truthiness: a NaN sentinel is truthy and would print
            # "FILLED BY nan", reporting a seam where the absence is real. Defence in depth
            # beside `continuity`'s own normalisation, because a caller can hand this a frame
            # that has been round-tripped through a format that has no None.
            filled = r["gap_filled_by"]
            line += (f", FILLED BY {filled}" if pd.notna(filled) and str(filled).strip()
                     else ", UNFILLED")
        out.append(line)
    return "\n".join(out)
