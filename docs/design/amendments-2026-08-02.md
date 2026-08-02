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
