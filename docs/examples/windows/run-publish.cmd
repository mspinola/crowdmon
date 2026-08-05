@echo off
REM Build the crowdmon damage panel on the Windows producer.
REM
REM Copy this OUT of the repo into your scheduler directory (e.g.
REM C:\Users\you\crowdmon\scheduler\) and fill in the markers there, so a `git pull`
REM never clobbers your edited paths. Same convention as cotdata's
REM docs/examples/windows/run-prices.cmd.
REM
REM WHY THIS RUNS HERE. The panel needs `unadj` AND `propadj` prices, and `propadj` is
REM derived on read from `unadj` + `backadj`, so BOTH stored tiers are a precondition.
REM Norgate is the only vendor supplying all of them and it is Windows-only, so this box
REM is the only one that can build a panel from a store it produced itself. Not a Python
REM constraint: see docs/design/amendments-2026-08-04.md D14.
REM
REM WHY NOT bin/publish_damage.sh. That is bash, and the launchd agent beside it is
REM macOS. Neither runs here. bin/publish_damage.py is the portable driver and is what
REM this calls, using the venv's python by full path because Task Scheduler runs with a
REM bare environment where a `python` on PATH may not resolve.
REM
REM ORDER. Chain this AFTER the cotdata producer task and BEFORE push-panel.cmd, behind
REM an errorlevel guard, exactly as cotdata chains sync-store.cmd. Publishing before the
REM prices land builds last week's panel; pushing before publishing ships it.
REM
REM Overwrite the markers below. Do NOT use angle brackets in a .cmd file: cmd reads them
REM as redirection and the file fails even on comment lines.
REM   REPLACE_WITH_COTDATA_STORE  = the store this box produces
REM                                 e.g. C:\Users\you\cotdata_store
REM   REPLACE_WITH_CROWDMON_STORE = where the panel is written. A DIFFERENT root from the
REM                                 store above, deliberately: this is a consumer's output,
REM                                 not the producer's data
REM                                 e.g. C:\Users\you\crowdmon_store
REM   REPLACE_WITH_REPO_PATH      = the crowdmon checkout
REM                                 e.g. C:\Users\you\code\crowdmon
REM   REPLACE_WITH_VENV_PATH      = its virtualenv, Python >=3.10
REM                                 e.g. C:\Users\you\code\crowdmon\.venv

setlocal
set "COTDATA_STORE=REPLACE_WITH_COTDATA_STORE"
set "CROWDMON_STORE=REPLACE_WITH_CROWDMON_STORE"
set "REPO=REPLACE_WITH_REPO_PATH"
set "VENV=REPLACE_WITH_VENV_PATH"

cd /d "%REPO%"
if %ERRORLEVEL% NEQ 0 ( echo cannot cd to %REPO% & exit /b 1 )

REM --dry-run first if you are verifying a new box: it builds and summarises without
REM writing. The real run prints the same summary and then the path it wrote.
"%VENV%\Scripts\python.exe" bin\publish_damage.py
if %ERRORLEVEL% NEQ 0 ( echo publish FAILED, code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

REM Non-zero here is a real failure and Task Scheduler already treats it as one. The
REM interesting case is the one that is NOT an exception: a run that reads the store
REM mid-write produces a SHORT panel, which is a perfectly well-formed panel nothing
REM downstream would question. publish._refuse_a_short_panel refuses a market count below
REM 80%% of the previous publish and exits non-zero, so that arrives here rather than as a
REM quietly wrong dashboard. (%% is an escaped percent sign; a bare %% in a .cmd is eaten.)
echo publish ok
exit /b 0
