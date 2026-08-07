# crowdmon is deprecated

**Decided 2026-08-07.** Development stops. The package is **frozen, not deleted**, and §4
states the conditions under which the decision would be worth revisiting.

---

## 1. Why

The thesis was `damage = crowding x illiquidity x holder fragility`. It was tested four times,
each time against a pre-registration frozen before the statistic was computed, each time
executed in `npf` because `tests/test_boundaries.py` refuses a `crucible` import precisely so
this package cannot render a verdict on its own output.

| test | result |
|---|---|
| §10 validation, the core claim: is `D` elevated *before* a forced-exit episode? | **`uninformative`**, and the clean episodes are **spent** |
| Index share: is index positioning stickier than swap? | **genuine null**, premise retired |
| Fragility orthogonality: do `Phi` and `I` separate the trend book's trades? | Stage 1 independent, **Stage 2 genuine null** |
| Forced-flow mechanism: when the trigger fires, does the pool move? | `supported` on the letter, **mostly artifact**, marginal residual |

Four honest tests, no positive result.

**The asymmetry between those failures is what decided it.** They did not all fail the same
way, and only one kind of failure is fixable.

The mechanism test failed for a repairable reason: it measured `Delta pool_net`, which this
package's own `futures/flow.py` documents in its first paragraph as unable to tell a forced
exit from a fresh entry in the same direction. That is a bad test, not a dead idea, and
`docs/handoffs/2026-08-06-forced-flow-respecification.md` records the corrected design.

**The §10 validation did not fail that way.** It tested the actual claim, competently, and
came back uninformative with **the evidence exhausted**. Hand-identified clean episodes are a
finite stock and they are spent. No better design recovers them; only new crises do, and those
cannot be scheduled.

So the optimistic path is narrower than it looks. Even a clean pass on a repaired mechanism
test establishes **the mapping**, which that pre-registration's §5.6 says explicitly is not
evidence that `D` predicts anything. The claim that would justify the footprint is the §10
claim, and it is out of ammunition.

**Waiting does not help**, which was checked rather than assumed. The mechanism sample already
spans 2012-05-15 to 2026-07-21, **57 blocks** of 13 weeks. A further year adds about four:
roughly 7% more data and 3% tighter standard errors. §1 of that pre-registration chose the
question partly because its evidence regenerates weekly, which is true in the sense that it is
never *spent* and false in the sense of getting usefully stronger on any horizon worth waiting
for.

### The argument that was considered and rejected

"The mechanism test was flawed, so the idea might still work" is true here. It is also the
argument that keeps dead projects funded for another six months. It raises the ceiling on what
a better test could find; it is not evidence of anything. Recorded because it is the strongest
case against this decision and it should not have to be re-derived by whoever reads this next.

---

## 2. What deprecated means here, concretely

| | |
|---|---|
| **Frozen** | No new modules, no new engines, no new handoffs against the composite |
| **Not deleted** | Every file stays. Other repos cite these documents, and a citation has to land on real text |
| **Not retracted** | The measurements stand. A parked hypothesis is not a withdrawn one |
| **Tests are NOT all green**, and §2.1 says why | 6 of 654 fail, all of them live pins drifting against a moving store. Red here does not mean broken |

### 2.1 The suite is red, and it is drift rather than rot

Measured on `main` at deprecation, **6 failed, 648 passed, 5 skipped**. An earlier draft of
this file claimed the suite was left green. It is not, and the claim was corrected rather than
the tests, because what is failing is worth understanding.

```
tests/test_brief_live.py::test_the_two_null_causes_split_where_C20_measured_them
tests/test_brief_live.py::test_the_separating_rule_still_has_zero_exceptions
tests/test_publish_live.py::test_the_trigger_counts_reproduce_d9
tests/test_publish_live.py::test_the_pool_column_is_supplied_so_the_agreement_flag_is_not_null
tests/test_publish_live.py::test_the_pool_check_removes_half_of_d9s_close_and_severe_cell
tests/test_publish_live.py::test_the_manifest_counts_match_the_panel_it_ships_with
```

**Every one is a `*_live` test comparing a recomputation against a pinned count.** The
`COTDATA_STORE` has advanced to report week **2026-08-04** while the published panel is pinned
at **2026-07-28**, so the recomputation carries one extra market-week and the pins are off by
exactly that: 6,669 against a pinned 6,668, and a date assertion reading `2026-08-04` where it
expects `2026-07-28`.

This is the same failure mode `docs/design/amendments-2026-08-05.md` §E1 already recorded, and
it was six pins then too.

**Three things follow, and the third is the one that matters.**

1. **Red does not mean broken here.** Nothing regressed. A frozen package pinned against a
   moving store fails by construction.
2. **It gets worse, not better.** Every week the store advances widens the gap. A reader
   running the suite in six months will see the same six failures with larger deltas.
3. **It is downstream of the §3 decision, not independent of it.** If the publish job keeps
   running, the panel keeps pace and these pass again; if it is switched off, they fail
   permanently. **Whichever way that goes, the fix is to neutralise the pins rather than to
   chase them**, because a frozen repo should not have tests that depend on data collected
   after it was frozen. That work is deliberately not done here: it belongs with whoever makes
   the §3 call, and doing it first would presume the answer.

**The harvest is complete.** [`docs/HARVEST.md`](docs/HARVEST.md) classifies all 108 numbered
findings in `docs/design/amendments-*.md` as PORTED, RESOLVED or DIES, and nothing remains
unhoused:

- **To `cotdata`**: `cross-report-comparability.md` (Legacy and TFF agree on exactly two
  quantities; the `spread_contracts` null trap) and `reading-the-store.md` (universe
  composition, coverage denominators, the volume parameter, code continuity, price tiers).
- **To `cotmetrics`**: `positioning-series-properties.md` (exceedances arrive in episodes, so
  a count of them is not a sample size; correlating positioning levels is spurious).

Facts were **restated, never moved**. `docs/analysis/` and the amendment series are
point-in-time records under this repo's doc lifecycle; rewriting them would destroy the record
of when each thing was learned, which is what makes "the data contradicted the brief" a
checkable claim.

### The verdicts live in npf

They were rendered there, and they stay there: `npf/docs/crowdmon/`, dated 2026-08-01,
2026-08-06 twice, each with a committed reproducer, a pinned store manifest, and for the
mechanism test a byte copy of the store at
`~/code/cotdata_store_snapshots/2026-08-06-forced-flow-mechanism`.

---

## 3. What is still running, and what is open

**Two launchd jobs and one consumer page**, listed rather than switched off, because turning
them off is a decision about whether the panel is still worth reading and that is not a
research question:

- `com.mspinola.crowdmon-publish` and `com.mspinola.crowdmon-live-tests`.
- `cot-analyzer`'s `/damage` page, this package's only consumer. Nothing in `npf` or
  `livebook` imports it.

**One open work order**,
[`docs/handoffs/2026-08-06-trigger-contradicted-copy.md`](docs/handoffs/2026-08-06-trigger-contradicted-copy.md).
It is a copy and vocabulary fix, not a research task: when `pool_agrees` is `False`, both
renderers say the level "would force a book that is not there", and the measurement says flow
follows either way with the difference between groups small. **Its status depends entirely on
the page**: worth doing if the panel keeps being read, moot if it does not, and it should be
closed unstarted rather than left open in that case.

---

## 4. Conditions for revisiting, stated so they are checkable

Vague promise is how a parked project becomes an undead one. **Any one of these, on its own,
makes it worth reopening. Nothing else does.**

1. **New clean forced-exit episodes.** §10 needs hand-identified episodes uncontaminated by
   the events already used. Two or more genuinely new ones would restore the test the whole
   thesis rests on. This is the only condition that addresses the core claim.
2. **A point-in-time replay becomes possible.** Vintages accumulate forward from 2026-07-31,
   and §7.8 of the §10 pre-registration gates its replay at **no earlier than 2026-11-01**.
   That answers a different question from §10, the decision-rule one, and it is the only
   scheduled thing in this list.
3. **The respecified mechanism test is run and comes back strong on the corrected outcome
   variable.** `docs/handoffs/2026-08-06-forced-flow-respecification.md` §4. This would raise
   the ceiling; on its own it still would not establish that `D` predicts anything, per §5.6.

**Not a condition**: a new module, a better weight table, another engine, or a reading of the
existing data from a fresh angle. The data has been read. What is missing is evidence that has
not happened yet.

---

## 5. What was worth building anyway

Recorded because a project that produced nothing and a project whose hypothesis did not survive
are different things, and the second one is normal.

The measurements outlived the thesis. Several are now load-bearing in `cotdata` and
`cotmetrics`: the `propadj` / `backadj` trap that corrected cotdata's own spec, the
Legacy/TFF comparability limit, the Supplemental basis mismatch, the open-interest identity
across 48,950 market-weeks, the fact that 76% of the Disaggregated universe is power and gas
basis, and the near-unit-root property that makes level correlations on positioning
meaningless.

The working agreement that produced them is the part most worth carrying forward: **measure,
do not assume**, and where a measurement contradicts a document, fix the document in the same
change and say so. Probing the actual files overturned a written assumption in nearly every
session here, including several of this package's own.

The harvest also turned up something this repo never looked for: `cotmetrics` computes six
price-against-positioning **level** correlations per lookback whose null has never been
measured, which the corrected rule above says cannot be interpreted without one. It is
written up there as a check to run rather than a defect report. A project's last useful act
being to hand a neighbour a question worth asking is a reasonable way to finish.
