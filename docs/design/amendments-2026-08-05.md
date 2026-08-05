# Spec amendments, 2026-08-05

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

Sections here carry an **`E` prefix**, per the per-day convention stated in
[README.md](README.md). [`amendments-2026-08-04.md`](amendments-2026-08-04.md) is closed at
D14. Cross-file references carry the date: `2026-08-04 §D12`.

---

## E1. Six live pins fail on store drift, and every one of them is a market COUNT

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

(Both green-run figures, per `§E1`; the live half currently reads six of those passes as
failures in both checkouts.)

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
