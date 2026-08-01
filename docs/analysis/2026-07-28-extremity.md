# Positioning extremity in risk units, week ending 2026-07-28

**Report** Disaggregated, futures-only. **Universe** 27 markets, 2006-06-13 to 2026-07-28.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_extremity.py`.
**Code** `crowdmon.core.aggregate` (trailing z and percentile), `crowdmon.futures.extremity`.

Module spec §6.1 and appendix §A.4, the last piece of the spec's step 3. With the
normalisation ladder complete through rung 4, positioning can finally be standardised
against its own history in the units that actually force deleveraging:

    x_t = P_t . M_t . F_t . sigma_t          net_risk_usd
    z_t = (x_t - mu_W) / s_W                 trailing 3 years
    pct = rank of x_t in the same window

Steps 1 to 3 are what the spec calls a working monitor on their own. This completes them.

---

## 1. The universe is 27 markets, and that is a data fact

A three-year window needs three years. The vintage store begins 2025-01-07 and holds about
nineteen months, so extremity cannot run on the 346-market breadth panel at all;
`add_extremity` raises rather than returning a silently all-null column. Only
`from_current_store` reaches back far enough: **27 markets, 20.1 years.**

Breadth and depth stay in different places. `fragility` and `flow` run across the full
279-market cross-section and extremity does not, and no amount of code changes that.

### Coverage

| outcome | rows |
|---|---|
| scored | 117,940 |
| short_history | 13,770 |
| no_risk_units | 4,260 |
| **total** | **135,970** |

**86.7% scored.** The two gaps are different things and were kept apart on purpose:

- **`short_history` (10.1%)** is the first two years of each series plus the far side of long
  gaps. Structural, and no fix exists: a market's first observation has no history to be
  extreme against.
- **`no_risk_units` (3.1%)** decomposes further, and it turned out to be one contract:

| outcome | rows |
|---|---|
| with_risk_units | 131,710 |
| no_notional | 4,215 |
| no_volatility | 45 |

**All 4,215 no-notional rows are market code `058643`, RANDOM LENGTH LUMBER.** Its COT
series runs to 2023-04-18 and its price coverage stops at 2022-08-02: a delisted contract,
replaced by the current LBR contract, with no price series to value it. That is a clean
answer rather than a systematic coverage problem, and it is the same `058643` the contract
master flags for carrying a 4.0 contract-size scale.

---

## 2. The measure disagreed with the spec, and the appendix settled it

Module spec §6.1 says "Rolling z-score and percentile of vol-scaled net notional, per market
per category, 3-year window, **winsorised**." Appendix §A.4 gives the plain
`z_t = (x_t - mu_W)/s_W` and says nothing about winsorising.

**The appendix is the authoritative statement of every formula in this package, so it wins.**
The measurement agrees with it, which is the more interesting part.

Winsorising assumes the values it clips are outliers. In positioning data they are usually
the top of a **build**, because positions accumulate over months rather than spiking for a
week. Clipping them removes the build, shrinks the standard deviation, and manufactures a
score from data that does not support it.

The worst case in twenty years is **Platinum, Other Reportable, 2026-01-27**. Its trailing
window's six largest values are a monotone run-up ending at the current point:

    31,523,743   47,131,876   47,592,840   54,396,691   55,713,367   62,513,836

Winsorising at 5% clips that run-up away:

    RAW         mean 9,815,959   std 8,590,872   ->  z =  6.13
    WINSORISED  mean 8,493,972   std 2,444,729   ->  z = 22.10

The standard deviation shrinks 3.5x and the score nearly quadruples, on identical data. A
z of 22 would top any ranking it entered.

Across the whole panel:

| winsor | median abs z | 99th | max | share above 6 |
|---|---|---|---|---|
| **0.00** | 0.85 | 3.65 | **9.6** | 0.05% |
| 0.05 | 0.91 | 4.31 | 22.1 | 0.32% |
| 0.10 | 1.00 | 5.46 | 27.4 | 0.75% |

`DEFAULT_WINSOR = 0.0`. The parameter stays, because a genuinely spiky series would benefit,
and it defaults off.

**The percentile is unaffected either way**, because ranks do not care about the magnitude of
the tails. Platinum reads 1.0000 at both settings. That is the strongest argument for the
spec's own instruction that the *percentile* is the thing to report: the one free parameter
in the module touches only the secondary number.

---

## 3. The latest week

Managed Money, the eight readings furthest from the median of their own three-year history.
Both tails, because a 4th percentile is as extreme as a 96th.

| market | code | net contracts | net risk USD | z | percentile |
|---|---|---|---|---|---|
| WHEAT-HRW | 001612 | 31,411 | 22,744,938 | 2.78 | **0.981** |
| GASOLINE RBOB | 111659 | 73,877 | 277,360,491 | 2.12 | 0.949 |
| WHEAT-SRW | 001602 | **−8,163** | **−5,703,126** | 1.53 | **0.943** |
| SOYBEANS | 005602 | 160,479 | 117,134,224 | 1.67 | 0.936 |
| COTTON NO. 2 | 033661 | 46,368 | 34,234,437 | 1.61 | 0.924 |
| FRZN CONC ORANGE JUICE | 040701 | −1,580 | −1,620,640 | −1.36 | 0.089 |
| LEAN HOGS | 054642 | −19,118 | −7,826,336 | −1.65 | 0.051 |
| COCOA | 073732 | −8,773 | −20,955,201 | −1.36 | 0.045 |

Nothing here is at a twenty-year extreme. The largest reading is HRW wheat at the 98th
percentile of its own trailing three years, and the distribution's own 99.9th percentile is
`|z| = 5.51` against this week's maximum of 2.78. **This is an unremarkable week**, which is
worth stating plainly: a monitor that finds something alarming every time it runs is not
measuring anything.

### The wheat row that looks like a bug and is not

WHEAT-SRW is net **short** 8,163 contracts, carries **negative** risk units, and reads at the
**94th percentile**. That combination is correct, and it is the single most important thing
to understand about this measure.

    WHEAT-SRW managed money, trailing three years
      window mean   -32,457,375
      window min    -86,323,167
      window max      6,798,925
      latest         -5,703,126     pct = 0.943

Managed Money is *usually* far more short in SRW wheat than it is now. A small short against
a history of much larger shorts is a high percentile. **Extremity is measured against own
history, not against zero**, and a reader who expects "high percentile" to mean "big long"
will misread it every time a market has a persistent directional bias, which is most
agricultural commercials and many spec books.

Contrast HRW wheat, where the same 98th-percentile reading *is* a large long: window range
−31.3m to +28.1m, latest +22.7m. Same percentile scale, opposite situations, and only the
window tells you which.

---

## 4. Extremes persist, and the base rate proves it

The percentile invites a frequency reading: 95th percentile, one week in twenty. Measured
over 117,940 scored market-weeks, that is wrong by a factor of two.

    share above the 95th percentile:  10.11%   (nominal 5%)
    share below the  5th percentile:   8.90%   (nominal 5%)

The cause is serial dependence, and it is measurable directly. Consecutive-week episodes
above the 95th percentile, per market-category:

| | |
|---|---|
| episodes | 2,477 |
| mean run length | **4.8 weeks** |
| median | 3 weeks |
| 90th percentile | 12 weeks |
| longest | **42 weeks** |
| share of hot weeks inside runs of 8+ weeks | **57.6%** |

**A 95th-percentile reading is not a one-in-twenty event. It is the middle of an episode
that lasts about five weeks on average and can last most of a year.** More than half of all
hot weeks occur inside runs of two months or longer.

This is module spec §11 item 7 ("positioning extremes persist for quarters") showing up as a
number rather than a caution, and it has a direct consequence for anything built on top:
**percentile exceedances are not independent events and must not be counted as though they
were.** Any downstream work that treats "weeks above the 95th" as a sample size has an
effective sample roughly a fifth of its nominal one. That bears on `crucible`'s job, not this
package's, but the measurement belongs here where it was made.

It also means the measure behaves as designed. A crowding indicator that flickered in and out
week to week would be describing noise; one that stays elevated through an episode is
describing a position.

---

## 5. What is missing

- **No `I` term, so no composite.** Appendix §A.9 is `D = C x I x Phi`. This document
  delivers `C`, `Phi` has existed since the first build, and `I` needs `T_eff`, which needs
  **volume**, which does not exist anywhere in this workspace. The composite is now blocked
  on exactly one missing data source and nothing else.
- **27 markets.** Not the 279-market cross-section, for the reason in §1. Every finding here
  is about liquid classic outrights and says nothing about ICE Energy Div or Nodal.
- **The z is ordinal, not distributional.** Positioning is not normal, so `z = 2.78` should
  not be read as a tail probability. The percentile is the honest form and is what §6.1 asks
  be reported.
- **Three years is a choice.** The spec specifies it and it is implemented as a calendar
  window rather than an observation count, so gaps shrink the window instead of silently
  reaching further back. It has not been swept, and a 5-year window would produce different
  percentiles. That sweep is worth doing before any rule is built on the number.
- **Nothing here is point-in-time.** `from_current_store` returns current values with
  revisions applied, so these scores are contaminated by hindsight in the ordinary
  CFTC-revision sense. Fine for description, not for evaluating a rule. The scores themselves
  contain no lookahead (§6 below), which is a different and narrower claim.

---

## 6. What was verified rather than assumed

The property this measure would be worthless without: **a score never changes when later
data arrives.** Tested by scoring a 250-point series and a 400-point superset and asserting
every overlapping value is identical, for both the z and the percentile
([`tests/test_extremity.py`](../../tests/test_extremity.py)).

That test exists because the failure is silent. A centred window, a full-sample mean, or a
stray `.shift(-1)` produces plausible numbers, passes every other test, and flatters every
historical result built on it. Nothing else in the suite would catch it.

Two related guards: an unsorted index raises rather than rolling backwards over rows that are
actually later, and a time-based window on a non-datetime index raises rather than silently
becoming positional.

---

## Bottom line

Extremity completes the spec's step 3, so the positioning engine now does everything it was
specified to do without prices for exit capacity: flow decomposition, breadth-depth,
fragility, and now extremity in risk units against three years of own history. Coverage is
86.7% of 136,000 market-weeks over twenty years, and the 3.1% with no risk units turned out
to be a single delisted lumber contract rather than anything systematic.

Two findings are worth more than the week's rankings. **Winsorising, which module spec §6.1
asks for, actively damages this measure** on positioning data: it mistakes a build for an
outlier and inflated platinum's score from 6.1 to 22.1. The appendix specifies no
winsorisation, the appendix is authoritative, and the measurement agrees, so it defaults off.
And **extreme readings persist far longer than the percentile suggests** — 10.1% of weeks sit
above the nominal 5% threshold, in episodes averaging five weeks and running up to 42, with
57.6% of hot weeks inside runs of two months or more.

The current week is quiet. HRW wheat at the 98th percentile of its own three years is the
strongest reading, against a panel whose 99.9th percentile is roughly twice as far out, and
nothing is near a twenty-year extreme.

**In plain terms: the machinery works, it is verified free of the lookahead that would make
it useless, and it says this week is normal.** The most useful things learned are about the
measure rather than the market: a high percentile can be a small short if the market is
usually shorter, and an extreme reading is the middle of a months-long episode rather than a
rare event. Both would mislead anyone reading the number without them.
