# Spec amendments, 2026-08-02

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc and
say so.

The first file under the one-file-per-day convention that
[`amendments-2026-08-01.md`](amendments-2026-08-01.md) closes. Cross-file references carry the
date: `2026-08-01 §A15`.

> **Filed here, measured on 2026-08-01.** The 08-01 file was closed to new sections partway
> through that day and the daily convention begins on 08-02, which leaves a few hours with no
> home. Both sections below were measured on 2026-08-01 against
> `COTDATA_STORE=~/code/cotdata_store`. Whoever picks up the convention next may prefer a
> different tie-break; this one is recorded rather than assumed.

Every figure below is reproduced by `docs/analysis/reproduce.py` or asserted in
`tests/test_commonality_live.py`.

---

## A1. §A.6's basket regression is vacuous unless the own market is excluded

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

## A2. §A.6 cannot change §A.9's composite, because a percentile ignores a constant

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
