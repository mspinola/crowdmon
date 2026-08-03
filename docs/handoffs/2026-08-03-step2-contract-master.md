# Handoff: contract spec inventory, then contract master

**Status:** complete (PR #NN), Task 1 executed, Tasks 2-3 found already shipped
**Date:** 2026-08-03
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-step2-contract-master.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** PR #44 merged; local checkout pulled current
**Deliverable:** Task 1 always; Tasks 2-3 only if Task 1's gate passes

---

> The body below is the work order **as issued**, preserved verbatim per this directory's
> rule. The outcome is appended as §5 and corrects two of its premises. Read §5 before
> acting on anything here.

## 0. Scoping decision, now made

The monitored universe is scoped by **where contract specs exist**, not by where the cocoa
shape holds.

Rationale: 25 of 279 Disaggregated codes currently produce a real `dtl_sell`; the other 254
are all missing a contract spec, none are missing volume. Everything downstream of the
contract master is already scoped this way in practice. Template classification was the
alternative criterion and is unsuitable: §B36 found 22 of 39 markets extreme over the pooled
window but only 17 in both halves, with cocoa running 0.976 then 0.100. A scoping rule built
on an unstable classification inherits that instability.

Consequence worth stating plainly: **spec coverage is a build backlog, not a boundary.** It is
something we control. So template-consistency and Managed-Money-size stop being scoping
criteria and become prioritisation criteria for which specs to add next. That is a better use
for both.

## Task 1 — Inventory first, and gate on it

Do not write the contract master before this is done and reported. The instinct is to build it
and then see what it covers. Reversed: establish what the covered set actually is, and confirm
it is analytically usable, before building normalisation on top of it.

### 1a. Enumerate the covered set

For the 25 codes with a real `dtl_sell`: market code, name, exchange, complex, and mean open
interest over the vintage panel.

### 1b. Answer the gating question

Are those 25 markets where the fragility argument means anything? Cross-reference against what
is already measured:

- **Complex distribution** — how many are metals, softs, grains, livestock, energy, and how
  many are ICE power/gas/carbon basis contracts
- **Stratum** — classic outright versus power/gas/carbon venue
- **Managed Money prominence** — median `|P_MM| / OI`, since §B33 showed energy outright is
  genuinely thin, with 58.1% of market-weeks under 5% of OI
- **Overlap with the always-template set** (gold, silver, copper, live cattle, feeder cattle,
  coffee, RBOB)

The failure mode this gate exists to catch: if the 25 are mostly ICE basis contracts rather
than the metals and livestock where the shape holds, the coverage is technically real and
analytically empty. Building roll calendars and normalisation on that set would be effort
spent on markets the thesis does not apply to.

### 1c. Split the 254

"No contract spec" almost certainly conflates two different problems:

- **Missing** — a real, tradeable contract whose spec we simply have not entered. A backlog
  item.
- **Inapplicable** — a code with no meaningful spec to have. A permanent exclusion.

Classify each of the 254 and report the split. These need different handling and should not
sit in one undifferentiated bucket.

### 1d. Report and stop if the gate fails

If the covered set is not analytically usable, stop and report rather than proceeding to Task
2. The correct next action in that case is adding specs for a prioritised set, not building
the contract master over an empty one.

If the gate passes, continue.

## Task 2 — Contract master

Module spec §13 step 2. Per covered market:

- Multiplier, currency, tick size
- Daily price limit rules where they exist (ags and some energy). §8 of the module spec treats
  a limit day as `V = 0`, a hard constraint with no equity analogue
- Roll calendar and first notice date

Continuous series: **ratio-adjusted**, so returns are correct. Retain the **unadjusted**
per-contract series separately: notional and margin calculations need unadjusted prices, and
one series cannot serve both. This is stated in the module spec §5.1 and is easy to get wrong
once.

Specs are a **maintained data asset, not code**. Keep them in config with a source noted per
field, so a wrong multiplier is traceable rather than mysterious.

## Task 3 — Normalisation ladder

Appendix §A.4. In order:

```
P  ->  P / OI  ->  P · M · F  ->  P · M · F · σ
```

The final form, vol-scaled notional, is the default for every cross-market comparison, because
risk limits are denominated in risk rather than contracts.

Then extremity: rolling z-score over a 3-year window, winsorised, reported as a percentile of
own history. Raw levels are not comparable across markets and should not be surfaced as if
they were.

This unblocks: real `T = Q / (κV)` replacing the `Q_sell / OI` proxy, and the square-root
impact estimate. Both were structured to take volume as an optional argument, so slotting it
in should not require a rewrite. **Confirm that holds rather than assuming it.**

## Applies throughout

The degenerate-input rule (`CLAUDE.md`). This task is dense with the failure mode: joining
specs to markets, aligning price series to positioning, computing ratios where a missing
denominator produces a plausible null. Three instances have already been caught late in this
package, two of which actively supported a false conclusion.

Specifically here:

- A market with a spec but no price data must be distinguishable from one with neither
- An all-null normalised column is a failure condition, not a result
- Any labelled input that must align with another gets its index validated and **raises** on
  mismatch. A docstring is not a safeguard
- Ratio-adjusted and unadjusted series must not be silently interchangeable

Also verify while in the area: whether `rank_markets` now validates index alignment, or still
relies on the docstring. That was §C5's trap and it should be structurally closed, not just
documented.

## Report back

- Task 1a: the covered set, with complex and stratum
- Task 1b: the gate verdict, is this set analytically usable, and on what evidence
- Task 1c: the missing/inapplicable split of the 254
- Task 2-3 if reached, or a prioritised list of specs to add if not
- Whether `rank_markets` alignment is structurally closed
- Anything contradicting this handoff, corrected in place

Do not proceed past Task 3. Cross-market PCA and trend alignment are the following step and
depend on normalisation being settled first.

---

# §5. Outcome, 2026-08-03

**Executed by:** a session that had written none of the modules under review
**Analysis:** [`../analysis/2026-07-28-contract-spec-inventory.md`](../analysis/2026-07-28-contract-spec-inventory.md)
**Amendments:** [`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C11-C14
**Reproducer:** [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`

## 5.1 The largest finding: Tasks 2 and 3 were already shipped

**This handoff was filed against a state of the repo that was already a day out of date, and
its own README says why that is expensive.** Tasks 2 and 3 ask for the contract master and the
normalisation ladder. Both exist, are tested, and are documented in `CLAUDE.md`'s layout table:

| task | asked for | already shipping |
|---|---|---|
| 2 | multiplier, currency, tick size | `futures/contract_master.py`, 269 lines |
| 3 | `P · M · F` | `futures/notional.py` (rung 3), refuses anything but `unadj` |
| 3 | `P · M · F · σ` | `futures/riskunits.py` (rung 4), refuses anything but `propadj` |
| 3 | rolling z, winsorised, percentile | `futures/extremity.py` + `core/aggregate.py` |
| 3 | "unblocks real `T = Q/(κV)`" | `futures/pressure.py`, and `volume.py` supplies `V` |

Nothing was rebuilt. **This is the third instance of the failure the handoffs README exists to
prevent** ("Two modules were built twice in one afternoon because each session started the
obvious next piece without re-checking"), and the first where the duplicate work was requested
in writing rather than assumed.

Task 3's one genuinely open instruction was its last line, "confirm that holds rather than
assuming it", about whether volume slots in without a rewrite. It does, and §5.4 is what
checking it turned up.

Task 2 has **two items that are genuinely unbuilt**, and both are blocked on data rather than
effort, which the handoff could not have known:

- **Daily price limits.** No price-limit table exists anywhere in the workspace. `CLAUDE.md`
  lists this as a standing data block. §8's `V = 0` treatment cannot be implemented.
- **Roll calendar and first notice date.** `futures/roll.py` ships roll-window volume, but all
  three components of spec §379 are blocked because the price frame's `Open Interest` is
  whole-market. Recorded at `2026-08-02 §B19`.

## 5.2 Task 1a and 1b: the gate PASSES

Full table in the analysis document §1.2. The four gate readings:

| reading | result |
|---|---|
| stratum | **25 of 25 real outright, 0 power/gas/carbon** |
| complex | Grains 6, Softs 6, Metals 5, Energies 4, Live Stock 3, Dairy 1 |
| always-template overlap | **7 of 7** |
| median `\|P_MM\|/OI` | covered **0.1371**, uncovered **0.0370** |

The failure mode §1b screens for is **absent rather than rare**. Against a panel that
`2026-08-02 §B31` measured as 76% ICE power and Nodal basis, zero covered markets are basis
contracts.

**§1b's quoted 58.1% is close but not the figure this measured.** Pooled over the four covered
energy outrights, 51.2% of market-weeks have Managed Money under 5% of OI (n=328), against
13.9% elsewhere in coverage. The handoff's 58.1% comes from `2026-08-02 §B33`, whose energy
population is not identical to "the covered energy outrights". The finding transfers; the
number belongs to a different set, and this is the citation-by-bare-number problem `§3` of
`2026-08-03-b-series-recovery.md` legislated against.

## 5.3 Two corrections to the premises

**The universe is 45 markets, not 25** (§C12). The handoff counted one report type. The spec
table holds 47 symbols; 26 reach Disaggregated and 21 reach TFF (union over 82 weeks), summing
to exactly 47, and in the latest week it is 25 + 20 = 45. The 22 "absent" symbols are
currencies, equity indices, rates and crypto, which CFTC does not publish on Disaggregated at
all. **§0's scoping decision is unaffected**; it is the count under it that was understated by
a factor of 1.8. Anything sized against "25 markets" should be sized against 45.

A sub-finding no coverage figure in this package had stated: **the count is report-week
dependent.** Oats is spec'd, priced, and in only 23 of 82 weeks, so a count taken on another
week is legitimately 26 with nothing having changed.

**"No contract spec" is three populations, not two** (§C14). Beyond `missing` and
`inapplicable` there are **7 differentials** (`WTI MIDLAND ARGUS VS WTI TRADE`, `GULF # 6 FUEL
OIL CRACK`, and five more). They have a multiplier and a tick size, so they are not
"inapplicable" as §1c defines it, and they are still permanent exclusions: the ladder computes
a position value and a differential does not have one. The measured split is **213 certificate
/ 7 differential / 34 real outright**.

The backlog is therefore **34 codes, roughly 23 instruments** (fourteen are variants inside
the Henry Hub, WTI/Brent and Mt Belvieu families). Prioritised head: ICE Europe WTI (798,670
mean OI), the Henry Hub complex, canola. **Micro gold should be settled before any of them**,
because it duplicates a covered market at a tenth the size and `2026-08-02 §B30` is the
precedent for merging before ranking.

## 5.4 `rank_markets` alignment: was NOT closed, now is (§C11)

Answering the handoff's direct question: it **still relied on the docstring**. `§C5` found the
trap, wrote it down, and changed nothing in code.

`rank_markets` documented `volume` as "aligned to `fragility`'s index", which is *positional*,
while the frame carries a `market_code` column that makes a `market_code`-indexed Series the
natural thing to pass. It was silently `reindex`ed to all-`NaN`. That output is a valid answer
to a different question ("no volume was available"), which is why `§C5`'s own first attempt
returned 0 of 279 and read as confirmation of a claim that was false.

Now raises. The check is on **labels, never values**, so the ordinary partial-coverage case (25
of 279 markets have a volume) stays expressible as `NaN` values under matching labels. Guarded
by two tests, one for the trap and one pinning the ordinary case so the guard cannot later be
tightened into rejecting it.

## 5.5 What is open

Task 1 is complete and its gate passed, so the handoff's own condition to continue is met.
Tasks 2-3 need nothing except the two data-blocked items in §5.1, both of which are already
tracked as standing blocks.

**Nothing here unblocks cross-market PCA or trend alignment, and neither needed unblocking:**
`futures/macro_pca.py` and `futures/alignment.py` both shipped on 2026-08-02. The handoff's
closing instruction not to proceed past Task 3 is moot for the same reason its Tasks 2-3 were.

The one decision this leaves for a human: **whether to spend the Norgate producer time on the
34-code backlog at all.** The gate passing means the current 45 are usable, not that the
backlog is valuable, and the analysis document deliberately stops short of recommending it.
