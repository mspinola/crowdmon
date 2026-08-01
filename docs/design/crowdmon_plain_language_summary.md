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

*Hypothetical, but built from realistic market structure.*

Suppose cocoa has been rising for eight months on genuine supply problems in West Africa. Real story, real shortage.

**What the positioning data shows.** Speculative funds are net long 90,000 contracts, the highest reading in five years. But the more revealing figure is the trader count — it is *falling* while the position grows. The same funds are holding progressively larger positions rather than new participants arriving.

The crowd isn't broadening. It is concentrating and levering up. That is the fragile configuration. The concentration figures confirm it: the four largest traders hold a growing share of the long side.

**What the liquidity data shows.** Cocoa trades perhaps 25,000 contracts on an average day, and during the rally the market has thinned out — many natural sellers have already sold. At a realistic exit rate, 90,000 contracts takes over two weeks to unwind.

And cocoa has daily price limits: on a limit-down day, trading effectively stops. You cannot exit at any price. That is a door that doesn't just narrow — it closes.

**What the trigger model shows.** Working backwards through the trend rules gives the level: the medium-term signal flips if cocoa falls about 9% from here. Estimated forced selling on that flip is roughly 35,000 contracts — a week and a half of normal volume, arriving all at once, into a market with price limits.

**The point is not that cocoa will fall.** The supply problem may be entirely real and prices may keep climbing for another year.

The point is that *if* it falls 9% for any reason at all — a decent rain forecast, a demand downgrade, nothing in particular — the mechanical selling that follows is far larger than the market can absorb. So the move won't stop at 9%. Somewhere around there, the reason prices are falling stops being cocoa and starts being the exit.

And this is knowable in advance, from public data, before anything happens.

---

## What it cannot tell you

**It cannot tell you when.** Positioning can sit at an extreme for months and keep going. The crowd being large is not a reason for it to be wrong.

So this doesn't generate trades. It changes how you hold them:

- smaller size in fragile markets,
- wider stops, because tight ones get blown through in a stampede,
- and a strong prior against adding to a position at the exact moment the exit is most congested.

It also tells you something useful *during* a crash — whether prices are falling because the facts changed, or because everyone is trying to leave at once. Those look identical while they are happening and they end very differently. The first is a reason to reconsider the position. The second usually reverses, once the forced sellers are done.

---

## The one-sentence version

Crowding on its own is harmless. It becomes dangerous when the crowd is large relative to the exit, and when enough of the crowd can be forced through that exit whether they want to go or not.

---
---

# Appendix — The same argument, formally

> Every formula below is implemented, and the worked examples are executed rather than read
> ([`tests/test_appendix.py`](../../tests/test_appendix.py)). Implementation notes and
> measured amendments live in [`amendments-2026-08-01.md`](amendments-2026-08-01.md) and
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

### Worked example — cocoa

Take $OI = 200{,}000$ contracts, with the positioning described in the main text:

| Category | Long | Short | Net $P_c$ | Gross $L_c+S_c$ | $w_c$ |
|---|---|---|---|---|---|
| Producer / Merchant | 40,000 | 150,000 | −110,000 | 190,000 | 0.1 |
| Swap Dealer | 30,000 | 20,000 | +10,000 | 50,000 | 0.4 |
| Managed Money | 100,000 | 10,000 | **+90,000** | 110,000 | 1.0 |
| Other Reportable | 20,000 | 15,000 | +5,000 | 35,000 | 0.5 |
| Non-Reportable | 10,000 | 5,000 | +5,000 | 15,000 | 0.6 |
| **Total** | 200,000 | 200,000 | 0 | 400,000 | |

**Forced selling** (net-long categories):

$$Q_{\text{sell}} = 0.4(10{,}000) + 1.0(90{,}000) + 0.5(5{,}000) + 0.6(5{,}000) = 99{,}500$$

**Forced buying** (net-short categories):

$$Q_{\text{buy}} = 0.1(110{,}000) = 11{,}000$$

**Fragility share:**

$$\Phi = \frac{0.1(190) + 0.4(50) + 1.0(110) + 0.5(35) + 0.6(15)}{400} = \frac{175.5}{400} = 0.44$$

**Reading the result.** The asymmetry is the entire point: roughly 99,500 contracts of forced selling face only 11,000 of forced buying. The short side is producers hedging physical harvest — they cannot be squeezed and will not cover in a panic. The long side is levered funds that can be made to sell. Same open interest, radically different behaviour depending on which way the market breaks.

None of this is visible in the headline net figure. "Managed Money net long 90,000" says nothing about who is on the other side or whether they can be forced to move.

Note also that Managed Money contributes 110,000 of the 175,500 fragility numerator — a single category dominates, which is typical, and is why $\Phi$ deserves sensitivity analysis across plausible weightings rather than being quoted to two decimals.

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

*Cocoa, continued.* Carrying $Q_{\text{sell}} = 99{,}500$ from A.2, with $V = 25{,}000$ contracts/day and $\kappa = 0.2$:

$$T = \frac{99{,}500}{0.2 \times 25{,}000} = \frac{99{,}500}{5{,}000} \approx 20 \text{ days}$$

Twenty trading days — a month — of forced selling in a market that has already thinned. Note this uses calm-market volume; the stress-conditioned figure below is worse.

Using the *unweighted* Managed Money net of 90,000 instead would give 18 days, which is close here only because that category dominates $Q$. Where fragility is spread more evenly the two diverge substantially, and the weighted figure is the meaningful one.

**Cost of forcing the exit.** The square-root impact law:

$$\mathcal{I} = Y \, \sigma \sqrt{\frac{Q}{V}} \qquad (Y \approx 0.5 - 1.0)$$

Two consequences follow directly from the functional form:

- Impact is *multiplicative* in $\sigma$. Crowding and volatility compound rather than add — which is why these episodes are short and deep rather than long and shallow.
- Impact is concave in $Q$. Doubling the crowd raises the cost by $\sqrt{2}$, not $2$. Size alone is not the problem; size relative to $V$ is.

**Spread and impact proxies** where only daily data exists — Amihud illiquidity:

$$\Lambda = \left\langle \frac{|r_t|}{\text{dollar volume}_t} \right\rangle$$

**Stress conditioning.** Calm-market $V$ overstates capacity, so the denominator is taken over the worst decile of market days:

$$V_{\text{stress}} = \text{median}\big(V_t : t \in D_{10}\big), \qquad D_{10} = \text{worst 10\% of market days}$$

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

*Cocoa, continued.* Suppose the 60-day signal flips at a price 9% below spot, and the model puts systematic supply on that flip at $Q^{*} = 35{,}000$ contracts. With $V = 25{,}000$ and $\kappa = 0.2$:

$$T^{*} = \frac{35{,}000}{5{,}000} = 7 \text{ days}$$

Seven days of normal volume, arriving at once — and that is only the trend-flip tranche, not the full $Q_{\text{sell}} = 99{,}500$. With daily volatility of, say, 2.5% and $Y = 0.75$:

$$\mathcal{I} = 0.75 \times 0.025 \times \sqrt{\frac{35{,}000}{25{,}000}} \approx 2.2\%$$

So the mechanical selling alone costs roughly 220 bp on top of whatever caused the initial 9% move. The forced flow is a material fraction of the total decline, which is the formal statement of "the move won't stop at 9%."

**Volatility trigger, same market.** If realised volatility doubles from 2.5% to 5% — plausible during a 9% break — vol targeting forces:

$$\frac{\Delta q}{q} = 1 - \frac{0.025}{0.05} = 50\%$$

a further reduction of roughly 45,000 contracts from the Managed Money book, *independent of price direction*. Both triggers fire in the same episode, and they compound.

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

*Cocoa, continued.* Positioning at a five-year extreme puts $C$ near the top of its range; $T \approx 20$ days against a thinning market puts $I$ high; $\Phi = 0.44$ with Managed Money dominating. All three terms elevated simultaneously — which is the configuration the system exists to flag, and is rarer than any one of them alone.

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
