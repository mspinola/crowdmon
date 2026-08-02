# Handoff: trend alignment, spec §368

**Status:** **COMPLETE**, shipped as `futures/alignment.py`. Findings in `2026-08-02 §B20`
**Date:** 2026-08-02
**Claimed by:** the session that built `composite.py`, `trigger.py`, `reflexivity.py`,
`roll.py`, `extremity.py`, `seasonal.py`, `concentration.py` and `weight_sensitivity.py`
**Blocked on:** nothing. Measured below

> Announced before the first line of code, per this directory's convention. If you were about
> to start it, say so and I will drop it.

---

## Scope, and it is the one the spec names

Module spec §368:

> **Trend alignment score.** Correlate the cross-market positioning vector against a canonical
> time-series momentum vector (blended 20/60/250-day TSMOM per market). High alignment means
> the trend book is fully expressed, little dry powder, maximum vulnerability to reversal.

Both inputs already exist here. `trigger.py` computes `sign(F_t - F_{t-k})` for exactly
20/60/250 (`DEFAULT_LOOKBACKS`), which **is** the canonical TSMOM, and the positioning panel is
what every other engine consumes. Nothing new is needed from the store.

## Measured before claiming

### The blend is weak for two markets in three, and that is structural

Blended TSMOM as the equal-weight sign average, so it takes values in `{-1, -1/3, +1/3, +1}`:

| blended value | markets, latest week |
|---|---|
| -1.000 | 3 |
| **-0.333** | **10** |
| **+0.333** | **8** |
| +1.000 | 5 |

**69.2% of markets sit at ±1/3**, meaning their horizons disagree. That reproduces the
reflexivity finding from the other direction: `2026-08-02 §B14` measured 23 of 33 markets
(69.7%) with horizons pointing different ways, and the blended score is `sum(s)/3`, so the two
are the same fact. **The momentum vector this correlates against is mostly weak by
construction**, and any interpretation of the alignment score has to carry that.

### It has no warm-up, and that makes it the earliest-starting engine in the package

| engine | first scored | warm-up from the 2006-06-13 panel start |
|---|---|---|
| **trend alignment** | **2006-06-13** | **none** |
| macro-book PCA (differenced) | 2006-06-20 | one week |
| `damage_sell` | 2010-05-25 | 3.9 years |
| `damage_sell_pct` | 2012-05-15 | 5.9 years |

1,051 weeks, 16 to 26 markets each, median 25. The alignment score is a cross-sectional
statistic computed within a week, so unlike `C = pct(z)` it stacks no rolling window at all.

Distribution across the whole panel, **deliberately not sliced by episode**: mean 0.433, sd
0.193, p5 0.100, median 0.446, p95 0.732, range -0.257 to 0.879. It varies, it is not pinned
near zero or one, and it goes negative occasionally.

### So this is the second engine that can see 2008, and the same discipline applies

The other session flagged that the absorption ratio can reach the 2008 crisis, which `D`
structurally cannot, and decided not to look at 2008 while building it. **That reasoning
applies here identically and for a stronger reason: this engine has no warm-up at all.**

2008 is the last clean episode this package has. The prereg's §2 spent Feb 2018, March 2020,
silver 2021, the ags window, the invasion, the yen carry and gold 2025, and §9 records that the
clean episodes are spent. **They are spent for `D`.** 2008 survives only because `D` could
never reach it, so no session has ever had the option of looking.

**I will not look at 2008, or at any episode on the §10 replay list, while building this.** The
distribution above is unconditional on purpose. If this measure is worth pointing at a systemic
unwind, that test gets pre-registered and specified by a session that did not build it, exactly
as §7 was.

## Four decisions to flag rather than default

Recorded here because `gamma` and `kappa` arrived by being defaulted quietly.

1. **Which positioning vector.** The other session's PCA uses Managed Money `net_risk_usd_z`
   differenced. This measurement used Managed Money net contracts in levels. **§368 says
   "positioning", §7 says "changes", and they are different objects.** Levels answer "is the
   book expressed", changes answer "is it being expressed now". §368's "fully expressed, little
   dry powder" reads as levels. Worth agreeing across the two engines or deliberately differing
   with a reason, not by accident.
2. **Rank or linear correlation.** The measurement used Spearman, which is robust to one
   market's position dominating in size. Pearson would let the largest book set the score.
3. **The blend weights.** §368 says "blended" and gives no weights. Equal weighting is the
   defensible base case for the same reason the uniform cohort split is in `reflexivity`: it
   asserts no knowledge that does not exist. State it, sweep it, never fit it.
4. **What "high" means.** The score is a correlation and needs no sign pinning, but §368's
   reading (high alignment equals vulnerability) is a claim about tail risk and not about
   returns. It belongs beside `D` under the same §A.10 prohibition: this cannot be traded.

## What this must not do

- **Must not be wired into `D`.** §A.9 has no term for it, exactly as it has none for §A.6's
  commonality (`§B2`) or §A.8's cascade. Reported beside, never inside.
- **Must not use `unadj` or `backadj` for the momentum.** `trigger.py` already refuses both and
  says why; this reuses that path rather than recomputing signs.
- **Must not look at 2008.** See above. That is the whole value of the engine and it is spent
  the first time someone slices it.

---

## 5. Outcome, appended 2026-08-02

Shipped as `futures/alignment.py`, 17 tests. Findings in `2026-08-02 §B20`, reproducer
`docs/analysis/reproduce.py` section 18.

**Both measurements in this handoff held.** The blend is ±1/3 for 68% of markets in the latest
week, and the engine covers all 1,051 panel weeks from 2006-06-13 with no warm-up.

**One thing the handoff did not anticipate, and it changes what to report.** The score
**cannot reach 1**: the blend takes at most four values, so across a panel it is heavily tied
and the correlation is bounded. Measured, the ceiling averages **0.931 and runs 0.340 to
0.969**, which is wide enough that the raw figure is not comparable week to week. A 0.30
against a 0.34 ceiling is an expressed book; the same 0.30 against a 0.97 ceiling is not.
`alignment_series` returns `alignment_ceiling` and `alignment_vs_ceiling` for that reason, and
`max_attainable` is public so the bound can be checked directly.

**All four flagged decisions were taken as flagged**, not defaulted: levels rather than changes
(§368 says positioning, §7 says changes, and the two cross-market engines differ deliberately);
Spearman, pinned by a test showing it resists one outsized book where Pearson does not; equal
blend weights as a stated prior with `blend_sensitivity` reporting the sweep; and the §A.10
prohibition carried into the rendered output rather than only the docstring.

**§4's prohibitions all held.** Not wired into `D`, momentum refuses anything but `propadj` by
reusing `trigger.py`'s own refusal, and **2008 has not been looked at**. The distributions
recorded here and in B20 are unconditional.

**Status: closed.**
