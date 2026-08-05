# Spec amendments, 2026-08-05

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

Sections here carry an **`E` prefix**, per the per-day convention stated in
[README.md](README.md). [`amendments-2026-08-04.md`](amendments-2026-08-04.md) is closed at
D14. Cross-file references carry the date: `2026-08-04 §D12`.

---

## E1. Six live pins fail on store drift, and every one of them is a market COUNT

> **Superseded in its diagnosis by `§E4`, which closed all six.** "Store drift" is too vague
> to be right: the six moved for ONE reason, and it is the second half of `§D11`'s tranche
> landing a day after the first half. The observation below (that six pins fail, that every
> one is a count, and that they predate any branch in flight) is accurate and is what the
> section was for. The implied cause is not. Read `§E4` for what actually moved and why.

Measured while re-taking the suite totals for the `column_definitions` branch, so this is a
side observation rather than the work, and it is recorded because a session that runs the
live suite tomorrow will see six red tests and needs to know they are not its doing.

Reproducer, from the **main checkout** at `265ff30`, with no branch applied:

```
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python -m pytest tests/ -q
6 failed, 644 passed, 5 skipped
```

| test | pins | store now holds |
|---|---|---|
| `test_publish_live.py::test_the_universe_is_the_47_covered_markets` | 47 covered markets | **49** |
| `test_stratum_live.py::test_no_covered_market_is_a_certificate_or_a_differential` | 27 outright | **29** |
| `test_publish_live.py::test_the_trigger_counts_reproduce_d9` | the `§D9` trigger counts | moves with the universe |
| `test_publish_live.py::test_the_pool_column_is_supplied_so_the_agreement_flag_is_not_null` | the pool coverage | moves with the universe |
| `test_brief_live.py::test_the_two_null_causes_split_where_C20_measured_them` | the `§C20` null-cause split | moves with the universe |
| `test_brief_live.py::test_the_separating_rule_still_has_zero_exceptions` | the same split | moves with the universe |

**The direction is the healthy one and that is the point.** The universe grew, so markets
that could not be scored now can be, and the failures are the pins noticing. Nothing here is
evidence of a defect in `src/`: the two that fail with a readable number fail by exactly the
amount the store gained (49 against 47, 29 against 27), and the other four are downstream of
the same universe.

**They are not fixed here**, because refreshing a pin is a measurement in its own right and
belongs with whoever re-derives `§C20` and `§D9` rather than with a manifest key. What is
recorded instead is that they are **pre-existing on `main`**, so a branch that inherits them
has not caused them, and a branch that reports a green live run has almost certainly not run
one.

## E2. The worktree suite figures in `CLAUDE.md` were wrong in both halves

`CLAUDE.md` carried "**From a worktree those two figures are 613 / 7 and 536 / 84**" beside a
main-checkout pair of 650 / 5 and 562 / 93, and a sentence stating the exact relationship
between them: a worktree skips the two producer-direction `test_boundaries` checks, so it
"reports two fewer passes".

**The sentence is right and neither pair matched it.** Measured at the same commit, on the
same store:

| | main checkout | worktree | delta |
|---|---|---|---|
| live (`COTDATA_STORE=~/code/cotdata_store`) | 650 / 5 | **652 / 7** | 2 passes move into skips |
| fixture (`COTDATA_STORE=/tmp/crowdmon_test`) | 562 / 93 | **564 / 95** | 2 passes move into skips |

(Both green-run figures. They were hypothetical when this section was written, because
`§E1`'s six failures sat inside the live half in both checkouts; `§E4` closed them, so the
live pair is now what a run actually reads.)

The old fixture pair sat **26 passes and 9 skips** from its own main figure, which is not a
delta any explanation in the file produces. So the pair was never re-measured alongside the
four totals it sits under, through at least the four moves the totals record. That is
precisely the drift the surrounding paragraph exists to prevent, arriving in the note that
warns about it.

**The fix is to state the pair as derived rather than quoted.** A worktree run is the main
figures with two passes moved into skips, and that is checkable arithmetic against numbers
the same paragraph already carries. A second independently-quoted pair is a second thing to
keep current, and this file is now the record of what happens when nobody does.

## E3. `column_definitions`: the four undefined panel columns, defined at the producer

`cot-analyzer`'s `/damage` page rendered "not defined in the panel, so not defined here" for
four columns it shows, because the manifest published `factor_questions` for `C`, `I` and
`Phi` and nothing for anything else. That admission is the mechanism working: the consumer
may not type a definition of its own (`cot-analyzer/tests/test_damage_vocabulary.py` fails
its build if it does, on ADR-0001's argument), so naming the gap is the only pressure that
gets it published here.

Added to [`report.py`](../../src/crowdmon/futures/report.py) as `COLUMN_DEFINITIONS`, keyed by
**panel column** with `<side>` where the panel carries a `sell` and a `buy` copy, and shipped
by [`publish.py`](../../src/crowdmon/futures/publish.py) as `column_definitions`. Five terms:
`damage_<side>_pct`, `trigger_<side>_sigma`, `trigger_<side>_pct`, `dtl_<side>`, `beta`.

**Deliberately a sibling of `FACTOR_QUESTIONS` and not more entries in it.** That key means
the three factors of `D = C x I x Phi`, and the consumer reads it that way: adding `beta` to
it would say four things multiply where three do.
`tests/test_publish.py::test_the_definitions_stay_out_of_the_factor_questions` asserts the two
key sets stay disjoint.

**Two things the definitions say that a formula alone does not**, both taken from measurements
already in this repo rather than composed here:

- `dtl_<side>` is named as **a level and not a percentile**, because `illiquidity_<side>`
  beside it in the same grid is the percentile of that very number, and a reader with two
  columns and one concept picks wrong.
- `beta` is named as **not a factor of `D`**. It sits in the panel as a caveat carrier
  (`commonality.py` is explicit that a constant `beta_bar` cannot change `D` at all, and that
  wiring it in is a decision about what `§A.9`'s `I` should be), so a reader seeing it in a
  damage grid would otherwise reasonably assume it multiplies in.

### The version trap, and why the key ships under `SCHEMA_VERSION = 1`

`cot-analyzer/src/components/crowdmon_artifact.py` refuses a `schema_version` it does not
recognise and degrades the **whole page** to an "unavailable" card. So a bump shipped ahead of
a consumer release does not ship the page without the new key, it takes the page down; a
reader that has never heard of an added optional key simply does not render it, which the
consumer pins in
`test_the_glossary_survives_a_manifest_that_carries_none_of_it`.

The constant's own comment now says so. It read "bumped whenever `PANEL_COLUMNS` or the
manifest shape changes in a way a reader must notice", which is true and does not tell you
which side of the line an added key falls on. **An additive optional key is not such a change.
Bump when an existing key changes meaning, shape or units.**

## E4. All six pins moved for one reason, and it is a tranche that landed in two halves

`§E1` recorded six failing live pins and called the cause store drift. That was a guess
dressed as a diagnosis. Measured properly, **every one of the six moves by exactly the
contribution of two markets**, rough rice (`039601`, `ZR`) and ICE Europe WTI (`067411`,
`WBS`), which are `§D11`'s backlog tranche.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`
for the spec side, and the three live test files themselves for the panel side.

### The landing took two producer runs, a day apart, and the pins were taken between them

`§D11` reads "once the producer run wrote `ZR` and `WBS` (cotdata #99 plus
`cotdata-update --metadata --prices`)". Those two flags write the **contract-spec table and
the price bars**. They do not write `cot_disagg`. The current-state COT parquets for the two
new markets arrived only with the next COT run, which `status.json` records as
`last_run.kinds = [cot_legacy, cot_disagg, cot_tff, cot_supplemental]` at
**2026-08-05T12:10:54Z**.

So for one day the tranche was half-landed: **spec'd and priced, but not on the panel.**
Every figure measured in that window recorded a state that was neither the before nor the
after, and three of the six pins were written inside it.

### The reconciliation, and there is no residue

| quantity | pinned | now | difference |
|---|---|---|---|
| markets on the published week | 47 | **49** | `+ZR +WBS` |
| of those, scoreable (a contract spec reaches them) | 45 | **47** | `+ZR +WBS` |
| scored on the sell side | 43 | **45** | both new markets score |
| forced-sell levels | 37 | **39** | both carry one |
| forced-buy levels | 35 | **37** | both carry one |
| pool answers | 37 | **39** | identically the sell-level count |
| horizons disagree | 27 of 45 | **29 of 47** | both disagree |
| current-state Disaggregated markets | 27 | **29** | `+ZR +WBS` |
| current-state market-weeks | 27,194 | **29,133** | `+1,051 +888 = +1,939` |
| warm-up nulls | 2,575 | **2,781** | `+103 +103` |
| missing-term nulls | 6,256 | **6,668** | `+206 +206` |
| scored rows | 18,363 | **19,684** | `+742 +579` |

Every difference is the sum of the two new markets' own rows. **No pre-existing row changed**,
which is the distinction that matters: a restatement would have moved these counts too, and it
would have moved them without the arithmetic closing. It closes to the row.

### Three things worth carrying, none of which is "the numbers were stale"

**1. A historical count can move without any history being restated.**
`test_brief_live.py` said so in a comment: "Historical rows, so these do not move when a new
week lands: a change means the store was restated or backfilled." Both stated causes are
right and the list is short by one. A new MARKET arrives carrying twenty years of its own
history, so it moves a historical total while leaving every existing row untouched. The
comment is corrected in place, because a note that enumerates the ways a number can move is
worse than no note when the enumeration is short: it tells the next reader to go looking for
a restatement that did not happen.

**2. Two different quantities were both called 47, and the pin cited the wrong one.**
`test_the_universe_is_the_47_covered_markets` cited `§D11`'s "47 covered markets". `§D11`
means **spec'd markets in the latest vintage week**, which is 27 Disaggregated plus 20 TFF
and is **still 47 today**. The test measures **markets on the published panel**, which was
27 Disaggregated plus 22 TFF, and is 49. The two coincided at 47 on the day the pin was
written, so the citation looked like it explained the number, and it never did.

The panel figure is larger because it includes the two markets no contract spec reaches:
MSCI EAFE (`244041`) and MSCI EM (`244042`), both `Role: heldout`, which Norgate carries
neither specs nor prices for. **They are rows a consumer counts and they can never produce a
`D`.** The refreshed pin asserts the decomposition rather than the total, and names them.

**3. `§D9`'s trigger counts were carried into a universe they were not measured on.**
37 and 35 were measured "of 45". They were pinned unchanged while the panel was 47, and
passed, because the two extra markets were the unscoreable pair and had no trigger either
way. A count that survives a change of denominator by luck is indistinguishable from one
that was re-measured, so the refreshed test pins **the eight markets with no forced-sell
level** (`ZB`, `ZT`, `ZN`, `ZF`, `SB`, `6S`, `6J`, `6E`) beside the counts. That set did not
move, and it is the part with a reason behind it: every one is a market whose every horizon
is currently short, which is an answer rather than a gap.

### What did not move, which is the actual finding

The gate `§C13` and `§D11` both check still passes, and passes on the same terms: **29 of 29
current-state markets are classic outright, 0 certificates and 0 differentials.** The covered
set remains the complement of what makes the vintage panel hard to reason about rather than a
sample of it, and the two additions are a grain and an energy outright, which is the
character it already had.
