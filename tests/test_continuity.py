"""A code's series can have a hole, and an instrument can be split across codes.

The distinction the module exists for is `gap_filled_by`: a hole a sibling code covers is a
venue seam, a hole nothing covers is a market that stopped reporting. Both look identical in
the panel and they are opposite findings, so most of these tests are about telling them apart.
"""
from __future__ import annotations

import pandas as pd
import pytest

from crowdmon.futures import (
    ContinuityError,
    continuity,
    format_continuity,
    migrations,
    unexplained_gaps,
)


def _panel(code: str, symbol: str | None, weeks: list[str], *,
           historical: bool = False) -> pd.DataFrame:
    """One code's report weeks, at the annotated-panel grain (two categories per week, so
    the readers have to de-duplicate rather than count rows)."""
    rows = []
    for week in weeks:
        for category in ("managed_money", "swap"):
            rows.append({"report_date": pd.Timestamp(week), "market_code": code,
                         "symbol": symbol, "is_historical_code": historical,
                         "category": category})
    return pd.DataFrame(rows)


def _weekly(start: str, n: int) -> list[str]:
    return [str(d.date()) for d in pd.date_range(start, periods=n, freq="7D")]


# ── the shape that produced the module ───────────────────────────────────────
def _rty_shaped() -> pd.DataFrame:
    """A current code with a hole, and a historical code that fills it. RTY in miniature."""
    current = _panel("CURRENT", "XX", _weekly("2006-01-06", 8) + _weekly("2017-01-06", 8))
    historical = _panel("HIST", "XX", _weekly("2008-01-04", 40), historical=True)
    return pd.concat([current, historical], ignore_index=True)


def test_a_hole_a_sibling_covers_is_reported_as_filled():
    got = continuity(_rty_shaped()).set_index("market_code")
    row = got.loc["CURRENT"]
    assert row["n_gaps"] == 1
    assert row["longest_gap_days"] > 3000
    assert row["gap_filled_by"] == "HIST", (
        "a sibling code covering the hole is the whole point of the report")
    assert row["codes_for_symbol"] == 2


def test_the_sibling_itself_is_whole():
    got = continuity(_rty_shaped()).set_index("market_code")
    assert got.loc["HIST", "n_gaps"] == 0
    assert got.loc["HIST", "is_historical_code"]


def test_a_hole_nothing_covers_is_left_unfilled():
    """Oats and the Nikkei: intermittent reporting with no sibling. The absence is real."""
    lonely = _panel("SOLO", "YY", _weekly("2010-01-01", 8) + _weekly("2012-01-06", 8))
    row = continuity(lonely).iloc[0]
    assert row["n_gaps"] == 1
    assert row["gap_filled_by"] is None, (
        "no sibling exists, so this must not be reported as a seam")
    assert row["codes_for_symbol"] == 1


def test_unexplained_gaps_excludes_the_covered_one():
    frame = pd.concat([_rty_shaped(),
                       _panel("SOLO", "YY", _weekly("2010-01-01", 8) + _weekly("2012-01-06", 8))],
                      ignore_index=True)
    got = unexplained_gaps(frame)
    assert list(got["market_code"]) == ["SOLO"], (
        f"only the uncovered hole is unexplained, got {list(got['market_code'])}")


def test_migrations_lists_only_split_symbols_oldest_first():
    frame = pd.concat([_rty_shaped(), _panel("ALONE", "ZZ", _weekly("2010-01-01", 20))],
                      ignore_index=True)
    got = migrations(frame)
    assert set(got["market_code"]) == {"CURRENT", "HIST"}
    assert "ALONE" not in set(got["market_code"])
    assert got["first"].is_monotonic_increasing


# ── the trap: nulls must never be grouped ────────────────────────────────────
def test_unmapped_codes_are_never_treated_as_one_instrument():
    """Two codes with no ContractMaster spec share a null symbol. Grouping on that would
    make every unmapped market a sibling of every other, and invent a migration."""
    frame = pd.concat([_panel("NOSPEC1", None, _weekly("2010-01-01", 6) + _weekly("2015-01-02", 6)),
                       _panel("NOSPEC2", None, _weekly("2012-01-06", 40))],
                      ignore_index=True)
    got = continuity(frame).set_index("market_code")
    assert got.loc["NOSPEC1", "codes_for_symbol"] == 1
    assert got.loc["NOSPEC1", "gap_filled_by"] is None, (
        "an unresolved code is not evidence of a shared instrument")
    assert got.loc["NOSPEC2", "codes_for_symbol"] == 1


# ── boundaries and plumbing ──────────────────────────────────────────────────
def test_holiday_shifts_are_not_gaps():
    """46 of 51 real codes top out at an 8-day gap. None of them is a hole."""
    weeks = [str(d.date()) for d in pd.to_datetime(
        ["2020-01-07", "2020-01-14", "2020-01-22", "2020-01-28", "2020-02-04"])]
    assert continuity(_panel("C", "S", weeks)).iloc[0]["n_gaps"] == 0


def test_tolerance_is_exclusive_at_the_boundary():
    """Lumber's single 21-day gap sits exactly at the default and must not be reported."""
    weeks = ["2023-01-03", "2023-01-24"]          # 21 days apart
    assert continuity(_panel("C", "S", weeks)).iloc[0]["n_gaps"] == 0
    assert continuity(_panel("C", "S", weeks), tolerance_days=20).iloc[0]["n_gaps"] == 1


def test_weeks_counts_report_weeks_not_rows():
    got = continuity(_panel("C", "S", _weekly("2020-01-07", 10)))
    assert got.iloc[0]["weeks"] == 10, "two categories per week must not double the count"


def test_a_raw_panel_is_refused_with_the_fix_named():
    raw = _panel("C", "S", _weekly("2020-01-07", 4)).drop(columns=["symbol"])
    with pytest.raises(ContinuityError, match="annotate"):
        continuity(raw)


def test_format_names_the_seam_and_the_absence_differently():
    frame = pd.concat([_rty_shaped(),
                       _panel("SOLO", "YY", _weekly("2010-01-01", 8) + _weekly("2012-01-06", 8))],
                      ignore_index=True)
    text = format_continuity(continuity(frame))
    assert "FILLED BY HIST" in text
    assert "UNFILLED" in text
    assert "HISTORICAL" in text


def test_a_nan_sentinel_still_reads_as_unfilled():
    """Regression, and the nastiest failure this module can have.

    Some pandas versions coerce the `None` sentinel to `NaN` in a column that also holds
    strings. **`NaN` is truthy**, so a truthiness check prints "FILLED BY nan" and reports a
    venue seam where the absence is real, which inverts the module's whole distinction. This
    forces the NaN rather than hoping for a pandas version that produces it.
    """
    frame = continuity(_panel("SOLO", "YY", _weekly("2010-01-01", 8) + _weekly("2012-01-06", 8)))
    frame.loc[:, "gap_filled_by"] = float("nan")
    text = format_continuity(frame)
    assert "UNFILLED" in text
    assert "nan" not in text.lower(), f"a NaN sentinel must never print as a sibling: {text}"


def test_the_sentinel_is_none_not_nan_in_a_mixed_frame():
    """The normalisation that stops the above arising in the first place. A frame holding
    both a filled and an unfilled gap is where the coercion happens."""
    frame = pd.concat([_rty_shaped(),
                       _panel("SOLO", "YY", _weekly("2010-01-01", 8) + _weekly("2012-01-06", 8))],
                      ignore_index=True)
    got = continuity(frame).set_index("market_code")
    assert got.loc["CURRENT", "gap_filled_by"] == "HIST"
    assert got.loc["SOLO", "gap_filled_by"] is None, (
        f"expected a None sentinel, got {got.loc['SOLO', 'gap_filled_by']!r}")


def test_empty_format_does_not_raise():
    empty = _panel("C", "S", _weekly("2020-01-07", 1)).iloc[:0]
    assert format_continuity(continuity(empty)) == "no rows"
