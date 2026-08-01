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

> **This file is CLOSED to new sections.** Three numbering collisions in one afternoon
> (A8/A9, A13/A14, A19/A20) because several sessions append here in parallel and none can see
> another's uncommitted numbering. The convention from 2026-08-02 is **one dated amendments
> file per day**, matching the dating that `docs/analysis/` already uses: start
> `amendments-YYYY-MM-DD.md` rather than extending this one. Cross-file references use the
> file date plus the section, as `2026-08-01 §A15`.
>
> Sections A1-A22 keep their numbers, which are cited from commit messages and module
> docstrings and must not move again.
>
> **Before appending, `grep '^## A' this file` and take the next free number.** Sections are
> numbered by position and several sessions append here in parallel, so "the next number"
> guessed from memory collides. It has happened twice: A8/A9 (riskunits versus extremity) and
> A13/A14 (volume versus composite), both caught after the fact and renumbered. Numbers are
> cited from commit messages and module docstrings once published, so the section that landed
> first keeps its number and the later one moves.

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
| A.5 | ~~stress-conditioned `V`, the volume-spike trap, `T = Q/(kappa V)`~~ | **built 2026-08-01**, see [A13](#a13-volume-was-in-the-store-all-along-under-a-parameter-named-for-the-front-month) |
| A.5 | ~~square-root impact `I = Y σ sqrt(Q/V)`, Amihud `Λ`~~ | **built 2026-08-01**, see [A19](#a19-exit-cost-and-exit-duration-rank-markets-almost-independently) |
| A.6 | ~~liquidity commonality `β̄`, `T_eff = T(1 + γβ̄)`~~ | **built 2026-08-01.** It cannot feed §A.9 as written, see [2026-08-02 §A1-A2](amendments-2026-08-02.md) |
| A.7 | ~~trigger solver, volatility trigger, forced flow~~ | **built 2026-08-01** (`futures/trigger.py`). `A` was never needed, see [2026-08-02 §B8](amendments-2026-08-02.md) |
| A.7 | the fitted replication model, and the trend-following FRACTION of Managed Money | a search, so a `SearchSpaceLog`. SG Trend / BTOP50 for §9.2 target 1 is genuinely absent |
| A.8 | reflexivity amplification `1/(1 - ℓg)` | ~~A.5 and A.7~~ **both built.** Needs `ℓ` and `g`, estimable from the pieces now in place |
| A.9 | ~~the composite `D = C x I x Φ`~~ | **built 2026-08-01**, see [A15](#a15-taking-a9-literally-leaves-phi-doing-almost-none-of-the-work). Uses `T`, not `T_eff` |
| A.10 | unwind-versus-repricing classification during a drawdown | ~~returns~~ **nothing**: `riskunits.sigma_series` serves propadj returns per symbol, so residual correlation and dispersion are computable. Unchecked, not blocked |

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

---

## A13. Volume was in the store all along, under a parameter named for the front month

**Contradicts:** `pressure.py`'s header ("`V` does not exist in this workspace"), the A.5 and
A.6 rows of the not-built table above, `README.md`'s note on `core/impact.py`, and two test
docstrings. All of them said the same thing, and all of them were wrong in the same way: they
described a data gap where there was a naming problem.

**What was actually there.** `cotdata.get_prices` takes `volume="front"` or
`volume="reconstructed"`, documented as "continuous front-month volume" and "true market
volume (first + second expiring contract)". The second reads like the fuller series. It is
the narrower one: `Volume_Reconstructed = FirstVolume + SecondVolume`, exactly two expiries,
while the plain `Volume` field spans the whole curve.

Two independent measurements establish that `front` is whole-market:

**1. Open interest matches the CFTC to the contract.** The price files carry an
`Open Interest` column Norgate collects from the exchange; the CFTC collects its own from
clearing members. Against COT total-market open interest for the same Tuesday:

| | |
|---|---|
| Exact agreement | **25 of 26 markets** |
| Palladium | 0.998 |
| Median ratio | **1.000** |

Two vendors and two collection paths cannot agree that precisely unless both are measuring
the whole market. Front-month data would be a fraction.

**2. Curve concentration orders exactly as contract structure predicts.** First two
contracts' share of `Volume`, trailing 500 days:

| | share | |
|---|---|---|
| ZN, ES | **1.00** | quarterly financials, everything in the front |
| 6E, PL, SI, GC | 0.95-0.998 | metals and FX, nearly all in the active month |
| HG, CT, ZW | 0.80-0.87 | |
| ZC, ZS, SB, ZL, ZM | 0.67-0.76 | ags, spread across crop months |
| RB, HO | 0.57-0.61 | |
| CL, NG | **0.52-0.54** | energy, spread across the strip |

A front-month series would read 1.00 everywhere. Crude's total is nearly **twice** its first
two contracts, so `Volume` cannot be front-month-only.

**Why the distinction is not cosmetic.** `Q` from COT covers all expiries. Using
`reconstructed` would understate the denominator by 48% in natural gas, 46% in crude and 0%
in ES, so `T` would be wrong by a different factor in every market, which is worse than a
constant bias. `volume.py` raises on it rather than documenting it.

**Coverage is not the constraint.** All 47 symbols have volume, median 100% of available
bars, history to 1977-79. Worst coverage is 6N at 94.8%.

**And it changes the answer.** If `T` ranked markets the way the `Q/OI` proxy does, the join
would be decoration. Rank correlation on the latest week is **0.585**: Class III Milk sits
19th by `Q/OI` and 2nd by `T`. `T` ranges 0.80 to 10.6 days, median 3.5.

**One finding that shapes how to read the output.** §A.5's stress-conditioned denominator
sounds strictly more cautious. It is not: **9 of 25 markets trade MORE under stress** (lumber
1.62x calm ADV, copper 1.35x, coffee 1.21x), so `T_stress` is *shorter* there. Cotton (0.70),
wheat (0.64) and soybean oil (0.72) go the other way, and their stress `T` is materially
longer: cotton runs 7.1 days calm against 10.2 stressed. Both figures are emitted and neither
is labelled the answer, because which one binds is a property of the market rather than of the
method.

---

## A14. "25 of 279 markets" is coverage of the tradeable universe, not a 9% sample

**Contradicts:** how the 25-market join was framed when first measured, including by this
session, as a limitation to be noted beside any result.

It is not a limitation. **The other 254 are markets that are not traded**: too expensive, no
liquidity, no access. A5 already measured what that universe is made of, and the two facts fit
together directly: 213 of the 279 (76%) are ICE Energy Div and Nodal power and gas basis
contracts rather than classic outrights. A monitor that covered all 279 would be spending most
of its coverage on ERCOT and PJM basis swaps.

So the correct statement is that **the volume join reaches every market in the tradeable
universe**, and the markets it does not reach are ones no position is held in. A ranking over
the 25 is not a sample of the 279; it is the population that matters, and the 279-market
rankings in `docs/analysis/` are the ones that need the caveat, not this.

This is the second time a coverage figure in this stack has been reported as a shortfall and
then withdrawn: the "42 of 95 joinable, 44%" headline in
`../cotdata/docs/design/crowdmon_step2_normalisation.md` was withdrawn for the same reason,
once it turned out all 42 deployed markets joined. Worth naming as a pattern. **A coverage
ratio whose denominator nobody chose is not a measurement of anything**, and the denominator
here is "every market the CFTC publishes", which was never the target.

## A15. Taking §A.9 literally leaves `Phi` doing almost none of the work

**Concerns:** appendix §A.9, which contradicts itself mildly. Its preamble says "each term
expressed as a percentile of its own history so the product is dimensionless"; its formula
wraps `C` and `I` in `pct()` and writes `Phi` out in full. The formula was taken literally,
on instruction. This records what that costs, because the choice is worth making on purpose.

**Measured** across 20,938 scored market-weeks, 27 markets:

| factor | correlation with `D` | mean | std | min | max |
|---|---|---|---|---|---|
| `illiquidity_sell` | 0.857 | 0.455 | 0.308 | 0.006 | 1.000 |
| `crowding_long` | 0.796 | 0.510 | 0.313 | 0.006 | 1.000 |
| `phi` | **0.145** | 0.368 | **0.082** | 0.176 | 0.699 |

The mechanism is structural, not empirical. `C` and `I` are percentiles and therefore uniform
on `[0, 1]` with a standard deviation near 0.29. `Phi` is a raw share of gross open interest,
which is a stable property of a market's participant mix: it spans 0.18 to 0.70 with a
standard deviation of 0.082. **Two terms vary roughly four times as much as the third**, so
`D` is close to `C x I` with a mild fragility tilt.

**The package is named for the term the literal reading nearly removes.**

**Resolved 2026-08-01: `Phi` is now percentile-ised**, following §A.9's preamble rather than
its formula. Measured before and after:

| reading | crowding | illiquidity | fragility | coverage |
|---|---|---|---|---|
| literal, raw `Phi` | 0.796 | 0.857 | **0.145** | 77.0% |
| preamble, `pct(Phi)` | 0.585 | 0.681 | **0.401** | 77.0% |

All three standard deviations land near 0.31. `phi_percentile=False` restores the literal
form, and both `phi` and `phi_pct` are emitted under either reading so the output says which
produced it.

**Coverage is unchanged**, which is not obvious: `pct(Phi)` needs a three-year window where
raw `Phi` needs none, but `C = pct(z)` already needs two stacked windows (§A16) and remains
the binding constraint.

Note for anyone reading a `Phi` percentile: a **constant** `Phi` percentile-ises to about
0.5, not 1.0, because tied values take their average rank. A market whose participant mix
never changes sits in the middle of its own distribution.

## A16. `C = pct(z)` costs four years of warm-up, and removes 2008 from the replay list

**Adds** a consequence of §A.9's `C = pct(z_t)` that neither §A.4 nor §A.9 states.

`C` stacks two trailing three-year windows: `z` needs three years of position history, and
its percentile needs three years of `z`. Measured on the real panel:

    data begins   2006-06-13
    first z       2008-06-03
    first D       2010-05-25
    warm-up       3.9 years

**The composite cannot score anything before 2010-05-25**, so the 2008 GFC is unreachable and
module spec §10's replay list loses the most useful episode on it. Reading `C` as `pct(x_t)`
instead (which `extremity` already emits as `net_risk_usd_pct`) would halve the warm-up, and
is a different formula rather than an optimisation.

## A17. `D` falls during an unwind, because `Q` leaves with the crowd

**Adds** an interpretive point that module spec §10's framing invites getting backwards. The
spec asks the composite to "elevate **before** the drawdown rather than coincidentally with
it", which is right, but the corollary is stronger than it sounds: `D` should be expected to
*fall* during the event.

**Measured**, March 2020, against the 2019 mean:

    crowding_long        0.4635  ->  0.5339    1.15x
    illiquidity_sell     0.3634  ->  0.3435    0.95x
    dtl_sell             4.4762  ->  3.5994    0.80x
    adv                 159,028  -> 170,044    1.07x

`T = Q/(kappa V)` fell from both ends at once: volume rose 1.07x and `Q` shrank as positions
were liquidated. Mean `D_sell` ran 1.18x baseline in the four months before, 0.75x during, and
0.89x after.

This is **not** §A.5's volume-spike trap, which `volume.py` closes by construction using
trailing aggregates rather than spot readings. It is the slower version, running through a
252-day average and compounded by the numerator genuinely shrinking. `D` describes a
pre-condition and decays as the position it describes leaves, which is correct behaviour and
not a defect.

**None of the above is a validation.** Hand-chosen windows, computed after the fact, by the
session that wrote the measure, on three reachable episodes. A real validation is
pre-registered and runs through `crucible`.

## A18. Concentration risk is a power and REC phenomenon, not a commodities one

**Adds** a measurement behind module spec §6.2, which introduces CR4/CR8 as "the metric set
that COT gives away free" and does not say what it shows. Published in every Disaggregated
and TFF file, **zero percent null across twenty years and all 279 markets**, and unused until
2026-08-01.

**Measured** on the latest week, CR4 on the more concentrated side:

    median 53.8    10th 29.4    90th 78.3    max 100.0

Four traders hold a median 53.8% of one side. The maximum is not a rounding artifact: in NJ
RECs Class 2 V2026 four traders hold the **entire** net short side.

**But the classic outrights are all diffuse**, and none is in the crowded-and-forceable cell:

| market | CR4 | quadrant |
|---|---|---|
| WHEAT-SRW | 8.6 | broad_and_forceable |
| CORN | 9.8 | broad_and_forceable |
| CRUDE OIL | 13.7 | diffuse_and_patient |
| SOYBEANS | 15.6 | broad_and_forceable |
| GOLD | 34.5 | broad_and_forceable |

Of the 64 markets that are both concentrated and fragile (both above the week's cross-
sectional median), **55 (86%) are ICE Energy Division or Nodal Exchange**, topped by renewable
energy certificates. Six sit on the classic exchanges.

This is the third finding pointing at the same gap. The fragility weights were written for
Disaggregated commodity categories, and the ICE/Nodal universe is 76% of the report
([A5](#a5-the-disaggregated-universe-is-mostly-power-and-gas-basis)). Whether "forceable"
means anything for an entity with a statutory delivery obligation is a question §6.3's weights
were never designed to answer.

**CR4 also falls with market size** (median 61.8 in the smallest open-interest quartile
against 36.0 in the largest), so a raw cross-market CR ranking is close to a ranking on
smallness and needs either a size control or the against-own-history form.

**Levels and history say opposite things**, which is the practical consequence. Soybeans at
CR4 15.6 is diffuse in absolute terms and sits at the **98th percentile of its own three
years**; a REC market at 100.0 is extreme absolutely and ordinary against itself. Five of the
six markets currently most extreme against own history are ags on the short side, which is
exactly the shape module spec §5.4 warns will appear as a seasonal artifact. Seasonal
adjustment is still unbuilt, so that reading is unresolved.
---

## A19. Exit cost and exit duration rank markets almost independently

**Adds** a measurement behind appendix §A.5, which gives both `T = Q/(kappa V)` and
`I = Y sigma sqrt(Q/V)` without saying how much the two differ in practice. The answer is: as
much as it is possible to differ.

Measured on the latest week, 25 markets:

| | |
|---|---|
| rank correlation, `T` vs square-root impact | **0.031** |
| exit cost range | 46 to 350 bps, median 106 |
| `Q/V` range | 0.16 to 2.11 days of total volume |

Near-orthogonal, and the mechanism is plain once stated: **`T` carries no volatility and the
cost is multiplicative in it.** Cotton has the longest days-to-liquidate in the set (7.1) and
the fourth-highest cost, because its daily vol is 1.8%. Cocoa exits in 1.5 days and costs the
third most, because its vol is 4.6%.

| market | `T` (days) | cost (bps) | daily sigma |
|---|---|---|---|
| FCOJ | 4.4 | **350** | 4.96% |
| Coffee | 4.3 | 251 | 3.65% |
| Cocoa | **1.5** | 189 | 4.61% |
| Cotton | **7.1** | 164 | 1.79% |
| Silver | 1.4 | 123 | 3.13% |

**Consequence.** Reporting one and not the other loses most of the information. A monitor that
ranked only on `T` would put cotton at the top and cocoa eleventh; ranking only on cost
reverses them. Both are emitted.

**Neither is the composite's `I` term.** §A.9 defines `I = pct(T_eff)`, so `composite.py` is
right to use the duration percentile. The square-root law is §A.5's *cost of forcing the
exit*, reported beside `D` rather than inside it.

## A20. Amihud without the contract multiplier is a different ranking, not a rescaled one

**Adds** a constraint the appendix's `Lambda = <|r_t| / dollar volume_t>` does not state,
because in equities it does not arise: a share's dollar volume is price times shares, and
there is no multiplier to forget.

In futures the multiplier spans four orders of magnitude across this universe (cocoa 10, RBOB
gasoline 42,000), and prices are quoted in whatever unit the contract trades in: dollars per
gallon for RBOB, cents per pound for copper. Dropping the multiplier therefore does not scale
Amihud, it **reorders it**:

| | |
|---|---|
| rank correlation, with vs without the multiplier | **0.500** |
| markets moving more than five places | **8 of 25** |

Cocoa reads 20th of 25 without it and 5th with it. RBOB gasoline reads illiquid without it and
is among the most liquid markets in the set at $20bn a day.

The correct ordering is the plausible one: orange juice ($40m/day), lumber ($18m/day) and
Class III Milk ($66m/day) are the illiquid markets, gold ($103bn/day) and crude ($73bn/day)
the liquid ones.

**Why this is a `raise` rather than a note.** A multiplier-free dollar volume is still
positive, still of roughly the right magnitude, and still produces a smooth-looking series.
Nothing downstream can detect it. `futures.impact.amihud_series` refuses a missing or
non-positive `point_value` outright, and `core.impact.amihud` documents the requirement on
the argument it cannot check.

Found while building A19: the first version of the measurement used price without the
multiplier and put heating oil and RBOB among the most illiquid markets in the store, which
is where it became obvious something was wrong.
## A21. `Phi` has no cross-market signal independent of the weight table

**Adds** an algebraic fact that reframes module spec §6.3 and appendix §A.2, and that neither
states. Set every weight to 1.0 and, because the Disaggregated category rows exclude
spreading:

    sum_c (L_c + S_c) = 2 . (OI - spreading)
    Phi_flat = 2(OI - spreading) / (2 . OI) = 1 - spreading / OI

**Verified to 1.11e-16 on all 27,194 market-weeks** of the twenty-year panel and on the
279-market latest week. Median `Phi_flat` is 0.9417.

So under equal weights `Phi` measures the spreading share and nothing else. **`Phi` is not a
measurement that the weights adjust; it is a weighted restatement of the category mix**, and
every cross-market difference in a real `Phi` comes from the weight table rather than from
positioning. Worth knowing before reading any `Phi` ranking, and it is also why
percentile-ising `Phi` in the composite mattered so much ([A15](#a15-taking-a9-literally-leaves-phi-doing-almost-none-of-the-work)):
the raw quantity has very little spread to begin with.

## A22. The weights are robust to their values, not to their ordering, and one matters most

**Discharges** module spec §6.3's requirement that weights be "subjected to sensitivity
analysis rather than presented as estimates" and appendix §A.11's "results should be reported
with sensitivity analysis across plausible weightings". Neither had been run, against four
published analyses that rank on `Phi`, `Q_sell` or `D`.

**Plausible class**: order-preserving jitter of ±0.15, since §6.3's judgement is an ordering
before it is a set of values. 200 variants, fixed seed.

| ranking | top-10 min | median | rank corr min |
|---|---|---|---|
| `q_sell_over_oi` | 7 | 9 | 0.782 |
| `q_buy_over_oi` | **4** | 8 | 0.849 |
| `phi` | 5 | 9 | 0.784 |

**Robust to values.** The sell-side top-10 keeps at least 7 of 10 under every plausible
weighting, and the result holds equally in 2012, 2018 and 2026.

**Not robust to ordering, correctly.** Inverting §6.3's order destroys the ranking: 0 of 10
survive, rank correlation −0.045, `Phi` correlation −0.699. A `Phi` insensitive to the
ordering would be measuring nothing.

**Producer/Merchant is the load-bearing weight.** Raising it from 0.1 to 0.3 is the only
single-weight move that pulls `Phi` correlation below 0.96 (to 0.900); a 20% cut to Managed
Money leaves it at 0.988. The reason is mass rather than importance: Producer/Merchant holds
**56% of gross open interest**, so at 0.1 it contributes 5.7% of `Phi` and at 0.3 it
contributes 17% and overtakes Managed Money. The weight nobody would think to argue about
decides the most.

**Consequence for a published result.** `Q_buy/OI` is the less stable ranking (worst case 4
of 10) precisely because it is dominated by Producer/Merchant. The
[2026-07-28 first-rankings](../analysis/2026-07-28-first-rankings.md) walkthrough selected
CIG Rockies as the top buy-side market; that selection should be read as indicative rather
than ordered. The sell-side pick is on firmer ground.

**Not covered**: TFF weights (same machinery, unrun), `kappa`, and whether the ordering itself
is right, which is a claim about holder behaviour that COT cannot settle.
