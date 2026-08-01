"""Rebuild the committed test fixtures from the real store.

Not run by the test suite: the fixtures are committed so tests run offline, and this exists
so the committed files have a reproducer rather than being unexplained binaries in the
repo. Every figure quoted in `docs/analysis/` comes from one of these two frames or from
the full store, and this script says exactly which rows the first two are.

    COTDATA_STORE=~/code/cotdata_store python tests/fixtures/build_fixtures.py

Market selection, and why each is here:

- `088691` GOLD — a large, liquid, well-understood market, present in both fixtures so the
  two can be cross-checked against each other.
- `067651` CRUDE OIL — a second liquid market, so no test passes on a single series.
- `004603` OATS — the thin-market gap case, and the reason `flow.decompose` has a gap rule
  at all. It falls below the reporting threshold and drops out of the report, giving a
  294-day interval ending 2025-09-09 and five more over 50 days. Nothing else in the
  Disaggregated universe exercises that path.
- `0063CU` CALIF LOW CARBON, `02339S` CIG ROCKIES FINANCIAL INDEX — the two markets the
  latest-week ranking selected, so the walkthroughs' arithmetic is checkable offline.

The history fixture spans 2006-06-13 to 2026-07-28, which is what makes the Phi-bound test
a claim about twenty years rather than about one capture.
"""
from pathlib import Path

from crowdmon.futures import from_current_store, from_vintage

HERE = Path(__file__).resolve().parent

#: Dropped from the vintage fixture: bitemporal bookkeeping this package never reads, and
#: `row_sha256` in particular is a permanent artifact of cotdata's revision detection that
#: has no business being duplicated into another repo's test data.
VINTAGE_DROP = ("row_sha256", "snapshot_id", "is_tombstone")


def main() -> None:
    history = from_current_store(market_codes=["088691", "067651", "004603"])
    history.to_parquet(HERE / "panel_disagg_history.parquet", index=False)
    print(f"history: {len(history):,} rows, "
          f"{history['report_date'].min().date()} to {history['report_date'].max().date()}")

    vintage = from_vintage()
    vintage = vintage[vintage["market_code"].isin(["0063CU", "02339S", "088691"])]
    vintage = vintage[[c for c in vintage.columns if c not in VINTAGE_DROP]]
    vintage.to_parquet(HERE / "panel_disagg_vintage.parquet", index=False)
    print(f"vintage: {len(vintage):,} rows, "
          f"{vintage['report_date'].min().date()} to {vintage['report_date'].max().date()}")


if __name__ == "__main__":
    main()
