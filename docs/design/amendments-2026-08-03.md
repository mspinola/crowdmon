# Spec amendments, 2026-08-03

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

Sections here carry a **`C` prefix**, per the per-day convention set in `f194c4e` and stated
in [README.md](README.md): "Each new file gets its own date and its own letter prefix (`B1`,
`C1`, ...)". [`amendments-2026-08-02.md`](amendments-2026-08-02.md) is closed at B37.
Cross-file references carry the date: `2026-08-02 §B31`.

> **CORRECTED 2026-08-03, and this header was the largest error in the file.** It said
> "these are the sections `2026-08-03-index-share.md` §2 cites as §B33-B36", that the
> citation "was written before they existed and cannot be honoured literally", and that
> "whoever wrote the handoff ran this measurement and did not record it ... an accurate one
> with no home".
>
> **All three are wrong. §B33 through §B37 existed, and had existed since 2026-08-02.** They
> were recorded, in
> [`amendments-2026-08-02.md`](amendments-2026-08-02.md) §B33-B37, on a branch
> (`claude/template-followups-doc-corrections-45de1d`, `11b7c81`) that was **never pushed**.
> The failure was not a missing record. It was a record that no reachable search would find,
> which is worse, because a missing record announces itself and this one produced a confident
> re-derivation instead. They are now on main and every citation below resolves.
>
> C1-C4 stand as a **blind re-derivation**, kept rather than reverted, because two
> independent measurements of one thing agreeing is evidence and only one of the four is
> actually wrong. What each becomes:
>
> | this file | the original | disposition |
> |---|---|---|
> | §C1, classification stability | `2026-08-02 §B36` | **Agree.** 22 pooled, 17 stable, same 17 codes. The cocoa pair differs by one week's assignment and §C1 resolves it below |
> | §C2, template rate invariant to `w_SD` | no counterpart | **Stands, and is new.** §B33 and §B35 ask different questions of the swap book. See §C2 |
> | §C3, `Q_sell`/`Q_buy` swept | no counterpart | **Stands, and is new.** It is the sweep §B34 measured at one weight and never swept |
> | §C4, `A_agnostic` undefined | `2026-08-02 §B34` | **SUPERSEDED.** §B34 defines it and measures a median of 3.0237. §C4 is corrected in place below |
>
> **The cited figures were never invented**, which the original header got right for the
> right reason: §C1 reproduces "22 of 39" and "17 in both halves" exactly.

Every figure below is reproduced by
[`../analysis/reproduce_template_stability.py`](../analysis/reproduce_template_stability.py)
against `COTDATA_STORE=~/code/cotdata_store`, over the vintage store's 82 weeks. Blocks are
named after the section: §C1 is `c1_classification_stability`, and so on through
`c8_does_the_composite_care`. **§C5 is the exception**: it belongs to crowdmon#42 and has its
own reproducer and live pin. The gap is named rather than silent.

---

## C1. Template classification is stable for 17 of 39 markets, and cocoa is the market that flips

**Establishes:** the caveat `2026-08-03-index-share.md` §3 states without a source.

The vintage window is 82 weeks. Split at 2025-10-21 into 41 and 41, over the 39 classic
outrights with at least 40 weeks (B31's universe and floor, so the pooled count is comparable
to it):

| count | markets |
|---|---|
| extreme over the **pooled** window | **22 of 39** |
| extreme in **both halves**, either side | 18 of 39 |
| extreme in **both halves, same side** | **17 of 39** |

"Extreme" is B31's banding: a template rate at or below 0.10, or at or above 0.90. The pooled
22 is B31's own classic-outright row read as a count (33.3% never plus 23.1% always, of 39),
so §C1 is not a new pooled measurement, it is the half-split that was missing.

**The gap between 22 and 17 is five markets whose classification is an artifact of the window
length**, not of the market. That is the instability §3 warns about, and it is now measured
rather than asserted.

**Exactly one market flips from one extreme to the other**, and it is the one the handoff
names:

| market | pooled | h1 | h2 |
|---|---|---|---|
| COCOA (073732) | 0.549 | **1.000** | **0.098** |

Cocoa is template in all 41 weeks of the first half and 4 of 41 in the second. Pooled it
reads 0.549, a number that describes no week cocoa has ever had. This is the same failure
`2026-08-02 §B31` records under "it is a mixture of always and never, not a 45% chance each
week", now with a market that changes which extreme it belongs to inside a single 82-week
window.

**Small discrepancy against the handoff's citation, now RESOLVED.** §3 cites cocoa as
"0.976 then 0.100"; measured here it is **1.000 then 0.098**. When this was written the
citation had no source. It does now: `2026-08-02 §B36` is where 0.976 / 0.100 comes from,
and the two are the same measurement under two boundary rules.

| | split date | rule | halves | cocoa h1 | cocoa h2 |
|---|---|---|---|---|---|
| §C1 (`c1_classification_stability`) | 2025-10-21 | `dates[41]`, strictly **before** | 41 / 41 | **1.0000** | **0.0976** |
| `2026-08-02 §B36` (`reproduce.py::template_stability`) | 2025-10-21 | median over **market-weeks**, at or before | 42 / 40 | **0.9762** | **0.1000** |

Carried through: cocoa is template in 41 weeks and not in the week of 2025-10-21. Put that
week in h1 and the first half reads 41/42 = 0.9762 while the second reads 4/40 = 0.1000. Put
it in h2 and the first half reads 41/41 = 1.0000 while the second reads 4/41 = 0.0976. One
week, two denominators, and both arithmetics are right.

**§C1's rule is the correct one**, on the narrow ground that it is the better-specified
split: 41 weeks against 41, where §B36's median is taken over market-weeks and is therefore
weighted by how many markets happened to report each week, which is a property of the panel
rather than of the window. The difference is cosmetic in every other respect and that is
measured rather than assumed: **22 pooled, 18 either-side, 17 same-side and the identical 17
market codes under both rules.** Quote 1.000 / 0.098 going forward, and expect 0.976 / 0.100
in anything written before 2026-08-03.

The largest movers, whether or not extreme, since restricting to the extremes hides that the
instability is broad:

| market | pooled | h1 | h2 | swing |
|---|---|---|---|---|
| COCOA | 0.549 | 1.000 | 0.098 | 0.902 |
| SOYBEAN MEAL | 0.354 | 0.000 | 0.707 | 0.707 |
| WHEAT-HRW | 0.256 | 0.000 | 0.512 | 0.512 |
| ALUMINUM | 0.548 | 0.370 | 0.867 | 0.496 |
| FRZN CONC ORANGE JUICE | 0.683 | 0.927 | 0.439 | 0.488 |
| WHEAT-HRSpring | 0.244 | 0.024 | 0.463 | 0.439 |
| BRENT LAST DAY | 0.720 | 0.512 | 0.927 | 0.415 |
| COTTON NO. 2 | 0.195 | 0.000 | 0.390 | 0.390 |

Three of the eight (soybean meal, wheat-HRW, cotton) go from **never** template in the first
half to a substantial rate in the second. A classification computed on either half alone would
disagree with the other half about what kind of market these are.

**What this changes.** Any statement of the form "market X is a template market" needs a
window attached, and comparisons across studies using different windows are not comparable.
`2026-08-02 §B31`'s complex-level findings (metals 66.5%, and the always-template list) are
pooled figures and inherit this: they are correct about the 82 weeks and are not a property of
the market.

## C2. The template rate cannot move with `w_SD`, and the sweep §2 asks for is a formality

**Contradicts:** `2026-08-03-index-share.md` §2, which asks for the template rate by stratum
to be recomputed "across `w_SD ∈ {0.2, 0.4, 0.7}`" and offers to read insensitivity as
evidence that "the weight matters less than the effort implies".

The template label is `_shape_labels(producer_merchant, managed_money)`: two category nets,
their signs, and nothing else. The fragility weights do not appear in it, cannot appear in it,
and `swap` is not one of the two categories it reads. So the rate is invariant to `w_SD` by
construction, not as an empirical finding.

Swept anyway, over the classic outrights, because a structural claim is cheap to check:

| `w_SD` | template rate |
|---|---|
| 0.2 | 0.447106 |
| 0.4 | 0.447106 |
| 0.7 | 0.447106 |

Identical to seven figures, as it must be. The value also reproduces `2026-08-02 §B31`'s
classic-outright row (44.7%), which is the cross-check that the sweep is measuring the
intended quantity rather than a constant for the wrong reason.

**This matters for how §2's result should be read.** §2 proposes to conclude, from an
insensitive template rate, that the weight "matters less than the effort implies". That
inference is not available: the insensitivity is a fact about which two series the shape rule
reads, and it would hold identically if `w_SD` were the single most load-bearing number in the
package. **A quantity that cannot respond to a parameter is not evidence about that
parameter.** §C3 measures a quantity that can.

**Checked against `2026-08-02 §B33` and `§B35` rather than assumed independent**, since all
three are about the swap book and the template rate. They do not overlap, and the three
together are stronger than any one:

| section | question | answer |
|---|---|---|
| §C2 | does the swap **weight** enter the template label? | no, structurally. It reads two other categories' nets |
| `2026-08-02 §B35` | does the swap **position** predict template status? | no, empirically. Spearman -0.114, sign reversing inside complexes |
| `2026-08-02 §B33` | is the fragile side of the template absent or symmetric? | neither. Half the weeks by sign, 64.9% of contracts by size |

§C2 is a fact about the code, §B35 a fact about the data, and §B33 about a different
quantity again. The one to carry: the swap book is neither an **input** to the template
label nor a **predictor** of it, so nothing about `w_SD` can be learned from that rate at
all. §C5 keeps the swept row anyway, as a completeness check and labelled as one.

## C3. What does move: `Q_sell`/`Q_buy` is insensitive pooled and highly sensitive on the Supplemental 13

`Q_sell` and `Q_buy` are weight-dependent by construction, so this is where §2's question has
an answer. `A = Q_sell / Q_buy`, medians over market-weeks:

**All 21,756 vintage market-weeks:**

| `w_SD` | median `Q_sell` | median `Q_buy` | median `A` | p90 `A` | max `A` | ceiling |
|---|---|---|---|---|---|---|
| 0.2 | 3,120.65 | 3,084.75 | 1.0213 | 5.3023 | 9.9683 | 10.0 |
| 0.4 | 3,734.25 | 3,811.35 | 0.9933 | 5.1620 | 9.9613 | 10.0 |
| 0.7 | 4,340.60 | 4,670.30 | 1.0153 | 6.2049 | 9.9508 | 10.0 |

Median `A` moves 1.0213 to 1.0153, **0.6%** across the sweep, and not monotonically. Pooled,
`w_SD` is close to irrelevant to the asymmetry.

**The 13 Supplemental markets, 1,066 market-weeks:**

| `w_SD` | median `Q_sell` | median `Q_buy` | median `A` | p90 `A` | max `A` | ceiling |
|---|---|---|---|---|---|---|
| 0.2 | 39,747.3 | 31,321.7 | 2.1845 | 6.1309 | 9.1451 | 10.0 |
| 0.4 | 56,886.6 | 31,431.4 | 2.5750 | 5.9993 | 9.2477 | 10.0 |
| 0.7 | 81,635.3 | 31,431.4 | 3.1028 | 6.8620 | 9.4015 | 10.0 |

Median `A` moves 2.1845 to 3.1028, **42.0%**, monotonically. `Q_sell` doubles while median
`Q_buy` is unchanged between 0.4 and 0.7, which locates the mechanism: on the median
Supplemental market the swap book sits on the **sell** side of the fragility split, so raising
its weight lifts the numerator alone.

**The two headline figures §2 asks about give opposite answers, and the population is the
reason.** Pooled over a universe that is three-quarters power and gas basis
(`2026-08-01 §A5`), `w_SD` is a rounding error. On the 13 agricultural markets §2 actually
restricts to, it is load-bearing: a 42% swing in the median asymmetry across a plausible
range. **`w_SD = 0.4` is not a safe default that happens not to matter. It is a number the
answer depends on, in exactly the markets the handoff cares about.**

Note the ceiling column: `max(w)/min(w)` is 10.0 at every swept value because `managed_money`
(1.0) and `producer_merchant` (0.1) bracket the table and `w_SD` never leaves that interval.
So none of the movement above is a ceiling artifact, which `2026-08-02 §B31` warns is
otherwise easy to mistake for a measurement.

## C4. CORRECTED. `A_agnostic` is DIRECTION-agnostic, and it was defined all along

> **This section was wrong, and it is kept rather than deleted because how it was wrong is
> the useful part.** It read "agnostic" as **weight**-agnostic. `A_agnostic` is
> **direction**-agnostic, defined and measured in
> [`amendments-2026-08-02.md`](amendments-2026-08-02.md) §B34, which was one unpushed commit
> away the whole time. Reproducer:
> [`../analysis/reproduce.py`](../analysis/reproduce.py)`::template_direction_agnostic`.
>
> ```
> A_directional = Q_sell / Q_buy
> A_agnostic    = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)
> ```
>
> Over the same 21,756 market-weeks at the shipped weights:
>
> | stratum | market-weeks | `A_dir` median | `A_agn` median | % of the 10.0 ceiling | breaches |
> |---|---|---|---|---|---|
> | classic outright | 3,214 | 1.4894 | **2.4974** | 25.0% | 0 |
> | everything else | 18,542 | 0.9041 | **3.1000** | 31.0% | 0 |
> | all | 21,756 | **0.9933** | **3.0237** | 30.2% | 0 |
>
> Not undefined, and nowhere near 1.0: **the typical market-week has one side three times
> the other**, and what is a coin flip is which side. `Q_sell` is the larger in 49.8% of
> market-weeks and only 4.8% are balanced within 10%. Everything §B34 draws from that
> follows, including that the 25.0% inverted market-weeks reclassify and take the
> direction-agnostic template from 44.7% to **69.7%** of classic outrights.
>
> **The lesson is not about weights.** An unresolvable citation was answered by guessing at
> the definition, and the guess was wrong in a way that no amount of care about the
> arithmetic below would have caught: every number in it is correct. That is why §3 of the
> b-series-recovery handoff changes the citation convention to path plus reproducer.
> Pinned from both sides in `tests/test_supplemental_live.py`
> (`test_c4_a_weight_agnostic_asymmetry_is_identically_one` and
> `test_c4_corrected_a_agnostic_is_direction_agnostic_and_not_degenerate`), so the wrong
> reading cannot creep back as a plausible guess.

### What the original section measured, retained as the thing the name does not mean

**Contradicts:** `2026-08-03-index-share.md` §2, which lists "`A_agnostic` median" among the
figures to recompute.

The string appeared nowhere in `src/`, `tests/` or `docs/design/` except in the handoff
citing it, on 2026-08-03, because §B34 was on a branch that had never been pushed.

The reading taken, an asymmetry computed with weights that do not discriminate between
categories, is identically 1. Since `sum_c P_c = 0`, the gross net-long total `G` equals the
gross net-short total (`2026-08-02 §B31`), so with a single shared weight `w`:

    Q_sell = w·G,   Q_buy = w·G,   A = Q_sell/Q_buy = 1

for every market, every week, and every `w`. Measured over all 21,756 market-weeks with every
weight set to 1.0:

| statistic | value |
|---|---|
| min | 1.000000 |
| median | 1.000000 |
| max | 1.000000 |
| share within 1e-9 of exactly 1.0 | **100.0000%** |

So a **weight**-agnostic asymmetry measures nothing at all. That is a true statement about a
quantity nobody asked for, and it is worth keeping on its own terms: it is the same result as
`2026-08-01 §A21` ("Phi has no cross-market signal independent of the weight table") in its
sharpest form, since with the weights flattened the asymmetry does not merely lose signal, it
becomes a constant. It is now pinned by
`test_c4_a_weight_agnostic_asymmetry_is_identically_one` for that reason and not as evidence
about `A_agnostic`.

**Consequence for the handoff, restated.** The original text read: "§2 lists three headline
figures. One cannot respond to the parameter it is swept against (§C2), one is undefined
(§C4), and one answers clearly and interestingly (§C3)." Two of three survive. The corrected
count is that **all three are available**: the template rate cannot respond and says so
(§C2), `A_agnostic` is defined by §B34 and is swept in §C6, and `Q_sell`/`Q_buy` answers
(§C3). §2 was executable in full, and was executed in full on 2026-08-02.

---

## C6. The reported band, and the measured lower bound is not on the same scale

> §C5 is not in this file's lineage: it belongs to crowdmon#42 (branch
> `claude/repo-hygiene-b33-b36-7e0c36`, `15a013a`) and records the stale "there is no volume"
> claim. The gap is named rather than silent, so that a reader who finds C4 next to C6 knows
> which PR to look in and does not conclude a section was lost. That is the same failure this
> whole file is about.

**Executes** §4 of [`../handoffs/2026-08-03-b-series-recovery.md`](../handoffs/2026-08-03-b-series-recovery.md),
under a design decision that is **settled and not relitigated here: the weights stay
static.** The reasoning, recorded so it is not reopened: swap sits at 0.305 of Managed Money
on routine turnover and 0.067 under stress
([`../analysis/2026-08-03-index-share.md`](../analysis/2026-08-03-index-share.md) §5), which
is incoherence across **regimes**, not across markets. A regime-switching table would need a
point-in-time stress classifier whose misclassifications would propagate into every
downstream figure including the composite. Instead the composite is reported under multiple
weight tables and **the spread is an uncertainty band rather than noise**.

**This is a decision about how weights are TREATED, not about what `swap` should be.** That
second question is filed separately and is explicitly the human's, in
[`../handoffs/2026-08-03-swap-dealer-weight-decision.md`](../handoffs/2026-08-03-swap-dealer-weight-decision.md)
("a session may prepare the change; it may not choose the number"). The static-weights
decision closes that handoff's option **(c)**, regime-conditional weights, and leaves (a),
(b) and (d) open. **`core/config.py` is unchanged by this work**, and §C6-C8 are the evidence
that handoff's §2 needs, not a substitute for it. Do not re-measure its §1.

Reproducer: [`../analysis/reproduce_template_stability.py`](../analysis/reproduce_template_stability.py)`::c6_the_reported_band`.

### The band, and why 0.067 is in it

`w_SD ∈ {0.067, 0.2, 0.4, 0.7}`. Three of those are round numbers chosen for spacing and
**should be labelled as such**; 0.067 is measured, the stress-regime figure, so it is the
empirically motivated lower bound rather than a fourth round number. The shipped value is
0.4.

**Template rate: 0.447106 at every value in the band**, as §C2 establishes it must be. The
row is kept for completeness and carries no information about the weight. §C2's cross-check
against `2026-08-02 §B33` and `§B35` is why: the swap book is neither an input to the shape
label nor a predictor of it.

All 21,756 vintage market-weeks:

| `w_SD` | kind | median `Q_sell` | median `Q_buy` | median `A_dir` | median `A_agn` | ceiling | `A_agn` as % of ceiling |
|---|---|---|---|---|---|---|---|
| 0.067 | **measured** | 2,651.1 | 2,558.7 | 1.0904 | **3.6316** | **14.925** | 24.3% |
| 0.2 | round | 3,120.6 | 3,084.8 | 1.0213 | **2.9211** | 10.000 | 29.2% |
| 0.4 | round, **shipped** | 3,734.2 | 3,811.4 | 0.9933 | **3.0237** | 10.000 | 30.2% |
| 0.7 | round | 4,340.6 | 4,670.3 | 1.0153 | **3.3642** | 10.000 | 33.6% |

The 13 Supplemental markets, 1,066 market-weeks:

| `w_SD` | median `Q_sell` | median `Q_buy` | median `A_dir` | median `A_agn` |
|---|---|---|---|---|
| 0.067 | 31,439.5 | 31,290.8 | 2.0137 | 3.6976 |
| 0.2 | 39,747.3 | 31,321.7 | 2.1845 | 3.3349 |
| 0.4 | 56,886.6 | 31,431.4 | 2.5750 | 3.0271 |
| 0.7 | 81,635.3 | 31,431.4 | 3.1028 | 3.1395 |

Zero ceiling breaches at any value, on either ratio, in any stratum.

### Two things the fourth value exposes that three did not

**The ceiling moves, and the band is therefore not on one scale.** At 0.2, 0.4 and 0.7 the
swap weight stays inside the interval `[0.1, 1.0]` that `producer_merchant` and
`managed_money` bracket, so `max(w)/min(w)` is 10.0 at all three and §C3 could compare raw
ratios across them. **At 0.067 swap becomes the smallest weight in the table**, below
`producer_merchant` at 0.1, so the ceiling becomes `1.0 / 0.067 = 14.925`: every raw ratio
gains 49% of headroom before anything about the data changes. Carried through on the pooled
median: 3.6316 at 0.067 is **larger** than 3.0237 at 0.4 in raw terms and **smaller** as a
fraction of its own ceiling (24.3% against 30.2%). The two comparisons disagree about the
ranking, which is `2026-07-28 §2.3`'s compare-within-a-report rule arriving from a new
direction. **Scale by the ceiling before comparing across the band.** This is asserted rather
than remembered, in `test_c6_the_measured_lower_bound_moves_the_ceiling_and_the_others_do_not`.

**`A_agnostic` is U-shaped in `w_SD`, with its minimum inside the band.** Pooled it runs
3.6316, 2.9211, 3.0237, 3.3642: down then up, minimised near the shipped weight. The
mechanism is that swap sits on both sides across the universe. Push `w_SD` down and the swap
book stops opposing anything, leaving the residual Managed-Money-against-Producer/Merchant
book, which is more lopsided; push it up and swap dominates whichever side it happens to be
on. So **the band's endpoints do not bracket the answer**, and quoting a min and a max from
it would understate the interior. `A_directional` behaves differently again: 1.0904, 1.0213,
0.9933, 1.0153, with no order at all, because it is direction cancelling (§B34).

On the classic outrights `A_agnostic` is monotonically decreasing instead (4.1963, 3.2886,
2.4974, 2.4135), so even the shape of the response is a population fact rather than a
property of the measure. §C3's finding generalises: **the answer depends on which universe
is being pooled, every time.**

---

## C7. `w_SD = 0.4` overstates fragile capital, worst where it is least deserved

**Executes** the second half of §4: report the DIRECTION of the bias, not only its magnitude,
and test the prediction that gold is worse affected than cocoa.

Reproducer: `../analysis/reproduce_template_stability.py::c7_direction_of_the_bias`.

`Phi` is the fragility-weighted share of a randomly chosen position-side, so a higher `Phi`
literally means "more of this book can be forced out". Comparing the shipped 0.4 against the
measured stress figure 0.067, over 21,756 market-weeks:

| | share of market-weeks |
|---|---|
| `Phi(0.4) > Phi(0.067)` | **99.31%** |
| exactly equal | 0.69% (a swap book of exactly zero gross, in 21 markets) |
| `Phi(0.4) < Phi(0.067)` | **0.00%** |

The sign is not a finding: raising a weight raises a weighted sum. **The size is, and so is
how unevenly it lands.** Mean **+26.67%**, median **+19.60%**, p90 **+56.14%**, max
**+237.12%**.

### Which markets carry it

Classic outrights with at least 40 weeks, mean `Phi` inflation from 0.067 to 0.4:

| market | `Phi` at 0.067 | `Phi` at 0.4 | inflation |
|---|---|---|---|
| HENRY HUB | 0.2410 | 0.3633 | **+50.8%** |
| CME MILK IV | 0.1692 | 0.2364 | +42.0% |
| BUTTER | 0.1511 | 0.2094 | +38.8% |
| WTI FINANCIAL | 0.2658 | 0.3590 | +35.5% |
| WTI-PHYSICAL | 0.1557 | 0.2070 | +32.9% |
| CHEESE | 0.1844 | 0.2419 | +31.4% |
| SILVER | 0.3283 | 0.4241 | +29.8% |
| **GOLD** | 0.3618 | 0.4619 | **+27.8%** |
| ... | | | |
| **COCOA** | 0.2811 | 0.3147 | **+12.1%** |
| ... | | | |
| MICRO GOLD | 0.5066 | 0.5128 | +1.2% |
| ROUGH RICE | 0.4589 | 0.4628 | **+0.9%** |

**The prediction holds. Gold is affected 2.30x as much as cocoa**, and the mechanism is the
one §4 named: on gold the swap dealer **is** the immovable physical-hedging side, with
Producer/Merchant at a tenth of the swap book, so weighting it at 0.4 books robust capital as
fragile. On cocoa the swap dealer holds the largest **net long**
(`2026-08-02 §B35`: in 47 of 82 weeks), which is much closer to what `w = 0.4` is meant to
describe. So **the overstatement is worst exactly where it is least deserved**, which is the
sharpest available statement of the bias and is not a general property of a high weight.

Note the top of the list is the heavy-swap-intermediation set, and `2026-08-02 §B35` measured
HENRY HUB as carrying the heaviest swap book in the classic universe at a share of 0.367.
That is a consistency check rather than a second finding: the inflation is mechanically a
function of swap gross share, and the ordering says the arithmetic is doing what it should.

**Direction of bias, stated for the operator.** Swap dealers become **stickier** under
stress, so the shipped weight overstates forced capital **precisely during the weeks the
monitor exists to warn about**. A `D` reading taken in a stress week is therefore biased
high, by a market-specific amount running from 1% to 51% on the outrights, and by the most on
the markets whose swap book is largest.

---

## C8. But the composite consumes a percentile, so most of that never arrives

**Qualifies §C7**, and the qualification is large enough that §C7 read alone would overstate
the operational consequence.

Reproducer: `../analysis/reproduce_template_stability.py::c8_does_the_composite_care`.

`A.9`'s `D = C × I × Φ` uses each term as a **percentile of its own history**, never as a
level. A weight change that lifts a market's whole `Phi` series by 28% lifts nothing at all
in the percentile. So the question is not how much `Phi` moves, it is whether the two weight
tables **order a market's own weeks differently**. Over 20,567 market-weeks in the 264
markets with at least 40 weeks:

| `|pct(Phi) at 0.4 − pct(Phi) at 0.067|` | |
|---|---|
| median | **0.0588** |
| mean | 0.0979 |
| p90 | 0.2439 |
| max | **0.8780** |
| moves more than 0.10 of a percentile | **32.55%** of market-weeks |
| moves more than 0.25 of a percentile | **9.79%** of market-weeks |

Carried through on the median market-week: a `Phi` that inflates 19.6% in level moves 5.9
percentiles in rank, so roughly nothing reaches `D`. On a tenth of market-weeks it moves more
than 25 percentiles, which does.

### Where the two tables genuinely disagree

Per-market Spearman between the two `Phi` series, over each market's own weeks: **median
0.9316**, but **98 of 264 markets fall below 0.90** and a handful invert outright.

| market | Spearman |
|---|---|
| TRANSCO ZONE 6 BASIS (ICE Energy Div) | **−0.4160** |
| PJM.N ILLINOIS HUB month-on (Nodal) | −0.0734 |
| PJM.N ILLINOIS HUB month-off (Nodal) | −0.0669 |
| MISO.INDIANA.HUB month-off (Nodal) | −0.0603 |
| CALIF CARBON CURRENT AUCTION | +0.1255 |

On those markets the two weight tables disagree about **which of that market's own weeks
were the fragile ones**, which is a disagreement no level comparison would surface. All five
are power, gas basis or carbon, which is the 76% of the Disaggregated universe
`2026-08-01 §A5` describes.

Cross-market, the ranking of mean `Phi` largely survives:

| population | Spearman, 0.4 against 0.067 |
|---|---|
| all 264 markets | 0.8521 |
| 39 classic outrights | **0.9540** |
| top-10 classic outrights by mean `Phi` | 8 of 10 in common |
| top-20 classic outrights | 18 of 20 in common |

**So the band is narrow where the package is usually read and wide where it is not.** On the
outrights the `w_SD` choice moves levels and barely moves rankings; on the ERCOT and PJM
book it can reorder a market's own history. Anyone publishing a `D` percentile on a
power or gas basis market should publish the band beside it; on a classic outright the band
is a footnote.

**What this does NOT establish.** None of §C6-C8 is evidence that the composite is right.
The sweep describes how a configured number moves an output, which is a statement about the
code and the weight table. Whether `D` measures anything is a different question, and this
package deliberately cannot answer it (`tests/test_boundaries.py` refuses an import of
`crucible` for exactly that reason).

---

## C9. The stale PyPI inference did not propagate here, and two stale FACTS survive in siblings

**Executes** §5 of [`../handoffs/2026-08-03-b-series-recovery.md`](../handoffs/2026-08-03-b-series-recovery.md):
"grep the siblings for the stale inference and fix any survivor."

The inference in question, from an older `trading_workspace/CLAUDE.md`: `cotdata` v0.2.0 was
tagged while PyPI carried 0.1.0, therefore **"a symbol added since 0.1.0 has no external
consumers by construction, so removing it is cheap"**. That stopped being true on 2026-08-02
when cotdata 0.3.0 shipped through tag-triggered Trusted Publishing (cotdata#94). PyPI now
carries **0.1.0 and 0.3.0**, so the whole producer CLI and the entire vintage subsystem are
published and may have external consumers. Deleting from them is a breaking change.

**In `crowdmon` the inference never appeared and nothing needs fixing.** Searched every `.md`,
`.py` and `.toml`. The only place the reasoning could plausibly have landed is
[`2026-08-02 §B29`](amendments-2026-08-02.md#b29-the-two-flow-decompositions-are-one-function-and-the-reason-given-for-the-gap-rule-is-wrong),
which declined to remove `cotdata.vintage_flow.decompose` on the grounds that it is "a
public-symbol removal in a PyPI package and a change to a shared working tree". That is the
**cautious** direction and it is unaffected by which versions are published, so it stands as
written. `2026-08-01-flow-decomposition.md` §10 says the same thing and likewise stands.

**Two stale facts survive in sibling checkouts. Recorded here rather than edited**, per the
working agreement on docs that live in another repo, and both are facts rather than the bad
inference, so neither is load-bearing:

| where | says | now |
|---|---|---|
| `cotdata/CHANGELOG.md` (the 0.3.0 entry, on `decompose`) | "is in no **published** release: PyPI carries 0.1.0" | PyPI carries 0.1.0 **and 0.3.0**. The narrow claim still holds: `decompose` was removed *in* 0.3.0, so it was in no published release at the time. A changelog is a dated record, so this is arguably correct as issued |
| `npf/tests/test_sibling_floors.py::test_cotdata_floor_predates_its_oldest_tag` | "npf pins `cotdata>=0.1.0`. PyPI carries 0.1.0, but the repo's oldest tag is v0.2.0" | The gap it records is real and the test still passes: `v0.1.0` is genuinely untagged. Only the parenthetical count of what PyPI carries is stale |

Neither propagates the "removing it is cheap" conclusion, which is the thing §5 asked about.
The workspace `CLAUDE.md` is already corrected and is the authority.
