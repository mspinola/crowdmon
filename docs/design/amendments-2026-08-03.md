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
`c8_does_the_composite_care`. **§C5 is the exception**: it arrived from crowdmon#42 with its
own inline reproducer and its own live pin in `tests/test_volume_live.py`.

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

## C5. "There is no volume" survived in three places after volume shipped, one of them in code

**Contradicts:** `README.md`'s third refusal ("there is no per-contract volume source in this
workspace, so `days_to_liquidate` is `None`") and `core/config.py`'s `KAPPA` comment ("so
today it is always `None`"). Both fixed in the same commit as this section.

`futures/volume.py` shipped a whole-market ADV, `pressure.py`'s own header was updated to say
so ("**`V` now exists**, and this module's header used to say it did not"), and two of its
three neighbours were not. Measured on the latest Disaggregated panel:

| quantity | value |
|---|---|
| markets on the panel | 279 |
| markets with a non-null `dtl_sell` | **25** |
| markets with a null `dtl_sell` | 254, **every one of them for want of a contract spec** |

So the claim was false rather than imprecise. Not one of the 254 nulls is a market with no
volume; they are Nodal power zones and minor grains with no entry in the contract master,
which is the same 87%-of-rows figure `ContractMaster` reports from the other direction.

Reproducer, against `COTDATA_STORE=~/code/cotdata_store`:

```python
p = ContractMaster.load().annotate(latest())
adv = add_volume(p)[["market_code", "adv"]].dropna().drop_duplicates("market_code") \
        .set_index("market_code")["adv"]
f = fragility_frame(p)
r = rank_markets(f, volume=f["market_code"].map(adv))      # positional, per the docstring
r["dtl_sell"].notna().sum()                                 # 25
```

**The alignment trap, found while writing that reproducer and worth carrying.**
`rank_markets` documents `volume` as "aligned to `fragility`'s index", which is **positional**.
Passing a `market_code`-indexed Series does not raise: it reindexes to `NaN` and every `dtl_*`
column comes back null, which is indistinguishable from "no volume was available". A first
attempt at the count above returned **0 of 279** for exactly this reason and looked like a
confirmation of the stale claim. Map to the frame's own `market_code` column first.

**What this changes about the working agreement, and it is not "check more carefully".** Volume
is already one of the four blocked-on rows `README.md` records as having proved stale on
re-test. This is the failure *after* that one: the blocker lifted, the finding was written
down, and the correction landed only where the work happened. `pressure.py` was right on
2026-08-02 while `README.md` and `core/config.py` were still wrong, which is worse than all
three being wrong together, because it makes the false version look corroborated by the two
files a reader reaches first while the file that is actually authoritative is the one nobody
opens. **Re-testing a blocker is half the job; the other half is a grep for every place that
asserted it.**

---

## C6. The reported band, and the measured lower bound is not on the same scale

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

---

## C10. Three of the swept values reorder the weight table, which is a second reason the band is not one scale

**Extends `§C6`, and was measured independently of it**, on the branch that became
crowdmon#44 while §C6-C8 were in flight on `claude/b-series-reconcile`. Kept rather than
folded in, because the two findings are about different properties of the same band and
neither implies the other.

`§C6` establishes that the band is not on one **scale**: at `w_SD = 0.067` swap becomes the
smallest weight in the table, so `max(w)/min(w)` goes from 10.0 to 14.925 and every raw ratio
gains 49% of headroom before anything about the data changes. Scale by the ceiling before
comparing.

**This section is about ORDER, and it bites at the other end of the band.** The ceiling is
`max/min`, so it is blind to anything that happens strictly between `producer_merchant` at
0.1 and `managed_money` at 1.0. Both 0.55 and 0.7 sit inside that interval, leave the ceiling
at exactly 10.0, and still reorder the table:

| `w_SD` | ceiling | order | what moved |
|---|---|---|---|
| 0.067 | **14.925** | violated | now below `producer_merchant` (this is §C6's case) |
| 0.100 | 10.000 | **collapsed** | **ties** `producer_merchant` |
| 0.200 | 10.000 | intact | |
| 0.305 | 10.000 | intact | the routine-turnover reading |
| 0.400 | 10.000 | intact | shipped |
| 0.550 | 10.000 | **violated** | now above `other_reportable` (0.5) |
| 0.700 | 10.000 | **violated** | now above `other_reportable` and `nonreportable` (0.6) |

`2026-08-01 §A22` is why this matters rather than being bookkeeping: §6.3's judgement is an
**ordering** before it is a set of values, order-preserving jitter keeps at least 7 of the
`Q_sell/OI` top 10, and **inverting the ordering destroys the ranking outright** (0 of 10
survive, rank correlation -0.045). A value that reorders the table is a different claim about
holder behaviour, not a rival value for the same claim. At 0.7 it asserts that a swap dealer
is more forceable than a retail account, which nobody in this project has argued.

**Consequence for `§C3`'s headline.** §C3 swept 0.2 to 0.7 and quoted a **42.0%** swing in
median `A_directional` on the Supplemental 13. Restricted to the order-preserving values,
`w_SD` spans `[0.2, 0.4]` and the same statistic moves:

| population | order-preserving `[0.2, 0.4]` | as §C3 quoted it |
|---|---|---|
| all 346 markets | 0.9869 to 1.0213, **3.5%** | 0.6% |
| the 13 Supplemental markets | 2.1845 to 2.5750, **17.9%** | 42.0% |

Not wrong arithmetic, the wrong band. **§C3's direction survives and its force does not.** The
shipped 0.4 sits 7.1% from the routine-turnover reading of 0.305.

**§C6's U-shape warning applies here too and is the stronger caveat.** §C6 measured
`A_agnostic` as U-shaped in `w_SD` with its minimum near the shipped weight, so the band's
endpoints do not bracket the interior and quoting a min and a max understates it. The 17.9%
above is an endpoint span on `A_directional` and inherits that: read it as "the plausible
range is a third of what §C3 implied", not as a bound.

### The tie at 0.1 is invisible to the obvious check

Setting `w_SD` to exactly `producer_merchant`'s 0.1 leaves the sorted category list
**unchanged**, because Python's sort is stable and the insertion order already puts `swap`
first. A naive order check therefore reports the ordering intact when it has been
**collapsed**: the table has stopped distinguishing a swap dealer from a producer hedging
physical, which is the single distinction §6.3 is most confident about, and it is a different
object from a re-weighting.

`weight_sensitivity.single_weight_sweep` reports `ties_with` and fails `preserves_order` on a
tie for that reason, and
`tests/test_supplemental_live.py::test_c10_the_plausible_band_is_narrower_than_c3_swept`
asserts the classification rather than the swing, since the classification is what makes the
smaller number the honest one and it is a property of the weight table rather than of any
week's data.

**This closes the floor on the weight decision's option (b).** "Cut it toward 0.1" stops at
0.1 exclusive: 0.1 itself is the boundary of the plausible class rather than a point inside
it, and the stress reading of 0.067 is unreachable without asserting something §6.3
contradicts. That is a constraint on the option, not an argument against it.

### `single_weight_sweep`, and why `sweep` could not answer this

`sweep` jitters **every** weight at once and reports rank *stability* (`top_n_overlap`,
`rank_corr`), which is the right shape for "does a published ranking survive the table being
wrong" and the wrong shape for "how far does the headline move when this one weight moves",
because a rank correlation is invariant to exactly the monotone rescaling a single weight
induces. The question had been asked three times by then and answered ad-hoc every time:
`2026-08-01 §A22` for `producer_merchant`, `§C3` and `§C6` for `swap`.

Reproducer: [`../analysis/reproduce_w_sd_band.py`](../analysis/reproduce_w_sd_band.py).

---

## C11. `rank_markets` now checks alignment instead of documenting it

**Closes `§C5`'s trap**, which was recorded and left open. `§C5` found it while writing a
reproducer, wrote it down, and changed nothing in code, so the next caller to reach for the
obvious Series was owed the same hour.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`,
which uses the corrected idiom and would return 0 of 279 under the old behaviour.

`rank_markets(fragility, volume=...)` documents `volume` as "aligned to `fragility`'s index".
That index is a `RangeIndex`, so the alignment is **positional**, while the frame carries a
`market_code` column that makes a `market_code`-indexed Series the natural thing to pass. It
was silently `reindex`ed to all-`NaN`, and every `dtl_*` column came back null.

**The reason this is worth a `raise` rather than a warning is that its output is a valid
answer to a different question.** "Every duration is null" is exactly what a panel with no
volume join looks like, which the package produced for months and which `README.md` and
`core/config.py` both still asserted at the time. `§C5` records the actual cost: a first
attempt at the covered-market count returned **0 of 279** and read as confirmation of the
stale claim, rather than as a broken call.

| call | before | now |
|---|---|---|
| `volume=f["market_code"].map(adv)` | 25 of 279 | 25 of 279, unchanged |
| `volume=adv` (indexed by `market_code`) | **0 of 279, silently** | `PressureError` |
| `volume=None` | all null | all null, unchanged |

**The check is on labels, never on values, and that is the whole design.** Partial volume
coverage is the *ordinary* case (25 of 279), so it has to stay expressible; a guard that
looked at nullity would reject the normal panel and push callers back onto the unchecked
path. `frame["market_code"].map(series)` produces the frame's own index with `NaN` values,
which passes, while a foreign index fails. The error reports the overlap because zero
overlap and partial overlap want different fixes: the first is a wrong index type, the second
is usually a frame filtered after the Series was built.

Guarded by `tests/test_panel.py::test_a_mislabelled_volume_index_raises_rather_than_nulling_every_duration`
and its companion `::test_a_market_with_no_volume_is_a_null_value_not_a_missing_label`, which
pins the ordinary case so the guard cannot later be tightened into rejecting it.

---

## C12. The covered universe is 45 markets across two report types, not 25

**Contradicts** [`../handoffs/2026-08-03-step2-contract-master.md`](../handoffs/2026-08-03-step2-contract-master.md)
§0 and §1a, which scope the monitored universe as "25 of 279 Disaggregated codes" and ask for
an inventory of 25. The 25 is correct and is not the universe.

The contract-spec table holds **47 symbols**, and every one of them has a price series
(`spec symbols without price: []`, and the converse is empty too). They reach the panels like
this, counting a market as covered when `ContractMaster.annotate` resolves a symbol for it:

| report type | markets on panel | spec'd, union over 82 weeks | spec'd in the latest week |
|---|---|---|---|
| Disaggregated | 346 | 26 | **25** |
| TFF | 111 | 21 | **20** |
| | | **47** | **45** |

26 + 21 = 47 exactly, so the spec table is fully consumed and nothing in it is stranded. The
handoff counted one report type. The 22 symbols missing from its list are not missing specs:
they are currencies (`6A 6B 6C 6E 6J 6M 6N 6S`, `DX`), equity indices (`ES NQ RTY YM EMD
NKD`), rates (`ZB ZF ZN ZT`) and crypto (`BTC ETH`), and they are absent from Disaggregated
because **CFTC does not publish financials there**. They are on TFF, where `fragility_frame`
scores them today.

`legacy` is a third report type and is deliberately refused rather than empty:
`ConfigError: no fragility weights configured for report_type 'legacy' ... its
'noncommercial' bucket merges levered funds with everything else non-commercial, which is the
distinction these weights exist to make.`

**Consequence for the handoff's §0, and it survives.** The scoping decision was "scope by
where contract specs exist, not by where the cocoa shape holds", and that decision is
unaffected: it is the *count* under it that was understated, by a factor of 1.8. Anything
sized against "25 markets" (a roll-calendar backlog, a coverage table, a published universe)
should be sized against 45.

### The count is report-week dependent, which no coverage figure in this package said

The union column above exceeds the latest-week column by exactly one on each panel, and the
Disaggregated case is oats (`004603`, `ZO`), which is **spec'd, priced, and simply not in the
latest report**. It appears in **23 of 82** vintage weeks. `2026-08-02 §B29` already recorded
oats as "intermittent reporting, and it recurs" for the flow work, so this is the same fact
arriving at the coverage layer.

So "25" is a statement about report week 2026-07-28 and not a property of the store, and a
count taken on a different week is legitimately 26 without anything having changed. Any
inventory published from one week carries its week, which is why the companion document is in
[`../analysis/`](../analysis/) (point-in-time, never amended) rather than in `design/`.


Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`, and the full covered-set table is in [`../analysis/2026-07-28-contract-spec-inventory.md`](../analysis/2026-07-28-contract-spec-inventory.md).

---

## C13. The gate passes, and the failure mode it screens for is absent rather than rare

**Executes** the handoff's §1b, whose stated purpose is to catch the case where "the 25 are
mostly ICE basis contracts rather than the metals and livestock where the shape holds", making
the coverage "technically real and analytically empty".

**Stratum is 25 of 25 real outright, and 0 of 25 power/gas/carbon venue.** Not a majority,
all of them. Read against the 76%-power universe `2026-08-02 §B31` measured, the covered set
is not a sample of the panel at all: it is the complement of the thing that made the panel
hard to reason about.

The stratum column uses `§C14`'s three classes, so the two sections are the same partition
counted from opposite ends:

| complex | covered | | class | covered | uncovered |
|---|---|---|---|---|---|
| Grains | 6 | | real outright | **25** | 34 |
| Softs | 6 | | differential / spread / crack | 0 | 7 |
| Metals | 5 | | environmental / power certificate | 0 | 213 |
| Energies | 4 | | | | |
| Live Stock | 3 | | | | |
| Dairy | 1 | | | | |

The 213 certificates are 145 ICE Futures Energy Div and 68 Nodal Exchange.

**Overlap with the always-template set is 7 of 7.** Gold, silver, copper, live cattle, feeder
cattle, coffee and RBOB, the markets `2026-08-02 §B36` found extreme in *both* halves of its
window, are all inside coverage. The set the handoff worried might be excluded is entirely
included.

**Managed Money prominence, median `|P_MM| / OI`: covered 0.1371, uncovered 0.0370.** The
covered markets carry 3.7x the levered-holder prominence of the ones that drop out, which is
the direction the fragility argument needs and is not something the spec table was selected
to produce.

### The one real qualification, and it was predicted

`§B33`'s energy finding reproduces and applies *inside* coverage: pooled over the four covered
energy outrights, **51.2%** of market-weeks have Managed Money under 5% of open interest
(n=328), against **13.9%** for the other 21 covered markets (n=1,722). Per market it is Nat
Gas 70.7%, WTI 69.5%, ULSD 54.9%, RBOB 9.8%.

So energy is thin on the fragility term wherever it appears, and being spec'd does not fix
that. This is a **known property of four named markets**, not a defect in the scoping rule,
and it is the opposite of the failure the gate screens for: the gate asks whether coverage is
full of markets the thesis cannot speak about, and the answer is that it contains four where
it speaks quietly and 21 where it speaks normally.

**Verdict: the gate passes.** Proceed rather than stop.


Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`, and the full covered-set table is in [`../analysis/2026-07-28-contract-spec-inventory.md`](../analysis/2026-07-28-contract-spec-inventory.md).

---

## C14. "No contract spec" is three populations, and only 34 of 254 are a backlog

**Executes** the handoff's §1c, which anticipates two populations (`missing` = a real
tradeable contract whose spec we have not entered; `inapplicable` = no meaningful spec to
have). Measured, there is a third, and it is the one that would have been mis-filed.

| class | n | disposition |
|---|---|---|
| environmental / power certificate | 213 | **inapplicable, permanent.** RECs, carbon allowances, PJM and ERCOT zones |
| differential, spread or crack | 7 | **inapplicable, and not for the same reason** |
| real outright | **34** | **missing. This is the backlog** |

**The middle row is the correction.** A venue-based split (the obvious one, and the one the
handoff's framing invites) puts 41 codes in "classic outright" because they trade on NYMEX and
COMEX rather than on Nodal. Seven of those are differentials, and they are the complete list
rather than examples:

| code | name |
|---|---|
| `0676A5` | WTI HOUSTON ARGUS/WTI TR MO |
| `067A71` | WTI MIDLAND ARGUS VS WTI TRADE |
| `022A13` | UP DOWN GC ULSD VS HO SPR |
| `0676A6` | WTI HOUSTON ARGUS/WTI BALMO |
| `111A34` | GULF COAST CBOB GAS A2 PL RBOB |
| `86465A` | GULF JET NY HEAT OIL SPR |
| `86565A` | GULF # 6 FUEL OIL CRACK |

These have a multiplier and a tick size, so they are not "no meaningful spec to have" in the
handoff's sense, and they are still permanent exclusions, for a reason the handoff's binary
cannot express: **the normalisation ladder computes a position value, and a differential does
not have one.** `P · M · F` on a spread whose `F` oscillates around zero is not a smaller
notional, it is not a notional. This is the same class of error as the `backadj` trap in
`CLAUDE.md`'s table, where a number is produced, is finite, and means nothing.

The 34 genuine backlog items, largest first by mean open interest over the vintage panel:

| market | mean OI | | market | mean OI |
|---|---|---|---|---|
| `067411` WTI, ICE Europe | 798,670 | | `191693` Aluminum MWP | 28,838 |
| `023A55` Henry Hub last-day fin | 420,336 | | `005603` Mini soybeans | 27,891 |
| `03565B` Henry Hub | 362,655 | | `189691` Lithium hydroxide | 27,847 |
| `135731` Canola | 271,205 | | `037021` USD Malaysian palm oil | 27,355 |
| `023A56` Henry Hub penultimate fin | 253,028 | | `063642` Cheese | 25,601 |
| `06765T` Brent last day | 217,269 | | `191696` Aluminium Euro prem | 24,299 |
| `06765A` WTI financial | 175,418 | | `06665T` Conway propane | 22,351 |
| `03565C` Henry Hub penult nat gas | 153,896 | | `188691` Cobalt | 15,233 |
| `06665O` Propane | 139,138 | | `050642` Butter | 14,789 |
| `001626` Wheat-HRSpring, MIAX | 77,384 | | `039601` Rough rice | 12,374 |
| `088695` Micro gold | 55,579 | | `052642` Non fat dry milk | 11,022 |
| `06665Q` Mt Belv normal butane | 51,235 | | `192691` N Euro HRC steel | 10,973 |
| `06665P` Mt Belvieu ethane | 49,818 | | `052644` CME Milk IV | 10,019 |
| `06665R` Mt Belv nat gasoline | 40,672 | | `406651` PGP propylene | 7,367 |
| `025651` Ethanol | 39,668 | | `025608` Ethanol T2 FOB | 5,647 |
| `192651` Steel HRC | 33,298 | | `06665B` Argus propane Far East | 5,264 |
| `06665G` Propane non-LDH Mt Bel | 29,972 | | `052645` Dry whey | 3,968 |

Two observations that change how the backlog should be read, rather than only its length.

**It is not 34 independent markets.** Fourteen of the 34 are variants within three families:

| family | codes | |
|---|---|---|
| Henry Hub natural gas | 4 | `023A55` `023A56` `03565B` `03565C` |
| WTI and Brent | 3 | `067411` `06765A` `06765T` |
| Mt Belvieu / propane / NGL grades | 7 | `06665B` `06665G` `06665O` `06665P` `06665Q` `06665R` `06665T` |
| everything else, one instrument each | 20 | |

Adding specs is per-code work, but the *analytical* gain is nearer **23 new instruments than
34**, and `continuity.py` already exists because a market code is not an instrument.

**Micro gold (`088695`) is the case to think about before the large ones.** It is the same
underlying as `088691`, which is already covered, at a tenth the contract size. Adding it
without a view on aggregation would put gold into every cross-market ranking twice, at two
scales, and `2026-08-02 §B30` is the precedent: two lumber codes were one instrument, and
merging them end to end lifted every rung. A spec is necessary and not sufficient.

**Adding any of these needs the Norgate producer**, which runs on the Windows box only
(`manifests/prices.json` records `"source": "norgate"` for both bars and `contract_specs`).
So the backlog is not a code change here, which is what the handoff's §0 means by "spec
coverage is a build backlog, not a boundary": it is something we control, and not something
this repo can execute alone.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::contract_spec_inventory`, and the full covered-set table is in [`../analysis/2026-07-28-contract-spec-inventory.md`](../analysis/2026-07-28-contract-spec-inventory.md).

---

## C15. The head of the backlog is NOT a duplicate, and the objection to it was mine

**Withdraws an objection this session raised**, and records why it was wrong, because the
reasoning that produced it is the kind that generalises badly.

`§C14` closed with the advice that **micro gold should be settled before the large backlog
items**, since it duplicates a covered market at a tenth the size and `2026-08-02 §B30` is
the precedent for merging two codes before ranking. That advice stands for micro gold. When a
request arrived to spec **ICE Europe WTI and the Henry Hub complex**, the same objection was
raised by analogy: these look like variants of `067651` (NYMEX WTI, covered as `CL`) and
`023651` (NAT GAS NYME, covered as `NG`), so specing them would put two underlyings into
every cross-market ranking six times over.

**Measured over the 82 vintage weeks, the analogy fails.**

| code | candidate | against | `r(OI)` | `r(MM net)` | `r(ΔMM)` | mean OI |
|---|---|---|---|---|---|---|
| `067411` | ICE Europe WTI | CL | 0.771 | **-0.224** | -0.054 | 798,670 |
| `023A55` | HH last day fin | NG | -0.097 | **-0.643** | -0.164 | 420,336 |
| `023A56` | HH penultimate fin | NG | -0.146 | -0.413 | -0.063 | 253,028 |
| `03565B` | HENRY HUB | NG | 0.179 | **-0.621** | -0.116 | 362,655 |
| `03565C` | HH penultimate nat gas | NG | -0.424 | -0.128 | -0.234 | 153,896 |

**Every Managed Money correlation is negative, and every flow correlation is near zero.**
These are not a second copy of the flagship's holder base; they are a different holder base
taking the other side, which is what a financially-settled look-alike beside a physically
settled benchmark should look like.

**The specific error is worth naming, because it is a measurement this package already had
the means to make and did not.** Open interest is the series that *does* track (WTI at
0.771), and open interest is what the eye reaches for when asking "is this the same market".
It is the wrong series for the question. Crowding is a property of *who holds*, so the
duplication test has to be run on the positioning, and on the positioning these five are
nearly independent of their flagships. Reasoning by analogy from a name (`§C14`'s micro gold)
and confirming it against the most available series would have removed the two largest items
in the backlog on a false premise.

**This does not rehabilitate micro gold.** `088695` is the same contract as `088691` at a
tenth the size, traded by the same participants against the same delivery. The distinction is
not "variant versus not" but whether the second code has its own holder base, and that is
measurable rather than inferable from the name. `§C14`'s advice is narrowed accordingly:
**test the positioning correlation before merging or excluding any variant code**, rather
than treating a shared underlying as sufficient grounds for either.

### The blocker is unchanged, and it is structural

Nothing here can be acted on from this repo. `ContractMaster.load()` reaches a spec only
through a **registry symbol** joined to the Norgate `contract_specs` table, and `coverage()`
requires a spec **plus both stored price tiers** (`unadj` and `backadj`, since `propadj` is
derived from the pair on read). All five candidates have **no registry symbol at all**, and
all three artifacts come from the Windows-only Norgate producer.

**MME and MFS are the worked example, already in the data.** They are the two of 49 registry
symbols with no `contract_specs` row, carry `norgate: null`, and report
`missing: specs,unadj_price,backadj_price`. Adding registry entries for the five candidates
without a producer run would reproduce exactly that and nothing more: five inert rows that
look like progress and change no coverage figure.

The work order is [`../handoffs/2026-08-03-spec-backlog-producer.md`](../handoffs/2026-08-03-spec-backlog-producer.md).

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::variant_codes_are_not_duplicates`.

---

## C16. Correlating positioning LEVELS is spurious, and §C15 led with it

**Corrects the EMPHASIS of `§C15`, not its conclusion.** Found while applying §C15's own
rule ("test positioning correlation before merging or excluding a variant code") to the ag
and dairy backlog, where several nearest-match pairings came back economically absurd:
Malaysian palm oil against lean hogs at 0.741, non fat dry milk against palladium at -0.666,
butter against NY Harbour ULSD at 0.693. Absurd pairings are a symptom, so the symptom was
measured rather than explained away.

**Managed Money net positioning is near unit-root.** Lag-1 autocorrelation over the covered
25 has median **0.956** (min 0.784, max 0.981); first-differenced it is 0.211. A correlation
between two such series is the Granger-Newbold spurious-regression problem in textbook form.

Three measurements, each stronger than the last:

| test | levels | first differences |
|---|---|---|
| cross-complex pairs, n=251, true `r` should be ~0: median \|r\| | **0.395** | 0.095 |
| the same, p90 / max | 0.705 / 0.878 | 0.229 / 0.392 |
| the same, share above 0.5 | **33.5%** | **0.0%** |
| max \|r\| scanning all 25 covered with an INDEPENDENT random walk, median | **0.773** | 0.237 |
| the same, p95 | 0.905 | 0.333 |

**A series with no relationship to anything scores a maximum level correlation of 0.773 half
the time.** So every "nearest holder base" figure computed on levels is uninformative, and
the absurd pairings above are not anomalies to explain: they are the expected output of the
procedure.

**What this does to `§C15`.** Its table led with `r(MM net)`, bolding negative level
correlations from -0.224 to -0.643 as the striking evidence that the energy variant codes
carry a different holder base. **Those numbers are noise.** §C15 also reported `r(ΔMM)`, at
-0.054 to -0.234, and against the noise band above (cross-complex differences, median 0.095
and p90 0.229) those are genuinely consistent with independence. **The conclusion survives on
the statistic it printed second.** That is luck rather than method: had the level correlations
come back strongly positive by chance, §C15 would have withdrawn a correct recommendation.

The corrected rule, superseding §C15's closing sentence: **test positioning correlation on
FIRST DIFFERENCES, against a noise band computed from the same panel.** A level correlation
is not weak evidence of a shared holder base, it is no evidence.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::positioning_levels_are_spurious`.

---

## C17. The ag and dairy backlog is mostly not worth speccing, and the dairy block fails the gate

**Answers** a request to prioritise the ag and dairy codes in the §C14 backlog. The honest
answer is that **six of the ten should not be specced at all**, and the largest by open
interest is not the one to start with.

Three criteria in order, the first deciding most of the list:

1. **Is there a levered holder?** Median `|P_MM| / OI` against the covered median of
   **0.1371**. This is `§C13`'s gate applied per candidate rather than to the whole set.
2. **Is the flow independent?** First-differenced correlation against the nearest *economic*
   sibling, judged against `§C16`'s noise band (p90 = 0.229). Levels are not used, and the
   sibling is paired by economics rather than by best fit, for the same reason.
3. **Can it be scored?** Weeks present of 82, per `2026-08-02 §B29`'s oats lesson.

| code | market | mean OI | weeks | MM share | MM net | `r(ΔMM)` | verdict |
|---|---|---|---|---|---|---|---|
| `039601` | ROUGH RICE | 12,374 | 82 | **0.433** | 5,173 | 0.047 | **INDEPENDENT** |
| `001626` | WHEAT-HRSpring | 77,384 | 82 | 0.278 | 20,934 | 0.338 | duplicative flow |
| `135731` | CANOLA | 271,205 | 82 | 0.209 | 56,733 | 0.584 | duplicative flow |
| `063642` | CHEESE | 25,601 | 82 | 0.076 | 2,058 | 0.520 | duplicative flow |
| `037021` | Malaysian palm oil | 27,355 | 82 | 0.048 | 1,147 | 0.053 | EXCLUDE, no levered holder |
| `052645` | DRY WHEY | 3,968 | **14** | 0.035 | 130 | 0.334 | EXCLUDE, history |
| `052642` | NON FAT DRY MILK | 11,022 | 82 | **0.018** | 204 | -0.076 | EXCLUDE, no levered holder |
| `050642` | BUTTER | 14,789 | 82 | **0.013** | 200 | 0.157 | EXCLUDE, no levered holder |
| `052644` | CME MILK IV | 10,018 | 82 | **0.012** | 106 | -0.174 | EXCLUDE, no levered holder |
| `005603` | MINI SOYBEANS | 27,891 | **13** | **0.000** | 0 | n/a | EXCLUDE, history |

**Only rough rice clears every bar, and it is the smallest market that does.** Its Managed
Money share of 0.433 is **3.2x the covered median** and the highest of any candidate, its
flow correlation against corn (0.047) sits well inside the noise band, and it has all 82
weeks. Ranking this backlog by open interest, which is how §C14 printed it, puts rough rice
seventh of ten.

**The dairy complex is the finding, and it is negative.** Butter, non fat dry milk, Class IV
milk and dry whey carry Managed Money books of **0.012 to 0.035 of open interest**, an order
of magnitude below the covered median, and 106 to 204 contracts in absolute terms. These are
hedger markets: dairy processors laying off input and output risk, with essentially no
levered participant to be forced out. Speccing them would add markets **the thesis cannot
speak about**, which is precisely what `§C13`'s gate exists to keep out of coverage. Cheese
is the only dairy code with a real Managed Money presence and its flow is 0.520 correlated
with Class III milk, which is unsurprising given Class III is priced off cheese.

**Two confirmations of earlier rules, both by measurement rather than by name.** Mini soybeans
is the micro-gold case `§C14` predicted, and it fails twice over: 13 of 82 weeks and a median
Managed Money net of **exactly zero**. And canola, the largest of the ten, is the most
duplicative on flow (0.584 against soybean oil), so open interest and analytical value point
in opposite directions across this whole set.

**Recommended tranche: `039601` rough rice alone**, with `001626` WHEAT-HRSpring second if a
third wheat class is wanted for its own sake rather than for new information. Everything below
that is either redundant with a covered market or has no holder the monitor can describe.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::ag_dairy_backlog_priority`.

---

## C18. The levered-holder bar is per COMPLEX, and §C17's flat cut is wrong for energy

**Corrects `§C17`'s first criterion.** §C17 excluded a candidate whose median `|P_MM| / OI`
fell under **0.05**, implicitly benchmarking against the pooled covered median of 0.1371.
Applied to the energy backlog that rule is not merely conservative, it is **wrong**, and it
was caught only because it condemned five codes already committed to a producer run.

**The covered median MM share by complex, which is what a candidate should face:**

| complex | covered median | n |
|---|---|---|
| Energies | **0.0435** | 4 |
| Grains | 0.0982 | 6 |
| Dairy | 0.1021 | 1 |
| Softs | 0.1651 | 6 |
| Metals | 0.1931 | 5 |
| Live Stock | 0.3039 | 3 |
| **pooled** | **0.1371** | 25 |

**Nat Gas (0.0369) and WTI (0.0399) are both UNDER the flat 0.05 cut.** They are the two
largest markets in the entire universe and they are already covered. A bar that excludes them
is not measuring whether a market has a levered holder; it is re-discovering that **energy is
thin on Managed Money**, which `2026-08-02 §B33` and `§C13` had both already measured, and
then mislabelling that property of the complex as a defect of each candidate.

The corrected bar: **a candidate is thin when its MM share is under 0.5x its own complex's
covered median.** The 0.5x is a choice rather than a measurement and is stated as one.

**Every `§C17` verdict survives**, which is why that block is kept and kept running rather
than deleted. Its candidates are grains (bar 0.0982) and dairy (0.1021), both near the pooled
0.1371, so the flat cut happened to be roughly right there. Palm oil is the only candidate
whose *reason* changes, from "under 0.05" to "0.49x of grains", and it lands the same way.

**The general lesson, and it is the second time this session:** `§C16` found a statistic that
returned strong correlations between unrelated markets, and this finds a threshold that
returns "no levered holder" for the largest markets in the book. Both were calibrated against
a pooled figure when the quantity varies by an order of magnitude across complexes. **A bar
taken from a pooled median is a bar for the median complex and for no other.**

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::backlog_priority_within_complex`.

---

## C19. The whole 34-code backlog under the corrected bar, and every committed code passes

**13 of 34 pass every bar**, 5 fail on duplicative flow and 16 on the levered-holder bar.

**All six committed codes pass**, so nothing already decided needs revisiting:

| code | market | x complex | `r(ΔMM)` |
|---|---|---|---|
| `023A56` | HENRY HUB PENULTIMATE FIN | 2.02x | -0.063 |
| `023A55` | HENRY HUB LAST DAY FIN | 1.09x | -0.164 |
| `067411` | ICE Europe WTI | 0.98x | -0.054 |
| `03565C` | HH PENULTIMATE NAT GAS | 0.78x | -0.234 |
| `03565B` | HENRY HUB | 0.70x | -0.116 |
| `039601` | ROUGH RICE | **4.41x** | 0.047 |

Tranche 1 spans 0.70x to 2.02x of typical energy, which is the range the covered energy
markets themselves occupy. Rough rice at 4.41x of grains is the strongest candidate anywhere
in the backlog, on any complex.

### Seven new candidates pass

| code | market | complex | x complex | mean OI |
|---|---|---|---|---|
| `06665P` | MT BELVIEU ETHANE OPIS | Energies | **3.80x** | 49,818 |
| `406651` | PGP PROPYLENE (PCW) CAL | Energies | 2.25x | 7,367 |
| `192691` | NORTH EURO HRC STEEL | Metals | **1.88x** | 10,973 |
| `192651` | STEEL-HRC | Metals | 0.98x | 33,298 |
| `06665Q` | MT BELV NORM BUTANE OPIS | Energies | 0.91x | 51,235 |
| `06665O` | PROPANE | Energies | 0.63x | 139,138 |
| `189691` | LITHIUM HYDROXIDE | Metals | 0.54x | 27,847 |

**Mt Belvieu ethane is the standout and was invisible under the flat bar.** At 3.80x the
energy median with 8,798 contracts of Managed Money net and all 82 weeks, it is the second
strongest candidate in the backlog after rough rice, and §C17's rule would have excluded it
at 0.165 > 0.05 only by luck: three of its NGL neighbours sit under 0.05 and would have been
excluded correctly for the wrong reason.

**`406651` and `192691` carry a caveat**: 66 and 78 weeks of 82 respectively. Both clear the
40-week floor, neither has the full history, and `192691` is 78 weeks because it is genuinely
newer rather than intermittent.

### The excludes, and one that is remarkable

**Micro gold fails BOTH bars**: 0.07x of the metals median, and flow correlation **0.355**
against gold, above §C16's 0.229 band. `§C14` recommended settling it before the large items
by analogy with `2026-08-02 §B30`'s lumber case; that recommendation is now **measured rather
than inferred**, and it is the only backlog code that is both thin and duplicative.

**`06765A` WTI FINANCIAL CRUDE OIL is the finding worth carrying.** Mean open interest
**175,418**, which would place it 15th of the covered 25, and a median Managed Money net of
**475 contracts**, 0.07x the energy bar. A market can be large, liquid, a pure outright, and
still contain essentially no participant this monitor describes. Two NGL codes are starker
still: `06665G` propane non-LDH at 29,972 OI and `025608` ethanol T2 at 5,647 both have a
median Managed Money net of **exactly zero**.

That is the same shape as the dairy block in `§C17` and it is now the dominant failure mode
across the whole backlog: **16 of 34 codes fail for want of a levered holder, against 5 for
redundancy.** The backlog is not mostly full of duplicates. It is mostly full of markets where
the fragility term has nothing to describe, which is what `§C13`'s gate found from the outside
and this finds from the inside.

Reproducer: [`../analysis/reproduce.py`](../analysis/reproduce.py)`::backlog_priority_within_complex`.
