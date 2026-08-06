# Handoff: pre-registration for the forced-flow mechanism test, to be executed by a cold session

**Status:** complete (executed 2026-08-06 in `npf`, PR #79). Verdict a **marginal lean**, see §8.

Written 2026-08-05, before computing any statistic below.

---

## 1. What this asks, and why it is not §10 again

§10 asked whether `D` is **elevated before** a forced-exit episode, over hand-identified
historical episodes. It was executed 2026-08-01, returned `uninformative`, and
[the clean episodes are spent](2026-08-02-validation-prereg.md). Nothing here reuses them.

This asks a different question, about a different column, with a different unit of
observation:

> When the trigger says a pool is mechanically forced out at price `F*`, and price reaches
> `F*`, **does that pool actually move?**

That is the claim `futures/trigger.py` makes and the only one it makes. It is a claim about a
mechanism, not about a return, and it is testable weekly rather than only at rare episodes, so
the evidence regenerates instead of being consumed.

**Why it is worth running at all.** The trigger distance is currently the least-evidenced
column crowdmon publishes. `2026-08-04 §D9` established that `move_from_spot` is an identity
with the trailing `k`-day return, so the distance carries no price information beyond momentum.
What `trigger.py` claims to add is **the mapping**: which pool, on which side, is forced at that
level. That mapping has never been tested against what the pool subsequently did.

---

## 2. Why neither crowdmon nor the author may execute this

`tests/test_boundaries.py` lists `crucible` in `FORBIDDEN_ROOTS`, with the stated reason that
a monitor able to render a verdict on its own output has stopped being a monitor. So the
verdict is rendered in `npf`, following §10's precedent exactly (§8 below).

**The author's contamination, declared.** The session writing this spent 2026-08-05 in
`crowdmon` and `cot-analyzer` on the damage page's axis, and in doing so looked at:

- the 2026-07-28 published panel, both sides, including which markets carry
  `trigger_*_pool_agrees == False` (13 on the buy side);
- a one-week repricing comparison, 2026-07-28 against 2026-08-04, which found 41% of
  (market, side) pairs cross the 1.5-sigma close line in five sessions and 27 of 70 change
  their nearest lookback.

That second measurement is **the volatility of the predictor**, not of the outcome. No
subsequent pool movement was examined, and no crossing was paired with any position change.
The outcome variable is untouched by this session.

It cannot be undone, so it is handled structurally: **every threshold, window, universe and
statistic below is fixed here and may not move once results are visible.** If a result wants a
different window, it does not get one.

---

## 3. Data availability, measured 2026-08-05

Against `~/code/cotdata_store` and `~/code/crowdmon_store`.

**Nothing needed here is missing.** The published panel already carries full history, which an
earlier reading of this situation got wrong by confusing the number of published snapshots
(one) with the depth of the panel inside it:

| column | non-null rows | distinct weeks |
|---|---|---|
| `phi` | 51,316 | 1,051 |
| `dtl_sell` | 48,848 | 1,051 |
| `illiquidity_sell` | 43,522 | 948 |
| `crowding_long` | 38,415 | 845 |
| `damage_sell_pct` | 33,400 | 742 |
| `trigger_sell_sigma` | **39** | **1** |

Panel range 2006-06-13 to 2026-07-28, 53 market codes, 48 scored, first scored week
**2012-05-15** on both report types (`C = pct(z)` stacks two three-year windows with a third
rolling on top).

`trigger_*` is one week because `add_trigger_distance` is a point-in-time overlay, and its
docstring is explicit that this is **cost rather than correctness**: roughly 95,000
price-store reads for a full history against 90 for one week.

### 3.1 The 95,000 reads are avoidable, measured

`trigger_prices` computes `move_from_spot = flip/spot - 1 = ratio_then/ratio_now - 1`
([trigger.py:152](../../src/crowdmon/futures/trigger.py:152)). The `unadj` spot **cancels**.
The distance is therefore a pure function of the `propadj` series, and the signal is
`sign(ratio_now - ratio_then)`, also pure `propadj`.

So the whole history is vectorisable from **one price read per symbol**, not two reads per
(symbol, week):

```python
r = cotdata.get_prices(sym, adjustment="propadj")["Close"].dropna()
move_k  = r.shift(k) / r - 1.0          # == move_from_spot, exactly
signal_k = np.sign(r - r.shift(k))      # == the signal column
```

**Verified against `trigger_prices` at 4 dates x 3 lookbacks spanning 2015 to 2026: maximum
absolute difference 2.22e-16, all 12 signals matching.** The evaluator must reproduce this
equivalence check before relying on the vectorised form, and must record the max absolute
difference in the outcome.

Note `iloc[-1 - k]` is `k` **bars** back, not `k` calendar days. `shift(k)` matches it.

### 3.2 Point-in-time status, stated per stage rather than in general

This is a **mechanism** test, not a decision-rule test. The distinction decides what the
revised-data prohibition applies to.

| stage | inputs | PIT status |
|---|---|---|
| A | `propadj` only | **clean by construction.** `F*` is anchor-invariant, so it computes correctly as of any past date |
| B | first difference of COT positions | **revised, and that is the better input.** The workspace rule blesses first differences on revised values for flow; the test measures what the pool actually did, not what a reader saw |
| C | B, plus volume and `kappa` | as B |

**Explicitly out of scope, and the evaluator must not drift into it:** any claim of the form
"a reader of the published panel on date T would have seen X and acted". That is the
decision-rule version, it requires `pit_complete`, and it is
[§7.8's deferred vintage replay](2026-08-02-validation-prereg.md), re-check no earlier than
2026-11-01.

If the outcome section states or implies a real-time-actionable claim, the verdict is void.

---

## 4. The control, which is the whole design

A raw crossing-to-unwind rate is worthless. `move_from_spot` is the trailing `k`-day return,
so "did price cross `F*`" is "did the `k`-day return reverse", which has a high mechanical base
rate. Measured against zero it would manufacture a result.

**The control is already in the panel: `trigger_{side}_pool_agrees == False`.**

`_agrees` returns `(pool_net > 0) == (signal > 0)`
([trigger.py:302](../../src/crowdmon/futures/trigger.py:302)). Where it is `False`, the price
level is real and **the book that would be forced is not there**. `2026-08-04 §D10` measured
the signal and the observed pool agreeing on only 65.9% of (market, horizon) pairs, so the
control group is large rather than exotic.

The two groups share the price mechanics exactly and differ only in whether a forceable holder
is present. That makes this a differential test rather than a rate, and it is the comparison
the package's own thesis implies: **fragility is the term that decides who actually gets
hurt.**

If unwind follows crossings equally in both groups, the crossing is measuring momentum
mean-reversion and the positioning overlay adds nothing. That is a real and publishable
outcome.

---

## 5. Test specification, frozen

### 5.1 Universe and period

- Report types: **`disaggregated` and `tff`, run separately and never pooled.** They partition
  differently and `macro_pca`'s `B21` established the report type is the subject, not a
  parameter.
- Markets: every `market_code` in the published panel with a resolvable `symbol` and a scored
  `damage_{side}_pct`. **Frozen by that rule, not by a hand-picked list.**
- Period: **2012-05-15 to the last complete report week at execution.** Start is the measured
  first scored week, not §6's stated floor.
- Lookbacks: `{20, 60, 250}`, per `DEFAULT_LOOKBACKS`. Not swept.

### 5.2 Stage A, the crossing

For each (market, report week `t`, side), using the vectorised form of §3.1:

A **crossing** occurs if, during the five trading sessions following `t`, the `propadj` close
reaches or passes `F*` for the **nearest** qualifying lookback on that side, in the direction
that flips the signal.

- Sell side: signal `+1` (long now), flip is **downward**.
- Buy side: signal `-1` (short now), flip is **upward**.
- Where several lookbacks qualify, the nearest by `|move_from_spot|` is the one that counts,
  matching `nearest_trigger`.

Record `crossed ∈ {True, False}` and the distance in sigma at `t`.

### 5.3 Stage B, the differential test

**This is the primary test. A and C are supporting.**

Outcome variable, per (market, week, side):

```
u = Δ pool_net over the following report week, divided by open_interest at t
```

`pool_net` and `pool_category` are published columns, so the pool is the one the trigger
named, not one the evaluator chose. Normalising by `open_interest` makes it comparable across
markets. **`open_interest` is the whole-market total repeated on every category row; do not sum
it across categories.**

Directional convention, fixed here: a forced **sell** is `u < 0`, a forced **buy** is `u > 0`.
Multiply the buy side by `-1` so both sides are "more negative means more forced flow in the
predicted direction", and state in the outcome that this was done.

The statistic is the **difference in median `u` between the agrees group and the contradicted
group, among crossings only**:

```
Δ = median(u | crossed, pool_agrees == True) - median(u | crossed, pool_agrees == False)
```

The claim predicts **Δ < 0**. Rows where `pool_agrees` is null (no pool supplied) are dropped,
not imputed, and their count is reported.

Report as secondary, without a threshold attached: the same difference among **non**-crossings,
which should be near zero if the crossing is what matters rather than the group label.

### 5.4 Stage C, the duration and size claim

**The trap, named in advance so a straw man is not refuted.** `dtl_sell` / `dtl_buy` as
published are **not** the prediction for triggered flow. `nearest_trigger`'s docstring is
explicit that `T` covers the whole fragility-weighted side while the trigger fires only the
trend-following slice of the weight-1.0 pool: on 6C, 9.00 days against 6.57 if the pool goes
flat and 13.13 if it reverses.

So the predicted flow is a **bracket**, not a number:

```
flow_close   = |pool_net|          (Δs = 1, pool goes flat)
flow_reverse = 2 · |pool_net|      (Δs = 2, the rule reverses)
```

Stage C asks only: among crossings in the agrees group, does realised `|Δ pool_net|` fall
inside `[0, flow_reverse]`, and where does it sit in that bracket? Report the median position
as a fraction. **No pass/fail threshold is attached to Stage C.** It is descriptive, and
pre-registering it as descriptive is what stops it being read as a second chance at a
positive result.

### 5.5 Inference, and the dependence that will otherwise inflate it

Crossings cluster in calendar time: one macro move crosses many markets in the same week, and
§6.3 of the §10 prereg measured exceedance runs averaging 4.8 weeks. A test treating
(market, week) rows as independent would overstate its sample badly.

**Block bootstrap over calendar weeks**, resampling whole **13-week blocks of weeks and taking
every market in those weeks**, so serial and cross-sectional dependence are both preserved.
10,000 draws, `seed=20260805`. The p-value is the fraction of draws whose Δ is at least as
negative as observed.

An IID bootstrap over rows is **forbidden** and its result may not be reported even as a
comparison.

### 5.6 Pass criteria, committed before looking

| outcome | criterion |
|---|---|
| **supported** | Δ < 0 with block-bootstrap raw p < 0.05, **and** the sign of Δ holds in at least **6 of the 10 asset classes** that have crossings in both groups, **and** the equivalence check in §3.1 reproduces below 1e-12 |
| **contradicted** | Δ >= 0, **or** the sign holds in 4 or fewer asset classes |
| **uninformative** | anything else, including p between 0.05 and 0.20 |

**All three conditions are required for `supported`.** The asset-class condition exists because
the panel's classes are unbalanced (Currencies 9 markets, Dairy 1) and a p-value alone can be
carried by one cluster; `clustering`'s `{6J, ZB, ZF, ZN, ZT}` yen-carry group is a live example
of five nominally separate markets that are one bet.

**Pre-committed statement about power.** Crossings are common but correlated, and the effective
sample is far smaller than the row count. A `supported` verdict is evidence that the mapping is
real, **not** evidence that `D` predicts returns, and it must not be described as the latter.
`uninformative` is a plausible outcome and is not a failure of the measure.

### 5.7 What is forbidden

- **Sweeping the crossing horizon.** Five sessions, fixed. Not 1, not 10.
- **Sweeping the lookback set**, or reporting per-lookback results as if they were separate
  tests.
- **Choosing markets by looking at the outcome**, or dropping a market because it is noisy.
- **Substituting a price series.** `propadj` per the layer-2 trap table. `unadj` cancels out of
  this test entirely and `backadj` is not a price.
- **Pooling the two report types**, or pooling the two sides without the sign flip in §5.3.
- **Reporting the IID bootstrap.**
- **Any real-time-actionable framing**, per §3.2.
- **Trading `D` or the trigger.** `composite.py` and §A.10.

### 5.8 Variant count for the SearchSpaceLog

This specification defines **6 variants**: 2 report types x 3 pre-declared robustness readings
(primary; crossings measured on the second following week instead of the first; and the
non-crossing placebo of §5.3). Every one is run and every one is logged, including any that
looks bad. If the evaluator runs anything not on this list, the count rises and the outcome
section says so.

`run_gauntlet` is **not** the instrument here, for the same reason §7.7 of the §10 prereg
records: it judges a directional strategy from a `TradeLog`, and this test produces no trades.

### 5.9 Store pinning, non-negotiable

Norgate back-adjusted series **restate history on every roll**, crowdmon derives `propadj` on
read, and a restatement therefore propagates into returns, volatility and every downstream term
**across all history**. A verdict computed against an unpinned live store does not reproduce
next week, and the difference reads as a methodology problem rather than as a restatement.

Reproduce §0 of the §10 verdict exactly: `status.json` at pin time, a SHA-256 / size / mtime
manifest of every parquet actually read, a byte copy outside the repo, and a measured count of
store files modified after the run began. All committed beside the outcome.

---

## 6. What the evaluator has to set up

Per §7.9 of the §10 prereg, unchanged and still current:

```bash
cd npf && .venv/bin/pip install --no-deps -e ../crowdmon
```

`--no-deps` matters. Verify the install resolves to the real tree rather than the workspace
phantom namespace package:

```bash
cd npf && .venv/bin/python -c "import crowdmon; print(crowdmon.__file__)"
```

A `None` there means the phantom, and every figure below would be computed from a package that
is not installed. Check `__file__`, not that the import succeeded.

The panel is read from `CROWDMON_STORE`, prices from `COTDATA_STORE`. The evaluator needs
**no** crowdmon computation for Stages A and B beyond the vectorised price arithmetic and the
published `pool_net` / `pool_category` / `trigger_*_pool_agrees` columns.

---

## 7. Where this lives, and where it runs (DECIDED)

**Lives here**, in `crowdmon/docs/handoffs/`, because this directory's README is the status
register that stops a handoff being executed twice, and `npf` has no equivalent. Filing it in
`npf` would leave it untracked, which `2026-08-03-index-share.md` records the cost of.

**Runs in `npf`**, by a session that has written none of crowdmon, per §2.

**The verdict is written in `npf`**, beside the §10 one, as
`npf/docs/crowdmon/YYYY-MM-DD-forced-flow-mechanism-verdict.md`, with a reproducer script
committed next to it. The outcome section below gets a pointer and a one-line result, not a
copy: `2026-08-03-index-share.md` records what two lineages of one document cost.

**Do not edit this body after execution.** Append §8.

---

## 8. Outcome

**Executed 2026-08-06 in `npf`**, by a session that has written none of this package. Verdict
and every number: `npf/docs/crowdmon/2026-08-06-forced-flow-mechanism-verdict.md`, reproducer
beside it. A pointer and a one-line result, never a copy.

**§5.6's criteria return `supported` on both report types, and the headline should not be
quoted on its own.** §5.3's own placebo carries **73.8%** (Disaggregated) and **51.9%** (TFF) of
the effect and is itself significant, where §5.3 says it "should be near zero if the crossing is
what matters rather than the group label". Removing the label leaves a real but small residual:
a difference-in-differences of **-0.001388 (p 0.047)** and **-0.002657 (p 0.0099)**, roughly
1.2% and 1.9% of the pool against headline figures of 4.5% and 4.0%. Disaggregated would not
survive a correction across even the two report types. **A marginal lean, not a clean
confirmation.**

§3.1's equivalence check reproduced **exactly**, 2.220446049250313e-16 over 96 comparisons
rather than the required 12, all 96 signals matching. Store pinned per §5.9: 267 parquets,
**zero moved during the run**, byte copy at
`~/code/cotdata_store_snapshots/2026-08-06-forced-flow-mechanism`.

**Four places this specification was wrong or unexecutable, each with the measurement that
shows it.** They are recorded here rather than corrected above, because the body is the record
of what was actually asked.

- **§5.6 has no placebo condition, and that is the gap the run found.** §5.3 pre-registers the
  expectation and attaches no criterion, so the criteria can be satisfied, and here are
  satisfied, by an effect that is mostly the group label. Anything re-running this should fix
  that first; the difference-in-differences is the shape the fix should take.
- **§4's control cannot be read from the panel, and §3 already says why.** §4 says the control
  "is already in the panel"; §3's own table measures `trigger_*_pool_agrees` at 39 rows over one
  week, because `add_trigger_distance` is a point-in-time overlay. §3 is the correct one. The
  control was recomputed over all 1,051 weeks from published `pool_net` plus `propadj`, along
  §3.1's vectorisation. Worth carrying: **`pool_agrees` reduces to the SIGN of `pool_net` and
  does not depend on the lookback at all**, which is what makes the placebo indispensable rather
  than a courtesy.
- **§4's central design claim is false as measured.** "The two groups share the price mechanics
  exactly and differ only in whether a forceable holder is present": the contradicted group
  crosses **more often** in both report types, 25.60% against 20.11% (Disaggregated) and 24.20%
  against 21.80% (TFF), because agreement selects weeks whose trend is less likely to reverse
  inside five sessions.
- **§5.5's p-value cannot be computed as written.** A bootstrap resampling the observed data is
  centred on the observed statistic, so "the fraction of draws at least as negative as observed"
  is ~0.5 whatever is true. Measured, it is: `p_literal` runs 0.465 to 0.526 across all six
  variants, including those whose recentred `p_null` is 0.0000. Both are reported; the criteria
  use the recentred one. Precedent for recording rather than silently applying: §7.7 of
  [`2026-08-02-validation-prereg.md`](2026-08-02-validation-prereg.md).

**Variant count: 8, not §5.8's 6**, and §5.8 requires saying so. The two additions are the
difference-in-differences, one per report type. Also added and carrying no statistic: a per-side
descriptive table, and the equivalence check widened from 1 symbol to 8 (its reported figure is
a maximum, so widening can only tighten the gate).

**One declared deviation from §6.** The equivalence check runs in **crowdmon's own venv** rather
than installing crowdmon into `npf/.venv`. That venv is shared by the main checkout and every
worktree, and installing into it changes what a concurrent session imports for the duration of a
run that does not need it. §6 is setup guidance rather than a threshold, statistic, universe or
criterion, so nothing frozen by §2 moved, and §6's own text says no crowdmon computation is
needed for Stages A and B. The phantom-package check §6 asks for is asserted in code before
anything is computed.

**§7's premise about where this lives has since changed, and the file stays here anyway.** §7
says it lives here because "`npf` has no equivalent" register. `npf` grew one on 2026-08-06 and
its companion, `2026-08-05-fragility-orthogonality.md`, moved there. This one does not move: it
is tracked here, it has now been executed and closed here, and moving a closed handoff would buy
nothing and cost a second lineage of one document.
