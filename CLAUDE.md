# CLAUDE.md — crowdmon

Guidance for Claude Code working in this repo. Workspace-wide rules are in
`../CLAUDE.md` and the governance they point at (`npf/AGENTS.md`, `crucible/AGENTS.md`);
this file covers what is specific to this package.

> **Renamed from `crowdmon-futures` on 2026-08-01**, directory, remote and package
> together. The old name survives only where it is historically correct: `cotdata`'s design
> docs describe "the crowdmon-futures step-1 build", which is what it was called at the
> time, and `crowdmon_futures_cot_module.md` is a real filename in that repo. Neither is a
> stale reference to fix.

## The thesis, in one sentence

**Damage = crowding x illiquidity x holder fragility** — crowding is a property of the
position, illiquidity of the market, and fragility of the holder, and fragility is the term
that decides who actually gets hurt.

Futures are zero-sum, so "everyone is long" is impossible and net imbalance alone says
almost nothing: every long is somebody's short. What differs between the two sides is who is
holding and whether their exit is discretionary. That is the whole reason this package
exists rather than another positioning index.

**It ships no strategy.** Every output is a statement about tail shape and forced-flow risk,
not about next week's return. Positioning extremes persist for quarters.

## Design docs, and which one wins

| Document | Where |
|---|---|
| [`crowdmon_plain_language_summary.md`](docs/design/crowdmon_plain_language_summary.md) — the argument in prose, **and the authoritative appendix** | here |
| [`crowdmon_futures_cot_module.md`](docs/design/crowdmon_futures_cot_module.md) — the primary spec, §13 build order | here |
| [`amendments-2026-08-01.md`](docs/design/amendments-2026-08-01.md) — where measurement contradicted the above | here |
| `crowdmon_step2_normalisation.md` — layer 2, proposed and measured, **not accepted** | `../cotdata/docs/design/` |
| `cot_vintage.md` — the vintage store this reads | `../cotdata/docs/design/` |

**The appendix of `crowdmon_plain_language_summary.md` (§A.1-A.11) is the authoritative
statement of every formula.** Where a handoff and the appendix disagree, the appendix wins.

It is written in LaTeX, which renders on GitHub and not in every viewer. The source is plain
text either way, so read the file rather than a rendering if the math matters.

**Its worked example is executed, not just read** ([`tests/test_appendix.py`](tests/test_appendix.py)):
§A.2's cocoa figures and §A.5's days-to-liquidate reproduce exactly, so the implementation
is pinned to the specification rather than merely believed to match it. Two places where the
appendix is right about its example and wrong about real data (spreading, and "a single
category dominating is typical") are in amendments §A6.

Precedence: **a measurement beats a doc, the appendix beats a handoff, and a handoff beats
your own judgement about what would be nicer.**

The first two documents were copied in on 2026-08-01 and **`cotdata` still holds its own
copies**. This repo's are canonical; the cotdata ones should become pointers when something
next brings that repo open. Do not edit both.

## Doc lifecycle — four directories, four different rules

| Directory | Lifecycle |
|---|---|
| `docs/design/` | **living.** Amended as measurements land. The current best statement of how the system works |
| `docs/handoffs/` | **append-only.** Dated work orders, status-tracked. Preserved verbatim; append an outcome, never edit the body |
| `docs/analysis/` | **point-in-time.** Computed against a named report week. **Never amended** — a later week gets a new file |
| `docs/adr/` | **immutable once accepted.** Superseded by a new ADR rather than edited |

The distinction that matters most is design versus analysis. A design doc that says
something the data disproved is a bug to fix; an analysis document that says something later
weeks disproved is a correct record of what was true then, and editing it to match the
present erases the evidence that anything changed.

**A handoff without a completion status will be re-executed by a future session.** Closing
one out is what stops the same analysis being run twice with different results.

## Working agreement

- **Measure, do not assume.** Probing the actual files has now overturned six written
  assumptions. Two worth internalising: the Oct-Nov 2025 shutdown left report dates
  completely intact (it broke release dates instead), and Managed Money dominates the Phi
  numerator in only 29% of markets rather than typically.
- **Specs are amendable.** If a measurement contradicts a doc, fix the doc in the same PR
  and say so. Where the doc lives in a sibling checkout, record it in
  `docs/design/amendments-*.md` rather than editing a shared working tree, and say that too.
- **Additive only.** `current/` output stays byte-identical.
- **Every quoted figure carries a reproducer.** `docs/analysis/reproduce.py` regenerates
  every number in the analysis documents; `tests/fixtures/build_fixtures.py` regenerates the
  committed test data.
- **House style: worked numbers over abstract restatement, everywhere.** Carry the numbers
  through each formula in sequence, show the arithmetic rather than only its result, end in
  prose. A formula whose inputs are never printed is one nobody has ever checked.
  `futures.report.format_q_block` exists for exactly this.
- No em dashes in any output, chat or committed prose. The one exception is a handoff body,
  which is preserved as issued.
- Any response reporting results ends with a plain-language recap of the bottom line
  alongside the technical answer, not replacing it.

## The boundaries, and why they are not arbitrary

Enforced by [`tests/test_boundaries.py`](tests/test_boundaries.py), in both directions.

| May import | May not | Why not |
|---|---|---|
| `cotdata`, `marketdata` | `cotmetrics` | a peer consumer of the same store computing a different unitless index. Two disagreeing answers to one question |
| | `npf`, `livebook` | strategy and execution, the layers above |
| | `crucible`, `crucible_stack` | you are the intern, crucible is the judge. A monitor that can render a verdict on its own output has stopped being a monitor |

Neither producer may import this package either. That direction breaks nothing here, so it
would be found last, which is why it is checked from here.

Third-party imports are allowlisted too (`pandas`, `numpy`, `pyarrow` and the two siblings).
Reaching for anything else fails the boundary test on purpose: a new dependency belongs in
`pyproject.toml` as a deliberate choice, not discovered by an import that happened to work.

## Layout

```
src/crowdmon/
  core/                     asset-class agnostic — shared with the equity monitor (spec §12)
    aggregate.py            trailing z-scores and percentiles. No lookahead by construction
    config.py               fragility weights, kappa, tolerances. Configured, never fitted
    report.py               markdown rendering. Knows nothing about categories
  futures/                  COT-specific. Knows about categories, market codes, open interest
    cot_adapter.py          the CotSource seam: refuses lookahead, filters on provenance
    io.py                   canonical panels + the OI identity as a reported rate
    contract_master.py      market code to multiplier, never an inner join
    notional.py             rung 3, contracts to USD. Refuses anything but unadj
    riskunits.py            rung 4, notional x sigma. Refuses anything but propadj
    flow.py                 A.3 flow decomposition
    fragility.py            A.2 Q_sell / Q_buy / Phi
    breadth.py              §6.2 breadth-depth quadrant
    extremity.py            §6.1 / A.4 vol-scaled positioning vs 3y of own history
    volume.py               A.5 denominator. `front` is whole-market, `reconstructed` is not
    composite.py            A.9 D = C x I x Phi. The whole system in one number
    volume.py               whole-market ADV + A.5 stress V. Refuses anything but "front"
    pressure.py             A.5 exit capacity. T = Q/(kappa V) is a real duration now
```

`riskunits.py` sits **here beside `notional.py`, not in `core/`**: it needs `propadj` where
notional needs `unadj`, and that asymmetry is a fact about futures continuous-contract
construction rather than a general one.

**The rule for `core/`: only what is genuinely asset-class agnostic.** When in doubt it goes
in `futures/` and can be promoted later, which is cheap; demoting something after the equity
monitor has grown a dependency on it is not.

`core/aggregate.py` arrived with extremity: it is the first thing in `core/` to earn its
place rather than be assumed into it, and it is genuinely agnostic (it knows nothing about
markets or categories).

`core/store.py` and `core/impact.py` are still **absent rather than stubbed**. Nothing needs
them yet and an empty module invites being imported. The first wants history the vintage
store does not have; the second wants a volume source that does not exist here.

One knowing exception to the agnostic rule: the fragility weights in `core/config.py` are
keyed by Disaggregated and TFF category names. The handoff places them there, and the
*shape* is what the equity monitor will need too, with 13F holder types. If that lands, this
file grows a second table or the weights split per asset class.

## Things that will bite you

- **Two stores, different shapes.** The vintage store holds 346 markets but only from
  2025-01-07; the current-state parquets hold 27 markets back to 2006. Breadth and depth are
  in different places. `futures.from_vintage` and `futures.from_current_store` are separately
  named for this reason — do not add a flag that hides which one you got.
- **Nothing is point-in-time before 2026-07-31.** Vintages accumulate forward only, so any
  earlier week is a current value with revisions applied. Fine for descriptive work and for
  flow decomposition (a first difference on revised values is the *better* input). Not fine
  for evaluating a rule, which must go through `VintageCotSource.load` and filter on
  `pit_complete`.
- **`open_interest` is the market total repeated on every category row.** Summing it across
  categories multiplies it by five and silently divides every ratio in the system.
- **`Q_sell` and `Q_buy` must never be added.** Forced longs sell and forced shorts buy;
  their sum describes an event that cannot happen. `q_gross` exists and is named so it
  cannot be mistaken for a flow.
- **Phi uses gross over `2·OI`, never nets over OI.** Nets sum to zero across categories and
  cannot form a share. The wrong form is unbounded; the bound is asserted on every
  computation precisely to stop a regression to it.
- **Trader counts are suppressed routinely**, not exceptionally — 44% of Managed Money long
  counts in the latest week, and non-reportables have none by definition. Null is a real
  state. Never impute one: it feeds straight into the average position per trader.
- **Editable installs mean the installed package is the working tree.** A `git checkout` in
  `../cotdata` changes this package's behaviour with no change here, and other sessions share
  those checkouts.

## Layer 2 trap, now coded and guarded

The two factors of `net_notional × σ` come from **three different price series**, and each
module refuses the others. All three refusals are measured, not asserted, and each is a
`raise` rather than a warning because each error is invisible to the check a reasonable
person would actually run.

| Module | Wants | Refuses, and why it slips past a spot check |
|---|---|---|
| `notional` | `unadj` | `backadj` notional is wrong by +294% (gold 2002), +257% (crude 2004), and **exactly 0% today**, growing monotonically backwards |
| `riskunits` | `propadj` | `backadj` percent vol is 201x too high for ZS, 182x for ZN, and **0.47x for gold**, which never goes negative and passes every implausibility screen |
| `riskunits` | `propadj` | `unadj` full-sample vol looks fine (GC 1.01x) while a 63-day window spanning a roll is up to 9.84x off; crude's worst roll day is a fabricated 130.7% move |

`test_notional_live.py` and `test_riskunits_live.py` pin every one of those numbers against
the real store, and `docs/analysis/reproduce.py` prints them. If cotdata's adjustment logic
changes, they fail and the docstrings get corrected rather than quietly becoming folklore.

**An earlier version of this file said volatility wanted `backadj`. That was wrong.**
Additive back-adjustment preserves absolute price CHANGES, not percentage returns. Module
spec §5.1 had it right ("ratio-adjusted (not difference-adjusted) so returns are correct").
See `docs/design/amendments-2026-08-01.md` A8.

A negative price is **not** by itself a sign of the wrong series, in any of the three
adjustments. WTI settled at -37.63 on 2020-04-20; `unadj` records it faithfully and `propadj`
carries it through at -24.11, because ratio adjustment scales by a positive factor and so
preserves the underlying sign. Only the **rate** distinguishes an event from an artifact:
across all 47 symbols `propadj` has exactly one non-positive close (0.009% of crude) against
`backadj`'s 52.3% for soybeans. Nothing clips or rejects a negative price, `riskunits` masks
only the returns touching one, and anything downstream assuming `sign(notional) ==
sign(position)` is wrong on real data. See amendment A9: this assumption has now been made
and corrected three times in this codebase's short history.

## Commands

```bash
uv venv --python 3.11 && uv pip install -e ".[dev]" -e ../cotdata -e ../marketdata
```

Tests run fully offline against committed fixtures, but `cotdata` guards on the store env
var at import, so it must be set even when unused:

```bash
COTDATA_STORE=/tmp/crowdmon_test .venv/bin/python -m pytest tests/ -q -rs
```

```bash
.venv/bin/python -m ruff check src tests
```

Regenerate the analysis figures (needs the real store):

```bash
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce.py
```
