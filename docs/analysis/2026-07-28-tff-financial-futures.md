# TFF: financial futures, week ending 2026-07-28

**Report** Traders in Financial Futures, futures-only, released 2026-07-31.
**Universe** 93 markets in the latest week, 111 over the panel (2025-01-07 onward).
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_tff.py`.
**Code** unchanged. Every engine ran on TFF as written; nothing in `src/` was touched for
this analysis.

The Disaggregated work ([first-rankings](2026-07-28-first-rankings.md)) found that 76% of
that universe is ICE Energy Division and Nodal power and gas basis, so a "cross-market"
result over it describes ERCOT and PJM rather than the macro book. **TFF is where the macro
book actually is**: rates, FX, equity index. This is the first look at it.

Three things had to be established before any number here could be trusted, and all three
are traps that would have produced confident wrong answers. They are §2. The findings are
§3 onward.

---

## 1. What is in here

| venue | markets |
|---|---|
| CHICAGO MERCANTILE EXCHANGE | 44 |
| COINBASE DERIVATIVES, LLC | 26 |
| CHICAGO BOARD OF TRADE | 18 |
| ICE FUTURES U.S. | 4 |
| CBOE FUTURES EXCHANGE | 1 |

Open interest is overwhelmingly rates. The nine-contract US rates complex alone carries
**40.5 million contracts**, 79% of all TFF open interest, against 6.9 million in equity
index, 2.9 million in FX and 0.9 million in crypto.

But **crypto is 33 of the 90 markets** and 26 of them are Coinbase "PERP STYLE" contracts.
By market count the report is a third crypto; by open interest it is 2%. Any unweighted
cross-market statistic over TFF is largely a statement about small crypto contracts, which
is the same shape of hazard as ICE Energy Div in the Disaggregated report and needs the same
care.

---

## 2. Three traps, all of which produce confident wrong answers

### 2.1 The "Consolidated" markets are aggregates, not markets

S&P 500, NASDAQ-100 and DJIA each appear **three times**: a full-size contract, a micro
contract at one tenth the size, and a "Consolidated" row. The consolidated row is not a
separate market. It is exactly the sum of the other two in full-size-equivalents:

| index | Consolidated | full-size + micro/10 | |
|---|---|---|---|
| S&P 500 | 2,007,178 | 1,984,408 + 227,701/10 = 2,007,178.1 | **exact** |
| NASDAQ-100 | 319,776 | 294,781 + 249,950/10 = 319,776.0 | **exact** |
| DJIA | 87,436 | 83,013 + 44,234/10 = 87,436.4 | **exact** |

Ranking across all 93 markets therefore counts S&P 500 open interest twice. Every table
below drops the three consolidated codes, leaving **90 markets**.

Worth knowing: the aggregation is exact at the open-interest level but **the category split
is not simply additive**. S&P 500 consolidated shows Asset Manager 1,160,957 against
1,159,241 + 17,159/10 = 1,160,956.9 (exact), but Dealer 166,249 against a component sum of
174,325 and Leveraged 150,572 against 161,175. Consolidation reclassifies some traders, most
likely because a trader small enough to be non-reportable in one contract crosses the
threshold when the two are combined. So the consolidated row is a real, separately computed
view rather than a mechanical sum, and it is still not an independent market.

### 2.2 The open-interest identity is exact except in those same three

On Disaggregated the identity holds **exactly**, 27,194 of 27,194 market-weeks. On TFF it
does not:

| market-weeks | unbalanced | rate | worst |
|---|---|---|---|
| 6,279 | 111 | 1.77% | **3 contracts** |

Every one of the 111 falls in `13874+` S&P 500 Consolidated (51 weeks), `20974+` NASDAQ-100
Consolidated (44) and `12460+` DJIA Consolidated (16), and every one is within CFTC's own
rounding tolerance. This is the `/10` division in §2.1 showing up as a rounding residual, not
a mapping fault. `cotdata` predicted exactly this and named the three markets before anyone
looked here.

**So the identity still works as a parse check on TFF**, provided the tolerance is used
rather than exact equality, and provided a break outside those three codes is treated as
real. `oi_identity` reports both `balanced` and `within_tolerance` for this reason.

### 2.3 Phi is not comparable across report types

This is the one that would do the most damage, because the number looks comparable.

| | median Phi | mean | max |
|---|---|---|---|
| TFF | **0.495** | 0.565 | 0.936 |
| Disaggregated | **0.240** | 0.254 | 0.619 |

TFF looks twice as fragile. Part of that is real and part is an artifact of the weight sets,
and the two have to be separated.

**The artifact.** The lowest weight in each set is different. Disaggregated has
Producer/Merchant at **0.1**, and that category holds 56% of gross open interest, so it acts
as a huge low-weight ballast dragging every Phi down. TFF's lowest weight is Asset Manager at
**0.3**. A market whose entire open interest sat in the least-forceable category available
would score 0.10 on Disaggregated and 0.30 on TFF. **Phi has a different floor in each
report, so the two scales do not correspond.**

**The real part.** Where the gross actually sits:

| TFF | share of gross | weight | mean Phi contribution |
|---|---|---|---|
| leveraged | 0.3113 | 1.0 | 0.3113 |
| dealer | 0.2166 | 0.4 | 0.0866 |
| asset_manager | 0.1708 | 0.3 | 0.0512 |
| other_reportable | 0.1120 | 0.5 | 0.0560 |
| nonreportable | 0.0946 | 0.6 | 0.0568 |

| Disaggregated | share of gross | weight | mean Phi contribution |
|---|---|---|---|
| producer_merchant | 0.5648 | 0.1 | 0.0565 |
| swap | 0.1324 | 0.4 | 0.0529 |
| other_reportable | 0.1018 | 0.5 | 0.0509 |
| managed_money | 0.0627 | 1.0 | 0.0627 |
| nonreportable | 0.0520 | 0.6 | 0.0312 |

**The weight-free comparison, which is valid**: the category carrying weight 1.0 holds
**21.5% of all gross open interest in TFF** against **8.3% in Disaggregated**. Two and a half
times as much of the financial-futures market sits with holders who have an exit function
written into their mandate. That statement needs no weights and survives any reasonable
reweighting.

Note also that Leveraged Funds' *mean per-market* share is 31.1% while its OI-weighted share
is 21.5%. The gap says leveraged funds concentrate in the **small** markets, which is the
crypto tail in §5.

> **Rule for anything downstream: compare Phi within a report, never across.** Rank TFF
> markets against TFF markets. To compare a rates contract against a metals contract, use
> the weight-free share of gross held at weight 1.0, or wait for the vol-scaled notional
> from `riskunits` (rung 4), which is denominated in risk rather than in category shares.

---

## 3. Fragility by asset class

90 markets, consolidated aggregates dropped.

| asset class | markets | open interest | median Phi | max Phi | median `Q_sell/OI` | median `Q_buy/OI` |
|---|---|---|---|---|---|---|
| rates/credit | 16 | 40,534,783 | 0.4253 | 0.6623 | 0.1414 | **0.2624** |
| equity index | 25 | 6,944,721 | 0.4553 | 0.7275 | 0.1594 | **0.2466** |
| fx | 15 | 2,923,492 | 0.4882 | 0.5725 | 0.2336 | 0.2295 |
| crypto | 33 | 934,477 | **0.7380** | 0.9362 | 0.2280 | **0.4285** |
| commodity index | 1 | 197,081 | 0.3852 | 0.3852 | 0.1900 | 0.2695 |

**`Q_buy` exceeds `Q_sell` in every asset class except FX.** That is the opposite of the
Disaggregated picture, where the sell side led, and it has one dominant cause: the
weight-1.0 category (Leveraged Funds) is net **short** across most of the financial complex,
while the low-weight categories (Asset Manager 0.3, Dealer 0.4) are net long. Whichever way
those markets break, the fragile side is the one that has to buy.

FX is the exception and is close to symmetric (0.234 sell against 0.230 buy).

---

## 4. The rates complex: the cash-futures basis trade, visible

79% of TFF open interest sits in nine contracts. Net position by category, latest week:

| market | asset_manager | leveraged | dealer | open interest |
|---|---|---|---|---|
| SOFR-3M | −587,821 | **−2,445,938** | +2,949,333 | 12,809,153 |
| UST 5Y NOTE | +2,896,249 | **−2,108,638** | −815,799 | 6,193,040 |
| UST 10Y NOTE | +2,611,964 | **−2,155,739** | −459,602 | 5,313,478 |
| UST 2Y NOTE | +1,845,012 | **−1,564,294** | −481,870 | 4,406,588 |
| FED FUNDS | −47,032 | −263,963 | +202,287 | 2,688,322 |
| ULTRA UST 10Y | +709,907 | −400,210 | −255,345 | 2,479,519 |
| ULTRA UST BOND | +1,131,787 | −862,638 | −271,486 | 2,462,300 |
| UST BOND | +568,268 | −389,522 | −269,722 | 1,859,732 |
| SOFR-1M | −54,209 | −278,504 | +368,749 | 1,583,625 |

Totals across all nine:

    leveraged          -10,469,446
    asset_manager       +9,074,125
    dealer                +966,545
    other_reportable      +322,937
    nonreportable         +105,839

**Asset Managers are long 9.07 million contracts against Leveraged Funds short 10.47
million.** This is the textbook shape of the cash-futures basis trade: levered relative-value
books short the future and long the deliverable bond, with asset managers taking the long
futures leg as a duration substitute.

Exit pressure says the same thing in the system's own units. `Q_buy` exceeds `Q_sell` in
**every one of the nine**, with `sell_to_buy` between 0.34 and 0.50:

| market | `Q_sell` | `Q_buy` | `Q_sell/OI` | `Q_buy/OI` | Phi | `sell_to_buy` |
|---|---|---|---|---|---|---|
| SOFR-3M | 1,221,991 | 2,622,284 | 0.0954 | 0.2047 | 0.3304 | 0.466 |
| UST 5Y NOTE | 884,091 | 2,434,958 | 0.1428 | 0.3932 | 0.4419 | 0.363 |
| UST 10Y NOTE | 792,352 | 2,348,069 | 0.1491 | **0.4419** | 0.4744 | 0.337 |
| UST 2Y NOTE | 658,887 | 1,757,042 | 0.1495 | 0.3987 | 0.4746 | 0.375 |
| ULTRA UST BOND | 344,879 | 974,516 | 0.1401 | 0.3958 | 0.4229 | 0.354 |

### 4.1 The caveat that governs the whole section

**Module spec §11 warns that Leveraged Funds in TFF "includes relative-value books whose
'net' is meaningless in isolation", and the basis trade is precisely such a book.** The
futures short is one leg of a hedged position whose other leg is a cash bond this report
cannot see.

So `Q_buy = 2.35 million` in UST 10Y is a real statement about **futures-market flow** if
that position is unwound, and it is **not** a statement that yields would collapse. An
unwinding basis trade sells cash and buys futures simultaneously; the futures leg is the
half this data can see, and reading it as directional exposure would be a serious error.

What the number does say is that the forced flow, if it comes, arrives in the futures market
as **buying**, and that is a fact about which side of the book has a liquidity problem. That
distinction — a real flow that is not a directional view — is exactly why this package keeps
`Q_sell` and `Q_buy` apart rather than reporting a single fragility figure.

### 4.2 Is it growing?

Leveraged net across the nine, last fourteen weeks:

| report_date | leveraged net | asset manager net | weekly change |
|---|---|---|---|
| 2026-04-28 | −8,947,276 | +9,533,622 | |
| 2026-05-26 | −9,370,671 | +8,577,701 | +85,378 |
| 2026-06-02 | −9,945,361 | +9,041,816 | −574,690 |
| 2026-06-23 | −10,648,162 | +9,235,048 | −387,796 |
| 2026-06-30 | −10,896,230 | +9,085,547 | −248,068 |
| **2026-07-07** | **−11,002,315** | +9,164,980 | −106,085 |
| 2026-07-14 | −10,953,559 | +9,149,446 | +48,756 |
| 2026-07-21 | −10,744,036 | +9,032,081 | +209,523 |
| 2026-07-28 | −10,469,446 | +9,074,125 | +274,590 |

The position built steadily from −8.95M at the end of April to a panel peak of **−11.00M on
2026-07-07**, and has eased for three consecutive weeks since. Over the whole 19-month panel
the range is −7.81M to −11.00M, so the latest reading sits **17% up from its most-short
extreme** — still near the top of its own range, and no longer growing.

**The 19 months is the binding limitation.** The vintage store begins 2025-01-07, so there is
no 2019 or March-2020 comparison available here, and "near the top of its range" means the
top of a range that does not contain either episode this configuration is famous for. A
percentile against 19 months is not a percentile against history.

Flow decomposition on UST 10Y Leveraged is `mixed` in **seven of the last eight weeks**,
which is the two-sided book asserting itself: long 309,480 against short 2,465,219, with both
legs moving materially most weeks. The four-state table is not the right lens on a
relative-value category, and the classifier correctly declines to pretend otherwise.

Breadth-depth on the short side is the more informative view:

| report_date | position | traders | avg/trader | Δtraders | Δavg | quadrant |
|---|---|---|---|---|---|---|
| 2026-06-30 | 2,323,942 | 82 | 28,341 | −4 | +1,974 | narrow_and_deep |
| 2026-07-07 | 2,421,237 | 79 | 30,649 | −3 | +2,308 | **narrow_and_deep** |
| 2026-07-14 | 2,467,616 | 84 | 29,376 | +5 | −1,272 | wide_and_shallow |
| 2026-07-21 | 2,447,147 | 85 | 28,790 | +1 | −586 | wide_and_shallow |
| 2026-07-28 | 2,465,219 | 87 | 28,336 | +2 | −454 | wide_and_shallow |

The peak week was reached the concentrating way: **trader count falling 86 → 79 while average
position rose to 30,649**, which is the spec's "narrow and deep" cell, the violent-unwind
configuration. It has since gone the other way, adding eight traders and shedding size per
trader. So the most concentrated moment in this panel was three weeks ago and the
configuration is currently loosening.

Eighty-seven traders hold 2.47 million contracts, an average of 28,336 each.

---

## 5. Crypto: where Phi and Q point in opposite directions

The five highest Phi readings in the entire TFF set are all crypto, all on Coinbase:

| market | open interest | Phi | `Q_sell/OI` | `Q_buy/OI` | top contributor | share |
|---|---|---|---|---|---|---|
| NANO XRP | 30,804 | **0.9362** | 0.0337 | 0.0655 | leveraged | 0.914 |
| Nano Bitcoin | 142,195 | **0.9350** | 0.0300 | 0.0581 | leveraged | 0.885 |
| DOGECOIN PERP STYLE | 4,582 | 0.8651 | | | leveraged | 0.707 |
| POLKADOT PERP STYLE | 4,891 | 0.8409 | | | leveraged | 0.668 |
| CRYPTO HYPE PERP STYLE | 7,379 | 0.8318 | | | leveraged | 0.642 |

Nano Bitcoin in full:

| category | long | short | net | gross | `w_c` | Phi contribution |
|---|---|---|---|---|---|---|
| leveraged | 121,869 | 129,734 | −7,865 | 251,603 | 1.0 | **0.8847** |
| other_reportable | 16,319 | 7,796 | +8,523 | 24,115 | 0.5 | 0.0424 |
| nonreportable | 1,545 | 2,203 | −658 | 3,748 | 0.6 | 0.0079 |
| asset_manager | 0 | 0 | 0 | 0 | 0.3 | 0.0000 |
| dealer | 0 | 0 | 0 | 0 | 0.4 | 0.0000 |

**Asset Manager and Dealer are exactly zero.** There is no institutional long-only money and
no dealer intermediation in this contract at all. It is levered funds trading against levered
funds, with a small retail and other-reportable fringe.

Now read the two numbers together:

    Phi        = 0.9350   (2nd highest of 90 markets)
    Q_sell/OI  = 0.0300   (near the bottom of the set)
    Q_buy/OI   = 0.0581

Leveraged Funds holds **88.5% of gross open interest** and a net of only **−7,865 contracts,
5.5% of OI**. Long 121,869 against short 129,734: the category is almost entirely offsetting
itself.

**Phi is near its ceiling and Q is near the floor, in the same market, and both are correct.**
Phi answers "if this market has to move, how much of it sits with holders who can be forced?"
— nearly all of it. Q answers "how much net exposure would actually have to change hands?" —
very little. A market can be composed entirely of fragile holders and still have almost no
directional crowding, because they are on both sides.

This is the cleanest demonstration in either report of why the system carries both numbers,
and it is a caution against ever compressing them into one. A composite that multiplied a
high Phi by a high crowding percentile would score this market as dangerous; the crowding
term is what stops it.

The larger Coinbase perpetual-style contracts behave differently: NANO ETHER PERP STYLE
(219,650 OI) shows `Q_buy/OI` of 0.503 with Phi 0.657, and NANO BITCOIN PERP STYLE (162,619)
shows 0.332 with Phi 0.632. Those carry genuine one-sided exposure. **The "Nano" and "PERP
STYLE" variants of the same underlying are structurally different books**, which is worth
knowing before treating crypto as one bucket.

---

## 6. What is missing

Beyond the standing limitations in the Disaggregated analysis (no volume so no
days-to-liquidate, no prices so no trigger level, weights are judgement):

- **The cash leg.** Every reading in §4 is half a trade. TFF sees the futures side of the
  basis trade and cannot see the bonds. Nothing here can distinguish a levered directional
  short from a hedged relative-value book, and the two have opposite implications.
- **19 months of history.** The vintage store begins 2025-01-07. Every "near the top of its
  range" in this document is a range that excludes 2019 and March 2020, which are the
  episodes this configuration is known for. `from_current_store` does not cover TFF, so there
  is no deeper history available in this package today.
- **TFF weights have never been sensitivity-tested.** They were configured from module spec
  §6.3 and this is their first use. §2.3 shows the floor of the weight set drives the level
  of Phi, so the TFF weights deserve the same sweep the flow tolerance got before any TFF Phi
  is quoted as a level rather than a rank.
- **No `combined` series.** Futures-only, as everywhere in this package. In equity index
  particularly, options positioning is large and invisible here.

---

## 7. Bottom line

TFF is a genuinely different population from the Disaggregated report and it is where the
macro book lives: 79% of its open interest sits in nine US rates contracts, against a
Disaggregated universe that is three quarters power and gas basis.

The headline structural fact is that **the fragile side of financial futures is short**.
Leveraged Funds are net short 10.47 million contracts across the rates complex against Asset
Managers long 9.07 million, and `Q_buy` exceeds `Q_sell` in every one of the nine contracts
and in every asset class except FX. That is the cash-futures basis trade, and it is the exact
inversion of the levered-long picture the design doc's cocoa example uses. The position
reached a panel peak of −11.00M three weeks ago, reached it the concentrating way (trader
count falling while average size rose), and has eased since.

Two cautions carry more weight than the finding. **The basis trade is a hedged book**, so
`Q_buy` describes a futures flow and not a directional view; anyone reading 2.35 million
contracts of forced buying in UST 10Y as a yield call has misread it, and the spec warned
about exactly this category. And **Phi cannot be compared across report types**: TFF's median
of 0.495 against Disaggregated's 0.240 is partly a real difference (the weight-1.0 category
holds 21.5% of gross here against 8.3% there) and partly an artifact of the two weight sets
having different floors, 0.3 against 0.1.

The most interesting single market is Nano Bitcoin, where Phi is 0.935 and `Q_sell/OI` is
0.030. Everyone in that contract is forceable and almost nobody is net exposed, because
levered funds hold 88.5% of the gross and are trading against themselves. It is the clearest
case in either report of crowding and fragility being genuinely separate quantities.

**In plain terms: this is a real and substantial finding about where the fragile money sits
in financial futures, and it points the opposite way from the commodity picture.** But it is
descriptive, not predictive, and it is weakened by two specific things rather than by general
hedging: half of the largest trade is invisible to this data, and the history is nineteen
months, which does not include either episode anyone would want to compare against.
