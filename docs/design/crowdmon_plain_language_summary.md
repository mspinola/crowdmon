# Crowded Positioning in Futures Markets

**A plain-language summary**

Companion to `crowdmon_futures_cot_module.md` (the technical specification). This document explains the same ideas without jargon, for readers who want to understand the reasoning rather than build the system.

---

## The idea

In futures, every position has someone on the other side of it — for every contract someone owns, someone else has sold it. So it is never possible for "everyone" to be on one side. What makes a market fragile isn't which side has more contracts. It's **who** is holding, and what would force them to leave.

A farmer who has sold corn futures to lock in a price for his harvest cannot be forced out. If the price moves against him, he shrugs — he owns the actual corn, and the whole point of the hedge was to fix his price. Nothing can make him buy back that position in a hurry.

A leveraged fund holding the same position is a different animal. It borrowed to take the position, it has rules about how much it can lose, and its investors can ask for their money back. If the price moves against it far enough, it doesn't *decide* to exit. Its risk rules exit for it.

That distinction is what this whole system is built around. **Damage comes from three things multiplied together:**

- how concentrated the position is,
- how hard it is to trade out of,
- and how many holders can be forced out against their will.

The third term is the one that decides who actually gets hurt.

---

## Why this is measurable

Every week, the U.S. futures regulator publishes exactly how many contracts each type of participant holds in each market: commercial hedgers, speculative funds, dealers, small traders. Both long and short. Plus how many individual traders are in each group, and how concentrated the biggest holders are.

That is a genuine census of positioning, published every week, for free. And because futures are a closed system, the totals are exact rather than estimated.

Alongside it, the exchanges publish exact daily trading volume. So you can put a real number on both halves of the problem: how big the crowd is, and how wide the door is.

**The critical arithmetic is the ratio.** If speculative funds hold 200,000 contracts and the market trades 100,000 contracts a day, they can't all leave at once. You can't realistically be more than about a fifth of a day's trading without moving the price against yourself, so at that rate the exit takes ten days. Ten days of everyone selling into the same market is not an orderly exit. It's a rout.

Two things make it worse than that sounds:

- Trading volume during a panic isn't the calm-market volume you measured. It is often worse exactly when you need it most, because buyers step back.
- The cost of forcing a trade rises with volatility. The same exit costs far more during turmoil than in quiet conditions.

---

## The part that is genuinely predictable

A large share of speculative futures money runs on rules rather than opinions. These funds follow trends: they buy what has been rising and sell what has been falling. And they size positions by volatility, holding less of anything that is moving around a lot.

Those rules are public knowledge and can be modelled. Which means you can work backwards and ask: **at what price does the trend rule flip from buy to sell?**

That is the whole thing. You get a specific price level where a large, identifiable pool of money becomes a forced seller — and you can estimate how many contracts, and what it will cost to move them.

The volatility rule adds a second trigger that catches people out. Because these funds hold less when markets are turbulent, a sharp rise in volatility forces selling **regardless of which direction prices went**. A violent up-day can force liquidation just as a down-day can.

---

## A worked example

*Hypothetical, and deliberately extreme. §A.2 in the appendix works a real market (live cattle, report week 2026-07-28) through the same arithmetic; this one is here because an extreme case is easier to follow. Cocoa itself does not currently show this configuration.*

Suppose cocoa has been rising for eight months on genuine supply problems in West Africa. Real story, real shortage.

**What the positioning data shows.** Speculative funds are net long 90,000 contracts, the highest reading in five years. But the more revealing figure is the trader count — it is *falling* while the position grows. The same funds are holding progressively larger positions rather than new participants arriving.

The crowd isn't broadening. It is concentrating and levering up. That is the fragile configuration. The concentration figures confirm it: the four largest traders hold a growing share of the long side.

**What the liquidity data shows.** Cocoa trades perhaps 25,000 contracts on an average day, and during the rally the market has thinned out — many natural sellers have already sold. Against that volume, 90,000 contracts is under four days of *total* market turnover. But a seller cannot be the whole market: at a realistic participation rate of a fifth of daily volume, the same 90,000 contracts takes about 18 trading days to unwind.

And cocoa has daily price limits: on a limit-down day, trading effectively stops. You cannot exit at any price. That is a door that doesn't just narrow — it closes.

**What the trigger model shows.** Working backwards through the trend rules gives the level: the medium-term signal flips if cocoa falls about 9% from here. Estimated forced selling on that flip is roughly 35,000 contracts, which is 1.4 days of total market turnover.

That figure understates it, because the forced sellers cannot be the entire market: somebody has to be taking the other side, and the traders being stopped out are not available to absorb each other. Hold them to a fifth of daily volume and the same 35,000 contracts takes about seven trading days to clear, arriving all at once, into a market with price limits.

**The point is not that cocoa will fall.** The supply problem may be entirely real and prices may keep climbing for another year.

The point is that *if* it falls 9% for any reason at all — a decent rain forecast, a demand downgrade, nothing in particular — the mechanical selling that follows is far larger than the market can absorb. So the move won't stop at 9%. Somewhere around there, the reason prices are falling stops being cocoa and starts being the exit.

And this is knowable in advance, from public data, before anything happens.

---

## What it cannot tell you

**It cannot tell you when.** Positioning can sit at an extreme for months and keep going. The crowd being large is not a reason for it to be wrong.

So this doesn't generate trades. It changes how you hold them:

- smaller size in fragile markets,
- exit on positioning rather than on price where you can, and use defined-risk protection (a long put, a spread) wherever gap risk is real,
- and a strong prior against adding to a position at the exact moment the exit is most congested.

The middle one used to read "wider stops, because tight ones get blown through". That is wrong, and wrong in a way worth stating plainly: **a stop is a trigger, not a guarantee.** It converts to a market order when touched, and in a gapping or limit-locked market that order fills wherever the market next trades, which may be far below the level you named. A stop in a stampede fires *because* the cascade happened, not before it, so widening it does not buy protection, it only moves where you find out.

Widening does change one thing, and it is a trade-off rather than an improvement: a wide stop keeps you in a positioning unwind, which is the case that usually reverts, and it costs you more in a fundamental repricing, which is the case that persists. Which one you are in is exactly the question §A.10's classification answers, and it is answerable while the drawdown is happening.

It also tells you something useful *during* a crash — whether prices are falling because the facts changed, or because everyone is trying to leave at once. Those look identical while they are happening and they end very differently. The first is a reason to reconsider the position. The second usually reverses, once the forced sellers are done.

---

## The one-sentence version

Crowding on its own is harmless. It becomes dangerous when the crowd is large relative to the exit, and when enough of the crowd can be forced through that exit whether they want to go or not.

---
---

# Appendix — The same argument, formally

> Every formula below is implemented, and the worked examples are executed rather than read
> ([`tests/test_appendix.py`](../../tests/test_appendix.py)). The thread through §A.2, §A.5,
> §A.7 and §A.9 is one **real** market at a stated report week, recomputed from the store by
> that test and by `docs/analysis/reproduce.py` (`appendix_a2_worked_example`); the
> constructed figures kept beside it are labelled as constructed everywhere they appear.
> Implementation notes and measured amendments live in
> [`amendments-2026-08-01.md`](amendments-2026-08-01.md) and
> [`amendments-2026-08-02.md`](amendments-2026-08-02.md); anyone building from this appendix
> should read those alongside it.


Each section below corresponds to a claim made above. Nothing new is introduced; the plain-language statements are simply written in a form that can be computed.

## A.0 Notation

| Symbol | Meaning | Units |
|---|---|---|
| $L_c, S_c$ | long / short contracts held by category $c$ | contracts |
| $P_c = L_c - S_c$ | net position of category $c$ | contracts |
| $OI$ | total open interest | contracts |
| $N_c$ | number of traders in category $c$ | count |
| $q_c = P_c / N_c$ | average position per trader | contracts |
| $M$ | contract multiplier | units per contract |
| $F$ | futures price | currency per unit |
| $\sigma$ | daily return volatility | dimensionless |
| $V$ | average daily volume | contracts |
| $\kappa$ | participation rate (share of volume one can take) | dimensionless, $\approx 0.2$ |
| $w_c$ | fragility weight of category $c$ | $[0,1]$ |

---

## A.1 "Every position has someone on the other side"

The closed-system property, which is why net imbalance alone says nothing:

$$\sum_c L_c = \sum_c S_c = OI \qquad\Longrightarrow\qquad \sum_c P_c = 0$$

Any statement of the form "the market is long" is therefore vacuous. The quantity that varies is not the net, but its distribution across categories with different exit constraints.

## A.2 "What matters is who is holding" — fragility

Assign each category a constraint weight $w_c \in [0,1]$: the probability that a holder in that category exits involuntarily under stress.

| Category (Disaggregated report) | $w_c$ | Rationale |
|---|---|---|
| Managed Money | 1.0 | Vol targets, margin, drawdown limits, redemptions |
| Non-Reportable (small traders) | 0.6 | Retail; small but least resilient per unit |
| Other Reportable | 0.5 | Mixed |
| Swap Dealer | 0.4 | Hedged, but balance-sheet constrained |
| Producer / Merchant / Processor | 0.1 | Hedging physical; can stand for delivery |

Weights are configured judgement, not fitted estimates — see A.11.

**Forced exit size must be split by direction.** Forced longs sell; forced shorts buy. Summing them into one figure produces a number that corresponds to no actual flow:

$$Q_{\text{sell}} = \sum_{c\,:\,P_c > 0} w_c P_c \qquad\qquad Q_{\text{buy}} = \sum_{c\,:\,P_c < 0} w_c |P_c|$$

These are the numerators for everything that follows. Note this is *not* position size — it is position size filtered by who can be made to leave.

**Fragility share.** Since $\sum_c P_c = 0$, nets cannot form a share of anything. Use gross positions, whose total is exactly $2 \cdot OI$:

$$\Phi = \frac{\sum_c w_c \,(L_c + S_c)}{2 \cdot OI} \;\in [0,1]$$

which reads as the average fragility of a randomly chosen position-side. The farmer and the leveraged fund can hold identical contract counts and enter this sum ten times apart.

### Worked example: live cattle, report week 2026-07-28

Real CFTC values, Disaggregated, released 2026-07-31. $OI = 298{,}449$ contracts:

| Category | Long | Short | Net $P_c$ | Gross $L_c+S_c$ | $w_c$ |
|---|---|---|---|---|---|
| Producer / Merchant | 41,461 | 140,446 | **−98,985** | 181,907 | 0.1 |
| Swap Dealer | 68,622 | 7,026 | +61,596 | 75,648 | 0.4 |
| Managed Money | 84,907 | 17,882 | **+67,025** | 102,789 | 1.0 |
| Other Reportable | 13,899 | 36,601 | −22,702 | 50,500 | 0.5 |
| Non-Reportable | 25,614 | 32,548 | −6,934 | 58,162 | 0.6 |

**Forced selling** (net-long categories):

$$Q_{\text{sell}} = 1.0(67{,}025) + 0.4(61{,}596) = 91{,}663.4$$

**Forced buying** (net-short categories):

$$Q_{\text{buy}} = 0.5(22{,}702) + 0.1(98{,}985) + 0.6(6{,}934) = 25{,}409.9$$

**Fragility share:**

$$\Phi = \frac{1.0(102{,}789) + 0.6(58{,}162) + 0.4(75{,}648) + 0.5(50{,}500) + 0.1(181{,}907)}{2 \times 298{,}449} = \frac{211{,}386.1}{596{,}898} = 0.354$$

**Reading the result.** The asymmetry is the entire point: 91,663 contracts of forced selling face 25,410 of forced buying, a ratio of 3.61. The short side is cattle feeders and packers hedging physical animals, who can stand for delivery and will not cover in a panic. The long side is a levered fund book, plus a swap book that is constrained but not forced. Same open interest, different behaviour depending on which way the market breaks.

None of this is visible in the headline net figure. "Managed Money net long 67,025" says nothing about who is on the other side or whether they can be forced to move.

**Two things this real example shows that a constructed one would not.**

*The weight decides, not the size.* Producer/Merchant carries by far the largest net on the short side at −98,985, and contributes **less to $Q_{\text{buy}}$ than Other Reportable does** (9,898.5 against 11,351.0), whose net is a quarter of the size at −22,702. That inversion is the whole content of the weighting: a big position that cannot be forced out is not exit pressure.

*The fragile side is not one category.* $Q_{\text{sell}}$ is Managed Money plus a Swap Dealer book 74% as large in gross terms, which enters at $w = 0.4$ and so contributes 24,638 of the 91,663. Managed Money carries 48.6% of the $\Phi$ numerator here, the largest single share but not a takeover. Measured across the full Disaggregated universe, Managed Money is the top $\Phi$ contributor in only 29% of markets, so a single category dominating is **not** typical and $\Phi$ should be read beside its contributions rather than alone. This is why $\Phi$ deserves sensitivity analysis across plausible weightings rather than being quoted to two decimals (A.11).

### The constructed extreme, retained

The following table is **hypothetical and near-maximal**, built to make the asymmetry as visible as possible. It was previously presented here as though it were typical, which it is not. It is kept because an extreme case is a useful thing to see, and it is the example the main text's cocoa narrative refers to.

| Category | Long | Short | Net $P_c$ | Gross $L_c+S_c$ | $w_c$ |
|---|---|---|---|---|---|
| Producer / Merchant | 40,000 | 150,000 | −110,000 | 190,000 | 0.1 |
| Swap Dealer | 30,000 | 20,000 | +10,000 | 50,000 | 0.4 |
| Managed Money | 100,000 | 10,000 | **+90,000** | 110,000 | 1.0 |
| Other Reportable | 20,000 | 15,000 | +5,000 | 35,000 | 0.5 |
| Non-Reportable | 10,000 | 5,000 | +5,000 | 15,000 | 0.6 |
| **Total** | 200,000 | 200,000 | 0 | 400,000 | |

$$Q_{\text{sell}} = 0.4(10{,}000) + 1.0(90{,}000) + 0.5(5{,}000) + 0.6(5{,}000) = 99{,}500$$

$$Q_{\text{buy}} = 0.1(110{,}000) = 11{,}000 \qquad\qquad \Phi = \frac{175.5}{400} = 0.44$$

**Where it sits.** $Q_{\text{sell}}/Q_{\text{buy}} = 9.045$. That ratio is bounded above by $\max(w)/\min(w) = 10.0$, a property of the weight table rather than of any market, so the example stands at **90.5% of the mechanical ceiling**. It is attainable: 54 of 21,756 measured market-weeks reach it, across 14 markets, mostly power and gas basis but including eight outright market-weeks in copper, coffee, RBOB, canola and spring wheat. It is the 99.75th percentile of the classic outrights. The live cattle example above, at 3.61, is the 70th percentile: above the middle, and nowhere near the bound.

### How common is this shape?

Measured over 82 vintage weeks, 346 markets, 21,756 market-weeks (amendments B28, B31, B32, B33, B34):

| stratum | template (hedger short, fund long) | inverted | same side | no directional pair | market-weeks |
|---|---|---|---|---|---|
| classic outright | 44.7% | 25.0% | 26.5% | 3.7% | 3,214 |
| power/gas/carbon venue | 26.8% | 25.6% | 32.7% | 14.8% | 16,365 |

"No directional pair" is a market where one of the two categories is flat or absent, so the shape is inexpressible rather than false.

Four things a reader should carry away, none of which invalidate the construction above:

- **It is a commodity claim.** On the financial (TFF) report the mirror configuration, a stable long side facing a fragile short one, is 77.3% of open interest and this shape is 3.8%. The forced flow there is buying.
- **The hedged short side is the robust half; the fund side is not.** Among classic outrights Producer/Merchant is net short in 69.2% of market-weeks and Managed Money net long in 50.0%.
- **That 50.0% is a coin flip in sign, not in size.** Managed Money holds 64.9% of its contracts on the long side, and its median position is 13.9% of open interest when long against 7.2% when short. The fund is present and large in both directions; it is not absent.
- **Direction is incidental to the mechanism.** Measured without a direction, $\max(Q)/\min(Q)$ has a median of 3.02 across all market-weeks and under 5% of them are genuinely balanced. The signed median of 0.993 reported in B31 is direction cancelling, not symmetry.

The shape is also a property of particular markets rather than of a given week: metals 66.5% of market-weeks, softs 52.4%, grains 38.2%, and every crude oil and natural gas code in the store at zero.

## A.3 "Concentrating rather than broadening" — the breadth–depth decomposition

Since $P = N q$ exactly, the weekly change in a category's position decomposes as:

$$\Delta P = \bar{N}\,\Delta q \;+\; \bar{q}\,\Delta N \;+\; \Delta N \Delta q$$

- $\bar{N}\Delta q > 0$ with $\Delta N \le 0$ — **existing holders levering up**. Narrow and deep. This is the cocoa configuration.
- $\bar{q}\Delta N > 0$ with $\Delta q \approx 0$ — **crowd broadening**. Wide and shallow.

Identical $\Delta P$, opposite fragility. The decomposition is exact and requires only data already published.

**Flow decomposition** separates a further ambiguity, using the fact that $\Delta P = \Delta L - \Delta S$:

| $\Delta L$ | $\Delta S$ | Interpretation |
|---|---|---|
| $> 0$ | $\approx 0$ | new longs — fresh conviction |
| $\approx 0$ | $< 0$ | short covering — **finite fuel**, ends when $S \to 0$ |
| $\approx 0$ | $> 0$ | new shorts |
| $< 0$ | $\approx 0$ | long liquidation |

A rally with $\Delta S < 0$ has a hard upper bound on its remaining fuel, namely $S$ itself. A rally with $\Delta L > 0$ does not.

## A.4 "Comparable across markets" — normalisation

Raw contract counts are not comparable across time or markets. The ladder, in increasing usefulness:

$$\underbrace{P}_{\text{contracts}} \;\to\; \underbrace{\frac{P}{OI}}_{\text{share}} \;\to\; \underbrace{P \cdot M \cdot F}_{\text{notional}} \;\to\; \underbrace{P \cdot M \cdot F \cdot \sigma}_{\text{risk units}}$$

The final form — vol-scaled notional — is the one that corresponds to what forces deleveraging, since risk limits are denominated in risk, not in contracts.

Extremity is then reported as a rolling standardised score over a 3-year window $W$:

$$z_t = \frac{x_t - \mu_{W}(x)}{s_{W}(x)}, \qquad x_t = P_t M_t F_t \sigma_t$$

and surfaced as a percentile of its own history, since raw levels are not comparable across markets.

## A.5 "How wide is the door" — exit capacity

**Days to liquidate.** If you can absorb at most a fraction $\kappa$ of daily volume without becoming the tape:

$$T = \frac{Q}{\kappa V}$$

*Live cattle, continued.* Carrying $Q_{\text{sell}} = 91{,}663.4$ from A.2, with a measured $V = 75{,}328.6$ contracts/day and $\kappa = 0.2$:

$$T_{\text{sell}} = \frac{91{,}663.4}{0.2 \times 75{,}328.6} = \frac{91{,}663.4}{15{,}065.7} = 6.08 \text{ days}$$

$$T_{\text{buy}} = \frac{25{,}409.9}{15{,}065.7} = 1.69 \text{ days}$$

Six days against under two. That gap, not either number alone, is what the directional split exists to show: a break downwards has more than three times the exit to clear than a break upwards.

Using the *unweighted* Managed Money net of 67,025 instead would give 4.45 days, against 6.08 weighted. The two diverge here because the swap book adds 27% of $Q_{\text{sell}}$, which is the general case; they coincide only where a single category dominates $Q$, and the weighted figure is the meaningful one either way.

*The constructed extreme, continued.* Carrying $Q_{\text{sell}} = 99{,}500$ with an assumed $V = 25{,}000$ gives $T = 99{,}500 / 5{,}000 \approx 20$ days: a month of forced selling in a market that has already thinned. That is 3.3 times the live cattle reading, on a $Q/OI$ of 0.50 against 0.31 into a market a third the size. This is the shape the measure exists to flag. Note both use calm-market volume; the stress conditioning below revises it, and not always downwards.

**Cost of forcing the exit.** The square-root impact law:

$$\mathcal{I} = Y \, \sigma \sqrt{\frac{Q}{V}} \qquad (Y \approx 0.5 - 1.0)$$

Two consequences follow directly from the functional form:

- Impact is *multiplicative* in $\sigma$. Crowding and volatility compound rather than add — which is why these episodes are short and deep rather than long and shallow.
- Impact is concave in $Q$. Doubling the crowd raises the cost by $\sqrt{2}$, not $2$. Size alone is not the problem; size relative to $V$ is.

**Spread and impact proxies** where only daily data exists — Amihud illiquidity:

$$\Lambda = \left\langle \frac{|r_t|}{\text{dollar volume}_t} \right\rangle$$

**Stress conditioning.** Calm-market $V$ overstates capacity, so the denominator is taken over the worst decile of market days:

$$V_{\text{stress}} = \text{median}\big(V_t : t \in D_{10}\big), \qquad D_{10} = \text{worst 10\% of market days}$$

**It does not always cut the other way.** Live cattle's worst decile trades *more* than its average day (87,874 against 75,329), so $T_{\text{sell}}$ falls to 5.22 days under stress conditioning rather than rising. That is a real property of markets where the bad days are the busy days: measured, **9 of 25 markets trade more under stress**, and it is why $V_{\text{stress}}$ is reported beside $V$ rather than substituted for it. Treating the stress figure as automatically the conservative one is wrong on more than a third of the tradeable universe.

**The volume-spike trap.** During a selloff $V_t$ rises sharply, so a naively computed $T_t = Q/(\kappa V_t)$ *falls* — the monitor reports improving liquidity precisely as liquidity is being consumed. The denominator must therefore be frozen to a calm-regime baseline during flagged stress windows, with realised $V_t$ surfaced separately as a diagnostic rather than allowed into the ratio.

## A.6 "Individual doors may be the same door" — commonality

Per-market exit times cannot simply be added, because liquidity co-moves. Regress each market's liquidity change on the basket average:

$$\Delta \Lambda_{i,t} = \alpha_i + \beta_i \, \Delta \Lambda_{M,t} + \varepsilon_{i,t}$$

and use $\bar\beta$ as a multiplier on aggregate exit pressure:

$$T_{\text{eff}} = T \cdot \big(1 + \gamma \bar{\beta}\big)$$

$\bar\beta \to 0$ means independent exits and the individual $T_i$ are meaningful. $\bar\beta \to 1$ means every exit closes at once, and the aggregate is worse than the sum of its parts. This term is what distinguishes *crowded-and-liquid* from *crowded-and-illiquid*.

## A.7 "Rules rather than opinions" — the forced-seller model

Systematic position size as a function of signal and volatility:

$$q_i = \underbrace{s_i(F)}_{\text{trend signal}} \cdot \underbrace{\frac{\sigma_{\text{target}}}{\sigma_i}}_{\text{vol targeting}} \cdot \underbrace{\lambda(\Sigma)}_{\text{portfolio scaling}} \cdot A$$

with $s_i \in [-1, 1]$ a squashed blend of time-series momentum over lookbacks $k \in \{20, 60, 250\}$ days, and $A$ estimated aggregate capital.

**Trigger price.** For a simple momentum signal $s = \operatorname{sign}(F_t - F_{t-k})$, the flip condition is immediate:

$$F^{*} = F_{t-k}$$

The price at which a large pool of capital becomes a forced seller is simply the price of $k$ days ago. For smoothed or blended signals, solve $s_i(F^*) = 0$ numerically. Forced flow on the flip:

$$Q^{*} = A \cdot \frac{\sigma_{\text{target}}}{\sigma} \cdot \Delta s$$

and the cost of that flow follows from A.5.

*Live cattle, continued.* Spot is 231.75 on 2026-07-31 and the pool is **observed rather than modelled**: the Managed Money net of 67,025 contracts, taken from the COT itself. There is no $A$ to estimate, which removes the largest free parameter in the block and the governance hazard that comes with a calibrated replication model.

| lookback | flips at | from spot | signal now |
|---|---|---|---|
| 20d | 239.23 | +3.2% | short, flips up |
| 60d | 244.69 | +5.6% | short, flips up |
| 250d | 219.04 | **−5.5%** | long, flips down |

**The horizons disagree, and that is information rather than noise.** The short-dated signals are already short and would be forced to *buy* on a rally; only the 250-day pool is long, and it turns into a forced seller 5.5% below spot. "The trend book in live cattle" is not one pool with one trigger.

Taking the 250-day flip, with $V = 75{,}328.6$, $\kappa = 0.2$, $\sigma = 0.88\%$ daily and $Y = 0.75$:

$$T^{*} = \frac{67{,}025}{15{,}065.7} = 4.4 \text{ days} \qquad \mathcal{I} = 0.75 \times 0.0088 \times \sqrt{\frac{67{,}025}{75{,}328.6}} = 62\text{ bp}$$

if the pool merely closes. If it reverses to fully short, $\Delta s = 2$, the flow doubles to 134,050 contracts, 8.9 days, and 88 bp. Both figures are quoted because the factor of two is real and which one applies depends on whether the book goes flat or goes short.

**Volatility trigger, same market.** Realised volatility is 14.0% annualised. A five-point shock to 19.0% forces:

$$\frac{\Delta q}{q} = 1 - \frac{0.140}{0.190} = 26\%$$

a reduction of roughly 17,700 contracts from the Managed Money book, *independent of price direction*. Both triggers can fire in the same episode, and they compound.

*The constructed extreme, continued.* At the other end of the range: suppose a 60-day signal flips 9% below spot with $Q^{*} = 35{,}000$ against $V = 25{,}000$. Then $T^{*} = 7$ days, and at 2.5% daily volatility $\mathcal{I} = 0.75 \times 0.025 \times \sqrt{35{,}000/25{,}000} \approx 2.2\%$. The mechanical selling alone costs roughly 220 bp on top of whatever caused the initial move, which is the formal statement of "the move won't stop at 9%." A doubling of volatility from 2.5% to 5% would force a further 50%, around 45,000 contracts. The live cattle figures above are the same arithmetic on a market that is not in that state.

**The volatility trigger.** Because $q \propto 1/\sigma$:

$$\frac{\partial q}{\partial \sigma} = -\frac{q}{\sigma} \qquad\Longrightarrow\qquad \epsilon_{q,\sigma} = -1$$

Unit elasticity. A volatility move from $\sigma_0$ to $\sigma_1$ forces a proportional reduction of:

$$\frac{\Delta q}{q} = 1 - \frac{\sigma_0}{\sigma_1}$$

A doubling of volatility forces a 50% reduction **with no reference to price direction whatsoever**. This is the formal content of "a violent up-day can force liquidation just as a down-day can."

## A.8 "The reason prices are falling stops being cocoa" — reflexivity

Let an initial liquidation $Q_1$ move price by $\Delta F_1 = -\ell Q_1$, and let that move trigger further forced selling $Q_2 = g \, |\Delta F_1|$, where $g$ is the sensitivity of systematic supply to price. Total displacement over the cascade:

$$\Delta F_{\text{total}} = -\ell Q_1 \sum_{n=0}^{\infty} (\ell g)^n = \frac{-\ell Q_1}{1 - \ell g}$$

The amplification factor $\dfrac{1}{1-\ell g}$ is finite only while $\ell g < 1$.

- $\ell g \ll 1$ — an orderly repricing. The fundamental news is the story.
- $\ell g \to 1$ — the cascade dominates. The exit is the story.
- $\ell g \ge 1$ — no equilibrium in the model; in practice, price limits, margin hikes, or exhaustion of the fragile holders terminate it.

$\ell$ rises as liquidity thins and $g$ rises with $\Phi$ (A.2), so both terms move the wrong way at the same moment. This is why crowded markets do not fall by the size of the news.

**Price limits** enter as a hard constraint rather than a cost: on a limit day, executable volume is zero,

$$V_t = 0 \quad\Longrightarrow\quad T \to \infty$$

which is the difference between a narrow door and a closed one.

## A.9 "Damage comes from three things multiplied together"

Collecting the above, with each term expressed as a percentile of its own history so the product is dimensionless:

$$\mathcal{D} = \underbrace{C}_{\text{crowding}} \times \underbrace{I}_{\text{illiquidity}} \times \underbrace{\Phi}_{\text{fragility}}$$

$$C = \text{pct}\big(z_t\big), \qquad I = \text{pct}\big(T_{\text{eff}}\big), \qquad \Phi = \frac{\sum_c w_c (L_c + S_c)}{2 \cdot OI}$$

Multiplicative, not additive: if any single term is near zero, damage is near zero. A large position in a liquid market held by unconstrained hedgers is safe. A modest position in a thin market held entirely by levered vol-targeters is not.

*Live cattle, continued.* Against its own 2006-2026 history, at the same report week:

$$\mathcal{D} = \underbrace{0.057}_{C} \times \underbrace{0.204}_{I} \times \underbrace{0.146}_{\Phi\text{ pct}} = 0.0017$$

which is the **9.6th percentile of its own history**. The market carries the template shape in all 82 weeks measured, and its damage reading is near the bottom of its range.

That is not a contradiction, it is the multiplicative form doing its job. Shape is a statement about *who* holds; $\mathcal{D}$ is a statement about *how much*, relative to the exit and to this market's own past. Positioning happens to be light (the 67,025 Managed Money net is the smallest of the 82 weeks in the vintage store), so $C$ is near zero and takes the product with it whatever $\Phi$ says. A market can be perfectly template-shaped and perfectly safe.

*The constructed extreme, continued.* Positioning at a five-year extreme puts $C$ near the top of its range; $T \approx 20$ days against a thinning market puts $I$ high; $\Phi = 0.44$ with one category dominating. All three terms elevated simultaneously, which is the configuration the system exists to flag and is rarer than any one of them alone.

Report $\mathcal{D}$ as a percentile of its own history, never as an absolute level. The number has no meaning across markets; only its position within its own distribution does.

## A.10 "It cannot tell you when"

Formally, the system estimates a property of the conditional loss distribution, not its location:

$$\mathcal{D}_t \;\perp\; \mathbb{E}[r_{t+1}], \qquad \mathcal{D}_t \;\to\; \text{skew}(r_{t+1}),\;\; \text{ES}_\alpha(r_{t+1})$$

Crowding informs tail shape — expected shortfall, downside skew, gap risk — and carries no first-moment content. This is why every legitimate use is a sizing, structuring, or classification decision rather than a directional one, and why $\mathcal{D}$ must never be traded directly.

**Classification during a drawdown.** The two cases distinguish empirically:

| | Residual correlation | Dispersion | $\ell g$ | Base case |
|---|---|---|---|---|
| Positioning unwind | rises | falls | $\to 1$ | reverts |
| Fundamental repricing | flat | rises | $\ll 1$ | persists |

Falling dispersion with rising residual correlation means the market has stopped pricing individual facts and started pricing the exit.

## A.11 Known biases in these estimates

- **$T$ is a lower bound on pain, not an estimate of it.** $V$ is endogenous: realised capacity during an unwind depends on how many others are exiting, which is the quantity being measured. The model treats $V$ as exogenous and is therefore systematically optimistic.
- **$Q$ grows as the position loses.** A position moving against the holder grows in notional and in risk-unit terms with no trade, so required exit capacity rises super-linearly while available capacity falls.
- **$w_c$ are judgement, not estimates.** The fragility weights are configured, not fitted, and results should be reported with sensitivity analysis across plausible weightings.
- **Categories are not entities.** $P_c$ aggregates heterogeneous holders; a category-level net can mask offsetting books with quite different constraints.
