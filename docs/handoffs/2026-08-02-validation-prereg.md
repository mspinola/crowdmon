# Handoff: pre-registration for §10 validation, to be executed by a cold session

**Status:** **complete and frozen, awaiting execution.** Jointly drafted: §2 and §6 by the
composite author, §4, §5 and §7 by the commonality/impact session, §8 by the human.
**Frozen means frozen:** §7 is a pre-registration, so amending it after a result is seen
destroys the only thing it was for. Append an outcome section instead.
**Date:** 2026-08-02
**Lives:** here, permanently. **Runs:** in `npf`, through `crucible`. See §8.
**Target:** a session that has written none of this package
**Not for:** either session that built crowdmon. See §1.

---

## 1. Why neither builder can execute this

Agreed by both sessions, on two independent grounds.

**The boundary forbids it physically.** `tests/test_boundaries.py` refuses an import of
`crucible` and says why: "a package that can import the judge can render a verdict on its own
output. Keeping the import out means a directional strategy derived from this work has to
leave the package to be validated, **which is the seam**."

Read that precisely: it forbids **importing** crucible, not **describing** a validation. What
has to leave crowdmon is the execution, not the document. See §8.

**Governance forbids it procedurally.** `npf/AGENTS.md`: "Never render the verdict on a book
you authored in the same session." Between the two sessions active on 2026-08-01 to 08-02,
every engine in this package was written. That reasoning does not stop applying because the
next build-order step happens to be labelled validation.

**What the builders can legitimately do** is pre-register: commit to the tests before results
are seen, which is the standard pattern (`livebook/docs/PREREGISTRATION.md`). §2 is the
honesty problem with that here.

---

## 2. Declared priors: what has already been looked at

**This is the section that cannot be written by anyone else, and it is the reason the split in
§3 is what it is.** A pre-registration is only worth something if it commits before results
are seen. Parts of this one cannot, and the evaluator needs to know exactly which.

### March 2020 has been examined twice, and the answer reversed

| formula reading | lead-in (Oct19-Jan20) | event (Feb-Apr20) | after |
|---|---|---|---|
| `Phi` raw, per §A.9's formula | **1.18x** baseline | 0.75x | 0.89x |
| `Phi` percentile-ised, per §A.9's preamble | **0.76x** | 0.45x | 0.68x |

Under the first reading `D` looked mildly elevated before the drawdown, which is what §10 asks
for. Under the second it is below baseline throughout. **The apparent lead was an artifact of
a near-constant term** (`2026-08-01 §A15`, §A21). The percentile-ised reading is the one that
shipped.

Anyone specifying a March 2020 test after reading that table is choosing windows and
thresholds knowing which choices produce which answer. **That is why the test specification is
not this session's to write.**

### Other windows already seen

| window | mean `D_sell` vs baseline | reading |
|---|---|---|
| 2021 ags / lumber | 1.65x | percentile-ised |
| 2022 invasion | 1.88x | percentile-ised |

Both hand-chosen after the fact, on the same data, by the session that wrote the measure.
Neither is evidence and both were labelled as such where published
(`docs/analysis/2026-07-28-composite.md` §5).

### What has NOT been looked at

- Feb 2018, Aug 2024 yen carry, silver 2021, gold 2025: **never examined at all**, by either
  session, under any formula reading. These are clean.
- No episode has been examined with `D_buy`. Every look has been the sell side.
- No episode has been examined per-market. Every figure above is a cross-sectional mean.

**Those three are where an uncontaminated test can still be specified**, and the evaluator
should weight them accordingly.

---

## 3. The split, and why it is not the obvious one

The first proposal was that the `composite.py` author write the test specification, since they
own the module and ran the episodes. **That is backwards**, for the reason §2 makes concrete:
the value of a pre-registration lives in committing before seeing, and that author has seen
the answer flip sign.

| section | owner | rationale |
|---|---|---|
| §1 why neither builder executes | both, agreed | done |
| **§2 declared priors** | **composite author** | only they know what was looked at |
| **§6 reading instructions** | **composite author** | findings about modules they built |
| §4 data availability | commonality/impact session | measured it. **Done, and it overturned the shared premise** |
| §5 inputs inventory | commonality/impact session | done |
| **§7 test specification and thresholds** | **commonality/impact session** | **uncontaminated by §2** |
| §8 where this lives, where it runs | **decided by the human**, see §8 | not either session's call |

The composite author supplies the disclosure and the reading instructions. The other session
specifies the tests. Neither runs them.

---

## 4. Data availability

Reproducer: `docs/analysis/reproduce.py` section 13, against `COTDATA_STORE` as of
2026-08-02. Detail in [`2026-08-02 §B10`](../design/amendments-2026-08-02.md).

### The figure both sessions were quoting is right and does not mean what we said

Report dates do span 2025-01-07 to 2026-07-28, 82 weeks. From that both sessions concluded
that **gold 2025 is point-in-time and the other episodes are not**. That conclusion is wrong,
and the corrected version is worse for the evaluator, so it must not be discovered downstream.

| | measured |
|---|---|
| observations | 224,280 |
| distinct keys | 224,280 |
| **keys observed more than once** | **0** |
| capture timestamps | 2026-07-31 and 2026-08-01, two backfills |

**Every key in the store has exactly one observation, and all of them were taken this week.**
A report date reaching back to January 2025 records when the CFTC measured the position, not
when this store first saw the value. All 82 weeks were read from current state, after every
revision they have ever received.

So there is **no as-published value for any week, gold 2025 included**. The store holds one
vintage and it is today's. Point-in-time coverage is not 1 episode of 6. It is **0 of 6**.

### What that does to §10's mechanical test

§10 asks that "vintage replay reproduces historical values exactly". With one observation per
key, an as-of replay at *any* date returns the same values by construction, so that test
**passes trivially and demonstrates nothing**. It cannot fail today, which is the same thing
as saying it cannot pass today.

**Do not mark it passed. Defer it with a date.** It becomes a real test the first time a key
carries two observations with different values, which requires the store to sit through a
revision. Forward accumulation begins with the first weekly release after 2026-08-01.

### The release-date index is mostly a guess

`VintageCotSource` indexes on release date rather than report date, deliberately, because a
Tuesday report date embeds a three-day lookahead. That index is currently:

| release-date provenance | report weeks |
|---|---|
| `derived` (report_date + 3d, weekend-adjusted, **a guess**) | 51 |
| `scheduled` (from a published calendar, not observed) | 29 |
| `published` (observed) | **2** |

cotdata's `vintage_schedule` docstring is explicit that `derived` is "the fallback" and that
consumers "must be able to exclude `derived` rows from strict PIT evaluation". Under that
strict reading the usable panel is **2 report weeks of 82**.

This compounds the earlier shutdown finding rather than restating it. The Oct-Nov 2025
shutdown was recorded as leaving that window `derived`; the measurement here is that
`derived` covers everything through November 2025, not only the shutdown.

### What is therefore available, and what an evaluator should do with it

- **Available:** the full current-state panel, 27 markets from 2006, which is what every
  figure in `docs/analysis/` was computed on. `D` itself scores nothing before **2010-05-25**,
  because `C = pct(z)` stacks two three-year windows (`2026-08-01 §A16`). The 2008 GFC is
  unreachable and no amount of vintage accumulation changes that.
- **Not available, permanently:** as-published values before 2026-07-31. `cot_vintage.md` §5.3
  records this as a property of starting a vintage store late, not a gap to be filled.
- **Not available, temporarily:** as-published values from 2026-08-01 forward, which accrue
  one week at a time.

Consequence for §7: **every episode test is a current-state test**, and the size of the
resulting contamination is **not measurable in this store**, because measuring it needs the
revisions that have not been recorded. It would be easy to write "COT revisions are small"
here. There is no reproducer for that claim in this workspace, so it is not written here.

---

## 5. Inputs inventory

Reproducer: `docs/analysis/reproduce.py` section 14. Detail in
[`2026-08-02 §B11`](../design/amendments-2026-08-02.md).

### The headline: none of the three configured constants can move `D`

This is the sensitivity analysis an evaluator would reach for first, and it is already done,
with a null result. Spending a day on it would produce three columns of zeros.

| constant | value | sanctioned range | can it move `D`? | why |
|---|---|---|---|---|
| `kappa` | 0.2 | conventional | **no**, measured `0.00e+00` | `T = Q/(kappa.V)`, and `I = pct(T)` **within a market**, so a global `kappa` is a positive scalar under a monotonic transform |
| `Y` | 0.75 | `Y_RANGE = (0.5, 1.0)` | **no**, structurally | `Y` never enters `add_composite`. It feeds exit COST; `D`'s `I` is exit DURATION (`2026-08-01 §A19`) |
| `gamma` | 0.5 | **none, anywhere** | **no**, measured `0.00e+00` | `T_eff = T.(1 + gamma.beta_bar)`, same invariance (`2026-08-02 §B2`) |

`kappa` measured over 27,194 market-weeks on 27 markets, at 0.05, 0.4 and 1.0 against the
configured 0.2. Not "small". Bit-identical, at a fivefold cut and a fivefold rise.

**The `gamma` result was known and the `kappa` result was not**, and they are the same
argument. That is the warning worth passing on: this system percentile-ises within a market
at three separate points, and a percentile eats any global positive scalar. An evaluator who
does not notice will read a null as a robustness result when it is an algebraic identity.

### What does move `D`

| input | where | known effect |
|---|---|---|
| **fragility weight ORDERING** | `core/config.py` | inverted: **0 of the top 10** survive (`2026-08-01 §A22`) |
| fragility weight VALUES | `core/config.py` | +/-0.15 order-preserving jitter keeps **7-10 of the top 10**. Robust |
| **`phi_percentile`** | `add_composite(...)` | flips the March 2020 reading from 1.18x to 0.76x. See §2 |
| `window` / `min_periods` | `1095D` / 104 | sets the 2010-05-25 floor. Shortening it buys history and costs baseline |

The weights are five numbers with argued rationales, not fitted values, and `config.py` says
so at length. **Vary their order, not their magnitude.** The magnitude question is answered.

### The rest of the surface, for completeness

Configured elsewhere, none of it swept, all of it defensible-by-default rather than measured:

| where | constants |
|---|---|
| `futures/riskunits.py` | vol window 63, min periods 42, `MAX_NONPOSITIVE_RATE` 0.01, staleness 5d |
| `futures/volume.py` | ADV window 252, stress lookback 1260, stress decile 0.10, min periods 60/20 |
| `futures/commonality.py` | lambda window 21, beta window 252, min obs 500 |
| `futures/impact.py` | Amihud window 252, min periods 60 |
| `futures/trigger.py` | lookbacks (20, 60, 250), pool category `managed_money` |
| `core/config.py` | `DOMINANCE_TOLERANCE` 0.25 (swept: `flow.tolerance_sensitivity`), `GAP_DAYS_TOLERANCE` 0 |

**Three series choices are not parameters and must not be swept as though they were.**
`notional` requires `unadj`, `riskunits` and `volume` require `propadj`, `trigger` requires
`propadj`. Each refuses the others and each refusal carries a measured number
(`2026-08-01 §A8`, `§A9`, `§A20`, `2026-08-02 §B9`). An evaluator "testing robustness" by
swapping a series is not perturbing an assumption, it is introducing a known defect.

---

## 6. Reading instructions the evaluator needs first

Four things about `D` that are not discoverable from the number, gathered in the README and
repeated here because an evaluator who does not know them will mis-specify a test.

1. **`D` falls during an unwind, and that is correct.** It describes a pre-condition, and both
   the position and the forceable holders leave while the event happens. A test that expects
   `D` to peak *during* a drawdown is testing the opposite of what the measure claims.
   `2026-08-01 §A17`.
2. **`Phi` has no cross-market signal independent of the weight table.** Flat weights reduce it
   exactly to `1 - spreading/OI`. `2026-08-01 §A21`.
3. **Extremity readings persist.** 10.11% of weeks sit above the nominal 5% threshold, in
   episodes averaging 4.8 weeks and running to 42, with 57.6% of hot weeks inside runs of 8+.
   **Exceedances are not independent events**, so any test treating "weeks above the 95th" as a
   sample size has an effective sample roughly a fifth of its nominal one. `2026-08-01 §A11`.
4. **`D` assumes exits are independent across markets and they are not.** `pct(T_eff) ==
   pct(T)` bit-identically, so §A.6's commonality cannot enter `D` at all and must be read
   beside it. `2026-08-02 §B2`.

Plus the scope limit: **`D` scores nothing before 2010-05-25** on a 27-market panel, because
`C = pct(z)` stacks two three-year windows. The 2008 GFC is unreachable. `2026-08-01 §A16`.

---

## 7. Test specification

**Written 2026-08-02 by the commonality/impact session, before computing any statistic below.**

### 7.0 This session's own contamination, declared

§3 assigned this section here because this session had not seen the episode results. **It has
now read §2**, so March 2020 is no longer clean for this author either. That cannot be undone,
so it is handled structurally rather than apologised for:

**The test form is fixed on episodes neither session has looked at, and then applied to the
contaminated ones with zero free parameters.** Every window length, gap, statistic and
threshold below is chosen against the clean set in §7.2 and is not permitted to change when it
reaches §7.3. If a contaminated episode wants a different window to look good, it does not get
one.

### 7.1 The claim under test

Module spec §10: `D` is elevated **before** a forced-exit episode. Per §6.1, `D` falls
*during* the unwind and that is correct, so the test window ends before the event, and a test
of the event window itself would test the opposite of the claim.

### 7.2 The clean set, and what it is measured on

Established this session (reproducer: `reproduce.py` section 13 for the vintage figures,
and the panel/price checks in [`2026-08-02 §B12`](../design/amendments-2026-08-02.md)):

| episode | window | panel | markets, **fixed here and not to be revised** | direction |
|---|---|---|---|---|
| Feb 2018 vol unwind | 2018-02-05 | **TFF** | ES, NQ, RTY, YM, EMD | `D_sell` |
| Aug 2024 yen carry | 2024-08-05 | **TFF** | 6J, NKD | `D_buy` |
| Silver squeeze | 2021-02-01 | Disagg | SI | `D_buy` |
| Gold 2025 | 2025-04-22 | Disagg | GC | `D_sell` |

Two of the four are on **TFF, which has never been scored by either session.** The composite
analysis is Disaggregated only. The inputs exist: 22 of 24 TFF markets carry a `ContractMaster`
symbol, and all 21 checked have `unadj` and `propadj` prices with volume, back to 1979-2005,
well before `D`'s 2010 floor. **What has not been verified is that `add_composite` runs on
TFF end to end.** That is the evaluator's first task, and if it does not run, that is a
finding to report rather than a reason to drop the two clean episodes.

The two `D_buy` entries matter disproportionately: §2 records that **no episode has ever been
examined on the buy side**, so those two are the least contaminated evidence available.
Direction is set by who gets forced, not by which way price moved: a yen-carry unwind and a
silver squeeze both force **buying**, so both take `D_buy`.

### 7.3 The contaminated set, run identically

| episode | window | markets | direction | §2 prior |
|---|---|---|---|---|
| March 2020 | 2020-02-24 | all 27 Disagg | `D_sell` | seen, 1.18x raw / **0.76x** shipped |
| 2021 ags / lumber | 2021-04-01 | ZC, ZW, ZS, ZM, ZL, LBR | `D_sell` | seen, 1.65x |
| 2022 invasion | 2022-02-24 | ZW, CL, NG | `D_sell` | seen, 1.88x |

**Reported as replication, never as evidence.** These three do not enter the pass criterion in
§7.5 at any weight. They are run because a form that works on the clean set and fails here is
informative in the other direction, and because refusing to run them would let a reader assume
they were tried and hidden.

**March 2020 is additionally a wiring check, with its target stated here in advance.** The
composite author's contamination is a liability everywhere else in this document and an asset
in exactly one place: because §2 published the answer, this episode has a **known expected
value**, and reproducing it tests the implementation rather than the market.

> **Expected: the March 2020 lead-in returns approximately 0.76x baseline** under the shipped
> percentile-ised reading, per §2. This is committed before the form is run.

Judge that check on **reproduction, not implication**. A result far from 0.76x is a defect in
the implementation of §7.4, not a finding about 2020, and it must be fixed before any clean
episode in §7.2 is scored. A result near 0.76x says the wiring is right and says nothing
whatever about whether `D` works, since 0.76x is *below* baseline and was the measurement that
retired the apparent lead in the first place.

This check has no bearing on §7.5. It is a precondition for running §7.5, not an input to it.

### 7.4 The statistic

1. **Unit of observation: one number per (market, episode).** Not per week. §6.3 measures that
   exceedances cluster (mean run 4.8 weeks, 57.6% of hot weeks inside runs of 8 or more), so a
   week-level test would overstate its sample by roughly five times. Collapsing to one number
   per market-episode removes the problem rather than correcting for it.
2. **Lead-in window: the 13 report weeks ending 14 days before the episode date.** One quarter,
   with a two-week gap so a slow-forming event cannot leak into its own predictor.
3. **Per-unit statistic:** the **median** of `damage_{side}_pct` over those 13 weeks. Median,
   not mean, because `D` is already a percentile and a single spike should not carry a quarter.
4. **Reference distribution:** the same market's `damage_{side}_pct` over all weeks at least 26
   weeks away from *any* episode in §7.2 or §7.3, **block-bootstrapped in 13-week blocks**,
   10,000 draws, `seed=20260802`. Blocks preserve the persistence in §6.3; an IID bootstrap
   would not.
5. **Pooled statistic:** the unweighted mean of the per-unit medians across the 9 clean
   (market, episode) pairs. Unweighted, because weighting by open interest would make Feb 2018
   a test of ES alone.
6. **p-value:** the fraction of bootstrap draws whose pooled statistic is at least the observed.

### 7.5 Pass criteria, committed before looking

| outcome | criterion |
|---|---|
| **supported** | pooled p < 0.05 **and** at least 6 of the 9 clean units have a lead-in median above 0.50 |
| **contradicted** | pooled median at or below 0.50, or 5 or more of 9 units below it |
| **uninformative** | anything else, including p between 0.05 and 0.20 |

**Both halves are required.** The p-value alone can be carried by one market inside one
episode, which is exactly the failure §6.2 warns about in a different guise.

**Pre-committed statement about power, so a null is not over-read.** Nine correlated units
across four episodes is a small test, and it is the largest clean test this data admits. A
`supported` verdict here is weak positive evidence, not a `REAL` pillar. **`uninformative` is
the most likely outcome and is not a failure of the measure.** Recording that in advance is
the point of pre-registering it.

### 7.6 What is forbidden

Each of these turns the test into a restatement of its own inputs.

- **Selecting affected markets by looking at `D`.** The lists in §7.2 and §7.3 come from the
  public description of each episode and are frozen. Add nothing.
- **Adding episodes.** §10's replay list plus nothing.
- **Using `D_sell` for a squeeze**, or `D_buy` for a long unwind. Direction is fixed above.
- **Swapping a price series** to test robustness. Per §5 those are not parameters, and each
  substitution introduces a defect with a measured magnitude.
- **Sweeping `kappa`, `Y` or `gamma`.** Per §5 they cannot move `D`, measured at `0.00e+00`.
  Vary the fragility weight **ordering** and the `phi_percentile` reading instead.
- **Treating report weeks as independent.**

### 7.7 crucible integration

Under npf governance the denominator is the whole search, so the count is stated here rather
than reconstructed later. The primary run is **one variant**: the single form in §7.4. Every
robustness run (window 9 or 17 weeks, gap 0 or 28 days, mean instead of median, block length 8
or 21, `phi_percentile=False`) is a **further variant and must be counted in the
`SearchSpaceLog`** whether or not it is reported. That is **11 variants** if the full
robustness set is run, and the evaluator must pass the log itself to
`run_gauntlet(..., n_variants=log)` rather than a hand-written integer.

### 7.8 Deferred, with a reason and a date

Per §4, §10's mechanical test that "vintage replay reproduces historical values exactly"
**passes trivially today** because no key has been observed twice. Do not record it as passed.
It becomes executable once the store has sat through a revision, which needs weekly releases
after 2026-08-01 to accumulate. Re-check no earlier than **2026-11-01**, by which point roughly
13 releases will have landed.

---

## 8. Where this lives, and where it runs (DECIDED)

**Decided by the human, 2026-08-02.** Both sessions had read the boundary as putting the
document out of scope too. It does not.

| | where | why |
|---|---|---|
| **this document** | stays here, `crowdmon/docs/handoffs/` | the boundary forbids importing `crucible`, not describing a validation |
| **the execution** | an evaluator session in `npf`, which has `crucible` | that is the seam the boundary draws |
| **the verdict** | `npf/docs/` | written where it is run, by whoever ran it |

The reasoning worth preserving: this splits the difference **without hiding a public package's
pre-registration inside a private repo**. crowdmon is public and `npf` is not. A prereg that
lives where the thing it constrains cannot be read by the same audience is a weaker prereg,
whatever directory it sits in.

Consequences for the evaluator:

- Read this file from crowdmon. Do not copy it into `npf`, because that opens exactly the
  silent-regression window CLAUDE.md describes, where a duplicated living document drifts
  until someone happens to diff the copies. Cite the path.
- The verdict document in `npf/docs/` is the new artifact, and it is the one that may cite
  `crucible`. Nothing in this repo changes when it lands.
- This handoff stays **append-only** either way (`docs/handoffs/` lifecycle). The outcome gets
  appended here with a pointer to the `npf` verdict, not written over §2 or §6.

---

## Open questions for the human

1. ~~Does the split in §3 stand?~~ **Accepted by the commonality/impact session**, with the
   contamination it introduces declared in §7.0 rather than argued away.
2. ~~Where does this document live once complete?~~ **Answered, §8.**
3. ~~Is §10 validation even next?~~ **They are parallel**, and neither blocks the other. §A.8
   is the composite author's and its horizon blocker is answered in
   [`2026-08-02-reflexivity.md`](2026-08-02-reflexivity.md). This document is finished and
   waiting on a session that neither of us can supply.

### The one thing still needing a decision

**Who is the cold session, and when.** This pre-registration is frozen as of 2026-08-02, and
a frozen prereg decays: every further week of building in this package is another week of
findings the eventual evaluator will have read before running §7. Two of the four clean
episodes rest on TFF, which nobody has scored yet, and **the first session to score TFF spends
that cleanliness**. If §7 is not going to be executed reasonably soon, say so, because the
honest alternative is to score TFF for other purposes and record here that the clean set
shrank to two Disaggregated episodes.
