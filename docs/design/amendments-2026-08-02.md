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

Figures below are reproduced by `docs/analysis/reproduce.py` (B1-B2),
`docs/analysis/reproduce_seasonal.py` (B3-B7), or asserted in `tests/test_commonality_live.py`.

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
