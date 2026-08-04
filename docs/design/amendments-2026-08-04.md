# Spec amendments, 2026-08-04

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

Sections here carry a **`D` prefix**, per the per-day convention stated in
[README.md](README.md): "Each new file gets its own date and its own letter prefix (`B1`,
`C1`, ...)". [`amendments-2026-08-03.md`](amendments-2026-08-03.md) is closed at C30.
Cross-file references carry the date: `2026-08-03 §C30`.

> **Opening this file exposed a hole in the machinery that checks it.**
> `tests/test_references.py` matched section IDs with `[ABC]`, hardcoded, so the first
> amendment file of any new day would have defined nothing the resolver could see and every
> citation into it would have silently stopped being checked. Widened to `[A-Z]` in the same
> PR as `§D1`. It is the same failure the file exists to catch, one level up: a guard whose
> pattern stops matching passes every assertion above it.

---

## D1. Norgate carries two of the six backlog codes, and the four Henry Hub look-alikes do not exist

**§4 of [`../handoffs/2026-08-03-spec-backlog-producer.md`](../handoffs/2026-08-03-spec-backlog-producer.md)
answered.** That section named one genuine unknown, whether the vendor carries each requested
contract, and said it could not be settled from the Linux side. It can now: the human supplied
Norgate's own `FuturesContractDetails.xls`, the workbook the `contract_specs` table is built
from.

**The answer is the one §4 suspected, for exactly the codes it flagged.** The producer ask
drops from **six codes to two**.

| CFTC code | market | Norgate |
|---|---|---|
| `039601` | ROUGH RICE | **`ZR`, present** (CBOT) |
| `067411` | CRUDE OIL, LIGHT SWEET-WTI, ICE Futures Europe | **`WBS`, present** |
| `023A55` | HENRY HUB LAST DAY FIN, NYMEX | **absent** |
| `03565B` | HENRY HUB, NYMEX | **absent** |
| `023A56` | HENRY HUB PENULTIMATE FIN, NYMEX | **absent** |
| `03565C` | HENRY HUB PENULTIMATE NAT GAS, NYMEX | **absent** |

### The absence is enumerated, not searched for

A keyword search coming back empty is weak evidence about a vendor catalogue. This is not
that. **Norgate's entire energy universe is eight contracts**, so the four absences are read
off a complete list:

| code | name | exchange | status here |
|---|---|---|---|
| `CL` | Crude Oil | NYMEX | covered, `067651` |
| `HO` | NY Harbor ULSD | NYMEX | covered |
| `RB` | RBOB Gasoline | NYMEX | covered |
| `NG` | Henry Hub Natural Gas | NYMEX | covered, `023651` |
| `BRN` | Brent Crude Oil | ICE Europe | not requested |
| `WBS` | **WTI Crude Oil** | ICE Europe | **the tranche-1 head** |
| `GAS` | Low Sulphur Gasoil | ICE Europe | not requested |
| `GWM` | UK Natural Gas | ICE Europe | not requested |

Norgate lists **one** Henry Hub contract and it is `NG`, which is already covered. §4's rule
applies as written: report vendor-absent, substitute no proxy, and the four stay in the
backlog. §9.2's end state moves with them, from 51 covered markets to **47**, and `joinable`
from 53 of 55 to **49 of 51**.

`§C15`'s conclusion is untouched. It measured that these are a different holder base rather
than duplicates of `CL` and `NG`, and that remains why they are worth having. They are simply
not obtainable from this vendor.

### The workbook is the same source as the store, checked rather than assumed

Cross-checked against `$COTDATA_STORE/metadata/contract_specs.parquet`:

- **47 of 47** stored symbols appear in the workbook, none unmatched
- `Tick Value` and `Point Value` agree exactly on all 47, zero disagreements
- `Norgate_Symbol` follows `&<CODE>_CCB` on 47 of 47

So it is authoritative for the spec row rather than a marketing summary, and the two survivors
are both **USD**, which is what `ContractMaster.load()` refuses to assume:

| | `ZR` Rough Rice, CBOT | `WBS` WTI Crude Oil, ICE Europe |
|---|---|---|
| contract size | 2000 hundredweight | 1000 barrels |
| tick size / tick value | 0.5 cent / 10.0 | 1 cent / 10.0 |
| point value | **20.0** | **1000.0** |
| currency | USD | USD |

Neither has a registry entry yet; `cotdata/src/cotdata/registry.yaml` carries 49 symbols and
neither code is among them.

### What the workbook does NOT supply, and it is most of the job

The handoff's §3 asks for three artifacts per symbol. This settles the vendor question and
supplies most of one of them:

| artifact | supplied here? |
|---|---|
| `contract_specs` row | **partly.** Every column but `Margin`, which is not in the workbook. `contract_master.py` reads `float(row["Margin"])` and the stored table has zero nulls across 47 rows, so a null would be the first. Nothing in `src/` computes with margin, so it would not break a `D` |
| `unadj` series | **no.** Needs the subscription |
| `backadj` series | **no.** Needs the subscription, and `propadj` is derived from the pair, so both are the precondition for the one rung 4 wants |

`Contract Size` and `Tick Size` are prose in the workbook ("1000 barrels", "0.01 of a dollar")
where the store holds floats, so they are parsed rather than copied.

### An unsought finding: 58 contracts the store does not carry

The workbook lists 105 contracts against the store's 47. Two of the 58 extras are tranche-2
candidates the human dropped on 2026-08-03, and **vendor coverage is not why they were
dropped**: `RS` Canola and `MWE` Hard Red Spring Wheat are both available. If `§C17`'s flow
test is ever re-run on WHEAT-HRSpring, per §9.3's advice that it is the one worth revisiting,
the data exists.

The rest is mostly a block of CFTC-reported **financials** the backlog work never examined,
because `§C14` scoped itself to Disaggregated: `SR3` SOFR, `ZQ` fed funds, `UB`, `TN`, `VX`
and the four equity micros, among others. Those report on TFF, where `§C17`'s levered-holder
bar means something different and `§C18`'s within-complex benchmarking would have to be
re-derived. **Recorded, not proposed**: it is a different question from the one §C19 answered
and it should not be read as a third tranche.

### Reproducer

The workbook is a Norgate subscriber file and **cannot be committed**, for the same reason the
price store cannot: it is commercial and this repo is public. So the check is stated rather
than scripted, and it is two filters a subscriber can re-run in a minute:

    Group == "Energy"                  -> the eight rows above, complete
    Code in {"ZR", "WBS", "RS", "MWE"} -> present; no Henry Hub row but NG

The durable check is the one already written down in §5 of the handoff, against the store
after the run: `joinable` moves 47 of 49 to **49 of 51**, with `MFS` and `MME` still the two
unjoinable.

---

## D2. The raw `T` ranking is substantially a statement about market structure, not about this week

**Reproducer:** `docs/analysis/reproduce_single_number.py::d2_t_ranking_is_structural`.

[`../analysis/2026-07-28-exit-capacity.md`](../analysis/2026-07-28-exit-capacity.md) publishes
`T = Q / (kappa V)` as a cross-market ranking. That document is correct on every figure and its
§9 says plainly that it makes no claim about whether a week is unusual. The defect is editorial:
a table sorted by `T` descending is read as "where is the trouble", and that is not what it
answers.

Measured over the 45 markets that reach a live `dtl_sell`, week ending 2026-07-28:

| test | value |
|---|---|
| rank correlation, this week's `T` vs each market's own long-run median `T` | **0.639** |
| top-10 overlap, raw `T` vs 3-year percentile of own history | **3 of 10** |

Seven of the top ten change. Four markets sit in the raw top ten while running **below** their own
median:

| symbol | `T_now` | own median | vs own normal | 3y pctile | rank raw -> pctile |
|---|---:|---:|---:|---:|---:|
| LE live cattle | 6.084 | 8.789 | 0.692x | **0.204** | 4 -> **35** |
| OJ orange juice | 4.356 | 11.719 | **0.372x** | **0.191** | 10 -> **36** |
| DC Class III milk | 8.980 | 11.662 | 0.770x | 0.758 | 2 -> 18 |
| CT cotton | 7.120 | 9.986 | 0.713x | 0.815 | 3 -> 12 |

And the five markets at or above their own 3-year p90 are buried in the middle. Sterling is at
**1.000**, its highest exit time in three years and 2.29x its own median, and ranks **12th** on the
raw table:

| symbol | `T_now` | own median | vs own normal | 3y pctile | rank raw -> pctile |
|---|---:|---:|---:|---:|---:|
| 6B | 4.138 | 1.805 | 2.293x | **1.000** | 12 -> **1** |
| 6C | 5.614 | 1.776 | **3.161x** | 0.994 | 6 -> 2 |
| 6N | 4.012 | 2.523 | 1.590x | 0.975 | 13 -> 3 |
| 6S | 4.402 | 1.833 | 2.401x | 0.962 | 9 -> 4 |
| KE | 3.982 | 4.445 | 0.896x | 0.962 | 14 -> 4 |

**History is not the constraint.** All 45 markets carry at least 156 weeks; the median is 1,051 and
only lumber is short at 195. The percentile was available the whole time and was not used.

### What follows

**The level keeps exactly one job: a floor.** A percentile cannot say whether a level is trivial,
and this week exactly one market is affected. DJIA reads `D_sell_pct` 0.783 on a `T_sell` of **0.27
days**, and a quarter-session exit cannot be disorderly however unusual it is for that contract.
So: rank on the percentile, gate on the level. That is one number and one threshold, not two
numbers to reconcile.

**Not a correction to the analysis document.** `docs/analysis/` is point-in-time and never amended.
Its figures stand; this is the reading instruction that belongs beside them.

---

## D3. `T_sell / T_buy` **is** `Q_sell / Q_buy`, so a side-ratio index cannot see joint congestion

**Reproducer:** `docs/analysis/reproduce_single_number.py::d3_the_ratio_is_t_over_t`.

    T_sell / T_buy  =  [Q_sell / (kV)] / [Q_buy / (kV)]  =  Q_sell / Q_buy

The volume term cancels exactly. Checked on all 1,051 sterling weeks: max
`|T_sell/T_buy - Q_sell/Q_buy|` is **4.44e-16**.

This has a pleasant consequence and a fatal one. Pleasant: because the raw long and short sides are
always equal by zero-sum, the ratio is **size-free by construction** and is purely a statement about
holder composition. Fatal: it moves only when the two sides **diverge**, and it is blind to both
moving together.

Sterling on 2026-07-28 is that blind spot:

| | level | 3y pctile | share of 3y median |
|---|---:|---:|---:|
| `Q_sell` | 84,267 | **99.36** | **167%** |
| `Q_buy` | 47,071 | **98.09** | **196%** |
| `adv` | 101,825 | 12.10 | 93% |
| `T_sell` | 4.138 | **100.00** | 181% |
| `T_buy` | 2.311 | **98.09** | 214% |
| **ratio** | 1.790 | **25.48** | 83% |

Both weighted sides are at records and the ratio reads the 25th percentile, because the short side
grew *more* (196% of its median against 167%), so the ratio moved against the long side while the
long side set a record. Sterling's own 3-year median ratio is 2.17.

**The configuration where everyone is stuck at once is arguably the most dangerous one available,
and it is exactly the one a ratio divides out.** That is a stronger argument against a ratio
headline than any measurement of its behaviour.

---

## D4. "At-risk vs not-at-risk" is one series twice, and so is the Legacy pair it would be modelled on

**Reproducer:** `docs/analysis/reproduce_single_number.py::d4_the_partition_is_degenerate`.

The proposal was an index of leveraged / at-risk TFF categories against non-leveraged / not-at-risk
ones, by analogy with reading commercials against large specs in Legacy. It cannot work, and the
analogy is the reason rather than the defence.

Over 22,183 TFF market-weeks:

    at_risk_net + not_at_risk_net  =  0.0000   (max, not mean)
    corr(at_risk_net, not_at_risk_net) = -1.0000000000

Futures are zero-sum, so **any** partition of the five categories into two groups gives `A = -B`
exactly. The comparison contributes nothing. This is the same trap
[`../../src/crowdmon/futures/fragility.py`](../../src/crowdmon/futures/fragility.py) already
documents for `Phi`: nets sum to zero across categories, so a weighted net is not a share of
anything.

Excluding the two small categories buys a little independence and not much. Across the 24 markets
with at least 156 weeks, `corr(leveraged, dealer + asset_manager)` has a median of **-0.919**,
range -0.978 to -0.397.

**The analogy is the finding.** Across 303 Legacy markets, `corr(commercial, noncommercial)` has a
median of **-0.9939**, with 90% of markets below -0.854. The comms-versus-specs pair that everyone
already reads is *also* one series printed twice. The redundancy is not introduced by the proposal;
it is inherited from the convention, and two lines on a chart look like two pieces of information.

### What is non-degenerate: one index per SIDE, not per camp

Sterling, its record week:

| week | lev idx | non-lev idx | `T_sell` idx | `T_buy` idx |
|---|---:|---:|---:|---:|
| 2026-07-07 | 14.6 | 87.3 | 97.5 | 98.7 |
| 2026-07-21 | 36.3 | 62.4 | 92.4 | 86.6 |
| **2026-07-28** | **45.9** | **62.4** | **100.0** | **98.1** |

    corr(lev idx, non-lev idx)   = -0.9396   mirrors
    corr(T_sell idx, T_buy idx)  = +0.6723   not mirrors

On its most congested week on record, the category pair reads **46 and 62** and notices nothing.
The two side indices read **100 and 98**. A category net is a difference and stays mid-range while
both sides' weighted exposure goes to a record; and unlike the ratio in §D3, two side indices *can*
both be maxed, which is the whole point.

---

## D5. `Phi` is NOT inert in `D`, which refutes the suspicion that prompted the test

**Reproducer:** `docs/analysis/reproduce_single_number.py::d5_phi_is_not_inert`.

`2026-08-01 §A22` and `2026-08-03 §C8` establish that `Phi` carries no signal independent of the
weights, and its within-market standard deviation is 0.082 against roughly 0.29 for the two
percentile terms beside it. The reasonable suspicion was that percentile-ising something that
stable amplifies noise, or does nothing at all once `D` is itself percentile-ised per market.
**Both are wrong.** Over 32,079 market-weeks and 46 markets:

| side | corr(`D2_pct`, `D3_pct`) | rank corr | median abs diff | 90th pct abs diff |
|---|---:|---:|---:|---:|
| sell | 0.8059 | 0.8069 | 0.0892 | **0.3121** |
| buy | 0.8438 | 0.8453 | 0.0764 | 0.2803 |

where `D2 = C x I` and `D3 = C x I x Phi`, each percentile-ised within its own market. In one week
in ten, including `Phi` moves the published percentile by more than 0.3.

It is structural rather than jitter:

| term | median lag-1 autocorrelation | within-market sd |
|---|---:|---:|
| `pct(Phi)` | **0.888** | 0.306 |
| `C` | 0.950 | 0.311 |
| `I` | 0.947 | 0.303 |

And it reorders substantially: latest-week top-10 overlap **5 of 10** (sell) and 8 of 10 (buy), and
across all 742 weeks the top-5 overlap averages **2.47 of 5**.

### What this does not say

It does not say `Phi` belongs there. There is no outcome to score against, so `Phi` could be
systematically improving or systematically degrading the number and this comparison cannot
distinguish them. The same session proposed the removal and ran the test, which is the arrangement
workspace governance separates for a reason.

**What survives from `§A22` and `§C8` is the interpretation, not a prediction of inertness:** the
0.31 of reordering is the weight table talking. Whether that is a feature turns on whether the
weights are believed, and they are configured judgement, deliberately never fitted.

**Do not drop `Phi` on the strength of this.** It is doing too much for a change that cannot be
justified by measurement, and removing a term because it is inconvenient to explain is the wrong
reason.

---

## D6. `Phi`'s effect on `D_pct` is not monotone, so a lone percentile is uninterpretable

**Reproducer:** `docs/analysis/reproduce_single_number.py::d6_phi_is_not_monotone`.

Week ending 2026-07-28:

| | `C` | `I` | `pct(Phi)` | `D2_pct` | `D3_pct` | effect |
|---|---:|---:|---:|---:|---:|---:|
| ZC corn | 0.930 | 0.841 | **0.395** | 0.917 | 0.955 | **+0.038** |
| 6B sterling | 0.420 | 1.000 | **0.376** | 0.707 | 0.611 | **-0.096** |
| 6C CAD | 0.389 | 0.994 | 0.739 | 0.771 | 0.885 | +0.115 |
| YM DJIA | 0.752 | 0.516 | 0.287 | 0.796 | 0.783 | -0.013 |

Corn and sterling both carry a **below-median** `pct(Phi)` and it moves them in **opposite
directions**, because the percentile of a product is not monotone in each factor's percentile: what
matters is the market's own joint history of the three terms, not this week's value of one of them.

**Consequence, and it is a hard one: "more fragile means more damage" is not a sentence anyone may
write.** A single `D_pct` therefore cannot be interpreted even by a reader who knows the formula.

Sterling is also the case that shows the composite behaving well. Its `I` is 1.000, a record exit
time, and `D_sell_pct` is only 0.611, because `C` is 0.420: the levered book is mid-range and, per
§D8, half of `Q_sell` is the dealer book. **`D` correctly discounts a record `T` when the crowd
driving it is not the fragile crowd.** Without the factors published that reads as the measure
missing something; with them it reads as the measure working.

### Acted on, same day

`composite.damage_block` and `futures.report.format_damage_block` publish `C`, `I` and `pct(Phi)`
beside `D_pct` on every render, with the multiplication written out, the raw `T` in days for the
§D2 floor, and explicit denials of the probability and monotonicity readings. Five fixture tests in
[`../../tests/test_composite.py`](../../tests/test_composite.py) pin it, one of them asserting the
denial text is present so it cannot be edited out silently. Bands are deliberately coarse: `D_pct`
is a percentile of a product of percentiles and a two-decimal label implies precision the
construction does not have.

---

## D7. Legacy and TFF agree on exactly two quantities, and neither is a category

**Reproducer:** `docs/analysis/reproduce_single_number.py::d7_legacy_and_tff_share_two_things`.

Over 6,279 overlapping market-weeks:

| test | result |
|---|---|
| `open_interest` identical | **100.0000%**, max difference **0** |
| `nonreportable` long identical | **100.0000%** |
| `nonreportable` short identical | **100.0000%** |
| TFF category sum == Legacy category sum | 34.6% |
| `dealer` == `commercial` | **15.3%** long, 14.5% short |
| `asset_manager + leveraged + other_reportable` == `noncommercial` | **15.6%** long, 15.8% short |

So the two reports describe the same pool of contracts and agree exactly on where the
reportable line falls. Above that line, the obvious mapping fails about 85% of the time, for two
compounding reasons.

**Spreading is counted differently.** Legacy breaks out spreading only for non-commercial traders
and nets commercial spreading into long and short; TFF breaks it out for every category. Canadian
dollar, 2026-07-28, open interest 372,447:

    TFF     long 348,849 + spread 23,598 = 372,447   residual 0
    Legacy  long 362,728 + spread      0 = 362,728   residual 9,719
    gap between the two long totals     = 13,879 = 23,598 - 9,719

exact to the contract. Note that cotdata's `canonicalize_legacy` sets `spread_contracts` to `NA`
on every row, so the Legacy 9,719 is **derived as the identity residual, not read**. Summing an
all-null column returns 0, which would print as a measurement of zero spreading and is not one.
Store-wide: the identity `long + spread == OI` closes on **99.984%** of TFF market-weeks and
**19.857%** of Legacy ones, median residual 912.

**The traders in each bucket are different people, and this is the reason no correction recovers
the mapping.** If Legacy's `noncommercial` were the same traders as TFF's buy side, their spreading
would match:

    Legacy non-commercial spreading (derived)          =  9,719
    TFF asset_manager + leveraged + other_reportable   = 15,278

### What follows

**Any quantity built by subtracting one report's category from another's mixes a classification
difference with a spreading-convention difference, and neither is recoverable from published data.**
Same shape as the Supplemental trap in the root `CLAUDE.md`: Index Traders does not nest inside
Disaggregated's Swap Dealer. The only quantities that carry across are open interest and
`nonreportable`.

This also puts numbers behind two claims `core/config.py` and `io.from_current_store` already make
about refusing Legacy. Its `noncommercial` bucket would fuse `leveraged` at weight 1.0 with
`asset_manager` at 0.3, which in sterling this week are -102,495 and -101,160: two positions within
1.3% of each other in size and opposite in forceability. And `Phi`'s denominator would hold
contracts its numerator cannot see on 80% of market-weeks.

---

## D8. Sterling: the levered book and Legacy non-commercial point opposite ways, 12 weeks running

**Reproducer:** `docs/analysis/reproduce_single_number.py::d8_sterling_sign_conflict`.

Legacy reports non-commercial in sterling net **short 64,814** contracts on 2026-07-28. Leveraged
funds are net **long 41,097**. The short is institutional: asset managers at -140,911.

This is not a one-week artifact. The sign conflict holds in **all 12 of the last 12 weeks** and in
**57 of the 82 weeks** the vintage store holds (69.5%).

It is the sharpest available demonstration of §D7: a Legacy reader is not merely missing detail,
they are pointed at the wrong side of the market, because Legacy nets a large institutional short
against a smaller levered long and reports one negative number.

### The caveat, and it belongs beside the finding

`Q_sell` decomposes as:

    dealer            107,350 x 0.4 =  42,940.0    51.0% of Q_sell
    leveraged          41,097 x 1.0 =  41,097.0    48.8%
    other_reportable      460 x 0.5 =     230.0     0.3%
                                       --------
                                        84,267.0

**Half of sterling's record `T_sell` is the dealer book at weight 0.4**, not a levered-fund crowd.
The sign contradiction is untouched by this, and it is the claim worth making. The supporting
duration figure needs the caveat, and §D6 shows the composite already applying it: `D_sell_pct`
reads 0.611 rather than tracking the 1.000 illiquidity term.

---

## D9. The offside term is built, and it belongs beside `D` rather than inside it

**Reproducer:** `docs/analysis/reproduce_single_number.py::d9_offside_is_beside_not_inside`.

The framing that prompted this: crowding has three parts, **lopsided, offside, trapped**. `D`
has `C` for lopsided and `I` for trapped and nothing for offside. `trigger.py` has computed
`F*` since it was written, and **nothing consumed it**: `alignment.py` and `reflexivity.py`
import it, `composite.py` does not.

`trigger.nearest_trigger` and `trigger.add_trigger_distance` now supply it, and
`composite.damage_block` publishes it beside `D_pct`.

### The side convention, which is the one error that would look plausible

A signal currently **long** flips **down**, so its pool becomes a forced **seller** and it
lands on the `sell` side beside `Q_sell`, `T_sell` and `damage_sell`. A signal currently short
flips up and is a forced buyer. Pairing a trigger with the opposite side's severity produces
entirely reasonable-looking numbers, so it is asserted in
[`../../tests/test_composite.py`](../../tests/test_composite.py) rather than left to review.

### The unit is daily sigma, because a percentage does not travel

A 3% move is a routine day in natural gas and a large one in 2-year notes. Distance divided by
daily sigma is "how many ordinary days of movement until the rules fire". Measured on 45
markets, week ending 2026-07-28:

| | count |
|---|---|
| with a forced-**sell** trigger | **37** of 45 |
| with a forced-**buy** trigger | **35** of 45 |
| **horizons disagree** (both exist) | **27** of 45 |

Distance to the nearest forced-sell trigger: median **1.8 sigma**, p10 0.6, p90 8.0.

That 27 of 45 is the module's own claim, measured across the universe for the first time:
"the trend book in gold" is not one pool with one trigger in 60% of markets.

### The distance is the trailing return, and that is an identity

Since `F* = F_{t-k}`, the move required to reach the flip is exactly the `k`-day return that
has already happened:

    move_from_spot = F_{t-k}/F_t - 1 = -r_k / (1 + r_k)

Verified to six decimals on every lookback of every market checked. **So the trigger distance
carries no price information beyond trailing momentum.** What it adds is the mapping: which
pool, on which side, is mechanically forced at that level, and how large it is. That is the
part positioning data supplies and a price chart does not.

### Why it is not a fourth multiplicand

Two reasons, and the first is the governing one.

**A.10.** `D` is a conditional severity: the appendix states `D ⊥ E[r_{t+1}]` and
`D → skew, ES`. It answers "how bad if forced" and deliberately refuses "when". A distance to
the flip answers only "how close". Multiplying them turns `D` into an unconditional quantity,
which is precisely what A.10 declines to produce.

**It would double-count `C`.** Because the distance is the trailing return and positioning
extremity is downstream of the same trend, the two co-move:

| | corr | rank corr |
|---|---:|---:|
| `crowding_long` | **-0.4811** | -0.4560 |
| `illiquidity_sell` | -0.2346 | -0.1575 |
| `damage_sell_pct` | -0.2174 | -0.1617 |
| `fragility` | +0.1134 | +0.2791 |

A fourth factor would compound one signal twice, which is the same defect as fragility sitting
inside both `I` and `Phi` (§D5). There is no reason to add a third instance knowingly.

> **CORRECTED in the same session, before it shipped.** A first pass measured
> `corr(distance, damage_sell_pct) = -0.017` and concluded the two were **orthogonal**, which
> would have been a different and stronger argument. That figure was an artifact: it read
> triggers at the **latest price bar** and positioning at the **report date**, three days
> apart. Measured consistently at `as_of = report_date` it is **-0.217**, and gasoline moves
> from 1.29 sigma to 4.8 sigma between the two readings. The decision does not rest on
> independence and never did; the doctrinal reason above is sufficient on its own.

### What is preserved by keeping them separate: the quadrant

| | not severe | severe |
|---|---:|---:|
| **not close** | 16 | 5 |
| **close** | 10 | **4** |

Close and severe, week ending 2026-07-28: **corn** (0.25 sigma, `D_sell_pct` 0.955),
**soybean meal** (0.64, 0.803), **Class III milk** (1.10, 0.764) and **DJIA** (0.93, 0.783).
A product collapses all four cells into one scalar, and close-and-harmless is a genuinely
different state from far-and-severe.

**§D2's level floor still binds and this shows why.** DJIA sits in the close-and-severe cell on
a `T_sell` of **0.27 days**. The quadrant ranks; the level gates.

### A bug the tests found

`trigger_prices` accessed `["Close"]` on whatever `cotdata.get_prices` returned, so a symbol
the store does not carry raised a bare `KeyError('Close')` and killed the caller mid-run. That
matters because `add_trigger_distance` iterates over whatever symbols a frame holds, and the
coverage ladder is explicit that markets die at the price join: one unresolvable symbol should
null one row, not abort the panel. It now raises `TriggerError` with the reason, and
`add_trigger_distance` catches it per symbol.

---

## D10. The trigger side came from the price signal, and the observed pool disagrees a third of the time

**Reproducer:** `docs/analysis/reproduce_single_number.py::d10_pool_versus_signal`.

**A defect in §D9, found within the hour by rendering two markets by hand.**

`trigger.py`'s whole departure from §A.7 is that the pool is **observed rather than
modelled**: §A.7 estimates forced flow from a replicated CTA book with an aggregate capital
term `A`, and this package refuses to guess `A` and reads the Managed Money / leveraged net
from COT instead. §D9's `nearest_trigger` then took the **side** from the price signal alone,
which quietly reintroduced the modelled logic the module exists to avoid.

Measured on 45 markets by 3 horizons, week ending 2026-07-28:

| horizon | observed pool sign agrees with the trend signal |
|---|---:|
| 20d | **64.4%** |
| 60d | **57.8%** |
| 250d | 75.6% |
| **pooled** | **65.9%** of 135 pairs |

Three markets (**WHEAT-SRW, DJIA, USD INDEX**) have the pool opposite the signal on **every**
horizon.

### What that does to a reading

Canadian dollar is the worked case. Leveraged funds are net **short 102,495** contracts while
the **20-day signal is long**, so the nearest "forced selling" level sits 2.4 sigma away and
describes a long book that **is not there**. The level is real; the pool it would force is
not.

Lumber is the counter-case and shows the flag is not merely pessimistic: Managed Money is net
**long 1,954** and the 20-day signal is long, so its 0.8-sigma forced-sell trigger is a level
at which an actually-held book gets forced.

### Fixed

`nearest_trigger` takes an optional `pool_net` and `add_trigger_distance` an optional
`pool_column`, producing `trigger_{side}_pool_agrees` as a **tri-state**: `True`, `False`, or
`None` for "no pool supplied". Collapsing the last two would be a real error, because "the
pool is on the other side" and "nobody checked" carry opposite implications.

`report.format_offside` prints the disagreement and **suppresses the quadrant** when it fires,
because labelling such a row CLOSE and SEVERE is precisely wrong.

### Also fixed, same pass: a null `D_pct` rendered a broken sentence

`format_damage_block` interpolated an empty percentage, producing "of the last 3 years of
weeks in this market,  looked less dangerous". Lumber is the live case, and it is worth having
rather than an edge case: `C = pct(z)` stacks two three-year windows and needs six years of
prices, lumber has four, so `I` (0.777) and `Phi` (0.599) exist and `D` cannot be formed. An
unscored row now names which factor is null and says the surviving factors are readable on
their own.

**The general lesson is about where the check belonged.** Both defects were invisible to the
fixture tests and to the panel-level reproducer, and both appeared immediately on rendering
**two named markets by hand**. A per-market block is the level at which a reader meets the
output, and it is therefore the level at which nonsense shows up.
## D11. The tranche landed: 47 covered markets, the gate still passes, and four print statements had gone stale

**§6 of [`../handoffs/2026-08-03-spec-backlog-producer.md`](../handoffs/2026-08-03-spec-backlog-producer.md)
executed**, once the producer run wrote `ZR` and `WBS` (cotdata #99 plus
`cotdata-update --metadata --prices`). New point-in-time record:
[`../analysis/2026-08-04-contract-spec-inventory.md`](../analysis/2026-08-04-contract-spec-inventory.md).
Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`.
Pinned live in
[`../../tests/test_contract_master_live.py`](../../tests/test_contract_master_live.py).

### What moved

| | before | after |
|---|---|---|
| covered markets, latest week | 45 | **47** |
| Disaggregated / TFF, latest week | 25 / 20 | **27** / 20 |
| registry symbols | 49 | **51** |
| `joinable` | 47 of 49 | **49 of 51** |
| backlog, real outright | 34 | **32** |

The certificate count (213) and the differential count (7) are **identical on both dates**,
which is the check that the two rows came out of the backlog population rather than out of
some other one.

### The gate still passes, and the interesting number is the one that did not move

| | before | after |
|---|---|---|
| covered stratum | 25 of 25 real outright | **27 of 27** |
| power / gas / carbon inside coverage | 0 | **0** |
| always-template markets inside (`2026-08-02 §B36`) | 7 of 7 | **7 of 7** |
| median \|P_MM\|/OI, covered | 0.1371 | **0.1371** |
| median \|P_MM\|/OI, uncovered | 0.0370 | **0.0364** |

**The covered median is unchanged to four decimal places.** Rough rice was selected on a
Managed Money share of 0.433, the highest of any backlog candidate measured, and ICE Europe
WTI on a holder base measurably unlike `CL`'s (`2026-08-03 §C15`). Adding one market far above
the median and one energy market, where energy is thin on this term everywhere (`§B33`), moved
the median of 27 markets not at all. That is what a median does, and the reading is that the
covered set's **character** is unchanged rather than that the additions were inert. Anyone
tempted to use this statistic to detect a coverage change should not: it is chosen for
robustness and it is robust.

### Four print statements had gone stale, and they contradicted their own output

`contract_spec_inventory` hardcoded figures that were current when written:

| printed | computed directly above it |
|---|---|
| `26 + 21 = 47 is the whole contract_specs table` | `TOTAL 49 47` |
| `25 of 25 are classic outright` | `covered stratum: {'real outright': 27}` |
| `nearer 23 instruments than 34` | 32 real outright |
| `[§C5 pinned 25 / 254]` | `covered 27, uncovered 252` |

All four now derive from what the function computed, and the `§C5` pin is labelled with the
date it was taken. This is the house rule about not restating a measured figure as a literal
in a report string, arriving as a **bug rather than as a style note**: a reproducer whose
prose disagrees with its own table is worse than one with no prose, because the reader has to
work out which half to believe.

The `26 + 21 = 47` form had a second problem worth naming. It was an **arithmetic** argument
that nothing spec'd is stranded, and it worked only while the registry and the spec table had
the same length. They no longer do (51 against 49). It is now a **set** identity, printed in
both directions:

```
symbols on a panel 49, joinable 49, registry 51;
  joinable-but-unseen [], seen-but-unjoinable []
```

`MFS` and `MME` are in neither set: no spec, and not on either vintage panel.

### Open interest has now failed as a backlog ordering three times

`§C14` ranked the backlog by open interest, which put the Henry Hub complex at the head.
`§C18` then found the levered-holder bar must be applied within complex rather than pooled,
which moved rough rice, the **smallest** candidate, to the top. `§D1` now removes the four
largest entries entirely, because the vendor does not carry them. The remaining head of the
list by open interest is `06765T` Brent last day and `06765A` WTI financial, the latter with
175,418 mean OI and a median Managed Money net of **475 contracts**.

### One instruction in §6 pointed at a file that never carried the number

§6 says to update the covered-universe count in "`CLAUDE.md` and `docs/handoffs/README.md`,
both of which now say 45". `CLAUDE.md` does not, and never did: the count lives in the
handoffs README (two rows) and in the analysis documents. Recorded because a session that
takes the instruction literally goes looking for a number that is not there, and either edits
something adjacent or concludes the instruction is stale in some larger way. Both rows are
updated, and the completed step-2 row is **annotated rather than rewritten**, since its
figures are the correct record of what `§C12` measured on 2026-07-28.
---

## D12. The trigger is a moving level, and a net-basis Legacy/TFF comparison isolates reclassification

**Reproducer:** `docs/analysis/reproduce_single_number.py::d12_drift_and_net_reconciliation`.

> **§D11 is deliberately skipped, not missing.** It is taken by an in-flight branch
> (crowdmon#63) that had not merged when this was written. Four counter collisions have
> already happened in this repo and the convention only says who renumbers *after* one; here
> the number was visibly claimed, so reserving it costs nothing and avoids a fifth. If #63 is
> abandoned, D11 stays unused and this note explains the gap.

Four clarifications that came out of writing up §D9's trigger term for a non-technical
audience. None changes a number already published; all four are things a reader would
otherwise get wrong.

### 1. It is time-series momentum, not a breakout

`F* = F_{t-k}` compares today's price to **one bar**, the close exactly `k` sessions back. A
breakout compares against the **extreme of a window**. On 6C, 2026-07-28, they are different
levels:

| | level | from spot |
|---|---:|---:|
| spot | 0.71050 | |
| **TSMOM trigger `F_(t-250)`** | **0.73993** | **+4.14%** |
| Donchian 250d high | 0.74826 | +5.31% |
| Donchian 250d low | 0.70500 | -0.77% |

There is no breakout logic anywhere in `src/`; `alignment.py` uses the same TSMOM.

### 2. The level drifts on its own, so it is a snapshot rather than a countdown

Because the reference is a single rolling bar, the trigger moves even when price does not.
Measured on 6C over 120 sessions:

| | daily sd | max daily move |
|---|---:|---:|
| reference bar `F_(t-250)` | **0.4256%** | 1.71% |
| spot `F_t` | 0.2540% | 0.77% |

**The reference bar moves 1.68x as much as spot**, so most of the variation in
distance-to-trigger is last year's bars rolling off rather than price approaching a level.
The last ten sessions ran 4.19, 3.87, 3.77, 4.45, 5.39, 5.29, 4.91, 4.51, 4.55, 4.14 percent.

This matters for how the number is quoted. "4% away, 17 days of movement" reads as a
countdown and is not one: it can close without the market doing anything.

### 3. The rule reverses, it does not exit, so there are three "days" figures

`s = sign(F_t - F_{t-k})` is always in the market. A flip is `Δs = 2`, not 1, which is why
`trigger_block` has always reported `flow_close` and `flow_reverse` and picks neither. The
consequence for a reader of `damage_block` is that three durations are in play and they are
not interchangeable:

| | contracts | days at `kV = 15,609` |
|---|---:|---:|
| whole fragility-weighted short side (`T_buy`) | 140,470 | **9.00** |
| the levered pool alone, goes flat | 102,495 | 6.57 |
| the levered pool alone, reverses | 204,990 | 13.13 |

`T_buy` covers every short-side category weighted by forceability. The **trigger fires only
the trend-following slice of the levered book.** Quoting `T_buy` beside a trigger distance
therefore describes two different populations, which is fine as long as it is said.

### 4. On NETS, the Legacy/TFF comparison is spreading-clean

`§D7` measured that the two reports agree on open interest and non-reportables and on nothing
else, with two compounding causes: different spreading conventions and different trader
classification. **A net comparison removes the first.** A spread position is equal long and
short, so it nets to zero and sits in its own column in both reports.

6C, 2026-07-28:

| | value |
|---|---:|
| non-reportable, Legacy vs TFF | -12,711 vs -12,711, **diff 0** |
| Legacy non-commercial | -176,310 |
| vs asset managers + leveraged | -203,655, **diff +27,345 (15.5%)** |
| vs asset managers + leveraged + other reportables | -192,796, **diff +16,486 (9.4%)** |
| Legacy commercial | +189,021 |
| vs dealer | +205,507, **diff -16,486** |

The two discrepancies are **exactly equal and opposite at 16,486**, which is the floor under
any two-way grouping. So on this market **16,486 contracts of net position are classified on
opposite sides of the line by the two reports**, with no spreading confound mixed in.

**The practical rule this gives a reader**, which `§D7` could state only loosely: Legacy's
speculative short reads roughly **9% smaller** than TFF's comparable grouping. Anyone
presenting the two side by side should say they do not reconcile, because the subtraction is
the first thing a reader tries.
