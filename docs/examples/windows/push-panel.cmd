@echo off
REM crowdmon damage panel push to the REMOTE Linux dash server, over rsync + SSH.
REM Chained after run-publish.cmd behind an errorlevel guard, so it fires at a
REM known-consistent moment rather than on a timer that might land mid-write.
REM
REM Copy this OUT of the repo into your scheduler directory and fill in the markers
REM there. Same convention as cotdata's docs/examples/windows/push-to-server.cmd, which
REM this is modelled on line for line; read that file's header for the full reasoning
REM behind the Cygwin choices, which apply here unchanged.
REM
REM WHY A SEPARATE PUSH. CROWDMON_STORE is a different store ROOT from COTDATA_STORE, so
REM cotdata's push does not carry it and no exclusion list change would make it. That
REM separation is deliberate: the panel is a consumer's output and does not belong inside
REM the producer's data.
REM
REM This is small. Roughly 4 MB of parquet plus 220 KB of blocks per week, eight weeks
REM retained, and only the newest dated directory changes between runs.
REM
REM -- The three Cygwin-rsync gotchas, same as cotdata's push --------------------
REM 1. Use the ssh that SHIPS WITH rsync, never native Windows OpenSSH: a Cygwin rsync
REM    driving native ssh corrupts the binary stream and dies with
REM      "connection unexpectedly closed (0 bytes received so far)".
REM 2. That Cygwin ssh has no HOME, so give it an explicit writable UserKnownHostsFile.
REM 3. All local paths are cygdrive form, including the key.
REM -----------------------------------------------------------------------------
REM
REM Overwrite the markers below. Do NOT use angle brackets in a .cmd file.
REM   REPLACE_WITH_SSH_EXE_CYG     = the ssh that ships with rsync, cygdrive form
REM                                  e.g. /cygdrive/c/ProgramData/chocolatey/lib/rsync/tools/bin/ssh.exe
REM   REPLACE_WITH_SSH_KEY_CYG     = batch SSH private key, cygdrive form
REM   REPLACE_WITH_KNOWN_HOSTS_CYG = a writable known_hosts, cygdrive form
REM   REPLACE_WITH_PANEL_PATH_CYG  = source CROWDMON_STORE, cygdrive form
REM                                  e.g. /cygdrive/c/Users/you/crowdmon_store
REM   REPLACE_WITH_REMOTE          = user@host:/path/to/crowdmon_store (no trailing slash)
REM                                  A SIBLING of the workspace on the server, which is
REM                                  where cot-analyzer's reader looks by default:
REM                                  e.g. deploy@dash.example.com:/root/crowdmon_store

setlocal
set "RSYNC=C:\ProgramData\chocolatey\bin\rsync.exe"
set "SSH_EXE=REPLACE_WITH_SSH_EXE_CYG"
set "KEY=REPLACE_WITH_SSH_KEY_CYG"
set "KNOWN=REPLACE_WITH_KNOWN_HOSTS_CYG"
set "SRC=REPLACE_WITH_PANEL_PATH_CYG"
set "DEST=REPLACE_WITH_REMOTE"
set "SSH=%SSH_EXE% -i %KEY% -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=%KNOWN%"

REM DATED DIRECTORIES FIRST, MANIFEST LAST, and here that ordering is load-bearing rather
REM than merely tidy. The reader resolves the current week THROUGH manifest.json, so a
REM manifest naming a directory that has not landed is caught and reported as a partial
REM sync; the reverse, data present and manifest stale, silently serves last week as
REM though it were this week. There is deliberately no `latest` symlink for the same
REM reason. See src/crowdmon/futures/publish.py::publish_panel.
REM
REM --delete makes this a true mirror, which is what prunes a week the publisher has
REM already dropped from its rolling window. Nothing on the server owns anything under
REM this root, so unlike cotdata's push there is no consumer-owned directory to exclude.
REM *.tmp and the dot-prefixed staging directories are the publisher's atomic-write temps
REM and must never propagate half-written.
"%RSYNC%" -az --delete ^
  --exclude "manifest.json" --exclude "*.tmp" --exclude ".*" ^
  -e "%SSH%" "%SRC%/damage/" "%DEST%/damage/"
if %ERRORLEVEL% NEQ 0 ( echo panel push FAILED, rsync code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

REM manifest.json last, once every directory it can name is on the far side.
"%RSYNC%" -az -e "%SSH%" "%SRC%/damage/manifest.json" "%DEST%/damage/manifest.json"
if %ERRORLEVEL% NEQ 0 ( echo manifest push FAILED, rsync code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

REM No service restart needed. cot-analyzer's reader caches on the manifest's mtime, so a
REM fresh sync is picked up on the next request without touching the systemd unit. That
REM is unlike a cotdata store push, whose consumers hold an in-process indexer.
echo panel push ok
exit /b 0
