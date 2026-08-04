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

## D2. The tranche landed: 47 covered markets, the gate still passes, and four print statements had gone stale

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
