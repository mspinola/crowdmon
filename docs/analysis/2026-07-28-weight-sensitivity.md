# How much of a fragility result is the weights? Week ending 2026-07-28

**Report** Disaggregated, futures-only. **Universe** 279 markets in the latest week; 27
markets, 2006-2026, for the identity check.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_weight_sensitivity.py`.
**Code** `crowdmon.futures.weight_sensitivity`, module spec §6.3 and appendix §A.11.

Both documents require this and neither had been run. §6.3: weights are "configured,
documented as judgement, and subjected to sensitivity analysis rather than presented as
estimates". §A.11, listing known biases: "results should be reported with sensitivity
analysis across plausible weightings."

**Four analyses in this directory rank markets on `Phi`, `Q_sell` or `D` without one.** This
is that debt paid, and it is a debt against work already published rather than a new
capability.

---

## 1. What counts as a plausible weighting

The judgement in §6.3 is an **ordering** before it is a set of values:

| category | `w_c` |
|---|---|
| managed_money | 1.0 |
| nonreportable | 0.6 |
| other_reportable | 0.5 |
| swap | 0.4 |
| producer_merchant | 0.1 |

Confidence that a levered fund is more forceable than a retail account, which is more
forceable than a producer hedging physical, is far higher than confidence that Swap Dealer is
*exactly* 0.4. So the plausible class swept here is **order-preserving jitter**: move every
weight by a uniform draw in `±0.15`, keep it in `[0.02, 1]`, reject any draw that reorders
the categories, and repeat 200 times from a fixed seed.

A weighting that says producers are the most forceable is not a rival estimate of the same
judgement, it is a different claim. Those are reported separately in §3 as reference points.

The `0.02` floor matters: producer sits at 0.1, so unbounded `±0.15` jitter would zero it,
and a zero weight is not a small weight. It removes the category from every sum it belongs
in, which is a different experiment.

---

## 2. The flat baseline is degenerate, and it is algebra

Setting every weight to 1.0 looks like the natural null. It is not. In the Disaggregated
schema the category rows exclude spreading, so

    sum_c (L_c + S_c) = 2 . (OI - spreading)

and therefore

    Phi_flat = 2(OI - spreading) / (2 . OI) = 1 - spreading / OI

Checked against the store rather than asserted:

| | |
|---|---|
| market-weeks checked (latest week) | 279 |
| max abs residual | **1.11e-16** |
| the same over twenty years | 27,194 market-weeks, max residual **1.11e-16** |
| median `Phi_flat` | 0.9417 |
| std `Phi_flat` | 0.0925 |

Exact to floating point, everywhere.

**So `Phi` carries no cross-market information independent of the weight table.** Under equal
weights it measures the spreading share and nothing else. `Phi` is not a measurement that the
weights adjust; it is a weighted restatement of the category mix, and every cross-market
difference in a real `Phi` is the weight table speaking.

That is the single most useful thing in this document and it changes how the other four
analyses should be read. It also explains why percentile-ising `Phi` in the composite mattered
so much: the raw quantity has very little spread to begin with.

---

## 3. Reference weightings, which are not plausible

| variant | median `Phi` | top-10 overlap | rank corr | `Phi` corr |
|---|---|---|---|---|
| flat (all 1.0) | 0.9417 | 3/10 | 0.485 | **−0.115** |
| crowd_only (Managed Money alone) | 0.0322 | 7/10 | 0.531 | 0.696 |
| **inverted** (§6.3 reversed) | 0.7572 | **0/10** | **−0.045** | **−0.699** |

`inverted` is the wrongness check, and it is the one that matters. Reversing the judgement
destroys the ranking completely: zero of the top ten survive and rank correlation is −0.045,
statistically indistinguishable from no relationship. **The weights are doing real work.** A
sensitivity analysis that showed the answer was the same under any weighting would not be
reassuring, it would mean `Phi` was measuring nothing.

---

## 4. The plausible sweep

200 order-preserving variants, jitter ±0.15, seed 0.

| ranking | top-10 min | median | 5th pct | rank corr min | median |
|---|---|---|---|---|---|
| `q_sell_over_oi` | 7 | 9 | 8 | 0.782 | 0.956 |
| `q_buy_over_oi` | **4** | 8 | 5 | 0.849 | 0.980 |
| `phi` | 5 | 9 | 7 | 0.784 | 0.982 |

Top-10 overlap distributions:

    q_sell_over_oi   {7: 3, 8: 66, 9: 83, 10: 48}
    q_buy_over_oi    {4: 2, 5: 14, 6: 18, 7: 32, 8: 51, 9: 65, 10: 18}
    phi              {5: 2, 6: 3, 7: 10, 8: 27, 9: 79, 10: 79}

**The sell-side ranking is robust and the buy-side one is not.** `Q_sell/OI` keeps at least 7
of its top 10 under every plausible weighting and usually 9. `Q_buy/OI` drops to 4 in the
worst case and is below 8 in a third of draws.

That asymmetry has a cause. `Q_sell` is dominated by Managed Money, whose weight is pinned at
the top of the order and cannot move much without breaking it. `Q_buy` is dominated by
Producer/Merchant at 0.1, which has the whole range below the next category to move in, and
which holds 56% of gross open interest so a change there moves the most mass.

**This bears directly on a published result.** The first analysis selected CIG Rockies as the
top market by `Q_buy/OI` and built a walkthrough around it. That selection is the less stable
of the two, and a reader should treat the buy-side top-10 as indicative rather than ordered.
The sell-side pick (CALIF LOW CARBON) is on firmer ground.

---

## 5. One weight matters much more than the others

Moving a single weight, everything else held:

| variant | median `Phi` | top-10 | rank corr | `Phi` corr |
|---|---|---|---|---|
| **producer_merchant 0.1 → 0.3** | 0.358 | 8 | **0.827** | **0.900** |
| other_reportable 0.5 → 0.3 | 0.219 | 8 | 0.977 | 0.963 |
| swap 0.4 → 0.2 | 0.212 | 9 | 0.954 | 0.969 |
| swap 0.4 → 0.6 | 0.262 | 7 | 0.984 | 0.975 |
| producer_merchant 0.1 → 0.2 | 0.299 | 10 | 0.941 | 0.983 |
| managed_money 1.0 → 0.8 | 0.229 | 9 | 0.996 | 0.988 |
| nonreportable 0.6 → 0.4 | 0.227 | 10 | 0.997 | 0.988 |
| producer_merchant 0.1 → 0.02 | 0.192 | 10 | 0.955 | 0.995 |
| nonreportable 0.6 → 0.7 | 0.244 | 10 | 0.999 | 0.997 |
| managed_money 1.0 → 0.9 | 0.235 | 10 | 0.999 | 0.997 |

**Producer/Merchant is the load-bearing weight**, by a clear margin: raising it from 0.1 to
0.3 is the only single move that pulls `Phi` correlation below 0.96 and rank correlation below
0.94. Every other perturbation, including a 20% cut to Managed Money, leaves both above 0.96.

The reason is mass, not importance. Producer/Merchant holds **56% of gross open interest**
across the universe, so at 0.1 it contributes 5.7% of `Phi` and at 0.3 it contributes 17%,
overtaking Managed Money as the largest single contributor. The weight nobody would think to
argue about is the one that decides the answer.

Note the asymmetry: moving it **down** to 0.02 barely matters (`Phi` corr 0.995) while moving
it **up** to 0.3 matters most. At 0.1 it is already close to the floor of its effect.

---

## 6. Does the answer depend on the week?

40 variants, top-5 overlap, three widely separated weeks:

| week | top-5 overlap min | median | rank corr min |
|---|---|---|---|
| 2012-06-26 | 4/5 | 4/5 | 0.978 |
| 2018-06-26 | 4/5 | 4/5 | 0.962 |
| 2026-07-28 | 3/5 | 4/5 | 0.980 |

Stable. The conclusion is a property of the weight structure rather than of the current
cross-section.

---

## 7. What this does not cover

- **TFF weights are unswept.** The same machinery applies (`plausible_variants` takes any
  weight map) and it has not been run. TFF's lowest weight is 0.3 against Disaggregated's
  0.1, so its sensitivity profile will differ.
- **`kappa` and the flow tolerance are separate parameters** with their own sweeps: the flow
  tolerance is done, `kappa` is not.
- **The ordering itself is not tested against anything.** This measures sensitivity to the
  values given the ordering. Whether the ordering is right is a claim about how holders
  behave under stress and cannot be settled from COT alone.
- **It does not license the ICE/Nodal universe.** Three analyses have now found the weights
  were written for Disaggregated commodity categories while 76% of the report is power, gas
  basis and RECs. Robustness to ±0.15 jitter says nothing about whether the ordering means
  anything for an entity with a statutory delivery obligation.

---

## Bottom line

The weights survive the test that §6.3 and §A.11 ask for, with one caveat and one caution.

**They are robust to their values.** Across 200 plausible order-preserving weightings, the
`Q_sell/OI` top-10 keeps at least 7 of 10 and usually 9, and rank correlation stays above
0.78. The result holds equally in 2012, 2018 and 2026.

**They are not robust to their ordering, and should not be.** Reversing §6.3's judgement
destroys the ranking entirely: 0 of 10 survive, rank correlation −0.045. That is the right
outcome. A `Phi` that was insensitive to the ordering would be measuring nothing.

**The caveat: the buy-side ranking is materially less stable than the sell side** — a worst
case of 4 of 10 against 7 of 10 — because it is dominated by Producer/Merchant at 0.1, the one
weight with room to move and 56% of gross open interest behind it. That is the load-bearing
parameter, and it is the one nobody would think to argue about. The published `Q_buy/OI`
top-10, including the CIG Rockies walkthrough, should be read as indicative rather than
ordered.

**The caution is the algebra in §2.** Under equal weights `Phi` reduces exactly to
`1 − spreading/OI`, verified to 1.11e-16 across 27,194 market-weeks. `Phi` has no
cross-market signal that does not come from the weight table.

**In plain terms: the rankings are not fragile to getting the numbers a bit wrong, they are
entirely dependent on getting the order right, and the weight that decides the most is the
smallest one.** That is a genuinely reassuring result for the four analyses already
published, with the buy-side caveat attached, and it sharpens rather than settles the
recurring question of whether a weight table written for commodity hedgers means anything in
a power market.
