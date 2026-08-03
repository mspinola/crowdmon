# Spec amendments, 2026-08-03

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

Sections here carry a **`C` prefix**, per the per-day convention set in `f194c4e` and stated
in [README.md](README.md): "Each new file gets its own date and its own letter prefix (`B1`,
`C1`, ...)". [`amendments-2026-08-02.md`](amendments-2026-08-02.md) is closed at B32.
Cross-file references carry the date: `2026-08-02 §B31`.

> **These are the sections `2026-08-03-index-share.md` §2 cites as "§B33-B36".** That
> citation was written before they existed and cannot be honoured literally: the amendments
> are one file per day and 08-02 closed at B32, so work measured on 08-03 takes `C`. The
> mapping is
>
> | cited | is |
> |---|---|
> | §B36 (classification instability) | **§C1** |
> | §B33 (template rate by stratum, swept) | **§C2** |
> | §B34-B35 (`Q_sell`/`Q_buy`, swept) | **§C3** |
> | `A_agnostic` median | **§C4**, which finds it undefined |
>
> **The cited figures were not invented.** §C1 reproduces "22 of 39" and "17 in both halves"
> exactly. Whoever wrote the handoff ran this measurement and did not record it, which is the
> failure the amendment convention exists to prevent, arriving from the other direction: not a
> stale number, an accurate one with no home.

Every figure below is reproduced by
[`../analysis/reproduce_template_stability.py`](../analysis/reproduce_template_stability.py)
against `COTDATA_STORE=~/code/cotdata_store`, over the vintage store's 82 weeks.

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

**Small discrepancy against the handoff's citation, recorded rather than smoothed.** §3 cites
cocoa as "0.976 then 0.100"; measured here it is **1.000 then 0.098**. The difference is one
week in the first half and is consistent with a split point one row earlier. The counts (22,
17) match exactly, so this is a split-boundary difference and not a disagreement about what
cocoa did.

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

## C4. `A_agnostic` has no definition here, and the obvious one is degenerate

**Contradicts:** `2026-08-03-index-share.md` §2, which lists "`A_agnostic` median" among the
figures to recompute.

The string appears nowhere in `src/`, `tests/` or `docs/design/` except in the handoff citing
it. There is no such quantity in this package.

The natural reading, an asymmetry computed with weights that do not discriminate between
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

So a weight-agnostic asymmetry measures nothing at all. This is the same result as
`2026-08-01 §A21` ("Phi has no cross-market signal independent of the weight table") in its
sharpest form: with the weights flattened, the asymmetry does not merely lose signal, it
becomes a constant.

**No definition is invented here.** A useful `A_agnostic` would have to be some other
quantity, most plausibly an asymmetry of the underlying position concentration that does not
route through the weights at all, and choosing it is a design decision rather than a
measurement. Whoever wrote §2 had something in mind; it is not recoverable from the citation,
and guessing would put a number in a document with nothing behind it.

**Consequence for the handoff.** §2 lists three headline figures. One cannot respond to the
parameter it is swept against (§C2), one is undefined (§C4), and one answers clearly and
interestingly (§C3). §2 is executable on `Q_sell`/`Q_buy` alone, and that is enough to answer
the question it was really asking.

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

## C6. §C3's own 42% is inflated: 0.7 is outside the plausible class, and the honest figure is 17.9%

**Corrects `2026-08-03 §C3`**, which is this file. Swept over the wider band the regime
finding implies (0.067 stress, 0.305 routine, plus §C3's grid), and reported through the new
`weight_sensitivity.single_weight_sweep` rather than ad-hoc.

The classification that matters is not new. `2026-08-01 §A22` established that §6.3's
judgement is an **ordering** before it is a set of values, and measured what the distinction
is worth: order-preserving jitter keeps at least 7 of the `Q_sell/OI` top 10, while inverting
the ordering destroys it entirely (0 of 10, rank correlation -0.045). A swept value that
reorders the table is a different claim, not a rival value.

**Three of the seven swept values are outside that class, and one of them is §C3's own
endpoint.** With `producer_merchant: 0.1`, `other_reportable: 0.5`, `nonreportable: 0.6`:

| `w_SD` | status | why |
|---|---|---|
| 0.067 | **outside** | now below `producer_merchant` |
| 0.100 | **outside** | **ties** `producer_merchant`, collapsing the distinction |
| 0.200 | inside | |
| 0.305 | inside | |
| 0.400 | inside | live |
| 0.550 | **outside** | now above `other_reportable` |
| 0.700 | **outside** | now above `nonreportable` and `other_reportable` |

Median `A = Q_sell/Q_buy`, over the 82-week vintage panel:

| population | over the **order-preserving** band `[0.2, 0.4]` | over the full 0.067-0.7 band |
|---|---|---|
| all 108,780 rows / 346 markets | 0.9869 to 1.0213, **3.5%** | 0.9739 to 1.0904, 12.0% |
| the 13 Supplemental markets | 2.1845 to 2.5750, **17.9%** | 2.0137 to 3.1028, 54.1% |

**So §C3's headline 42.0% is not wrong arithmetic, it is the wrong band.** It swept 0.2 to
0.7 and quoted the span, and 0.7 puts a swap dealer above both retail and the mixed
"other reportable" bucket, which is a claim about holder behaviour nobody in this project has
made. Restricted to values that keep §6.3's ordering intact, the answer is **17.9% on the
markets in scope and 3.5% pooled**.

**The conclusion moves with it, and it moves toward the sceptical reading.** §C3 closed with
"`w_SD = 0.4` is not a safe default that happens not to matter. It is a number the answer
depends on." That survives in direction and not in force: 17.9% across the whole plausible
range is a real dependence and it is not the 42% that sentence was written about. The
practical distance is smaller still, because the live value 0.4 and the routine-turnover
reading 0.305 are 7.1% apart on the Supplemental 13 (2.5750 to 2.3920).

**The tie at 0.1 is worth stating separately, because a stable sort hides it.** Setting
`w_SD` to exactly `producer_merchant`'s 0.1 leaves the sorted category list unchanged, so a
naive order check reports the ordering intact. It is not intact, it is **collapsed**: the
table stops distinguishing a swap dealer from a producer hedging physical, which is the one
distinction §6.3 is most confident about. `single_weight_sweep` reports `ties_with` and fails
`preserves_order` on a tie for that reason. This matters directly for the decision, since
"cut it toward 0.1" is one of the options on the table and 0.1 exactly is the boundary of the
class rather than a point inside it.

**What this does not change.** The template rate is still identically 0.447106 at every one
of the seven values, spread 0.000000000, because `_shape_labels` reads two category nets and
their signs and no weight of any kind enters it (§C2). Widening the band does not give that
quantity the ability to respond, and an insensitivity there remains uninformative about
`w_SD` no matter how wide the sweep.

Reproducer: [`../analysis/reproduce_w_sd_band.py`](../analysis/reproduce_w_sd_band.py).
