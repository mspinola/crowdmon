# Design docs

**Living documents.** Amended as measurements land, and the current best statement of how
the system works. That is what separates this directory from its neighbours: a design doc
that says something the data disproved is a bug to fix, while an
[analysis](../analysis/) document that says something later weeks disproved is a correct
record of what was true then. See [../handoffs/README.md](../handoffs/README.md) for the
full four-way split.

New crowdmon design work is authored **here**, under this repo's `docs/`, from the first
keystroke (workspace governance: never drafted in an agent scratchpad).

| Document | Where | What |
|---|---|---|
| [`crowdmon_plain_language_summary.md`](crowdmon_plain_language_summary.md) | **here** | the argument in prose, and the **authoritative appendix** (§A.1-A.11). Every formula in the package is defined here |
| [`crowdmon_futures_cot_module.md`](crowdmon_futures_cot_module.md) | **here** | full system description v0.1, and the §13 build order. The primary spec |
| [`amendments-2026-08-01.md`](amendments-2026-08-01.md) | **here** | A1-A22: what the layer-3 build measured that the two above get wrong. **Closed** |
| [`amendments-2026-08-02.md`](amendments-2026-08-02.md) | **here** | B1-B37: commonality (why §A.6 is vacuous unless the own market is excluded, and why it cannot reach §A.9) through the template follow-ups and §A.2's real worked example. **Closed** |
| [`amendments-2026-08-03.md`](amendments-2026-08-03.md) | **here** | C1-C24: template classification stability (17 of 39 markets survive a half-split, and cocoa flips), the `w_SD` sweep the index-share handoff asks for, and the contract-spec backlog. **Closed** |
| [`amendments-2026-08-04.md`](amendments-2026-08-04.md) | **here** | D1 onward: what single number this package delivers. The raw `T` ranking is largely structural, two candidate replacement indices are degenerate by zero-sum, and `Phi` is neither inert nor monotone in `D`. Then the offside term, the pool-versus-signal defect it shipped with, and D13's composition of the two: the pool check removes half the CLOSE-and-SEVERE cell. Then D14: only the Norgate producer can write a store this package can read, and that is a TIER fact rather than an OS one. **The open file** |
| `crowdmon_step2_normalisation.md` | cotdata | contract master and normalisation: **accepted, and layer 2 shipped** as `futures/notional.py` and `futures/riskunits.py`. **History, not instructions**: it named `backadj` for volatility, corrected on cotdata `main` in `ff2b755`. The trap table in [`../../CLAUDE.md`](../../CLAUDE.md) is authoritative on the three price series |
| `cot_vintage.md` | cotdata | the vintage store this package reads. §9 records two adversarial reviews and one deliberately unmet acceptance criterion |

The first two arrived on 2026-08-01, having been written before this package existed. **The
duplication is resolved and there is no "do not edit both" hazard left.**
`cotdata/docs/design/crowdmon_futures_cot_module.md` is now a 52-line pointer here rather
than a copy, and the plain-language summary never existed in cotdata at all: its history
there is empty. The remaining two are about cotdata's own subsystems and belong where they
are.

The lesson from that episode is kept in [`../../CLAUDE.md`](../../CLAUDE.md) rather than
here, because it is procedural rather than about these files: the copy silently lost 104
lines for a day, and duplicating a living document opens a regression window that closes only
when someone diffs the copies. If a document must appear in two repos, one of them is a
pointer from the first commit.

The filename `crowdmon_futures_cot_module.md` keeps the old package name deliberately. It is
the name merged PRs and `cotdata/docs/design/cot_vintage.md` link to, and it is not wrong on
its own terms: the document describes the futures COT module, which is `crowdmon.futures`.

**The appendix is authoritative and is also executed.**
[`tests/test_appendix.py`](../../tests/test_appendix.py) runs the worked thread through §A.2,
§A.5, §A.7 and §A.9 against the implementation; every figure reproduces. **That thread is now
a real market** (live cattle, report week 2026-07-28) rather than a constructed one, which
buys a second failure mode worth having: the figures can drift because the *store* changed,
not only because the code did, so
[`tests/test_appendix_live.py`](../../tests/test_appendix_live.py) re-derives them from the
real store and fails with an instruction to update the document. The constructed near-maximal
table is retained beside it, labelled, because it sits at 90.5% of a config-set ceiling and is
useful precisely for that. See `amendments-2026-08-02.md` §B37.

The appendix is written in LaTeX, which renders on GitHub and not in every viewer, but the
source is plain text either way, so read the file rather than a rendering when the math
matters.

## Amendments are one file per day

`amendments-2026-08-01.md` is closed at A22. Each new file gets its own date and its own
letter prefix (`B1`, `C1`, ...), so a bare section reference can never be ambiguous about
which file it means. Cross-file references still carry the date: `2026-08-01 §A15`.

The reason is measured rather than theoretical. Sections are numbered by position, several
sessions append in parallel, and none can see another's uncommitted numbering: that produced
three collisions in one afternoon (A8/A9, A13/A14, A19/A20), each caught only after a push
and each needing a renumber that then broke references written before the bump. Dating the
file removes the shared counter entirely, and it is not a new convention: `docs/analysis/` is
already dated and never amended for the same reason.

Numbers already published stay put. They are cited from commit messages and module
docstrings, so a section that has landed never moves again.

### The letter prefix is not enough on its own: cite the PATH and the REPRODUCER

The prefix removes ambiguity about **which file**; it does nothing about **which repo**, and
a session with no context cannot tell "this section does not exist" from "this section exists
somewhere I did not look". Both halves, every time:

```
docs/design/amendments-2026-08-02.md §B34
docs/analysis/reproduce.py::template_direction_agnostic
```

Measured rather than theoretical, like the dating convention above. `§B33-B36` was cited by
two handoffs and read by three sessions, each of which searched `git log` on `main`, found
nothing, and concluded the sections had never been written. They had, on 2026-08-02, on a
branch that was never pushed. The second of those sessions re-derived all four and, having no
definition to work from, guessed `A_agnostic` wrong (`2026-08-03 §C4`, corrected).

[`../../tests/test_references.py`](../../tests/test_references.py) resolves every bare
`§X##` in the repo against the sections defined here and fails on any that does not land, so
the old form breaks loudly instead of quietly. **An unresolvable reference is marked, never
deleted**: it goes in that file's `KNOWN_UNRESOLVED` with a reason and a place to look. It
also checks each letter series for holes, which is the cheapest thing that would have caught
`B32` being followed by nothing while four documents cited `B33`.

Amendments to the cotdata-resident specs are recorded here rather than edited into them,
because that is a shared checkout and an edit from this repo would leave uncommitted changes
on its `main`.

## What is settled, and what is not

**Settled.** This package is the right home for everything from normalisation onward,
because normalisation joins COT to prices and crucible-stack ADR-0007 exists to keep those
domains apart everywhere else. The boundary is enforced in `tests/test_boundaries.py`.

**Measured, and better than the proposal assumed.** All 42 `Role: deploy` markets in the
deployed `params.yaml` join cleanly to contract specs and unadjusted prices; the only two
failures are held-out markets Norgate does not cover. Coverage is not a constraint.

**The trap in layer 2, now coded and guarded.** Each rung takes a different price series and
both refuse the rest:

| rung | needs | what the wrong series does |
|---|---|---|
| `notional` | `unadj` | `backadj` notional is wrong by +294% (gold 2002), +257% (crude 2004), and **exactly 0% today**, growing monotonically backwards |
| `riskunits` | `propadj` | `backadj` percent vol is 201x too high for soybeans, 182x for 10Y notes, and **0.47x for gold**, which never goes negative and passes every implausibility screen |

**An earlier version of this file said volatility wanted `backadj`. That was wrong**, and the
error originated here rather than in the spec: additive back-adjustment preserves absolute
price CHANGES, not percentage returns. Module spec §5.1 had it right all along, "ratio-
adjusted, not difference-adjusted, so returns are correct". See
[amendments-2026-08-01.md](amendments-2026-08-01.md) §A8. Both guards raise rather than warn.

**Not settled.** Roll calendar, first notice date and daily price limits are blocked on
data rather than code: there is no per-expiry price source in the stack and none is being
built. Anything needing a calendar spread is blocked on that, not on this package.
