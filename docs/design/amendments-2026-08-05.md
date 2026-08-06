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

---

## E5. The damage panel prices at the report date, not at the latest bar, and that stands

Raised as a question about the `/damage` chart in `cot-analyzer`: is the plot using the most
recent price available, and would using it make the chart more accurate? Measured rather than
argued, then **decided as no change**. Recorded here because the reasoning is not written down
anywhere else and the question will recur: "use fresher data" is a reasonable-sounding
suggestion that nothing in the code refuses out loud.

### What the code actually does, measured

`publish` calls `add_trigger_distance(scored, pool_column="pool_net")` with no `as_of`, so
`stamp = frame["report_date"].max()` ([trigger.py:354](../../src/crowdmon/futures/trigger.py:354)).
That stamp reaches `trigger_prices`, which truncates before taking spot:

```python
ratio_series = ratio_series[ratio_series.index <= stamp]
level_series = level_series[level_series.index <= stamp]
spot = float(level_series.iloc[-1])
```

Volatility takes the same discipline by a different route: `add_risk_units` joins `sigma_daily`
with `merge_asof(..., direction="backward", tolerance=tol)`, so a row gets the most recent sigma
at or before its own report date and never one after it. It also publishes `sigma_date` and
`sigma_staleness_days`, so the gap is a value a reader inspects rather than an assumption.

The gap is not cosmetic. Panel anchored on 2026-07-28 against a price store running to
2026-08-04:

| symbol | store's latest close | close actually used |
|---|---|---|
| GC | 4152.60 | 4038.70 |
| NG | 2.68 | 2.66 |
| ZC | 442.25 | 458.50 |

Gold 2.8% away, corn 3.5% in the other direction.

### What repricing to the latest bar would do

Recomputing every trigger at 2026-08-04, 47 markets, **70 (market, side) pairs with a trigger on
both dates**:

| | |
|---|---|
| median absolute change | **1.742 sigma** (p90 5.901, max 65.256) |
| new/old ratio | median 0.903, range 0.025 to 328.567 |
| **cross the 1.5 close line** | **29 of 70, 41%** |
| nearest lookback `k` changes | 27 of 70 |
| a side gains / loses a trigger entirely | 6 / 6 |

Worst individual moves: `LBR` buy 66.906 -> 1.650 sigma as the nearest horizon flips 250d to
60d, `ZL` sell 1.604 -> 11.916, `ZR` sell 10.239 -> 1.321.

**That 41% is the argument against repricing, not for it.** A quantity where two fifths of
readings cross the threshold defining the quadrant column in five sessions is not a precise
measurement being degraded by staleness. It is a noisy one, and refreshing it yields fresher
noise. This is `nearest_trigger`'s "snapshot, never a countdown" measured on the panel rather
than on one market.

### Why the anchor stands

1. **The pool would still be stale.** COT is weekly, published Friday for Tuesday. Fresh price
   against a week-old position trades "both inputs one week old" for "one current, one stale",
   which is vintage skew inside a single row rather than between rows. It lands hardest on
   `trigger_*_pool_agrees`, which compares the sign of the price signal to the sign of the
   observed pool: at matched vintage those already disagree on a third of (market, horizon)
   pairs (`2026-08-04 §D10`), and refreshing one side of a comparison stops it meaning what it
   says.
2. **The history would break at its last point.** Every historical week is computed at its own
   report date, so a latest-price current week would be defined differently from all 1,050
   before it, at exactly the observation a reader looks at hardest. A "latest price" history
   cannot be rebuilt retrospectively without lookahead, which is what release-date indexing,
   `pit_complete` and the §10 pre-registration exist to prevent.
3. **Daily publishing stops being idempotent.** The publisher runs daily against weekly data
   *because* the panel is anchored on the report date, so a re-run between releases is a no-op
   while a failed weekly publish would leave a stale panel up for seven days. Price-at-run-time
   makes every day's panel differ for the same report week, which also collides with the
   additive-only rule.
4. **It is bigger than the trigger column.** `D` is price-dependent through `C`
   (notional x sigma) and `I` (sigma, volume). Repricing only the trigger puts `D` and the
   trigger at different vintages within one row; repricing everything marks Tuesday's contracts
   at today's price.

### One expectation that did not survive contact

`nearest_trigger` records that the reference bar drifts faster than spot, measured on 6C over
120 sessions at a daily standard deviation of 0.4256% against 0.2540%, **1.68x**. The natural
inference is that most of the drift in distance-to-trigger is last year's bars rolling off
rather than price moving.

Over 2026-07-28 to 2026-08-04 across 47 markets it is the other way round: **|spot move| median
2.705%, |F\* move| median 1.527%, a ratio of 0.56x.** These are different measurements (one week
cross-sectionally against a 120-session daily dispersion on one market), so this does not
contradict the docstring and the docstring is left as it stands. It does mean the reassuring
version, that the drift is mostly bookkeeping, is **not established**, and nobody should quote
it as though it were.

### What would be legitimate, if the live read is ever wanted

An **additional** `trigger_*_sigma_live` column beside the anchored one, labelled as a different
vintage, never a replacement. `trigger_prices` is anchor-invariant and takes `as_of`, so
`publish` would call `add_trigger_distance` a second time. It has to happen in `crowdmon` on the
price-holding machine: `cot-analyzer` computes no metrics and cannot reach a price store
([ADR-0001](../adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md)).

### Reproducer

Not in `docs/analysis/reproduce.py`. Every figure above came from ad-hoc scripts in the session
of record, against `~/code/cotdata_store` and `~/code/crowdmon_store/damage/2026-07-28`, and the
store was **not pinned**. Norgate restates history on every roll, so the repricing table is a
point-in-time observation that will not reproduce exactly. It is recorded at this fidelity
deliberately: the decision rests on the 41% being large, not on it being 41%.
