# Handoff: B-series recovery, reference hygiene, weight sensitivity

**Status:** **COMPLETE**, see §8. §1 closed separately, see §7.
**Date:** 2026-08-03
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-b-series-recovery.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** CIT Supplemental ingestion (cotdata#96, merged); index-share §1 (crowdmon#37, merged); §C1-C4 (crowdmon#39, merged) and their live pins (crowdmon#41, merged)
**Deliverable:** one lineage of the B-series rather than two, a reference convention that fails loudly, and the `w_SD` sensitivity under a settled static-weights decision

> Update `Status:` to `complete (PR #NN)` when executed.

---

## 0. What changed between drafting and filing, and why Tasks 1 and 2 look different

This handoff was drafted with four tasks. Two of them were checked before filing, per the
working agreement, and both premises had moved:

**The stale status marker is already fixed.** The draft's Task 1 said
`docs/handoffs/2026-08-03-index-share.md` on main carries `Status: open... unblocked and
unclaimed` above a section titled `## 5. Outcome, §1 executed`. On `origin/main` that line
now reads `Status: COMPLETE as far as it can go, 2026-08-03`, fixed by the merges of
crowdmon#37 and #39. **crowdmon#38 is CLOSED.** Nothing to do, and the original diagnosis was
right at the time it was written: the guard was inverted for part of 2026-08-03.

**The B-series was found, and the draft's Task 2 is the reason.** It instructed a session to
grep for reproducer function names rather than section IDs, and to search all refs rather than
`git log` on main. Done, and it paid immediately. §B33 through §B37 **exist**. They are not
absent, they were never a foreign convention, and nothing needs re-deriving. What they need is
reconciling, which is Task 2 below and is a different and more delicate job.

So the two tasks that follow are not the two that were drafted. The two that were drafted are
recorded above as closed so that no session re-opens them.

---

## 1. Recover the branch before anything else (data-loss risk, do this first)

**`claude/template-followups-doc-corrections-45de1d`, commit `11b7c81`, is local-only.**

```
git show --stat 11b7c81
git ls-remote --heads origin claude/template-followups-doc-corrections-45de1d   # returns nothing
gh pr list --state all --head claude/template-followups-doc-corrections-45de1d  # returns []
```

Never pushed, no PR, one commit ahead of `origin/main`, **2,070 insertions across 17 files**.
It carries §B33-B37 (484 lines added to `amendments-2026-08-02.md`), a handoff
`docs/handoffs/2026-08-02-template-followups.md`, seven reproducer blocks in
`docs/analysis/reproduce.py`, `src/crowdmon/futures/fragility.py` changes, and four test files
including `tests/test_appendix_live.py` and `tests/test_template_strata.py`.

It exists in exactly one place on one disk. **Push it first**, as its own step, before any
reconciliation work. A `rm -rf` of a stale worktree, or hazard 2 of the editable-install list,
takes all of it with no copy anywhere.

Push the branch as it stands. **Do not rebase, squash or amend it**: its value right now is as
an unaltered record of what the earlier session measured, and Task 2 needs to diff it against
main. Whether it becomes a PR that merges, or a PR that is closed with its findings ported, is
Task 2's outcome and not a decision to take while pushing.

---

## 2. Reconcile §B33-B37 against §C1-C4, which are two lineages of one measurement

`2026-08-03 §C1-C4` (crowdmon#39, on main) is a **re-derivation of work that already existed**,
performed by a session that could not find the original. Both worked the same 21,756 vintage
market-weeks, so they are directly comparable, and where they disagree exactly one of them is
right.

**§C4 is the one that is wrong, and it is wrong in a way that matters.** It records
`A_agnostic` as **undefined**: "the string exists nowhere in the package, and the natural
reading is identically 1.0 on 100.0000% of 21,756 market-weeks". §B34 defines it explicitly:

```
A_directional = Q_sell / Q_buy
A_agnostic    = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)
```

and reports a median of **3.0237** over all 21,756 market-weeks (classic outright 2.4974,
everything else 3.1000), with zero ceiling breaches. That is not degenerate and it is not 1.0.
The definition was one unmerged commit away the whole time.

The mapping, and what each pair needs:

| main (`amendments-2026-08-03.md`) | branch (`amendments-2026-08-02.md`) | disposition |
|---|---|---|
| §C1, classification stability | **§B36** | Agree on the headline. §C1 gets "22 of 39 pooled, 17 in both halves" and so does §B36. §C1 reads cocoa **1.000 then 0.098**, §B36 reads **0.976 then 0.100**, which is the figure the index-share handoff §3 cited verbatim. Resolve the split point and state which is correct |
| §C2, template rate invariant to `w_SD` | §B33, §B35 | §C2's finding (the shape rule reads two nets and their signs, so no weight enters) looks independent and probably survives. §B35 retires the swap-share hypothesis at Spearman **-0.114**. Check for overlap rather than assuming there is none |
| §C4, `A_agnostic` undefined | **§B34** | **§C4 is superseded.** §B34 defines it and measures it |
| §C3, `Q_sell`/`Q_buy` swept | no counterpart | §C3 is genuinely new. It is the sweep §B34 did not run |

**Correct §C4 in place, and say why.** `docs/design/` is living and a design doc the data
disproved is a bug to fix. Amend §C4 to point at §B34 as the definition, keep the record that
it was re-derived blind, and carry the reason: the citation was resolvable only on a ref
nobody checked. Do not delete §C1-C4 wholesale. §C3 has no counterpart and §C2 appears sound,
so a blanket revert would lose real work.

**Also correct the two places that now say the wrong thing about provenance.** Both assert the
figures were run but never recorded:

- `docs/design/amendments-2026-08-03.md` header: "Whoever wrote the handoff ran this
  measurement and did not record it ... an accurate one with no home."
- `docs/handoffs/2026-08-03-index-share.md` §6: "So whoever wrote this handoff ran the
  measurement and did not record it, which is a better failure than a fabricated citation and
  still cost a session to rediscover."

It **was** recorded, in §B36, on an unpushed branch. The failure was not a missing record, it
was a record that no reachable search would find. §6 is a handoff outcome section, so append
the correction rather than editing that body; the amendments header is `design/` and gets
fixed in place.

`docs/analysis/2026-08-03-index-share.md` states §B33-B36 "do not exist". It is `analysis/`,
**point-in-time and never amended**. Leave it. It is a correct record of what a session could
see on 2026-08-03. The correction belongs in `design/`.

---

## 3. Structural fix: reference results by path, not by bare section ID

`§B33` names neither a repo nor a file. That is what made it unresolvable, and Task 2 is the
proof: the sections were one `git show` away, and three sessions in a row concluded they were
missing because nothing in the citation said where to look.

**The convention going forward is path plus reproducer:**

```
docs/design/amendments-2026-08-02.md §B34
docs/analysis/reproduce.py::template_direction_agnostic
```

Both are checkable by a session with no context, and both fail loudly.

- Add this to `CLAUDE.md` beside the existing working agreement, and to
  `docs/design/README.md` beside the letter-prefix convention it already states.
- **Sweep the bare references.** There are **104 `§B##` occurrences across 19 files** in
  `crowdmon` (`grep -rno "§B[0-9]\+" docs/ *.md`), plus `cotdata`. Most resolve fine to
  `amendments-2026-08-0{1,2}.md`; the sweep is about making that explicit, not about
  rewriting prose.
- **Mark unresolvable references, never delete them.** A reference that cannot be located is
  a visible gap and a finding. Deleting it makes the gap invisible, which is how this one
  survived three sessions.
- Cross-file references already carry the date (`2026-08-02 §B31`). Keep that and add the
  file path; the date alone did not stop this.

---

## 4. Weight sensitivity, under a settled static-weights decision

**Design decision, now made: weights stay static.** Record it, do not relitigate it.

The reasoning, so the next session does not reopen it: the measurement showed swap dealers sit
at **0.305** of Managed Money on routine turnover and **0.067** under stress (index-share §5,
`docs/analysis/2026-08-03-index-share.md`). That is incoherence across **regimes**, not across
markets, which is the opposite of the per-market direction the index-share handoff was built
to explore. A regime-switching weight table would need a stress classifier, and its
misclassifications would propagate into every downstream figure, including the composite. The
cost is not worth the coherence.

Instead the composite is reported under multiple weight tables and **the spread is treated as
an uncertainty band rather than as noise**.

Run the sensitivity as the index-share §2 specified (template rate by stratum, `A_agnostic`
median, `Q_sell`/`Q_buy`), with two additions:

- **Add 0.067 as a fourth value**, so the sweep is `w_SD ∈ {0.067, 0.2, 0.4, 0.7}`. It is the
  measured stress-regime figure and therefore the empirically motivated lower bound rather
  than a round number chosen for spacing. The other three are round numbers and should be
  labelled as such.
- **Report the direction of bias, not just the magnitude.** Swap dealers get *stickier* under
  stress, so `w_SD = 0.4` **overstates fragile capital precisely when the composite is
  supposed to be informative**. Quantify how much, and name the markets most affected.
  **Gold should be worse affected than cocoa**, because swap sits on gold's immovable
  physical-hedging side while on cocoa it holds the largest net long. State whether that
  prediction holds; if it does not, that is the finding.

`A_agnostic` is now defined (§B34), so unlike §C4 this sweep has all three figures available.
Expect the template rate to stay flat: §C2 established it cannot respond to `w_SD` at all,
and that insensitivity is a fact about which two series the shape rule reads rather than
evidence that the weight does not matter. Do not repeat §2's proposed inference.

**Record the outcome in the module spec**, `docs/design/crowdmon_futures_cot_module.md`:

- **§6.3 Holder fragility** gets the static-weights decision, the reason, and the
  reported-band convention. §6.3 currently ends "Weights are configured, documented as
  judgement, and subjected to sensitivity analysis rather than presented as estimates", which
  is the right place to land it. Note there that the spec's §6.3 table is the *conceptual*
  one and `src/crowdmon/core/config.py` holds the live values (`swap: 0.4`,
  `managed_money: 1.0`, `producer_merchant: 0.1`).
- **§11 What this system does not measure** gets metals. See below.

**The weight table itself stays unchanged.** This task produces evidence and a recorded
decision about *how weights are treated*, not a new number.

---

## 5. Also record

**Metals are permanently unresolved by this route.** The Supplemental report covers 13
agricultural markets. Gold, silver and copper are outside it and always will be. Gold
motivated half the original swap-dealer question, and it is the case where a swap dealer sits
on the immovable side, so it still needs an argument that is not in this data. Write it into
module spec **§11** as an eighth entry so it is not rediscovered a fourth time.

**PyPI, verify it did not propagate.** `cotdata` on PyPI carries **0.1.0 and 0.3.0**, not
0.1.0 alone. Anything published may have external consumers, so removing a public symbol is a
breaking change rather than a free one. This inverts an older claim that a symbol added since
0.1.0 has no external consumers by construction. Already corrected in
`trading_workspace/CLAUDE.md`; grep the siblings for the stale inference and fix any survivor.

---

## 6. Report back

- Task 1: the branch pushed, and its ref, before anything else touched it
- Task 2: the reconciliation, per row of the table, and specifically what §C4 becomes
- Task 3: the sweep result, **including every reference that could not be resolved**
- Task 4: the sensitivity table across all four `w_SD` values, the bias-direction finding, and
  whether gold is worse affected than cocoa
- Anything contradicting this handoff, corrected in place

**Do not start the contract master (module spec §13 step 2).** The scoping decision, whether
to narrow it to template-consistent markets or to markets where Managed Money is large, is
still open and is a design question rather than a measurement.

**Do not render a verdict on the composite using any of this.** The sweep describes how a
configured number moves an output. It is not evidence that the output is right.

---

## 7. Outcome, §1 executed 2026-08-03, before the session started

Appended per the append-never-edit rule; §0-§6 above are preserved as issued.

The branch is pushed, unaltered:

```
11b7c81a67a77622f5d044d6328e151eee3833ac  refs/heads/claude/template-followups-doc-corrections-45de1d
```

No rebase, no squash, no amend, and **no PR opened**, because whether it merges or is closed
with its findings ported is §2's outcome rather than a decision to take while pushing. The
work now exists somewhere other than one disk, which was the whole of §1.

**§1 is closed. A session executing this handoff starts at §2.** This section exists so that
the branch is not pushed twice or, worse, "recovered" a second time by someone who reads §1
and does not reach here.

---

## 8. Outcome, §2 through §5 executed 2026-08-03

Appended per the append-never-edit rule; §0-§7 above are preserved as issued. §1 was closed
before this session started and is recorded in §7.

### §2. Reconciled, and the B-series is now on `main` rather than on one branch

**Ported, not merged.** `11b7c81` predates six merges to `main` and is stale on files `main`
has since moved: `flow.py`'s module docstring (cotdata#93 removed the duplicate `decompose`),
`bin/check_skips.py`, `bin/live-tests.sh`, `tests/conftest.py`,
`tests/test_supplemental_live.py` and the whole 08-03 index-share lineage. Merging it would
have reverted all of that, so its own diff was cherry-picked instead: 2,070 insertions across
17 files, three conflicts, all in index tables. **The branch itself is untouched**, per §1.

That decision answers §1's open question. `claude/template-followups-doc-corrections-45de1d`
should be **closed without merging**, its findings having landed here.

Per row of §2's table:

| row | disposition |
|---|---|
| §C1 vs **§B36**, classification stability | **Both correct, split point RESOLVED.** Both split on 2025-10-21; they differ only on which half that week falls in. Cocoa is not template that week, so §B36's inclusive rule reads 41/42 and 4/40 (0.976 / 0.100) and §C1's exclusive rule reads 41/41 and 4/41 (1.000 / 0.098). **§C1's is the better-specified rule** (41/41 rather than 42/40; §B36's median is over market-weeks and so is weighted by how many markets reported each week). **Every other figure is identical under both**, measured: 22 pooled, 18 either-side, 17 same-side, the same 17 codes |
| §C2 vs §B33, §B35 | **No overlap, and the three are complementary.** §C2 is a fact about the code (the shape label reads two other categories' nets), §B35 a fact about the data (swap share does not predict template status, Spearman -0.114), §B33 about a third quantity. Together: the swap book is neither an **input** to the template label nor a **predictor** of it |
| §C4 vs **§B34** | **§C4 SUPERSEDED and corrected in place.** It read "agnostic" as **weight**-agnostic; §B34 defines it as **direction**-agnostic, `max(Q_sell,Q_buy)/min(Q_sell,Q_buy)`, median **3.0237** over the same 21,756 market-weeks. The wrong reading is kept beside the right one and both are pinned |
| §C3 | **Stands, genuinely new.** Extended to four values as §C6 |

**Also corrected, as §2 directed.** `amendments-2026-08-03.md`'s header ("an accurate one
with no home") is fixed in place, `design/` being living. The index-share handoff's §6 ("ran
the measurement and did not record it") gets an appended §7 rather than an edit, `handoffs/`
being append-only. `docs/analysis/2026-08-03-index-share.md` is **deliberately untouched**:
`analysis/` is point-in-time, and it is a correct record of what a session could see.

### §3. Convention changed, and the sweep came back cleaner than expected

`CLAUDE.md` and `docs/design/README.md` now both carry **path plus reproducer**. The sweep
found **368 bare `§X##` references across 42 files**, and rewriting prose is not the fix, so
the bare form was made to **fail loudly** instead: `tests/test_references.py` resolves every
one against the sections `docs/design/amendments-*.md` defines, and also checks each letter
series for holes, which is the cheapest thing that would have caught B32 being followed by
nothing while four documents cited B33.

**Exactly one reference does not resolve**, and it is not a gap in this work: `§C5` belongs
to crowdmon#42, unmerged. It is recorded in `KNOWN_UNRESOLVED` with a reason and a place to
look, never deleted, and a fourth test fails once it becomes resolvable so the allowlist
cannot rot.

### §4. The band, and the prediction holds

Filed as `2026-08-03 §C6-C8`. Reproducer
`docs/analysis/reproduce_template_stability.py::c6_the_reported_band` onward; pinned by four
new live assertions. **The static-weights decision is recorded, not relitigated**, in module
spec §6.3, along with the reported-band convention and a note that §6.3's table is conceptual
while `core/config.py` holds the live values. **No weight value changed.**

`w_SD ∈ {0.067, 0.2, 0.4, 0.7}`, three round and one measured, pooled over 21,756
market-weeks:

| `w_SD` | median `Q_sell` | median `Q_buy` | median `A_dir` | median `A_agn` | ceiling | `A_agn` as % of ceiling |
|---|---|---|---|---|---|---|
| 0.067 (measured) | 2,651.1 | 2,558.7 | 1.0904 | 3.6316 | **14.925** | 24.3% |
| 0.2 | 3,120.6 | 3,084.8 | 1.0213 | 2.9211 | 10.000 | 29.2% |
| 0.4 (shipped) | 3,734.2 | 3,811.4 | 0.9933 | 3.0237 | 10.000 | 30.2% |
| 0.7 | 4,340.6 | 4,670.3 | 1.0153 | 3.3642 | 10.000 | 33.6% |

Template rate is 0.447106 at every value, as §C2 says it must be. Three findings the original
three-value sweep could not produce:

- **The fourth value is not on the same scale.** At 0.067 swap drops below
  `producer_merchant` at 0.1 and becomes the table's minimum, so the ceiling rises 10.0 to
  14.925 and every raw ratio gains 49% of headroom. Scale by the ceiling before comparing
  across the band.
- **`A_agnostic` is U-shaped with its minimum inside the band**, so the endpoints do not
  bracket the answer. On the classic outrights it is monotonically decreasing instead, which
  makes even the shape of the response a population fact.
- **Direction of bias: `w_SD = 0.4` overstates fragile capital**, on 99.31% of market-weeks
  and never the other way, median **+19.60%**, per market from **+0.9%** (rough rice) to
  **+50.8%** (Henry Hub). **Gold at +27.8% is 2.30x cocoa at +12.1%, so §4's prediction
  holds**, and the mechanism is the one it named: on gold the swap dealer is the immovable
  physical-hedging side, on cocoa it holds the largest net long. The overstatement is worst
  exactly where it is least deserved, and it bites during the weeks the monitor exists for.

**And the qualification, which §4 did not ask for and which matters most.** The composite
consumes `pct(Phi)`, not `Phi`, so a level shift mostly vanishes: median percentile shift
**0.0588**. But 9.79% of market-weeks shift more than 0.25, and on **98 of 264 markets** the
two weight tables **order that market's own weeks differently** (per-market Spearman median
0.9316, minimum -0.4160). Cross-market the ranking survives on the outrights (0.9540, 18 of
the top 20) and degrades over the full universe (0.8521). **The band is narrow where the
package is usually read and wide where it is not.**

**Relationship to `2026-08-03-swap-dealer-weight-decision.md`, which was filed in parallel
and is still open.** These are two different questions and neither supersedes the other. That
handoff asks **what number `swap` should take** and is explicitly the human's. §4 above is
about **how weights are treated**, and that decision was already made. Static weights closes
its option (c), regime-conditional weighting, and leaves (a), (b) and (d) open. §C6-C8 are
evidence for its §2, not a substitute for it, and its §1 is cited rather than re-measured.

### §5. Metals recorded, PyPI checked

Module spec **§11 gains an eighth entry**: the Supplemental covers 13 agricultural markets
and no metals, so gold, silver and copper are permanently outside this route. It names gold
as the case that motivated half the original question and carries the two cross-report
constraints (Index Traders does not nest inside Swap Dealer; combined against futures-only).

**The stale PyPI inference did not propagate to `crowdmon`.** Filed as `2026-08-03 §C9`. Two
stale **facts** survive in siblings (`cotdata/CHANGELOG.md`'s 0.3.0 entry and
`npf/tests/test_sibling_floors.py`'s docstring), both recorded there rather than edited, per
the working agreement on docs in another checkout. Neither carries the "removing it is cheap"
conclusion, which is what §5 asked about.

### Not done, deliberately

The contract master (module spec §13 step 2) is **not started**. No verdict is rendered on the
composite: §C6-C8 describe how a configured number moves an output, which is a statement about
the code, not evidence that the output is right.

**Status: COMPLETE.**
