# Handoff: roll windows, and why spec §379's roll congestion is not what gets built

**Status:** **COMPLETE**, shipped as `futures/roll.py`. Findings in `2026-08-02 §B19`
**Date:** 2026-08-02
**Claimed by:** the session that built `composite.py`, `trigger.py`, `reflexivity.py`,
`extremity.py`, `seasonal.py`, `concentration.py` and `weight_sensitivity.py`
**Blocked on:** nothing, for the reduced scope below. **Spec §379's version is blocked
permanently**, see §1.

> Announced before any code, per this directory's convention. If you were about to start
> this, say so and I will drop it.

---

## 1. Measured first: all three components of §379 are blocked

Module spec §379 defines roll congestion as three things:

> **Roll congestion.** Calendar spread volatility and bid-ask behaviour during roll windows,
> plus OI migration rate front to next.

| component | needs | status |
|---|---|---|
| calendar spread volatility | two contract prices at once | **blocked**, no per-expiry price source (ADR-0007, workspace CLAUDE.md) |
| bid-ask behaviour | quote data | **blocked**, nothing in the stack carries quotes |
| **OI migration front to next** | per-expiry open interest | **blocked**, and this one was not previously known |

**The third is a new finding and it is the reason this handoff exists.** `cotdata.get_prices`
returns an `Open Interest` column, which looks like the front-contract OI a migration rate
needs. It is not. Measured against COT's whole-market total, 1,051 weeks per market:

| symbol | mean `px_OI / COT_OI` | p5 | p95 |
|---|---|---|---|
| GC, SI | 1.000 | 1.000 | 1.000 |
| CL, ZC, NG | 1.000 | 0.999 | 1.000 |
| ZS | 1.000 | 0.998 | 1.000 |

**It is the whole-market number, identical to what COT reports.** So there is no front-versus-
next split anywhere in the stack and the migration rate cannot be computed, exactly or
approximately.

This extends the `front` naming trap that `volume.py` already documents. That column is named
`front` and is whole-market; `Open Interest` is not even named `front` and is also
whole-market. **Two columns on the same frame both look per-contract and neither is.**

**An earlier claim of mine was wrong.** `2026-08-02 §B16` says roll congestion "is not
blocked" on the strength of `roll_dates` existing. Roll *timing* is available and that part
stands. §379's roll *congestion* is blocked in all three of its stated components, and I
conflated the two, which is precisely the error I warned the other session about for PCA: the
nearest reachable object is not the one the spec names.

## 2. What is buildable, and it is not nothing

Roll dates are real: `roll_dates` is populated for 47 of 49 symbols, 235 rolls for GC back to
1978 (`§B16`). What that supports:

**Roll-window volume inflation, which is measurable and large.** Median daily volume in the
10 days before a roll against the baseline outside 20 days:

| | ratio |
|---|---|
| SI 1.70, GC 1.66, KC 1.68, 6E 1.65 | highest |
| **median across 14 markets** | **1.57x** |
| NG 1.10, LE 1.13, ZS 1.19 | lowest |

**The consequence lands on an existing module, and it is the interesting part.** `pressure.T =
Q / (kappa . V)` uses a trailing ADV that averages across roll windows. Roll-window volume is
overwhelmingly *spread* volume: people moving a position from one expiry to the next, not
people taking outright directional risk. So a `V` that includes it **overstates the liquidity
available to someone trying to leave**, and `T` is optimistic by construction for every market
in the panel.

That is §379's "measurable, predictable tax" arriving through the one door the data leaves
open. The spread itself is invisible, but its footprint in volume is not.

## 3. Scope

Build `futures/roll.py`:

- `roll_calendar(symbol)` — roll dates plus days-to-next-roll per bar
- `roll_window_volume(symbol)` — volume inside against outside the window, per market
- `adv_roll_adjusted(...)` — ADV with roll windows excluded, beside the unadjusted one, so the
  overstatement in `T` is visible rather than corrected silently
- `exit_collision(...)` — whether a forced exit of `T` days overlaps the next roll

**Named `roll.py` and not `congestion.py`, deliberately.** Nothing here computes §379's
congestion measure and the module docstring says so, so that a later session reading spec §13
step 4 does not mark it satisfied.

## 4. What this must not do

- **Must not silently replace `pressure`'s ADV.** The roll-adjusted figure is reported beside
  the existing one. Changing `T` under the composite would move `D` and every published figure
  with it, which is a calibration decision and not this module's to take.
- **Must not claim §379 is satisfied.** §13 step 4 keeps limit moves and true roll congestion
  as blocked, and the blocked table gets both, not neither.
- **Must not infer rolls from price gaps.** `roll_dates` reads the Delivery Month column, which
  is what makes it series-invariant across all three adjustments (`§B16`). Inferring from gaps
  would reintroduce the dependency that invariance currently rules out.

---

## 5. Outcome, appended 2026-08-02

Shipped as `futures/roll.py`, 16 tests. Findings in `2026-08-02 §B19`, reproducer
`docs/analysis/reproduce.py` section 17.

**§1 held in full.** All three §379 components are blocked, and the `Open Interest` finding
reproduced independently in the other session across eight markets.

**§2 was wrong twice, and the body above is left standing because this directory is
append-only.** Both corrections came from the session that owns `pressure`, and both are
right:

| §2 said | measured |
|---|---|
| roll-window effect **1.57x**, quoted as the bias in `T` | ratio **1.239x**, and the bias in `T` is **5.1%** |
| `T` "optimistic by construction for every market" | **pessimistic** for SI, NG, HO, RB and LE, five of sixteen |

The first is an order-of-magnitude error of the most ordinary kind: the ratio is a fact about
roll days, `T` is driven by a trailing mean, and a 24% lift on 22% of bars is a 5% lift on the
average. **Quoting a conditional statistic as if it were the unconditional effect.**

The second is worse than a sign error in one market, because **the ratio does not predict the
sign**. SI has a roll-day ratio of 1.244 and an ADV inflation of 0.983: more volume on roll
days by median, less by mean. So the two numbers cannot substitute for each other in either
magnitude or direction, and `roll_window_stats` returns both for that reason.

**§4's three prohibitions all held.** ADV is reported beside, never replaced; §379 stays in the
blocked table with limit moves; rolls come from Delivery Month and never from price gaps.

One addition §3 did not anticipate: `roll_adjusted_adv` **refuses** below a 25% survival floor
and flags the monthly rollers rather than refusing them, because CL, NG, HO and RB put 52-53%
of their bars inside a window and excluding those markets would remove exactly the ones a
fuel-shock scenario is about.

**Status: closed.**
