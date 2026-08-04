# Contract spec inventory after the backlog run: 47 markets, and the gate still passes

**Report week:** 2026-07-28 (latest), vintage panel from 2025-01-07, 82 weeks
**Handoff:** [`2026-08-03-spec-backlog-producer.md`](../handoffs/2026-08-03-spec-backlog-producer.md) §6
**Reproducer:** [`reproduce.py`](reproduce.py)`::contract_spec_inventory`
**Amendments:** [`../design/amendments-2026-08-04.md`](../design/amendments-2026-08-04.md) §D1, §D2
**Data:** `cot_disagg` and `cot_tff` vintage observations, `contract_specs` (Norgate, written 2026-08-04 11:48)

Point-in-time, per this directory's rule. **A new file rather than an edit to
[`2026-07-28-contract-spec-inventory.md`](2026-07-28-contract-spec-inventory.md)**, which is
the correct record of the same week measured before two markets were added. Both are true of
report week 2026-07-28 and they disagree, which is exactly the case the rule exists for.

> **Two markets landed and nothing else moved.** `ZR` rough rice and `WBS` ICE Europe WTI
> now carry specs and both price tiers, so covered markets go **45 -> 47** and `joinable`
> goes **47 of 49 -> 49 of 51**. The gate the previous inventory reports still passes, now
> at **27 of 27** classic outright with zero power, gas or carbon contracts.
>
> **The four Henry Hub codes are still in the backlog and always will be** (`§D1`): Norgate
> does not carry them, so they are vendor-absent rather than unrequested.

---

## 1. What changed, in one table

| | 2026-07-28 inventory | today | source of the change |
|---|---|---|---|
| covered markets, latest week | 45 | **47** | `ZR`, `WBS` |
| Disaggregated, latest week | 25 | **27** | both new codes are Disaggregated |
| TFF, latest week | 20 | 20 | unchanged |
| spec'd union over 82 weeks | 47 | **49** | plus oats, still intermittent |
| registry symbols | 49 | **51** | cotdata #99 |
| `joinable` | 47 of 49 | **49 of 51** | the producer run |
| uncovered Disaggregated codes | 254 | **252** | the same two, moved across |
| backlog, real outright | 34 | **32** | the same two, removed |

Nothing else in the inventory moved. The certificate count is 213 and the differential count
is 7 on both dates, which is the check that the two new rows came out of the **backlog** and
not out of some other population.

## 2. The identity that says nothing is stranded

The previous inventory made this point arithmetically (`26 + 21 = 47`, the whole spec table).
That form breaks the moment the registry and the spec table stop having the same length, which
is now: 51 registry symbols, 49 with specs. So it is stated as a set identity instead, and the
reproducer prints both directions:

```
symbols on a panel 49, joinable 49, registry 51;
  joinable-but-unseen [], seen-but-unjoinable []
```

Every symbol that can be priced appears on a panel, and every symbol on a panel can be priced.
`MFS` and `MME` are neither: they are the two MSCI index products Norgate does not carry, they
have no spec, and they do not appear on either vintage panel.

## 3. The two new markets

| | `ZR` rough rice | `WBS` WTI Crude Oil |
|---|---|---|
| CFTC code | `039601` | `067411` |
| exchange | CBOT | ICE Europe |
| point value | 20.0 | 1,000.0 |
| tick value | 10.0 | 10.0 |
| margin | 1,375 | 13,080 |
| `unadj` / `backadj` / `propadj` | 10,062 rows, 1986-08-20 -> 2026-08-03 | 5,288 rows, 2006-02-03 -> 2026-08-03 |

Both point values match the vendor's own `FuturesContractDetails.xls` exactly, which is the
cross-check `§D1` ran before the entries were written.

All three tiers agree on the last close (`ZR` 1,417.50, `WBS` 79.98). That is the documented
behaviour rather than a defect: adjustment anchors at the most recent contract, so the
back-adjustment error is exactly zero today and grows backwards, which is the first row of the
layer-2 trap table.

Both are present in the latest report week, so rough rice lands in the latest-week count
rather than only in the union. §9.2 of the handoff predicted that from its 82-of-82 week
count, and it holds.

## 4. The gate, re-run rather than assumed

`2026-07-28-contract-spec-inventory.md` §2 reports a gate: is the covered set analytically
worth scoring, or is it technically real and empty? Re-run on the wider set:

| | 2026-07-28 | today |
|---|---|---|
| covered stratum | 25 of 25 real outright | **27 of 27 real outright** |
| power / gas / carbon inside coverage | 0 | **0** |
| always-template markets inside (`2026-08-02 §B36`) | 7 of 7 | **7 of 7** |
| median \|P_MM\|/OI, covered | 0.1371 | **0.1371** |
| median \|P_MM\|/OI, uncovered | 0.0370 | **0.0364** |

The covered median is **unchanged to four decimal places**, which is worth a sentence rather
than a shrug. Rough rice was selected on a Managed Money share of 0.433, the highest of any
backlog candidate, and ICE Europe WTI on a holder base measurably different from `CL`'s
(`2026-08-03 §C15`). Adding one market far above the median and one energy market, where
energy is thin on this term everywhere (`§B33`), moved the median of 27 markets not at all.
A median is robust to exactly this, and the reading is that **the covered set's character did
not change**, not that the additions were inert.

The complex mix moved as expected: Grains 6 -> 7, Energies 4 -> 5, everything else identical.

## 5. What is left in the backlog, and what it is made of

32 real outright codes, down from 34:

| family | codes | note |
|---|---|---|
| Henry Hub | 4 | **permanently blocked.** Norgate carries one Henry Hub contract and it is `NG` = `023651` (`§D1`) |
| Mt Belvieu / propane / NGL | 7 | one instrument family; `06665P` ethane is the strongest at 3.80x its complex (`§C19`) |
| WTI / Brent | 2 | `06765A` WTI financial and `06765T` Brent last day. `06765A` has 175,418 mean OI and a median Managed Money net of 475 contracts |
| one-instrument codes | 19 | including micro gold, which fails both bars (`§C19`) |

So the analytical gain is nearer 22 instruments than 32, and the head of the list by open
interest is now four contracts nobody can price.

**The ordering advice in `§C14` is now doubly wrong and worth restating.** It ranked the
backlog by open interest, which put the Henry Hub complex first; `§C18` then showed the
levered-holder bar has to be applied within complex rather than pooled, which moved rough rice
to the top; and the vendor answer removes the four largest entries outright. Open interest has
now failed as a backlog ordering three separate times.

## 6. Reproducing this

```bash
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python -c "
import sys; sys.path.insert(0, 'docs/analysis')
import reproduce; reproduce.contract_spec_inventory()"
```

Four sentences of that function's output were hardcoded literals written when they were
current (`26 + 21 = 47`, `25 of 25 are classic outright`, `nearer 23 instruments than 34`).
They contradicted the numbers printed directly above them the moment this run happened, and
are now derived. That is the house rule about not restating a measured figure as a literal in
a report string, arriving as a bug rather than as a style note.
