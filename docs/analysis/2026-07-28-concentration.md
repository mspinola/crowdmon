# Concentration: CR4 and CR8, week ending 2026-07-28

**Report** Disaggregated, futures-only. **Universe** 279 markets in the latest week; 27
markets, 2006-2026, for the history.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_concentration.py`.
**Code** `crowdmon.futures.concentration`, module spec §6.2.

CFTC publishes the share of each side held by the four and eight largest traders in every
file. **Zero percent null across the whole twenty-year history and all 279 markets**, needing
no prices, no volume and no contract master. Spec §6.2 calls it "the metric set that COT
gives away free and that has no cheap equity equivalent", and it had gone unused until now.

---

## 1. Four traders hold half of one side in the median market

`CR4` on the more concentrated side, 279 markets:

| | |
|---|---|
| min | 8.6 |
| 10th | 29.4 |
| 25th | 40.4 |
| **median** | **53.8** |
| 75th | 68.4 |
| 90th | 78.3 |
| max | **100.0** |

The short side is the more concentrated one in the large majority of markets. A CR4 of 100.0
is not a rounding artifact: in NJ RECs Class 2 V2026, **four traders hold the entire net short
side**.

### Two things a CR number is not

**It is not a share of open interest.** CFTC computes CR on *net* positions, so the
denominator is one side's net total rather than gross or OI. A CR4 of 45% does not say four
traders hold 45% of the market.

**It is not fragility.** `Phi` asks what *kind* of holder is on each side; CR4 asks how *few*
there are, knowing nothing about who. The two are independent by construction and the whole
value of having both is in the cases where they disagree.

---

## 2. Concentration falls as markets get larger

| open interest quartile | markets | median CR4 | median Phi |
|---|---|---|---|
| smallest | 70 | **61.8** | 0.3 |
| small | 70 | 61.0 | 0.2 |
| large | 69 | 56.5 | 0.2 |
| largest | 70 | **36.0** | 0.2 |

A 26-point spread from smallest to largest quartile. Unsurprising in direction and useful in
magnitude: it means **a cross-market ranking on raw CR4 is close to a ranking on smallness**,
and any use of concentration across markets needs either a size control or the
against-own-history form in §5.

---

## 3. The quadrant, and the one cell that needs both measures

Thresholds are this week's cross-sectional medians, so the split is relative by construction
and each side is about half the universe.

| | low `Phi` | high `Phi` |
|---|---|---|
| **low CR4** | diffuse and patient: 63 | broad and forceable: 76 |
| **high CR4** | few and patient: 76 | **few and forceable: 64** |

The bottom-right cell is the one worth finding and the only one that needs both numbers.
Neither measure alone separates a market held by a handful of patient hedgers from one held
by a handful of levered funds.

**By venue, it is almost entirely power and environmental:**

| quadrant | CBOT | CME | COMEX | ICE ENERGY | ICE US | NYMEX | NODAL |
|---|---|---|---|---|---|---|---|
| broad_and_forceable | 7 | 7 | 7 | 28 | 6 | 9 | 11 |
| diffuse_and_patient | 0 | 2 | 0 | 39 | 0 | 13 | 8 |
| **few_and_forceable** | **1** | **2** | **3** | **32** | **0** | **3** | **23** |
| few_and_patient | 0 | 0 | 0 | 46 | 0 | 4 | 26 |

**55 of the 64 `few_and_forceable` markets (86%) are ICE Energy Division or Nodal Exchange.**
Six sit on the classic exchanges.

The top of that cell:

| market | CR4 | side | Phi | open interest |
|---|---|---|---|---|
| NEW JERSEY RECs CLASS 2 V2026 | **100.0** | short | 0.345 | 9,960 |
| NEW JERSEY RECs CLASS 2 V2027 | 96.7 | short | 0.341 | 10,756 |
| NJ COMPLIANCE RECs CLASS 1 | 90.2 | short | 0.241 | 28,722 |
| MARYLAND SOLAR REC | 89.2 | short | 0.307 | 55,581 |
| NAT GAS TETCO-WLA INDEX | 87.0 | short | 0.299 | 27,521 |
| PJM.APS_month_on_dap | 85.4 | short | 0.257 | 13,611 |
| CME MILK IV | 81.0 | long | 0.269 | 10,882 |

Renewable energy certificates dominate, and the pattern is consistent: **short side, four
traders, small market**. That is a compliance market, where a handful of obligated parties
sell certificates they must deliver. Whether "forceable" means anything for an entity with a
statutory obligation is a question the fragility weights were never designed to answer, and
this is the third finding in a row pointing at the same gap: the weights were written for
Disaggregated commodity categories and the ICE/Nodal universe is not that.

---

## 4. Every classic outright is diffuse

| market | CR4 | side | Phi | quadrant |
|---|---|---|---|---|
| GOLD | 34.5 | short | 0.468 | broad_and_forceable |
| CORN | 9.8 | long | 0.313 | broad_and_forceable |
| SOYBEANS | 15.6 | short | 0.259 | broad_and_forceable |
| CRUDE OIL | 13.7 | short | 0.229 | diffuse_and_patient |
| WHEAT-SRW | 8.6 | short | 0.334 | broad_and_forceable |

**None is in `few_and_forceable`, and none is close.** Wheat's four largest traders hold 8.6%
of the net short side against a universe median of 53.8. Concentration risk in this report is
not a commodity-futures phenomenon; it is a power, gas-basis and REC phenomenon, and it
compounds the earlier finding that 76% of the Disaggregated universe is those markets.

---

## 5. Against own history, the picture inverts

Levels are not comparable across markets, so the same argument that motivates
`extremity` applies here: what is comparable is where a market sits against its own past.
27-market panel, 2006-2026, **24,365 of 27,194 market-weeks scored** (the rest is warm-up),
and **zero null CR values in twenty years**.

Most concentrated against own three-year history, latest week:

| market | CR4 | side | z | percentile |
|---|---|---|---|---|
| SOYBEANS | 15.6 | short | 1.81 | **0.984** |
| WTI-PHYSICAL | 13.7 | short | 1.64 | 0.962 |
| PLATINUM | 38.0 | short | 1.44 | 0.930 |
| SOYBEAN MEAL | 30.1 | short | 1.33 | 0.908 |
| COTTON NO. 2 | 26.6 | short | 1.53 | 0.854 |
| SOYBEAN OIL | 19.9 | short | 0.55 | 0.783 |

**Soybeans at a CR4 of 15.6 is at the 98th percentile of its own three years**, while a REC
market at 100.0 would rank unremarkably against its own history because it is always that
concentrated. The two views answer different questions and the second is the one that says
something has *changed*.

Note that all six are the **short** side, and five of six are ags. That is worth flagging
rather than interpreting: spec §5.4 warns that commercial positioning in ags is strongly
seasonal, seasonal adjustment is still unbuilt, and a concentration reading taken at one point
in the crop calendar may be a calendar artifact. The `extremity` work measured that effect as
real but modest for `D`; it has not been measured for CR.

---

## 6. What is missing

- **No seasonal adjustment** (§5.4), and §5 above is the case where it would matter most.
- **CR is on nets, so it interacts with `Phi` oddly.** A market whose net is small relative to
  gross can post a high CR on a small absolute position. Nothing here normalises for that.
- **The quadrant thresholds are medians of the week**, so membership is relative and a time
  series of it would need fixed cuts. `quadrant()` takes explicit thresholds for that reason.
- **Legacy has no CR columns**, so this is Disaggregated and TFF only.
- **CR is not in the composite.** `D = C x I x Phi` has no concentration term, and §A.9 does
  not define one. Whether "few holders" belongs in the damage product or beside it is a design
  question, not an oversight.

---

## Bottom line

CR4 and CR8 were published in every file for twenty years, are never null, need no other data,
and were unused. They are now read, with the derived gap between the fourth and eighth trader
and a percentile against own history.

**The headline is that concentration risk in this report is not a commodities phenomenon.**
Four traders hold a median 53.8% of one side across 279 markets, but every classic outright is
diffuse: wheat 8.6, corn 9.8, crude 13.7, gold 34.5, none of them in the `few_and_forceable`
cell. That cell holds 64 markets and 86% of them are ICE Energy Division or Nodal, topped by
renewable energy certificates where **four traders hold the entire net short side**.

The second finding is that levels and history say opposite things. Soybeans at CR4 15.6 is
diffuse in absolute terms and at the **98th percentile of its own three years**; a REC market
at 100.0 is extreme in absolute terms and ordinary against itself. Which one matters depends
on whether the question is "can this market absorb an exit" or "has something changed here".

**In plain terms: a free, complete, twenty-year dataset that says the crowded-into-few-hands
risk sits almost entirely in power and environmental contracts rather than in the commodities
the spec is written around.** The caution is that five of the six markets currently extreme
against their own history are ags on the short side, seasonal adjustment is still unbuilt, and
that pattern is exactly what §5.4 warns would appear as a calendar artifact.
