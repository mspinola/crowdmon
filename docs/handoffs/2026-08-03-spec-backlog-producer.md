# Handoff: contract specs for the §C14 backlog

**Status:** **COMPLETE 2026-08-04 (§12).** §4 was answered from the vendor catalogue (§11): Norgate carries only `039601` rough rice and `067411` ICE Europe WTI, and the four Henry Hub codes are vendor-absent and stay in the backlog. Both landed via cotdata #99 plus the producer run, `joinable` is **49 of 51** and covered markets **45 -> 47**. §6's follow-up is executed. Findings `2026-08-04 §D1`, `§D11`
**Date:** 2026-08-03
**Target:** whoever runs the Norgate producer, plus a follow-up `crowdmon` session
**Depends on:** PR #46 (the inventory that identified these codes)
**Evidence:** [`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C14-§C19
**Reproducer:** `../analysis/reproduce.py::variant_codes_are_not_duplicates`, `::backlog_priority_within_complex`

> **Two tranches. §1-§7 are the five energy codes and were written first; §8 is the ag and
> dairy tranche, appended later.** The title of this file said "ICE Europe WTI and the Henry
> Hub complex" while §1-§7 were the whole of it; it is broadened here because a single
> producer run covers both and the operator should not have to find two documents.
>
> **The producer ask is SIX codes: §1's five, plus `039601` rough rice.** §8 ranked four ag
> candidates and **§9 records the decision to take only the first**, so read §9 before acting
> on §8's table. §9.2 supersedes §5's expected counts, which were written for tranche 1 alone.
>
> **§8.3 corrects a statistic §2 leads with**, so read it before quoting §2's table, and
> **§10.1 corrects the BAR §8 uses**, which would have condemned four of §1's five codes.
> §10 tests the remaining 24 backlog codes and proposes no third tranche; all six committed
> codes pass, so §1, §8 and §9 stand unchanged.

---

## 0. What is being asked for, and what is NOT

Add five CFTC market codes to crowdmon's covered universe, taking it from 45 markets to 50.
They are the head of the §C14 backlog by open interest.

**This handoff writes no code and changes no coverage.** Every one of the three artifacts
required per symbol comes from the Norgate producer, which runs on the Windows box only. It
is filed here so the producer run is mechanical and checkable rather than exploratory, and so
the next `crowdmon` session finds a claim rather than starting the analysis over.

**Do not add the registry entries ahead of the producer run.** §C15 records the reason with a
worked example: `MME` and `MFS` are registry symbols with `norgate: null`, and they report
`missing: specs,unadj_price,backadj_price` and are invisible to coverage. Five more inert
rows would look like progress and change nothing.

## 1. The five codes

| CFTC code | market name | mean OI | proposed symbol |
|---|---|---|---|
| `067411` | CRUDE OIL, LIGHT SWEET-WTI, ICE Futures Europe | 798,670 | `CLI` |
| `023A55` | HENRY HUB LAST DAY FIN, NYMEX | 420,336 | `HHL` |
| `03565B` | HENRY HUB, NYMEX | 362,655 | `HH` |
| `023A56` | HENRY HUB PENULTIMATE FIN, NYMEX | 253,028 | `HHPF` |
| `03565C` | HENRY HUB PENULTIMATE NAT GAS, NYMEX | 153,896 | `HHP` |

Symbols are **proposals, not decisions.** They must not collide with the 49 existing registry
symbols, and `HH` in particular is short enough to be worth a second look. The registry is
`cotdata/src/cotdata/registry.yaml`, grouped by asset class; these belong under `Energies`
beside `CL`, `RB`, `HO`, `NG`.

## 2. Why these five, and the objection that was raised and withdrawn

They look like variants of two already-covered flagships (`067651` NYMEX WTI as `CL`,
`023651` NAT GAS NYME as `NG`), and §C14 had advised settling micro gold before the large
backlog items precisely because a variant code duplicates a covered market.

**That objection was raised against this request and does not survive measurement.** Over the
82 vintage weeks, Managed Money net positioning correlates **negatively** with the flagship in
all five cases and week-to-week flow is near zero:

| code | `r(OI)` | `r(MM net)` | `r(ΔMM)` |
|---|---|---|---|
| `067411` | 0.771 | **-0.224** | -0.054 |
| `023A55` | -0.097 | **-0.643** | -0.164 |
| `023A56` | -0.146 | -0.413 | -0.063 |
| `03565B` | 0.179 | **-0.621** | -0.116 |
| `03565C` | -0.424 | -0.128 | -0.234 |

Open interest tracks, which is what makes them look like duplicates; positioning does not, and
positioning is the series crowding is a property of. Detail and the general lesson in §C15.

## 3. What the producer must write, per symbol

All three, or the symbol stays invisible. `coverage()` reports `joinable` only when all are
present, and each has a distinct consumer:

| artifact | needed by | note |
|---|---|---|
| `contract_specs` row | `ContractMaster` | point value, tick size, tick value, currency, margin, exchange, group. Written by the producer's `--metadata` flag |
| `unadj` price series | `notional.py` (rung 3) | refuses anything else. Back-adjusted notional is wrong by +294% on gold in 2002 and **exactly 0% today** |
| `backadj` price series | `riskunits.py` (rung 4), indirectly | `propadj` is **derived on read from the unadj/backadj pair** (`cotdata.prices._ratio_adjust`), so both stored tiers are the precondition for the one derived tier |

**Currency must be USD or `ContractMaster.load()` raises.** All 47 current specs are USD,
which is what removes an FX layer from rung 3. ICE Europe WTI is USD-denominated, so this
should hold, but it is asserted rather than assumed and a non-USD row fails loudly rather than
producing a USD-labelled number that is not USD.

## 4. The step that has to happen first

**Confirm Norgate carries each of the five.** This is not known from the Linux side and is the
one genuine unknown in this handoff. The financially-settled Henry Hub look-alikes
(`023A55`, `023A56`, `03565C`) are the doubtful ones: Norgate's futures universe is built
around liquid outrights, and a cash-settled look-alike may simply be absent.

If Norgate does not carry a given contract, **do not substitute a proxy.** `MME`/`MFS` are
priced off ETF proxies via yahoo, which is defensible for an index and is not for these: the
whole point of a financially-settled look-alike is that it differs from the benchmark it
settles against, so pricing it off the benchmark would erase the thing being measured. Report
it as vendor-absent and it stays in the backlog.

## 5. Verification, after the producer run

From a `crowdmon` checkout against the real store:

```
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python -c "
from crowdmon.futures import ContractMaster
cov = ContractMaster.load().coverage()
print(cov[~cov['joinable']][['symbol','cftc_code','missing']].to_string(index=False))
print('joinable:', int(cov['joinable'].sum()), 'of', len(cov))
"
```

Expected before: `joinable: 47 of 49`, with `MFS` and `MME` unjoinable.
Expected after all five land: `joinable: 52 of 54`, same two unjoinable.

Then re-run the inventory and confirm the covered count moves 45 -> 50:

```
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce.py
```

## 6. What the follow-up `crowdmon` session owns

Only once the artifacts exist:

- Re-run `contract_spec_inventory` and **write a new dated file** in `docs/analysis/`. The
  existing `2026-07-28-contract-spec-inventory.md` is point-in-time and must not be amended.
- Update the covered-universe count in `CLAUDE.md` and `docs/handoffs/README.md`, both of
  which now say 45.
- Re-measure the four suite figures rather than adjusting them by hand. They were found stale
  by +2 in PR #46 and adding live assertions for new markets will move them again.
- Check `continuity.py`: `03565B` and `023651` are both Henry Hub natural gas on NYMEX under
  different codes, and whether they are one instrument or two is a question that module exists
  to answer. §C15 says their holder bases differ, which is evidence for two, not proof.

## 7. What this does NOT unblock

The other two standing energy blocks are untouched. Price limits still have no table anywhere
in the workspace, so §8's `V = 0` treatment for a limit day remains unimplementable, and
§379's OI migration is still blocked because the price frame's `Open Interest` is whole-market
(`2026-08-02 §B19`). Adding these five improves breadth and neither of those.

Nor does it change the §10 validation verdict. That closed `uninformative` on spent episodes,
and new markets supply no new clean episodes for weeks that have already happened.

---

# §8. Second tranche, appended 2026-08-03: the ag and dairy backlog

**Appended after the body above was written, not an edit to it.** §1-§7 concern the five
energy codes. This section adds the ag and dairy tranche, so a single producer run covers
both. Its evidence is
[`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C16 and §C17;
reproducer `../analysis/reproduce.py::ag_dairy_backlog_priority`.

## 8.1 The answer is mostly "do not"

Asked to prioritise the ten ag and dairy codes in the §C14 backlog, the measured answer is
that **six should not be specced at all** and one more is marginal. Ranking by open interest,
which is how §C14 printed the backlog, gets the order close to backwards.

| priority | code | market | why |
|---|---|---|---|
| **1** | `039601` | ROUGH RICE | **the only clear yes.** MM share 0.433, 3.2x the covered median and the highest of the ten; flow independent of corn (0.047, inside the noise band); all 82 weeks |
| 2 | `001626` | WHEAT-HRSpring | MM share 0.278, but flow 0.338 against wheat-SRW is above the noise band. Worth it only if a third wheat class is wanted for its own sake |
| 3 | `135731` | CANOLA | largest of the ten at 271,205 OI and the **most duplicative on flow** (0.584 against soybean oil). Size and value point opposite ways |
| 4 | `063642` | CHEESE | only dairy code with real Managed Money (0.076), and 0.520 correlated with Class III milk, which is priced off cheese |
| - | `037021` `050642` `052642` `052644` | palm oil, butter, NFDM, Class IV milk | **do not spec.** MM share 0.012 to 0.048, an order of magnitude under the covered median, 106 to 1,147 contracts absolute. Hedger markets with no levered holder to force out |
| - | `052645` `005603` | dry whey, mini soybeans | **do not spec.** 14 and 13 weeks of 82. Mini soybeans also has a median Managed Money net of exactly zero |

**If only one thing is added from this tranche, add rough rice.** Norgate almost certainly
carries it (`ZR`, a standard CBOT contract), which makes it the cheapest item in the whole
backlog as well as the best justified.

## 8.2 Why the dairy block is a refusal rather than a deferral

Butter, non fat dry milk, Class IV milk and dry whey are not "small markets we will get to".
They are markets **this monitor has nothing to say about**. Damage is crowding x illiquidity x
holder fragility, and with Managed Money at 1.2% to 3.5% of open interest there is no fragile
holder for the fragility term to describe. Adding them would grow the covered count while
lowering the share of coverage the thesis applies to, which is exactly the failure §C13's gate
was built to catch, arriving from the inside instead of the outside.

This is worth stating because the natural next request is "then do the metals and the
remaining energy codes", and the same test should be run first. Cobalt, lithium hydroxide and
the two aluminium codes are all plausible members of the same category.

## 8.3 One methodological correction that changes §2 of this handoff

§2 above argues the energy five are not duplicates, and leads with Managed Money **level**
correlations. `§C16` measures that statistic and finds it spurious: positioning levels have
lag-1 autocorrelation of 0.956, and an **independent random walk** scanned against the covered
25 posts a maximum level correlation of **0.773 half the time**.

**§2's conclusion survives, on its second statistic.** The first-differenced correlations it
also reported (-0.054 to -0.234) sit inside a noise band of p90 = 0.229, so the energy five
really are flow-independent of `CL` and `NG`. But the bolded negative numbers in §2's table
are noise and should not be quoted. Any future variant test uses first differences.

---

# §9. Decision, 2026-08-03: the ag tranche is cut to rough rice alone

**Decided by the human**, on the §C17 evidence, and recorded here rather than by editing §8
so that what was recommended and what was chosen stay separately readable.

## 9.1 The decision

**Tranche 2 is `039601` ROUGH RICE and nothing else.** §8.1 ranked four codes as worth
considering and the lower three are dropped:

| code | market | §8.1 rank | disposition |
|---|---|---|---|
| `039601` | ROUGH RICE | 1 | **IN** |
| `001626` | WHEAT-HRSpring | 2 | dropped. Flow 0.338 against wheat-SRW is above the noise band, and a third wheat class was not wanted for its own sake |
| `135731` | CANOLA | 3 | dropped. Most duplicative of the ten on flow (0.584) |
| `063642` | CHEESE | 4 | dropped. Flow 0.520 against Class III milk, which is priced off cheese |

The six §8.1 already refused are unaffected and stay refused.

**This makes the whole producer ask six codes**: the five energy codes of §1 plus rough rice.

## 9.2 What this does to the §5 verification numbers

§5 was written for tranche 1 alone and its figures still describe that tranche. With rough
rice added the end state moves by one. Rough rice is present in **82 of 82** vintage weeks
including the latest, so unlike oats it lands in the latest-week count rather than only in
the union:

| | covered markets, latest week | `joinable` |
|---|---|---|
| today | 45 | 47 of 49 |
| after tranche 1 (five energy codes) | 50 | 52 of 54 |
| after tranche 2 (rough rice) | **51** | **53 of 55** |

`MFS` and `MME` remain the two unjoinable throughout, for the reason §0 gives.

## 9.3 Why the three dropped codes are dropped rather than deferred

Worth stating so a later session does not read the drop as a scheduling decision and quietly
re-add them. All three failed on **flow correlation against an already-covered market**, which
is a statement about information rather than about size or effort:

- canola at 0.584 against soybean oil is the largest of the ten by open interest (271,205)
  and the most redundant of the four by flow. **Size was the reason to want it and flow is
  the reason not to**, which is the same inversion §C17 records for the tranche as a whole.
- cheese at 0.520 against Class III milk is close to definitional: Class III milk is priced
  off cheese, so the two books respond to one input.
- WHEAT-HRSpring at 0.338 is the mildest case and the only genuinely arguable one. It clears
  the levered-holder bar comfortably (MM share 0.278, twice the covered median). It is
  dropped on the narrow ground that a third wheat class adds a market rather than adding
  information, and the flow number says most of what it would contribute is already in
  wheat-SRW and wheat-HRW.

**If any one of the three is revisited, WHEAT-HRSpring is the one to revisit**, and the test
to re-run is `§C17`'s, not a fresh argument from open interest.

## 9.4 Rough rice, and why it is cheap as well as justified

`039601` is a standard CBOT contract (Norgate `ZR`), so §4's vendor-coverage question, which
is the real risk for the three cash-settled Henry Hub look-alikes, is close to a formality
here. It is the **smallest market in the tranche by open interest (12,374) and the strongest
on the criterion that decides**: Managed Money share of 0.433, 3.2x the covered median and the
highest of any backlog candidate measured.

If the producer run is split for any reason, **run rough rice first.** It is the one item in
the whole backlog that is both certain to be available and certain to be worth having.

---

# §10. The rest of the backlog tested, appended 2026-08-03: seven new candidates, no change to the ask

**Appended after §9.** §C17's test was run on the remaining 24 metals and energy codes, which
`§C19` reports. **Nothing here changes the committed six**, and no third tranche is proposed:
this section exists so the next session finds the measurement rather than re-running it, and
so the seven codes that passed are on record as passing rather than as unexamined.

## 10.1 The committed six all pass, and one bar had to be fixed first

Running the test on the energy backlog initially condemned **four of the five tranche-1
codes**. That was a fault in the test, not in the tranche. `§C18` has the detail: §C17 used a
flat cut of 0.05 on Managed Money share, benchmarked against the pooled covered median of
0.1371, and the **covered energy median is 0.0435**. Nat Gas (0.0369) and WTI (0.0399), the
two largest markets in the universe and both already covered, sit under that flat cut.

Benchmarked within complex, as §C18 corrects it:

| code | market | x complex | verdict |
|---|---|---|---|
| `039601` | ROUGH RICE | **4.41x** grains | the strongest candidate anywhere in the backlog |
| `023A56` | HH PENULTIMATE FIN | 2.02x energy | pass |
| `023A55` | HH LAST DAY FIN | 1.09x energy | pass |
| `067411` | ICE Europe WTI | 0.98x energy | pass |
| `03565C` | HH PENULT NAT GAS | 0.78x energy | pass |
| `03565B` | HENRY HUB | 0.70x energy | pass |

Tranche 1 spans 0.70x to 2.02x, which is the range the covered energy markets themselves
occupy. **§1, §8 and §9 stand unchanged.**

## 10.2 Seven codes pass and are NOT being asked for

Recorded so they are visible, not to expand the run. If a later tranche is wanted, this is the
list and the order:

| code | market | complex | x complex | mean OI | note |
|---|---|---|---|---|---|
| `06665P` | MT BELVIEU ETHANE OPIS | Energies | **3.80x** | 49,818 | strongest new candidate, all 82 weeks |
| `406651` | PGP PROPYLENE (PCW) CAL | Energies | 2.25x | 7,367 | **66 of 82 weeks** |
| `192691` | NORTH EURO HRC STEEL | Metals | **1.88x** | 10,973 | **78 of 82 weeks**, genuinely newer rather than intermittent |
| `192651` | STEEL-HRC | Metals | 0.98x | 33,298 | all 82 weeks |
| `06665Q` | MT BELV NORM BUTANE OPIS | Energies | 0.91x | 51,235 | all 82 weeks |
| `06665O` | PROPANE | Energies | 0.63x | 139,138 | all 82 weeks |
| `189691` | LITHIUM HYDROXIDE | Metals | 0.54x | 27,847 | all 82 weeks, at the bar |

**Mt Belvieu ethane is the one to take first if any are taken.** It was invisible under the
flat bar and is the second strongest candidate in the whole backlog after rough rice.

**Norgate coverage is the open question for all seven**, exactly as §4 states for tranche 1,
and it is more doubtful here: OPIS- and PCW-assessed NGL contracts and European steel are
further from Norgate's liquid-outright universe than a CBOT grain is. Confirm before
committing to any of them.

## 10.3 What the excludes say about the backlog as a whole

**16 of 34 codes fail for want of a levered holder; only 5 fail for redundancy.** The backlog
is not mostly duplicates. It is mostly markets where the fragility term has nothing to
describe, which is `§C13`'s gate finding from the inside what it found from the outside.

Two worth naming:

- **`06765A` WTI FINANCIAL CRUDE OIL**: mean OI **175,418**, which would rank 15th of the
  covered 25, and a median Managed Money net of **475 contracts**. Large, liquid, a pure
  outright, and empty of the participant this monitor is about.
- **`088695` MICRO GOLD fails both bars**, at 0.07x of metals and flow 0.355 against gold.
  §C14 recommended settling it by analogy with `2026-08-02 §B30`; that is now measured, and it
  is the only backlog code that is both thin and duplicative.

`06665G` propane non-LDH (29,972 OI) and `025608` ethanol T2 both have a median Managed Money
net of **exactly zero**.

---

# §11. §4 answered, 2026-08-04: the vendor carries two of the six, and the ask shrinks

**This is the outcome for §4, the one step this handoff said had to happen first and could not
be settled from the Linux side.** It is answered by the vendor's own catalogue, which the
human supplied: Norgate's `FuturesContractDetails.xls`, the workbook `contract_specs` is built
from. Nothing else in this handoff is executed; §1, §8, §9 and §10 stand as written.

Findings: `2026-08-04 §D1`.

## 11.1 The answer, and it is the one §4 suspected

| CFTC code | market | Norgate | disposition |
|---|---|---|---|
| `039601` | ROUGH RICE | **`ZR`** | **ask stands** |
| `067411` | WTI, ICE Futures Europe | **`WBS`** | **ask stands** |
| `023A55` | HENRY HUB LAST DAY FIN | absent | **vendor-absent**, stays in the backlog |
| `03565B` | HENRY HUB, NYMEX | absent | **vendor-absent** |
| `023A56` | HENRY HUB PENULTIMATE FIN | absent | **vendor-absent** |
| `03565C` | HENRY HUB PENULTIMATE NAT GAS | absent | **vendor-absent** |

§4 flagged the three cash-settled look-alikes as the doubtful ones and was right about all
three, plus `03565B` goes the same way. **The producer ask is two codes, not six.**

The absence is read off a **complete enumeration rather than a keyword search**: Norgate's
entire energy universe is eight contracts (`CL`, `HO`, `RB`, `NG`, `BRN`, `WBS`, `GAS`,
`GWM`), of which four are already covered. It lists exactly one Henry Hub contract and it is
`NG`, which is `023651` and already in the store.

§4's rule is applied as written: reported vendor-absent, no proxy substituted.

## 11.2 What this does to §5 and §9.2

Both were written for a six-code run. Superseded:

| | covered markets, latest week | `joinable` |
|---|---|---|
| today | 45 | 47 of 49 (verified 2026-08-04) |
| §9.2's expectation, all six | 51 | 53 of 55 |
| **achievable** | **47** | **49 of 51** |

`MFS` and `MME` remain the two unjoinable throughout. §5's shell command is unchanged and is
still the check that matters; only its expected numbers move.

## 11.3 The workbook does not shorten the run

It settles the vendor question and supplies most of one artifact of three. The `unadj` and
`backadj` series both still need the subscription, and `propadj` is derived from that pair, so
**the Windows box is still the blocker for everything §3 asks for**. The workbook also has no
`Margin` column, which `contract_master.py` reads per spec row and which is non-null on all 47
today.

It was cross-checked against the store rather than trusted: 47 of 47 stored symbols present,
`Tick Value` and `Point Value` agreeing exactly on every one.

## 11.4 Two things worth carrying

**Vendor coverage is not why the three ag codes were dropped.** `RS` Canola and `MWE` Hard Red
Spring Wheat are both in the catalogue. §9.3 says WHEAT-HRSpring is the one to revisit if any
is, by re-running `§C17`'s test; the data for it exists.

**There is a block of CFTC-reported financials nobody has looked at**, because `§C14` scoped
itself to Disaggregated: `SR3`, `ZQ`, `UB`, `TN`, `VX` and the equity micros are all in the
catalogue and none is in the store. They report on TFF, where the levered-holder bar means
something different, so this is **recorded and not proposed**. It is not a third tranche and
§10's "no third tranche" is unaffected.

## 11.5 Status

**Still open, still blocked on the Windows box**, and now scoped: **two codes**, rough rice
first per §9.4. §4 is closed.

---

# §12. CLOSED 2026-08-04: the tranche landed, and §6 is executed

**Complete.** The producer run wrote both codes the vendor carries, the store synced, and the
follow-up §6 assigns to a `crowdmon` session is done. Findings: `2026-08-04 §D1` (the vendor
answer) and `§D11` (the landing). New point-in-time record:
[`../analysis/2026-08-04-contract-spec-inventory.md`](../analysis/2026-08-04-contract-spec-inventory.md).

## 12.1 What landed

`cotdata` #99 added `ZR` (`039601`) and `WBS` (`067411`) to the registry, which is the
**precondition** for the run rather than a consequence of it: `get_symbol_metadata` resolves
`REGISTRY[internal].norgate`, so an unlisted symbol is a `KeyError` before any fetch. Then, on
the Windows box:

```
cotdata-update --metadata --symbols ZR WBS
cotdata-update --prices  --symbols ZR WBS
```

Verified against the real store: both carry a spec and all three price tiers (`ZR` 10,062 rows
from 1986-08-20, `WBS` 5,288 from 2006-02-03, both to 2026-08-03), both point values match the
vendor sheet, and **`joinable` reads 49 of 51** with `MFS` and `MME` still the only two out.
Covered markets moved **45 to 47**, both new codes present in the latest report week, as §9.2
predicted from rough rice's 82-of-82 week count.

## 12.2 §6's four items

| item | done |
|---|---|
| re-run `contract_spec_inventory`, **new dated file** | `docs/analysis/2026-08-04-contract-spec-inventory.md`. The 2026-07-28 file is untouched and both are correct about the same week |
| update the covered-universe count | `docs/handoffs/README.md`, two rows. **`CLAUDE.md` never carried it**, see `§D11` |
| re-measure the four suite figures | done, rather than adjusted by hand |
| `continuity.py` on `03565B` vs `023651` | **moot, and settled the other way.** Whether they are one instrument or two no longer matters: Norgate carries no series for `03565B`, so it cannot be scored under either answer |

## 12.3 What is still true

**The four Henry Hub codes stay in the backlog permanently**, absent a vendor change, which
`tests/test_contract_master_live.py::test_the_four_henry_hub_codes_are_absent_rather_than_forgotten`
now asserts so that a future session reads it as settled rather than as an oversight. The bar
it fails on is availability, not merit: `§C15` measured their holder base as genuinely
different from `NG`'s, which is why they were wanted.

§7's list is unchanged. Price limits still have no table, §379's OI migration is still blocked
on whole-market `Open Interest`, and the §10 validation verdict is untouched, since new markets
supply no new clean episodes for weeks that already happened.

The seven codes `§10.2` recorded as passing but not requested are unaffected and stay
unrequested.

## 12.4 Status

**COMPLETE.** Nothing open.
