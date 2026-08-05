#!/usr/bin/env bash
# Publish the weekly damage panel, for a UI to read without importing this package.
#
# The consumer is cot-analyzer, which CANNOT import crowdmon: its production host runs
# Python 3.9 against this package's >=3.10 floor, it cannot produce the Norgate `unadj` and
# `propadj` prices the ladder needs however it is provisioned, and it records in three
# places that it computes no metrics of its own. So the seam is a file. See
# docs/adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md.
#
# CROWDMON_STORE is deliberately a DIFFERENT store from COTDATA_STORE, following npf's
# CMRDATA_STORE: this is a consumer's output, and writing it into the producer's store would
# put a consumer's artifact inside the data it reads.
#
# TIMING IS LOAD-BEARING, and not for the usual reason. bin/live-tests.sh records an
# observed incident (2026-08-03) where reading the store while it was being written made
# panels momentarily unreadable: that run reported 480 passed / 12 skipped against the usual
# 487 / 5. A test suite fails loudly in that situation. A PUBLISHER would write a panel with
# a third of the markets missing, and a short panel is a perfectly well-formed panel that
# nothing downstream would question. `publish._refuse_a_short_panel` is the guard, and the
# 09:15 slot (shared with the live tests, clear of the observed write windows) is why it
# should rarely fire.
#
# WHERE THIS RUNS, and the constraint is narrower than "Windows".
#
# This package runs anywhere the store is READABLE, macOS included, and does so on the full
# price-dependent chain: a local run builds all 49 markets, 47 of them with beta attached
# and both trigger sides. The other two carry no contract spec at all, so no machine can
# score them (2026-08-05 E4). Norgate being Windows-only constrains who can PRODUCE prices,
# not who can read a synced copy of them.
#
# What matters is that the panel is built UPSTREAM OF WHATEVER SHIPS IT. The dash server's
# sync originates on the Windows/Norgate box, so in practice that means publishing there;
# a panel built downstream of the sync is one the sync never sees. If the sync origin ever
# moves, this moves with it and no code changes.
#
# THIS SCRIPT AND THE LAUNCHD AGENT BESIDE IT ARE macOS/LINUX, and what they feed is a LOCAL
# cot-analyzer. Useful, and not a deploy. The production path is Windows Task Scheduler
# running scheduler copies of docs/examples/windows/run-publish.cmd and push-panel.cmd,
# chained behind errorlevel guards after the cotdata producer task. See README.md,
# "Scheduling it on the Windows producer".
#
# Usage:
#   ./bin/publish_damage.sh                  # build and write
#   ./bin/publish_damage.sh --dry-run        # build and summarise, write nothing
#
# Wire to launchd (local only): see bin/com.mspinola.crowdmon-publish.plist.example.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# launchd does not read ~/.zshrc or ~/.bash_profile, which is the only place these are
# exported, so default them here exactly as bin/live-tests.sh does. Both stores raise on
# unset rather than defaulting, so a miss would be loud anyway; this makes it work instead
# of relying on that.
export COTDATA_STORE="${COTDATA_STORE:-$HOME/code/cotdata_store}"
export CROWDMON_STORE="${CROWDMON_STORE:-$HOME/code/crowdmon_store}"
VENV_PY="${VENV_PY:-$REPO/.venv/bin/python}"

if [ ! -x "$VENV_PY" ]; then
    echo "no interpreter at $VENV_PY. Create it with:" >&2
    echo "  uv venv --python 3.11 && uv pip install -e \".[dev]\" -e ../cotdata -e ../marketdata" >&2
    exit 2
fi

if [ ! -d "$COTDATA_STORE" ]; then
    echo "COTDATA_STORE=$COTDATA_STORE does not exist. The panel is built from it, and a" >&2
    echo "missing store yields no panel rather than a short one." >&2
    exit 2
fi

echo "store   $COTDATA_STORE"
echo "out     $CROWDMON_STORE"
exec "$VENV_PY" bin/publish_damage.py "$@"
