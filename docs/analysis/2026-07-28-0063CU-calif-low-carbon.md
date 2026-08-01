# CALIF LOW CARBON FSC-OPIS (`0063CU`), week ending 2026-07-28

**Selected by ranking, not by hand:** highest `Q_sell / OI` of 279 markets in the latest
Disaggregated report. Ranking tables and method in
[2026-07-28-first-rankings.md](2026-07-28-first-rankings.md).

ICE Futures Energy Division. California Low Carbon Fuel Standard credits, OPIS-assessed.
Report week 2026-07-28, released 2026-07-31, provenance `published`, futures-only.
Reproducer: `python docs/analysis/reproduce.py`.

---

## 1. Category table

Open interest **113,935**, of which 3,245 is spreading.

| category | long | short | net | gross | `w_c` | Phi contribution | Q side | Q contribution |
|---|---|---|---|---|---|---|---|---|
| managed_money | 69,007 | 0 | +69,007 | 69,007 | 1.0 | 0.3028 | sell | 69,007 |
| swap | 30,450 | 2,321 | +28,129 | 32,771 | 0.4 | 0.0575 | sell | 11,252 |
| other_reportable | 2,557 | 21,383 | -18,826 | 23,940 | 0.5 | 0.0525 | buy | 9,413 |
| producer_merchant | 8,566 | 86,986 | -78,420 | 95,552 | 0.1 | 0.0419 | buy | 7,842 |
| nonreportable | 110 | 0 | +110 | 110 | 0.6 | 0.0003 | sell | 66 |

Two things are visible before any formula is applied.

**Managed Money holds 69,007 long contracts and exactly zero short.** Not "almost none" —
zero, and it has been zero every week of the trailing twelve. This is a purely directional
book with no offsetting leg at all, which is unusual and matters for everything below: there
is nothing internal to the category that could cushion an exit.

**Producer/Merchant is short 86,986 against 8,566 long.** That is the classic hedge: an
entity with physical exposure selling it forward. It is also the single largest gross
position in the market at 95,552 contracts, 84% of open interest on one side.

---

## 2. `Q_sell`, `Q_buy` and `Phi`, with the arithmetic

    Q_sell = 1 x 69,007 + 0.4 x 28,129 + 0.6 x 110
           = 69,007 + 11,251.6 + 66
           = 80,324.6 contracts

    Q_buy  = 0.5 x 18,826 + 0.1 x 78,420
           = 9,413 + 7,842
           = 17,255.0 contracts

    Phi    = (1 x 69,007 + 0.4 x 32,771 + 0.5 x 23,940 + 0.1 x 95,552 + 0.6 x 110)
             / (2 x 113,935)
           = (69,007 + 13,108.4 + 11,970 + 9,555.2 + 66) / 227,870
           = 103,706.6 / 227,870
           = 0.4551

`Phi`'s reachable ceiling here is **0.9715**, not 1: spreading (3,245 contracts) counts
toward open interest but is a matched long and short in one trader's hands with no
directional exit, so it sits in the denominator and outside the numerator by design.

Exit pressure, both directions, OI-denominated:

    Q_sell / OI = 80,324.6 / 113,935 = 0.7050
    Q_buy  / OI = 17,255.0 / 113,935 = 0.1514
    Q_sell / Q_buy = 4.66

**The asymmetry is the number to read.** The fragility-weighted long position is 4.7 times
the fragility-weighted short position, and equals 70% of the entire open interest. This is
the most one-sided market in the 279 on this measure.

### Which category is the headline really about?

Managed Money contributes **0.3028 of the 0.4551 Phi — 67%.** So the reading is
substantially a statement about one category, and about sixteen traders within it. The other
four categories together contribute 0.152. Any sentence beginning "this market is 46%
fragile" should be read as "Managed Money's purely long book is two-thirds of what makes
this market fragile".

---

## 3. Flow decomposition

### Latest week, every category

| category | long | short | Δlong | Δshort | Δnet | ΔOI | state | OI corroborates |
|---|---|---|---|---|---|---|---|---|
| managed_money | 69,007 | 0 | +1,138 | 0 | +1,138 | +2,152 | **new_longs** | True |
| nonreportable | 110 | 0 | +104 | 0 | +104 | +2,152 | new_longs | True |
| other_reportable | 2,557 | 21,383 | +272 | +2,530 | -2,258 | +2,152 | new_shorts | True |
| producer_merchant | 8,566 | 86,986 | +430 | -956 | +1,386 | +2,152 | mixed | |
| swap | 30,450 | 2,321 | -255 | +115 | -370 | +2,152 | mixed | |

Managed Money added 1,138 longs with the short leg unmoved, and open interest rose 2,152,
so the label is corroborated: these are contracts that did not previously exist, not a
position transferred from another category. Fresh conviction, not short covering — and
since Managed Money holds no shorts at all, short covering is not available to it as a
mechanism.

### Managed Money, trailing 12 weeks

| report_date | days | long | short | Δlong | Δshort | Δnet | state | OI corroborates |
|---|---|---|---|---|---|---|---|---|
| 2026-05-12 | 7 | 67,037 | 0 | +777 | 0 | +777 | new_longs | True |
| 2026-05-19 | 7 | 68,181 | 0 | +1,144 | 0 | +1,144 | new_longs | True |
| 2026-05-26 | 7 | 68,016 | 0 | -165 | 0 | -165 | long_liquidation | True |
| 2026-06-02 | 7 | 68,290 | 0 | +274 | 0 | +274 | new_longs | True |
| 2026-06-09 | 7 | 68,377 | 0 | +87 | 0 | +87 | new_longs | False |
| 2026-06-16 | 7 | 67,069 | 0 | -1,308 | 0 | -1,308 | long_liquidation | True |
| 2026-06-23 | 7 | 66,832 | 0 | -237 | 0 | -237 | long_liquidation | True |
| 2026-06-30 | 7 | 65,931 | 0 | -901 | 0 | -901 | long_liquidation | True |
| 2026-07-07 | 7 | 65,302 | 0 | -629 | 0 | -629 | long_liquidation | False |
| 2026-07-14 | 7 | 66,834 | 0 | +1,532 | 0 | +1,532 | new_longs | True |
| 2026-07-21 | 7 | 67,869 | 0 | +1,035 | 0 | +1,035 | new_longs | True |
| 2026-07-28 | 7 | 69,007 | 0 | +1,138 | 0 | +1,138 | new_longs | True |

**The sequence matters more than the last week, and here it says something the last week
alone does not.** The position peaked at 68,377 on 2026-06-09, bled off over four
consecutive `long_liquidation` weeks to 65,302 on 07-07 (a 4.5% reduction), and has been
rebuilt in three consecutive `new_longs` weeks to **69,007 — a new high above the June
peak**. Every interval is 7 days, so none of this is a gap artifact.

That is a position that was tested and re-established larger. It is a meaningfully different
configuration from one that has simply been grinding higher: a set of holders reduced under
some pressure in mid-June and then bought it all back plus more, which is the behaviour of
conviction rather than of drift.

Two weeks (06-09 and 07-07) show `oi_corroborates = False`: the label says positioning
changed but market open interest moved the other way, so those weeks describe a **transfer**
between categories rather than net new or closed risk.

---

## 4. Breadth-depth: `ΔP = N₀·Δq + q₀·ΔN + ΔN·Δq`

Managed Money long side. Trader counts are published for this category in this market, which
is not guaranteed — 44% of Managed Money long counts are suppressed across the report.

| report_date | position | traders | avg/trader | ΔP | ΔN | Δq | depth | breadth | joint | dominant | quadrant |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-12 | 67,037 | 14 | 4,788 | +777 | 0 | +55.5 | +777 | 0 | 0 | depth | narrow_and_deep |
| 2026-05-19 | 68,181 | 13 | 5,245 | +1,144 | -1 | +456.3 | +6,389 | -4,788 | -456 | depth | narrow_and_deep |
| 2026-05-26 | 68,016 | 13 | 5,232 | -165 | 0 | -12.7 | -165 | 0 | 0 | depth | distributing |
| 2026-06-02 | 68,290 | 14 | 4,878 | +274 | +1 | -354.1 | -4,604 | +5,232 | -354 | breadth | wide_and_shallow |
| 2026-06-09 | 68,377 | 14 | 4,884 | +87 | 0 | +6.2 | +87 | 0 | 0 | depth | narrow_and_deep |
| 2026-06-16 | 67,069 | 14 | 4,791 | -1,308 | 0 | -93.4 | -1,308 | 0 | 0 | depth | distributing |
| 2026-06-23 | 66,832 | 14 | 4,774 | -237 | 0 | -16.9 | -237 | 0 | 0 | depth | distributing |
| 2026-06-30 | 65,931 | 15 | 4,395 | -901 | +1 | -378.3 | -5,296 | +4,774 | -378 | depth | wide_and_shallow |
| 2026-07-07 | 65,302 | 15 | 4,353 | -629 | 0 | -41.9 | -629 | 0 | 0 | depth | distributing |
| 2026-07-14 | 66,834 | 16 | 4,177 | +1,532 | +1 | -176.3 | -2,645 | +4,353 | -176 | breadth | wide_and_shallow |
| 2026-07-21 | 67,869 | 16 | 4,242 | +1,035 | 0 | +64.7 | +1,035 | 0 | 0 | depth | narrow_and_deep |
| 2026-07-28 | 69,007 | 16 | 4,313 | +1,138 | 0 | +71.1 | +1,138 | 0 | 0 | depth | narrow_and_deep |

**Which term dominates: depth, in 9 of 12 weeks.** But that is mostly mechanical — the
trader count only changes in 5 of the 12 weeks, and when it does not change the breadth term
is identically zero and depth absorbs the whole move by construction. The informative read
is the trend across the window rather than the weekly label.

Over the twelve weeks: **traders 14 → 16, average position 4,788 → 4,313.** The crowd got
*wider and individually smaller*. The two weeks in the last month that added a trader
(07-14, and 06-30 on the way down) are both `wide_and_shallow`.

**This cuts against the naive reading of the headline.** A `Q_sell/OI` of 0.705 with Phi
two-thirds carried by one category looks like the "narrow and deep" cell of the spec's
quadrant — the violent-unwind configuration. The breadth decomposition says the opposite is
happening at the margin: the position is being rebuilt to new highs by *more* traders each
holding *less*, which is the "wide and shallow" pattern that grinds rather than breaks.

The caveat is scale. Sixteen traders is not a crowd. Going from 14 to 16 is a 14% change in
participant count driven by two entities, and the average position per trader is 4,313
contracts, which is 3.8% of the entire market's open interest **each**. This is a
concentrated market that happens to be getting marginally less concentrated, not a broad
one.

---

## 5. Reading

Managed Money holds a purely long book of 69,007 contracts — 61% of open interest, with no
short leg whatsoever — sitting across roughly sixteen traders. The other side is a physical
hedger short 86,986 contracts at a fragility weight of 0.1, which is the point of the
weighting: that entity is offsetting a cash exposure and can stand for delivery, so it does
not get forced anywhere by a price move.

**The fragile direction is unambiguously down.** `Q_sell` is 4.7x `Q_buy`, and it is 70% of
open interest. If the levered long side is forced out, it must sell into a book whose
natural counterparty is a hedger with no obligation to bid and no forced-buy function of its
own. The 0.5-weighted `other_reportable` short (18,826 net) is the only other candidate
buyer with any fragility, and at 9,413 weighted contracts it is roughly an eighth of the
weighted selling it would have to absorb.

**What would have to happen to force that side out.** Nothing here can answer that, and it
is worth being explicit about the gap rather than gesturing at it. Forcing a levered long
out takes one of: a price move large enough to breach stops or drawdown limits, a
volatility increase that shrinks a vol-targeted position mechanically, or a margin increase.
This document has **no price, no volatility and no margin data**, so it can say the position
is large and one-sided and structurally forceable, and it cannot say what level would do it
or how close that level is. That is the trigger solver in spec §9.3, which needs the
contract master, prices and the CTA replication model.

The flow evidence points away from imminence rather than toward it. The position was reduced
4.5% over four weeks in mid-June and fully rebuilt to a new high, by a slowly widening set of
holders each holding slightly less. That is not the signature of a position under stress. If
this configuration is dangerous, it is dangerous in the way a large well-financed position
is dangerous — it has a lot to sell if it ever has to — not in the way a position already
being liquidated is.

**What is missing here specifically**, beyond the standing list in the ranking document: no
volume for this contract, so `days_to_liquidate` is `None` and 70% of open interest cannot
be converted into days; no price, so no trigger level; the 0.1 producer weight is doing
substantial work in making this market look one-sided, and a reader who thought California
LCFS obligated parties were more forceable than a crop hedger would get a materially
different `Q_buy`.

---

## Bottom line

This is the most one-sided positioning structure in the Disaggregated report as of
2026-07-28, and the imbalance is genuine rather than an artifact of a thin market: 113,935
contracts of open interest, above the universe median. A purely long Managed Money book
equal to 61% of open interest faces a physical hedger who cannot be forced to do anything,
so if this market breaks, it breaks downward, and there is very little fragile capital on
the other side to catch it.

That is a statement about tail shape, not a warning. The trailing twelve weeks show the
position tested in June, rebuilt to a new high, and spread across two more traders at a
lower average size, which is the opposite of the concentrating-into-fewer-hands pattern that
precedes violent unwinds. **In plain terms: a large, lopsided, well-held position with no
sign of stress in it — genuinely notable structure, no evidence of imminent trouble, and no
ability to say what would trigger it until prices and volume exist in this package.**
