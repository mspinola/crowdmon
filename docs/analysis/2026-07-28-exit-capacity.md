# Exit capacity: `T = Q / (kappa V)` across the covered set, week ending 2026-07-28

**Reports** Disaggregated and TFF, futures-only, released 2026-07-31.
**Universe** 372 market codes in the two reports, **45** of which reach a live `T`.
**Comparison week** 2026-07-21, in §8 only, and from the current-state store per §6.2.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_exit_capacity.py`.
**Code** `crowdmon.futures.pressure`, `volume`, `fragility`, appendix §A.5 and §A.2.
Nothing in `src/` was written or changed for this document.

The first cross-report `T` table. `pressure.rank_markets` has emitted `dtl_sell` since
`futures/volume.py` supplied a whole-market denominator, and
[2026-07-28-composite.md](2026-07-28-composite.md) consumes it as the `I` term, but the
duration itself has never been published as a ranking over both report types with the
seam between them stated. That is what this is.

> **This document ranks. It does not validate.** Every figure is descriptive, computed on
> one week by a session that did not author the engines. There is no holdout, no
> pre-registration and no `crucible` verdict, and a `T` is a statement about tail shape,
> not about next week's return. Read it as "how long would the forced side take to leave",
> never as a signal.

---

## 1. What is being computed, and from what

    T = Q / (kappa . V)         days to liquidate

with `kappa = 0.2` (`core/config.py`), `Q` the fragility-weighted one-sided position from
appendix §A.2, and `V` a trailing whole-market daily volume from §A.5. Both directions are
carried separately and never added: forced longs sell and forced shorts buy, so `Q_sell`
and `Q_buy` describe two different events and their sum describes none.

The three inputs come from three different places, and that is the fact §6 is about:

| input | source | needs |
|---|---|---|
| `Q_sell`, `Q_buy`, `Phi` | **either** COT store, they agree exactly (§6.1) | one report week |
| `kappa` | `core/config.py` | nothing. It is configured judgement, not fitted |
| `V`, `V_stress` | the price store, via `cotdata.get_prices` | about five years of daily bars per symbol |

`Q` is priced in contracts and so is `V`, which is why `T` needs neither the notional rung
nor the risk-unit rung of the normalisation ladder. It is the one headline number in the
package that is unit-clean without a price series for the numerator.

---

## 2. Coverage: 45 of 372 codes, and every drop is the same drop

| report | codes | live `dtl_sell` | no symbol | no volume within tolerance |
|---|---|---|---|---|
| disaggregated | 279 | **25** | 254 | **0** |
| tff | 93 | **20** | 73 | **0** |

**Not one market is lost for want of a volume.** All 327 drops are codes with no contract
spec, so they never reach the volume join at all. That is the distinction
`volume.volume_coverage` exists to make visible, and it changes what the table is: the 45
are not a sample of 372, they are the traded universe, and the 327 are codes that are not
traded through this workspace (ICE Energy Division and Nodal power and gas basis dominate
the Disaggregated remainder, per [2026-07-28-first-rankings.md](2026-07-28-first-rankings.md)).

Volume staleness is **0 days** on every one of the 45, so no `T` here rests on a
stale denominator.

The three Consolidated equity index codes (`13874+`, `20974+`, `12460+`) have no contract
spec and therefore no `T`. Their full-size components appear instead, so nothing in the
table double-counts an aggregate against its parts, which is the trap
[2026-07-28-tff-financial-futures.md](2026-07-28-tff-financial-futures.md) §2.1 records.

---

## 3. The ranking

Sorted by `T_sell` descending. **D** is Disaggregated, **T** is TFF. `kV` is the
denominator in contracts per day. **†** flags a thin fund, defined in §4.

| # | rpt | market | sym | `Q_sell` | `Q_buy` | `kV` | **`T_sell`** | `T_buy` | `Phi` |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | D | LUMBER | LBR | 2,352.3 | 396.7 | 222.7 | **10.56** | 1.78 | 0.446 |
| 2 | D | MILK, Class III | DC | 3,630.7 | 7,192.0 | 404.3 | **8.98** | 17.79 | 0.325 |
| 3 | D | COTTON NO. 2 | CT | 86,374.7 | 13,117.6 | 12,130.6 | **7.12** | 1.08 | 0.311 |
| 4 | D | LIVE CATTLE | LE | 91,663.4 | 25,409.9 | 15,065.7 | **6.08** | 1.69 | 0.354 |
| 5 | T | MEXICAN PESO | 6M | 72,843.0 | 38,445.8 | 12,787.7 | **5.70** | 3.01 | 0.536 |
| 6 | T | CANADIAN DOLLAR | 6C | 87,632.3 | 140,469.6 | 15,608.9 | **5.61** | 9.00 | 0.497 |
| 7 | D | COPPER #1 | HG | 75,119.7 | 8,527.9 | 14,366.1 | **5.23** | 0.59 | 0.345 |
| 8 | D | SOYBEAN MEAL | ZM | 163,387.9 | 25,735.9 | 36,758.8 | **4.44** | 0.70 | 0.287 |
| 9 | T | SWISS FRANC | 6S | 25,888.8 | 30,555.7 | 5,881.0 | **4.40** | 5.20 | 0.454 |
| 10 | D | ORANGE JUICE | OJ | 1,251.6 | 1,683.6 | 287.3 | **4.36** | 5.86 | 0.533 |
| 11 | D | COFFEE C | KC | 34,871.2 | 6,059.0 | 8,100.8 | **4.30** | 0.75 | 0.310 |
| 12 | T | BRITISH POUND | 6B | 84,267.0 | 47,070.9 | 20,365.0 | **4.14** | 2.31 | 0.492 |
| 13 | T | NZ DOLLAR | 6N | 30,978.5 | 44,995.5 | 7,722.2 | **4.01** | 5.83 | 0.485 |
| 14 | D | WHEAT-HRW | KE | 63,307.0 | 17,257.4 | 15,896.7 | **3.98** | 1.09 | 0.309 |
| 15 | D | SOYBEANS | ZS | 228,494.0 | 41,544.7 | 60,287.1 | **3.79** | 0.69 | 0.259 |
| 16 | D | CORN | ZC | 327,137.6 | 84,773.9 | 88,722.3 | **3.69** | 0.96 | 0.313 |
| 17 | D | SOYBEAN OIL | ZL | 150,166.8 | 23,575.9 | 42,066.4 | **3.57** | 0.56 | 0.243 |
| 18 | D | GOLD | GC | 169,075.9 | 78,758.9 | 48,065.4 | **3.52** | 1.64 | 0.468 |
| 19 | D | SUGAR NO. 11 | SB | 95,379.1 | 127,660.2 | 31,854.8 | **2.99** | 4.01 | 0.393 |
| 20 | T | UST 2Y NOTE | ZT | 658,887.1 | 1,757,042.0 | 230,408.2 | **2.86** | 7.63 | 0.475 |
| 21 | T | USD INDEX **†** | DX | 10,339.6 | 12,457.4 | 4,205.9 | **2.46** | 2.96 | 0.573 |
| 22 | T | UST 5Y NOTE | ZF | 884,091.0 | 2,434,957.6 | 363,183.9 | **2.43** | 6.70 | 0.442 |
| 23 | T | JAPANESE YEN | 6J | 79,128.5 | 126,907.1 | 33,552.9 | **2.36** | 3.78 | 0.540 |
| 24 | D | GASOLINE RBOB | RB | 89,518.6 | 15,415.8 | 38,935.8 | **2.30** | 0.40 | 0.303 |
| 25 | D | FEEDER CATTLE | GF | 11,814.6 | 6,453.2 | 5,355.2 | **2.21** | 1.21 | 0.386 |
| 26 | T | UST BOND | ZB | 231,445.2 | 502,726.8 | 108,971.4 | **2.12** | 4.61 | 0.430 |
| 27 | D | LEAN HOGS | HE | 27,462.0 | 33,737.5 | 13,046.0 | **2.11** | 2.59 | 0.407 |
| 28 | D | PLATINUM | PL | 11,790.1 | 3,580.7 | 6,135.5 | **1.92** | 0.58 | 0.456 |
| 29 | T | EURO FX | 6E | 80,565.1 | 135,404.4 | 42,779.9 | **1.88** | 3.17 | 0.420 |
| 30 | D | PALLADIUM | PA | 2,490.8 | 6,173.0 | 1,383.7 | **1.80** | 4.46 | 0.619 |
| 31 | T | AUSTRALIAN DOLLAR | 6A | 38,394.5 | 15,180.3 | 21,920.5 | **1.75** | 0.69 | 0.488 |
| 32 | T | UST 10Y NOTE | ZN | 792,351.7 | 2,348,068.6 | 464,452.1 | **1.71** | 5.06 | 0.474 |
| 33 | D | COCOA **†** | CC | 11,423.1 | 10,616.3 | 7,611.4 | **1.50** | 1.39 | 0.262 |
| 34 | D | SILVER | SI | 25,654.7 | 11,614.9 | 18,982.4 | **1.35** | 0.61 | 0.417 |
| 35 | D | NY HARBOR ULSD **†** | HO | 43,073.6 | 8,222.7 | 37,572.2 | **1.15** | 0.22 | 0.321 |
| 36 | T | E-MINI S&P 500 | ES | 351,306.0 | 601,966.1 | 326,421.1 | **1.08** | 1.84 | 0.441 |
| 37 | T | E-MINI S&P 400 **†** | EMD | 2,952.6 | 2,334.8 | 2,760.6 | **1.07** | 0.85 | 0.469 |
| 38 | T | BITCOIN | BTC | 2,739.7 | 7,078.2 | 2,598.5 | **1.05** | 2.72 | 0.522 |
| 39 | D | WHEAT-SRW **†** | ZW | 29,893.5 | 15,899.3 | 31,257.8 | **0.96** | 0.51 | 0.334 |
| 40 | T | ETHER | ETH | 3,680.0 | 6,576.6 | 4,063.8 | **0.91** | 1.62 | 0.445 |
| 41 | D | WTI-PHYSICAL **†** | CL | 164,932.9 | 204,244.8 | 195,180.8 | **0.85** | 1.05 | 0.229 |
| 42 | D | NAT GAS | NG | 85,353.4 | 150,014.2 | 107,206.4 | **0.80** | 1.40 | 0.262 |
| 43 | T | RUSSELL E-MINI | RTY | 34,200.0 | 78,467.0 | 43,810.3 | **0.78** | 1.79 | 0.466 |
| 44 | T | DJIA x $5 **†** | YM | 5,775.7 | 5,814.4 | 21,470.0 | **0.27** | 0.27 | 0.492 |
| 45 | T | NASDAQ MINI | NQ | 29,046.9 | 69,786.4 | 118,262.9 | **0.25** | 0.59 | 0.563 |

`T_sell` spans 0.25 to 10.56 days, median 2.36.

**The head of the table is small ag and livestock, and the tail is financial.** That
ordering is the whole reason the duration is computed rather than the position size:
lumber's `Q_sell` of 2,352 contracts is the smallest but one in the table, and it ranks
first because 2,352 contracts is ten days of what a forced seller can take. Corn's
`Q_sell` is 139 times larger and clears in a third of the time.

**`T_sell` and `T_buy` disagree constantly, and that is the informative part.** Copper
takes 5.23 days to unwind the long side and 0.59 to unwind the short, a factor of 8.8.
Milk runs the other way, 8.98 against 17.79. Collapsing the pair into one number would
throw away the only part of the measurement that names a direction.

---

## 4. Thin funds: 7 of 45, and all of them sit low

A `T` over a market with no fragile capital is well formed and meaningless: the arithmetic
is fine and the subject is absent. The screen is `|P_fragile| / OI < 0.05`, where
`P_fragile` is the NET of the weight-1.0 category, `managed_money` on Disaggregated and
`leveraged` on TFF.

| rpt | sym | `P_fragile` | `OI` | `|P|/OI` | `T_sell` rank |
|---|---|---:|---:|---:|---:|
| T | EMD | -164 | 36,145 | **0.00454** | 37 |
| T | YM | -1,194 | 83,013 | **0.01438** | 44 |
| D | ZW | -8,163 | 463,502 | **0.01761** | 39 |
| T | DX | -1,601 | 58,251 | **0.02748** | 21 |
| D | CC | -8,773 | 201,223 | **0.04360** | 33 |
| D | HO | 11,246 | 249,594 | **0.04506** | 35 |
| D | CL | 92,943 | 1,859,795 | **0.04997** | 41 |

**The screen removes nothing from the head.** The flagged markets rank 21, 33, 35, 37, 39,
41 and 44 of 45, so no result in this table's top twenty depends on it. That is worth
recording because the opposite outcome was equally available and would have been a finding
about the measure rather than the market.

**WTI is inside the cut by 0.005% of open interest** (0.049975), so it is on the line
rather than clearly flagged. Nothing else is near: the next market up is natural gas at
0.0633, and the whole 0.04 to 0.07 band holds only cocoa, ULSD, WTI and natural gas.

**Cocoa is the one to notice**, because it is the market the appendix's constructed worked
example is drawn from. Its Managed Money net is now 4.4% of open interest and **short**,
which is consistent with `docs/design/amendments-2026-08-02.md` §B31 and §B36 recording
that cocoa has not held the template shape since early 2026.

---

## 5. TFF and Disaggregated are two populations, and five rows should not be read at all

**20 of the 45 are TFF**, and the six-outcome template of `fragility.shape_labels` is
inexpressible on all of them. The template needs a low-weight immovable holder, which on
Disaggregated is `producer_merchant` at 0.1; TFF's nearest analogue is `asset_manager` at
0.3, a different claim about a different holder. A `Q_sell / Q_buy` asymmetry from the D
block and one from the T block are not comparable quantities, which is why the report type
is carried on every row of the reproducer's output rather than mentioned once.

**The five equity index rows are the suspect set**: ES (36), EMD (37), RTY (43), YM (44),
NQ (45). All five land in the bottom ten. NQ at 0.25 days and YM at 0.27 say the entire
fragile book clears inside a third of a session, which is what a category net made of
basis and spread legs against cash and ETF exposure looks like rather than a directional
book anyone can be forced out of. Two of the five (YM, EMD) carry the thin-fund flag
independently, and YM's `top_phi_category` is `dealer`, not `leveraged`. **No `T` from
those five rows should be used.**

The rates complex has a quieter version of the same problem. ZT, ZF, ZN and ZB carry the
four largest `Q_buy` figures in the table by a wide margin (2.43M, 2.35M, 1.76M and 503k
against 140k for the next market, Canadian dollar), and `T_buy` figures of 7.63, 6.70, 5.06
and 4.61 that rank 3rd, 4th, 8th and 9th of 45. A levered-fund short in Treasuries is
substantially the cash-futures basis trade, which is a hedged position wearing a
levered-fund label. The numbers are computed correctly and the holder is not the one the
weight describes.

---

## 6. The COT data this rests on, and why it did not need to be the vintage store

**This analysis was computed from the vintage store, and it did not need to be.** The same
45 markets, at identical values, come out of the ordinary current-state parquets, which are
also the store with twenty years of history rather than eighteen months. The section is
written this way round because the wrong choice was made first and the reason it looked
right is worth recording.

### 6.1 The two stores give the same answer here, exactly

Running the whole chain off `from_current_store` instead of `latest` (which routes to
`from_vintage`):

| column | markets differing | max abs diff |
|---|---|---|
| `q_sell` | **0** | 0.0 |
| `q_buy` | **0** | 0.0 |
| `phi` | **0** | 0.0 |
| `dtl_sell` | **0** | 0.0 |
| `dtl_buy` | **0** | 0.0 |
| `open_interest` | **0** | 0.0 |
| `P_fragile` | **0** | 0.0 |

45 live markets either way, none live in one store and not the other. Not "agree to
tolerance": bit-identical, because the underlying CFTC numbers are the same numbers.

### 6.2 Why the vintage store bought nothing, and the trap that hid it

The vintage store's advantage is **breadth**, and `futures/io.py` states it plainly: 346
Disaggregated codes and 111 TFF against the current-state parquets' 27 and 24. Reaching for
it on a cross-market ranking is the documented, normally correct move, and that is the
reasoning that put it here.

**It is the wrong move for `T` specifically, because the binding constraint sits upstream of
the report.** `T` needs a volume denominator, a volume needs a `symbol`, and a `symbol`
needs a `ContractMaster` entry. Only 45 codes clear that join, 327 do not, and **every one
of the 45 is already in the current-state store**:

| report | vintage codes | current-state codes | live-`T` codes | of those, in current-state |
|---|---|---|---|---|
| disaggregated | 346 | 27 | 25 | **25** |
| tff | 111 | 24 | 20 | **20** |

That is not a coincidence, it is the same selection applied twice. The current-state store
holds `cotdata.registry`'s universe, which is the markets this workspace actually trades,
and `ContractMaster` covers the markets this workspace has contract specs for. **Breadth
past the registry is exactly the breadth that cannot be scored**, so on any question needing
a price the extra 300+ vintage codes are guaranteed to drop out before they reach the
answer. The 279-to-25 collapse in §2 is that fact stated in the other direction.

The cost of the wrong choice is history. The vintage store holds **82 weeks** from
2025-01-07; the current-state store holds **1,051 weeks** from 2006-06-13, for the same 45
markets. So the store chosen for breadth gave up 92% of the depth and returned no breadth
that survived the join.

### 6.3 What the reports have to carry, in either store

**One report week, and no more.** `Q` and `Phi` are cross-sectional: no lag, no difference,
no trailing window. The scored week is **1,860 rows**, 1,395 Disaggregated and 465 TFF,
which is the entire COT requirement of the table above.

Columns read, on the natural key
`['report_date', 'market_code', 'report_type', 'combined', 'category']`: `market_name`,
`long_contracts`, `short_contracts`, `spread_contracts`, `open_interest`. That is five
value columns and a five-part key.

`spread_contracts` is read for schema conformance (`io.REQUIRED_COLUMNS`) and reported as
`spread_total`, but it stays outside the `Phi` numerator: spreading is a matched long and
short in one trader's hands and carries no directional exit.

**The vintage store carries 22 columns and `T` uses 10 of them.** The four vintage-only
columns (`release_date`, `release_date_source`, `observed_at`, `snapshot_id`) are read only
by the release-indexed path in §6.5, which is bookkeeping about the read rather than an
input to `T`. Never read in either store: `trader_count_long`, `trader_count_short`,
`cr4_net_long`, `cr4_net_short`, `cr8_net_long`, `cr8_net_short`, `row_sha256`,
`is_tombstone`.

`combined` is `False` throughout both stores, so every figure here is futures-only. The
Supplemental report is futures-and-options combined and is in neither store, which is why
no number here can be differenced against it.

### 6.4 What only the vintage store can do, and why this table is not it

Four things, and this analysis uses none of them:

1. **Index on release date rather than report date.** Using the Tuesday embeds a three-day
   lookahead, and three days is where the largest moves are. Descriptive cross-sections do
   not care; anything evaluating a rule does.
2. **Provenance.** `release_date_source` distinguishes a recorded publication from the
   inferred "Friday after the Tuesday", which is what fails on holiday shifts and on the
   Oct-Nov 2025 backlog.
3. **`pit_complete`.** Whether a row is as-published or a later-captured stand-in.
4. **Revisions.** Multiple vintages per key, which is what a restatement looks like.

The rule that follows: **use `from_current_store` for a descriptive cross-section that needs
a price, and `VintageCotSource` when the date the information became public is part of the
question.** `latest()` is the trap in between, because its name says "the newest week" and
says nothing about which store it came from.

**Legacy is unusable in either store**, by design. `core/config.py` has no Legacy weights on
purpose: its `noncommercial` bucket merges levered funds with everything else
non-commercial, which is exactly the distinction the weights exist to make. So of the
vintage store's three report domains, `T` can use two, and `from_current_store` refuses
Legacy outright for a related reason (it drops non-commercial spreading, so its
open-interest identity cannot close).

### 6.5 The half that is genuinely scarce is the volume, and it is in neither COT store

`V` comes from `cotdata.get_prices(symbol, adjustment="unadj", volume="front")`, which is
the **price** store. It needs roughly five years of daily bars per symbol:
`DEFAULT_ADV_WINDOW = 252` for the calm denominator (min 60 observations) and
`DEFAULT_STRESS_LOOKBACK = 1260` for `V_stress` (min 20), with `propadj` closes on the side
to rank the stress decile. Plus `ContractMaster` for the `market_code` to `symbol` join,
which is where all 327 unscoreable codes die.

**So the COT half of `T` is cheap and either store supplies it, while the price half is the
one under a commercial subscription.** That asymmetry is the same constraint `CLAUDE.md`
records for the live test suite: Norgate data cannot be committed to a public repo, so 67
assertions never run in CI.

### 6.6 What one vintage cannot tell you

**The release-indexed read and the current-state read are byte-identical here**, 0 markets
differing on `q_sell`, `q_buy`, `phi`, `dtl_sell`, `dtl_buy`, `open_interest` and
`p_fragile`, max absolute difference 0.0. **That is not evidence of revision stability**, and
it is a different fact from §6.1. A frame cannot disagree with itself, and the store holds
exactly one vintage of this week.

**Every row of the scored week is `pit_complete = False`**, and the cause is a timing
detail worth recording rather than a fault. The captures run at roughly 01:15Z, and CFTC
releases at 15:30 ET Friday:

| report week | first `observed_at` |
|---|---|
| 2026-06-23 | 2026-07-31 01:15:12 |
| 2026-06-30 | 2026-07-31 01:15:12 |
| 2026-07-07 | 2026-07-31 01:15:12 |
| 2026-07-14 | 2026-07-31 01:15:12 |
| 2026-07-21 | 2026-07-31 01:15:12 |
| **2026-07-28** | **2026-08-01 13:54:35** |

The 2026-07-31 01:15Z capture predates that day's release by about eighteen hours, so it
holds the five prior weeks and not the scored one. The first capture containing report week
2026-07-28 is the following day's. `VintageCotSource.load("2026-07-31")` admits captures
through 2026-08-01 00:00, does not find one, and falls back to the earliest vintage held,
which is the 13:54 capture. The values are therefore as they stood about 22 hours after
release, not as published.

The release **date** is nonetheless recorded rather than inferred: provenance is
`published`, the strongest tier, on all 1,860 rows. That is the distinction that fails on
holiday shifts and on the Oct-Nov 2025 backlog, and this week is clean on it.

### 6.7 The ceiling the store choice imposes on everything downstream

The vintage store holds **82 report weeks**, 2025-01-07 to 2026-07-28, across 346
Disaggregated codes, 457 Legacy and 111 TFF. So any trailing statistic taken over it is
capped at 82 weeks, and `composite`'s `I = pct(T)` wants three years of history to
percentile against.

That is the concrete consequence of §6.2 rather than a separate point. **A cross-section
this table's shape cannot be extended backwards through the vintage store**, and it does not
need to be: the same 45 markets carry 1,051 weeks in the current-state store. This is the
two-stores asymmetry `futures/io.py` documents (breadth and depth are in different places),
and the correction here is that `T` only looked like a breadth question. Once the
contract-spec join is applied it is a depth question wearing a breadth question's clothes.

---

## 7. The stress denominator, and where it inverts the calm reading

`V_stress` is §A.5's median volume on the worst decile of return days, trailing. It is
**not reliably the conservative case**: 22 of the 45 markets trade MORE under stress, so
their `T_stress` is shorter than `T_calm`. Split by report, **9 of 25 Disaggregated** and
**13 of 20 TFF**. Stress is the binding case on 23 of 45.

Where it moves the reading most:

| rpt | sym | `T_sell` calm | `T_sell` stress | `V_stress / V_calm` |
|---|---|---:|---:|---:|
| T | ZT | 2.86 | **5.35** | 0.53 |
| D | PA | 1.80 | **3.13** | 0.58 |
| D | KE | 3.98 | **6.18** | 0.64 |
| T | ZF | 2.43 | **3.56** | 0.68 |
| D | CT | 7.12 | **10.17** | 0.70 |
| D | ZL | 3.57 | **4.94** | 0.72 |
| D | HG | 5.23 | **3.86** | 1.35 |
| D | LBR | 10.56 | **6.52** | 1.62 |
| T | YM | 0.27 | **0.15** | 1.80 |

**Cotton is the one that changes rank**: 10.17 days under stress puts it second behind
lumber, ahead of milk. The four Treasury contracts all lose liquidity under stress and all
move up. The equity index contracts move the other way and get faster, which is a second,
independent reason to distrust them: a position that becomes easier to exit precisely when
everything else becomes harder is more likely a hedge leg than a forced holding.

---

## 8. Week on week: 2026-07-21 into the scored week

One week of context, and it is here for a specific reason rather than for completeness: a
`T` table read on its own gives no sense of whether a market's position in it is a standing
property or this week's news. Both weeks come from the current-state store, so the
comparison carries no store difference that could be mistaken for a market move.

**The same 45 markets are live in both weeks**, none entering or leaving.

### 8.1 The ranking is close to static

| statistic | value |
|---|---|
| rank correlation of `T_sell` | **0.9897** |
| median absolute change in `T_sell` | **5.15%** |
| largest rank move | **4** places |
| markets moving 2 places or fewer | **38 of 45** |

That is the answer to "is this week unusual" at the level of ordering, and it is no. It is
also what §1's framing predicts: positioning extremes persist for quarters, so a monitor
whose ranking reshuffled weekly would be measuring noise.

### 8.2 Almost all of the movement is positioning, not liquidity

**`ΔV` never exceeds 1.37%, and is under 0.7% in 34 of 45 markets.** So `ΔT` tracks `ΔQ`
almost exactly, and the two columns below are near-identical everywhere.

This is structural rather than a fact about this fortnight. `Q` is a fresh weekly
observation while `V` is a 252-day trailing mean, so one new day can move the denominator by
at most about 1/252 of that day's deviation from the mean. **A week-on-week `T` move is
therefore a positioning statement and never a liquidity one**, and anything reading it as
"the market got thinner" is reading the wrong factor. Liquidity does move `T`, but on the
timescale of the window, not the report.

| rpt | sym | rank 21 → 28 | `T_sell` 21 | `T_sell` 28 | `ΔT` | `ΔQ_sell` | `ΔV` |
|---|---|---:|---:|---:|---:|---:|---:|
| D | LBR | 4 → **1** | 6.35 | 10.56 | **+66.3%** | +66.8% | +0.3% |
| D | DC | 1 → 2 | 8.93 | 8.98 | +0.6% | +0.5% | -0.1% |
| D | CT | 2 → 3 | 7.25 | 7.12 | -1.8% | -1.3% | +0.6% |
| D | LE | 3 → 4 | 6.72 | 6.08 | -9.4% | -9.2% | +0.3% |
| T | 6M | 7 → 5 | 5.11 | 5.70 | +11.5% | +12.1% | +0.5% |
| T | 6C | 6 → 6 | 5.43 | 5.61 | +3.3% | +3.3% | -0.0% |
| D | HG | 5 → 7 | 5.67 | 5.23 | -7.8% | -7.6% | +0.2% |
| D | ZM | 9 → 8 | 4.17 | 4.44 | +6.7% | +7.4% | +0.6% |
| T | 6S | 10 → 9 | 4.16 | 4.40 | +5.7% | +5.8% | +0.1% |
| D | OJ | 12 → 10 | 3.89 | 4.36 | +11.8% | +11.1% | -0.7% |
| D | KC | 8 → 11 | 4.33 | 4.30 | -0.5% | +0.1% | +0.6% |
| T | 6B | 16 → 12 | 3.34 | 4.14 | **+24.1%** | +24.0% | -0.0% |
| T | 6N | 11 → 13 | 4.02 | 4.01 | -0.3% | -0.3% | +0.0% |
| D | KE | 14 → 14 | 3.67 | 3.98 | +8.4% | +9.6% | +1.1% |
| D | ZS | 17 → 15 | 3.31 | 3.79 | +14.6% | +15.3% | +0.6% |
| D | ZC | 20 → 16 | 2.93 | 3.69 | **+25.7%** | +27.0% | +1.0% |
| D | ZL | 13 → 17 | 3.85 | 3.57 | -7.3% | -6.5% | +0.8% |
| D | GC | 15 → 18 | 3.55 | 3.52 | -1.0% | -1.7% | -0.7% |
| D | SB | 18 → 19 | 3.02 | 2.99 | -0.8% | -0.9% | -0.2% |
| T | ZT | 19 → 20 | 2.93 | 2.86 | -2.5% | -1.9% | +0.6% |
| T | DX | 25 → 21 | 2.24 | 2.46 | +10.0% | +8.6% | -1.3% |
| T | ZF | 21 → 22 | 2.40 | 2.43 | +1.3% | +1.7% | +0.3% |
| T | 6J | 24 → 23 | 2.26 | 2.36 | +4.2% | +4.0% | -0.1% |
| D | RB | 22 → 24 | 2.29 | 2.30 | +0.2% | +0.2% | +0.0% |
| D | GF | 23 → 25 | 2.29 | 2.21 | -3.8% | -3.0% | +0.8% |
| T | ZB | 28 → 26 | 2.06 | 2.12 | +3.1% | +3.2% | +0.2% |
| D | HE | 26 → 27 | 2.13 | 2.11 | -1.2% | -1.4% | -0.2% |
| D | PL | 29 → 28 | 1.93 | 1.92 | -0.3% | -1.2% | -0.9% |
| T | 6E | 27 → 29 | 2.08 | 1.88 | -9.3% | -9.5% | -0.2% |
| D | PA | 30 → 30 | 1.90 | 1.80 | -5.2% | -5.5% | -0.3% |
| T | 6A | 31 → 31 | 1.78 | 1.75 | -1.4% | -1.4% | -0.0% |
| T | ZN | 32 → 32 | 1.70 | 1.71 | +0.2% | +0.5% | +0.3% |
| D | CC | 33 → 33 | 1.58 | 1.50 | -5.2% | -4.2% | +1.1% |
| D | SI | 34 → 34 | 1.44 | 1.35 | -6.4% | -6.9% | -0.6% |
| D | HO | 36 → 35 | 1.19 | 1.15 | -3.8% | -4.2% | -0.4% |
| T | ES | 38 → 36 | 1.09 | 1.08 | -1.3% | -0.9% | +0.5% |
| T | EMD | 35 → 37 | 1.24 | 1.07 | **-13.9%** | -13.6% | +0.4% |
| T | BTC | 37 → 38 | 1.14 | 1.05 | -7.7% | -8.7% | -1.1% |
| D | ZW | 39 → 39 | 1.05 | 0.96 | -8.9% | -8.0% | +1.0% |
| T | ETH | 40 → 40 | 0.95 | 0.91 | -5.0% | -6.3% | -1.4% |
| D | CL | 43 → 41 | 0.66 | 0.85 | **+28.5%** | +29.6% | +0.8% |
| D | NG | 42 → 42 | 0.78 | 0.80 | +1.7% | +1.5% | -0.2% |
| T | RTY | 41 → 43 | 0.79 | 0.78 | -1.3% | -1.3% | +0.0% |
| T | YM | 44 → 44 | 0.29 | 0.27 | -7.5% | -7.2% | +0.3% |
| T | NQ | 45 → 45 | 0.22 | 0.25 | +9.4% | +10.0% | +0.5% |

### 8.3 Lumber is the week's only large move, and it is real

Managed Money net long went from **755 to 1,954 contracts** against open interest of 6,938
rising to 8,203, so `|P_MM| / OI` went 0.109 to 0.238, more than doubling. `kV` was
effectively flat at 222.0 to 222.7 contracts per day. Working it through:

    T_21 = 1,410.1 / 222.04 = 6.35 days
    T_28 = 2,352.3 / 222.68 = 10.56 days

That is funds adding to a position in a market where a forced seller's whole daily budget
is about 222 contracts, and it takes lumber from 4th to 1st, displacing Class III milk.

**On the stress denominator it is much less dramatic**, 3.91 to 6.52 days, because lumber
trades 1.62x its calm volume on the worst decile of days. It is one of the 22 markets in §7
where stress is the *favourable* case, so the headline `T_sell` of 10.56 is the conservative
read and not the only one.

Nothing else moved more than 30%. The next four are WTI +28.5%, corn +25.7%, sterling
+24.1% and soybeans +14.6%, all of which move by 4 rank places or fewer.

### 8.4 Two markets crossed the thin-fund line, in opposite directions

| rpt | sym | `P_fragile` 21 → 28 | `|P|/OI` 21 → 28 | flag |
|---|---|---|---:|---|
| D | ZC | 56,713 → **126,776** | 0.0326 → **0.0730** | thin → **not thin** |
| D | HO | 13,381 → **11,246** | 0.0516 → **0.0451** | not thin → **thin** |

Membership is 7 in both weeks and it is not the same 7: `{CC, CL, DX, EMD, YM, ZC, ZW}`
becomes `{CC, CL, DX, EMD, HO, YM, ZW}`.

**Corn is the one that matters.** Managed Money net more than doubled on essentially
unchanged open interest (1,742,139 to 1,736,827), so a market that had no meaningful fragile
capital a week earlier now has some, and its `T_sell` of 3.69 days went from a well-formed
number with no subject to a number about something. That is the screen doing exactly the
work §4 describes, and it is the argument for recomputing the flag every week rather than
treating it as a property of the market.

---

## 9. What this document does not say

- **Nothing about returns.** `T` is a duration under an assumed participation rate, not a
  forecast. `kappa = 0.2` is configured judgement, and every figure scales inversely with it.
- **Nothing about cost.** Duration and cost are different questions and rank differently;
  see `docs/analysis/reproduce.py::exit_cost` and amendments A19 / A20.
- **Nothing about whether the week is unusual.** §8 adds exactly one week of history, which
  is enough to say the *ordering* is stable and nowhere near enough to say whether any
  *level* is high. `T` measured against its own history is the composite's `I` term and
  lives in [2026-07-28-composite.md](2026-07-28-composite.md), off the current-state store's
  1,051 weeks.
- **Nothing about the 327 unscoreable codes.** They are absent from the ranking, not scored
  as zero. `futures.coverage` is where that question belongs.

---

## Bottom line, in plain language

Forty-five futures markets can be scored this week out of 372 the two reports cover, and
every market that drops out drops because the workspace has no contract specification for
it, not because volume is missing. Of the forty-five, the ones where a forced seller would
take longest to get out are lumber at about ten and a half days, Class III milk at nine,
cotton at seven and live cattle at six: all small to mid-sized agricultural and livestock
markets where a fund position is large against how much trades in a day. The big financial
contracts sit at the bottom because they trade enormous volume relative to any position in
them. Seven markets have almost no fragile capital in them, so their number is arithmetic
without a subject, and WTI sits right on that line. The twenty financial-futures markets
cannot be read with the same template as the agricultural ones, and the five stock index
contracts among them should be ignored entirely, because their category positions are most
likely hedge legs rather than positions anyone can be forced out of. On a bad day the
picture shifts: cotton takes ten days instead of seven and the Treasury contracts all get
slower, while the stock index contracts get faster.

Compared with the week before, almost nothing changed. The same forty-five markets score,
the order is nearly identical, and a typical market's exit time moved about 5%. Trading
volumes barely moved at all, which is expected rather than lucky: the denominator is a
year-long average, so a single week cannot shift it. Anything that does change week to week
is funds changing their positions. The one real story is lumber, where funds roughly doubled
their net long into a market that trades about 1,100 contracts a day, taking its exit time
from six and a half days to ten and a half and making it the most crowded exit in the set.
Corn is worth watching for the opposite reason: a week earlier it had almost no fund money
in it and its number described nobody, and now it does.

On the data question, the answer is smaller than it looks and this document got it wrong on
the first pass. The positioning side needs one week of one CFTC report, about 1,900 rows,
five value columns, and it never touches the trader counts or the concentration columns.
**It does not need the point-in-time vintage store at all**: the ordinary current-state
files give byte-identical numbers for all 45 markets, and they carry twenty years of history
instead of eighteen months. The vintage store was reached for because it covers many more
markets, which is normally the right instinct and is useless here, since the markets it adds
are precisely the ones with no contract specification and so no volume, and they drop out
before any number is produced. What is genuinely scarce is the other half: the volume
denominator, five years of daily bars per market from a commercial subscription that cannot
be shared. Point-in-time data would matter if this were testing a rule as of a past date.
It is a description of one week, so it is not needed, and the one thing the vintage store
could have told us here, how much CFTC revises these numbers afterwards, it cannot, because
this week has been captured exactly once.
