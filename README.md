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

`core/store.py` is absent rather than stubbed: it wants history the vintage store does not yet
have, and an empty module invites being imported. `core/aggregate.py` **arrived with
extremity** and holds the trailing z-scores and percentiles; it is the first thing in `core/`
to earn its place rather than be assumed into it. `core/impact.py` holds the square-root law
and Amihud, which are true of any market with a price, a volatility and a volume.

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

**The positioning engine is the first useful output and needs none of the modelling.**
`extremity` standardises a market's positioning against its own trailing history,
`concentration` reads the CFTC's own CR4/CR8 net shares, and `breadth` splits a change in
position into how much came from more traders against bigger traders. Spec §13 calls this the
step that earns its keep before any model, and it does: none of it consumes a price, a
multiplier or a volatility. `seasonal` sits beside them for the ag markets whose positioning
has a calendar, and `weight_sensitivity` exists because every fragility weight is judgement
and a result that does not survive them moving is a result about `core/config.py`.

**The composite is built, and it is the number the package exists to produce.**
`add_composite` is §A.9's `D = C × I × Φ`, multiplicative so that a near-zero term carries the
whole score toward zero, which is the thesis: a large position in a liquid market held by
unconstrained hedgers is safe. Two readings of the formula had to be settled by measurement
rather than by reading it again, and both are recorded in `docs/design/`. `Φ` enters as a
percentile, following §A.9's preamble over its own formula, because the literal version
correlates with `D` at **0.145** against 0.857 for `I`, so the term the package is named for
almost disappeared.

Two limits belong next to it rather than in a footnote. **`D` scores nothing before
2010-05-25**, because `C = pct(z)` stacks two three-year windows, which puts the 2008 crisis
permanently out of reach on this panel. And **`D` carries no first-moment content and must
never be traded**: §A.10 is explicit that it estimates the shape of a conditional loss
distribution and not its location. `tests/test_boundaries.py` is what stops that eroding by
drift rather than by decision.

**The floor is not one date. It is a property of which quantity you read, and the number
§A.10 tells you to report has a later one.** `damage_sell_pct` is `pct(D)`, which stacks a
**third** rolling window on the two above, so it scores nothing before **2012-05-15**:
`2010-05-25` plus 103 weekly observations, the 104th being `min_periods`. Measured on both
report types, and identical on each.

| you read | first scored week | warm-up from the 2006-06-13 panel start |
|---|---|---|
| `damage_sell` / `damage_buy`, the raw product | 2010-05-25 | 3.9 years |
| **`damage_sell_pct` / `damage_buy_pct`**, what §A.10 says to report | **2012-05-15** | **5.9 years** |

Two further years go to the percentile, and they go to the reading this package recommends,
so anyone planning coverage from the 2010 figure over-counts by two years for the most likely
use. Found by the §10 evaluator counting units rather than by any output the package emits
(`docs/design/amendments-2026-08-02.md` §B17); `futures/coverage.py` is the report that now
answers "scoreable after every window is stacked" directly, per market.

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

**The forced-seller model needed no estimate of CTA capital, which is why it exists.** §A.7
models systematic position size as `q = s(F) · (σ_target/σ) · λ(Σ) · A`, and `A` is aggregate
systematic capital calibrated against SG Trend or BTOP50. Neither index is in this workspace,
so the whole section sat recorded as blocked. Three of those four terms are positive scalars,
and a positive scalar moves neither where a signal crosses zero nor a proportional response.
**The replication model exists to estimate other people's positions, and COT reports them
weekly**, so `futures/trigger.py` uses the observed Managed Money net instead and reports, per
market and horizon, the price at which the trend flips and how much is forced when it does.

That was the **fourth** blocked-on row in the spec to prove stale, after volume, extremity and
§A.10's returns, and three of the four were re-testable in under an hour. A blocker recorded
once is rarely re-tested, which has now cost this project more time than any defect in the
code. What is genuinely still absent is spec §9.2's first calibration target, a regression of
modelled returns on SG Trend, declared rather than approximated.

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

**Step 5's cross-market engine is built, all three parts.** §13 step 5 asks for panel, **PCA**
and **trend alignment**: the panel is `futures/commonality.py`, the PCA is
`futures/macro_pca.py`, and trend alignment is `futures/alignment.py`.
`futures/clustering.py` (spec §369) sits beside them, clustering markets by return correlation
rather than by sector label. Two findings worth carrying before reading any of their output:
**PC1 is the subject, not a parameter** (it is the grain complex on Disaggregated and the
macro book on TFF, §B21), and **the alignment score cannot reach 1**, its ceiling averaging
0.931 and moving enough that the raw figure is not comparable across weeks (§B20).

> **What is left to build is not listed here.**
> [`docs/handoffs/README.md`](docs/handoffs/README.md) is the status table and is the only
> place that tracks it. An earlier version of this section named three modules as unbuilt that
> had already shipped, and a version before that named A.7 as "the last large unbuilt piece"
> after A.7 shipped, which got the trigger module built twice in one afternoon. A hand-kept
> "what's next" list in a README is how that happens.

**Step 4 is two constraints, not one, and both are blocked on data.**

| §13 step 4 item | state |
|---|---|
| **limit moves** | **blocked on data.** No daily price limit table exists in `cotdata` or `marketdata`, and spec §3 says the source is "manually maintained" by nothing |
| **roll congestion** | **blocked on data, in full.** §379's three components are calendar spread volatility, bid-ask behaviour and OI migration front to next: the first two need a per-expiry price source and quotes, neither of which exists, and the third is blocked too (§B19) |

**The third one is the trap, and it was recorded here as "not blocked" for a day.**
`cotdata.get_prices` returns an `Open Interest` column that reads exactly like the front-month
figure a migration rate needs. It is not: measured against COT's whole-market total over 1,051
weeks per market, the mean ratio is **1.000** for GC, SI, CL, ZC, NG, ZS, ZW and HG. It is the
same number COT already reports. Two columns on one frame both look per-contract and neither
is, `volume.py`'s `front` being the other.

What shipped instead is `futures/roll.py`: roll-window volume and its effect on `pressure.T`,
which is **5.1% median across 16 markets and wrong-signed for five of them**. That is roll
*timing*, which is available, rather than roll *congestion*, which is not. Conflating the two
is what produced the earlier claim.

Step 7's report layer is buildable but is the last item, after validation, in the spec's own
ordering. `futures/report.py` is the COT-specific half of it; `futures/continuity.py` sits
under it, because a market code is not an instrument and a migrated code otherwise reads as
two markets that each die halfway.

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
- **No volume is invented, and none has to be.** `T = Q/(κV)` is the real output and
  `futures/volume.py` supplies the denominator, so `days_to_liquidate` is a real duration on
  25 of the 279 markets on the latest Disaggregated panel. The other 254 are codes with no
  contract spec, not markets with no volume. It is still `None` without a volume argument,
  and it stays `None` rather than being estimated: `Q/OI` ranks markets and does not measure
  a duration, and the two rank at 0.585. What is genuinely absent is a **per-contract**
  volume, which `T` never needed.

### Reading `D` on live output

**Four numbered instructions over five findings, and the denominator is the five.** None of
them is discoverable from the number itself. They were measured separately and are gathered
here because together they are the reading instructions. The third carries a qualifier
(`3b`) that arrived later and narrows it rather than adding a fifth *instruction*; it cites a
finding of its own, so the ledger the brief prints is over five. This section said "four" at
the top and "five" at the bottom for a day, both defensible and together a contradiction a
reader meets before reaching either number (`2026-08-03 §C30`).

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

**3b. That robustness is a statement about pooled rankings, and it does not transfer to a
level on a subpopulation.** Sweeping Swap Dealer alone over `w_SD ∈ {0.2, 0.4, 0.7}` moves the
median `Q_sell/Q_buy` by **0.6% across all 21,756 vintage market-weeks** and by **42.0% across
the 13 Supplemental agricultural markets**, monotonically. Pooled over a universe that is
three-quarters power and gas basis, one weight is a rounding error; on a named subset of
outrights it is load-bearing. So "the weights are robust" is true of the published rankings and
is not a licence to read any weight as safe for any question. **The population is part of the
sensitivity result, not context around it.** (`2026-08-03 §C3`)

**4. `D` assumes exits are independent across markets, and they are not.** `I` is `pct(T)`
rather than `pct(T_eff)` deliberately: with a constant `beta_bar` the two are bit-identical,
because a percentile ignores a positive scalar multiple. So §A.6's commonality **cannot** enter
`D` through the formula §A.9 gives, and the measured spread is large enough to matter — milk
and hogs near 0.07 (their own door) against the wheats above 1.0 (the same door as everyone).
**Read `commonality_betas` beside `D`, not inside it.** A high `D` in a market with
`beta` near 1.0 is worse than the same `D` at 0.07, and nothing in the composite says so.
(`2026-08-02 §B2`)

**These five are the denominator, and `futures/brief.py` carries three of them.** The list
above is duplicated into `brief.READING_INSTRUCTIONS`, and
[`tests/test_reading_instructions.py`](tests/test_reading_instructions.py) is what keeps the
copy honest: add a sixth instruction here and it fails, because a caveat this section states
and the brief omits is omitted **silently** and the brief still reads as complete
(`2026-08-03 §C30`). The list is prose here and code there, so a market-week can travel with
a ledger over it instead of a reader having to hold this page: `§A17` via `ΔD` beside the
flow state, `§B2` via `add_commonality`, and `§C3` via `stratum.classify`, which turns
`§C8`'s band rule into a value rather than prose beside code that could check it.

**The remaining two are not properties of a market-week at all**, and both were shown so by
measurement rather than left unbuilt: `§A21` is identical on every row, and `§A22` is a
property of a pooled ranking under a weight sweep. The brief **names** them in its own output
rather than omitting them, which is the pre-registered condition it ships under, and its
footer says the assembly is convenience with one genuine gap closed rather than a safety
guarantee.

```python
from crowdmon.futures import (add_score_state, add_unwind_state, classify,
                              coverage_ladder, decompose)
from crowdmon.futures.brief import format_brief, market_brief

scored = classify(add_unwind_state(add_score_state(scored), decompose(panel)))
print(format_brief(market_brief(scored, "057642",
                                ladder=coverage_ladder(per_category, scored))))
```

Only `stratum` and `score_state` come for free; `beta` needs `add_commonality`, which the
composite chain never calls (`2026-08-02 §B2`), so a brief assembled without it declares the
gap rather than passing over it.

`add_score_state` is the one caveat no other output stated (`2026-08-03 §C20`, `§C24`): a
third of market-weeks carry no `D`, for two causes that mean opposite things, and both
rendered as the same blank cell. Detail in `2026-08-03 §C25-§C27`, reproducer
[`docs/analysis/reproduce_brief.py`](docs/analysis/reproduce_brief.py).

### Publishing the panel, for a reader who cannot import this package

`bin/publish_damage.sh` writes the whole panel to `CROWDMON_STORE` (a *different* store from
`COTDATA_STORE`, following npf's `CMRDATA_STORE`): every market-week over both report types,
plus the latest week's `format_damage_block` output pre-rendered, plus a manifest carrying
every vocabulary and every reading instruction generated from the live constants.

```bash
COTDATA_STORE=~/code/cotdata_store CROWDMON_STORE=~/code/crowdmon_store bin/publish_damage.sh
```

It exists because the consumer that wants `D` **cannot import this package**. `cot-analyzer`
serves from a Linux host that runs **Python 3.9** against this package's `>=3.10` floor, and
that host cannot produce the Norgate `unadj` + `propadj` prices the ladder needs however it is
provisioned. Three softer reasons point the same way, and
[ADR-0001](docs/adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md) is the
record. This is the package's first and only writer; `core/store.py` is still absent, because
an artifact is a statement made once a week and forgotten while a store is state this package
would read back.

### Scheduling it on the Windows producer

`bin/publish_damage.sh` and the launchd agent beside it are macOS/Linux, and what they
feed is a **local** cot-analyzer. The panel that reaches the public dashboard is built and
pushed on the Windows/Norgate box, because that is the only machine that can produce a
store this package can read at all (`2026-08-04 §D14`) and the only one the dash server's
sync originates from (`cotdata/docs/SYNCING.md`).

Two templates, following cotdata's convention exactly: copy them **out of the repo** into
a scheduler directory, fill in the `REPLACE_WITH_*` markers there so a `git pull` never
clobbers your paths, and wire them to Task Scheduler.

| template | does |
|---|---|
| [`docs/examples/windows/run-publish.cmd`](docs/examples/windows/run-publish.cmd) | builds the panel via the portable `bin/publish_damage.py` |
| [`docs/examples/windows/push-panel.cmd`](docs/examples/windows/push-panel.cmd) | rsyncs `CROWDMON_STORE` to the dash server over SSH |

**Chain them behind `errorlevel` guards, after the cotdata producer task:** prices, then
publish, then push. Publishing before the prices land builds last week's panel; pushing
before publishing ships it. Nothing enforces the ordering.

`CROWDMON_STORE` is a separate store **root** from `COTDATA_STORE`, so cotdata's own
`push-to-server.cmd` does not carry the panel and no change to its exclusion list would
make it. That is why the push is a second script rather than a flag.

**Three things a reader of the panel must be told, and the artifact carries all three as
data rather than leaving them to prose on this page.** The trigger columns are the **latest
week only** (a full history is ~95,000 price-store reads against 90 for one week), so there
is no offside history to plot. `trigger_{side}_pool_agrees` is a **tri-state**, and a chart
must suppress the quadrant on `False` exactly as `format_offside` does: on 2026-07-28 the
observed pool contradicts the signal on 16 of the 35 sell-side markets that have a level, so
ignoring it doubles the population of the one cell a reader acts on (`2026-08-04 §D13`). And
a consumer must hold **none of this package's vocabulary** in its own source: a hard-coded
`"warmup"` or `QUADRANT` string is another copy of a living document in a repo with weaker
guards than this one.

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
print(cm.coverage_summary())      # 49 of 51 registry symbols joinable, over 51 codes
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
- what measurement contradicted in both of the above, **one file per day** because a shared
  section counter collided three times in one afternoon across parallel sessions. Read them
  alongside the two documents above, not after:
  [amendments-2026-08-01.md](docs/design/amendments-2026-08-01.md) (A1-A22, closed),
  [amendments-2026-08-02.md](docs/design/amendments-2026-08-02.md) (B1-B32, closed),
  [amendments-2026-08-03.md](docs/design/amendments-2026-08-03.md) (C1 onward, **the open
  file**). [`docs/design/README.md`](docs/design/README.md) is the index and states the
  convention.

Still in `cotdata`, because they are about that repo's own subsystems:

- [crowdmon_step2_normalisation.md](https://github.com/mspinola/cotdata/blob/main/docs/design/crowdmon_step2_normalisation.md)
  (contract master and normalisation). **Accepted, and layer 2 shipped** as
  `futures/notional.py` and `futures/riskunits.py`, so it is **history, not instructions**:
  an earlier version of this line said "not accepted" and was stale on both counts. It named
  `backadj` for volatility in four places, corrected on cotdata `main` in `ff2b755`. The trap
  table in [CLAUDE.md](CLAUDE.md) is authoritative on the three price series; that document
  is not.
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
