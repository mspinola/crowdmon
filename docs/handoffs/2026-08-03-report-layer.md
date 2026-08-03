# Handoff: step 7's report layer, and whether a `D` can carry its own caveats

**Status:** open
**Date:** 2026-08-03
**Drafted against:** `075ad26916dcef41c5e0efcd7cf75671c395048a` (`main`, merge of PR #46)
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-report-layer.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** PR #46 merged; local checkout pulled current; the real store for anything live
**Deliverable:** §2 always. §3 and §4 only if §2's gate passes
**Not this handoff:** the contract-spec backlog. See §1.2

> Announced before the first line of code, per this directory's convention. If you were about
> to start it, say so and I will drop it.

---

## 0. Why this and not something else

§13's build order has one step left that is not blocked on data. Steps 1 through 6 have
shipped or are recorded blocked (limit moves and §379's roll congestion, both on data,
`2026-08-02 §B19`), step 7's validation ran and closed `uninformative`
([2026-08-02-validation-prereg.md](2026-08-02-validation-prereg.md)), and its seasonal
adjustment shipped with the adjustment defaulting off. What remains of step 7 is the report
layer, and the spec puts it last on purpose: a report is the only artifact a reader receives
without also receiving the code.

That is the actual subject here. Not rendering, which exists. The question is whether the
things a reader must know before reading a `D` can travel with the number, or whether they
can only ever live in prose that goes stale.

Right now they live in prose that goes stale. `README.md` gathers four reading instructions
for `D` plus a qualifier (`2026-08-01 §A17`, `§A21`, `§A22`, `2026-08-03 §C3`,
`2026-08-02 §B2`), and nothing the package emits carries any of them. A frame handed to
someone else arrives bare.

## 1. What already exists, and must not be built again

**Read this section before writing anything.** The last handoff
([2026-08-03-step2-contract-master.md](2026-08-03-step2-contract-master.md)) asked in writing
for four modules that already existed, and it was the third instance of the duplicate-build
failure this directory exists to prevent. A report-layer handoff is unusually exposed to it,
because "the report layer" sounds like a greenfield and is not.

### 1.1 Shipped, on `main` at the sha above

| Already there | Where |
|---|---|
| markdown table rendering, per-column formats, identifier and boolean protection | `core/report.py`: `to_markdown`, `as_numeric`, `formatter`, `NO_SEPARATOR`, `NEVER_NUMERIC` |
| the category table, the `Q`/`Phi` arithmetic with every term spelled out, the flow sequence, the audited ranking table | `futures/report.py`: `category_table`, `q_arithmetic`, `format_q_block`, `flow_sequence`, `ranking_table` |
| the composite tables | `futures/composite.py`: `damage_report`, `top_damage` |
| the coverage ladder and its rendering | `futures/coverage.py`: `coverage_ladder`, `unscoreable`, `coverage_summary`, `format_coverage` |
| the alignment block and its attainable ceiling | `futures/alignment.py`: `format_alignment_block`, `max_attainable` |
| the weight band, including the single-weight form | `futures/weight_sensitivity.py`: `sweep`, `single_weight_sweep`, `summarise` |
| a market code is not an instrument | `futures/continuity.py` |

If a task below reads as asking for one of these, the task is wrong and the finding is worth
more than the code. Say so and stop, exactly as PR #46 did.

### 1.2 Claimed elsewhere, right now

A worktree is live on branch `claude/spec-backlog-producer`, at this same sha with
`docs/analysis/reproduce.py` modified. Treat the 34-code spec backlog from `2026-08-03 §C14`
as taken. Confirm before touching `contract_master.py`, the covered-set inventory, or
`docs/analysis/2026-07-28-contract-spec-inventory.md`.

### 1.3 The one obligation nobody owns

`2026-08-03 §C8` ends with an operating rule:

> Anyone publishing a `D` percentile on a power or gas basis market should publish the band
> beside it; on a classic outright the band is a footnote.

Nothing in `src/` can apply that rule. Grep for `stratum`, `outright`, `basis` under
`src/crowdmon/` and the only hits are unrelated prose in three docstrings. The
classic-outright classification exists in
`docs/analysis/reproduce_template_stability.py::c8_does_the_composite_care` and nowhere a
consumer can reach. So the rule is written down, measured, and structurally unenforceable.

Reproducer: `docs/analysis/reproduce_template_stability.py::c8_does_the_composite_care`,
figures in `docs/design/amendments-2026-08-03.md §C8`.

---

## 2. Task 1, the gate: can a caveat attach to a row at all?

**Do not write a report before this is answered and reported.** The instinct is to build the
brief and discover afterwards which warnings it can honestly carry. Reversed: establish which
of the known caveats are properties of a *row*, which are properties of a *panel*, and which
are properties of the *package* and can never be a column, and report that split before
building anything on top of it.

The question, stated so it can come back either way: **for each caveat this package has
measured, is there a value already computable per market-week that tells a reader the caveat
applies here?**

Work through at least these, because they differ in kind and the differences are the finding:

- the warm-up floors, `2010-05-25` for `damage_sell` and `2012-05-15` for `damage_sell_pct`
  (`README.md`, found by the §10 evaluator, `2026-08-02 §B17`)
- unscoreability and the rung a market dies at (`futures/coverage.py`,
  `2026-08-02 §B30`: 2 of 27 is really 1 of 26 and lumber is genuinely unscoreable)
- `Phi`'s reachable ceiling, which is below 1 wherever there is spreading and is already
  returned by `q_arithmetic`
- the `w_SD` band, per §1.3, which needs a stratum the package does not have
- commonality, which `2026-08-02 §B2` says to read beside `D` and never inside it, and which
  spans milk and hogs near 0.07 against the wheats above 1.0
- `2026-08-01 §A17`, that a falling `D` may be a market mid-exit rather than a market getting
  safer, which is a statement about a *direction of change* and may have no per-row form at all
- `2026-08-01 §A21`, that `Phi` reduces exactly to `1 - spreading/OI` under flat weights, which
  is a statement about the whole construction and is certainly not a column

**The failure mode this gate exists to catch.** A brief that renders every caveat as fixed
prose at the top of the page is a README with extra steps, and it goes stale by exactly the
mechanism that has already bitten this repo four times: the README named three shipped modules
as unbuilt, then named A.7 as unbuilt after A.7 shipped and got the trigger module built twice
in one afternoon, then `docs/handoffs/README.md` carried an open marker over finished analysis
on 2026-08-03, then the step-2 handoff requested four existing modules. Hand-kept prose beside
computed numbers is the common cause. If most caveats turn out to be panel-level or
package-level, a per-row brief is the wrong artifact and this handoff should say so rather than
ship one.

**Degenerate inputs specific to the gate.** Answer each explicitly rather than discovering it
in §3:

- a market inside its warm-up window, where `damage_sell_pct` is null. "Not yet scoreable" and
  "scored, and low" must not render identically. A blank cell says the second
- a market that is unscoreable at some rung, where the null arrives from a different cause than
  the warm-up and means something different
- a migrated market code, per `futures/continuity.py` and `2026-08-02 §B30`, which keyed on the
  code alone reads as two markets each dead halfway
- suppressed trader counts, 44% of Managed Money long counts in the latest week and 100% of
  non-reportables by definition. Null is a real state. **Never impute one**
- a market-week with a single populated category, or with spreading equal to open interest,
  where `Phi`'s ceiling collapses toward zero and a value read against 1.0 is meaningless
- a panel holding one report week, where every trailing percentile is undefined by
  construction rather than by data quality
- a panel mixing report types. `2026-08-02 §B21` shows PC1 is a different subject on
  Disaggregated and TFF, and the Supplemental is futures-and-options combined where the other
  three are futures-only, so an open-interest column pooled across reports is two quantities
  under one heading

---

## 3. Task 2, conditional on the gate: the brief

Only if §2 finds that a useful number of caveats are row-computable.

The intent is one artifact per market-week that a reader can act on without also holding the
README, and which cannot silently drift from what the package measures. Not a new number. The
brief's job is assembly and refusal, and every figure in it comes from a module that already
computes it.

The questions worth answering in the doing:

- Does a reader who receives only the brief reach the same conclusions as a reader who has read
  `README.md`'s four reading instructions? That is checkable: pick readings the caveats are
  supposed to prevent, and see whether the brief prevents them
- Which caveats must be **loud**, in the sense that the brief refuses to print a bare number
  without them, and which are genuinely a footnote? `2026-08-03 §C8` already answers this for
  one of them in one direction, and the answer is population-dependent
- Does the assembly surface anything about the composite that the per-engine outputs did not?
  It may not. §5 is about that

**The failure mode this task guards against.** A number published without its caveats gets
traded. §A.10 states that `D` estimates the shape of a conditional loss distribution and not
its location, spec §9.4 carries the standing caution that the replication model must not become
a signal by drift, and `tests/test_boundaries.py` is what stops that eroding by drift rather
than by decision. A brief is the first artifact in this package designed to leave the package,
which makes it the first place that erosion is cheap.

**Degenerate inputs specific to the brief**, beyond §2's list:

- a market where `Q_sell` and `Q_buy` are both large. They must not be summed, in a total row,
  in a chart, or in prose. Their sum describes an event that cannot occur
- a market whose cascade has `g_up` and `g_down` pointing opposite ways, which is 23 of 33.
  Merging them reports a market with two live cascades as quieter than one with none
- an alignment score, which `2026-08-02 §B20` shows cannot reach 1 and whose ceiling averages
  0.931 and moves. The raw figure is not comparable across weeks and a brief that tabulates it
  across weeks says otherwise
- a market on the power, gas basis or carbon book, where §C8 measured Spearman as low as
  −0.4160 (Transco Zone 6) between the two weight tables over that market's own history. This
  is where §1.3's rule binds
- a zero or missing open interest, which divides every ratio in the system
- open interest summed across category rows, which multiplies it by five, since
  `open_interest` is the market total repeated on every row

---

## 4. Task 3, conditional on §3: make §C8's rule enforceable

Only if §3 ships and §2 found the stratum to be row-computable.

The intent is that the operating rule in §1.3 stops depending on a reader remembering it. That
means the classic-outright versus power-gas-carbon distinction has to be reachable from the
package rather than from an analysis script, and the brief has to consult it rather than
document it.

**The failure mode.** `2026-08-03 §C11` is the precedent: `rank_markets` documented an
alignment requirement instead of checking it, and the requirement was found unmet. A rule that
lives in prose beside code that could check it is a rule that will be violated by someone who
never read the prose.

**The degenerate input specific to this one**, and it is the reason this task is third rather
than first: the covered universe is **45 markets across two report types**, not 25
(`2026-08-03 §C12`), the count is report-week dependent, and the 254 uncovered codes are three
populations rather than two (`§C13`, `§C14`: 213 certificates, 7 differentials, 34 real
outright backlog). Any stratum classifier that hardcodes a count, or that assumes one report
type, is wrong on arrival. It must derive the split from the data and print what it derived,
the way `cotdata-vintage coverage` does for Supplemental coverage.

---

## 5. What a negative result looks like, and it is an acceptable outcome

Three distinct negatives are live here, and any of them closes this handoff honestly.

1. **Most caveats are not row-computable.** §2 finds that `§A17`, `§A21` and `§A22` are
   statements about the construction rather than about a market-week, and that what remains is
   two or three nulls that the existing per-engine outputs already expose. Then the right
   artifact is not a brief, and §3 does not run. Report the split and stop.
2. **The brief adds nothing a reader would not get from the modules.** §3 builds it, the
   readings-it-should-prevent check comes back showing the per-engine outputs already prevent
   them, and the brief is decoration. Report that and either drop it or ship it labelled as
   convenience rather than as safety.
3. **The caveats cannot be carried without going stale anyway.** Every candidate mechanism
   turns out to require a hand-maintained string somewhere. That is a real finding about this
   class of artifact and is worth more than a brief nobody trusts.

None of these is a failure of the task. The handoff exists to find out which of the four
outcomes is true, and three of them are negative. Precedent, and it is why this section is
here rather than implied: the §10 pre-registration named `uninformative` in advance as the most
likely verdict and it was, and `2026-08-03-index-share.md` §4 named its own premise's retirement
in advance and the premise was retired. Both are recorded as findings, not as failures. A
handoff that only anticipates success is a handoff that will report success.

---

## 6. What this must NOT do

- **Must not compute a new statistic.** Every figure comes from a module that already produces
  it. If the brief wants a number nothing computes, that is a finding to report, not a function
  to add in `report.py`. A report layer that computes is a sixth engine wearing a report's name
- **Must not be wired into `D`.** §A.9 has no term for a report, as it has none for §A.6, §A.8,
  §368 or §369
- **Must not change `current/` output.** Additive only, per the working agreement
- **Must not sum `Q_sell` and `Q_buy`**, anywhere, including in a total row a table library
  would add for free
- **Must not merge `g_up` and `g_down`**, and must not present a single cascade number
- **Must not impute a suppressed trader count**, or a missing volume, or a missing spec. Null
  is a real state and it feeds straight into the average position per trader
- **Must not add a dependency.** `tests/test_boundaries.py` allowlists `pandas`, `numpy`,
  `pyarrow`, `cotdata` and `marketdata`. No `tabulate`, no `jinja2`, no `matplotlib`, no
  templating engine. `core.report.to_markdown` is hand-rolled for exactly this reason
- **Must not present any ranking as a trade list.** No forward returns, no next-week language,
  no direction. §11 item 7 and §A.10 both say this package has no first-moment content, and
  spec §9.4 is the standing caution
- **Must not restate a measured figure as a literal in a report string.** Cite by path plus
  reproducer, or derive it. A hardcoded `0.931` in a rendering is `README.md`'s failure mode
  moved into `src/`
- **Must not slice a named historical window**, and in particular must not look at 2008. Three
  engines can already reach it and the episode is spent the first time any of them is sliced
- **Must not amend anything under `docs/analysis/`.** Point-in-time, never amended. A later
  week gets a new file
- **Must not edit a sibling working tree.** If something in `../cotdata` or `../marketdata` is
  wrong, record it in `docs/design/amendments-2026-08-03.md` and say so
- **Must not touch the spec backlog** claimed per §1.2 without checking with that session first

---

## 7. Closing this out

Append an outcome section to this file. Do not edit the body: it is the record of what was
asked, which is the only thing that makes "the gate came back negative" a checkable claim.

Update the row in [README.md](README.md) with the status and the PR number in the same PR that
lands the work, not afterwards. `2026-08-03-index-share.md` sat marked open on top of finished
analysis for part of a day and invited a second execution whose numbers would not have matched
the first.

Findings go in `docs/design/amendments-2026-08-03.md` if it is still the open file on the day,
otherwise a new dated file. Cite by path plus reproducer;
[`tests/test_references.py`](../../tests/test_references.py) will fail on an ID it cannot
resolve, which is the point.

If §2's gate fails, that is the deliverable. Write it up, close the handoff, and do not build
§3 anyway.
