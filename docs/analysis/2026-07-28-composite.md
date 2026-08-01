# The composite `D = C x I x Phi`, week ending 2026-07-28

**Report** Disaggregated, futures-only. **Universe** 27 markets, first score 2010-05-25.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_composite.py`.
**Code** `crowdmon.futures.composite`, appendix §A.9.

The first output that is the system rather than a component of it. With volume merged, all
three terms exist for the first time:

    D    = C x I x Phi
    C    = pct(z_t)                              crowding      (extremity, rung 4)
    I    = pct(T)                                illiquidity   (Q / kappa V)
    Phi  = pct( sum_c w_c (L_c+S_c) / (2 . OI) ) fragility     (since the first build)

> **This document validates nothing.** The episode windows in §5 are a descriptive look,
> computed after the fact on hand-chosen windows, by the session that wrote the measure.
> Workspace governance is explicit that the generator pass and the evaluator pass stay
> separate, and that a real validation is pre-registered and runs through `crucible`. Read §5
> as "where does the number go", not as evidence that it works.

---

## 1. The headline finding is about the formula, not the market

> **Acted on, same day.** The measurement below was taken with `Phi` entering raw, per §A.9's
> formula. It showed the term the package is named for doing almost none of the work, so
> `Phi` is now **percentile-ised**, following §A.9's preamble instead. `phi_percentile=False`
> restores the literal reading. The before-and-after is at the end of this section; every
> other figure in this document is from the literal run and is labelled where it matters.

**Taking §A.9 literally made `Phi` nearly inert.** Correlation of each factor with `D_sell`
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

### What changed when `Phi` was percentile-ised

| reading | crowding | illiquidity | fragility | coverage |
|---|---|---|---|---|
| literal, raw `Phi` | 0.796 | 0.857 | **0.145** | 77.0% |
| preamble, `pct(Phi)` | 0.585 | 0.681 | **0.401** | 77.0% |

All three standard deviations are now about 0.31 and the three terms share the work.
Fragility's correlation with `D` nearly triples.

**Coverage is unchanged**, which was worth checking rather than assuming: `pct(Phi)` needs a
three-year window where raw `Phi` needs none, but `C = pct(z)` already needs two stacked
three-year windows and is the binding constraint, so the extra warm-up finishes well inside
it and costs nothing.

One behaviour worth knowing: a **constant** `Phi` percentile-ises to about 0.5, not 1.0.
Every value in the window ties and ties take their average rank, so a market whose
participant mix never changes sits in the middle of its own distribution. That is the right
answer and it is not the obvious one.

---

## 2. Coverage, and a four-year warm-up

| outcome | rows |
|---|---|
| scored | 20,938 |
| no_crowding | 6,256 |
| no_illiquidity | 3,606 |
| no_fragility | 2,829 |
| **total** | **27,194** |

**77.0% scored.** Raw `Phi` is never missing, since it needs only COT; its percentile needs a
three-year window, which is why `no_fragility` is 2,829 rather than zero. Total coverage is
unchanged because `C` needs two stacked windows and remains the binding constraint.

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

| market | C (long) | I (sell) | Phi (pct) | phi raw | D | D pct | days |
|---|---|---|---|---|---|---|---|
| GASOLINE RBOB | 0.898 | 0.815 | 0.975 | 0.303 | 0.714 | **0.987** | 2.3 |
| NAT GAS NYME | **0.274** | 0.567 | 0.777 | 0.262 | 0.121 | **0.987** | 0.8 |
| SUGAR NO. 11 | 0.631 | 0.669 | 0.936 | 0.393 | 0.395 | 0.981 | 3.0 |
| CORN | 0.930 | 0.841 | 0.395 | 0.313 | 0.309 | 0.955 | 3.7 |
| WTI-PHYSICAL | 0.885 | 0.242 | 0.822 | 0.229 | 0.176 | 0.828 | 0.8 |
| SOYBEAN MEAL | 0.892 | 0.796 | 0.159 | 0.287 | 0.113 | 0.803 | 4.4 |
| NY HARBOR ULSD | 0.720 | 0.312 | **1.000** | 0.321 | 0.225 | 0.796 | 1.1 |
| MILK, Class III | 0.420 | 0.758 | 0.312 | 0.325 | 0.099 | 0.764 | **9.0** |

And the other direction, which is a different list:

| market | C (short) | I (buy) | Phi (pct) | phi raw | D | D pct | days |
|---|---|---|---|---|---|---|---|
| NAT GAS NYME | 0.726 | 0.873 | 0.777 | 0.262 | 0.492 | **1.000** | 1.4 |
| FRZN CONC ORANGE JUICE | 0.860 | 0.930 | 0.968 | 0.533 | **0.774** | 0.930 | 5.9 |
| LEAN HOGS | 0.943 | 0.637 | 0.834 | 0.407 | 0.501 | 0.905 | 2.6 |
| GOLD | 0.803 | 0.433 | 0.471 | 0.468 | 0.164 | 0.854 | 1.6 |
| COPPER | 0.357 | 0.618 | 0.274 | 0.345 | 0.060 | 0.834 | 0.6 |

Both the raw share and its percentile are printed. Soybean meal is the clearest case for why:
a raw `Phi` of 0.287 is close to the 0.368 panel mean and reads as ordinary, while its
percentile of 0.159 says this market is **less** fragile than its own recent norm. The raw
number compares across markets, the percentile within one, and `D` uses the percentile.

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

Yes, and more so than under the literal reading. Correlation with `D_sell`:

| factor | corr | std |
|---|---|---|
| `illiquidity_sell` | 0.681 | 0.308 |
| `crowding_long` | 0.585 | 0.313 |
| `fragility` | **0.401** | 0.313 |
| *(raw `phi`, which `D` no longer uses)* | *0.110* | *0.082* |

No term dominates and all three have the same spread. Natural gas is the illustration in both
directions at once: it tops the **buy** list at `D` = 0.492 and appears near the top of the
**sell** list with `D` = 0.121, because `C_long` of 0.274 is a crowded short. The same market,
the same week, two very different damages depending on which way it breaks.

---

## 5. Episode windows, descriptive only

Module spec §10 asks that the composite "elevate **before** the drawdown rather than
coincidentally with it". These windows were chosen by hand, after the fact, on the same data,
by the session that wrote the measure. **This is a look, not a test.**

Baseline mean `D_sell` across all scored weeks: **0.1413**.

| window | market-weeks | mean D | vs baseline | C | I | Phi |
|---|---|---|---|---|---|---|
| Mar 2020 lead (Oct19-Jan20) | 449 | 0.1070 | **0.76x** | 0.573 | 0.496 | 0.373 |
| Mar 2020 event (Feb-Apr20) | 319 | 0.0629 | **0.45x** | 0.534 | 0.343 | 0.267 |
| Mar 2020 after (May-Aug20) | 424 | 0.0965 | 0.68x | 0.574 | 0.400 | 0.370 |
| 2021 ags/lumber | 547 | 0.2337 | **1.65x** | 0.633 | 0.717 | 0.469 |
| 2022 invasion | 432 | 0.2651 | **1.88x** | 0.608 | 0.631 | 0.590 |

### March 2020 does not lead, and the earlier reading said it did

Under the literal raw-`Phi` formula this window read 1.18x baseline in the lead-up, which
looked like weak support for spec §10's "elevate before the drawdown". **Percentile-ising
`Phi` removes it**: the lead-up is 0.76x, the event 0.45x, the aftermath 0.68x. The whole
episode sits below baseline. That earlier 1.18x was an artifact of a term with almost no
variance, and correcting the formula corrected the conclusion with it.

What moved during the event, against the 2019 mean:

    crowding_long        0.4635  ->  0.5339    1.15x
    illiquidity_sell     0.3634  ->  0.3435    0.95x
    fragility            0.4068  ->  0.2666    0.66x
    dtl_sell             4.4762  ->  3.5994    0.80x
    adv                 159,028  -> 170,044    1.07x

Two terms fell together. `T` dropped 20% as volume rose 1.07x and `Q` shrank with the
liquidation, and **fragility fell by a third** as the forceable holders left. That is
coherent: `D` describes a pre-condition, and both the position and the holders it describes
exit during the event. It is also not the volume-spike trap, which `volume.py` closes by
construction with trailing aggregates.

2021 and 2022 read 1.65x and 1.88x, both stronger than under the literal formula, and in both
the lift is broad rather than carried by one term.

**None of this is evidence the measure works.** Three hand-chosen windows, after the fact, on
the same data, by the session that wrote it, with the best episode out of reach.

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

The system computes end to end: COT positions through contract master, notional, risk units,
extremity and volume into one bounded number per market per direction per week, 77.0%
coverage over sixteen scoreable years, no lookahead in any rolling window.

**The formula reading turned out to matter more than anything the numbers said.** Built
literally, with `Phi` as a raw share, the fragility term correlated 0.145 with `D` while the
two percentile terms correlated 0.86 and 0.80 — the package's namesake concept doing a
fourteenth of the work, for the structural reason that a share of gross open interest varies
four times less than a percentile does. Following §A.9's preamble instead brings fragility to
0.401 and gives all three terms the same spread, at no cost in coverage.

**That change also reversed a conclusion.** Under the literal reading, `D` ran 1.18x baseline
before March 2020, which looked like weak support for the spec's "elevate before the
drawdown". Percentile-ised, the lead-up is 0.76x and the whole episode sits below baseline.
The apparent lead was an artifact of a near-constant term. 2021 and 2022 strengthen to 1.65x
and 1.88x.

The episode look remains descriptive and is not a validation, on three hand-chosen windows
with the 2008 GFC out of reach behind a four-year warm-up.

**In plain terms: the machinery is complete, days-to-liquidate is a real duration at last, and
the most valuable thing this exercise produced was catching that the literal formula nearly
discarded the concept the system is built on — and that fixing it removed the one encouraging
result the earlier version had reported.** Whether `D` anticipates anything is unanswered,
unanswerable from here, and belongs to a pre-registered run through `crucible`.
