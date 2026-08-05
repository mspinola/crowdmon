# Handoff: publish the damage panel, so a UI can read `D` without importing this package

**Status:** **CLOSED.** §1-§3 complete (the publisher, the ADR, the tests). **§4, the
asset-class rollup, is WITHDRAWN as not wanted** (2026-08-04, by the requester). Its gate
passed; that was never the question. See the second outcome section
**Date:** 2026-08-04
**Claimed by:** the session asked how to visualise crowdmon's weekly findings in
`cot-analyzer`
**Blocked on:** nothing. `2026-08-04 §D9`-`§D12` had all landed before this started
**Depends on:** [ADR-0001](../adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md),
which this handoff proposed and which was accepted in the same pass
**Not this handoff:** the `cot-analyzer` page itself, which is a change in another repo and
carries its own obligations (see §5)

> Announced before the first line of code, per this directory's convention. If you were about
> to start it, say so and I will drop it.

---

## Scope

`composite.damage_block` plus `report.format_damage_block` and `report.format_offside`
deliver one self-describing reading per market-week, and nothing reads them. The question was
how to get that in front of a reader in `cot-analyzer`, the only UI in the workspace.

## Measured before claiming, and the obvious integration is impossible

The obvious route is `-e ../crowdmon` in `cot-analyzer` and a call to `add_composite` in a
Dash callback. It fails on four counts and the fourth is arithmetic rather than argument:

| # | Obstacle | Source |
|---|---|---|
| 1 | cot-analyzer "computes no metrics of its own", recorded three times | `cot-analyzer/README.md:9`, `:50`, `docs/ARCHITECTURE.md:45` |
| 2 | this package refuses the same shape from its own side | `brief.py`: "a derivation in the rendering is how the next engine gets built by accident" |
| 3 | the ladder needs Norgate `unadj` + `propadj` + `contract_specs`; the host cannot produce prices | `cot-analyzer/server-side/README.md`, crucible-stack ADR-0007 |
| 4 | **that host runs Python 3.9**; this package declares `>=3.10` | `cot-analyzer/server-side/README.md:58-59`, `pyproject.toml` |

So the seam is a file. ADR-0001 records it.

## What shipped

**§1. `futures/publish.py`** — `build_damage_panel`, `panel_manifest`, `publish_panel`,
`store_root`, `annotated_panel`. Both report types concatenated, every caveat carrier
attached, atomic write, `CROWDMON_STORE` raising when unset.

**§2. `bin/publish_damage.py` and `bin/publish_damage.sh`** — the driver, modelled on
`bin/live-tests.sh`, defaulting both env vars because launchd reads no shell profile.

**§3. Tests** — `tests/test_publish.py` (17, fixture) and `tests/test_publish_live.py` (11,
real store). `tests/test_boundaries.py` now walks `bin/` as well as `src/crowdmon`.

## Four decisions taken deliberately rather than by default

**1. Both report types, not just Disaggregated.** Disaggregated alone is 27 commodity
markets. With TFF the panel is **47 markets across all 10 asset classes**, and equities,
currencies, rates and crypto reach a reader through TFF or not at all. `§D7` is the argument
for why Legacy cannot stand in.

**2. `add_commonality` runs by default.** The composite chain never calls it, so README
reading instruction 4 (`§B2`, exits are not independent) has no per-row carrier unless the
publisher adds one. It was budgeted as the expensive step and measured at **1.3s** of an 8.0s
build, so the reason to leave it on is no longer even cost.

**3. The pool column is supplied.** `docs/analysis/reproduce_single_number.py` calls
`add_trigger_distance` with no `pool_column`, which leaves every `*_pool_agrees` null. `§D10`
measures that the observed pool and the price signal disagree on a third of pairs, so a panel
published that way ships a trigger that cannot say whether the book it would force exists.
See §D13 for what supplying it does to the headline.

**4. The blocks are pre-rendered, and the vocabularies travel as data.** A consumer
assembling its own layout from the structured dict would have rebuilt the
`include_caveats=False` flag `brief.py` deliberately does not have. A consumer holding its
own copy of `SCORE_STATES` or the four `QUADRANT` strings would be the fifth copy of a living
document, in the repo with the weakest guards.

## What this must not do

- **No aggregation of `D` across markets.** `composite.py` is explicit that the raw product
  has no meaning across markets. The panel is per market-week and the rollup is §4, gated.
- **No new reading instruction.** ADR-0001 settles that a rollup does not extend
  `brief.READING_INSTRUCTIONS`, so `tests/test_reading_instructions.py` and
  `tests/test_references.py` do not pull against each other.
- **No read-back.** `core/store.py` stays absent. Nothing in `src/` opens `CROWDMON_STORE`
  except the short-panel interlock on the write.

---

## §4. The asset-class rollup — OPEN, unclaimed, gate measured

The useful class-level object is **not** a mean of `D`. It is a count of markets per asset
class in each of the four cells `report.QUADRANT` already defines, whose boundaries are
`CLOSE_SIGMA` and the `0.75` severity floor rather than a threshold anyone would have to
invent. It only ever asks a per-market yes/no question and counts booleans, so nothing is
averaged or compared across markets at any point.

**Pre-registered gate, written before the counts were looked at:** if the median asset class
has fewer than 3 scored markets, the rollup ships as counts only with no share column.

**Measured 2026-08-04, week ending 2026-07-28**, scored sell side:

| asset class | n |
|---|---:|
| Currencies | 9 |
| Grains | 6 |
| Softs | 5 |
| Metals | 5 |
| Equities | 5 |
| Energies | 4 |
| Fixed Income | 4 |
| Live Stock | 3 |
| Crypto | 1 |
| Dairy | 1 |

Median **4.5**, so the **gate passes**. The share column ships, suppressed below n=4 with an
explicit `share_suppressed` boolean rather than a null a reader has to interpret, and a
single-market class renders as "one market, this is that market's reading" rather than as
0% or 100%.

**The constraint whoever takes this inherits.** A count of simultaneous extremes within an
asset class *is* a joint-occurrence statement, and joint occurrence is exactly what `D` is
measured not to carry: `beta_bar` is 0.634 excluding own-market, with milk and hogs near 0.07
and the wheats above 1.0. Grains sharing a door is *why* they go extreme together. So the
rollup must carry `min_beta` and `max_beta`, the spread rather than the mean, and must refuse
to emit a share at all when `beta` is absent.

Name it `futures/rollup.py`. **Not `breadth.py`**: that name is taken by the §6.2
breadth-versus-depth decomposition and is exported flat from `futures/__init__.py`.

## §5. The consumer's obligations, for whoever writes the `cot-analyzer` page

Not this repo's work, and recorded here because the artifact is only a contract if the other
side keeps it:

1. **No crowdmon string literal in cot-analyzer source.** Not `"warmup"`, not `"certificate"`,
   not the `QUADRANT` strings. Enforced by a grep test on that side. This is the obligation
   ADR-0001 places on a consumer, and without it the artifact is a convention.
2. **The quadrant is suppressed when `trigger_*_pool_agrees` is `False`.** `format_offside`
   does this and a chart must too: plotting such a market in the CLOSE-and-SEVERE cell is
   precisely wrong. `NA` is a third state and must not render as `False`.
3. **No offside history.** The trigger columns are the latest week only, by cost.
4. **No countdown framing.** `§D12`: the reference bar moves 1.68x as much as spot, so most
   of the variation in distance-to-trigger is last year's bars rolling off.
5. **A markets-with-no-trigger list, visible.** 37 of 47 have a forced-sell level. Dropping
   the other 10 silently reads as "no risk", which is `§C26` at a new grain.
6. **The reader never raises.** `use_pages=True` imports every page module at startup, so an
   exception on the artifact path takes down the page registry rather than the page.

---

## Outcome, appended 2026-08-04

§1-§3 shipped. **Every measurement in this handoff held**, and the build reproduces `§D9`'s
trigger counts exactly (37 forced-sell, 35 forced-buy on 2026-07-28).

**One finding the work produced that nobody was looking for**, filed as
[`../design/amendments-2026-08-04.md`](../design/amendments-2026-08-04.md) §D13, reproducer
`tests/test_publish_live.py::test_the_pool_check_removes_half_of_d9s_close_and_severe_cell`:
composing `§D9`'s quadrant with `§D10`'s pool check **removes half the CLOSE-and-SEVERE
cell**, and it removes the two markets that most needed removing.

**All four flagged decisions were taken as flagged.** The prohibitions held: nothing
aggregates `D`, `READING_INSTRUCTIONS` is unchanged, and `core/store.py` is still absent.

**§4 remains open.** Its gate is measured and passes; nobody has claimed it.

**Status: §1-§3 closed. §4 open.**

---

## Outcome, appended 2026-08-04 (second): §4 is WITHDRAWN

**Not deferred, not blocked. Not wanted.** The requester, asked directly whether to build
it: *"i don't think the asset class rollup is necessary. if i said that i meant assets."*

**The requirement was per-MARKET all along.** The original ask was to visualise the output
"per asset class", and that phrase was a wording slip for "per asset". The delivered page
already does the right thing: one row per market, **grouped** by asset class for layout, and
grouping a published value by a published key is presentation rather than a metric. No
class-level number was ever wanted.

### The lesson, which is about gates and not about rollups

§4's gate passed. Median scored markets per asset class measured **4.5** against a
pre-registered bar of 3, so the work was cleared to proceed, and it sat here as an open
invitation with a green light attached.

**A feasibility gate cannot answer a desirability question, and this one was never asked.**
The gate tested whether a class-level statistic *could* be computed honestly given the
cardinality. It could. Nobody tested whether anyone wanted it, and the answer was no. Writing
the gate made the work look more justified than it was, because a passed pre-registration
reads like a decision when it is only a permission.

That is worth carrying beyond this file: **pre-registering a gate is not the same as
establishing a requirement**, and a handoff section that carries a passing gate and no named
consumer is the shape most likely to be built by a session that never asks who asked for it.

### What is deliberately NOT reverted

- **`asset_class` stays on the published panel.** It is a column
  `ContractMaster.annotate` already produced, the page groups by it, and it costs nothing.
  Withdrawing the rollup is not a reason to remove a grouping key.
- **`futures/rollup.py` was never written**, so there is nothing to delete. The name stays
  free, and if a class-level object is ever genuinely wanted, §4's body below still records
  the correct construction (counts within `report.QUADRANT`'s own cells, never a mean of
  `D`) and the `§B2` exposure it inherits. Read it as a design note, not as a work order.

### A trap left in place on purpose

**§4's heading below still reads "OPEN, unclaimed"**, because this directory preserves
handoff bodies verbatim and appends outcomes rather than editing them. A session that skims
to the section heading and stops will read a live work order with a passing gate. The
front-matter `Status` line and the row in [`README.md`](README.md) both say WITHDRAWN, and
they are what a session is supposed to read first.

**Status: CLOSED. §1-§3 shipped, §4 withdrawn.**
