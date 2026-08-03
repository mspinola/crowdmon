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

## B22. The z-scored panel costs the entire 2008 window and buys nothing

**Corrects a claim this module shipped with**, and the correction is the module's whole point.

`macro_pca` first defaulted to §7's literal "matrix of z-scored positioning", differencing
`net_risk_usd_z`. The differenced panel started 2008-06-10, and that was reported as reaching
the 2008 unwind where `D` cannot.

**The panel is not the claim.** `rolling_absorption` stacks `min_periods` on top of it, so the
point-in-time series, the only form anyone would use, began **2010-06-01, one week after `D`'s
2010-05-25 floor.** The descriptive whole-panel figure reached 2008; the usable one did not.

| input | panel starts | **rolling starts** |
|---|---|---|
| `net_contracts` | 2006-06-20 | **2008-06-10** |
| `net_risk_usd_z` | 2008-06-10 | **2010-06-01** |

**And the z-scoring buys nothing**, because `absorption_ratio` standardises columns inside
every window, so a pre-standardised panel is redundant work. Over the 844 overlapping weeks:

| | |
|---|---|
| correlation of the two rolling series | **0.9607** |
| mean absolute difference | **0.0086** |
| means | 0.153 against 0.152 |
| weeks the raw panel sees and the z-scored one does not | **103**, 2008-06-10 to 2010-05-25 |

So the default is `net_contracts` and `RISK_PANEL_INPUT` keeps the §7-literal form one
argument away. §5.2's warning that raw contracts load on market size does not apply: a
correlation matrix is scale-free, and §5.2 is about comparing levels across markets, which
this does not do.

**The general shape, which is the third time today:** a warm-up window inherited from an
upstream module silently became the binding constraint on a downstream one. Same as `D`'s two
stacked three-year windows (`2026-08-01 §A16`) and `058644`'s 75 weeks of `z` against a 104
minimum (`§B17`).

---

## B23. High cell coverage, an empty rectangle, and a delisting that costs two years

**Adds** the measurements behind `macro_pca.select_markets`.

| | |
|---|---|
| Disaggregated panel | 1051 weeks x 27 markets |
| cells present | **95.8%** |
| weeks complete across every market | **5** |

The holes are spread across markets rather than concentrated in weeks, so 95.8% coverage
yields **five usable rows in twenty years** and a naive listwise PCA is empty in every sense
that matters. *(An earlier draft of this section said zero, measured on a narrower z-scored
panel. The other session measured 5 independently and was right; the assertion is now written
as a rate rather than a pinned number.)*

| markets kept | complete weeks | span ends |
|---|---|---|
| 27 | 5 | n/a |
| 25 | 889 | 2026-06-02 |
| **24** | **1050** | 2026-07-28 |
| 22 | 1050 | same |

**Dropping the right markets buys the whole panel; stopping one short costs two years**,
because a delisted market truncates everything to its own last week. Selection is derived from
the coverage counts, and ties break toward more markets so the rule never drops one it did not
have to.

**2008 is the last unspent episode in this package**, and it is unspent precisely because
`C = pct(z)` could never reach it, so no session has ever had the option of looking. That
makes it more valuable than the ones §2 of the pre-registration already declared, not less.
**No episode in this module's history has been examined by its author**, deliberately, and
whoever specifies a 2008 test should be a session that did not build the PCA, for the same
reason neither builder could specify §7.

---

## B24. An eigenvector's sign is not identified, and a signed cosine reports the flip as news

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

---

## B25. §369's thesis holds, its example does not, and the cluster it actually finds is the yen carry

**Amends:** module spec §369. Reproducer: `docs/analysis/reproduce.py` section 19.
44 to 46 markets, `propadj` log returns, 2016 onward.

### The section's own illustration is not in the data

> "Long energy" and "short JPY" can be the same macro trade in a given regime.

| pair | correlation |
|---|---|
| 6J vs CL | **-0.140** |
| 6J vs HO | -0.144 |
| 6J vs RB | -0.106 |
| 6J vs NG | -0.044 |

Essentially nothing, and the wrong sign for the phrasing.

### What is there is the yen with the entire US rates complex

| pair | correlation |
|---|---|
| **6J vs ZF** | **0.540** |
| 6J vs ZN | 0.535 |
| 6J vs ZT | 0.508 |
| 6J vs ZB | 0.464 |
| **6J vs NKD** | **-0.414** |

All four positives exceed the average **within**-class pair (0.410). **At `k = 8` the
clustering puts `{6J, ZB, ZF, ZN, ZT}` in a cluster of their own**, which is §369's thesis
holding exactly and its example failing exactly: the macro trade sector taxonomy hides is carry
funding against duration. That is the Aug 2024 yen carry unwind from the spec's own §443 replay
list, arriving from the price side rather than the positioning side.

The negative 6J/NKD pair is the same trade seen from the funding end and is the strongest
inverse cross-class link in the panel.

Crypto is the other genuine cross-class cluster: ETH against NQ 0.431, ES 0.425, RTY 0.413.

### Sector taxonomy is mostly right, which §369 does not concede

| | mean correlation |
|---|---|
| within an asset class (107 pairs) | **0.410** |
| across asset classes (839 pairs) | **0.077** |

5.3x. So labels are a good first approximation, clustering earns its keep on a minority of
pairs, and the informative output is `cross_class_pairs` rather than the partition. §369 reads
as though the taxonomy actively misled, and on this data it does not.

### The correlation gap does NOT become partition agreement, and an earlier draft said it did

`cluster_sweep`'s first docstring claimed high agreement with the taxonomy was the expected
result, reasoning from 0.410 against 0.077. Measured:

| k | agreement with asset class | largest cluster |
|---|---|---|
| 2 | **0.132** | 45 |
| 4 | 0.350 | 39 |
| 6 | 0.480 | 35 |
| 8 | 0.533 | 33 |
| 10 | **0.802** | 20 |

**Agreement is lowest where the claim predicted it highest.** Average linkage on a correlation
distance produces one large cluster plus singletons, so at small `k` the partition says "nearly
everything together" against a taxonomy that says "mostly apart" and they disagree on almost
every pair. A statement about pair averages does not translate into partition agreement at any
particular `k`. Corrected, with a test asserting the direction rather than a level.

### "In a given regime" overstates the instability

The pairwise correlation structure correlates at **r = 0.857** between 2016-2020 and 2021-2026
across 1,980 pairs; 6J/ZN moves only 0.577 to 0.516. Trailing windows remain right because
detecting change is the point, but heavy membership churn indicates a window that is too short
rather than a regime that turned.

### Two implementation notes worth carrying

**No `scipy`, no `sklearn`**, per the boundary allowlist, so the clustering is hand-written
Lance-Williams in numpy. **Agglomerative rather than k-means for a governance reason**: k-means
needs a random initialisation and `crucible/AGENTS.md` requires randomized procedures to take
an explicit seed and reproduce. Hierarchical on a correlation distance is deterministic.

Determinism needed more than "no RNG". Ties in the distance matrix are broken by position, so
the market order is sorted before use and a test feeds shuffled columns and asserts identical
labels. Separately, `np.fill_diagonal` on a derived DataFrame's `.values` **raises** under
copy-on-write, so the distance matrix is built through numpy rather than by mutating a frame.
## B26. A hole in a code's series is not one finding, it is two, and only one of them is a migration

**Closes** the third §B17 finding, that `hist_codes` migrations are invisible downstream.
Reproducer: `futures/continuity.py` against `COTDATA_STORE` as of 2026-08-02.
**B19 through B25 were taken by the roll-congestion, trend-alignment, macro-PCA and
clustering PRs while this was open, so this is B26.**

### The information was already present and nothing put it together

`ContractMaster` resolves both Russell codes to `RTY` and sets `is_historical_code` correctly
on the ICE one. The gap was never the registry. It was that no reader joins a code's *internal
continuity* to its *siblings*:

| code | venue | weeks | span | longest internal gap |
|---|---|---|---|---|
| `239742` | CME | 587 | 2006-06-13 to 2026-07-28 | **3255 d, 8.9 years**, ending 2017-08-15 |
| `23977A` | ICE | 516 | 2008-07-22 to 2018-06-05 | none |

**The two are complementary, not redundant**, and `23977A` covers `239742`'s hole almost
exactly. Together they are a continuous twenty-year market. Apart, the CME code looks like it
began in 2017, which is why `pct(D)` does not reach it until 2023 and why the
pre-registration's Feb 2018 unit was scored on the **retiring** venue with a 163-week
reference series against 444 for its peers.

Lumber is the clean case for contrast: `058643` hands off to `058644` in 2023 with a two-month
overlap and no holes on either side.

### The measurement that shaped the API, and would have made a naive fix wrong

Over all 51 codes in the two current-state panels, **46 have a longest inter-week gap of 8
days**, which is a holiday shift. The five that do not are two unrelated causes:

| code | longest gap | sibling fills it? | what it is |
|---|---|---|---|
| `239742` RTY | 3255 d | **yes, `23977A`** | a venue migration |
| `004603` oats | 294 d | no | intermittent reporting, and it recurs |
| `240741` NKD | 168 d | no | intermittent reporting, and it recurs |
| `112741` NZD | 28 d | no | one missed month in 2006 |
| `058644` LBR | 21 d | n/a | exactly at the tolerance, not over it |

**So "this code has a hole" is not actionable and a report emitting only that would have
invented migrations for oats and the Nikkei.** `gap_filled_by` is the column that separates a
venue seam from a market that genuinely stopped reporting, and the two are opposite findings:
one means the history exists elsewhere, the other means it does not exist.

Oats and the Nikkei were both checked rather than assumed. Neither is a single outage: oats
returns from holes ending 2024-11-05, 2025-09-09 and 2026-05-19, the Nikkei from 2024-12-10,
2025-04-08, 2025-09-23 and 2026-03-03. **Two of those land in autumn 2025 and neither is the
shutdown**, which `2026-08-01` records as breaking release dates and leaving report dates
intact. These are report-date absences, so they are a different thing that happens to be
nearby.

### What was deliberately not built

**The codes are not stitched.** Concatenating `23977A` onto `239742` yields a continuous `RTY`
and also splices two venues with different tick sizes, different participants and a
contract-size scale, which is a decision with consequences at every rung above it. The seam is
reported; the splice is left to a caller willing to argue for it in the open.

**The tolerance is 21 days and exclusive.** Above 21 and below 28 the store contains nothing,
so the threshold is not cutting a continuum in half. Lumber's single 21-day gap sits exactly
on it and is correctly silent.

---

## B27. `select_markets` drops a migrated market twice, and the merge has to precede the difference

**Extends** [`§B26`](#b26) and `macro_pca.select_markets`. Reproducer: `futures/macro_pca.py`
`merge_migrated_codes`, against `COTDATA_STORE` as of 2026-08-02.

### The interaction neither module could see alone

`select_markets` maximises listwise-complete weeks and receives only a matrix, so it cannot
know that two short columns are one long instrument. `continuity` knows, and is never
consulted. On the Disaggregated panel the two facts compose into a silent loss:

| | markets kept | complete weeks | span | PC1 share |
|---|---|---|---|---|
| as shipped | 24 of 27 | 1050 | 2006-06-20 to 2026-07-28 | 0.1310 |
| `merge_migrations=True` | **25 of 26** | **1050** | same | **0.1262** |

**Lumber's `058643` and `058644` are two of the three exclusions**, and merged the market
rejoins over the *same* 1050 weeks with nothing dropped to make room. The cost of the split
was never coverage. It was that the instrument was invisible.

`PANEL_INPUT` is `net_contracts`, which is price-free, so this is not the same market
`coverage.py` reports as unscoreable. Lumber has **no usable price series and 880 weeks of
perfectly good positioning**, and the two reports disagreeing about it is correct rather than
a contradiction.

### The ordering is load-bearing and the wrong order fails silently

Merge the **levels** and the handoff week records the position moving between contracts:
lumber steps from -2130 to -906 and the difference is a real -1224. Merge the **differences**
instead and the old code's final week is `NaN` in both inputs, one series having ended and the
other having no prior value, so **the exit never happens**. The position simply ceases to
exist and no reading anywhere says so.

`positioning_panel` therefore merges inside itself, before its own `.diff()`, rather than
offering the operation to a caller holding a differenced frame. `test_macro_pca_migrations.py`
asserts the right answer and separately asserts that the wrong order produces `NaN`, so a
refactor that moves the merge fails in the tests rather than in someone's PCA.

### Concurrency is the guard, and nothing on this store is near it

Summing is only valid for a handoff. Two codes reporting together throughout are an aggregate
and its components, or a double count, and summing them counts the same open interest twice.
Measured concurrent share of the union: **lumber 5 of 1050 weeks, 0.5%**, the Russell roughly
4%. The bar is 0.25, so it rejects a shape that does not occur here rather than tuning one
that does. **A market left unmerged is dropped; a market wrongly merged is double-counted, and
the second is the worse failure**, which is why the guard fails toward leaving codes separate.

### Off by default

Turning this on changes which markets the PCA runs over and therefore every figure downstream,
including B21's PC1 composition and B23's selection table. Default output is byte-identical
and asserted so.

---

## B28. The cocoa template is a JOINT claim, and answering it with two margins understates the miss

**Contradicts:** the headline of
[`2026-07-28-first-rankings.md` §2](../analysis/2026-07-28-first-rankings.md), which answers
the handoff's §6 question with per-category sign frequencies and concludes that "any rule
that assumes producers are short and funds are long will be wrong about half the
Disaggregated universe". The direction of that finding is right. **The magnitude is
understated by between 1.4x and 1.5x depending on the denominator, and the most interesting
case is invisible in it.**

Reproducer: `docs/analysis/reproduce.py`, the `template_shape` block, report week 2026-07-28.

> **The analysis document is not amended.** `docs/analysis/` is point-in-time and records
> what was measured against a named week; editing it to match a later reading erases the
> evidence that anything changed. The correction lives here, and §2 of that document stands
> as issued.

### The margins are correct and answer a different question

Reproduced exactly, twice, independently of the committed table:

| category | net long | net short | flat |
|---|---|---|---|
| managed_money | 120 (43.0%) | 117 (41.9%) | 42 (15.1%) |
| producer_merchant | **141 (50.5%)** | 138 (49.5%) | 0 |
| swap | 135 (48.4%) | 139 (49.8%) | 5 (1.8%) |
| other_reportable | 121 (43.4%) | 147 (52.7%) | 11 (3.9%) |
| nonreportable | 158 (56.6%) | 107 (38.4%) | 14 (5.0%) |

**But the template is a statement about a pair.** Appendix §A.2's cocoa example is
Producer/Merchant net short 110,000 *against* Managed Money net long 90,000: one instrument,
two categories, opposed. A marginal frequency cannot address that, because two categories
can each be short half the time while rarely being opposed to each other at all. That is not
a hypothetical here. It is what the data does.

### The joint distribution, which is the one the question asked for

| shape | markets | of 279 | of the 237 with a directional MM net |
|---|---|---|---|
| **template** (PM short, MM long) | 76 | 27.2% | **32.1%** |
| inverted (PM long, MM short) | 67 | 24.0% | 28.3% |
| **same side, both short** | 50 | 17.9% | 21.1% |
| **same side, both long** | 44 | 15.8% | 18.6% |
| MM net flat | 42 | 15.1% | n/a |

**"MM net flat" is not "no fund position", and the distinction is this package's own
thesis.** Of the 42, forty are genuinely empty, but `064DZS` and `064DZT` (both Nodal PJM.DOM
day-ahead power) each carry Managed Money long 750 against short 750: a 1,500-lot gross book
that nets to zero. A net is not a holding, which is exactly why Phi uses gross over `2·OI`.
They are excluded from the second denominator because they have no *directional* net to
compare against the hedger, not because the fund is absent.

Two corrections fall out, and the second is the substantive one.

**The template shape is a minority at under a third, not half.** A rule assuming
Producer/Merchant short and Managed Money long is wrong in 203 of 279 markets (72.8%), or
161 of 237 (67.9%) counting only markets with a directional MM net. §2 says "about
half". Measured as the conjunction it actually asserts, it is closer to seven in ten.

**Hedger and fund sit on the SAME side in 94 markets: 33.7% of all 279, or 39.7% of the 237
with a directional MM net.** This case does not appear anywhere in the marginal table, cannot
be derived from it, and is not contemplated by the template at all. The template's implicit
model is a two-sided market in which the fragile side is opposed by an immovable one. In a
third of this universe that opposition does not exist.

**Both denominators are quoted deliberately.** 33.7% is the one comparable to §2's own
figures, which are all over 279. Quoting only 39.7% would be the same convenient-denominator
move this section is correcting, two paragraphs after making the charge.

Where the Q axis lands when the opposition is gone, counting the single largest contributor
per market:

| shape | side | managed_money | producer_merchant | swap | other_reportable | nonreportable |
|---|---|---|---|---|---|---|
| template, 76 | `Q_sell` | **51** | 0 | 14 | 7 | 4 |
| template, 76 | `Q_buy` | 0 | **43** | 17 | 16 | 0 |
| same side, 94 | `Q_sell` | 26 | 13 | **35** | 17 | 3 |
| same side, 94 | `Q_buy` | **32** | 12 | 27 | 21 | 2 |

On template markets the axis is clean: Managed Money tops `Q_sell` in 51 of 76 and
Producer/Merchant tops `Q_buy` in 43 of 76, and neither ever tops the other side. On
same-side markets it genuinely shifts, **but to a plurality rather than a takeover**: Swap
Dealer plus Other Reportable top `Q_sell` in 52 of 94 (55%) and `Q_buy` in 48 of 94 (51%),
and Managed Money is still the single largest `Q_buy` contributor in 32 of 94. The useful
statement is that the hedger-versus-fund axis stops being reliable, not that some other pair
replaces it.

### What this changes, and what it does not

Nothing in the code. `fragility` never assumed the template shape, which is precisely why
the directional split exists: `Q_sell` and `Q_buy` are computed by sign over every category,
so a same-side market produces a correct reading with no special case. This amendment is
about how a Phi is **read**, not how it is computed, and it strengthens rather than weakens
§2's argument for keeping the two directions apart.

What it does change is the standing advice on interpreting a headline Phi. `fragility.
contributions` is already printed beside every Phi for the reason 2026-08-01 §A6 gives, that
one category dominating changes what the number means. B28 adds a second reason: **check
whether the two large categories are opposed before reading the market as having a fragile
side and a stable one.** In a third of this universe (94 of 279) there is no stable
counterparty in the template's sense, and the question of who absorbs a forced exit has a
different answer.

### Why the margins were reached for first

Worth recording, because the mistake is cheap to repeat. The handoff's §6 asks whether real
markets show "heavily producer-hedged short side, fragile levered long side", which reads as
two independent clauses and invites two independent frequency counts. It is one clause about
a joint configuration. Any future comparison against a worked example should measure the
example's **shape**, meaning the contingency table, rather than its **components**.

---

## B29. The two flow decompositions are one function, and the reason given for the gap rule is wrong

**Contradicts** two things at once: the standing characterisation of the duplication left
open by [`2026-08-01-flow-decomposition.md`](../handoffs/2026-08-01-flow-decomposition.md)
§9, repeated in `flow.py`'s module docstring, that the two implementations "answer slightly
different questions"; and the justification for the gap rule given in
[`2026-07-28-first-rankings.md` §7.2](../analysis/2026-07-28-first-rankings.md) and in
`test_flow.py`'s oats docstring.

Reproducer: `docs/analysis/reproduce.py`, the `flow_equivalence` block. Pinned offline in
[`tests/test_flow_equivalence.py`](../../tests/test_flow_equivalence.py).

> **Both are historical as of cotdata#93**, which removed the copy this section argued
> against. Neither raises: the reproducer prints the figures with a note saying why it can no
> longer derive them, and the test skips with the same reason. Regenerate against
> `cotdata<=0.2.0`. A reproducer that crashed once the change it recommended was made would
> read as a broken measurement rather than a completed one.

### They are the same function

`cotdata.vintage_flow.decompose` is **`crowdmon.futures.flow.decompose` evaluated at
`tolerance=1.0` with the gap rule off.** Not a similar approach, not a defensible
alternative: the same function at the corner of its own parameter space. On the liquid
panel, 27 markets and 135,835 transitions from 2006 to 2026:

| | result |
|---|---|
| row sets | identical, 135,835 both, 0 left-only, 0 right-only |
| label agreement | **100.000000%**, zero mismatches |
| `d_long`, `d_short`, `d_net` | identical on every row |

This is not luck. Both take the dominant leg as `argmax(|ΔLong|, |ΔShort|)`, both break exact
ties to the long leg, both treat a doubly-unmoved week as `quiet` unconditionally rather than
through a threshold. Setting `tolerance=1.0` makes `smaller <= tolerance * larger` true
everywhere, so nothing is ever `mixed`, and that is precisely `cotdata`'s classifier.

### At the default tolerance they disagree on 62% of weeks, in exactly two ways

| this module | `long_liquidation` | `new_longs` | `new_shorts` | `quiet` | `short_covering` |
|---|---|---|---|---|---|
| `gap` | 664 | 857 | 808 | 13 | 623 |
| `long_liquidation` | **13,427** | 0 | 0 | 0 | 0 |
| `mixed` | 19,463 | 20,938 | 20,822 | 0 | 19,937 |
| `new_longs` | 0 | **14,422** | 0 | 0 | 0 |
| `new_shorts` | 0 | 0 | **12,560** | 0 | 0 |
| `quiet` | 0 | 0 | 0 | **313** | 0 |
| `short_covering` | 0 | 0 | 0 | 0 | **10,988** |

Read the off-diagonal. Every disagreement sits in the `mixed` row or the `gap` row, and
**where this module commits to a direction the agreement is 100.000000% on 51,710 rows**.
The two never name opposite directions for the same week, and cannot, because the tolerance
only gates whether the smaller leg disqualifies a label. A pure state can become `mixed`; it
can never become a different pure state.

**So the difference is entirely in what each REFUSES.** That one is parameter-free and always
commits. This one can say "two-sided" and can say "that was not a week". Both refusals are
real capabilities and neither is a different opinion about the data.

### The gap rule is right, and the reason recorded for it is not

§7.2 and the oats test both say that without the gap rule the 294-day oats interval "would
enter every ranking as the largest weekly flow in the sample". **Measured, it would not, and
not by a wide margin:**

| | contracts |
|---|---|
| max abs `d_net` on the 294-day oats interval | **868** |
| oats' own max on an ordinary (<= 8 day) week | 3,024 |
| panel-wide max on any interval over 14 days | 2,552 |
| panel-wide max on an ordinary week | **180,597** |

The five rows on that interval rank **153rd, 367th, 1487th, 1714th and 3205th** of oats' own
4,555 transitions. It is not the largest flow in the panel, in the market, or in the year.

**The mechanism defeats the fear, and it is obvious in hindsight.** A market drops out of the
Disaggregated report *because it has fallen below the reporting threshold*. It is therefore
tiny while it is away and tiny when it returns, so its re-entry delta is small for the same
reason it went missing at all. The feared artifact requires a large market to vanish for
months, which is not a thing that happens.

**The rule survives on comparability, not on magnitude.** A 294-day difference is not a
weekly flow at any size, and a number that is not a week must not sit in a column of weeks
where something will eventually sum it, average it, or z-score it. That argument was always
the better one and it is the one that should have been written down. Nothing about the
implementation changes; `gap_days_tolerance` stays at its strict default.

### What is done, and what is left

The dedup **cannot go the natural direction**: `tests/test_boundaries.py` forbids `cotdata`
from importing `crowdmon`, so `cotdata` cannot delegate to the general implementation, and
inverting that would make a producer depend on its consumer. The check therefore lives here,
on the side that may import `cotdata` freely.

`tests/test_flow_equivalence.py` asserts the equivalence, the two-kinds-of-disagreement
property and the never-opposite-directions property, on the committed fixtures and offline.
**The duplication is now managed rather than merely known about**: two copies of one
algorithm in two repos drift, and drift is invisible when each side has its own passing
tests, so these assertions fail the moment either classifier changes.

What remains is a decision in a **different repo** and is deliberately not taken here.
`cotdata.vintage_flow.decompose` has exactly one consumer, `cotdata`'s own
`vintage_cli.py:293` (`cotdata-vintage flow`); nothing in `crowdmon` calls it, and the
`vintage_flow` import in `cot_adapter.py` is for `zero_sum_check`, a different function that
is genuinely `cotdata`'s. Removing it is a public-symbol removal in a PyPI package and a
change to a shared working tree that other sessions have checked out, which is not something
to do as a side effect of a `crowdmon` amendment. Recorded as an open decision, with the
measurement it needs now attached to it.

---

## B30. `coverage` solved one migration failure and does not know about its mirror image

**Extends** [`§B17`](#b17) and [`§B18`](#b18), and connects them to [`§B26`](#b26) and
[`§B27`](#b27), which were written later by a different session and never checked against
the coverage report. Reproducer: `docs/analysis/reproduce.py`, the
`lumber_is_one_instrument` block.

### The trap that was solved, and the one beside it

`coverage` keys on `market_code` rather than `(market_code, market_name)`, and §B17 records
why: four **phantoms**, pre-migration NYBOT names sitting inside codes that score 742 weeks,
so a name-keyed report invents more dead markets than it finds. That fix is correct and
stands.

It handles **one code carrying several names**. The mirror image is **one instrument
carrying several codes**, and nothing in `coverage` knows about it:

| | shape | handled by |
|---|---|---|
| phantom | one code, several names | `coverage`, by keying on the code |
| **split** | **one instrument, several codes** | `continuity`, `macro_pca.merge_migrated_codes`, **not `coverage`** |

The two markets the ladder reports as scoring nothing are **the two halves of one migrated
contract**: `058643` runs 2006-06-13 to 2023-04-18 and `058644` runs 2023-02-21 to
2026-07-28, they overlap in **7 weeks of 1051**, and both carry contract symbol `LBR`. §B26
and §B27 established exactly this for the macro PCA, where merging them recovers the market.
Nobody re-ran the coverage report afterwards.

### So is "2 of 27 score nothing" real, or an artifact of the split?

The suggestive number says artifact. Separately the codes hold 37 and 178 priced weeks;
merged they hold **208 contiguous priced weeks**, twice the 104-week extremity window.

**Measured end to end, it is real.** Merging the levels before any window (per §B27), through
both halves of the pipeline rather than only the per-category half:

| rung | `058643` | `058644` | merged |
|---|---|---|---|
| weeks | 880 | 178 | 1051 |
| `price` | 37 | 178 | **208** |
| `extremity_z` | 0 | 75 | **96** |
| `illiquidity` | 0 | 75 | **92** |
| `crowding` | 0 | 0 | **0** |
| `damage_sell` non-null weeks | 0 | 0 | **0** |

**Every rung rises substantially and the verdict does not move.** `crowding` is zero either
way, because `C = pct(z)` stacks a second three-year window on top of the 96 z values and 96
is not enough to fill it. The zero is a property of the instrument, which has four years of
prices against a measure needing six, and not of the code split.

What does change is the arithmetic of the headline: **2 of 27 becomes 1 of 26**, purely by
counting one instrument once. The unscoreable *share* is barely moved; the count of dead
markets is halved because one of the two was never a separate market.

### What follows, and what does not

**No code change.** `coverage` gaining a merge step would alter the report's row count and
change no conclusion in it, and the handoff that commissioned this module put "changing any
window, minimum or threshold" explicitly out of scope. Adding migration awareness is a build
item for whoever wants it, not a correction.

**§B18 is vindicated on the point it was least sure of.** It said `coverage` and the PCA
disagreeing about lumber "is correct rather than a contradiction", because one needs prices
and the other does not. That was an argument; this is the measurement behind it. Lumber has
1051 weeks of perfectly good positioning and cannot be scored for damage, and both reports
are right.

**The reading that would have been wrong.** Stopping at "208 contiguous priced weeks, twice
the window" gives the confident and false answer that the split caused the zero. It survives
one round of checking, because merging only the per-category half of the pipeline also
returns `crowding=0`, for the unrelated reason that `build()` still reads the unmerged store
and every per-market rung reports `058644` alone. Two different routes to the same number,
one of them meaningless. The end-to-end run is what distinguishes them.

---

## B31. The template is a metals-and-livestock shape, not a harvest shape, and B28's 27.2% is a population average

**Refines** [B28](#b28-the-cocoa-template-is-a-joint-claim-and-answering-it-with-two-margins-understates-the-miss),
which is right that the cocoa template is a joint claim and right to measure it as a
contingency table. Two things it could not see from one week of the pooled universe: the
27.2% is an average over a population that is **76% ICE power and gas basis**
([2026-08-01 A5](amendments-2026-08-01.md#a5-the-disaggregated-universe-is-mostly-power-and-gas-basis)),
which is not the population appendix §A.2's example is drawn from, and a single week cannot
distinguish a shape that is a property of the market from one that is a property of the week.

Reproducer: `docs/analysis/reproduce.py`, the `template_shape_stratified` block, all 82
vintage weeks (2025-01-07 to 2026-07-28, 346 markets, 21,756 market-weeks).

> B28 is not amended and its figures stand. It measured one week over the whole universe and
> said so. This section measures 82 weeks stratified, which is a different measurement, and
> it moves the reading rather than correcting an error.

### Split by population, the template roughly doubles

| stratum | template | inverted | both short | both long | MM flat | market-weeks |
|---|---|---|---|---|---|---|
| classic outright | **44.7%** | 25.0% | 22.8% | 3.7% | 1.7% | 3,214 |
| spread/basis/regional | 25.3% | 13.0% | 17.8% | 19.9% | 23.8% | 2,177 |
| power/gas/carbon venue | 26.8% | 25.6% | 16.0% | 16.7% | 14.8% | 16,365 |

In the latest week alone the classic figure is 52.5% against 23.0%, so B28's pooled 27.2% is
very close to the power/gas number for the arithmetic reason that power and gas are most of
the universe.

**The hand-drawn "classic outright" list is not doing the work.** A venue-only split, with no
judgement about any individual contract, gives ag/metal exchanges 47.3% against power/gas
26.8%, and the ag/metal share is higher in **82 of 82 weeks**, median gap +19.8pp, smallest
gap +7.4pp. Paired by week, so the highly autocorrelated weeks are not being counted as
independent draws.

### The fragile long side is the half that fails, and it is the half the thesis needs

| stratum | PM net short | MM net long | both (the template) | if independent |
|---|---|---|---|---|
| classic outright | 69.2% | **50.0%** | 44.7% | 34.6% |
| power/gas venue | 46.5% | 43.6% | 26.8% | 20.3% |

Two things fall out. The clauses are **positively dependent** (44.7% against 34.6% under
independence), which is the fact a marginal table structurally cannot show and the reason
B28's correction was the right one. And the binding constraint is Managed Money, not the
hedger: even among classic outrights the producer-hedged short side holds in seven weeks in
ten, while the fragile levered long side is a coin flip. The half of the template that fails
is the half carrying the `damage = crowding x illiquidity x fragility` argument.

### It is a mixture of always and never, not a 45% chance each week

Per market, over its own 82 weeks, and this is the finding that changes how the number should
be read:

| stratum | never (<=10%) | 10-25% | 25-50% | 50-75% | 75-90% | always (>=90%) | markets |
|---|---|---|---|---|---|---|---|
| classic outright | 33.3% | 12.8% | 7.7% | 12.8% | 10.3% | **23.1%** | 39 |
| spread/basis/regional | 50.0% | 11.5% | 15.4% | 7.7% | 7.7% | 7.7% | 26 |
| power/gas/carbon venue | 54.8% | 9.0% | 11.1% | 8.5% | 5.0% | 11.6% | 199 |

**64.0% of the 264 markets with at least 40 weeks sit at one extreme or the other.** The
universe is not a coin weighted to 27%; it is a mixture of markets that essentially always
carry the shape and markets that essentially never do. "The template holds in x% of markets"
invites a per-week probability reading that the data does not support.

### Which markets are always template is not the ones the example suggests

By complex, template share of market-weeks: **metals 66.5%**, softs 52.4%, energy outright
40.9%, grains/oilseeds 38.2%, livestock/dairy 37.2%, lumber 19.5%.

Always template (>=90% of weeks): LIVE CATTLE, FEEDER CATTLE, GOLD, SILVER, COPPER, COFFEE C,
GASOLINE RBOB (all 1.000), ETHANOL 0.939, PLATINUM 0.927.

Never template (<=10%): HENRY HUB, WTI-PHYSICAL, WTI FINANCIAL, WTI ICE EUROPE, NON FAT DRY
MILK, CME MILK IV (all 0.000), WHEAT-SRW 0.024, CHEESE and BUTTER 0.037, MICRO GOLD 0.037,
MILK CLASS III 0.073, ROUGH RICE 0.073, PALLADIUM 0.098.

**Every crude oil and natural gas code in the store is never-template, and the metals are the
most reliably template complex of all.** The appendix motivates the shape with a physical
harvest that a producer sells forward, and it fits gold, silver, copper and cattle best while
fitting wheat, rice and the entire crude complex worst. Whatever generates the shape, an
annual harvest is not it. Nothing here explains the mechanism, and this section deliberately
does not guess at one.

### A sixth outcome B28 does not have: no hedger side at all

`PM == 0` is not "MM net flat". It is a market with no Producer/Merchant position to be on
the other side, where the template is not false but **inexpressible**. It is 73 of 21,756
market-weeks, concentrated almost entirely in the retail-sized contracts: MICRO GOLD 58 weeks
of 80 (its Producer/Merchant gross book is zero in 58 of them, so the category is absent
rather than flat), MICRO SILVER 5, Coinbase GOLD-1oz 4, and 6 scattered elsewhere.

This is why the block labels shapes by explicit mask rather than by fall-through. A first
pass at it defaulted unmatched rows to "MM net flat" and duly reported MICRO GOLD as an
MM-flat market, when Managed Money is net long there in 84% of weeks and it is the *hedger*
that is missing.

### Cocoa does not currently show the cocoa shape

| week | producer | swap | managed money | other | non-rep | shape |
|---|---|---|---|---|---|---|
| 2025-01-07 | -36,528 | -5,886 | **+35,138** | +656 | +6,620 | template |
| 2025-10-21 | -16,747 | +11,176 | -918 | +7,094 | -605 | both short |
| 2026-07-28 | -18,433 | **+22,894** | **-8,773** | +3,217 | +1,095 | both short |

Producer/Merchant is net short in **82 of 82 weeks**, so that half of the template is as solid
as the example implies. Managed Money is net long in only 45 of 82, and in the latest week is
net *short*. The largest net long is the **Swap Dealer in 47 of 82 weeks**, against Managed
Money in 35. §A.2 puts Swap Dealer at +10,000 beside Managed Money at +90,000; real cocoa is
currently the reverse, and the long side is an index or swap book rather than a levered fund.

That is a `w_c` of 0.4 rather than 1.0 sitting where the example's fragility comes from, which
is the difference between a market that can be forced out and one that mostly cannot.

### The asymmetry is bounded by the weight table, and §A.2 sits at 90.5% of the ceiling

Since `sum_c P_c = 0`, the gross net-long total `G` equals the gross net-short total, so
`Q_sell <= max(w)*G` and `Q_buy >= min(w)*G`, giving

    Q_sell / Q_buy  <=  max(w) / min(w)  =  1.0 / 0.1  =  10.0

Checked rather than argued: across all 21,756 market-weeks the maximum observed ratio is
**9.9613** and there are **zero** breaches of 10.0.

**This corrects a reading of my own from earlier in the same session.** "No template market
in the latest week reaches the appendix's 9.05x, the maximum being copper at 8.81x" is true
and nearly meaningless, because the quantity is config-bounded at 10.0 and 9.045 is 90.5% of
that bound. The example is near-maximal by construction, not empirically extreme, and it is
attainable: 54 market-weeks reach or exceed it, though all of them are gas basis, power or
crude-differential markets rather than outrights.

The number worth carrying from that check is a different one. **The median market-week ratio
is 0.993** (p90 5.162, p99 8.197), so the typical market has `Q_sell` and `Q_buy` within a
percent of each other: no asymmetry whatsoever. The cocoa example is not a typical market
dressed up, it is one tail of a distribution whose centre is symmetric.

This is the same lesson as
[2026-08-01 A21](amendments-2026-08-01.md#a21-phi-has-no-cross-market-signal-independent-of-the-weight-table)
in a second place. A ratio whose ceiling is set by `core/config.py` is partly a statement
about the config, and quoting it as a free measurement overstates what was measured.

### What this changes

**No code change, again.** `fragility` computes `Q_sell` and `Q_buy` by sign over every
category and has never assumed the template, which is what lets a same-side or hedgerless
market produce a correct reading with no special case.

What changes is standing advice, extending B28's. Before reading a `Phi` as "a fragile side
opposed by a stable one": check the two large categories are opposed (B28), and check the
market is one whose shape persists rather than one sampled in an unusual week (here). For
crude, natural gas and SRW wheat the template is not a weak prior, it is the wrong prior.

---

## B32. On TFF the cocoa shape is not rare, it is out of range, and the mirror image is the market

**Extends** [B31](#b31-the-template-is-a-metals-and-livestock-shape-not-a-harvest-shape-and-b28s-272-is-a-population-average),
which answered "do real markets show the cocoa shape" for Disaggregated and left TFF, the
half of the COT universe the macro book lives in, unmeasured.

Reproducer: `docs/analysis/reproduce_tff.py`, the `template_shape_tff` block, all 82 vintage
weeks, 108 markets, 6,033 market-weeks. Respects the three traps
[`2026-07-28-tff-financial-futures.md` §2](../analysis/2026-07-28-tff-financial-futures.md)
establishes: the three consolidated aggregates are dropped, and every figure is reported both
unweighted and open-interest-weighted because crypto is a third of the market count and 2% of
the open interest.

### There is no producer category, so the analogue is structural rather than exact

| Disaggregated | w | TFF | w |
|---|---|---|---|
| managed_money | 1.0 | leveraged | 1.0 |
| nonreportable | 0.6 | nonreportable | 0.6 |
| other_reportable | 0.5 | other_reportable | 0.5 |
| swap | 0.4 | dealer | 0.4 |
| **producer_merchant** | **0.1** | **asset_manager** | **0.3** |

The weight-1.0 fragile holder maps cleanly. The floor does not. Producer/Merchant is a
physical hedger who can stand for delivery; Asset Manager is a pension or insurance book,
unlevered and slow but with no delivery to stand for. **The template's immovable side has no
counterpart in financial futures**, and the rest of this section is what sits there instead.

### The mirror image is the market, and by open interest it is most of it

Asset Manager against Leveraged Funds, all 82 weeks:

| asset class | MIRROR (stable long, fragile short) | cocoa direction | same long | same short | no stable side | market-weeks |
|---|---|---|---|---|---|---|
| rates/credit | **72.5%** | 6.8% | 10.3% | 10.4% | 0.0% | 1,141 |
| equity index | 44.9% | 12.0% | 30.8% | 8.0% | 3.5% | 2,001 |
| fx | 29.3% | 16.3% | 30.5% | 23.9% | 0.0% | 1,196 |
| crypto | 16.4% | 0.5% | 0.2% | 10.2% | **72.7%** | 1,613 |
| commodity index | 72.0% | 0.0% | 28.0% | 0.0% | 0.0% | 82 |

Weighted by open interest rather than market count: **MIRROR 77.3%**, both-short 10.8%,
both-long 7.2%, **cocoa direction 3.8%**.

**In the rates complex the inversion is near-total.** Across the nine contracts the
cash-futures basis trade runs through, 624 of 738 market-weeks are MIRROR: Leveraged Funds
net short in **93.0%** of them, Asset Managers net long in **87.9%**. This is the same
configuration §4 of the TFF analysis showed by hand for one week, now measured over 82.

The forced-flow consequence is the opposite of cocoa's, and it is not a detail. Cocoa's story
is a fragile long side that must **sell** into a hedger who will not bid. The rates story is a
fragile short side that must **buy** from an asset manager who will not offer. The median
`Q_sell/Q_buy` on TFF is **0.582** against 0.993 on Disaggregated, so the lean is systematic
rather than a feature of one week.

### Dealer is not the stable counterparty either

Running the same pair with Dealer (w=0.4) in the stable slot gives a different and messier
answer: **same-side-both-short is 55.3% by open interest** and 50.5% of rates market-weeks.
Dealer and Leveraged sit on the *same* side of the rates complex about half the time, which
is what the basis trade implies (the dealer is intermediating, not taking the other side of
the risk). So there is no second candidate for the immovable counterparty. Asset Manager is
the only one, and it plays the role in the opposite direction.

### Crypto has a fragile side and no stable side at all

`asset_manager` is **absent** from crypto, not merely flat: gross zero in 1,172 of 1,613
market-weeks (72.7%), with **zero** cases of a non-zero gross book netting to zero. Leveraged
Funds are present in **100%** of those same market-weeks.

That is the micro-gold finding from B31 at scale and in the more dangerous direction. Micro
gold is a market with a fund and no hedger; so is a third of TFF by market count. A monitor
reading "the fragile side is opposed by a stable one" gets no answer here rather than a weak
one, and by market count this is the single most common configuration in the whole TFF report.

### The asymmetry ceiling is three times tighter, so §A.2 is unreachable

The B31 bound applies per report type, with each report's own weights:

| report | max(w)/min(w) | max observed | breaches |
|---|---|---|---|
| Disaggregated | **10.000** | 9.9613 | 0 of 21,756 |
| TFF | **3.333** | 3.1157 sell/buy, 3.2584 buy/sell | 0 of 6,033 |

**§A.2's 9.05x cannot occur on TFF in any state of the world.** It is not that financial
futures happen not to show that asymmetry; the weight table makes it arithmetically
impossible, because the least-forceable TFF holder is three times more forceable than a
physical producer. The example is out of range rather than unrepresentative.

This is [2026-07-28 §2.3](../analysis/2026-07-28-tff-financial-futures.md)'s "Phi has a
different floor in each report, so the two scales do not correspond", applied to the
asymmetry ratio instead of to Phi, and it has the same consequence: **compare within a
report, never across.**

### Shape is less market-determined here than on Disaggregated

52.8% of the 72 TFF markets with at least 40 weeks sit at one extreme of their mirror share,
never or always, against 64.0% on Disaggregated. 11 markets are always MIRROR; 3 are always
cocoa-direction. So the mixture reading from B31 survives, weakly, and TFF markets change
configuration more readily than commodity markets do.

### What this changes

**No code change.** Every engine already runs on TFF as written, as the 2026-07-28 analysis
found, and `fragility` computes both directions by sign.

What it settles is the scope of the question B28 and B31 were answering. **The cocoa template
is a commodity-market claim.** On Disaggregated it is a real minority shape concentrated in
metals and livestock; on TFF the same configuration is 3.8% of open interest, its mirror is
77.3%, and the asymmetry the example is famous for is unreachable by construction. Anyone
carrying "fragile longs facing immovable shorts" as a default mental model of a crowded
futures market is holding a picture that is wrong about the largest part of the COT universe
by open interest, and wrong in the direction that matters: the forced flow there is buying.
