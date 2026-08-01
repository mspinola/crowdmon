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
| [`amendments-2026-08-02.md`](amendments-2026-08-02.md) | **here** | B1-B7: commonality (why §A.6 is vacuous unless the own market is excluded, and why it cannot reach §A.9) and seasonality. **The open file** |
| `crowdmon_step2_normalisation.md` | cotdata | contract master and normalisation: **proposed and measured, not accepted**. Read before starting layer 2 |
| `cot_vintage.md` | cotdata | the vintage store this package reads. §9 records two adversarial reviews and one deliberately unmet acceptance criterion |

The first two arrived on 2026-08-01, having been written before this package existed. **The
`cotdata` copies still exist**, so those two files are now duplicated across repos: the ones
here are canonical, and the cotdata ones should become pointers when something next brings
that repo open. Do not edit both. The remaining two are about cotdata's own subsystems and
belong where they are.

The filename `crowdmon_futures_cot_module.md` keeps the old package name deliberately. It is
the name merged PRs and `cotdata/docs/design/cot_vintage.md` link to, and it is not wrong on
its own terms: the document describes the futures COT module, which is `crowdmon.futures`.

**The appendix is authoritative and is also executed.**
[`tests/test_appendix.py`](../../tests/test_appendix.py) runs §A.2's cocoa example and §A.5's
days-to-liquidate against the implementation; every figure reproduces. It is written in
LaTeX, which renders on GitHub and not in every viewer, but the source is plain text either
way, so read the file rather than a rendering when the math matters.

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
