"""Fixtures for the engine tests.

Two real panels, committed as parquet so the suite runs offline (`tests/fixtures/`, built
by `build_fixtures.py`), plus a synthetic-panel factory for the classification tests.

The synthetic factory exists because the four pure flow states are *definitions*, and a
definition should be tested against a case constructed to be unambiguous rather than
against real data where it happens to hold. Real data then tests that the definition
survives contact with it, which is a different question and is asked separately.
"""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def pytest_terminal_summary(terminalreporter) -> None:
    """Write every skip and its reason to `$CROWDMON_SKIP_REPORT`, when that is set.

    The suite's most valuable assertions are the `*_live.py` ones, and they are exactly the
    ones that **skip silently** when the store they need is absent. A green run therefore
    proves much less than it looks like it proves, and nothing in the ordinary output says
    which of the two happened. `bin/check_skips.py` turns this file into a pass or fail
    against a profile; see that module for what each profile allows and why.

    Off unless the env var is set, so an ordinary `pytest` is unchanged and no stray file
    appears in a working tree.
    """
    target = os.environ.get("CROWDMON_SKIP_REPORT")
    if not target:
        return
    rows = []
    for report in terminalreporter.stats.get("skipped", []):
        reason = ""
        longrepr = getattr(report, "longrepr", None)
        # A skip's longrepr is (fspath, lineno, "Skipped: <reason>"); anything else is a
        # shape pytest does not currently produce, so fall back rather than index blindly.
        if isinstance(longrepr, tuple) and len(longrepr) == 3:
            reason = str(longrepr[2]).removeprefix("Skipped: ").strip()
        else:
            reason = str(longrepr or "").strip()
        rows.append({"nodeid": report.nodeid, "reason": reason})
    rows.sort(key=lambda r: (r["nodeid"], r["reason"]))
    Path(target).write_text(json.dumps(rows, indent=2) + "\n")


@pytest.fixture(scope="session")
def history_panel() -> pd.DataFrame:
    """Gold, crude and oats, Disaggregated, 2006-06-13 to 2026-07-28.

    The long one. Current-state values with revisions applied, so it is not point-in-time
    and nothing here evaluates a rule against it — it is for schema and identity claims
    that need two decades to mean anything.
    """
    return pd.read_parquet(FIXTURES / "panel_disagg_history.parquet")


@pytest.fixture(scope="session")
def vintage_panel() -> pd.DataFrame:
    """The two ranked markets plus gold, from the vintage store, 2025-01-07 onward."""
    return pd.read_parquet(FIXTURES / "panel_disagg_vintage.parquet")


@pytest.fixture
def make_panel():
    """Build a canonical panel from per-week (long, short) pairs.

    Signature: `make_panel({"managed_money": [(100, 50), (140, 52)]}, ...)`, one tuple per
    consecutive report date. Open interest defaults to something comfortably larger than
    any position so that it never becomes the thing under test by accident.
    """
    def _make(series: dict[str, list[tuple[int, int]]], *,
              start: str = "2026-01-06", freq_days: int = 7,
              market_code: str = "TEST01", open_interest: int | None = None,
              report_type: str = "disaggregated", combined: bool = False,
              dates: list[str] | None = None) -> pd.DataFrame:
        n = len(next(iter(series.values())))
        if dates is not None:
            stamps = pd.to_datetime(dates)
        else:
            stamps = pd.date_range(start, periods=n, freq=f"{freq_days}D")
        biggest = max(max(long_ + short_ for long_, short_ in legs)
                      for legs in series.values())
        oi = open_interest if open_interest is not None else biggest * 10

        rows = []
        for category, legs in series.items():
            for stamp, (long_, short_) in zip(stamps, legs):
                rows.append({
                    "report_date": stamp, "market_code": market_code,
                    "market_name": f"TEST {market_code}", "report_type": report_type,
                    "combined": combined, "category": category,
                    "long_contracts": long_, "short_contracts": short_,
                    "spread_contracts": 0, "open_interest": oi,
                    "trader_count_long": 10, "trader_count_short": 10,
                })
        return pd.DataFrame(rows)
    return _make
