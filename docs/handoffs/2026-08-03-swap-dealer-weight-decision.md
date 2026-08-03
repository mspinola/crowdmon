# Handoff: the Swap Dealer weight decision

**Status:** **complete, 2026-08-03 (PR #44).** Decided by the human as **option (a)**:
`swap: 0.4` stands, examined and deliberately kept. See §7. §6 corrects §1's headline figure
before the decision was taken, and `single_weight_sweep` (the one item §4 released) is built. **§8 records `§C6-C8`, which landed in parallel and did not reverse the decision**: they close option (c) outright, measure the cost of (a), and show most of it never reaches `D`.
**Date:** 2026-08-03
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-swap-dealer-weight-decision.md`
**Target:** the human. A session may prepare the change; it may not choose the number
**Depends on:** [2026-08-03-index-share.md](2026-08-03-index-share.md) (closed),
`2026-08-03 §C1-C5`, `2026-08-01 §A21-A22`
**Deliverable:** a decision on `swap: 0.4`, or a recorded decision to leave it

> Update `Status:` to `complete (PR #NN)` when the decision lands, including if the
> decision is "unchanged". A weight deliberately left alone and a weight nobody got to
> look the same in `config.py` and are not the same thing.

---

## 0. Why this is filed separately

The index-share handoff was told, in its own §2: "**Do not change the weight table in this
session. Produce the evidence; the decision is separate and follows.**" It obeyed that, and
closed. This is the follow-on it named, filed rather than left implicit so that the next
session does not either re-run the evidence or quietly edit the number.

Both failure modes have precedent here. Two modules were built twice in one afternoon
because nobody wrote the claim down first, and the index-share handoff itself was executed
from a stale `open` marker while it was being moved between repos.

---

## 1. What is already known, and must not be re-measured

**The premise this started from is retired.** Index positioning is **not** meaningfully
stickier than swap positioning. Median 12-week autocorrelation is index 0.777 against swap
**0.826**; index leads in only 4 of 13 markets; and in the worst 5% of weeks the swap book
moves **less** than the index book (-0.00167 against -0.00336). The two persistence
statistics disagree on direction, which on its own disqualifies index share as a
discriminator.

**That is a genuine null and the clean evidence is spent.** `2026-08-03-index-share.md` §4
named this outcome in advance as a real one. Do not re-run it expecting a per-market weight
to fall out.

**What replaced it, and nobody was looking for it.** Against Managed Money at 1.0:

| regime | swap sits at | nearest configured weight |
|---|---|---|
| routine turnover | **0.305** | `swap: 0.4` |
| the worst 5% of weeks | **0.067** | `producer_merchant: 0.1` |

One weight cannot be both. **The incoherence in `swap: 0.4` is between REGIMES, not between
markets**, which is the opposite of the per-market direction the work set out to find. It
needs no Supplemental report and would show up in metals or anywhere else.

**And the parameter is load-bearing exactly where it is being asked about.** Sweeping
`w_SD` alone over {0.2, 0.4, 0.7}, median `A = Q_sell/Q_buy` (`2026-08-03 §C3`):

| population | median `A` | swing |
|---|---|---|
| all 21,756 vintage market-weeks | 1.0213 → 1.0153 | **0.6%**, non-monotonic |
| the 13 Supplemental markets | 2.1845 → 3.1028 | **42.0%**, monotonic |

Pooled over a universe that is three-quarters ERCOT and PJM basis, `w_SD` is a rounding
error. On the agricultural outrights it is not. `Q_sell` doubles while median `Q_buy` is
unchanged from 0.4 to 0.7, which locates the mechanism: on the median Supplemental market
the swap book sits on the **sell** side, so raising its weight lifts the numerator alone.

---

## 2. The decision, stated as options

None of these is recommended here. That is the point of the file.

**(a) Leave `swap: 0.4` and record why.** Defensible: it is close to the routine-turnover
figure of 0.305, and routine weeks are most weeks. Cost: every `Q_sell` published during
the weeks the monitor exists to warn about is computed with a weight measured to be roughly
6x too high for those weeks.

**(b) Cut it toward 0.1.** Defensible: `crowdmon` is a stress monitor, so the stress-regime
number is the relevant one and 0.067 is nearer `producer_merchant` than `swap`. Cost: it
collapses a category distinction on the ~95% of weeks that are not stressed, and it moves a
weight to fit a measurement, which `core/config.py`'s own header forbids in the strongest
terms ("configured, not fitted ... must never be tuned until an output looks better").

**(c) Make the weight regime-conditional.** This is what the evidence actually points at
and it is the largest change: `weights_for(report_type)` becomes
`weights_for(report_type, regime)`, and something has to decide the regime, point-in-time,
without lookahead. That is a new design decision, not a number.

**(d) Publish the sensitivity beside the output instead of choosing.** `Q_sell` ships with
its `w_SD ∈ {0.2, 0.4, 0.7}` band on Supplemental markets, and the reader sees the 42%.
Cheapest, and consistent with §6.3's "subjected to sensitivity analysis rather than
presented as estimates", but it pushes the judgement onto every reader forever.

**If (b) or (c) is chosen, `TFF_WEIGHTS["dealer"]` is 0.4 for the same reason and by the
same argument.** It has never been exercised (`config.py` says so). Changing swap and
leaving dealer would split a deliberate symmetry by accident.

---

## 3. Constraints on whatever is decided

**Metals are permanently outside the Supplemental report.** Gold, silver and copper are not
covered and never will be by this source. Gold is the case that motivated half the original
question, the market where the swap dealer sits on the **immovable** side with
Producer/Merchant at a tenth of the swap book. Nothing measured here reaches it. Anything
concluded for ag transfers to metals only with an argument that is not in this data.

**Do not tie the decision to template classification.** `2026-08-03 §C1`: 22 of 39 markets
read extreme pooled but only 17 in both halves, and cocoa runs 1.000 then 0.098 inside a
single 82-week window. A classification computed on either half disagrees with the other
about what kind of market five of them are. Prefer statements about position behaviour.

**Swap is not the load-bearing weight in the table; Producer/Merchant is.**
`2026-08-01 §A22`: PM at 0.1 holds **56% of gross open interest**, and raising it to 0.3 is
the only single-weight move that pulls `Phi` correlation below 0.96. A session that
re-opens the weight table should know that the weight nobody argues about decides the most,
and that this handoff is deliberately not about it.

**`Phi` has no signal independent of the weights at all.** `2026-08-01 §A21`: set every
weight to 1.0 and it reduces exactly to `1 - spreading/OI`, to 1.11e-16 on 27,194
market-weeks. So this decision is not calibrating a measurement, it is choosing what the
measurement means. `2026-08-03 §C4` is the sharpest form: with the weights flattened the
asymmetry is identically 1.0 on 100.0000% of market-weeks.

---

## 4. What a session may do without the decision

- Add a single-weight sweep to `futures/weight_sensitivity.py`. It currently jitters **all**
  weights order-preservingly and reports rank stability, so it cannot express "hold the
  table, move one weight over a stated grid, report a level on a named subpopulation", which
  is what §C3 needed and did ad-hoc in
  [`../analysis/reproduce_template_stability.py`](../analysis/reproduce_template_stability.py).
  A22 did the same thing ad-hoc for Producer/Merchant. Twice ad-hoc is a missing function.
- **Not** change any value in `core/config.py`. That is the decision, and it is not a
  session's to make.

---

## 5. Report back

- The option chosen, in the terms of §2, with the reasoning
- Whether `TFF_WEIGHTS["dealer"]` moves with it
- What the change does to the published `Q_sell/OI` and `Q_buy/OI` rankings, measured
- An explicit note that metals remain unresolved, because they do

---

## 6. Amendment, 2026-08-03: the sweep §4 called for was built, and it corrects §1

Appended per the append-never-edit rule; §0-§5 above are preserved as issued.

§4 listed "add a single-weight sweep to `futures/weight_sensitivity.py`" as the one thing a
session could do without the decision. It is built (`single_weight_sweep`), and running it
over the wider band **corrects a figure in §1 of this handoff.**

**§1 quotes 42.0% on the Supplemental 13. That band was 0.2 to 0.7, and 0.7 is outside the
plausible class**: it puts a swap dealer above both `nonreportable` (0.6) and
`other_reportable` (0.5). `2026-08-01 §A22` established that §6.3's judgement is an ordering
before it is a set of values, and that reordering it destroys the rankings entirely, so an
order-violating value is a different claim rather than a rival one.

Restricted to values that keep the ordering intact, `w_SD` spans `[0.2, 0.4]` and median
`A = Q_sell/Q_buy` moves:

| population | order-preserving band | full 0.067-0.7 band |
|---|---|---|
| all 346 markets | 0.9869 to 1.0213, **3.5%** | 12.0% |
| the 13 Supplemental markets | 2.1845 to 2.5750, **17.9%** | 54.1% |

**Read §2's options against 17.9% and 3.5%, not 42.0%.** The direction of §1's finding
survives (`w_SD` is load-bearing on the Supplemental markets and a rounding error pooled) and
its force does not. Live 0.4 against the routine-turnover reading 0.305 is 7.1% apart.

**Option (b) needs a boundary correction.** "Cut it toward 0.1" lands on a **tie** with
`producer_merchant`, which collapses the swap-versus-hedger distinction rather than
reweighting it, and any value below 0.1 inverts it. So (b)'s usable range is open at the
bottom: it stops at 0.1 exclusive, and the stress reading of 0.067 is not reachable without
making a claim §6.3 contradicts. That is a constraint on the option, not an argument
against it.

Full detail and the reproducer: `2026-08-03 §C6`.

**Status: still open. The weight table is still unchanged.**

---

## 7. Decision, 2026-08-03: option (a). `swap: 0.4` stands, and the reasoning is on the record

Appended per the append-never-edit rule. **The decision was made by the human**, presented
with §2's four options against §6's corrected figures rather than §1's.

**`swap` stays at 0.4. `TFF_WEIGHTS["dealer"]` stays at 0.4.** No value in `core/config.py`
changed.

### Why (a) rather than the other three

The correction in §6 is what made it defensible. Against §1's 42.0% the weight looked like a
number the answer depended on; against §6's **17.9% over the order-preserving band, and 3.5%
pooled**, it is a number the answer is mildly sensitive to on 13 markets and nearly indifferent
to everywhere else. 0.4 sits inside the plausible class and 7.1% from the routine-turnover
reading of 0.305, which is where most weeks are.

Each of the others was declined on its own terms, and none is refuted:

- **(b) cut toward 0.1** fits a stress-regime number to the ~95% of weeks that are not
  stressed, and `core/config.py`'s header forbids tuning a configured weight until an output
  looks better. §6 also closed its floor: 0.1 exactly is a tie, not a value.
- **(c) regime-conditional** is what the evidence actually points at and remains the honest
  long answer. It is a design decision rather than a number, needs a point-in-time regime
  classifier with no lookahead, and nothing else in the package is regime-conditional.
- **(d) publish the band** is what §6.3 literally asks for, but at 17.9% the band is now
  small enough to read as noise rather than as a caveat, and it defers the judgement to every
  reader forever.

### What is recorded rather than resolved

**The regime incoherence is real and is now a documented under-weighting, not a fixed one.**
Swap behaves at 0.067 of Managed Money in the worst 5% of weeks and carries 0.4. Every
`Q_sell` published during exactly the weeks this package exists to warn about overstates the
forceability of the swap book. That is the known cost of (a) and it is written into
`core/config.py` beside the value, so the next reader meets it there rather than here.

**Metals are exactly where §3 left them.** The Supplemental report does not cover gold,
silver or copper and never will. The case that motivated half of §0, a swap dealer on the
immovable side, is untouched by any of this.

**(c) is not closed, it is unscheduled.** If a regime classifier arrives for another reason,
this decision should be re-opened rather than treated as settled precedent.

**Status: complete. The weight table is unchanged, deliberately.**

---

## 8. §C6-C8 landed in parallel, and they reached the same place by a different road

Appended after the decision, on merging `origin/main` into PR #44. **The decision in §7 was
taken without this evidence**, because PR #43 (`claude/b-series-reconcile`) was in flight at
the same time and neither branch could see the other. Recorded rather than folded into §7, so
that what was known at the moment of deciding stays legible.

**Nothing here reverses §7.** Two of the three findings support it and the third is its cost,
now measured rather than asserted.

| section | bearing on the decision |
|---|---|
| **§C6** | Settles that **weights stay static** and the composite is reported under several tables with the spread as an uncertainty band. That **independently closes option (c)**, which §7 set aside on judgement, so (c) is now closed by a decision rather than merely unscheduled |
| **§C7** | The cost of (a), quantified: `Phi(0.4) > Phi(0.067)` on **99.31%** of market-weeks, median **+19.6%**, and **worst exactly where it is least deserved**. Gold inflates **+27.8%** against cocoa's +12.1%, **2.30x**, because on gold the swap dealer *is* the immovable hedging side |
| **§C8** | Why that mostly does not arrive. `D` consumes `Phi` as a **percentile**, so a 19.6% level inflation moves the median market-week only **5.9 percentiles**. Cross-market Spearman is **0.954** on classic outrights, 18 of the top 20 in common |

**§C8 supplies the operating rule §7 did not have**, and it is sharper than anything in §2's
option list:

> On classic outrights the `w_SD` choice moves levels and barely moves rankings, so the band
> is a footnote. On the ERCOT and PJM book it can reorder a market's **own** history (Transco
> Zone 6 basis at Spearman **-0.416**), so publish the band beside a `D` percentile there.

That is option (a) **and** a scoped option (d), which is a better answer than either alone and
was not available when §2 was written.

**One thing §7 got right for a reason it did not have.** §7 declined (b) partly because 0.1 is
a tie and 0.067 unreachable (§C10). §C7 now shows 0.067 is also the value that inflates the
**ceiling** to 14.925 (§C6), so the stress reading was doubly unusable as a weight: outside the
ordering *and* off the scale everything else is measured on.

**Status unchanged: complete. `swap: 0.4` and `TFF_WEIGHTS["dealer"]: 0.4` stand.** Option (c)
moves from unscheduled to closed by §C6. The `core/config.py` annotation §7 added should be
read alongside §C7's per-market table, which is the detail it summarises.
