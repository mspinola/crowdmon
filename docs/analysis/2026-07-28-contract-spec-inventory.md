# Contract spec inventory: what can be scored, and is it worth scoring

**Report week:** 2026-07-28 (latest), vintage panel from 2025-01-07, 82 weeks
**Handoff:** [`2026-08-03-step2-contract-master.md`](../handoffs/2026-08-03-step2-contract-master.md) tasks 1a-1c
**Reproducer:** [`reproduce.py`](reproduce.py)`::contract_spec_inventory`
**Amendments:** [`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C12, §C13, §C14
**Data:** `cot_disagg` and `cot_tff` vintage observations, `contract_specs` (Norgate)

Point-in-time, per this directory's rule. A later week gets a new file, and §1.1 below is the
reason that rule bites harder here than usual.

> **The gate passes.** The covered set is 25 of 25 real outright, contains all seven
> always-template markets, and carries 3.7x the Managed Money prominence of the markets that
> drop out. The failure the handoff's §1b screens for (coverage that is technically real and
> analytically empty) is **absent rather than rare**: zero covered markets are ICE power or
> Nodal basis contracts.
>
> **Two corrections to the handoff, neither of which changes its §0 decision.** The covered
> universe is **45 markets across two report types, not 25** (§1), and "no contract spec" is
> **three populations, not two** (§3).

---

## 1. The covered set

The handoff scopes the monitored universe as "25 of 279 Disaggregated codes". That count is
correct and it is not the universe. The contract-spec table holds 47 symbols, every one of
which has a price series, and they reach both report types:

| report type | markets on panel | spec'd, union over 82 weeks | spec'd in the latest week |
|---|---|---|---|
| Disaggregated | 346 | 26 | **25** |
| TFF | 111 | 21 | **20** |
| | | **47** | **45** |

26 + 21 = 47 is the entire spec table, so nothing in it is stranded. The 22 symbols absent
from the handoff's list are not missing specs: they are currencies, equity indices, rates and
crypto, and **CFTC does not publish financials on the Disaggregated report**. They are scored
on TFF today, which [`2026-07-28-tff-financial-futures.md`](2026-07-28-tff-financial-futures.md)
already reports on.

`legacy` is a third report type and is refused rather than empty, because its `noncommercial`
bucket merges levered funds with everything else non-commercial and that is the distinction
the fragility weights exist to make.

### 1.1 The count is report-week dependent

The union column exceeds the latest-week column by exactly one on each panel. On Disaggregated
that market is oats (`004603`, `ZO`), which is spec'd, priced, and simply **not in the latest
report**: it appears in 23 of 82 vintage weeks. `2026-08-02 §B29` already recorded oats as
"intermittent reporting, and it recurs" while doing the flow work; this is the same fact
arriving at the coverage layer.

So "25" is a statement about report week 2026-07-28, not a property of the store. A count
taken on another week is legitimately 26 with nothing having changed.

### 1.2 The 25, largest first by mean open interest

`dtl_sell` is days for the fragile long side to liquidate at `kappa = 0.2` of ADV, and is
shown because it is the column whose nullity defines this set.

| code | market | symbol | exchange | complex | mean OI | median \|P_MM\|/OI | `dtl_sell` |
|---|---|---|---|---|---|---|---|
| `067651` | WTI-PHYSICAL | CL | NYMEX | Energies | 1,951,648 | 0.040 | 0.85 |
| `002602` | CORN | ZC | CBOT | Grains | 1,698,705 | 0.073 | 3.69 |
| `023651` | NAT GAS NYME | NG | NYMEX | Energies | 1,584,777 | 0.037 | 0.80 |
| `080732` | SUGAR NO. 11 | SB | ICE US | Softs | 936,883 | 0.109 | 2.99 |
| `005602` | SOYBEANS | ZS | CBOT | Grains | 903,758 | 0.067 | 3.79 |
| `007601` | SOYBEAN OIL | ZL | CBOT | Grains | 641,109 | 0.076 | 3.57 |
| `026603` | SOYBEAN MEAL | ZM | CBOT | Grains | 594,283 | 0.137 | 4.44 |
| `001602` | WHEAT-SRW | ZW | CBOT | Grains | 461,881 | 0.167 | 0.96 |
| `088691` | GOLD | GC | NYMEX | Metals | 445,755 | 0.287 | 3.52 |
| `111659` | GASOLINE RBOB | RB | NYMEX | Energies | 377,301 | 0.134 | 2.30 |
| `057642` | LIVE CATTLE | LE | CME | Live Stock | 356,927 | 0.327 | 6.08 |
| `022651` | NY HARBOR ULSD | HO | NYMEX | Energies | 330,916 | 0.047 | 1.15 |
| `054642` | LEAN HOGS | HE | CME | Live Stock | 322,495 | 0.275 | 2.11 |
| `001612` | WHEAT-HRW | KE | KCBT | Grains | 288,693 | 0.120 | 3.98 |
| `033661` | COTTON NO. 2 | CT | ICE US | Softs | 284,800 | 0.196 | 7.12 |
| `085692` | COPPER- #1 | HG | NYMEX | Metals | 237,272 | 0.193 | 5.23 |
| `083731` | COFFEE C | KC | ICE US | Softs | 169,174 | 0.205 | 4.30 |
| `084691` | SILVER | SI | NYMEX | Metals | 144,286 | 0.149 | 1.35 |
| `073732` | COCOA | CC | ICE US | Softs | 135,143 | 0.089 | 1.50 |
| `076651` | PLATINUM | PL | NYMEX | Metals | 78,002 | 0.137 | 1.92 |
| `061641` | FEEDER CATTLE | GF | CME | Live Stock | 75,782 | 0.304 | 2.21 |
| `052641` | MILK, Class III | DC | CME | Dairy | 26,932 | 0.102 | 8.98 |
| `075651` | PALLADIUM | PA | NYMEX | Metals | 18,992 | 0.239 | 1.80 |
| `040701` | FRZN CONC ORANGE JUICE | OJ | ICE US | Softs | 9,269 | 0.135 | 4.36 |
| `058644` | LUMBER | LBR | CME | Softs | 8,291 | 0.444 | 10.56 |

Mean open interest spans 235x, from WTI at 1.95M to lumber at 8,291, which is the argument for
`top_by`'s `min_open_interest` floor being an explicit argument rather than a default: an
unfiltered `Q/OI` ranking over this set is partly a ranking of its smallest members.

---

## 2. The gate

The handoff's §1b asks one question: are these markets where the fragility argument means
anything? Four readings, all of which point the same way.

**Stratum: 25 of 25 real outright, 0 of 25 power/gas/carbon venue.** Not a majority, all of
them. Against a panel `2026-08-02 §B31` measured as 76% ICE power and Nodal gas basis, the
covered set is not a sample of the panel; it is the complement of the part that made the panel
hard to reason about.

**Complex distribution:** Grains 6, Softs 6, Metals 5, Energies 4, Live Stock 3, Dairy 1.

**Always-template overlap: 7 of 7.** Gold, silver, copper, live cattle, feeder cattle, coffee
and RBOB, the markets `2026-08-02 §B36` found extreme in both halves of its window, are all
inside coverage. The set most at risk of exclusion is entirely included.

**Managed Money prominence: covered 0.1371, uncovered 0.0370** (median `|P_MM| / OI`). The
covered markets carry 3.7x the levered-holder prominence of those that drop out. Worth stating
plainly: the spec table was assembled for a trend-following universe, not for this, so the
alignment is a happy accident rather than a designed one. It is still real.

### 2.1 The one qualification, and it was predicted

`2026-08-02 §B33` found energy outright genuinely thin on Managed Money, and that reproduces
*inside* coverage. Pooled over the four covered energy outrights, **51.2%** of market-weeks
have Managed Money under 5% of open interest (n=328), against **13.9%** for the other 21
covered markets (n=1,722):

| market | share of weeks with \|P_MM\|/OI < 5% |
|---|---|
| NAT GAS | 70.7% |
| WTI-PHYSICAL | 69.5% |
| NY HARBOR ULSD | 54.9% |
| GASOLINE RBOB | 9.8% |

Being spec'd does not fix this, and nothing here should be read as claiming it does. But it is
the opposite of the failure the gate screens for. The gate asks whether coverage is full of
markets the thesis cannot speak about; the answer is that it holds four where it speaks
quietly and 21 where it speaks normally, and the four are named.

**Verdict: the gate passes. Proceed.**

---

## 3. What the 254 uncovered codes actually are

The handoff anticipates two populations: `missing` (a real contract whose spec we have not
entered, a backlog item) and `inapplicable` (no meaningful spec to have, a permanent
exclusion). Measured, there are three.

| class | n | disposition |
|---|---|---|
| environmental / power certificate | 213 | inapplicable, permanent |
| differential / spread / crack | **7** | inapplicable, for a different reason |
| real outright | **34** | **missing. This is the backlog** |

The 213 are 145 ICE Futures Energy Div and 68 Nodal Exchange: RECs, carbon allowances,
compliance certificates and power zones.

**The middle row is the correction.** A venue split, which is the obvious cut and the one the
handoff's framing invites, puts 41 codes in "classic outright" because they trade on NYMEX and
COMEX rather than Nodal. Seven are differentials (`WTI MIDLAND ARGUS VS WTI TRADE`, `GULF # 6
FUEL OIL CRACK`, and five more). These have a multiplier and a tick size, so they are not "no
meaningful spec to have", and they are still permanent exclusions for a reason the binary
cannot express: **the normalisation ladder computes a position value and a differential does
not have one.** `P · M · F` on a spread whose `F` oscillates around zero is not a smaller
notional; it is not a notional. Same class of error as the `backadj` trap, where a number is
produced, is finite, and means nothing.

The 34 backlog items are enumerated in
[`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C14. Two things
change how that list should be read:

**It is not 34 instruments.** Fourteen are variants inside three families: Henry Hub natural
gas (4 codes), WTI and Brent (3), and Mt Belvieu propane and NGL grades (7). The analytical
gain is nearer 23 new instruments than 34.

**Micro gold (`088695`) is the case to settle before the large ones.** Same underlying as the
covered `088691` at a tenth the contract size. Adding it without a view on aggregation puts
gold into every cross-market ranking twice at two scales, and `2026-08-02 §B30` is the
precedent: two lumber codes were one instrument, and merging them end to end lifted every rung
and changed no verdict.

**Adding any spec needs the Norgate producer**, which runs on the Windows box only. So the
backlog is not a code change in this repo, which is what the handoff's §0 means by "spec
coverage is a build backlog, not a boundary": we control it, and not from here.

---

## 4. Bottom line

The set of markets this package can score is **45 in the latest week**, 25 on Disaggregated
and 20 on TFF, and it is scoped by where contract specs exist. Every one of the 25 commodity
markets is a classic outright, all seven always-template markets are inside, and levered-holder
prominence is 3.7x that of the excluded markets. This is a set the fragility argument applies
to, so the handoff's gate passes and the work it gates is not blocked.

Of the 254 codes that drop out, 220 should never come back: 213 are environmental and power
certificates and 7 are differentials with no position value to compute. The genuine backlog is
34 codes, roughly 23 distinct instruments, headed by ICE Europe WTI, the Henry Hub complex and
canola, and it needs the Norgate producer rather than a change here.

In plain terms: the coverage is small, but it is small in the right way. It is not a random
quarter of the panel, it is very nearly exactly the classic exchange-traded commodity
contracts, which is where the crowding-and-forced-exit thesis was always meant to apply. The
one honest caveat is that the four energy markets carry a thin Managed Money book about half
the time, so their fragility readings deserve less weight than their size suggests.
