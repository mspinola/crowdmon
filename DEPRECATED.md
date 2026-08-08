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

**Re-measured 2026-08-08, two days later: 9 failed, 643 passed, 7 skipped.** The count is
recorded rather than the figure above being edited, because the change *is* the point. Three
more pins broke in two days, in two files the original six did not touch:

```
tests/test_stratum_live.py::test_the_latest_week_partitions_exactly_where_C14_partitioned_it
tests/test_stratum_live.py::test_the_seven_differentials_are_still_exactly_seven_and_still_those_seven
tests/test_supplemental_live.py::test_c2_template_rate_cannot_move_with_w_sd
```

Point 2 below predicted this in general terms and understated it: the drift does not merely
widen existing deltas, it **recruits new tests** as the store advances into weeks the pinned
counts never saw. Anyone reading "6 of 654" as the standing number will be wrong, and more so
each week.

**Three things follow, and the third is the one that matters.**

1. **Red does not mean broken here.** Nothing regressed. A frozen package pinned against a
   moving store fails by construction.
2. **It gets worse, not better, and in two ways rather than one.** Every week the store
   advances widens the gap. This point originally said a reader running the suite in six
   months would see "the same six failures with larger deltas", which the 2026-08-08
   re-measurement above shows was too kind: the count itself grows as the store reaches weeks
   the pins never saw. Six became nine in two days.
3. **It was downstream of the §3 decision, and that decision has now been made.** The
   reasoning stood as written: if the publish job kept running the panel would keep pace and
   these would pass again, and if it was switched off they would fail permanently. **It was
   switched off on 2026-08-08** (§3), so they now fail permanently and no longer flap.

   **The fix remains what it always was: neutralise the pins rather than chase them**, because
   a frozen repo should not have tests that depend on data collected after it was frozen. It is
   still not done here, but the reason has changed. It was withheld because doing it would
   presume the §3 answer; now it is simply unclaimed work on an inert package, and the daily
   job that used to surface the failures is gone, so nothing reports them any more. Anyone
   running the suite should expect a growing set of red `*_live` pins, nine as of 2026-08-08,
   and read this section rather than debug them.

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

## 3. Nothing is still running, and nothing is open

**Resolved 2026-08-08. This section previously listed two launchd jobs, one consumer page and
one open work order, left running because switching them off was a decision about whether the
panel is still worth reading rather than a research question.** That decision was made and it
went against the panel:

- `com.mspinola.crowdmon-publish` and `com.mspinola.crowdmon-live-tests` were unloaded and
  their plists deleted. `live-tests` had been failing every morning since deprecation, on the
  drifting live pins §2.1 describes, notifying about a package nobody is developing.
- `cot-analyzer`'s `/damage` page was removed in that repo's PR #22, along with its artifact
  reader and both test files. This package now has **no consumers at all**; nothing in `npf`
  or `livebook` ever imported it.
- [`docs/handoffs/2026-08-06-trigger-contradicted-copy.md`](docs/handoffs/2026-08-06-trigger-contradicted-copy.md)
  was **closed unstarted**, which is what its own §1 instructed for exactly this case. Outcome
  appended as its §8.

`~/code/crowdmon_store` is now written by nothing and read by nothing. It is left in place
rather than deleted, on the same reasoning as §2: it costs 8.7M and removing it is not
reversible.

**None of this is evidence about the thesis.** Per §4, removing a consumer meets none of the
three conditions for revisiting, and it retracts nothing. The package still builds, its
measurements still stand, and §5's harvest is untouched. What changed is that it is now
genuinely inert rather than quietly scheduled.

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
