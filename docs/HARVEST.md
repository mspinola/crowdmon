# Harvest: what outlives this package, and where it went

`crowdmon` is being deprecated: its hypothesis is unproven and out of testable evidence, four
pre-registered tests having returned `uninformative`, two genuine nulls, and one marginal lean
that was mostly artifact. The decision itself and the conditions under which it would be
revisited are recorded separately, and this file is **only the map of what its measurements
left behind**.

That distinction is the point of the harvest. The hypothesis failing says nothing about the
measurements made along the way, several of which are durable facts about data that other
packages own. They would be orphaned by a repo going quiet rather than by being wrong.

This file is the map. It classifies every numbered finding in
[`design/amendments-*.md`](design/) as one of:

| class | meaning |
|---|---|
| **PORTED** | a durable fact a sibling owns, **restated in that sibling and merged**, with provenance back here |
| **TO PORT** | identified, owner named, **not yet restated**. Still only readable here |
| **RESOLVED** | already fixed or already moved before this harvest. Nothing to do |
| **DIES** | true, and about the composite hypothesis, the weight table, or this package's own internals. It has no consumer once the hypothesis is parked |

**PORTED and TO PORT are kept apart on purpose.** A harvest that marked everything done on the
day it was planned is the same failure as a status line that goes stale: the next reader would
have no way to tell which facts had actually reached a surviving package. Only the rows below
that say PORTED have been written somewhere else.

**The amendments files are not edited by this harvest and must not be.** `analysis/` and the
amendment series are point-in-time records under this repo's doc lifecycle: a harvest that
rewrote them would destroy the record of when each thing was learned, which is the only reason
a reader can check the claim "the data contradicted the brief". Porting means **restating the
fact in the owning repo and citing the section here**, never moving or deleting the section.

**A DIES classification is not a claim that the finding is wrong.** Most of them are correct
and were expensive to establish. It means no surviving package reads them.

---

## PORTED to `cotdata`

Two documents, both read in full and restated rather than summarised from headers.

**[`cotdata/docs/design/cross-report-comparability.md`](../../cotdata/docs/design/cross-report-comparability.md)**

| finding | what carries |
|---|---|
| **D7** | **Legacy and TFF agree on exactly two quantities**, `open_interest` and `nonreportable`, over 6,279 overlapping market-weeks at 100.0000%. Above the reportable line the obvious mapping fails ~85% of the time, for two compounding reasons that no correction recovers: spreading is counted differently (Legacy breaks it out for non-commercial only), and the buckets hold different traders. **Any quantity built by subtracting one report's category from another's is not interpretable.** Same shape as the Supplemental trap |
| **D7, second half** | **`canonicalize_legacy` sets `spread_contracts` to `NA` on every row**, so summing that column returns 0, which prints as a measurement of zero spreading and is not one. The identity `long + spread == OI` closes on 99.984% of TFF market-weeks and **19.857%** of Legacy ones. A live trap in cotdata's own API, not a crowdmon concern, and confirmed still live at harvest time |
| **A1** | The Oct-Nov 2025 shutdown left COT **report** dates intact and broke only **release** dates |
| **A2** | Gaps come from **thin markets falling out of the report**, not from data loss. Oats (`004603`), 294-day interval ending 2025-09-09 |

**[`cotdata/docs/design/reading-the-store.md`](../../cotdata/docs/design/reading-the-store.md)**

| finding | what carries |
|---|---|
| **A5** | **76% of the 279-market Disaggregated universe is ICE Energy Div / Nodal power and gas basis.** A cross-market result over the full universe is mostly about ERCOT and PJM |
| **A14**, **C12** | **A coverage ratio whose denominator nobody chose is not a measurement.** Withdrawn twice now, in two packages. Ported as the rule plus the warning that the count itself moves (25, then 45, then 47), rather than as any one number |
| **A13** | **The fuller-sounding volume parameter is the narrower series.** `reconstructed` is exactly two expiries; `front` is whole-market, established by open interest matching the CFTC on 25 of 26 markets at a median ratio of 1.000 |
| **B26, B27, B30** | **A hole in a code's series is two different things**, and only one is a migration. RTY worked example, the lumber contrast, and the ordering rule: the merge across sibling codes must precede any differencing, because the other order fails silently |
| **D14** | **`propadj` is derived on read, Norgate is the only vendor supplying all tiers and is Windows-only by mechanism, and databento owes only `backadj`.** Composed: a databento-backed store cannot produce `propadj` at all. A live constraint on ADR-0007 step 2, and a **tier fact rather than an OS fact** |

## TO PORT, not yet done

Identified and owned, still readable only here. **These are the remainder of the harvest.**

| finding | owner | what carries |
|---|---|---|
| **A11** | `cotmetrics`, consumed by `npf` / `crucible` | **Extreme positioning readings persist far longer than a percentile implies.** Over 117,940 scored market-weeks: 10.11% above the 95th percentile against a nominal 5%, mean run 4.8 weeks, 90th percentile 12, longest 42, and **57.6% of hot weeks inside runs of 8+ weeks**. A 95th-percentile reading is the middle of an episode. **Anything treating "weeks above the 95th" as a sample size has an effective sample roughly a fifth of nominal.** A11's own text says the measurement belongs downstream |
| **C16** | `cotmetrics` | **Correlating positioning LEVELS across markets is spurious**, and an earlier section here led with exactly that error |
| **B33, B34** | `cotmetrics` | Managed Money's coin flip is in the **sign**, not the size, and is a mixture rather than a per-week 50%. A median asymmetry of 0.993 is **direction cancelling**: the same book measured without a direction gives 3.0237 |

`cotmetrics` has no `docs/` directory today, so these need a home created rather than a file
appended, which is why they are not in this pass.

---

## RESOLVED before this harvest

| finding | where it went |
|---|---|
| **A8** | Volatility needs `propadj`, not `backadj`. Corrected on cotdata `main` in `ff2b755`, which also fixed the cause: the availability table listed two options where there were three |
| **A9** | `propadj` is not strictly positive (crude, 2020-04-20). `cotdata/src/cotdata/prices.py` now states the correction in the docstring itself |
| **B29** | The two flow decompositions were one function. Deduplicated in cotdata #93; `zero_sum_check` stayed in cotdata as a claim about its own parse |
| **C5** | "There is no volume" survived in three places after volume shipped, one of them in code. Fixed at the time |
| **C9** | The stale PyPI inference did not propagate here. The root `CLAUDE.md` carries the corrected version |
| **B10** | The vintage store held zero point-in-time observations. Superseded by time: vintages accumulate forward from 2026-07-31, and §7.8's replay is date-gated to 2026-11-01 rather than blocked |
| Supplemental report facts | Authored in `cotdata` from the start (`cotdata/docs/analysis/2026-08-03-cit-supplemental-measurements.md`). Nothing to move |

---

## DIES with the hypothesis

Correct, and with no consumer once the composite is parked. Listed so that a future reader
can see they were considered rather than missed.

**The composite and its terms**: A3, A4, A15, A17, A19, A21, A22, B2, B5, B8, B11, B13, B14,
B15, C2, C3, C6, C7, C8, C10, C23, C29, D2, D3, D4, D5, D6.

**The weight table**: A21, A22, C6, C7, C8, C10, and the whole
`2026-08-03-swap-dealer-weight-decision.md` lineage. The one durable part of that lineage,
that a single weight was doing opposite work in two regimes, is a statement about the weight
table and does not survive it.

**Template shapes**: B28, B31, B32, B35, B36, B37, C1. The producer-short / fund-long
"template" is a crowdmon construct.

**The trigger and the offside term**: D9, D10, D12, D13, and both 2026-08-06 handoffs. See
the deprecation notice for what happens to the one presentation change left unstarted.

**Package internals, engines, and reporting**: A6, A7, A10, A12, A16, A18, A20, B1, B3, B4,
B6, B7, B9, B12, B16, B17, B18, B19, B20, B21, B22, B23, B25, C11, C13, C14, C15, C17, C18,
C19, C20, C21, C22, C24, C25, C26, C27, C30, D8, D11, E1, E2, E3, E4, E5.

**One in that list is worth a second look before it goes: B24.** "An eigenvector's sign is not
identified, and a signed cosine reports the flip as news" is a general numerical fact, not a
crowdmon one. It is filed as DIES because nothing in a surviving package currently runs a PCA.
If one ever does, this is the section to read.

**Two more that are general rather than local, filed as DIES for the same reason: B13** (`l·g`
grows as the square root of the pool, not linearly, and the linear reading invented a blow-up)
and **B14** (which cascade step is worst is a race, and both written-down answers were wrong).
Both are about reasoning by analogy failing against measurement, which is the lesson this repo
produced most often and the one least tied to its hypothesis.

---

## What this harvest deliberately does not do

- **It does not delete anything.** The amendments, the analyses and the handoffs stay exactly
  as they are. Deprecation is not deletion, and a reader arriving from a citation in another
  repo has to land on the real text.
- **It does not re-verify the DIES list.** Those findings were measured once, recorded with
  reproducers, and are being parked rather than retracted.
- **It does not carry the hypothesis forward in a new home.** If the composite is ever
  revisited, it starts from the deprecation notice's stated conditions, not from a fragment ported
  into a package that never asked for it.
