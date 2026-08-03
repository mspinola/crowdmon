# Handoff: B-series recovery, reference hygiene, weight sensitivity

**Status:** open
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
