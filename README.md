# crowdmon

A crowding and forced-exit monitor.

**Damage = crowding x illiquidity x holder fragility.** Crowding is a property of the
position, illiquidity of the market, and fragility of the holder, and fragility is the term
that decides who actually gets hurt. Two holders can carry the same position in the same
market and behave completely differently under stress, because one of them has an exit
function written into its mandate and the other does not.

Futures first (`crowdmon.futures`), because COT resolves the four structural weaknesses of
the 13F approach: the short book is reported rather than invisible, the lag is three days
rather than forty-five, open interest is known exactly rather than estimated against an
estimated float, and trader counts and concentration ratios are published. It also models
the systematic flow response function — given a price or volatility move, how many contracts
must trend-following and vol-targeting capital mechanically transact, and what does that
cost in impact terms. The equity monitor is the follow-on, and `crowdmon.core` is what the
two share.

**It ships no strategy.** Every output is a statement about tail shape and forced-flow
risk, not about next week's return. Positioning extremes persist for quarters.

> **Renamed from `crowdmon-futures` on 2026-08-01.** The old name was wrong in a way that
> would have got worse: it named the first asset class as though it were the system. The
> monitor is `crowdmon`, and futures is where it starts.

## Layout

```
src/crowdmon/
  core/          asset-class agnostic: config, rendering. Shared with the equity monitor
  futures/       COT-specific: ingestion, contract master, positioning engines
```

`core/store.py` and `core/aggregate.py` are absent rather than stubbed: both want history the
vintage store does not yet have. `core/impact.py` holds the square-root law and Amihud, which
are true of any market with a price, a volatility and a volume.

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

**Layer 1, the full normalisation ladder, and the two price-free engines.**
`VintageCotSource` is the `CotSource` seam over `cotdata`'s vintage store; `ContractMaster`
is the market-code to multiplier join; `add_notional` is contracts to USD; `add_risk_units`
is notional scaled by volatility, which module spec §5.2 makes the default unit for any
cross-market comparison. Flow decomposition and fragility-weighted exit size run alongside,
and need no prices, no multiplier and no normalisation. Every input is a column the canonical
schema already carries, which is what makes them the right first consumers of it.

The two normalisation modules each **refuse** every price series but their own, rather than
documenting the requirement: notional wants `unadj` (tradeable levels), risk units want
`propadj` (percentage returns). Both errors are invisible on a spot check, since notional's
is exactly zero at the present date and back-adjusted volatility understates gold by half
without ever producing an implausible number, so both are a `raise`, with the measured
figures in the docstring and pinned by a live test.

**Exit capacity is a real duration now.** `T = Q / (κ·V)` was blocked on a volume source that
turned out to have been in the store the whole time, under a `cotdata` parameter named
`front` that reads like front-month and is whole-market. `futures/volume.py` supplies both a
calm trailing ADV and §A.5's stress-conditioned `V_stress`, neither of them a spot reading, so
the volume-spike trap is closed by construction. It is not cosmetic: `T` and the old `Q/OI`
proxy rank markets at 0.585 correlation, and Class III Milk sits 19th on one and 2nd on the
other.

**Exit cost is separate from exit duration, and they barely rank together.** `T` says how long
the forced side takes to leave; §A.5's `I = Y·σ·√(Q/V)` says what leaving costs. Because the
cost carries volatility and the duration does not, the two rank markets at **0.031**
correlation on the latest panel: cotton has the longest `T` and the fourth-highest cost, cocoa
exits in a day and a half and costs the third most. Both are reported, and neither is the
composite's `I` term, which §A.9 defines as `pct(T_eff)`.

**Liquidity commonality is measured, and it does not reach the composite.** §A.6 asks whether
exits go through the same door, and the answer splits the universe cleanly: livestock and milk
sit at β 0.07-0.11, grains and energy at 0.95-1.02. But two findings mean §A.6 cannot feed
§A.9 as both sections are written. Including a market in its own basket makes β̄ identically 1
**by algebra**, for any data at all; and even a correct constant β̄ leaves `pct(T_eff)`
bit-identical to `pct(T)`, because a percentile ignores a scalar multiple. `t_effective` is
offered and deliberately not wired into `D`. See
[amendments-2026-08-02.md](docs/design/amendments-2026-08-02.md).

**The cascade has no single `g`, and asking which horizon to use was the wrong question.**
§A.8 amplifies an initial liquidation by `1/(1 - λ·g)`, where `g` is the pool forced per unit
price move. Both obvious readings divide the whole observed net by one horizon's trigger
distance, which assumes every holder runs that horizon and moves gold's `λ·g` from 0.06 to 0.4
depending which you pick. `futures/reflexivity.py` makes `g` a **signed staircase** over price
distance instead, so the two readings become the bracket rather than rivals.

`g_up` and `g_down` are separate and are never summed: 23 of 33 markets have horizons pointing
different ways at once, so at gold a rally forces the short slice to cover while a selloff
forces the long slice to liquidate. Two cascades, opposite directions, different distances.
Netting them would report a market with two live cascades as quieter than one with none.

Two things about it are worth knowing before reading a number. Cohort sizes are unknown but
**constrained**, because they must reproduce the observed net, which makes the implied gross
pool 3x the net wherever the horizons disagree and equal to it where they do not. And the
worst step is a **race** rather than always the nearest one: `λ·g ~ √Q/d`, so a nearer step
wins only when the next trigger is more than 41% further out, and 6 of 33 multi-step
staircases peak past their nearest. The headline is the max over steps, not the first.

Next: **§10 validation, which by design does not happen here.** Every engine in the package
was written by the two sessions active on 2026-08-01 and 08-02, and `tests/test_boundaries.py`
refuses an import of `crucible` precisely so a verdict cannot be rendered on this package's own
output. The tests are pre-registered in
[docs/handoffs/2026-08-02-validation-prereg.md](docs/handoffs/2026-08-02-validation-prereg.md),
which declares what has already been looked at and what is still clean, and is frozen awaiting
a session that has written none of this.

```python
from crowdmon.futures import decompose, fragility_frame, latest, top_by

panel = latest()                          # every market in the newest report week
frag = fragility_frame(panel)             # Q_sell, Q_buy, Phi, and the OI-denominated ratios
top_by(frag, "q_sell_over_oi", n=10)      # where forced longs are largest
top_by(frag, "q_buy_over_oi", n=10)       # and where forced shorts are
decompose(panel_history)                  # new longs / short covering / new shorts / ...
```

Three refusals worth knowing before reading any output:

- **`Q_sell` and `Q_buy` never combine.** Forced longs sell and forced shorts buy, so their
  sum describes an event that cannot occur. The asymmetry between them is the informative
  number: it is what separates a market whose longs can be forced out from one whose shorts
  can be squeezed.
- **`Phi` is gross over `2·OI`, and the bound is asserted.** Nets sum to zero across
  categories and cannot form a share of anything. The wrong form (`Σ w|P|/OI`) is unbounded,
  so `0 ≤ Phi ≤ 1` is checked on every computation rather than only in tests.
- **No volume is invented.** `T = Q/(κV)` is the real output and there is no per-contract
  volume source in this workspace, so `days_to_liquidate` is `None` and `volume` is an
  optional argument that slots in later. `Q/OI` ranks markets; it does not measure a
  duration.

### Reading `D` on live output

Four things, and none of them is discoverable from the number itself. They were measured
separately and are gathered here because together they are the reading instructions.

**1. `D` falls during an unwind, and that is correct.** It describes a pre-condition, and both
the position and the forceable holders it describes leave while the event happens. Across
March 2020, mean `D_sell` ran 0.76x baseline in the four months before, **0.45x during**, and
0.68x after. A rising `D` is a market loading up; a falling `D` is not a market getting safer,
it may be a market mid-exit. (`2026-08-01 §A17`)

**2. `Phi` has no signal independent of the weight table.** Set every weight to 1.0 and it
reduces exactly to `1 - spreading/OI`, verified to 1.11e-16 on 27,194 market-weeks. `Phi` is
not a measurement the weights adjust; it is a weighted restatement of the category mix. Read a
fragility number as a statement about the configured judgement, not about positioning.
(`2026-08-01 §A21`)

**3. The rankings survive the weights being wrong, but not being reordered.** Across 200
plausible order-preserving weightings the `Q_sell/OI` top-10 keeps at least 7 of 10; inverting
the §6.3 ordering destroys it entirely (0 of 10, rank correlation −0.045). And the
load-bearing weight is Producer/Merchant at 0.1, because it holds 56% of gross open interest,
which makes `Q_buy/OI` the less stable of the two published rankings. (`2026-08-01 §A22`)

**4. `D` assumes exits are independent across markets, and they are not.** `I` is `pct(T)`
rather than `pct(T_eff)` deliberately: with a constant `beta_bar` the two are bit-identical,
because a percentile ignores a positive scalar multiple. So §A.6's commonality **cannot** enter
`D` through the formula §A.9 gives, and the measured spread is large enough to matter — milk
and hogs near 0.07 (their own door) against the wheats above 1.0 (the same door as everyone).
**Read `commonality_betas` beside `D`, not inside it.** A high `D` in a market with
`beta` near 1.0 is worse than the same `D` at 0.07, and nothing in the composite says so.
(`2026-08-02 §B2`)

### First results

[`docs/analysis/`](docs/analysis/) holds the first run over real data, ranked rather than
hand-picked, each figure reproduced by `docs/analysis/reproduce.py`. The headline structural
finding: the design doc's worked example (levered long, producer-hedged short) describes
**about half** the Disaggregated universe. Producer/Merchant is net long in 141 of 279
markets, so the two markets the ranking selected are structural opposites.

```python
from crowdmon.futures import VintageCotSource, provenance_summary

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
from crowdmon.futures import ContractMaster

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

Here, in [`docs/design/`](docs/design/):

- [crowdmon_plain_language_summary.md](docs/design/crowdmon_plain_language_summary.md) —
  the argument in prose, with a mathematical appendix (§A.1-A.11). **The appendix is the
  authoritative statement of every formula in this package**; where anything else disagrees
  with it, it wins. Written in LaTeX, which renders on GitHub and not in every viewer, so
  read the source if the math matters.
- [crowdmon_futures_cot_module.md](docs/design/crowdmon_futures_cot_module.md) — the full
  system description and the §13 build order.
- [amendments-2026-08-01.md](docs/design/amendments-2026-08-01.md) — what measurement
  contradicted in both of the above. Read it alongside them, not after.

Still in `cotdata`, because they are about that repo's own subsystems:

- [crowdmon_step2_normalisation.md](https://github.com/mspinola/cotdata/blob/main/docs/design/crowdmon_step2_normalisation.md)
  (contract master and normalisation, proposed and measured, **not accepted**)
- [cot_vintage.md](https://github.com/mspinola/cotdata/blob/main/docs/design/cot_vintage.md)
  (the vintage store this package reads)

**The appendix's worked example is executed as a test**, in
[tests/test_appendix.py](tests/test_appendix.py), rather than only read. §A.2's cocoa
figures (`Q_sell = 99,500`, `Q_buy = 11,000`, `Phi = 0.44`) and §A.5's ~20-day
days-to-liquidate all reproduce exactly, so the implementation is pinned to the
specification instead of assumed to match it. An authoritative document whose worked example
nobody runs is a document nobody has checked.

## Docs, and four different lifecycles

| Directory | Lifecycle |
|---|---|
| [`docs/design/`](docs/design/) | **living.** Amended as measurements land |
| [`docs/handoffs/`](docs/handoffs/) | **append-only.** Dated work orders, status-tracked. A handoff without a completion status gets re-executed |
| [`docs/analysis/`](docs/analysis/) | **point-in-time.** Computed against a named report week, never amended |
| [`docs/adr/`](docs/adr/) | **immutable once accepted.** Superseded, not edited |

A design doc that says something the data disproved is a bug to fix. An analysis document
that says something later weeks disproved is a correct record of what was true then.

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
