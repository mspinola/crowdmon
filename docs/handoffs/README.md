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
| [2026-08-01-flow-decomposition.md](2026-08-01-flow-decomposition.md) | **complete, closed out 2026-08-02 as §10.** Layer 3, flow decomposition and fragility-weighted exit size. Landed as `0917eb1` with **no PR**, predating the PR workflow. §9's premise 4 is now closed (the appendix surfaced and is executed in `tests/test_appendix.py`); its §6 cocoa answer was sharpened by `2026-08-02 §B28`. Its one open item, the duplicated `decompose`, was **measured and pinned as `2026-08-02 §B29`**: `cotdata`'s is this one at `tolerance=1.0` with gaps off, 100.000000% agreement. **That decision has since been made**: cotdata dropped its copy in cotdata#93, so `cotdata.vintage_flow.decompose` no longer exists and `tests/test_flow_equivalence.py` skips rather than comparing. `zero_sum_check` stays in cotdata, being a claim about its own parse, and `futures/cot_adapter.py` runs it on every load. **Nothing open** |
| [2026-08-02-reflexivity.md](2026-08-02-reflexivity.md) | **COMPLETE.** §A.8 cascade amplification, shipped as `futures/reflexivity.py`. The horizon decision it was blocked on was dissolved rather than answered: `g` is a staircase, so no horizon is picked. Corrections in `2026-08-02 §B13-B15` |
| [2026-08-02-validation-prereg.md](2026-08-02-validation-prereg.md) | **EXECUTED 2026-08-01, verdict `uninformative`.** §10 pre-registration, run in `npf` by a cold session. Outcome appended as §9, crowdmon-facing findings as `2026-08-02 §B17`. §7.8 deferred, re-check 2026-11-01. **The clean episodes are spent** |
| [2026-08-02-macro-book-pca.md](2026-08-02-macro-book-pca.md) | **complete (PR #21).** `futures/macro_pca.py`. PC1 is the grain complex on Disaggregated and the macro book on TFF (`B21`), so the report type is the subject rather than a parameter. Reaches 2008; no episode examined, deliberately |
| [2026-08-02-coverage-reporting.md](2026-08-02-coverage-reporting.md) | **complete (PR #15), corrected twice (PR #17, PR #19), closed out 2026-08-02.** `futures/coverage.py`, keyed on `market_code`. `2026-08-02 §B18` found the ladder skipped the three terms `D` is built from, and that it is not monotonic because `phi` is price-free. Close-out added the missing third correction and `§B30`: the two unscoreable markets are one migrated instrument, and merging them end to end lifts every rung and changes no verdict, so **2 of 27 is really 1 of 26** and lumber is genuinely unscoreable |
| [2026-08-02-roll-congestion.md](2026-08-02-roll-congestion.md) | **COMPLETE.** `futures/roll.py`. All three components of spec §379 are blocked, including OI migration: the price frame's `Open Interest` is whole-market. What shipped is roll-window volume and its effect on `pressure.T`, which is 5.1% and wrong-signed for five of sixteen markets. `2026-08-02 §B19` |
| [2026-08-02-trend-alignment.md](2026-08-02-trend-alignment.md) | **COMPLETE.** Spec §368, shipped as `futures/alignment.py`. The score **cannot reach 1**: the blend is heavily tied, so the ceiling averages 0.931 and runs 0.340 to 0.969, and the raw figure is not comparable across weeks. No warm-up, so it is the earliest-starting engine here. `2026-08-02 §B20`
| [2026-08-02-correlation-clustering.md](2026-08-02-correlation-clustering.md) | **COMPLETE.** Spec §369, shipped as `futures/clustering.py`. Its own JPY-energy example is **not in the data**; the real cluster is `{6J, ZB, ZF, ZN, ZT}`, the yen carry, which the partition finds on its own at k=8. `2026-08-02 §B25` |
| [2026-08-02-template-followups.md](2026-08-02-template-followups.md) | **COMPLETE.** Five measurements and two doc corrections, `2026-08-02 §B33-§B37`. Its §3 hypothesis is **retired**: swap share does not predict template status, at any aggregation. Two of its own premises were corrected in place: the §1 dichotomy is not exhaustive (the fund is half the weeks and **two thirds of the contracts**), and the "median 0.993, no asymmetry" reading it inherited from `§B31` is direction cancelling. §A.2 now works a **real** market, live cattle, pinned by `tests/test_appendix_live.py`. Contract master deliberately **not** started. Executed 2026-08-02 on `claude/template-followups-doc-corrections-45de1d` and **never pushed**, which is what `2026-08-03-b-series-recovery.md` §1 recovered and §2 landed |
| [2026-08-03-index-share.md](2026-08-03-index-share.md) | **COMPLETE as far as it can go, 2026-08-03.** The only handoff here authored in another repo (cotdata#97, moved here as PR #36; a second session filed a duplicate copy before checking the remote, which is what the claim-first convention below exists to stop). §1: **the premise is retired, exactly as §4 anticipated.** Index positioning is not meaningfully stickier than swap. Swap is the MORE persistent at 12 weeks (median 0.826 vs 0.777, index ahead in only 4 of 13), index is 14% steadier week to week, and **under the worst 5% of weeks the swap book moves less than the index book** (-0.00167 vs -0.00336), adding to net long in 3 of 13 where index never does. §2 was recorded as blocked on **§B33-B36**, and re-derived blind as **`2026-08-03 §C1-C4`**. **Both readings are now corrected** (`2026-08-03-b-series-recovery.md` §2, and this file's appended §7): §B33-B37 **existed all along**, on an unpushed branch, so 08-02 closed at **B37** rather than B32 and §2 was in fact executable in full a day before it was called blocked. The cited figures were **not invented**: "22 of 39" and "17 in both halves" reproduce exactly. Of §2's three headline figures one **cannot respond to `w_SD`** (the shape rule reads two nets and their signs), one (`A_agnostic`) is **defined by `§B34` at a median of 3.0237**, not undefined as §C4 first read it, and `Q_sell`/`Q_buy` answers: median `A` swings **42.0% on the 13 Supplemental markets** against 0.6% pooled, so **`w_SD` is load-bearing exactly where the handoff cares**. Unsought finding: swap sits at 0.305 of Managed Money on routine turnover and 0.067 under stress, so `swap: 0.4` is incoherent **between regimes, not between markets**. **Metals are permanently outside coverage, so most of §0 is still open.** Weight table unchanged |
| [2026-08-03-b-series-recovery.md](2026-08-03-b-series-recovery.md) | **COMPLETE, outcome as §7 and §8.** §1 recovered `claude/template-followups-doc-corrections-45de1d` (`11b7c81`), local-only with 2,070 insertions, by pushing it unaltered. §2 landed its content on `main` by **porting rather than merging** (the branch predates six merges and would have reverted `flow.py`, `check_skips.py`, `conftest.py` and the whole 08-03 lineage), so **that branch should be CLOSED unmerged**. `amendments-2026-08-02.md` is now B1-**B37**: it never closed at B32, it closed on a branch nobody could see. **§C4 is superseded**, having read `A_agnostic` as WEIGHT-agnostic where `§B34` defines it as DIRECTION-agnostic at a median of **3.0237**; corrected in place with both readings pinned. The cocoa split point is **resolved**: same date, 2025-10-21, differing only on which half that week falls in, and every other figure identical under both rules. §3 changed the citation convention to **path plus reproducer** and made the bare form fail loudly (`tests/test_references.py` over 368 references in 42 files; exactly one unresolved, `§C5`, owned by #42 and recorded rather than deleted). §4 ran the band `w_SD ∈ {0.067, 0.2, 0.4, 0.7}` under a **settled static-weights decision** and filed `2026-08-03 §C6-C8`: `w_SD = 0.4` overstates fragile capital on 99.31% of market-weeks by a median +19.6%, **gold at +27.8% is 2.30x cocoa at +12.1% so the prediction holds**, and 0.067 moves the ceiling 10.0 to 14.925 so the band is not on one scale. Most of it never reaches the composite, which consumes `pct(Phi)`, except on **98 of 264 markets** where the two tables reorder a market's own weeks. **Weight table unchanged** |

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
