# The composite `D = C x I x Phi`, week ending 2026-07-28

**Report** Disaggregated, futures-only. **Universe** 27 markets, first score 2010-05-25.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_composite.py`.
**Code** `crowdmon.futures.composite`, appendix §A.9.

The first output that is the system rather than a component of it. With volume merged, all
three terms exist for the first time:

    D    = C x I x Phi
    C    = pct(z_t)                              crowding      (extremity, rung 4)
    I    = pct(T)                                illiquidity   (Q / kappa V)
    Phi  = sum_c w_c (L_c + S_c) / (2 . OI)      fragility     (since the first build)

> **This document validates nothing.** The episode windows in §5 are a descriptive look,
> computed after the fact on hand-chosen windows, by the session that wrote the measure.
> Workspace governance is explicit that the generator pass and the evaluator pass stay
> separate, and that a real validation is pre-registered and runs through `crucible`. Read §5
> as "where does the number go", not as evidence that it works.

---

## 1. The headline finding is about the formula, not the market

**Taking §A.9 literally makes `Phi` nearly inert.** Correlation of each factor with `D_sell`
across 20,938 scored market-weeks:

| factor | correlation with `D` | mean | std | min | max |
|---|---|---|---|---|---|
| `illiquidity_sell` | **0.857** | 0.455 | 0.308 | 0.006 | 1.000 |
| `crowding_long` | **0.796** | 0.510 | 0.313 | 0.006 | 1.000 |
| `phi` | **0.145** | 0.368 | **0.082** | 0.176 | 0.699 |

The mechanism is structural rather than empirical. `C` and `I` are percentiles, so each is
uniform on `[0, 1]` by construction with a standard deviation near 0.29. `Phi` is a raw
share of gross open interest, which is a stable property of a market's participant mix: it
spans 0.18 to 0.70 across twenty years and 27 markets, with a standard deviation of 0.082.
**Two terms vary four times as much as the third**, so `D` is very close to `C x I` with a
mild fragility tilt.

That is a direct consequence of the reading instruction. §A.9's preamble says "each term
expressed as a percentile of its own history so the product is dimensionless" and its formula
writes `C` and `I` inside `pct()` and `Phi` out in full. The formula was taken literally, as
directed. **The preamble would have fixed exactly this**: percentile-ising `Phi` too would
give all three terms equal spread and let holder fragility carry a third of the variation
rather than a fourteenth.

This is not an argument that the literal reading is wrong. It is the measurement that lets
the choice be made deliberately, and it is worth making deliberately, because the package is
named for the term the literal reading nearly removes. Both forms are one argument apart in
`composite.py`.

---

## 2. Coverage, and a four-year warm-up

| outcome | rows |
|---|---|
| scored | 20,938 |
| no_crowding | 6,256 |
| no_illiquidity | 3,606 |
| no_phi | 0 |
| **total** | **27,194** |

**77% scored.** `Phi` is never missing, because it needs only COT.

    data begins   2006-06-13
    first z       2008-06-03     one 3-year window, at min_periods
    first D       2010-05-25     a second one
    warm-up       3.9 years

`C = pct(z_t)` stacks two trailing windows: `z` needs three years of position history, and
its percentile needs three years of `z`. **The composite cannot say anything about 2008**, so
the GFC is not testable on this panel at all, and the module spec §10 replay list loses its
most useful episode. Reading `C` as `pct(x)` instead would halve the warm-up and is a
different formula.

---

## 3. The latest week

Highest `damage_sell` percentile, every factor shown, because a composite that hides its
terms is unauditable.

| market | C (long) | I (sell) | Phi | D | D pct | days to liquidate |
|---|---|---|---|---|---|---|
| SUGAR NO. 11 | 0.631 | 0.669 | 0.393 | 0.166 | **0.981** | 3.0 |
| GASOLINE RBOB | 0.898 | 0.815 | 0.303 | 0.222 | 0.962 | 2.3 |
| CORN | 0.930 | 0.841 | 0.313 | 0.245 | 0.930 | 3.7 |
| SOYBEAN MEAL | 0.892 | 0.796 | 0.287 | 0.203 | 0.930 | 4.4 |
| WHEAT-HRW | 0.981 | 0.962 | 0.308 | **0.291** | 0.924 | 4.0 |
| SOYBEAN OIL | 0.892 | 0.879 | 0.243 | 0.190 | 0.866 | 3.6 |
| COTTON NO. 2 | 0.968 | 0.815 | 0.311 | 0.245 | 0.866 | 7.1 |
| NAT GAS NYME | **0.274** | 0.567 | 0.262 | **0.041** | 0.854 | 0.8 |

And the other direction, which is a different list:

| market | C (short) | I (buy) | Phi | D | D pct | days |
|---|---|---|---|---|---|---|
| GOLD | 0.803 | 0.433 | 0.468 | 0.163 | 0.924 | 1.6 |
| FRZN CONC ORANGE JUICE | 0.860 | 0.930 | **0.533** | **0.427** | 0.924 | 5.9 |
| LEAN HOGS | 0.943 | 0.637 | 0.407 | 0.245 | 0.892 | 2.6 |
| NAT GAS NYME | 0.726 | 0.873 | 0.262 | 0.166 | 0.879 | 1.4 |
| COPPER | 0.357 | 0.618 | 0.345 | 0.076 | 0.803 | 0.6 |

**Days-to-liquidate is finally a real number.** These are 0.6 to 7.1 days at 20%
participation, against the appendix's cocoa example of 20 days. Nothing in the current
cross-section is anywhere near that.

### The trap in reading the percentile

Natural gas appears in **both** tables. On the sell side its raw `D` is 0.041, the lowest in
the table and a quarter of the next, yet its percentile is 0.854. That is §A.10 working as
specified — "report `D` as a percentile of its own history, never as an absolute level" —
and it means the percentile ranks a market **against itself**, not against the others.

So the sell-side table is not a league table. Sugar tops it at 0.981 with a raw `D` of 0.166,
while wheat-HRW has the largest raw `D` at 0.291 and ranks fifth. Both readings are correct
and they answer different questions: "unusual for this market" versus "large in absolute
terms". The raw column is printed beside the percentile so the difference is visible rather
than inferred.

---

## 4. Is it multiplicative in practice?

Yes, in the sense that matters: no single term determines `D`. The two percentile terms have
correlations of 0.86 and 0.80 with the product, which is what you would expect of two roughly
independent uniform factors. Natural gas is the clean illustration — `I` of 0.567 and `Phi`
of 0.262 are unremarkable, and a `C` of 0.274 (a crowded *short*, not a long) collapses
`damage_sell` to 0.041. An additive score would have placed it mid-table.

`Phi`'s weak contribution is §1 and is a property of the formula's construction.

---

## 5. Episode windows, descriptive only

Module spec §10 asks that the composite "elevate **before** the drawdown rather than
coincidentally with it". These windows were chosen by hand, after the fact, on the same data,
by the session that wrote the measure. **This is a look, not a test.**

Baseline mean `D_sell` across all scored weeks: **0.1067**.

| window | market-weeks | mean D | vs baseline | C | I | Phi |
|---|---|---|---|---|---|---|
| Mar 2020 lead (Oct19-Jan20) | 449 | 0.1257 | **1.18x** | 0.573 | 0.496 | 0.359 |
| Mar 2020 event (Feb-Apr20) | 319 | 0.0797 | **0.75x** | 0.534 | 0.343 | 0.342 |
| Mar 2020 after (May-Aug20) | 424 | 0.0952 | 0.89x | 0.574 | 0.400 | 0.349 |
| 2021 ags/lumber | 547 | 0.1700 | **1.59x** | 0.633 | 0.717 | 0.354 |
| 2022 invasion | 432 | 0.1451 | 1.36x | 0.608 | 0.631 | 0.362 |

### March 2020 is the interesting one, and it went down

`D` was 1.18x baseline in the four months before, **0.75x during the event**, and 0.89x
after. The direction is what the spec asks for (elevated before, not during), but 1.18x is a
weak lead and the drop during is worth explaining rather than celebrating.

What moved, against the 2019 mean:

    crowding_long        0.4635  ->  0.5339    1.15x
    illiquidity_sell     0.3634  ->  0.3435    0.95x
    phi                  0.3666  ->  0.3415    0.93x
    dtl_sell             4.4762  ->  3.5994    0.80x
    adv                 159,028  -> 170,044    1.07x

**`T` fell from both ends at once.** Volume rose 1.07x and `Q` fell as positions were
liquidated, so days-to-liquidate dropped 20% and `I` with it. That is not the volume-spike
trap — the volume module uses trailing aggregates and never a spot reading, which is what
stops the sharp version of this — but it is the same mechanism running slowly through a
252-day average, compounded by the numerator genuinely shrinking.

The honest reading: **`D` describes a pre-condition, and by definition it decays as the
position it describes leaves.** Once the crowd is out there is nothing left to force out.
Whether the 1.18x lead is signal or noise is exactly the question this document cannot
answer, on one episode, with a hand-chosen window, and n=3 episodes of which one is not
reachable.

2021 and 2022 are the more encouraging readings at 1.59x and 1.36x, and in both the lift
comes mostly from `I` (0.717 and 0.631 against a 0.455 mean) rather than from crowding.

---

## 6. What is missing

- **`T_eff`, so §A.6 is absent.** `I = pct(T)`, not `pct(T_eff)`. The commonality adjustment
  `T_eff = T(1 + gamma . beta_bar)` needs an Amihud panel and a value for `gamma`, which the
  appendix never gives. `T_eff` reduces to `T` exactly at `gamma = 0`, so this is that
  special case. The consequence is not cosmetic: **`D` currently assumes exits are
  independent across markets**, and §A.6 exists because they are not. The illiquidity term is
  optimistic in precisely the conditions where it matters most.
- **No 2008.** The four-year warm-up in §2 removes the best episode on the list.
- **27 markets.** Extremity cannot run on the 279-market vintage panel, so neither can `D`.
- **`kappa = 0.2` is unswept.** Every duration scales as `1/kappa`, so the ranking is
  invariant to it but the days are not.
- **`T` is a lower bound on pain** (§A.11): `V` is endogenous and treated as exogenous, so
  every duration here is optimistic.
- **Not point-in-time.** `from_current_store` carries revisions. The scores contain no
  lookahead, which is a narrower and separately tested claim.

---

## Bottom line

The system computes end to end for the first time: COT positions through a contract master,
notional, risk units, extremity and volume into a single bounded number per market per
direction per week, with 77% coverage over sixteen scoreable years and no lookahead in any
rolling window.

The most useful thing measured is about the formula rather than the market. **Taking §A.9
literally leaves `Phi` doing almost none of the work** — a correlation of 0.145 against 0.86
and 0.80 for the two percentile terms, because a raw share of gross open interest varies four
times less than a percentile does by construction. The package is named for holder fragility
and the literal composite nearly removes it. §A.9's own preamble specifies the fix, and the
two readings are one argument apart in the code, so this is a decision worth making on
purpose rather than by precedence.

The episode look is not a validation and should not be read as one. For what it is worth on
three hand-chosen windows: `D` ran 1.18x baseline before March 2020 and fell to 0.75x during
it, which is directionally what the spec asks for and a weak signal on one episode; 2021 and
2022 read 1.59x and 1.36x, driven mostly by illiquidity rather than crowding.

**In plain terms: the machinery is complete and behaves sensibly, days-to-liquidate is a real
duration at last, and nothing in the current week is remotely close to the appendix's worked
example.** Whether `D` actually anticipates anything is unanswered, unanswerable from here,
and belongs to a pre-registered run through `crucible` rather than to the session that built
it.
