# CLAUDE.md — crowdmon

Guidance for Claude Code working in this repo. Workspace-wide rules are in
`../CLAUDE.md` and the governance they point at (`npf/AGENTS.md`, `crucible/AGENTS.md`);
this file covers what is specific to this package.

> **The repo directory and GitHub remote are still named `crowdmon-futures`.** The Python
> package, `pyproject.toml` and CI are `crowdmon`. The directory rename touches the
> workspace `CLAUDE.md` sibling table and the remote, so it is a deliberate step that has
> not been taken. Do not be surprised by the mismatch, and do not "fix" it in passing.

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
| `crowdmon_futures_cot_module.md` — the primary spec, §13 build order | `../cotdata/docs/design/` |
| `crowdmon_step2_normalisation.md` — layer 2, proposed and measured, **not accepted** | `../cotdata/docs/design/` |
| `cot_vintage.md` — the vintage store this reads | `../cotdata/docs/design/` |
| [`docs/design/amendments-2026-08-01.md`](docs/design/amendments-2026-08-01.md) — where measurement contradicted the above | here |

**The appendix of `crowdmon_plain_language_summary.md` (§A.1-A.11) is the authoritative
statement of every formula.** Where a handoff and the appendix disagree, the appendix wins.

**That document does not currently exist anywhere in the workspace.** If you find it, the
Phi definition and the cocoa-template comparison in `docs/analysis/` should be re-checked
against it (amendments §A6). Until then the implemented formulas are the ones in the
2026-08-01 handoff, and the one that could have gone wrong is asserted rather than trusted.

Precedence: **a measurement beats a doc, the appendix beats a handoff, and a handoff beats
your own judgement about what would be nicer.**

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
    config.py               fragility weights, kappa, tolerances. Configured, never fitted
    report.py               markdown rendering. Knows nothing about categories
  futures/                  COT-specific. Knows about categories, market codes, open interest
    cot_adapter.py          the CotSource seam: refuses lookahead, filters on provenance
    io.py                   canonical panels + the OI identity as a reported rate
    contract_master.py      market code to multiplier, never an inner join
    notional.py             rung 3, contracts to USD. Refuses back-adjusted prices
    flow.py                 A.3 flow decomposition
    fragility.py            A.2 Q_sell / Q_buy / Phi
    breadth.py              §6.2 breadth-depth quadrant
    pressure.py             A.5 exit capacity, days-to-liquidate pending a volume source
```

`riskunits.py` (rung 4, vol-scaled notional) belongs **here beside `notional.py`, not in
`core/`**: it needs `backadj` where notional needs `unadj`, and that asymmetry is a fact
about futures continuous-contract construction rather than a general one.

**The rule for `core/`: only what is genuinely asset-class agnostic.** When in doubt it goes
in `futures/` and can be promoted later, which is cheap; demoting something after the equity
monitor has grown a dependency on it is not.

`core/store.py`, `core/aggregate.py` and `core/impact.py` are **absent rather than stubbed**.
Nothing needs them yet and an empty module invites being imported. The first two want history
the vintage store does not have; the third wants a volume source that does not exist here.

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

Notional must come from **unadjusted** prices and volatility from **back-adjusted** returns,
so the two factors of `net_notional × σ` come from different series on purpose. Off
back-adjusted, notional is wrong by +294% (gold 2002) and +257% (crude 2004), and crude's
back-adjusted series reads -27.52 on a day the market traded at +11.57. The error is
**exactly zero at the present date** and grows monotonically backwards, so it passes every
spot check anyone would run while corrupting the whole evaluation history.

`notional.add_notional` **raises rather than warns** on any adjustment but `unadj`. Keep
that guard hard and keep the measured numbers in its docstring: they are what makes it a
guard rather than a comment, and a future reader who only sees recent data will find nothing
wrong. `test_notional_live.py` pins them against the real store.

A negative price is **not** by itself a sign of the wrong series. WTI settled at -37.63 on
2020-04-20 and `unadj` records it faithfully, so a long position genuinely had negative
notional that day. Nothing clips or rejects one, and anything downstream assuming
`sign(notional) == sign(position)` is wrong on real data.

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
