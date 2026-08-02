# Spec amendments, 2026-08-02

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

**This file opens the per-day amendments convention** set in `f194c4e`.
[`amendments-2026-08-01.md`](amendments-2026-08-01.md) reached A22 and is closed. Sections
here carry a **`B` prefix**, so a bare reference like "§B2" can never be ambiguous about which
file it means; the next file takes `C`. Cross-file references still carry the date:
`2026-08-01 §A15`.

> **Filed under 08-02, measured on 08-01.** The 08-01 file was closed to new sections partway
> through that day, which leaves a few hours with no home. Everything below was measured on
> 2026-08-01 against `COTDATA_STORE=~/code/cotdata_store`.
>
> **B1 and B2 were originally filed as A1 and A2** in this file, by the commonality session,
> before the `B` prefix landed. They are renumbered here so that "A1" means exactly one thing
> across the whole directory. `6c2b488`'s commit message refers to them by the old labels.

Figures below are reproduced by `docs/analysis/reproduce.py` (B1-B2, B9-B12),
`docs/analysis/reproduce_seasonal.py` (B3-B7), or asserted in `tests/test_commonality_live.py`
and `tests/test_trigger_live.py`.

---

## B1. §A.6's basket regression is vacuous unless the own market is excluded

**Contradicts:** appendix §A.6, which says to "regress each market's liquidity change on the
basket average" without saying whether market `i` belongs to its own basket. Taken literally
it does, and the resulting `beta_bar` is **not a measurement**.

**The identity.** If the basket is the simple mean of the same `N` series,

    sum_i cov(y_i, ybar) = cov(sum_i y_i, ybar) = cov(N.ybar, ybar) = N.var(ybar)

so `mean_i beta_i = 1` **exactly, for any data whatsoever**. Verified numerically to twelve
decimal places on independent series with zero real commonality, on strongly co-moving series,
and on a five-market sample. The number is the same in every case, because it is arithmetic
rather than an observation.

**On the real panel**, 25 markets, 2015-2026, Amihud illiquidity in log changes:

| basket | `beta_bar` |
|---|---|
| including the own market | **0.9999** |
| excluding it | **0.6341** |

The inflation is largest exactly where the measure matters most. Class III Milk goes from
**0.070 to 0.849**, a factor of **12**, so the market that most clearly exits through its own
door is made to look like one that exits with everybody else. Mean inflation across the
universe is 2.27x.

**Consequence.** `commonality_betas` excludes by default and the `exclude_own=False` path
exists only so a test can demonstrate the identity. A default that silently returned 1.0 for
everything would be the worst kind of wrong: plausible, stable, and meaningless.

**The signal that survives exclusion is real and interpretable:**

| markets | `beta` | reading |
|---|---|---|
| DC milk, HE hogs, LE cattle | 0.07-0.11 | own supply cycle. A different door |
| OJ, NG, GF, PL | 0.32-0.38 | |
| CC cocoa, GC gold, SB sugar | 0.54-0.58 | |
| CL crude, SI silver, ZC corn, RB gasoline | 0.95-0.97 | |
| ZW wheat, KE wheat-HRW | 1.01-1.02 | the same door |

That spread is what §A.6 is for, and it distinguishes crowded-and-liquid from
crowded-and-illiquid exactly as the section claims.

---

## B2. §A.6 cannot change §A.9's composite, because a percentile ignores a constant

**Contradicts:** the implied connection between appendix §A.6 and §A.9. §A.6 defines
`T_eff = T . (1 + gamma . beta_bar)` and §A.9 defines `I = pct(T_eff)`. Composed, the second
discards the first.

**Why.** With `beta_bar` constant, `T_eff` is a positive scalar multiple of `T`. A percentile
is invariant under any monotonic transform, so `pct(T_eff) = pct(T)` **bit-identically**.
Measured: maximum absolute difference **0.00e+00** at `gamma = 0.5` and at `gamma = 2.0`, on
both synthetic and real duration series. The same holds for a per-market constant `beta_i`,
because §A.9 takes the percentile within a market.

So the literal composition of the two sections is a no-op. Wiring it into `composite.py` and
recording it in a changelog would change nothing at all about `D`.

**What does work, and how little.** Only a **time-varying** `beta_bar_t` reaches the
composite. Measured on a rolling 252-day estimate over 2016-2026:

| | |
|---|---|
| `beta_bar_t` range | 0.423 to 0.780 (sd 0.080) |
| resulting `1 + 0.5.beta_bar` | 1.211 to 1.390, a **1.15x** spread |
| `T`'s own range, latest week | 0.80 to 10.6 days, a **13x** spread |
| rank correlation of `pct(T_eff)` against `pct(T)` | **0.985** |

By year, `beta_bar_t` runs 0.663 in 2018 down to 0.473 in 2024, and rises from 0.622 in 2019
to 0.714 in 2020, which is the right direction for a liquidity-commonality measure during a
crisis but a small move. The panel starts in 2015 so the rolling estimate begins in 2016; an
earlier start shifts these by a few hundredths and changes nothing about the conclusion.

**Consequence, and what this branch deliberately does not do.** `commonality.py` offers
`t_effective` and does **not** wire it into `composite.py`. Choosing between "leave `I` as
`pct(T)`", "use a rolling `beta_bar_t` for a 0.985-correlated variant", and "change what §A.9
means by `I`" is a decision about the composite's definition, and it belongs to whoever owns
that calibration rather than to the module supplying the input.

**`gamma` is a third configured constant with less support than the other two.** §A.5 gives
`kappa = 0.2` and `Y` in 0.5 to 1.0. The appendix gives `gamma` no value and no range
anywhere. `gamma_sensitivity` reports its effect in the same spirit as
`flow.tolerance_sensitivity`, and on a constant `beta_bar` that report is a column of 1.000
rank correlations, which is the finding above stated in the output rather than buried in a
docstring.

---

## B3. Nothing is "dominated by seasonality", and the category §5.4 names is not seasonal at all

**Contradicts** module spec §5.4: "Commercial and producer-merchant positioning in
agricultural markets is strongly seasonal ... Raw z-scores on those categories are **dominated
by seasonality** and will produce spurious extremes every year at the same time ... Managed
Money is less affected but not immune."

**Measured** over twenty years, 27 markets, on week-of-year variance share of extremity `z`:

| category | ag | non-ag | ratio |
|---|---|---|---|
| other_reportable | 0.0074 | 0.0028 | 2.65x |
| swap | 0.0141 | 0.0065 | 2.17x |
| nonreportable | 0.0059 | 0.0056 | 1.04x |
| **producer_merchant** | **0.0046** | **0.0049** | **0.95x** |
| managed_money | 0.0016 | 0.0042 | 0.39x |

Sample sizes are comparable (197 against 248 per week), so this is not a power artifact.

- **"Dominated by seasonality" is false.** The largest share anywhere is **1.4%**. A component
  that small cannot manufacture the spurious annual extremes §5.4 warns about.
- **Producer/Merchant is not more seasonal in ags**, ratio 0.95. The categories that are, Swap
  and Other Reportable, go unmentioned in §5.4.
- **"Managed Money is less affected" holds**, and most clearly in ags: 0.0016, the lowest in
  the table by a factor of three.

## B4. Deseasonalising raises the standard deviation, so the adjustment is off by default

**Amends** §5.4's instruction to "apply a seasonal decomposition ... before z-scoring
commercial categories in ags."

**Measured** on ag extremity `z`, applying the trailing week-of-year profile:

| | |
|---|---|
| rows with a profile | 43,395 of 57,805 (75.1%) |
| std before | 1.2489 |
| std after | **1.3212** |
| correlation | 0.9599 |
| rows moved more than 0.5 z | 15.7% |

A trailing week-of-year mean is an **estimate with its own error**, and when the component
being removed is worth at most 1.4% of variance, that error exceeds the signal. Subtracting it
adds noise. It is not a small intervention either: 15.7% of rows move by more than half a
z-unit, and it costs a three-year warm-up on top of extremity's own.

`seasonal.deseasonalise` exists and defaults off. Turning it on trades a visible caveat for an
invisible transformation.

## B5. `mean_spread` is noise-inflated, and it reversed my own first reading

**Adds** a methodological caution that cost a wrong published statement before it was caught.

`seasonality_report` emits two statistics. `variance_share` is the between-week share of total
variance. `mean_spread` is max minus min of the ~53 weekly means, and is **biased upward by
noise**, being the range of 53 noisy estimates.

On a synthetic pair with identical true seasonal amplitude, adding noise moved `mean_spread`
from 20.7 to 64.2 while `variance_share` correctly fell from 0.98 to 0.13.

**On the real panel the two rank the categories nearly in reverse.** A first pass using
`mean_spread` reported that ags carry roughly twice the seasonal swing and that Managed Money
is the most seasonal ag category. Both are wrong. The concrete mechanism, for ag
Producer/Merchant:

| | week | mean z | observations |
|---|---|---|---|
| peak | 2 | +0.095 | 198 |
| trough | **53** | **−0.597** | **33** |

**ISO week 53 exists only in some years.** Excluding weeks with under 50 observations, the
spread falls from **0.692 to 0.275** z-units, against a non-ag figure of 0.334 computed the
same way, so on well-sampled weeks the ag swing is the *smaller* of the two.

`seasonality_report` now sorts on `variance_share`, emits `per_week` so the bias is visible,
and its docstring says never to compare `mean_spread` across groups of different size.

## B6. No week-of-year scheme pins a seasonal moment

**Adds** a floor on what §5.4's approach can resolve, which the spec does not state.

The third Tuesday of August falls in ISO week 34, 33, 33, 33, 34 over 2020-2024;
`dayofyear // 7` gives 33, 32, 32, 32, 33. A fixed point in the crop calendar drifts by ±1
week against any weekly index, because 52 weeks is not 365 days.

That smears any week-of-year profile by about a week in each direction. It is not something a
better bucketing fixes, and it is asserted in `tests/test_seasonal.py` so nobody tries.

## B7. Two earlier caveats are closed, and the readings they flagged are sound

**Resolves** open caveats in
[2026-07-28-extremity.md](../analysis/2026-07-28-extremity.md) ("real but modest, unmeasured
for CR") and [2026-07-28-concentration.md](../analysis/2026-07-28-concentration.md) ("five of
six markets extreme against own history are short-side ags, exactly what §5.4 predicts as an
artifact").

At **at most 1.4% of variance**, seasonality cannot lift five markets to the top of a
percentile ranking. The concentration reading is not a seasonal artifact.

Still open: seasonality of the **CR series itself** was not measured, only of extremity `z`.
And this is the Disaggregated 27-market panel; the ICE/Nodal power and REC universe has its own
calendar (compliance years, delivery periods) that is plausibly much stronger and is
unmeasured, since those markets lack the history a three-year profile needs.

---

## B8. §A.7 never needed the aggregate-capital estimate it was filed as blocked on

**Contradicts:** the not-built table's A.7 row, "prices + a CTA replication model", which
survived the module being built and is corrected in this commit.

§A.7 models systematic position size as `q = s(F) . (sigma_target/sigma) . lambda(Sigma) . A`,
and `A` is aggregate systematic capital calibrated against SG Trend or BTOP50. Neither index
is in this workspace, so the whole section was recorded as blocked. Three of those four terms
are positive scalars, and scalars do two things: they do not move where a signal crosses zero,
and they cancel out of a proportional response.

| §A.7 output | needs | was it blocked |
|---|---|---|
| trigger price `F* = F_{t-k}` | prices | **no** |
| volatility trigger `dq/q = 1 - sigma_0/sigma_1` | sigma | **no**, unit elasticity |
| forced flow `Q*` | `A`, **or an observed position** | not once COT is available |

The third row is the substantive one, and `trigger.py` acts on it: **the replication model
exists to estimate other people's positions, and COT reports them weekly.** An observed
Managed Money net multiplied by a proportional response needs no capital estimate at all.
That module's docstring makes the argument; this section records it against the table so the
row stops saying otherwise.

**Genuinely still absent:** module spec §9.2's *first* calibration target, a regression of
modelled returns on SG Trend or BTOP50 at an R2 of 0.6-0.8. Declared, not approximated. Target
2, reproducing the observed Managed Money panel, is available.

**Genuinely still hard, and not a data problem:** the trend-following fraction of Managed
Money. Spec §11.2 says the category blends CTAs, discretionary macro and risk parity, so a
trend response applied to the whole of it is an upper bound. Estimating the fraction is fitted,
therefore a search, therefore a `SearchSpaceLog` under npf governance.

**This is the fourth "blocked on" row in that table to prove stale**, after volume
([2026-08-01 §A13](amendments-2026-08-01.md)), extremity, and A.10's returns. Three of the four
were re-testable in under an hour. A blocker recorded once is rarely re-tested, and that has
now cost this project more time than any defect in the code has.

---

## B9. The trigger guard is about DISTANCE, not sign, and the numbers are three orders apart

**Adds** a measurement behind `trigger_prices`'s refusal of anything but `propadj`. The guard
is right; its stated reason ("backadj levels are not prices") is true but does not say how much
it matters, and every other refusal in this package carries a number.

| | `backadj` against `propadj` |
|---|---|
| agreement on the momentum SIGN | **99.4%** (min 97.1%, NG at 250 days) |
| disagreement on trigger DISTANCE, p95 at 250 days | cocoa **420pp**, milk 397pp, soybeans 336pp, crude 93pp, gold 31pp |

A module that only needed a direction could read either series. The trigger's useful output is
a distance from spot, a ratio of price levels, and additive back-adjustment inflates historical
levels. **Fourth appearance of this same failure**, after notional's price levels, riskunits'
percentage returns and impact's dollar volume.

**A note on §A.7's "solve `s(F*) = 0` numerically".** For an odd, equally weighted sign blend
it does not need solving: `s` steps by `2/n` at each `F_{t-k}` and crosses zero exactly at
their **median**. Recorded as documentation rather than built, because `trigger.py`
deliberately reports each horizon separately and the universe justifies that choice: measured
on the latest week, several markets have lookbacks pointing different ways at once, and gold's
20- and 60-day signals are short and flip up while its 250-day is long and flips down. A
blended trigger would average that away.

**One defect this measurement chased, in a module that has since been discarded.** A first,
duplicate implementation of this block computed `prices.iloc[-k]` where the signal compares
against `prices.shift(k)`, whose last value is `prices.iloc[-1 - k]`. One bar adrift. Both
outputs stayed individually plausible and the pair became inconsistent: soybeans reported a
signal of +0.33, meaning spot above the median lookback price, alongside a trigger 0.7%
**above** spot. `trigger.py` uses `iloc[-1 - k]` and is correct;
`test_the_flip_side_agrees_with_the_signal_it_derives_from` now pins it on 50-odd
lookback-market pairs so it cannot regress silently.

---

> **B10 onward were measured on 2026-08-02**, not 08-01 like B1-B9 above, against
> `COTDATA_STORE=~/code/cotdata_store`. They exist because writing §4, §5 and §7 of
> [the validation pre-registration](../handoffs/2026-08-02-validation-prereg.md) required
> measuring three things both sessions had been asserting.

---

## B10. The vintage store holds ZERO point-in-time observations, not one episode's worth

**Contradicts:** both sessions, independently, and the first draft of the pre-registration's
§4. Reproducer: `docs/analysis/reproduce.py` section 13.

Both sessions measured that vintage report dates span 2025-01-07 to 2026-07-28 and concluded
that **gold 2025 is point-in-time while the earlier episodes are not**. The span is right. The
conclusion does not follow from it.

| | measured |
|---|---|
| observations | 224,280 |
| distinct keys | 224,280 |
| **keys observed more than once** | **0** |
| capture timestamps | 2026-07-31 and 2026-08-01 only |

A report date records when the **CFTC measured a position**, not when this store first saw the
value. All 82 report weeks were backfilled from current state this week, after every revision
they have ever received. There is no as-published value for any week in the store, gold 2025
included. Point-in-time coverage is **0 of 6** episodes, not 1 of 6.

**The consequence that would otherwise be found by an evaluator, downstream, as a pass.**
Module spec §10 asks that "vintage replay reproduces historical values exactly". With one
observation per key an as-of replay at any date returns the same values **by construction**,
so that test cannot fail. A test that cannot fail has not passed. It becomes executable once
the store has sat through a revision, which needs releases after 2026-08-01 to accumulate.

**And the release-date index, which is the whole reason `VintageCotSource` refuses report
dates, is currently mostly a guess:**

| release-date provenance | report weeks |
|---|---|
| `derived` (`report_date + 3d`, weekend-adjusted) | 51 |
| `scheduled` (published calendar, not observed) | 29 |
| `published` (observed) | **2** |

cotdata's own `vintage_schedule` docstring says consumers "must be able to exclude `derived`
rows from strict PIT evaluation". Under that strict reading the usable panel is **2 weeks of
82**. This compounds the earlier shutdown finding rather than restating it: the Oct-Nov 2025
shutdown was recorded as leaving that window `derived`, and `derived` in fact covers
everything through November 2025.

**Nothing here is a defect in cotdata.** `cot_vintage.md` §5.3 records that a store started
late cannot reconstruct earlier vintages, and the vintage subsystem is doing exactly what it
says. The error was ours, in reading a report-date range as a vintage range.

---

## B11. `kappa` cannot move `D`, for the same reason `gamma` cannot, and that was not known

**Adds** to [§B2](#b2), which established that `gamma` cannot reach the composite. The same
argument applies to `kappa` and had not been made. Reproducer: `reproduce.py` section 14.

`T = Q / (kappa . V)` with a single global `kappa`, and `I = pct(T)` taken **within a market**.
A percentile is invariant under any monotonic transform, and multiplying by a positive constant
is one, so `kappa` cancels exactly.

| `kappa` | max change in `I` |
|---|---|
| 0.2 -> 0.05 | **0.00e+00** |
| 0.2 -> 0.4 | **0.00e+00** |
| 0.2 -> 1.0 | **0.00e+00** |

27,194 market-weeks, 27 markets. Not "small". Bit-identical, at a fourfold cut and a fivefold
rise.

`Y` does not reach `D` either, for a different and simpler reason: it never enters
`add_composite` at all. The square-root law feeds the exit **cost** and `D`'s `I` term is the
exit **duration**, which `2026-08-01 §A19` established are orthogonal.

**So all three configured constants are invariant for `D`.** The three that are always cited
as this system's judgement calls (`kappa` 0.2, `Y` 0.75, `gamma` 0.5, none of them fitted, one
of them with no sanctioned range anywhere) **cannot change its headline output by any amount.**

The warning worth carrying: this system percentile-ises within a market at three separate
points, and a percentile eats any global positive scalar. A reader who does not notice will
read a sensitivity null as a robustness result when it is an algebraic identity. What actually
moves `D` is the fragility weight **ordering** (`2026-08-01 §A22`, inverted: 0 of the top 10
survive) and the `phi_percentile` reading (`§A15`, which flips a conclusion).

---

## B12. Two of the four uncontaminated validation episodes are on TFF, which nobody has scored

**Adds** the panel-reach measurement behind pre-registration §7.2. Nothing here contradicts a
doc; it establishes something that was simply unknown when the clean set was named.

The pre-registration's §2 lists Feb 2018, Aug 2024, silver 2021 and gold 2025 as never examined
by either session. Whether they are **reachable** is a separate question and was not checked.

| episode | needs | in the Disaggregated panel? | in TFF? |
|---|---|---|---|
| Feb 2018 vol unwind | equity index | no | **yes**: ES, NQ, RTY, YM, EMD |
| Aug 2024 yen carry | JPY | no | **yes**: 6J, NKD |
| silver 2021 | SI | yes | n/a |
| gold 2025 | GC | yes | n/a |

The scored panel is **27 Disaggregated commodity markets**, and it holds no equity index, no FX
and no rates, so half the clean set is out of its reach.

**TFF reaches back as far as Disaggregated does, which the existing TFF analysis does not say.**
[`2026-07-28-tff-financial-futures.md`](../analysis/2026-07-28-tff-financial-futures.md) reports
"111 over the panel (2025-01-07 onward)", which is the **vintage** panel. Measured against the
current store, `from_current_store(report_type="tff")` returns **110,915 rows over 24 markets
from 2006-06-13**, the same start date as Disaggregated. That is not a correction to the TFF
document, which was reporting the vintage universe it was written about, but it is a fact that
document does not carry and that the clean set depends on.

**Inputs verified present, end-to-end run not verified.** 22 of the 24 TFF markets carry a
`ContractMaster` symbol (the two misses are the NYSE Liffe MSCI minis). All 21 checked have
`unadj` and `propadj` prices with volume, starting between 1979 and 2021, comfortably before
`D`'s 2010-05-25 floor. **`add_composite` has never been run on TFF** and this session
deliberately did not run it: scoring TFF is the first thing the §7 evaluator does, and doing it
here would have contaminated two of the four clean episodes to save them one command.

That is also the reason the pre-registration carries a deadline in its closing question. **The
first session to score TFF for any purpose spends that cleanliness**, and it is currently the
larger half of the only uncontaminated evidence this project has.

---

## B13. `l.g` grows as the square root of the pool, not linearly, and the linear reading invented a blow-up

**Contradicts:** the §A.8 view as supplied, this file's own first draft of it, and a figure one
session sent the other. Reproducer: `docs/analysis/reproduce.py` section 15.

`l` is a secant on §A.5's square-root law, not a constant of the market:

    l = I(Q)/Q = Y . sigma . sqrt(Q/V) / Q  =  Y . sigma / sqrt(Q.V)      so  l ~ Q^-1/2
    g = Q/d                                                               so  g ~ Q
    l.g ~ sqrt(Q) / d

Measured: tripling the pool multiplies `l.g` by **1.7321**, which is `sqrt(3)` to four figures.

The written-down version said "`P` scales `l.g` linearly". Under that reading gold's
whole-gross case came out at `l.g = 1.231`, past 1, and was reported as **"no equilibrium"**.

| gold reading | linear (wrong) | computed |
|---|---|---|
| 60d, pool = \|net\| | 0.058 | 0.049, 1.05x |
| 20d cohort under the constraint | 0.410 | 0.347, 1.53x |
| whole 3x gross pool at near distance | **1.231, no equilibrium** | **0.602, 2.51x** |

**Nothing at gold crosses 1.** The cohort constraint still moves the headline by 64%, which is
worth having, but the claim that getting it wrong produces a divergent cascade was an artifact
of the linear assumption.

Same correction to the trend fraction `f` (B8): the overstatement from attributing the whole
net to trend cohorts is `1/sqrt(f)`, not `1/f`. At `f = 0.5` gold goes `0.602 -> 0.426` and
2.51x -> 1.74x. **Milder than either session said**, in both directions.

Worth naming the failure mode rather than only the number: an error that makes a risk measure
look MORE alarming is the kind nobody double-checks. It survived being written into a handoff,
a cross-session message and a module docstring before anyone computed it.

---

## B14. Which cascade step is worst is a race, and both written-down answers were wrong

**Contradicts:** the §A.8 view (point 3) and the correction to it, which reached the right
conclusion for GC and CL from a false premise. Reproducer: section 15.

Two answers preceded the right one.

1. **"Amplification grows as the move extends"**, because only the fastest slice of the pool is
   in play near the first trigger. That counts only the numerator of a ratio.
2. **"The nearest step is always the worst"**, because trigger distances grow faster than the
   pool accumulates. **The premise is false.** Trigger distance is not monotonic in lookback:

| | 20d | 60d | 250d |
|---|---|---|---|
| GC | **1.94%** | 13.71% | 13.44% |
| ZC | 4.03% | 11.14% | **3.70%** |
| CL | 19.60% | **13.86%** | 29.51% |

ZC's 250-day trigger is its nearest and CL's 60-day is. A 20/60/250 ladder does not sit
progressively further out, so the staircase must be sorted by distance rather than horizon.

**The exact condition.** Since `l.g ~ sqrt(Q_cum)/d`, step `i` beats step `i+1` iff

    d_(i+1) / d_i  >  sqrt( Q_(i+1) / Q_i )

which under a uniform split is **1.414** at the first gap and **1.225** at the second. The
nearer step wins only when the next trigger is more than 41% further out.

**Measured within-direction across 33 markets: 6 of the 33 multi-step staircases peak PAST
their nearest step.** 6E holds two up-triggers at a distance ratio of 1.005, far inside 1.414.
So the headline is `max` over steps, not the nearest, and `headline` computes it.

**The race is only ever run within a direction.** Pooling `up` and `down` into one
distance-sorted ladder manufactures counterexamples that are artifacts of the pooling, because
adjacent steps then belong to different cascades. ZC reads as a middle-step market exactly that
way: its three steps sorted by distance are 250d-up, 20d-down, 60d-up, and it is monotone once
separated. That mistake was made and caught during this work, which is why it is a test.

A note on quoting: WHICH step wins is independent of the pool size, because
`lg_2/lg_1 = sqrt(2) . d_1/d_2` and the net cancels. That is what makes the 6-of-33 count
quotable without a real position per market. The amplification LEVELS are not net-independent,
and an earlier draft quoted 6E levels computed against a placeholder net from a universe scan.
Removed.

---

## B15. `sum(s) == 0` is reachable without touching the config, so the parity argument does not hold

**Contradicts:** the claim that an odd lookback count structurally bars the zero-sum case.
Reproducer: section 15.

The measurement behind that claim stands: across 45 markets in the latest week the distribution
of `sum(s)` is `{-3: 7, -1: 17, +1: 15, +3: 6}`, with no zeros. The inference does not.

**Parity protects the count of CONTRIBUTING signals, not the length of `DEFAULT_LOOKBACKS`**,
and two ordinary things reduce that count:

- a **flat** lookback returns `signal = 0`, holds `w.P.s = 0` and contributes nothing
- a lookback **longer than the price history** returns null

Either leaves two contributing signals, and `(-1, +1)` sums to zero, making the implied gross
pool infinite. A market with under 250 days of history reaches this with no configuration
change at all. **Both cases arose by accident while writing the tests**, which is the evidence
that they are ordinary rather than adversarial.

So the sweep's clean result is a fact about 45 mature markets in one week, not a theorem, and
the guard is load-bearing rather than defensive.

**A live bug fell out of the same fact.** `trigger.format_block` tested `signal > 0` and sent
everything else to "short, flips up", so a flat lookback rendered as a short whose trigger sits
0.0% away, which reads as the most urgent row in a block when it is not a trigger at all. Its
flip price is spot itself. Fixed, with a test.

---

## B16. Roll congestion is not blocked, and `roll_dates` returns empty rather than raising on a wrong argument

**Contradicts:** the reading that §13 step 4 is blocked in full, and my own first pass at
measuring it. Reproducer: `docs/analysis/reproduce.py` section 16.

§13 step 4 is "DTL, impact, limit-move and roll constraints", and it was read as one blocked
item because a per-expiry price source does not exist in the workspace (workspace CLAUDE.md,
ADR-0007). **Step 4 is two constraints with different answers.**

| item | data it needs | status |
|---|---|---|
| **limit moves** | a daily price limit table | **blocked.** No such table in `cotdata` or `marketdata` |
| **roll congestion** | roll timing | **not blocked.** `cotdata.roll_dates(symbol)` |

### Coverage, measured

| | |
|---|---|
| symbols in the registry | 49 |
| **non-empty `roll_dates`** | **47** |
| empty | 2 |
| errors | 0 |
| rolls per symbol | min 25, median 188, max 574 |
| span | first roll 1977-11-21, last 2026-07-31 |

The deepest are HO at 574 rolls, CL at 520 and NG at 436. **The two empties are not a gap**:
`MME` and `MFS` carry `norgate=None` and are sourced from Yahoo as `EEM` and `EFA`. They are
equity ETF proxies, so there is no Delivery Month to change and no roll to date. Every
instrument that is actually a futures contract has roll dates.

### What that unblocks, and what it does not

A full roll-congestion decomposition wants open interest split front against back, which needs
the per-expiry source that genuinely does not exist. **The useful question does not need it.**
`pressure.T` already gives days for the forced side to leave and `roll_dates` gives the days
the whole market has to move anyway, so whether an exit window collides with a roll is
answerable from two things already in the package.

### The trap: a wrong argument type is silent

`roll_dates(symbol: str)` returns an **empty `DatetimeIndex`** rather than raising when handed
something that is not a symbol string. `cotdata.all_symbols()` returns `Symbol` namedtuples,
not strings, so the obvious one-liner

    [len(cotdata.roll_dates(s)) for s in cotdata.all_symbols()]     # 0 for all 49

reports **zero coverage across the entire universe** and reads exactly like "this data does not
exist". That is how this measurement went wrong on its first pass, immediately after a
33-symbol hand-written list had returned 33 of 33. Two runs, same store, same function, 0% and
100%.

The docstring's stated empty case ("the producer did not carry Delivery Month") is real and
accounts for `MME` and `MFS`. It is indistinguishable from the wrong-type case, which is what
makes the failure quiet. **Pass `s.internal`, and treat a universe-wide zero as a bug in the
call before believing it about the data.**

The field is `internal`, not `symbol`, which makes this a ladder rather than one step:

| what you pass | what happens |
|---|---|
| the `Symbol` namedtuple | **silent, 0 rolls** |
| `s.symbol` | loud `AttributeError` |
| `s.internal` | correct |

The call anyone writes first is the silent one, and the obvious correction to it is the loud
one, so a session that hits the trap and then guesses is rescued by accident rather than by
understanding. That changes what "I tried unwrapping it" is worth as evidence.

### The `adjustment` argument is the one place a default series is safe

`roll_dates(symbol, adjustment="backadj")` inherits a series the way three other call sites in
this package must not. Measured across the registry:

| | |
|---|---|
| identical across `backadj` / `unadj` / `propadj` | **47 of 47** |
| differing | **0** |

**The reason matters more than the count.** Roll dates come from the Delivery Month column
changing, which is a property of the contract calendar. Price adjustment rescales bars; it does
not move a delivery month. So the default is harmless here by construction rather than by luck.

Recorded precisely **because it is the exception.** Four separate failures in this package have
been the wrong series (notional's levels, riskunits' returns, impact's dollar volume, trigger's
distance), so "check the series" is now the standing instinct and a session taking roll
congestion would otherwise spend real effort re-deriving this. The safety is **conditional**:
it holds while rolls are derived from Delivery Month, and would stop holding the day an
implementation inferred them from price gaps instead.

---

## B17. What the frozen validation found about this package, verified rather than accepted

**Source:** the §10 verdict, executed 2026-08-01 in `npf` by a session that wrote none of this
package. Verdict `uninformative`, which §7.5 named in advance as the most likely outcome and
recorded in advance as not a failure of the measure. Outcome appended at
[`2026-08-02-validation-prereg.md` §9](../handoffs/2026-08-02-validation-prereg.md).

Three of the four findings are about crowdmon rather than about the test, so they belong here
where a builder will meet them.

### The documented floor is right about `D` and wrong about anything read off `D`

`2026-08-01 §A16` and the README say **the composite scores nothing before 2010-05-25**,
because `C = pct(z)` stacks two three-year windows. That is correct **for `D` itself** and it
is what the sentence says.

It is not the number a consumer needs. §7.4 read `pct(D)`, which stacks a **third** rolling
window, and that starts **2012-05-15**. Verified here rather than taken:

    2010-05-25 + 103 weekly observations = 2012-05-15      (the 104th, min_periods=104)

exactly the evaluator's date. **Two further years are lost by anything taking a percentile of
`D`**, which is the natural thing to do with it and which the composite's own `phi_percentile`
reading already does one level down.

So the floor is not one date, it is a property of which quantity you read, and only the
innermost one is documented. A reader planning coverage from the published figure over-counts
by two years for the most likely use.

### Lumber produces no `D` in any week, in either contract code, and nothing says so

Module spec §10's own replay list names the 2021 ags/lumber episode. **The episode ran on five
markets with no lumber in it**, because neither code can be scored:

| code | why not |
|---|---|
| `058643` | notional in 37 of 880 weeks. No usable price series |
| `058644` | complete data, but 75 weeks of `z` against the 104-week minimum |

**The gap is in coverage reporting, not in the data.** `coverage_report` and
`risk_coverage_report` answer "no price" and "no volatility" per market, and neither surfaces
"scoreable weeks after every window is stacked", which is the question that decides whether a
market can appear in a result at all. A market on the spec's own replay list fell out silently
and was caught only because an evaluator counted units.

Reproduced on the real panel: **2 of 27 codes score zero weeks, 7.4%, and they are exactly the
two lumber codes.** The next lowest are oats at 555 weeks and the two wheats at 742, so there
is no near-miss band. It is zero or it is hundreds.

**The two fail at different rungs, and that is what the fix has to report.** `058643` dies at
the price join, 24 usable weeks of 880. `058644` has a complete `dtl_sell` in **every one** of
its 178 weeks and still scores nothing, dying at the extremity window with 75 weeks of `z`
against the 104 required. So "scoreable weeks" is necessary and not sufficient: a maintainer
looking at `058644` would see full exit-capacity coverage against no output and have nowhere
to start. **The report must name the rung that dropped the market.**

**Key it on `market_code`, never on `market_name`.** Grouping by `(code, name)` while checking
the above manufactured four phantom unscoreable markets: cotton, cocoa, sugar and coffee each
showed a 64-week block scoring zero, which is simply their pre-migration name. **11 of 27 codes
carry more than one `market_name`**, and `033661` is literally
`COTTON NO. 2 - NEW YORK BOARD OF TRADE` becoming `COTTON NO. 2 - ICE FUTURES U.S.`, while
`022651` carries five spellings of heating oil. All four of those codes score 845 weeks under a
code-level key. A name-keyed coverage report would invent unscoreable markets in the same panel
where it is supposed to find the real ones, and this is the same venue-migration fact that
finding 3 records for RTY.

Worth fixing before roll congestion or PCA, since both will hit the same blind spot: a market
that is present in every input and absent from every output.

### RTY resolves to the retiring venue in Feb 2018

`23977A` (ICE) against `239742` (CME). The CME code reported 18 weeks in the Feb 2018 window
but has **zero scored weeks**, because it restarts in Aug 2017 and `pct(D)` needs roughly five
years. So the unit was measured on the contract that was losing the listing, with a reference
series of 163 weeks against 444 for its peers.

The evaluator fixed the resolution rule before reading any value of `D`, using only scored-week
count and open interest, which is the right order. **For this package the point is that
`hist_codes` migrations are invisible downstream**: nothing in the panel says a market changed
venue mid-history, and the shorter series simply looks like a younger market.

### Not a crowdmon finding, recorded so it is not re-derived

§7.5's `contradicted` branch is an OR while `supported` is an AND, so they are not complements
and a run can improve its pooled statistic into a `contradicted` classification. It did not
affect the verdict. It lives in the frozen §7 and must not be edited there; it is a note for
whoever next writes a criterion of that shape.

### The result itself

Pooled statistic 0.5473 against a null mean of 0.4990, raw p 0.3121, 5 of 9 units above 0.50
where 6 were needed. **`D` leans very slightly hot before the four clean episodes and random
data produces that lean about a third of the time.** Nothing says `D` works, nothing says it
does not, and the clean episodes are now spent. The plumbing came back clean: §2's full table
reproduced on both `phi` readings and all three windows, and `add_composite` ran on TFF end to
end on the first attempt with 21 of 24 markets scored.

---

## B18. Both lumber codes fail at the SAME rung, so naming the rung is not enough

**Contradicts:** [`§B17`](#b17-what-the-frozen-validation-found-about-this-package-verified-rather-than-accepted)
above, written by this session, which said the two codes "fail at different rungs, and that is
what the fix has to report". They fail at the same one. Reproducer:
`docs/analysis/reproduce_composite.py` pipeline, non-null counts per rung.

Measured ladder, both codes:

| rung | `058643` (880 wk) | `058644` (178 wk) |
|---|---|---|
| `fragility` (price-free) | **777** | 75 |
| `adv` / `dtl_sell` | 24 | **178** |
| `illiquidity_sell` = `pct(T)` | 0 | 75 |
| `crowding_long` = `pct(z)` | **0** | **0** |
| `damage_sell` | 0 | 0 |

**Both terminate at `crowding_long`, and the root causes are different:**

- `058643` has price coverage collapse to 24 weeks of 880, so `z` can never fill a
  standardisation window. The *first zero* is two rungs after the rung that caused it.
- `058644` has complete `dtl_sell` in all 178 weeks and dies on history length: 75 weeks of
  `z` against the 104 required.

So B17's framing was wrong in a way that would have weakened the fix. The truer statement is
the stronger argument for what shipped in `coverage`: **a label naming the terminal rung is
insufficient precisely because both markets carry the same label for unrelated reasons.**
Printing the full ladder beside it is what distinguishes them, and the other session's
`drops_at` docstring says so.

**The ladder is not monotonic, which is the detail that makes it readable.** `058643` carries
**777** weeks of `fragility` against **24** of `dtl_sell`. Fragility is price-free (§A.2 needs
only columns the canonical schema already has), so a market can be richly covered at one rung
and nearly absent at the next. A reader who assumes coverage decreases down the ladder will
mis-locate every failure of this shape.

**Neither session predicted this correctly.** B17 guessed two different rungs; the coverage
handoff guessed `058643` drops at the price join. It drops at `extremity_z`. The measurement
disagreed with both, which is the fourth time in this file that a rung-level assumption has not
survived being counted.

---

## B19. Spec §379's roll congestion is blocked in full, and the roll-day ratio is not the bias in `T`

**Contradicts:** [`§B16`](#b16-roll-congestion-is-not-blocked-and-roll_dates-returns-empty-rather-than-raising-on-a-wrong-argument)
above, written by this session, which concluded roll congestion "is not blocked" from
`roll_dates` existing. Reproducer: `docs/analysis/reproduce.py` section 17.

### All three components of §379 are blocked

§379 defines roll congestion as "calendar spread volatility and bid-ask behaviour during roll
windows, plus OI migration rate front to next".

| component | needs | status |
|---|---|---|
| calendar spread volatility | two contract prices at once | blocked, no per-expiry source |
| bid-ask behaviour | quote data | blocked, nothing carries quotes |
| **OI migration front to next** | per-expiry open interest | **blocked, and this was not known** |

The third looks available. `cotdata.get_prices` returns an `Open Interest` column reading
exactly like the front-contract figure a migration rate needs. Measured against COT's
whole-market total, 1,051 weeks per market: **mean ratio 1.000 for GC, SI, CL, ZC, NG, ZS, ZW
and HG**, p5 no lower than 0.998. It is the same number COT reports.

**Two columns on one frame both look per-contract and neither is.** `volume.py` documents that
`front` is whole-market despite its name; `Open Interest` is not even named `front` and is
also whole-market.

B16 conflated roll *timing*, which is available, with roll *congestion*, which is not. That is
the same error this session had warned the other about for PCA a few hours earlier: **the
nearest reachable object is not the one the spec names.**

### The buildable part, and the figure that must not be quoted

Roll-window volume runs a median **1.239x** baseline across 16 markets. **That is a fact about
roll days and it is not the bias in `T`.** `pressure.T = Q/(kappa.V)` uses a trailing mean, so
the effect is diluted by how few days those are:

| | median of 16 |
|---|---|
| roll-day volume ratio | 1.239x |
| share of bars inside a window | 21.8% |
| **ADV inflation** | **1.0506x** |
| **`T` optimistic by** | **5.1%** |

**An order of magnitude apart.** An earlier version of this finding quoted 1.57x as the effect
on `T`. The other session, which owns `pressure`, caught it and independently measured 5.6%
against the 5.06% here; the residual is window definition, 10 bars against 10 calendar days.

### The two measures disagree in sign, so neither substitutes for the other

`T` is **pessimistic**, not optimistic, for **SI, NG, HO, RB and LE**, five of sixteen. So
"optimistic by construction for every market" is false, and it is false for the
refined-products complex a fuel-shock scenario cares most about.

Worse, the ratio does not predict even the sign. **SI has a roll-day ratio of 1.244 and an ADV
inflation of 0.983**: more volume on roll days by median, less by mean, because the days
outside the window carry the fatter tail. NG does the same.

**Which markets diverge depends on the lookback.** An earlier draft named HO, which diverges
over full history and does not over four years. `reproduce.py` now selects the divergent set
from the data rather than naming any market.

### A roll-excluded ADV is a different estimator

CL, NG, HO and RB roll monthly, so **52-53% of their bars sit inside a 10-bar window**.
Excluding them computes crude's ADV on half the sample. `roll.py` reports the excluded share
beside every figure, admits the monthly rollers with a flag, and refuses only below a 25%
survival floor.

**Nothing changes `pressure`'s ADV.** Moving `T` moves `I`, moves `D`, and moves the §9
verdict's inputs. On these numbers the case for changing it is weak: 5.1% median, wrong-signed
for five of sixteen, and a half-sample estimator for the energy complex. Both sessions agree
it is a human's call and not a module's.

---

## B20. The alignment score cannot reach 1, and the ceiling moves enough that the raw figure is not comparable across weeks

**Amends:** module spec §368, which says to "correlate the cross-market positioning vector
against a canonical time-series momentum vector" and gives no reading for the result.
Reproducer: `docs/analysis/reproduce.py` section 18.

### The blend is coarse by construction, and that bounds the correlation

The canonical TSMOM blend is an equal-weight sign average over 20/60/250, so it takes at most
**four** values, `{-1, -1/3, +1/3, +1}`. Across a 25-market panel it is therefore massively
tied, and a rank correlation against a heavily tied vector cannot reach 1.

Measured over all 1,051 panel weeks:

| | mean | p5 | median | p95 | min | max |
|---|---|---|---|---|---|---|
| `alignment` | 0.433 | 0.100 | 0.446 | 0.732 | -0.257 | 0.879 |
| **`alignment_ceiling`** | **0.931** | 0.852 | 0.945 | 0.966 | **0.340** | 0.969 |
| `alignment_vs_ceiling` | 0.463 | 0.113 | 0.477 | 0.781 | -0.583 | 0.932 |

**The ceiling is not a constant to memorise: it runs 0.340 to 0.969.** A week scoring 0.30
against a ceiling of 0.34 is a book almost perfectly expressed; the same 0.30 against a ceiling
of 0.97 is a book that is not. **The raw figure alone cannot tell those apart, and it is what
§368 asks for.** `alignment_vs_ceiling` is the comparable number and `alignment_series` returns
all three.

### The momentum vector is weak for two markets in three

Mean `momentum_strength` (mean `|blend|`) is **0.660** against a maximum of 1, and in the latest
week **68% of markets have horizons disagreeing**. That is `2026-08-02 §B14` from the other
direction: the blend is `sum(s)/3`, so the 69.7% mixed-direction figure and the ±1/3 share are
one fact seen twice.

Consequence: a low alignment score has two causes that look identical. The book may be
uncommitted, or the momentum vector it is measured against may point nowhere. `momentum_strength`
and `share_undecided` are returned so the reader can separate them.

### No warm-up, which makes it the earliest engine here

| engine | first scored | warm-up from the 2006-06-13 panel start |
|---|---|---|
| **trend alignment** | **2006-06-13** | **none** |
| macro-book PCA (differenced) | 2006-06-20 | one week |
| `damage_sell` | 2010-05-25 | 3.9 years |
| `damage_sell_pct` | 2012-05-15 | 5.9 years |

The score is cross-sectional within a week and stacks no rolling window at all. **So this and
the macro-book PCA are the two engines that can reach 2008**, the last episode nobody in this
package has looked at, clean only because `D` could never reach it. Neither module has been
sliced by a named episode and the module docstring says not to. Any such test gets
pre-registered and specified by a session that did not build it, as §7 was.

### The blend weights matter modestly and are swept, never fitted

| weights | mean alignment | rank correlation to equal |
|---|---|---|
| equal (1/3 each) | 0.4330 | 1.0000 |
| fast (0.6/0.3/0.1) | 0.3777 | 0.9414 |
| slow (0.1/0.3/0.6) | 0.4562 | 0.9475 |

A 21% swing in the mean and a correlation above 0.94 either way. The weights move the level
more than the ordering, which is the same shape `2026-08-01 §A22` found for the fragility
weights. §368 gives no weights, so equal is a **stated prior**, reported by `blend_sensitivity`
rather than assumed away.

### A guard that punished the behaviour it existed to encourage

`test_no_module_in_the_package_imports_scipy` scanned source files for the **substring**
`scipy` and allowlisted one filename. `alignment.py` explains in its docstring why it computes
Pearson-on-ranks instead of calling scipy, which is exactly what the guard wants modules to do,
and the guard failed on it.

The cheap way to make that pass is to delete the explanation. **Rewritten to parse imports with
`ast`**, so it catches a real `import scipy` and ignores prose, with a second test asserting the
parse would catch a genuine import rather than trivially returning an empty list.
## B21. PC1 is the grain complex on Disaggregated, and only the macro book on TFF

**Contradicts** module spec §7's "PC1 approximates the aggregate systematic book", which is
true of one panel and false of the other. Reproducer: `docs/analysis/reproduce.py` section 18.
Measured while building `futures/macro_pca.py`.

| panel | absorption | shuffled null | what PC1 actually is |
|---|---|---|---|
| Disaggregated | **0.143** | 0.054 | ZS +0.35, ZC +0.30, ZL +0.30, KE +0.27, ZM +0.26, SI +0.25 |
| TFF | **0.128** | 0.077 | YM +0.37, 6A +0.36, ES +0.36, NQ +0.35, 6S +0.29, **DX -0.26** |

Both are 947 weeks from 2008-06-10, on 24 and 16 markets.

TFF's first component is risk appetite in textbook form: long the equity indices, long the
commodity currency, **short the dollar**. That is the aggregate systematic book §7 describes.
Disaggregated's is the grain trade, and five of its top six are the soy/corn/wheat complex.

**This is the same shape as [2026-08-01 §A14](amendments-2026-08-01.md)**, where 76% of the
Disaggregated universe turned out to be ICE Energy and Nodal power so a "cross-market" result
over it was mostly about ERCOT and PJM. A cross-market statistic named for something broader
than its universe supports describes the universe, not the name. **The report type is not a
parameter to this engine, it is the subject.**

**And absorption is comparable to its own null, never across panels.** TFF's null is 0.077
against Disaggregated's 0.054 purely because a variance share is floored at `1/n` and TFF is
narrower. Read raw, TFF looks less crowded; against its null the gap is smaller but the
ranking claim was never available.

---

## B22. 95.7% cell coverage, zero complete weeks, and a delisting that costs two years

**Adds** the measurements behind `macro_pca.select_markets`. Nothing here contradicts a doc;
it establishes why the selection step exists at all.

| | |
|---|---|
| Disaggregated panel | 948 weeks x 26 markets |
| cells present | **95.5%** |
| **weeks with no missing market** | **0** |

The holes are spread across markets rather than concentrated in weeks, so a coverage figure
that reads as nearly complete yields an empty rectangle and a naive listwise PCA returns
nothing at all.

| markets kept | complete weeks | span ends |
|---|---|---|
| 26 | **0** | n/a |
| 25 | 746 | **2023-12-26** |
| **24** | **947** | 2026-07-28 |
| 22 | 947 | same |

**Dropping two markets buys the whole panel; dropping one fewer costs two and a half years**,
because the 25th delists and truncates everything to it. Selection is derived from the
coverage counts rather than hand-picked, and ties break toward more markets so the rule never
drops one it did not have to.

**The panel starts 2008-06-10 and `D` starts 2010-05-25.** `C = pct(z)` stacks two three-year
windows ([2026-08-01 §A16](amendments-2026-08-01.md)); this needs one. So the absorption ratio
reaches the 2008 crisis, and it is the only engine in the package whose history covers a
genuine systemic unwind. **No episode in it has been examined by its author**, deliberately:
pointing this at 2008 is exactly the after-the-fact window-picking the §10 pre-registration
exists to prevent, and it belongs in a pre-registration written by someone else.

---

## B23. An eigenvector's sign is not identified, and a signed cosine reports the flip as news

**Records a defect this module shipped with for one run**, caught by measuring rather than by
a test, and the reason `loading_rotation` uses `1 - |cos|` rather than `1 - cos`.

PC1 and -PC1 describe the same axis and the same book, so a sign convention is a presentation
choice and nothing more. `_pin_sign` pins the loadings to sum positive, and **that sum passes
through zero on real data whether or not anything about the book changes.**

Measured on the 24-market panel, 843 rolling readings:

| | signed cosine | `1 - abs(cos)` |
|---|---|---|
| readings above 1.0 | **8** | **0** |
| median | 0.0004 | 0.0004 |
| p95 | 0.0093 | 0.0079 |
| max | **1.9984** | 0.0916 |

The eight were 2018-05-08, 2018-06-05, 2019-10-29 and five consecutive weeks across
2020-06-30 to 2020-09-01, each reading ~1.99 against a median of 0.0004, **200x the p95 and
every one an artifact**. Under the absolute value they read ~0.002, which is what they always
were.

The general rule worth carrying: **anything derived from an eigenvector must be invariant to
its sign, or it is reporting `numpy` rather than the data.** The same applies to any future
loading-similarity, clustering or alignment measure built on top of this panel.
