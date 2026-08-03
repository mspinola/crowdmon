# Handoff: template finding follow-ups + doc corrections

**Status:** complete
**Date:** 2026-08-02
**Lives at:** `docs/handoffs/2026-08-02-template-followups.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** flow decomposition + fragility work (complete); B28/B31 template analysis (complete)
**Deliverable:** five measurements answered, two design docs corrected

> Update `Status:` to `complete (PR #NN)` when executed.

---

## 0. Context

The template analysis established that the cocoa shape is real where cocoa lives and a minority elsewhere: 44.7% among classic outrights against 26.8% at power/gas/carbon venues, over 82 vintage weeks and 21,756 market-weeks. Two structural findings came with it:

- **The producer-hedged short side is robust** (Producer/Merchant net short in 69.2% of classic-outright market-weeks), but **the fragile levered long side is a coin flip** (Managed Money net long in 50.0%). The thesis rests on the half that fails.
- **It is a mixture, not a per-week probability.** 64% of markets sit at one extreme. The universe partitions into template and non-template markets.

This handoff pursues the five questions that follow, all answerable by measurement, and corrects two errors in the design docs that the analysis exposed.

**Working agreement applies:** measure, don't assume. If a measurement contradicts a doc, fix the doc in the same PR and say so. Report negative results as findings — three prior beliefs in this project have already failed against better data, and the failures were more valuable than the confirmations.

**Do not guess at generating mechanisms.** The prior session's discipline on this was correct. Where a hypothesis is offered below it is explicitly labelled as one to be tested, not assumed.

---

## 1. Managed Money conditional magnitude given sign

**The question this settles.** MM net long in 50.0% of classic-outright market-weeks admits two very different readings:

- **Absence of positioning** — MM is small and directionless in these markets. The fragility argument genuinely fails.
- **Symmetric large positioning** — MM swings between large net long and large net short. The market is highly fragile; the template merely names the wrong direction half the time.

These have opposite implications and the current measurement cannot distinguish them.

**Compute**, restricted to the classic-outright stratum, per market and pooled:

```
|P_MM| / OI    conditional on P_MM > 0
|P_MM| / OI    conditional on P_MM < 0
|P_MM| / OI    unconditional distribution
```

Report the median and the interquartile range for each, plus the share of market-weeks where `|P_MM| / OI < 0.05` (a reasonable "directionless" threshold — state it, don't hide it, and show sensitivity to 0.02 and 0.10).

Also report the same for `w_c · |P_c| / Q_total` so the contribution to fragility is visible directly rather than inferred from position size.

**Report per complex** (metals, softs, energy, grains, livestock), since the template rate already varies sharply across them.

---

## 2. Direction-agnostic asymmetry

**The question this settles.** The template as specified encodes a direction. What the thesis actually requires is a levered concentration on *some* side that can be forced out — direction is incidental.

Define:

```
A_directional     = Q_sell / Q_buy
A_agnostic        = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)
```

Recompute the stratum table with `A_agnostic` and report how much of the previously "inverted" 25.0% reclassifies as template-consistent under the direction-agnostic reading.

**Carry the ceiling caveat explicitly.** Both ratios are bounded above by `max(w) / min(w) = 10.0` — a property of the weight table, not of any market. Report `A_agnostic` alongside the ceiling and as a fraction of it, exactly as B31 did. The median of 0.993 for `A_directional` is the number that matters most; report the `A_agnostic` median the same way.

**Do not change the weight table in this session.** Whether the 10× spread is right is a design question being handled separately, and it depends on §1's result. Measure under the current weights.

---

## 3. Swap-dealer share as a predictor of non-template status

**Hypothesis to test, not to assume.** Cocoa's largest net long is the Swap Dealer (+22,894 latest, largest in 47 of 82 weeks), which puts the would-be fragile capital at `w = 0.4` rather than 1.0. Crude and natural gas — never template, in every code in the store — also have large swap intermediation. The hypothesis is that swap-dealer prominence displaces Managed Money on the long side and thereby suppresses the template.

**Measure:**

```
swap_share = (L_SD + S_SD) / (2 · OI)          gross swap-dealer share
```

per market, averaged over the 82 weeks. Then:

- Correlation and rank correlation between `swap_share` and template rate, within the classic-outright stratum
- The same split by complex, since complex is a confound — if the relationship vanishes within complex, it is a complex effect wearing a swap-dealer costume
- Whether `swap_share` separates the always-template set (gold, silver, copper, live cattle, feeder cattle, coffee, RBOB) from the never-template set (all crude and gas codes, SRW wheat, rice)

**If the CIT supplemental report is available in the store**, also report index-trader share for the ag markets it covers. That directly tests whether the swap-dealer book is index flow rather than levered flow, which is the distinction that matters for weighting. If it is not ingested, say so — do not fetch it in this session.

**Negative result is a real outcome.** If swap share does not predict, report that plainly; it retires my hypothesis, which is the point of testing it.

---

## 4. Stability and seasonality across the 82 weeks

**The question this settles.** The reported 82-of-82 consistency is for the *gap* between ag/metal and power/gas venues. That is a different claim from stability of the *level*, and 82 weeks is roughly 1.6 years — enough for two harvest cycles, not enough to separate structure from regime with confidence.

**Measure:**

- Classic-outright template rate as a weekly time series. Trend? Level shift? Report a simple linear fit and eyeball the series; do not over-model 82 points.
- Per-complex template rate as weekly series. Is the metals-over-grains ordering stable week to week, or does it invert at any point?
- **Seasonality**, for ag and livestock specifically: template rate by week-of-year, or by month. Producer hedging follows the crop calendar, so a template rate that peaks at harvest and troughs off-season is a seasonal artifact rather than a structural property. This is the single most likely way the current ordering is misleading.
- Whether any always-template or never-template market changes classification within the window.

**State the coverage limit in the writeup.** With 1.6 years, seasonality can be observed but not confidently separated from trend. Say what the data can and cannot support rather than reporting a point estimate as if it settled the question.

---

## 5. Doc correction — real worked example in §A.2

`docs/design/crowdmon_plain_language_summary.md` §A.2 uses a constructed cocoa example. Two problems the analysis exposed:

1. **Cocoa does not currently show the cocoa shape.** Managed Money is net short (−8,773); the largest net long is the Swap Dealer. The example's Managed Money at +90,000 beside Swap Dealer at +10,000 is the reverse of the real market.
2. **The example sits at 90.5% of the mechanical asymmetry ceiling** (9.05× against a bound of 10.0), while the median real market is at 0.993 — no asymmetry at all. It was constructed at an extreme without that being stated.

**Replace with a real market** from the always-template set — gold or live cattle, whichever shows the structure most clearly — using actual COT values from a stated report date. Keep the existing format exactly: category table, then `Q_sell` / `Q_buy` / `Phi` with arithmetic shown, then a prose reading. Carry the same market through the A.5 and A.7 "continued" blocks so the worked thread stays consistent.

**Retain the constructed example**, relabelled, as an explicit illustration of an extreme case — with its position relative to the ceiling stated. It is useful precisely because it is extreme; it was misleading only because it was presented as typical.

**Add a short subsection** recording the template finding: the stratum table, the 69.2%/50.0% asymmetry between the robust short side and the coin-flip long side, the mixture result, and the per-complex ordering. A reader of the appendix should not come away believing the shape is universal.

---

## 6. Doc correction — weight-ceiling property

`docs/design/crowdmon_futures_cot_module.md`, fragility section (§6.3).

**Add explicitly:** any asymmetry metric built on the fragility weights is bounded above by `max(w) / min(w)`, currently 10.0. The weight table therefore determines the metric's range before any data is involved. Verified at zero breaches across 21,756 market-weeks.

This is a real design constraint that was not visible when the section was written. State it, state the current ceiling, and note that changing the weight spread rescales every asymmetry figure — so cross-version comparisons require the weight table version to be recorded alongside results.

**Also record** the PM == 0 labelling case fixed mid-measurement: a market with no hedger side is one where the template is *inexpressible*, not false, and must not fall through to an MM-flat label. This belongs in the spec so it is not re-introduced.

---

## 7. Tests

| Test | Assertion |
|---|---|
| Asymmetry ceiling | `A_directional` and `A_agnostic` never exceed `max(w)/min(w)`, entire history |
| PM == 0 | Markets with no hedger side label as inexpressible, never as MM-flat |
| Conditional magnitude | Sign-conditional distributions computed on disjoint, exhaustive subsets |
| Stratum integrity | Venue classification is deterministic and reproducible from market codes alone |
| Doc consistency | §A.2's stated numbers match a live recomputation from the store |

The last one matters most. The prior session's `test_assessment_doc.py` pattern — asserting a document's numbers against the database — is the right guard, and §A.2 will now contain real values that can drift.

---

## 8. Report back

- §1: conditional magnitude tables, and the verdict on absence-vs-symmetric-swing
- §2: reclassification share under direction-agnostic asymmetry, with ceiling caveat
- §3: swap-share relationship, within-complex, plus explicit statement if it does not hold
- §4: stability and seasonality, with the coverage limit stated
- §5, §6: doc diffs
- Anything measured that contradicts this handoff, with the handoff corrected in place

**Do not proceed to the contract master (module spec §13 step 2).** A scoping decision is pending on whether to narrow it to the template-consistent markets, and §1 and §3 of this handoff bear on it directly.

---
---

# §9. Outcome, executed 2026-08-02

All five measurements ran, both doc corrections landed, and all five tests exist. Detail in
[`../design/amendments-2026-08-02.md`](../design/amendments-2026-08-02.md) §B33 through §B37;
every figure is reproduced by `docs/analysis/reproduce.py`
(`template_conditional_magnitude`, `template_direction_agnostic`, `template_swap_share`,
`template_stability`, `appendix_a2_worked_example`).

## What each section returned

**§1, conditional magnitude: neither reading, and the handoff's dichotomy is not exhaustive.**
`B33`. The fund is not absent: median `abs(P_MM)/OI` is 0.1387 when net long and 0.0718 when
net short, and Managed Money carries a median 51% of the whole fragility-weighted book when
long. Nor is it symmetric: the long positions are about twice the size. The number that
settles the handoff's question is one the handoff did not ask for. Managed Money holds
**64.9% of its contracts on the long side while being net long in only 50.0% of weeks**, so
the coin flip is in the sign and not in the size, and B31's "the half the thesis needs"
overstates the failure by roughly 2:1 on the quantity that would actually have to leave. The
directionless share is 16.0% / 33.3% / 49.4% at cuts of 0.02 / 0.05 / 0.10. Per complex, the
pooled figure hides two different markets: livestock swings 30.9% of OI long against 2.7%
short, while energy outright is genuinely thin, with 58.1% of its market-weeks under 5% of OI.
The 50.0% is also a mixture rather than a flip, 12 markets long in at most a tenth of weeks
against 11 in at least nine tenths.

**§2, direction-agnostic asymmetry, and it corrects a reading in B31.** `B34`. All 25.0% of
the inverted market-weeks reclassify, taking the direction-agnostic template from 44.7% to
**69.7%** of classic outrights. Carrying the ceiling caveat as instructed produced the more
important finding: `A_agnostic` has a median of **3.024** across all 21,756 market-weeks
against `A_directional`'s 0.993, and only **4.8%** of market-weeks have the two sides within
10% of each other. B31's "the typical market has `Q_sell` and `Q_buy` within a percent of each
other: no asymmetry whatsoever" is direction cancelling, not symmetry. Lopsided is the norm;
lopsided nine to one is not. Zero ceiling breaches on either ratio.

**§3, swap-dealer share: the hypothesis is retired.** `B35`. Spearman −0.114 across the 39
classic outrights, −0.100 across all 264 markets with at least 40 weeks, and +0.038
within-market week to week. The sign **reverses inside the strata** (metals +0.63, livestock
−0.69, energy −0.51), which is worse for the hypothesis than a flat pooled correlation. It
does not separate the two extreme sets: always-template mean swap share 0.157, never-template
0.159, with nesting ranges. Henry Hub has the heaviest swap book in the classic universe and
is never template; gold has the second heaviest and is always template. The CIT supplemental
is **not ingested** (the store holds `cot_disagg`, `cot_legacy`, `cot_tff` only) and was not
fetched, per the instruction.

**§4, stability and seasonality: the level holds, the classification does not, and the
seasonality cannot be measured.** `B36`. The weekly rate is flat: mean 0.447, sd 0.066, linear
fit +0.023/year at R² 0.026. The per-complex ordering holds, metals above livestock in 82 of
82 weeks and above grains in 64. The apparent ag seasonality (peak 0.522 in May, trough 0.263
in December) **does not survive the one check two years permit**: months 8 to 12 exist in a
single year, and across the seven months present in both the profiles correlate **−0.232**,
with the entire amplitude coming from 2026. It is one year's path wearing month labels. The
coverage limit is stated in place and the check that would settle it is a third year, no
earlier than 2027-01. On classification, the handoff's question had a sharper answer than
expected: **22 of 39 markets are extreme over the pooled window but only 17 in both halves**,
11 move more than 0.25, and cocoa runs 0.976 then 0.100.

**§5, the appendix.** `B37`. Replaced with **LIVE CATTLE, report week 2026-07-28**, carried
through §A.2, §A.5, §A.7 and §A.9. Gold was measured and rejected: its immovable side is a
swap dealer at `w = 0.4`, its Producer/Merchant net being a tenth of the swap book, so it does
not carry the appendix's physical-hedger argument. The constructed table is retained under
"The constructed extreme, retained" with its 90.5%-of-ceiling position stated, and the §A.5,
§A.7 and §A.9 figures built on it are kept as labelled continuations. A "How common is this
shape?" subsection carries the stratum table and the four qualifications.

**§6, module spec §6.3.** Both additions landed: the `max(w)/min(w)` bound with both report
types' ceilings, the rescaling consequence for cross-version comparison, the
compare-within-a-report rule, and `PM == 0` as inexpressible with the fall-through failure
recorded.

**§7, tests.** All five, plus one the handoff did not ask for. `tests/test_template_strata.py`
covers the ceiling over twenty years and over the vintage panel, the
spread-versus-level property of the bound, and stratum integrity;
`tests/test_shape_labels.py` covers `PM == 0` and the disjoint-and-exhaustive property;
`tests/test_appendix.py` and the new `tests/test_appendix_live.py` cover doc consistency
offline and against the real store.

## What contradicted the handoff, and what it cost

**§1's dichotomy is not exhaustive**, and answering only the question as posed would have
returned "symmetric large positioning" and been misleading. The distinguishing measurement is
count share against contract share, which neither branch of the handoff's framing asks for.

**§2's "the median of 0.993 is the number that matters most" was right for the wrong
reason.** It matters because it is misleading, not because it is the centre of the
distribution. The instruction to report `A_agnostic` "the same way" is what surfaced it.

**§5's premise that the median real market has "no asymmetry at all"** is the same error and
is corrected in B34. The instruction it justified was still the right instruction.

**A code change the handoff did not scope.** `shape_labels` moved into
`crowdmon.futures.fragility` because the six-mask classification existed twice, in
`reproduce.py` and `reproduce_tff.py` with different label strings, which is precisely the
duplication `§B29` caught between the two flow decompositions. Additive: a new public symbol,
both reproducers now delegate, and the display names are unchanged.

## Left where it was found

**The contract master (module spec §13 step 2) was not started**, per the closing
instruction. §1 and §3 both bear on the scoping decision and neither settles it: §3 removes
swap-dealer prominence as a candidate criterion, and §1 shows that the template-consistent set
is not the same as the set where the fund is large.

**The weight table was not touched**, per §2's instruction, though §6's ceiling property is
now written down as the constraint any future change to it runs into.
