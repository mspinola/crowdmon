"""Merging codes that a venue migration split, so `select_markets` stops dropping them twice.

`select_markets` maximises listwise-complete weeks and only ever sees a matrix, so a market
whose history is split across two CFTC codes presents as two short columns and loses twice.
The merge has to happen upstream, where the symbol is still known, and it has to happen on
LEVELS: summing differences loses the old code's final position instead of recording it as
the exit it was. That last one is the test worth reading.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import (
    MacroPcaError,
    merge_migrated_codes,
    positioning_panel,
    select_markets,
)


def _rows(code: str, symbol: str | None, values: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([
        {"report_date": pd.Timestamp(week), "market_code": code, "symbol": symbol,
         "category": "managed_money", "report_type": "disaggregated",
         "net_contracts": value}
        for week, value in values.items()])


def _weeks(start: str, n: int) -> list[str]:
    return [str(d.date()) for d in pd.date_range(start, periods=n, freq="7D")]


def _handoff() -> pd.DataFrame:
    """`OLD` runs for six weeks and stops; `NEW` starts the week after. A clean migration."""
    weeks = _weeks("2023-01-03", 8)
    old = _rows("OLD", "SYM", {w: 100.0 for w in weeks[:6]})
    new = _rows("NEW", "SYM", {w: 10.0 for w in weeks[6:]})
    other = _rows("KEEP", "OTH", {w: float(i) for i, w in enumerate(weeks)})
    return pd.concat([old, new, other], ignore_index=True)


# ── the reason it happens before the difference ──────────────────────────────
def test_the_exit_is_recorded_as_a_change_not_lost_to_a_nan():
    """The discriminating case between merging levels and merging differences.

    `OLD` holds 100 in its final week and `NEW` opens at 10. On levels the merged series
    steps 100 -> 10 and the difference records **-90**, which is the position leaving. Sum the
    differences instead and both inputs are `NaN` in that week (one series has ended, the
    other has no prior value), so the exit silently never happens.
    """
    merged = positioning_panel(_handoff(), merge_migrations=True)
    step = merged.loc[pd.Timestamp(_weeks("2023-01-03", 8)[6]), "SYM"]
    assert step == pytest.approx(-90.0), (
        f"the handoff must record the position leaving, got {step!r}")

    levels = positioning_panel(_handoff(), merge_migrations=True, difference=False)
    assert levels["SYM"].tolist() == [100.0] * 6 + [10.0] * 2


def test_merging_after_the_difference_would_lose_it():
    """Guards the ordering by demonstrating the wrong answer, so a refactor that moves the
    merge below the `.diff()` fails here rather than in someone's PCA."""
    differenced = positioning_panel(_handoff())          # unmerged, already differenced
    wrong = differenced[["OLD", "NEW"]].sum(axis=1, min_count=1)
    assert pd.isna(wrong.iloc[6]), (
        "if this is ever not NaN the premise changed; the merge order argument needs redoing")


# ── what it does ─────────────────────────────────────────────────────────────
def test_the_merged_column_is_named_for_the_instrument():
    merged = positioning_panel(_handoff(), merge_migrations=True)
    assert "SYM" in merged.columns
    assert "OLD" not in merged.columns and "NEW" not in merged.columns
    assert "KEEP" in merged.columns, "a single-code market must be untouched"


def test_select_markets_recovers_the_split_market():
    frame = _handoff()
    before = select_markets(positioning_panel(frame), min_markets=1)
    after = select_markets(positioning_panel(frame, merge_migrations=True), min_markets=1)
    assert "SYM" in after, "the whole point: the split market rejoins the panel"
    assert "OLD" not in before and "NEW" not in before


def test_default_is_off_and_output_is_unchanged():
    """Additive only. Turning this on changes every downstream figure, so it must be asked
    for rather than inherited."""
    frame = _handoff()
    assert positioning_panel(frame).equals(
        positioning_panel(frame, merge_migrations=False))
    assert "OLD" in positioning_panel(frame).columns


# ── the guards ───────────────────────────────────────────────────────────────
def test_concurrent_codes_are_not_summed():
    """Two codes reporting together throughout are an aggregate and its components, or a
    double count. Summing them would count the same open interest twice, which is a worse
    failure than dropping a market, so they are left alone."""
    weeks = _weeks("2023-01-03", 8)
    a = _rows("AGG", "SYM", {w: 100.0 for w in weeks})
    b = _rows("PART", "SYM", {w: 40.0 for w in weeks})
    merged = positioning_panel(pd.concat([a, b], ignore_index=True), merge_migrations=True)
    assert {"AGG", "PART"} <= set(merged.columns), "concurrent codes must stay separate"
    assert "SYM" not in merged.columns


def test_the_concurrency_bar_is_adjustable_and_bites_in_the_right_direction():
    weeks = _weeks("2023-01-03", 8)
    a = _rows("AGG", "SYM", {w: 100.0 for w in weeks})
    b = _rows("PART", "SYM", {w: 40.0 for w in weeks})
    frame = pd.concat([a, b], ignore_index=True)
    permissive = positioning_panel(frame, merge_migrations=True, max_concurrent_share=1.0)
    assert "SYM" in permissive.columns, "at a share of 1.0 nothing is rejected"


def test_null_symbols_are_never_merged():
    """An unresolved code is not evidence of a shared instrument. Grouping on a null symbol
    would make every unmapped market a sibling of every other."""
    weeks = _weeks("2023-01-03", 8)
    frame = pd.concat([_rows("NOSPEC1", None, {w: 1.0 for w in weeks[:4]}),
                       _rows("NOSPEC2", None, {w: 2.0 for w in weeks[4:]})],
                      ignore_index=True)
    merged = positioning_panel(frame, merge_migrations=True)
    assert {"NOSPEC1", "NOSPEC2"} <= set(merged.columns)


def test_an_unannotated_frame_is_refused_with_the_fix_named():
    frame = _handoff().drop(columns=["symbol"])
    with pytest.raises(MacroPcaError, match="annotate"):
        positioning_panel(frame, merge_migrations=True)


def test_merge_is_callable_directly_on_a_level_matrix():
    frame = _handoff()
    levels = positioning_panel(frame, difference=False)
    merged = merge_migrated_codes(levels, frame)
    assert "SYM" in merged.columns
    assert merged["SYM"].tolist() == [100.0] * 6 + [10.0] * 2


def test_a_single_code_symbol_is_left_completely_alone():
    weeks = _weeks("2023-01-03", 6)
    frame = _rows("ONLY", "SYM", {w: float(i) for i, w in enumerate(weeks)})
    levels = positioning_panel(frame, difference=False)
    merged = merge_migrated_codes(levels, frame)
    assert list(merged.columns) == ["ONLY"]
    assert np.allclose(merged["ONLY"], levels["ONLY"])
