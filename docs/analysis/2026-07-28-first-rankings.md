# First fragility rankings, Disaggregated week ending 2026-07-28

**Report week** 2026-07-28 (Tuesday as-of), released 2026-07-31, provenance `published`.
**Universe** 279 markets, futures-only, Disaggregated.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce.py`.
**Code** `crowdmon.futures.fragility` (A.2), `.flow` (A.3), `.pressure` (A.5).

This is the first real consumer of the canonical COT schema, and it was scoped partly as a
smoke test of that schema before anything larger depends on it. The schema held. Four
premises in the handoff did not, and those are in [§7](#7-what-the-data-contradicted).

---

## 1. Selection, and why it is not a selection

The two markets walked through below were **not chosen**. Every market in the latest report
was ranked by `Q_sell / OI`, then again by `Q_buy / OI`, and the top row of each ranking was
taken. Both full top-10 tables are printed so the selection is auditable, along with what
an open-interest floor would have done instead.

### Top 10 by `Q_sell / OI` — where forced longs are largest relative to the market

| market_name | market_code | open_interest | q_sell | q_buy | q_sell_over_oi | q_buy_over_oi | phi | top_phi_category | sell_to_buy |
|---|---|---|---|---|---|---|---|---|---|
| CALIF LOW CARBON FSC-OPIS - ICE FUTURES ENERGY DIV | 0063CU | 113,935 | 80,325 | 17,255 | 0.7050 | 0.1514 | 0.4551 | managed_money | 4.6551 |
| PJM NI HUB RT OFF-PK FIXED - ICE FUTURES ENERGY DIV | 0643BS | 82,803 | 51,770 | 7,897 | 0.6252 | 0.0954 | 0.4043 | managed_money | 6.5553 |
| CALIF CARBON ALL VINTAGE 2026 - ICE FUTURES ENERGY DIV | 0063EE | 209,464 | 102,014 | 34,924 | 0.4870 | 0.1667 | 0.4923 | managed_money | 2.9210 |
| ERCOT North 345KV Hub RT 7x8 - ICE FUTURES ENERGY DIV | 0643IK | 243,273 | 107,551 | 20,912 | 0.4421 | 0.0860 | 0.3261 | managed_money | 5.1430 |
| GOLD - COMMODITY EXCHANGE INC. | 088691 | 384,603 | 169,076 | 78,759 | 0.4396 | 0.2048 | 0.4681 | managed_money | 2.1468 |
| MINI SOYBEANS - CHICAGO BOARD OF TRADE | 005603 | 27,833 | 10,280 | 6,290 | 0.3693 | 0.2260 | 0.4419 | other_reportable | 1.6343 |
| PJM WESTERN HUB RT OFF - ICE FUTURES ENERGY DIV | 064394 | 269,539 | 92,463 | 24,442 | 0.3430 | 0.0907 | 0.3014 | managed_money | 3.7829 |
| PJM N. IL HUB RT PEAK - ICE FUTURES ENERGY DIV | 0643BT | 68,665 | 23,006 | 4,375 | 0.3350 | 0.0637 | 0.2825 | managed_money | 5.2582 |
| HENRY HUB - NEW YORK MERCANTILE EXCHANGE | 03565B | 401,535 | 134,450 | 117,604 | 0.3348 | 0.2929 | 0.3822 | other_reportable | 1.1432 |
| STEEL-HRC - COMMODITY EXCHANGE INC. | 192651 | 43,954 | 14,590 | 2,339 | 0.3319 | 0.0532 | 0.2755 | managed_money | 6.2369 |

### Top 10 by `Q_buy / OI` — where forced shorts are largest relative to the market

| market_name | market_code | open_interest | q_sell | q_buy | q_sell_over_oi | q_buy_over_oi | phi | top_phi_category | sell_to_buy |
|---|---|---|---|---|---|---|---|---|---|
| CIG ROCKIES FINANCIAL INDEX - ICE FUTURES ENERGY DIV | 02339S | 32,591 | 1,968 | 18,401 | 0.0604 | 0.5646 | 0.3811 | managed_money | 0.1069 |
| RGGI V2027 - ICE FUTURES ENERGY DIV | 0063F6 | 21,749 | 2,052 | 12,133 | 0.0944 | 0.5579 | 0.4180 | managed_money | 0.1691 |
| NAT GAS TETCO-WLA INDEX - ICE FUTURES ENERGY DIV | 0233EP | 27,521 | 1,222 | 11,861 | 0.0444 | 0.4310 | 0.2985 | managed_money | 0.1030 |
| TX REC CRS V30 BACK HALF - NODAL EXCHANGE | 006NHX | 2,923 | 228 | 1,111 | 0.0779 | 0.3802 | 0.2961 | other_reportable | 0.2048 |
| CRUDE DIFF-TMX WCS 1A INDEX - ICE FUTURES ENERGY DIV | 06742G | 59,059 | 3,479 | 22,164 | 0.0589 | 0.3753 | 0.2588 | managed_money | 0.1570 |
| ERCOT NORTH 345KV DA PK DLY FI - ICE FUTURES ENERGY DIV | 0643A5 | 21,640 | 2,130 | 8,112 | 0.0984 | 0.3749 | 0.3350 | managed_money | 0.2626 |
| NEW JERSEY RECs CLASS 2 V2026 - NODAL EXCHANGE | 006NLD | 9,960 | 2,767 | 3,625 | 0.2778 | 0.3640 | 0.3451 | swap | 0.7632 |
| TETCO M2 Basis (Receipts) - ICE FUTURES ENERGY DIV | 0233DR | 558,545 | 78,724 | 201,043 | 0.1409 | 0.3599 | 0.2701 | swap | 0.3916 |
| CIG ROCKIES BASIS - ICE FUTURES ENERGY DIV | 02339U | 446,294 | 27,823 | 159,392 | 0.0623 | 0.3571 | 0.2688 | managed_money | 0.1746 |
| PALLADIUM - NEW YORK MERCANTILE EXCHANGE | 075651 | 18,699 | 2,491 | 6,173 | 0.1332 | 0.3301 | 0.6192 | managed_money | 0.4035 |

**Selected: `0063CU` CALIF LOW CARBON FSC-OPIS and `02339S` CIG ROCKIES FINANCIAL INDEX.**
Walkthroughs are in
[0063CU-calif-low-carbon.md](2026-07-28-0063CU-calif-low-carbon.md) and
[02339S-cig-rockies.md](2026-07-28-02339S-cig-rockies.md).

### Is this ranking just an artifact of small markets?

`Q/OI` is a ratio, so it was worth checking. It is not: the top sell-side market carries
113,935 contracts of open interest, above the 279-market median of 43,954. Under a
100,000-contract floor the sell-side top-3 is unchanged in order (0063CU, 0063EE, 0643IK).
Only at a 250,000 floor does the leader change, to gold.

### What the ranked universe is actually made of

Eight of the twenty ranked rows are ICE Futures Energy Division or Nodal Exchange
instruments — power hubs, gas basis, carbon allowances, renewable energy certificates.
That is not a bias in the ranking; it is the shape of the universe. Of the 279 markets CFTC
publishes a Disaggregated report for, 213 (76%) are ICE Energy Div or Nodal:

| venue | markets |
|---|---|
| ICE FUTURES ENERGY DIV | 145 |
| NODAL EXCHANGE | 68 |
| NEW YORK MERCANTILE EXCHANGE | 29 |
| CHICAGO MERCANTILE EXCHANGE | 11 |
| COMMODITY EXCHANGE INC. | 10 |
| CHICAGO BOARD OF TRADE | 8 |
| ICE FUTURES U.S. | 6 |
| MIAX FUTURES EXCHANGE | 1 |
| ICE FUTURES EUROPE | 1 |

**This is worth stating plainly because it is easy to get backwards.** The famous
commodities are a small minority of the Disaggregated report, and a "cross-market" result
over this universe is mostly a result about North American power and gas basis swaps. Any
later cross-market engine (spec §7, PCA and trend alignment) will need to decide whether
that is the intended population, because a PC1 fitted on these 279 markets is a statement
about ERCOT and PJM, not about the macro book.

For orientation, where the classic outrights land on `Q_sell / OI`:

| market | rank of 279 | `Q_sell / OI` | Phi |
|---|---|---|---|
| GOLD | 5 | 0.4396 | 0.468 |
| SILVER | 28 | 0.2404 | 0.417 |
| SOYBEANS | 34 | 0.2240 | 0.259 |
| CORN | 46 | 0.1884 | 0.313 |
| CRUDE OIL | 131 | 0.0887 | 0.229 |
| WHEAT-SRW | 169 | 0.0645 | 0.334 |
| NAT GAS | 202 | 0.0510 | 0.262 |

Gold at rank 5 is the one to notice: a genuinely large, liquid market carrying a
fragility-weighted long position equal to 44% of its open interest.

---

## 2. Does the real data match the cocoa template?

The template in appendix A.2 is described as heavily producer-hedged on the short side with
a fragile levered long side. **The answer is that both shapes exist, and which one you get
is not predictable from the market being a commodity.**

> **Caveat on this comparison.** `crowdmon_plain_language_summary.md` is not present in
> either this repo or `cotdata/docs/design/`, so the cocoa example itself could not be read.
> What follows is checked against the one-line characterisation in the handoff, not against
> the appendix. See [§7](#7-what-the-data-contradicted).

| | 0063CU CALIF LOW CARBON | 02339S CIG ROCKIES |
|---|---|---|
| Managed Money | **+69,007 long**, 0 short | 0 long, **18,080 short** |
| Producer/Merchant | 8,566 long, **86,986 short** | **29,816 long**, 11,167 short |
| shape | matches the template | **inverts it** |
| `Q_sell / Q_buy` | 4.66 | 0.11 |

`0063CU` is the template almost exactly: Managed Money holds a purely long book of 69,007
contracts against zero shorts, and Producer/Merchant is short 86,986 as a hedge. Levered
long, hedged short.

`02339S` is the mirror image. Producer/Merchant is **net long** 18,649 and Managed Money is
**purely short** 18,080. The fragile side is the short side, and the immovable side is long.

That inversion is not exotic once you look for it. Across the 279 markets,
Producer/Merchant is net **long** in 141 of them (50.5%) and net short in 138 (49.5%) — as
close to a coin flip as the data can get. Managed Money is barely more committed: net long
in 43.0%, net short in 41.9%, exactly flat in 15.1%.

| category | net long | net short | flat |
|---|---|---|---|
| managed_money | 43.0% | 41.9% | 15.1% |
| producer_merchant | 50.5% | 49.5% | 0.0% |
| swap | 48.4% | 49.8% | 1.8% |
| other_reportable | 43.4% | 52.7% | 3.9% |
| nonreportable | 56.6% | 38.4% | 5.0% |

The template's shape is a *common case, not the structure of futures markets*, and it is
common for a specific reason: it describes a market where a physical producer is selling
forward. In a gas basis or power market the entity hedging physical is frequently buying
rather than selling, and the sign flips.

**Finding: any rule that assumes producers are short and funds are long will be wrong about
half the Disaggregated universe.** The directional split (`Q_sell` and `Q_buy` kept apart)
is what makes this visible rather than being averaged away, which is the argument for the
split rather than a single fragility number.

---

## 3. Phi is not a Managed Money proxy

The handoff anticipated that Managed Money would typically dominate the Phi numerator, and
that a walkthrough should say so rather than implying a broad reading. Measured, it does not
dominate. Managed Money is the largest contributor in **81 of 279 markets** (29%), and the
median largest contributor accounts for only 44% of the Phi it sits in.

| category | mean share of gross OI | weight | mean Phi contribution |
|---|---|---|---|
| producer_merchant | 0.5648 | 0.1 | 0.0565 |
| swap | 0.1324 | 0.4 | 0.0529 |
| other_reportable | 0.1018 | 0.5 | 0.0509 |
| managed_money | 0.0627 | 1.0 | 0.0627 |
| nonreportable | 0.0520 | 0.6 | 0.0312 |

Read the first and last columns together. Producer/Merchant holds **56% of gross open
interest** on average and contributes 5.7% to Phi; Managed Money holds **6%** and
contributes 6.3%. The 0.1 weight is doing exactly the job it was configured to do, and the
result is that Phi lands as a rough balance between the hedgers who are large but immovable
and the funds who are small but forced.

This is a property of the weight set, not a discovery about markets, and it is the reason
`fragility.contributions` exists and is printed in both walkthroughs. A Phi of 0.38 means
different things in a market where Managed Money carries three-quarters of it and one where
five categories each carry a fifth.

---

## 4. Flow decomposition: tolerance sensitivity

The dominance tolerance is the one free parameter in `flow.decompose`. Below 0.25 a week
must be more one-sided to earn a directional label; above it, less. Swept over
0.15 / 0.25 / 0.40, as required.

**Wide panel** — 346 markets, 2025-01-07 to 2026-07-28, 107,050 transitions:

| tolerance | new_longs | short_covering | new_shorts | long_liquidation | mixed | quiet | gap | reclassified vs 0.25 |
|---|---|---|---|---|---|---|---|---|
| 0.15 | 0.0865 | 0.0677 | 0.0888 | 0.0666 | 0.4707 | 0.1804 | 0.0392 | 0.0756 |
| 0.25 | 0.1075 | 0.0841 | 0.1100 | 0.0837 | 0.3951 | 0.1804 | 0.0392 | 0.0000 |
| 0.40 | 0.1337 | 0.1052 | 0.1359 | 0.1049 | 0.3007 | 0.1804 | 0.0392 | 0.0944 |

**Liquid panel** — the 27 registry markets, 2006-06-13 to 2026-07-28, 135,835 transitions:

| tolerance | new_longs | short_covering | new_shorts | long_liquidation | mixed | quiet | gap | reclassified vs 0.25 |
|---|---|---|---|---|---|---|---|---|
| 0.15 | 0.0733 | 0.0515 | 0.0595 | 0.0681 | 0.7235 | 0.0023 | 0.0218 | 0.1260 |
| 0.25 | 0.1062 | 0.0809 | 0.0925 | 0.0988 | 0.5975 | 0.0023 | 0.0218 | 0.0000 |
| 0.40 | 0.1484 | 0.1196 | 0.1349 | 0.1370 | 0.4361 | 0.0023 | 0.0218 | 0.1614 |

### The honest reading, in two halves

**The tolerance is doing a lot of work, and it must be reported.** On the liquid panel the
`mixed` share swings from 72% to 44% across the sweep, and **28.74% of all weeks change
label** between 0.15 and 0.40. By the handoff's own standard that is high instability, and
it means the pure-versus-mixed boundary is set by the parameter rather than by the data.

**But the tolerance never changes the direction, only the willingness to commit.** Of the
39,040 weeks that change label between 0.15 and 0.40, the number that move from one pure
state to a *different* pure state is **zero**. Every single change is `mixed` becoming pure.
That is structural rather than lucky: the dominant leg is `argmax(|ΔLong|, |ΔShort|)` and
does not depend on the tolerance at all, which only gates whether the smaller leg
disqualifies the label. It is asserted in
[`test_flow.py`](../../tests/test_flow.py) anyway, because an implementation that broke it
would still produce a plausible-looking distribution.

**So the tolerance is a confidence threshold, not a classifier.** A `new_longs` label is
robust to it; the *rate* of `new_longs` labels is not. Any downstream use that counts states
(a "share of weeks in short covering" style feature) inherits the parameter and needs the
sweep reported beside it. Any use that reads a specific week's label does not.

**One further caveat.** `mixed` is the modal state on the liquid panel at every tolerance
tested — 60% at the default. The spec's four-state table describes a minority of weeks. The
decomposition is still worth having, and the design doc's claim that it is "one line of code
and among the highest-value outputs in the system" is fair, but a reader should know that in
six weeks out of ten it declines to give one of the four answers.

---

## 5. The open-interest identity

Two identities, both exact on Disaggregated, both checked on every load:

- `Σ long == Σ short` across categories, each side including spreading (futures are closed
  and zero-sum, so every long is somebody's short)
- `Σ long + spreading == open_interest`

**Exception rate: zero. Not approximately zero.**

| panel | markets | span | market-weeks | unbalanced | `oi_gap` non-zero |
|---|---|---|---|---|---|
| liquid | 27 | 2006-06-13 to 2026-07-28 | 27,194 | 0 | 0 |
| wide | 346 | 2025-01-07 to 2026-07-28 | 21,756 | 0 | 0 |

By year on the liquid panel, every year from 2006 to 2026 shows 0 exceptions and a worst
absolute imbalance of 0. It is stable over history in the strongest sense available: it has
never once failed.

That is a real result about the parse rather than a tautology — the identity is computed
from five independently mapped category columns plus a separately mapped spreading column
and a separately mapped open-interest column, so a single misrouted column breaks it on the
first week. It is reported as a rate rather than raised on, per the handoff, and
[`test_panel.py`](../../tests/test_panel.py) verifies that corrupting one week surfaces as a
rate rather than as an exception.

---

## 6. What is missing

Stated once here rather than repeated in both walkthroughs.

- **No volume, so no real days-to-liquidate.** `T = Q / (κ·V)` is the actual output the
  spec is aiming at, and `V` does not exist anywhere in this workspace — ADR-0007 step 2 is
  on ice. `pressure.exit_pressure` returns `days_to_liquidate = None` and takes `volume` as
  an optional argument so the real figure slots in later. **No volume was estimated.**
  `Q/OI` is a stock-over-stock ratio and orders markets; it does not measure a duration.
- **No prices, so no trigger level.** Everything here is contract counts. A market whose
  fragile side is large tells you nothing about the price at which that side is forced out.
- **No notional, so no cross-market comparison of size.** 69,007 California carbon
  contracts and 69,007 gold contracts are not the same quantity of anything. Rankings here
  are within-market ratios for exactly this reason, and the contract master
  (`normalize/contract_master.py`) is the piece that lifts this.
- **The weights are judgement.** They are configured, documented and never fitted. Every
  number in these documents moves if they move, which is why per-category contributions are
  printed everywhere a Phi is.
- **Not point-in-time before 2026-07-31.** Vintages accumulate forward only, so every week
  before first capture is a current value with revisions applied. That is fine for these
  descriptive measurements and is not fine for evaluating a rule.
- **Trader counts are suppressed often.** 44% of Managed Money long counts and 47% of short
  counts are null in the latest week, and non-reportables have no count by definition. The
  breadth-depth decomposition returns null rather than imputing.

---

## 7. What the data contradicted

Per the working agreement: measure, do not assume, and if a measurement contradicts a doc,
fix the doc in the same change and say so.

### 7.1 The Oct-Nov 2025 shutdown left no gap in report dates

The handoff states that without gap handling "the Oct–Nov 2025 shutdown reads as one
enormous week of flow". **It does not.** Report dates run weekly and unbroken straight
through the window — 09-30, 10-07, 10-14, 10-21, 10-28, 11-04 — because CFTC published the
backlog carrying the correct as-of Tuesdays. Flow magnitudes in the window are ordinary:
median absolute Managed Money `Δnet` of 1,951 to 5,811 contracts against a 2025 baseline of
4,056.

The only interruption is the 2025-11-10 / 2025-11-18 pair, a 6-day interval followed by an
8-day one, which is a Veterans Day holiday shift (2025-11-11 fell on a Tuesday).

Where the shutdown **does** land is the release date, not the report date: every release
date in the window carries provenance `derived`, meaning "the Friday after the Tuesday",
which is precisely the inference the adapter documents as failing on backlog weeks. So a
flow decomposition indexed on report date is unaffected, and anything indexed on release
date over that window is resting on a guess.

### 7.2 Gaps are caused by thin markets, not by incidents

The gap rule is still necessary — just for a different reason. Across the full Disaggregated
history (27 markets, 27,167 transitions):

| interval | count | what it is |
|---|---|---|
| 7 days | 26,574 | normal |
| 6 or 8 days | 570 | holiday shifts, in matched pairs |
| 14 to 294 days | 23 | **a market dropping out of the report** |

Of the 23 long intervals, 22 are oats (`004603`) and one is lumber. A market that falls
below the reporting threshold vanishes from the report and reappears when it recovers;
oats has a 294-day interval ending 2025-09-09. Without the gap rule that single difference
enters every ranking as the largest weekly flow in the sample.

**Consequence for the rule as specified.** The handoff requires differencing only across
intervals exactly 7 days apart, which is implemented and is the default. On the liquid panel
that labels 2,965 rows `gap`, of which **2,850 are the 6-and-8-day holiday pairs** — real
weeks of flow, discarded. The alternative admits them but compares a 6-day move against an
8-day one, roughly a 30% difference in span. Neither is free, so `gap_days_tolerance` is a
parameter (default 0, the strict reading) and `days_elapsed` is always emitted.

### 7.3 Phi is not usually a Managed Money story

Covered in [§3](#3-phi-is-not-a-managed-money-proxy). Managed Money is the top contributor
in 29% of markets, not the typical case.

### 7.4 The cocoa template's shape holds in about half the universe

Covered in [§2](#2-does-the-real-data-match-the-cocoa-template). Producer/Merchant is net
long in 141 of the 279 markets (50.5%), so the template's producer-short shape describes
slightly under half of them.

### 7.5 The design docs and the package layout the handoff assumed

Three mismatches, none of them data findings, recorded so the next session is not surprised:

- **Package layout.** The handoff calls for `src/crowdmon/` split into `core/`
  (asset-class agnostic, shared with the equity monitor per module spec §12) and `futures/`
  (COT-specific). The repo it landed in was `crowdmon-futures` with `ingest/`, `normalize/`
  and `engines/`, already carrying layer 1 and the contract master. It has been restructured
  to the handoff's layout, and the reproducer output is byte-identical across the move, so
  nothing in this document depends on which layout produced it. Two deliberate deviations,
  both from the handoff's own rule that `core/` holds only what is genuinely asset-class
  agnostic: `futures/cot_adapter.py` remains beside `futures/io.py` (it answers a different
  question, "what was knowable on date *t*"), and `report.py` is split, with the markdown
  rendering in `core/` and the category tables and `Q`/`Phi` arithmetic in `futures/`.
  `core/store.py`, `core/aggregate.py` and `core/impact.py` are absent rather than stubbed.
  The **repo directory and remote were renamed to `crowdmon` in the same change**, so the
  package, the checkout and the remote all now agree.
- **`crowdmon_plain_language_summary.md` does not exist** in this repo or in
  `cotdata/docs/design/`. The handoff names its appendix as authoritative for every formula
  and as the source of the cocoa template. The formulas as given in the handoff were used
  instead, and they are self-consistent — the Phi bound holds by construction and is
  asserted. The cocoa comparison in §2 is against the handoff's one-line description only.
  **If that document exists somewhere, the Phi definition and the cocoa comparison should be
  re-checked against it.**
- **Flow decomposition already exists in `cotdata`** as `vintage_flow.decompose`, built
  2026-07-30, resolving the same "~0 never happens" problem by dominant leg with no
  tolerance and therefore no `mixed` state. This implementation is the tolerance-based one
  the handoff specifies. Both are defensible; they answer slightly different questions, and
  the difference is that this one can decline to name a direction. The duplication is real
  and worth resolving in a later session rather than silently.

---

## Bottom line

The schema survived its first real consumer without a scratch: the open-interest identity
holds on every one of 48,950 market-weeks across both panels and twenty years, with zero
exceptions and no tolerance needed. Nothing downstream needs to be defensive about it.

The two markets the ranking picked are structurally opposite — one levered long against
hedged shorts, the other levered short against a physically long hedger — and that is the
most useful thing found here. Roughly half the Disaggregated universe inverts the shape the
design doc's worked example uses, so the habit of reading "Managed Money" as the long side
and "Producer/Merchant" as the short side is a coin flip dressed up as structure. Keeping
`Q_sell` and `Q_buy` apart is what makes the inversion visible instead of averaging it into
a single number that describes neither market.

Two cautions carry forward with real force. The flow classifier's tolerance moves 29% of
week labels across the range tested, which is a lot; it is defensible only because it never
changes *which* direction a week is called, just whether the classifier commits to one at
all, and that is a theorem about the rule rather than a lucky property of this sample. And
`mixed` is the modal outcome at 60% of weeks, so the spec's four-state table describes a
minority of the data. Neither undermines the decomposition, but both belong in the caption
of any chart built on it.

Everything here is a statement about the shape of positioning, not about direction or
return. Without volume there is no days-to-liquidate and without prices there is no trigger
level, so the strength of what has been shown is: **a clean, reproducible measurement of
who holds what and which side is structurally forceable, and nothing at all about whether
anything is about to happen.**
