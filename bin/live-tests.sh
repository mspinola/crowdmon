#!/usr/bin/env bash
# crowdmon live-test run — the 52 assertions CI structurally cannot make.
#
# CI runs against a two-panel fixture store, so every `tests/*_live.py` assertion skips
# there: the layer-2 trap-table figures, the appendix's cocoa arithmetic, the volume and
# trigger measurements. They need Norgate-sourced prices and a `contract_specs` table,
# which is a commercial subscription and cannot be committed to a public repo, plus the
# vintage store, which accumulates forward only from 2026-07-31 and cannot be downloaded
# at all. See bin/check_skips.py for the full argument.
#
# So this runs where the data is: locally, on a schedule, against the real store.
#
# The load-bearing part is `--profile live`. A run whose store is missing or unsynced would
# otherwise SKIP its way to a green exit and report success having verified nothing. Under
# that profile a data-absent skip is a failure.
#
# Wire to launchd: see bin/com.mspinola.crowdmon-live-tests.plist.example
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# launchd does not read ~/.zshrc or ~/.bash_profile, which is the only place
# COTDATA_STORE is exported, so default it here exactly as livebook/bin/daily.sh does.
# The store raises on unset rather than defaulting, so a miss would be loud anyway; this
# makes it work rather than relying on that.
export COTDATA_STORE="${COTDATA_STORE:-$HOME/code/cotdata_store}"
VENV_PY="${VENV_PY:-$REPO/.venv/bin/python}"

if [ ! -x "$VENV_PY" ]; then
    echo "no interpreter at $VENV_PY. Create it with:"
    echo "  cd $REPO && uv venv --python 3.11 && uv pip install -e '.[dev]' -e ../cotdata -e ../marketdata"
    exit 2
fi
if [ ! -d "$COTDATA_STORE" ]; then
    echo "COTDATA_STORE=$COTDATA_STORE does not exist. Nothing to verify against."
    exit 2
fi

REPORT="$(mktemp -t crowdmon-skips)"
trap 'rm -f "$REPORT"' EXIT

echo "store   : $COTDATA_STORE"
echo "python  : $VENV_PY"
echo "revision: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo

# `|| true` deliberately: a test failure must not stop the skip check, because "everything
# skipped" and "something failed" are different diagnoses and the log should carry both.
set +e
CROWDMON_SKIP_REPORT="$REPORT" "$VENV_PY" -m pytest tests/ -q -rs
PYTEST_RC=$?
set -e

echo
"$VENV_PY" bin/check_skips.py --profile live "$REPORT"
SKIP_RC=$?

echo
if [ "$PYTEST_RC" -ne 0 ]; then
    echo "RESULT: FAIL — pytest exited $PYTEST_RC"
elif [ "$SKIP_RC" -ne 0 ]; then
    echo "RESULT: FAIL — tests passed but a live assertion did not RUN (see above)"
else
    echo "RESULT: OK — the live suite ran against the real store and passed"
fi

[ "$PYTEST_RC" -eq 0 ] && [ "$SKIP_RC" -eq 0 ]
