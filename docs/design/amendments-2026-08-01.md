# Spec amendments from the first engine build, 2026-08-01

Working agreement: measure, do not assume; if a measurement contradicts a doc, fix the doc
and say so. This records what the layer-3 build (flow decomposition, fragility, exit
pressure) measured against the real store and where it disagrees with what is written.

**Where the amendments need to land.** Two of the three affected statements are in
`cotdata/docs/design/crowdmon_futures_cot_module.md`, which lives in a sibling repo that is
a shared checkout currently clean on `main`. They are recorded here rather than applied
there, because editing another repo's working tree from this branch would leave uncommitted
changes on `main` in a checkout other sessions share, and the workspace notes that hazard
explicitly. **Apply them when the spec migrates into this repo** (see
[README.md](README.md)), or in a deliberate cotdata change.

Every figure below is reproduced by `docs/analysis/reproduce.py` against
`COTDATA_STORE=~/code/cotdata_store`, or by the offline fixtures in `tests/fixtures/`.

---

## A1. The Oct-Nov 2025 shutdown did not create a gap in report dates

**Contradicts:** the handoff's §3 rationale for gap handling ("Without this, the Oct–Nov
2025 shutdown reads as one enormous week of flow"). The module spec itself does not make
this claim; its §6.4 note correctly identifies the real gap sources as the pre-1992
fortnightly schedule and holiday shifts.

**Measured.** Disaggregated report dates run weekly and unbroken through the window:
2025-09-30, 10-07, 10-14, 10-21, 10-28, 11-04. CFTC published the backlog carrying the
correct as-of Tuesdays, so there is no hole to bridge. Flow magnitudes in the window are
ordinary — median absolute Managed Money `Δnet` of 1,951 to 5,811 contracts against a 2025
baseline of 4,056.

The only interruption is a 6-day interval to 2025-11-10 followed by an 8-day one to
2025-11-18, which is a Veterans Day shift (2025-11-11 fell on a Tuesday).

**Where the shutdown does land: the release date.** Every release date in the window carries
provenance `derived` — "the Friday after the Tuesday" — which is precisely the inference
`ingest/cot_adapter.py` documents as failing on backlog weeks. So:

- flow decomposition, which indexes on **report date**, is unaffected by the shutdown
- anything indexing on **release date** over Oct-Dec 2025 is resting on a guess, and must
  filter on `release_date_source` rather than trust the date

This strengthens rather than weakens the module spec §5.3 amendment. It is a second concrete
instance of the same point: the report-date series survived the shutdown intact and the
release-date series did not.

## A2. Gaps come from thin markets falling out of the report

**Amends:** module spec §6.4's note, which attributes non-7-day intervals to the pre-October
1992 fortnightly schedule and to holiday shifts. Both are real, and on the **Disaggregated**
report (2006+, so entirely post-fortnightly) there is a third source it does not mention,
and that source produces the only intervals large enough to matter.

**Measured** across the full Disaggregated history, 27 markets, 27,167 transitions:

| interval | count | cause |
|---|---|---|
| 7 days | 26,574 | normal |
| 6 or 8 days | 570 | holiday shifts, in matched pairs |
| 14 to 294 days | 23 | **a market dropping below the reporting threshold** |

Of the 23 long intervals, 22 are oats (`004603`) and one is lumber (`058644`). Oats has a
**294-day** interval ending 2025-09-09 and five more over 50 days. A thin market vanishes
from the report when it falls below the reportable threshold and returns when it recovers.
Without a gap rule, that single difference enters every ranking as the largest weekly flow
in the sample.

**Consequence for the rule as specified.** The strict reading (difference only across
exactly 7 days) is implemented and is the default. It labels 2,965 rows `gap` on the liquid
panel, of which **2,850 are the 6-and-8-day holiday pairs** — real weeks of flow, discarded.
Admitting them means comparing a 6-day move against an 8-day one, roughly a 30% difference
in span. Neither choice is free, so `config.GAP_DAYS_TOLERANCE` is a parameter (default 0)
and `days_elapsed` is always emitted rather than assumed.

## A3. Phi is not usually a Managed Money story

**Contradicts:** the handoff's §4 expectation that "one category dominates (Managed Money
typically will)". The module spec §6.3 makes no such claim, so this amends the handoff only.

**Measured** on the 279-market latest week. Managed Money is the largest contributor to the
Phi numerator in **81 markets (29%)**, not the typical case:

| top Phi contributor | markets |
|---|---|
| managed_money | 81 |
| producer_merchant | 70 |
| other_reportable | 56 |
| swap | 48 |
| nonreportable | 24 |

The median largest contributor accounts for only 44% of the Phi it sits in. The mechanism:

| category | mean share of gross OI | weight | mean Phi contribution |
|---|---|---|---|
| producer_merchant | 0.5648 | 0.1 | 0.0565 |
| swap | 0.1324 | 0.4 | 0.0529 |
| other_reportable | 0.1018 | 0.5 | 0.0509 |
| managed_money | 0.0627 | 1.0 | 0.0627 |
| nonreportable | 0.0520 | 0.6 | 0.0312 |

Producer/Merchant holds 56% of gross open interest and contributes 5.7% of Phi; Managed
Money holds 6% and contributes 6.3%. **At the configured weights, Phi is approximately a
balance between the hedgers who are large but immovable and the funds who are small but
forced.** That is a property of the weight set rather than a discovery about markets, and it
is worth stating in §6.3 because it is not obvious from the weight table and it changes how
a Phi value should be read.

`fragility.contributions` exists so this is checkable per market rather than assumed.

## A4. The producer-short / fund-long shape holds in about half the universe

**Amends:** the cocoa worked example's implied generality (appendix §A.2). The example itself
has since been read and reproduced exactly, see
[A6](#a6-the-plain-language-summary-was-found-and-the-implementation-matches-it); its shape
is Producer/Merchant net **short** 110,000 against Managed Money net **long** 90,000, so the
characterisation this section was originally checked against was accurate.

**Measured** on the 279-market latest week. Producer/Merchant is net **long** in 141 markets
(50.5%) and net short in 138 (49.5%). Managed Money is net long in 43.0%, net short in
41.9%, and exactly flat in 15.1%:

| category | net long | net short | flat |
|---|---|---|---|
| managed_money | 43.0% | 41.9% | 15.1% |
| producer_merchant | 50.5% | 49.5% | 0.0% |
| swap | 48.4% | 49.8% | 1.8% |
| other_reportable | 43.4% | 52.7% | 3.9% |
| nonreportable | 56.6% | 38.4% | 5.0% |

The template's shape describes a market where a physical producer sells forward. In a gas
basis or power market the entity hedging physical frequently buys, and the sign flips. Both
walkthroughs in `docs/analysis/` show one case each, and they are structural opposites.

**Any rule that assumes producers are short and funds are long is a coin flip on this
universe.** Keeping `Q_sell` and `Q_buy` separate is what surfaces it rather than averaging
it away, which is the strongest argument for the directional split.

## A5. The Disaggregated universe is mostly power and gas basis

**Adds** context absent from the spec, which discusses ags, metals and energy outrights
throughout. Of the 279 markets in the latest Disaggregated report, **213 (76%) are ICE
Futures Energy Division or Nodal Exchange** — power hubs, gas basis, carbon allowances,
renewable energy certificates.

This matters most for module spec §7 (cross-market engine). A PCA on positioning changes
across "all Disaggregated markets" would produce a PC1 describing ERCOT and PJM, not the
macro book, and the trend-alignment score would inherit the same population. §7 should state
which universe it means before it is built.

## A6. The plain-language summary was found, and the implementation matches it

**Resolved 2026-08-01.** `crowdmon_plain_language_summary.md` now lives in
[`docs/design/`](crowdmon_plain_language_summary.md). It was written before this build and
was not in the workspace while the build ran, so every formula here was taken from the
handoff body instead. The appendix is authoritative, so the whole thing needed re-checking
against it.

**It checks out.** The appendix's own worked example (§A.2 cocoa, §A.5 continued) is now
executed as a test rather than read, in [`tests/test_appendix.py`](../../tests/test_appendix.py),
and every figure reproduces:

| §A.2 / §A.5 says | implementation gives |
|---|---|
| `Q_sell = 99,500` | 99,500 |
| `Q_buy = 11,000` | 11,000 |
| `Phi = 175.5/400 = 0.44` | 0.438750 |
| MM numerator share `110,000 of 175,500` | 110,000 of 175,500 |
| `T = 99,500/(0.2 x 25,000) ~ 20 days` | 19.9 |
| unweighted MM comparison, 18 days | 18.0 |

The weight table in `core.config.DISAGGREGATED_WEIGHTS` is identical to §A.2's, and
`Q_sell`, `Q_buy`, `Phi` and `T = Q/(kappa V)` are all as written. Nothing had drifted.

**Two places where the appendix is right about its example and wrong about real data**, both
already handled in code but now traceable to the authoritative source rather than to the
handoff:

- **§A.1 asserts `sum L_c = sum S_c = OI`, and §A.2 that gross positions total "exactly
  `2 . OI`".** True in the example, which has no spreading. False on real Disaggregated
  data, where spreading counts toward open interest but is excluded from `L_c` and `S_c`, so
  the sums fall short by exactly the spreading and gross totals `2(OI - spreading)`. `Phi`
  is therefore bounded by a *reachable ceiling* below 1, which `market_fragility` emits as
  `phi_denominator_covered` (0.9715 for `0063CU`, 0.9791 for `02339S`). The bound `Phi
  ∈ [0,1]` still holds, and more tightly than the appendix claims.
- **§A.2 says a single category dominating the numerator is "typical".** Measured false, see
  [A3](#a3-phi-is-not-usually-a-managed-money-story): Managed Money is the top contributor in
  81 of 279 markets (29%), and the median top contributor carries 44% of the Phi it sits in.
  This now contradicts the *authoritative* document rather than the handoff, which raises its
  standing: it is the one place where the appendix generalises from its own constructed
  example and the generalisation does not survive contact with the report.

**One labelling correction.** The handoff cites "flow decomposition (appendix A.3)". §A.3 is
primarily the **breadth-depth** decomposition, with flow decomposition as a sub-section of
it. Both are there, so the citation is loose rather than wrong, but a reader going to A.3 for
the four-state table will find the `ΔP = N̄Δq + q̄ΔN + ΔNΔq` identity first.

**On that identity:** §A.3 writes `N̄` and `q̄` and calls the decomposition "exact". Exactness
requires those to be the *prior period's* values, not period means, since
`N₁q₁ - N₀q₀ = N₀Δq + q₀ΔN + ΔNΔq` is an algebraic rearrangement while a mean-based version
leaves a residual. `breadth.decompose_breadth` uses the prior week and asserts the residual
is zero to floating point, which is the reading that makes the appendix's own claim true.

### What the appendix specifies that is not built yet

Recorded here because the appendix is the fullest statement of the target and several of
these are cheaper than they look:

| § | Not built | Blocked on |
|---|---|---|
| A.4 | ~~extremity, rolling 3y z-score of vol-scaled notional~~ | **built 2026-08-01**, see [A10](#a10-winsorising-damages-extremity-and-the-appendix-is-right-not-to-ask-for-it) |
| A.5 | square-root impact `I = Y σ sqrt(Q/V)`, Amihud `Λ`, stress-conditioned `V`, the volume-spike trap | **volume**, which does not exist in this workspace |
| A.6 | liquidity commonality `β̄`, `T_eff = T(1 + γβ̄)` | volume |
| A.7 | forced-seller model and trigger solver | prices + a CTA replication model |
| A.8 | reflexivity amplification `1/(1 - ℓg)` | A.5 and A.7 |
| A.9 | the composite `D = C x I x Φ` | all of the above |
| A.10 | unwind-versus-repricing classification during a drawdown | returns |

Worth flagging from §A.7: the trigger price for a simple momentum signal is just
`F* = F_{t-k}`, the price of `k` days ago. That is far cheaper than a numerical solve, and it
means a first-cut trigger level needs only prices, not the full replication model.

§A.11 lists four known biases, of which the first matters most for reading anything this
package emits: **`T` is a lower bound on pain, not an estimate of it**, because `V` is
endogenous and the model treats it as exogenous. Every days-to-liquidate figure this system
ever prints will be systematically optimistic.

## A7. Flow decomposition now exists twice

`cotdata/vintage_flow.decompose` (built 2026-07-30) and `crowdmon.futures.flow`
(this build) both implement module spec §6.4 over the same canonical schema. They resolve
the spec's "~0" differently:

| | `cotdata.vintage_flow` | `crowdmon.futures.flow` |
|---|---|---|
| rule | dominant leg, parameter-free | dominant leg + dominance tolerance |
| `mixed` state | none, always commits | yes, 60% of weeks on the liquid panel |
| gap handling | emits `days_elapsed`, caller filters | `gap` state, deltas nulled |
| `fuel_remaining` | no | yes, on short covering |

Both are defensible. The tolerance-based one can decline to name a direction, which the
parameter-free one cannot, and 60% of liquid-panel weeks are two-sided enough to trigger it.

**This duplication is real and should be resolved rather than left.** The measured
tolerance-sensitivity result (see `docs/analysis/`) is relevant to the choice: across
0.15-0.40, 28.7% of week labels change, but **zero** change from one pure state to a
different pure state. The tolerance controls whether the classifier commits, never which
direction it commits to, which is structural — the dominant leg is `argmax|Δ|` and does not
depend on the tolerance. So the two implementations never disagree about direction; they
disagree only about how often to say "neither".

---

## A8. Volatility needs `propadj`, not `backadj`. My own earlier claim was wrong

**Contradicts:** `notional.py`'s module docstring and the old `futures/__init__.py`
paragraph, both of which said the volatility factor of `net_notional x sigma` should come
from the back-adjusted series "because only that carries correct returns". Also the rationale
(not the check) in `ContractMaster.coverage`, and two test docstrings.

**Does not contradict the module spec.** §5.1 already said continuous series should be
"built ratio-adjusted (not difference-adjusted) so returns are correct". The spec was right
and the consumer-side prose I wrote on top of it was wrong.

**Measured.** Additive back-adjustment preserves absolute daily price CHANGES, not
percentage returns. It folds roll gaps into the historical level, which corrupts the
denominator of every historical return and, on long-history contracts, drives the level
through zero. Annualised volatility from `pct_change`, full history:

| Market | via `backadj` | via `propadj` | inflation | `backadj` closes <= 0 |
|---|---|---|---|---|
| DC (Class III Milk) | 9.9e13 % | 9.2% | 1.1e13 x | 41.2% |
| ZS (soybeans) | 4366.9% | 21.7% | **201 x** | 52.3% |
| ZN (10-year note) | 1183.1% | 6.5% | **182 x** | 8.9% |
| CT (cotton) | 889.0% | 23.9% | 37 x | 2.6% |
| CL (crude) | 676.1% | 63.4% | 11 x | 0.6% |
| NG (natural gas) | 157.0% | 53.4% | 2.9 x | 0.0% |
| **GC (gold)** | **8.8%** | **18.9%** | **0.47 x** | **0.0%** |

Gold is why this became a hard refusal rather than a documented preference. It never goes
negative, so it survives every screen for a non-finite or absurd number, and its volatility
is still wrong by a factor of two in the *understating* direction. A markets-wide "implausible
volatility" check would clear it and flag nothing.

`unadj` fails in the opposite shape, and it is the shape that matters for this module.
Full-sample volatility barely notices the roll jumps (GC 1.01x, ZN 1.02x, ZS 1.05x), so a
whole-history check passes, while the contamination sits on a few dozen days and wrecks any
*short* window spanning one. On a 63-day window, peak inflation is 9.84x (DC, 2004-03-31),
2.93x (NG), 2.07x (LE), 1.57x (GC); crude's worst single roll day fabricates a **130.7%**
move. For DC, 95.8% of all 63-day windows are inflated by more than 25%.

> The 130.7% is measured **on roll dates only**, and the restriction matters. Crude's worst
> unadjusted move over all days is 306%, on 2020-04-21, coming off the negative settlement.
> That one is a real price crossing zero, not a roll artifact. A first draft of both the
> reproducer and `test_unadjusted_returns_carry_a_fabricated_jump_at_every_roll` took an
> unrestricted maximum, which meant the test would have kept passing even if roll
> contamination vanished entirely, since the 2020 sign change alone satisfied it. Both are
> now pinned to `cotdata.roll_dates`.

**Cross-check.** Dollar volatility per contract-unit is reachable two independent ways:
`unadj_price x sigma_pct(propadj)`, and `std(diff(backadj))`, the latter being exactly what
additive adjustment does preserve. On mid-history dates they agree within 2-10% (GC 1.023,
CL 0.968, ZS 0.958, ZN 0.981, DC 1.099, ES 1.005, 6E 1.002, KC 0.939). Two different series
and two different transformations landing on one number is the evidence that `propadj`
returns and `unadj` levels compose into a real dollar quantity.

**Applied in this PR** to `riskunits.py`, `notional.py`, `futures/__init__.py`,
`contract_master.py` and two test docstrings. Asserted in `tests/test_riskunits_live.py`.

**Not a change to `ContractMaster.coverage`'s check**, only to its stated reason. Requiring
both `unadj` and `backadj` is still correct, because `propadj` is *derived on read* by
cotdata from those two (`cotdata.prices._ratio_adjust`). Both stored tiers are the
precondition for the one derived tier. Same check, sounder reason.

---

## A9. `propadj` is not strictly positive, and cotdata's own docstring says otherwise

**Contradicts:** `cotdata/src/cotdata/prices.py`, `_ratio_adjust`: "A ratio-adjusted series
preserves percentage returns and stays strictly positive." Recorded here rather than edited,
same reason as the header of this document: cotdata is a shared checkout currently clean on
`main`.

**Measured.** Ratio adjustment scales each segment by a positive factor, so it *preserves*
the sign of the underlying series rather than imposing one. Across all 47 symbols in the
store, `propadj` has exactly **one** non-positive close anywhere: crude on **2020-04-20**,
where the unadjusted settlement was -37.63 and the propadj close is -24.11. The docstring's
claim holds wherever the underlying market stayed positive, which is everywhere except the
one day WTI did not.

This is the third time this session's lineage has re-made the same assumption. The first
version of `test_notional_live.py` asserted the *unadjusted* series could never be negative;
that was corrected. The first version of `_sigma_series` then raised on any non-positive
close in a `propadj` series, which meant refusing to compute a volatility for crude at all,
across its entire 43-year history, over one real day in 2020. The live test caught it.

**Resolution, and why it is a rate and not a presence test.** The two cases are three orders
of magnitude apart with nothing in between:

| | non-positive rate |
|---|---|
| `propadj`, CL (a real settlement) | **0.009%** (1 of 10,882) |
| `propadj`, all other 46 symbols | 0% |
| `backadj`, ZS | 52.3% |
| `backadj`, DC | 41.2% |
| `backadj`, ZN | 8.9% |

`MAX_NONPOSITIVE_RATE = 0.01` sits in that empty gap. Below it, the returns *touching* a
non-positive close are masked (undefined from a negative base, undefined across a sign
change) and the market keeps its volatility everywhere else. Above it, the series is not what
it claims to be and `_sigma_series` raises.

**Consequence for anything downstream:** a price series being negative is not evidence of a
wrong series, in any of the three adjustments. Only the *rate* is.

---

## What did not need amending

Worth recording, because a spec that survives contact is as much a result as one that does
not.

- **The canonical schema.** First real consumer, no changes needed.
- **The open-interest identity** (module spec §4 amendment, `Σ long == Σ short`, and
  `Σ long + spreading == OI` for Disaggregated). Holds **exactly** on 27,194 market-weeks
  over 2006-2026 and on 21,756 market-weeks across 346 markets in the vintage store. Zero
  exceptions, no tolerance required, stable in every single year.
- **§5.3's release-date discipline and the `derived` warning.** Confirmed by A1 above.
- **§6.4's core claim** that separating short covering from fresh conviction is high value
  for almost no code. The 2026-07-07 week in `02339S` is a clean real instance: `Δnet` of
  +9,809 that reads as aggressive buying and is a short position being closed, with a
  finite, published fuel supply visible beforehand.
- **§6.3's weights** produce a bounded, well-behaved Phi across the whole history. A3 is
  about how to *read* it, not about the weights being wrong.

## A10. Winsorising damages extremity, and the appendix is right not to ask for it

**Contradicts:** module spec §6.1, "Rolling z-score and percentile of vol-scaled net
notional, per market per category, 3-year window, **winsorised**." Appendix §A.4 gives the
plain `z_t = (x_t − μ_W)/s_W` and specifies no winsorisation. The appendix is authoritative,
so it wins on precedence alone; what makes this an amendment rather than a footnote is that
the measurement independently agrees.

**Why it misfires here.** Winsorising assumes the values it clips are outliers. In
positioning data they are usually the top of a **build**, because positions accumulate over
months rather than spiking for a week. Clipping them removes the build itself, shrinks the
scale, and manufactures a score the data does not support.

**Measured**, worst case in twenty years, Platinum / Other Reportable / 2026-01-27. The
trailing window's six largest values are a monotone run-up ending at the current point
(31.5m, 47.1m, 47.6m, 54.4m, 55.7m, 62.5m):

| | mean | std | z |
|---|---|---|---|
| raw | 9,815,959 | 8,590,872 | **6.13** |
| winsorised 5% | 8,493,972 | 2,444,729 | **22.10** |

The standard deviation shrinks 3.5x and the score nearly quadruples on identical data.
Panel-wide:

| winsor | median abs z | 99th | max | share above 6 |
|---|---|---|---|---|
| **0.00** | 0.85 | 3.65 | **9.6** | 0.05% |
| 0.05 | 0.91 | 4.31 | 22.1 | 0.32% |
| 0.10 | 1.00 | 5.46 | 27.4 | 0.75% |

`core.aggregate.DEFAULT_WINSOR = 0.0`. The parameter is kept, because a genuinely spiky
series would benefit from it, and it defaults off.

**The percentile is unaffected at any setting**, since ranks ignore the magnitude of the
tails (platinum reads 1.0000 either way). That is the strongest argument for §6.1's own
instruction that the *percentile* is what should be reported: the one free parameter in the
module touches only the secondary number.

## A11. Extreme positioning readings persist far longer than a percentile implies

**Adds** a measurement behind module spec §11 item 7 ("positioning extremes persist for
quarters"), which the spec states as a caution and which is directly quantifiable.

Over 117,940 scored market-weeks, 27 markets, 2006-2026:

    share above the 95th percentile:  10.11%   (nominal 5%)
    share below the  5th percentile:   8.90%   (nominal 5%)

Twice the nominal rate, because the readings are serially dependent. Consecutive-week
episodes above the 95th percentile, counted per market-category:

| | |
|---|---|
| episodes | 2,477 |
| mean run length | 4.8 weeks |
| median | 3 weeks |
| 90th percentile | 12 weeks |
| longest | 42 weeks |
| share of hot weeks inside runs of 8+ weeks | **57.6%** |

**A 95th-percentile reading is not a one-in-twenty event; it is the middle of an episode.**
The direct consequence for anything downstream: percentile exceedances are not independent,
so work that treats "weeks above the 95th" as a sample size has an effective sample roughly a
fifth of its nominal one. That is `crucible`'s problem rather than this package's, but the
measurement belongs where it was made.

It also confirms the measure behaves as intended. An indicator that flickered in and out week
to week would be describing noise.

## A12. Extremity cannot run on the breadth panel, and this is permanent

**Adds** a constraint the spec does not state. Module spec §6.1 specifies a 3-year window;
the vintage store begins 2025-01-07 and holds about nineteen months. So extremity runs only
on `io.from_current_store` (**27 markets**, 2006 onward) and never on the 346-market vintage
panel that `fragility` and `flow` use.

`extremity.add_extremity` raises on a too-short panel rather than returning an all-null
column, because a column of nulls does not say why it is null.

Breadth and depth are in different places and stay there. Any cross-market work combining
extremity with fragility is combining a 27-market measure with a 279-market one, and the
intersection is the 27.
