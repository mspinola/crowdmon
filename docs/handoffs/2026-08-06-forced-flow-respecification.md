# Specification correction: the forced-flow mechanism test measured the wrong variable

**Status:** **SPECIFICATION CORRECTION. NOT A WORK ORDER, and nothing here is to be executed
as it stands.** §7 lists what must be settled before any of it could be, and §8 states the
count that executing it would carry. A session that runs this as written is running an
un-pre-registered test on data that has already produced one verdict.

Written 2026-08-06, after
[`2026-08-05-forced-flow-mechanism-test.md`](2026-08-05-forced-flow-mechanism-test.md) was
executed and closed. It amends nothing in that file: that body is the record of what was
actually asked, and its §8 is the record of what came back.

---

## 1. What this is, and what it is not

The mechanism test returned `supported` on §5.6's criteria and a **marginal lean** once its
own placebo was accounted for. Its §8 records four places the specification was wrong or
unexecutable. **This file is about a fifth, which is larger than the other four together and
was not visible until the flow composition was looked at.**

It is a corrected design, filed so that the register carries the correction beside the result
rather than in a session's memory. It is **not** a request to re-run. §7 is explicit about why
not yet.

**Nothing here changes any published number, any weight, any threshold in `src/`, or the
verdict in `npf/docs/crowdmon/2026-08-06-forced-flow-mechanism-verdict.md`.**

---

## 2. The defect, in one paragraph

The test's outcome variable is `u = Δ pool_net / open_interest`
([`2026-08-05-forced-flow-mechanism-test.md`](2026-08-05-forced-flow-mechanism-test.md) §5.3).
On the sell side, a pool that **agrees** is long and sells when price falls to `F*`; a pool
that is **contradicted** is short and *adds shorts* when price falls to the same level. Both
are sell flow, both give `Δnet < 0`, and only the first is forced. The variable cannot
separate a forced exit from a fresh entry in the same direction, so a differential built on it
is comparing two different mechanisms that share a sign.

This is not a new insight about futures. It is the first paragraph of
[`../../src/crowdmon/futures/flow.py`](../../src/crowdmon/futures/flow.py):

> Net position change cannot tell them apart, because `Δnet = ΔLong − ΔShort` is the same
> either way, and that is the whole reason this module exists.

**The pre-registration chose an outcome variable that this package already documents as
unable to answer the question it was asked.** `flow.decompose` exists for exactly this
distinction, `flow_state` is a published column, and neither is referenced anywhere in the
frozen §5.

---

## 3. The evidence, and its status

**Advisory and descriptive. Not a result, not tested, and not to be cited as one.** Produced
2026-08-06 from the artifact the verdict already commits
(`npf/docs/crowdmon/reproduce_forced_flow_mechanism.py`, its `crossings.parquet`) joined to
the published `flow_state` of the week following each crossing. If any of it is to become
evidence it needs its own pre-registration and its own variant count.

Share of the week after a crossing carrying each `flow_state`, by group:

| report / side | group | `long_liquidation` | `new_shorts` | `short_covering` | `new_longs` |
|---|---|---|---|---|---|
| disaggregated / sell | agrees | **20.1%** | 9.4% | 2.6% | 5.6% |
| disaggregated / sell | contradicted | 3.9% | **25.8%** | 11.6% | 2.8% |
| disaggregated / buy | agrees | 2.4% | 6.7% | **31.0%** | 4.3% |
| disaggregated / buy | contradicted | 7.3% | 3.4% | 8.0% | **18.1%** |
| tff / sell | agrees | **15.7%** | 4.3% | 6.6% | 8.9% |
| tff / sell | contradicted | 4.8% | 9.0% | 12.6% | 6.3% |
| tff / buy | agrees | 5.4% | 10.5% | **11.2%** | 5.5% |
| tff / buy | contradicted | 12.6% | 6.8% | 4.7% | **11.9%** |

In all four cells the named pool does what the trigger says it does and the contradicted pool
does the opposite thing, a 3x to 5x separation, while the net change the test measured is the
same sign for both.

### The caveat that stops this being the fix as it stands

**The flow labels are themselves partly mechanical, and the same confound reappears one level
down.** A net-long book has a larger gross long leg, so its weekly moves are more likely to
dominate the classification and be labelled `long_liquidation`. Classifying by which leg
dominated therefore inherits a version of the defect §8 already found in the sign of
`pool_net`. A design that swapped `Δnet` for `flow_state` and changed nothing else would be a
better test with the same structural flaw.

---

## 4. The amended §5

Four changes. The first is the one that matters; the rest close the routes by which the
original could return a positive without a mechanism.

### 4.1 Outcome variable: the exposed leg, fractionally

Replace `u = Δ pool_net / open_interest` with the fractional change in the leg the trigger
claims is forced:

```
sell side:   u = Δ long_pool  / long_pool     (the long book the flip forces out)
buy  side:   u = Δ short_pool / short_pool    (the short book the flip forces to cover)
```

Scale-free, bounded below by -1, and directly the quantity the claim is about. It is a
**level ratio, not a category**, so it does not inherit §3's classification confound, and it
is far less exposed to net mean reversion than `Δnet` because it never mixes the two legs.

No sign flip is needed: on both sides more negative already means more of the exposed book
leaving, so §5.3's `-1` on the buy side goes away and with it one place a convention error
could hide.

**Data note.** The gross legs per category are **not** in the published damage panel; they
are in the canonical long panel that `futures/cot_adapter.py` loads. So this outcome variable
cannot be built from `CROWDMON_STORE` alone, which is a real change to §6's "the evaluator
needs no crowdmon computation" and must be stated in any re-specification.

### 4.2 Primary contrast: crossed vs not crossed, within the agreeing group

| | original | amended |
|---|---|---|
| primary | agrees vs contradicted, among crossings | crossed vs not crossed, **within agrees** |
| held fixed | the crossing | the book's side, and now its leg |
| contradicted group | the baseline | a **falsification**, §4.3 |

Both arms of the amended primary hold the same sign of `pool_net`, so the mean-reversion
baseline is identical on both sides of the comparison and cannot generate the result. This is
what §8's fourth bullet was pointing at.

### 4.3 The falsification needs a criterion, which is the whole gap

§5.3 stated the expectation that the non-crossing reading "should be near zero" and §5.6
attached no threshold to it. That is how the criteria came to be satisfied by an effect that
was mostly the group label.

Whatever the amended primary is, the contradicted group's version of the same contrast is a
**pre-registered falsification with a pass condition**, and the condition tests the
*difference between the two contrasts directly*, with its own bootstrap draw. Comparing two
p-values is not a test of their difference, and "significant here, not there" is exactly the
reading that produced the original verdict.

### 4.4 Side consistency, and the level of the position

- **Side consistency, by analogy with §5.6's asset-class condition.** The original's stronger
  surviving residual, TFF at p 0.0099, is a net of a sell side at -0.0072 and a buy side at
  **+0.0037** (verdict §4 and its `ffm-per-side-2026-08-06.csv`). A condition requiring both
  sides to carry the sign would have caught that; §5.6 has none.
- **Control the level of `pool_net`, not only its sign.** Mean reversion scales with position
  size and crossing weeks are not size-neutral, so signed `pool_net / OI` belongs in the
  design as a stratifier or a covariate rather than being collapsed to a sign.

---

## 5. What carries over unchanged

Not everything in §5 was wrong, and a re-specification that rewrites the parts that worked
would cost its own errors:

- **§3.1's vectorisation.** Reproduced exactly at `2.220446049250313e-16` over 96 comparisons.
  Keep it, keep the check, keep it as a gate.
- **§5.1's universe rule** (frozen by rule rather than by hand-picked list), the `{20, 60, 250}`
  lookbacks, and the five-session crossing window.
- **§5.5's block bootstrap** over 13-week calendar blocks taking every market in those weeks,
  and its ban on the IID version. Only the p-value definition needs the correction §8 records.
- **§5.9's store pinning**, in full.
- **§3.2's scope refusal.** Nothing here is real-time actionable, and a re-specification
  inherits that or voids itself.

---

## 6. The presentation consequence, which is separate and actionable now

Not part of any re-run, and filed here only so the pointer exists.

The measured non-specificity has a consequence for what is *rendered*, independent of whether
the mechanism test is ever re-run. `report.format_offside`
([`../../src/crowdmon/futures/report.py`](../../src/crowdmon/futures/report.py)) and
cot-analyzer's damage page both treat `pool_agrees == False` as a **suppression**: the
quadrant label is withheld and replaced with "the pool is on the other side, so this level
would force a book that is not there".

That is half right. The forced book is not there. But price still reaches the level, and flow
of comparable net size still follows; what differs is its composition. Suppressing the row
hides a real event rather than describing it.

The shape of the change, for whoever picks it up: lead with the level and its two existing
docstring caveats (time-series momentum rather than a breakout; a moving reference that closes
distance without the market moving); replace suppression with **re-labelling**, so a
contradicted row reads as "level live, flow expected, arriving as fresh exposure rather than
as an exit"; and demote `pool_agrees` from a gate to a composition flag, stating what it is,
the sign of `pool_net` and nothing more, with no lookback dependence.

---

## 7. Why this is not a work order, and what would have to change

**Do not open this as a task.** Three reasons, in order of weight:

1. **It is a materially different test, so it needs its own pre-registration**, written by
   someone who has not seen §3's table above, and executed by a session that did not write
   it. Filing a corrected design and executing it in the same lineage is the failure the
   generator/evaluator split exists to prevent.
2. **It would be a second look at data that has already produced a verdict.** The honest way
   to run it is as declared re-analysis carrying its own count, not under the original
   pre-registration's protection, and §8 must say so.
3. **Waiting does not fix that, and does not buy much either.** The sample already spans
   2012-05-15 to 2026-07-21, **57 blocks** of 13 weeks. A further year adds about 4, roughly
   7% more data and about 3% tighter standard errors. §1 of the original chose this question
   partly because its evidence regenerates weekly, which is true in the sense that it is never
   *spent* and false in the sense of getting usefully stronger on any horizon worth waiting
   for. Recorded here because the original's reasoning implies otherwise.

What would make it worth opening: a decision that the mapping's strength matters to how the
trigger column is **published**, which is §6 and does not need a re-run, or an independent
reason to revisit the composite. Neither is a strategy question, and neither licenses trading
`D` or the trigger (§5.7, and §A.10).

---

## 8. Count, if it is ever executed

The amended design as sketched is **2 report types x (primary + falsification)**, so **4**,
plus whatever robustness readings its own pre-registration declares. §3's table above is
advisory and carries no count because it is not evidence; it becomes countable the moment
anything is claimed from it.

`run_gauntlet` is not the instrument, unchanged from §5.8: this produces no trades and no
`TradeLog`.
