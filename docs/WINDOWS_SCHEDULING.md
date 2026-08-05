# Scheduling crowdmon on Windows (Task Scheduler)

**Read [`cotdata/docs/WINDOWS_SCHEDULING.md`](../../cotdata/docs/WINDOWS_SCHEDULING.md)
first.** It creates the producer tasks that everything here depends on, and it holds the
Task Scheduler material that is not specific to this package: the `schtasks` syntax, the
Friday COT release trigger, restart-on-failure, the interactive-session requirement, and the
troubleshooting list.

This file is deliberately thin and covers only what is different here. It does not restate
any of that, because a second copy of a living document drifts from the first and nobody
notices until someone diffs them (see `CLAUDE.md`, "The copy lost 104 lines and nobody
noticed for a day").

## What is scheduled here, and what is not

Two steps, and **neither gets its own timer**:

| step | template | does |
|---|---|---|
| publish | [`docs/examples/windows/run-publish.cmd`](examples/windows/run-publish.cmd) | builds the panel from the store, writes it to `CROWDMON_STORE` |
| push | [`docs/examples/windows/push-panel.cmd`](examples/windows/push-panel.cmd) | rsyncs the panel to the Linux dash server |

They are **chained onto the end of the cotdata prices task**, because the prices task has no
fixed finish time. `--require-final` defers with a non-zero exit until Norgate's Data Updater
has actually pulled the Finals, and restart-on-failure retries it every 10 minutes up to 6
times, so a task that fires at 20:55 can complete any time up to roughly an hour later. A
publish on its own 21:30 timer would build last week's panel on every slow night and look
entirely successful doing it.

The ordering is prices, then publish, then push. Publishing before the prices land builds
last week's panel; pushing before publishing ships it. **Nothing in the code enforces this.**

## The chain wrapper

Create one `.cmd` in your scheduler directory that calls the others in order. Keep it beside
the copies of the templates, outside both repos, so a `git pull` never touches it.

```bat
@echo off
REM crowdmon nightly chain. Lives in the scheduler directory, not in either repo.
REM Substitute your own scheduler path for C:\Users\you\scheduler below.

call "C:\Users\you\scheduler\run-prices.cmd"
if %ERRORLEVEL% NEQ 0 ( echo prices deferred or failed, code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

call "C:\Users\you\scheduler\run-publish.cmd"
if %ERRORLEVEL% NEQ 0 ( echo publish FAILED, code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

call "C:\Users\you\scheduler\push-to-server.cmd"
if %ERRORLEVEL% NEQ 0 ( echo store push FAILED, code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

call "C:\Users\you\scheduler\push-panel.cmd"
if %ERRORLEVEL% NEQ 0 ( echo panel push FAILED, code %ERRORLEVEL% & exit /b %ERRORLEVEL% )

echo nightly chain ok
exit /b 0
```

**The `call` is load-bearing and its absence is silent.** `cmd` treats a bare `.cmd`
invocation from inside another `.cmd` as a **transfer of control**, not a subroutine: it runs
the second script and then exits, never returning to the parent. Without `call` on the first
line, this file is an elaborate way to run `run-prices.cmd` alone, the publish and both
pushes never execute, and the task reports success. There is no error and nothing in the log
to look at.

The store push sits between publish and panel push so the server never briefly holds a panel
derived from data it has not received. Drop that line if this box does not also push the
cotdata store.

## Registering it

Repoint the **existing** cotdata prices task at the chain rather than creating a second task,
so there is one owner of the schedule and the restart-on-failure setting you already
configured covers the whole chain:

```bat
schtasks /Change /TN "cotdata prices" /TR "C:\Users\you\scheduler\run-nightly.cmd"
```

Verify it points somewhere real, since `schtasks` takes `/TR` as a literal string and does
not check the file exists:

```powershell
Get-ScheduledTask -TaskName "cotdata prices" | Select-Object TaskName, @{n='Action';e={$_.Actions.Execute}}
```

**Retrying the whole chain is the intended behaviour, and it is not free.** A push that fails
on a network blip re-runs the price fetch on the next retry. That fetch is idempotent, and so
is the publish (`publish_panel` replaces a dated directory that already exists), so a retry is
correct rather than merely tolerable. It just is not instant. If that becomes a problem the
answer is a separate event-triggered task, not a wrapper that swallows an exit code.

**Task settings.** The chain inherits everything from the prices task, which means it already
has the two settings that matter: "Run only when user is logged on" (required, because
`norgatedata` talks to the Norgate Data Updater in your desktop session) and, on anything
portable, the AC-power condition unchecked. The crowdmon steps need neither on their own
account, and inheriting them costs nothing.

## Verifying a run

Task Scheduler's Last Run Result is not a sufficient signal, for the same reason it is not
one in cotdata: a deferred `--require-final` price run exits non-zero by design. Read the
manifest instead.

```powershell
Get-Content C:\Users\you\crowdmon_store\damage\manifest.json | ConvertFrom-Json |
  Select-Object current_report_date,
    @{n='built_at'; e={$_.provenance.built_at}},
    @{n='markets';  e={$_.counts.markets}}
```

Three fields, answering three different questions:

- **`current_report_date`** is the CFTC report week. It advances weekly, not daily.
- **`provenance.built_at`** is the wall clock. This is the field that catches a schedule that
  quietly stopped: COT is weekly, so a dead job produces no new report week to notice, and a
  panel can be current on the week and months old on the clock.
- **`counts.markets`** should be 49 on a healthy store. A number materially below that is the
  thing to look at, not a curiosity.

## The two failure modes that are specific to the panel

**A short panel is a well-formed panel.** Reading the store mid-write does not raise; it
produces a panel with fewer markets, which nothing downstream would question and which
becomes "this week's findings" on the dashboard. `publish._refuse_a_short_panel` compares
against the previous manifest's market count and exits non-zero below 80%, so it arrives as a
failed task rather than a quietly wrong page. The scheduler notification is the **only**
channel that reports it: cot-analyzer renders a staleness banner rather than an error, which
is correct behaviour and also means nobody finds out from the dashboard.

**A stale panel looks exactly like a fresh one.** This is why the chain runs daily even though
the data is weekly. The panel is anchored on the report date and a re-run between releases is
idempotent, so a daily run costs nothing, while a weekly run that fails leaves the previous
week's panel up for seven days.

## Why this box at all

The panel needs `unadj` **and** `propadj` prices, and `propadj` is derived on read from
`unadj` + `backadj`, so both stored tiers are a precondition. Norgate is the only vendor
supplying all of them and it is Windows-only, by mechanism rather than by licence. Full
argument in [`docs/design/amendments-2026-08-04.md`](design/amendments-2026-08-04.md) §D14.

This is not a Python constraint and not an operating-system one: the package runs anywhere the
store is readable, macOS included, on the full price-dependent chain. The reason the publish
happens here is that the dash server's sync **originates** here, and a panel built downstream
of the sync is one the sync never sees. The macOS launchd agent
(`bin/com.mspinola.crowdmon-publish.plist.example`) feeds a local development cot-analyzer and
is not a deploy.
