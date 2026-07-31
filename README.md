# crowdmon-futures

A COT positioning and forced-flow monitor for futures markets. Measures crowding and
forced-exit risk, and models the systematic flow response function: given a price or
volatility move, how many contracts must trend-following and vol-targeting capital
mechanically transact, and what does that cost in impact terms.

**It ships no strategy.** Every output is a statement about tail shape and forced-flow
risk, not about next week's return. Positioning extremes persist for quarters.

## Why this is a separate package

`cotdata` holds CFTC positioning. `marketdata` holds bars. crucible-stack
[ADR-0007](https://github.com/mspinola/crucible-stack/blob/main/docs/adr/ADR-0007-cotdata-is-cot-only-bars-live-in-marketdata.md)
split them precisely because almost nothing joined the two domains, which is what made the
split cheap.

Normalisation is, by definition, a joiner: net contracts times a multiplier times a price,
scaled by a volatility estimated from returns. Putting it in `cotdata` would drag bars back
in at the moment ADR-0007 is pushing them out; putting it in `marketdata` would drag COT in,
and `marketdata` deliberately imports nothing from `cotdata`. The only home that does not
violate the seam is the consumer, which is this package.

That seam is enforced, not merely described: [`tests/test_boundaries.py`](tests/test_boundaries.py)
fails if this package imports a strategy repo, a peer consumer, or the judge, and also if
either producer imports this package.

| May import | May not import | Why not |
|---|---|---|
| `cotdata`, `marketdata` | `cotmetrics` | a peer consumer of the same store, computing a different unitless index. Two disagreeing answers to one question |
| | `npf`, `livebook` | strategy and execution, the layers above |
| | `crucible`, `crucible_stack` | you are the intern, crucible is the judge. A monitor that can render a verdict on its own output has stopped being a monitor |

## Status

**Layer 1, plus the contract master.** `VintageCotSource` is the `CotSource` seam over
`cotdata`'s vintage store; `ContractMaster` is the market-code to multiplier join. Notional
and vol-scaled risk units are next; see the proposal linked below.

```python
from crowdmon_futures.ingest import VintageCotSource, provenance_summary

src = VintageCotSource(report_type="disaggregated", min_source="scheduled")
panel = src.load("2026-07-24")          # the panel as it was knowable that day
print(provenance_summary(panel))        # and where each release date came from
```

Three things the adapter owns, none of which the store can do on its own:

- **It refuses lookahead.** Indexed on release date, never on the Tuesday report date.
  Using the report date embeds a three-day lookahead, and three days is exactly the window
  in which the largest moves happen, so it flatters every historical result in the wrong
  direction.
- **Provenance is a filter, not a footnote.** Release dates carry a source in
  `published > observed > announced > scheduled > derived`. `derived` is a guess that fails
  on precisely the weeks that matter: holiday shifts and publication backlogs. A release
  date without provenance is worse than none.
- **It validates on every load**, including the zero-sum identity (long total equals short
  total across categories, since every long is somebody's short). `cotdata` measured that
  at 149,412 of 149,412 weeks over 40 years, so a break means the category mapping moved.

### The contract master

```python
from crowdmon_futures.normalize import ContractMaster

cm = ContractMaster.load()
print(cm.coverage_summary())      # 47 of 49 registry symbols joinable, over 49 codes
panel = cm.annotate(panel)        # adds symbol, point_value, currency, contract_scale
print(cm.unmatched(panel))        # and says what has no spec, rather than dropping it
```

Three things it refuses to do quietly:

- **It never inner-joins.** The vintage store holds every market CFTC publishes (418 codes
  in the 2026 capture) while the registry names 49. Measured on the real store, **371 codes
  and about 87% of rows have no spec**: Nodal Exchange power zones, minor grains, and
  everything else nobody here trades. An inner join would discard all of it in silence and
  a "cross-market" result would then describe the 13% that survived. `annotate` adds
  columns and leaves them null; `drop_unmatched=True` is an explicit opt-in.
- **It applies the contract-size scale.** CFTC retires and reissues codes, and some
  predecessors carry a size change: lumber's `058643` is 4.0, because the contract was
  redefined. Using today's point value on an old row without it is wrong by 4x and looks
  fine. `cotdata.get_cot` handles this when stitching history, but the vintage path does
  not, so this layer must. Applied **by default**, so forgetting the argument gives the
  correct answer. Latent today (the 2026 capture holds no retired codes) and live the
  moment anyone backfills earlier years.
- **It checks currency rather than assuming it.** All 47 specs are USD, which removes an FX
  layer. That is a fact about the current universe, not a property of futures, so a non-USD
  contract raises instead of producing a USD-labelled number that is not USD.

### The point-in-time asymmetry, stated up front

Vintages accumulate forward only. CFTC serves current state with no archive, so the vintage
series begins at first capture (2026-07-31). For any earlier week the stored value is the
current one with revisions already applied. Both are returned and **`pit_complete` marks
which each row is**; anything evaluating a rule must filter on it rather than assume.

The price side has the same problem and no fix yet: Norgate back-adjusted series restate
history on every roll, and `marketdata` captures no vintages.

## Design docs

The system description and the step-2 proposal currently live in `cotdata`, because they
were written before this package existed. They belong here and should migrate once the
cross-repo links they are referenced by have settled:

- [crowdmon_futures_cot_module.md](https://github.com/mspinola/cotdata/blob/main/docs/design/crowdmon_futures_cot_module.md)
  (the full system description, and the build order)
- [crowdmon_step2_normalisation.md](https://github.com/mspinola/cotdata/blob/main/docs/design/crowdmon_step2_normalisation.md)
  (contract master and normalisation, proposed and measured, not yet built)
- [cot_vintage.md](https://github.com/mspinola/cotdata/blob/main/docs/design/cot_vintage.md)
  (the vintage store this package reads)

## Development

Sibling checkouts are load-bearing: `cotdata` and `marketdata` are installed editable from
`../`, so the installed package *is* the working tree and a `git checkout` in either one
changes this package's behaviour with no change here.

```bash
uv venv --python 3.11
uv pip install -e ".[dev]" -e ../cotdata -e ../marketdata
COTDATA_STORE=/tmp/crowdmon_test .venv/bin/python -m pytest tests/ -q
.venv/bin/python -m ruff check src tests
```
