# Handoffs

Dated work orders, one file per session-sized piece of work, named
`YYYY-MM-DD-<slug>.md`. Status-tracked in the file's own front matter.

**A handoff without a completion status will be re-executed by a future session.** That is
the whole point of the convention: a session that finds an `open` handoff should assume the
work is not done. So closing one out is not bookkeeping, it is what stops the same analysis
being run twice with different results.

```
**Status:** open
**Status:** complete (PR #NN)
```

## Two rules that keep these useful

**The work order is preserved verbatim, including anything the prose rules would forbid.**
Amending a handoff after execution destroys the record of what was actually asked, which is
the only thing that makes "the data contradicted the brief" a checkable claim rather than an
assertion. Append an outcome section; do not edit the body.

**Where a handoff was wrong, the outcome says so and points at the measurement.** The
amendments under [`../design/`](../design/) carry the detail; the handoff carries the
pointer, so a reader who starts from the work order is not left with the premises it opened
with.

| Handoff | Status |
|---|---|
| [2026-08-01-flow-decomposition.md](2026-08-01-flow-decomposition.md) | complete — layer 3, flow decomposition and fragility-weighted exit size |
| [2026-08-02-reflexivity.md](2026-08-02-reflexivity.md) | **COMPLETE.** §A.8 cascade amplification, shipped as `futures/reflexivity.py`. The horizon decision it was blocked on was dissolved rather than answered: `g` is a staircase, so no horizon is picked. Corrections in `2026-08-02 §B13-B15` |
| [2026-08-02-validation-prereg.md](2026-08-02-validation-prereg.md) | **EXECUTED 2026-08-01, verdict `uninformative`.** §10 pre-registration, run in `npf` by a cold session. Outcome appended as §9, crowdmon-facing findings as `2026-08-02 §B17`. §7.8 deferred, re-check 2026-11-01. **The clean episodes are spent** |
| [2026-08-02-coverage-reporting.md](2026-08-02-coverage-reporting.md) | **complete (PR #15), corrected same day (PR #17).** `futures/coverage.py`, keyed on `market_code`. `2026-08-02 §B18` found the ladder skipped the three terms `D` is built from, and that it is not monotonic because `phi` is price-free |

## A handoff can also be a claim

Two modules were built twice in one afternoon because each session started the obvious next
piece without re-checking. Writing the claim here before starting is the fix, and it costs a
few minutes against a duplicated module. A `claimed, not started` handoff says what is being
taken, what it is blocked on, and what decision it needs, so another session can object before
either of us has written anything.

## How this differs from the neighbouring directories

| Directory | Lifecycle |
|---|---|
| `design/` | **living.** Amended as measurements land. The current best statement of how the system works |
| `handoffs/` | **append-only.** A dated work order plus its outcome. Never revised in place |
| `analysis/` | **point-in-time.** Output computed against a named report week, never amended. A later week gets a new file |
| `adr/` | **immutable once accepted.** Superseded by a new ADR rather than edited |

The distinction that matters most is `design` versus `analysis`. A design doc that says
something the data disproved is a bug to fix; an analysis document that says something later
weeks disproved is a correct record of what was true then. Editing the second to match the
present would erase the evidence that anything changed.
