#!/usr/bin/env python3
"""Fail when a test SKIPPED for a reason its environment should not produce.

    CROWDMON_SKIP_REPORT=skips.json pytest tests/ -q
    python bin/check_skips.py --profile ci   skips.json
    python bin/check_skips.py --profile live skips.json

**Why this exists.** 65 of this package's assertions live in `tests/*_live.py` and need the
real store: the layer-2 trap-table figures (gold notional wrong by +294% in 2002, soybean
volatility 201x too high off `backadj`), the appendix's live-cattle arithmetic, the volume
and trigger measurements. Every one of them **skips silently** when the store is absent, and
CI runs against a two-panel fixture, so those 65 have never run in CI and a green badge has
never meant they passed. That is not a hypothetical failure mode; it is the current state,
and it is what this script exists to make visible.

The data cannot simply be committed. `manifests/prices.json` records `"source": "norgate"`
for both the price bars and the `contract_specs` table, Norgate is a commercial
subscription, and this repo is public. The vintage store is a second and independent
blocker: it accumulates forward only from 2026-07-31, so no download reconstructs it.

So the split is deliberate rather than a compromise waiting to be fixed:

- **CI** runs on fixtures and asserts the skip set is exactly the one a fixture store should
  produce. It cannot verify a real-store number, but it fails the moment a test starts
  skipping for a NEW reason, which is how a pin silently stops running.
- **`bin/live-tests.sh`** runs nightly against the real store under `--profile live`, where
  a data-absent skip is an ERROR. A run that skipped everything because the store was not
  synced fails loudly instead of passing green.

Exit codes: 0 clean, 1 a disallowed skip, 2 the report is missing or malformed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: Permanent design decisions. These skip in every environment and always will, so they are
#: allowed under every profile. Each is a substring match against the skip reason.
INTENTIONAL = (
    # cotdata dropped its duplicate decompose in cotdata#93; nothing left to compare.
    "removed as a duplicate",
    # The roll fixture deliberately ends after the last roll in its window.
    "fixture tail sits past the last roll",
    # test_boundaries walks ../cotdata and ../marketdata. Present in CI (the workflow checks
    # both out as siblings) and in the main checkout; ABSENT in a git worktree, because
    # WORKSPACE resolves relative to the test file. Allowed rather than fatal for that
    # reason, and it is why a worktree run is weaker than it looks.
    "not checked out beside this repo",
)

#: Skips that mean "this environment has no Norgate data". Expected under `ci`, and a
#: FAILURE under `live`, where their appearance means the store is missing or unsynced and
#: the run proved nothing.
DATA_ABSENT = (
    "store has no GC prices",
    "contract_specs table",
    "store not populated",
    "no readable store",
    "no readable TFF panel",
    # test_appendix_live.py, added with 2026-08-02 §B37. Three distinct guards, because the
    # appendix pins a NAMED market at a NAMED report week: the vintage panel may be
    # unreadable, present but not carrying 2026-07-28, or carrying it with no LE volume.
    "no readable vintage store",
    "store does not carry the appendix's market-week",
    "store has no LE volume",
)

PROFILES = {"ci": INTENTIONAL + DATA_ABSENT, "live": INTENTIONAL}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", type=Path, help="JSON written by CROWDMON_SKIP_REPORT")
    ap.add_argument("--profile", choices=sorted(PROFILES), required=True)
    args = ap.parse_args(argv)

    if not args.report.exists():
        print(f"FAIL: no skip report at {args.report}. Was CROWDMON_SKIP_REPORT set for "
              f"the pytest run? Without it conftest writes nothing and this check is "
              f"vacuous, which is the failure mode it exists to prevent.", file=sys.stderr)
        return 2
    try:
        rows = json.loads(args.report.read_text())
    except json.JSONDecodeError as exc:
        print(f"FAIL: {args.report} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    allowed = PROFILES[args.profile]
    bad = [r for r in rows if not any(frag in r["reason"] for frag in allowed)]

    print(f"skip check: profile={args.profile}, {len(rows)} skipped, {len(bad)} disallowed")
    for r in rows:
        mark = "DISALLOWED" if r in bad else "ok"
        print(f"  [{mark:10s}] {r['nodeid']}\n               {r['reason'][:110]}")

    if bad:
        print(f"\nFAIL: {len(bad)} test(s) skipped for a reason profile {args.profile!r} "
              f"does not allow.", file=sys.stderr)
        if args.profile == "live":
            print("Under `live` this almost always means COTDATA_STORE is unset, pointed "
                  "at a fixture, or not synced, so the run verified nothing it was "
                  "scheduled to verify. Check the store before touching this list.",
                  file=sys.stderr)
        else:
            print("A NEW skip reason appeared. Either a test grew a guard it should not "
                  "have, or a real dependency went missing. Do not add it to the allowlist "
                  "without establishing which.", file=sys.stderr)
        return 1

    print("OK: every skip is one this profile expects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
