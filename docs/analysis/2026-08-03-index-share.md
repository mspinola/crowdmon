# Index share and the Swap Dealer weight

**Report week:** 2026-07-28 (latest), history from 2006-01-03
**Handoff:** [`2026-08-03-index-share.md`](../handoffs/2026-08-03-index-share.md) §1
**Reproducer:** [`reproduce_index_share.py`](reproduce_index_share.py)
**Data:** `cot_supplemental` (13 markets, ingested 2026-08-03 via cotdata #96), `cot_disagg`,
`propadj` prices

Point-in-time, per this directory's rule. A later week gets a new file.

> **The result is negative, and it is the negative result §4 named in advance.** Index
> positioning is **not** meaningfully stickier than swap positioning. On the persistence
> measure the handoff called "the property that actually matters", swap wins. The premise
> for using index share to split the Swap Dealer weight does not survive its own test.

---

## 0. Method, and the one constraint that shapes every table

The Supplemental report is futures-and-options **combined**; the Disaggregated store is
futures-only. Their open interest is not the same quantity, so nothing here differences
across the two. Every statistic is a ratio formed inside one report, and every
index-versus-swap statement is an inference. Handoff §3 requires this and the reproducer
enforces it by never constructing a term that mixes denominators.

Three quantities, per market, weekly, 2006-01-03 to 2026-07-28 (1,074 weeks; soybean meal
696, having entered in 2013):

```
index_gross_share = (L_IT + S_IT) / (2 · OI)
index_long_share  = L_IT / OI
index_net         = L_IT − S_IT
```

Returns are `propadj` and nothing else. The layer-2 trap table refuses `backadj` for anything
denominated in percent, because additive back-adjustment preserves absolute price changes
rather than percentage ones. The return window runs prior report date to report date, so it
is contemporaneous with `diff()` on positioning rather than leading or lagging it.

## 1. Index prominence

The index book is a real presence and never a dominant one. Gross share runs 10.3% to 21.1%
of `2·OI`:

| market | `index_gross_share` | `index_long_share` |
|---|---|---|
| Chicago wheat | 0.2114 | 0.3481 |
| Lean hogs | 0.1783 | 0.3259 |
| Live cattle | 0.1629 | 0.3075 |
| Cotton | 0.1613 | 0.2894 |
| Sugar | 0.1606 | 0.2695 |
| KC wheat | 0.1565 | 0.2706 |
| Soybean oil | 0.1428 | 0.2508 |
| Corn | 0.1409 | 0.2369 |
| Soybean meal | 0.1364 | 0.2275 |
| Coffee | 0.1321 | 0.2302 |
| Soybeans | 0.1313 | 0.2203 |
| Feeder cattle | 0.1210 | 0.2094 |
| Cocoa | 0.1029 | 0.1615 |

Wheat is the outlier at both ends of the table, and cocoa, the market that motivated the
handoff, has the **smallest** index book of the thirteen.

## 2. Persistence, which is where the premise fails

The handoff's own framing: "Index positions should be sticky if they are what they claim to
be." They are sticky. So is the swap book, slightly more so.

**Autocorrelation at 12 weeks.** Reported with comparators, because a level series is
autocorrelated for every category and the bare index column cannot separate sticky from
ordinary:

| market | index | swap | managed money |
|---|---|---|---|
| Chicago wheat | 0.9248 | 0.9356 | 0.5641 |
| KC wheat | 0.8580 | 0.8963 | 0.6650 |
| Corn | 0.7180 | 0.7982 | 0.5654 |
| Soybeans | 0.6986 | 0.6671 | 0.5476 |
| Soybean oil | 0.8283 | 0.8153 | 0.4831 |
| Soybean meal | 0.7433 | 0.9648 | 0.5057 |
| Cotton | 0.7774 | 0.8265 | 0.6720 |
| Lean hogs | 0.6904 | 0.7345 | 0.4584 |
| Live cattle | 0.8386 | 0.8743 | 0.6283 |
| Feeder cattle | 0.8269 | 0.8260 | 0.6919 |
| Cocoa | 0.7404 | 0.6740 | 0.6047 |
| Sugar | 0.8350 | 0.9047 | 0.6848 |
| Coffee | 0.7754 | 0.9136 | 0.7202 |

**Index is more persistent than swap in 4 of 13 markets.** Medians: index 0.777, swap 0.826,
managed money 0.605. The swap book is the more persistent of the two, and both are far more
persistent than managed money.

**Week-to-week change volatility**, `sd(Δnet / OI)`, which is the cleaner statistic because it
is scale-free within each report:

| market | index | swap | managed money |
|---|---|---|---|
| Chicago wheat | 0.00817 | 0.00948 | 0.03081 |
| KC wheat | 0.00933 | 0.00925 | 0.02534 |
| Corn | 0.00577 | 0.00640 | 0.02495 |
| Soybeans | 0.00645 | 0.00816 | 0.02835 |
| Soybean oil | 0.00732 | 0.00881 | 0.02917 |
| Soybean meal | 0.00692 | 0.00757 | 0.02939 |
| Cotton | 0.00770 | 0.01228 | 0.03463 |
| Lean hogs | 0.00862 | 0.00891 | 0.02799 |
| Live cattle | 0.00652 | 0.00605 | 0.02358 |
| Feeder cattle | 0.00987 | 0.00916 | 0.03642 |
| Cocoa | 0.00882 | 0.01081 | 0.03034 |
| Sugar | 0.00705 | 0.01158 | 0.02504 |
| Coffee | 0.00677 | 0.00959 | 0.03148 |

Index is steadier than swap in 10 of 13, but the **median ratio is 0.862**: about 14%
steadier. Against managed money the median ratio is **0.265**, close to four times steadier.

So the two measures disagree on direction between index and swap and agree emphatically on
the gap to managed money. A 14% edge on one statistic and a deficit on the other is not a
basis for treating the index share of a swap book as a fragility discriminator.

## 3. Stress weeks, the most informative measurement

Worst 5% of report-week returns per market, 54 weeks each (35 for soybean meal). Mean
`Δnet / OI`, where negative means cutting net long:

| market | index, all weeks | index, stressed | managed money, stressed | swap, stressed |
|---|---|---|---|---|
| Chicago wheat | -0.00018 | -0.00490 | -0.02088 | -0.00443 |
| KC wheat | +0.00021 | -0.00665 | -0.02342 | -0.00225 |
| Corn | +0.00013 | -0.00111 | -0.02452 | -0.00083 |
| Soybeans | +0.00020 | -0.00448 | -0.02511 | -0.00492 |
| Soybean oil | +0.00020 | -0.00288 | -0.02381 | -0.00237 |
| Soybean meal | +0.00014 | -0.00157 | -0.03456 | **+0.00231** |
| Cotton | +0.00015 | -0.00286 | -0.02297 | -0.00577 |
| Lean hogs | +0.00014 | -0.00367 | -0.02403 | -0.00376 |
| Live cattle | +0.00005 | -0.00386 | -0.01520 | -0.00188 |
| Feeder cattle | +0.00015 | -0.00354 | -0.02217 | -0.00106 |
| Cocoa | +0.00015 | -0.00266 | -0.02657 | **+0.00432** |
| Sugar | +0.00018 | -0.00124 | -0.02829 | **+0.00300** |
| Coffee | +0.00007 | -0.00431 | -0.03250 | -0.00408 |

Three things, in order of how much they cost the premise.

**Index positioning does not hold under stress. It falls.** Mean -0.00336 against an
unconditional +0.00012, negative in all 13 markets. A low fragility weight asserts stickiness
under stress, and what the data shows is a book that sells into the worst weeks, only
modestly.

**Under stress the swap book moves LESS than the index book**, -0.00167 against -0.00336, and
that is the reverse of the handoff's mechanism. Index flow was supposed to be the sticky part
of the swap book; measured in the weeks that matter, the swap book is steadier than the index
book it supposedly gets its stickiness from.

**Swap adds to net long under stress in 3 of 13 markets** (soybean meal, cocoa, sugar), where
the index book never does. In those markets the swap book is absorbing rather than
liquidating, which is stabilising behaviour, and it is exactly the behaviour a fragility
weight of 0.4 already fails to distinguish from selling.

Relative to managed money at 1.0, which is what the weight table anchors on:

|  | swap / MM | index / MM |
|---|---|---|
| routine turnover | 0.305 | 0.265 |
| stress-week move | 0.067 | 0.135 |

Turnover is not fragility, and these bound the weight from observed behaviour rather than
setting it: a book can trade little and still be forced, which is the whole reason the weights
are configured rather than fitted. Recorded because they are the first empirical numbers this
package has had to put beside `swap: 0.4`, and they bracket it from both sides. Routine
turnover puts swap at 0.305 of managed money, close to the assigned 0.4. Stress behaviour
puts it at 0.067, far closer to `producer_merchant: 0.1`.

## 4. Index versus swap prominence

| market | `index_gross` | `swap_gross` | corr, level | corr, change |
|---|---|---|---|---|
| Chicago wheat | 0.2109 | 0.1558 | 0.5626 | 0.4739 |
| KC wheat | 0.1581 | 0.1080 | 0.7348 | 0.4631 |
| Corn | 0.1409 | 0.1091 | **0.0478** | 0.4636 |
| Soybeans | 0.1312 | 0.1051 | 0.5910 | 0.5656 |
| Soybean oil | 0.1428 | 0.1173 | 0.4627 | 0.4953 |
| Soybean meal | 0.1364 | 0.0974 | 0.6879 | 0.3746 |
| Cotton | 0.1609 | 0.1768 | 0.2544 | 0.5911 |
| Lean hogs | 0.1770 | 0.1503 | 0.5928 | 0.4535 |
| Live cattle | 0.1631 | 0.1399 | 0.6809 | 0.5816 |
| Feeder cattle | 0.1219 | 0.0665 | 0.5209 | 0.4241 |
| Cocoa | 0.1042 | 0.0752 | **-0.0917** | 0.3244 |
| Sugar | 0.1618 | 0.1539 | 0.5709 | 0.4574 |
| Coffee | 0.1324 | 0.1390 | 0.5371 | 0.4630 |

Median level correlation 0.563, median change correlation 0.463. The index book is larger
than the swap book in 11 of 13.

The divergences the handoff asked to be noted are worse than a weak average suggests.
**Cocoa's level correlation is -0.0917 and corn's is 0.0478**: in the market that motivated
this entire question, index share carries essentially no information about swap share, and
what little it carries points the wrong way. Any per-market scheme reading swap fragility off
index prominence would be reading noise in precisely the market it was built for.

## 5. Cocoa, carried through

Latest report date 2026-07-28. Supplemental, combined basis:

```
OI                 = 262,836
CIT long           =  50,157
CIT short          =  20,509

index_gross_share  = (50,157 + 20,509) / (2 × 262,836) = 70,666 / 525,672 = 0.1344
index_long_share   = 50,157 / 262,836                                     = 0.1908
index_net          = 50,157 − 20,509                                      = 29,648
```

Disaggregated, futures-only basis, not differenced against the above:

```
OI                 = 201,223
swap_gross_share   = 0.1141      swap_net = 22,894
mm_gross_share     = 0.1226
```

History: mean `index_gross_share` 0.1029, the smallest of the thirteen. Autocorrelation
0.976 / 0.887 / 0.740 at 1, 4 and 12 weeks, against the swap book's 0.674 at 12 weeks, so
cocoa is one of the four markets where index is the more persistent. Change volatility
0.00882 index against 0.01081 swap and 0.03034 managed money.

Under stress, cocoa index cuts -0.00266 while cocoa swap **adds** +0.00432. The handoff opens
by describing cocoa's swap book as fragile capital underweighted at 0.4. In the worst 5% of
cocoa weeks over twenty years, that book buys.

## 6. Live cattle, carried through

The appendix's worked example. Latest report date 2026-07-28:

```
OI                 = 445,137
CIT long           =  77,978
CIT short          =  10,565

index_gross_share  = (77,978 + 10,565) / (2 × 445,137) = 88,543 / 890,274 = 0.0995
index_long_share   = 77,978 / 445,137                                     = 0.1752
index_net          = 77,978 − 10,565                                      = 67,413
```

Disaggregated: OI 298,449, `swap_gross_share` 0.1267, `swap_net` 61,596, `mm_gross_share`
0.1722.

The long-short asymmetry is the sharpest here of any of the thirteen: 77,978 against 10,565
is 7.38 to 1, and the index book is a one-way long by construction. Mean historical
`index_gross_share` is 0.1629, so the current 0.0995 is well below its own history. Live
cattle is also the market with the highest index-swap level correlation but one (0.6809) and
the mildest stress cut of the thirteen (-0.00386 index, -0.00188 swap, -0.01520 managed
money, against a 5% return cut of only -3.56%).

## 7. What this changes, and what it does not

**The weight table is unchanged**, per handoff §2. This document is evidence, not a decision.

What the evidence supports: **retiring the premise**, which §4 anticipated in as many words.
Splitting Swap Dealer fragility by index share requires index capital to be meaningfully
stickier than the rest of the swap book. It is not. It is 14% steadier on one statistic, less
persistent on another, and it sells harder under stress than the swap book does.

What remains genuinely open is a different and simpler question, which this data does speak
to: **whether `swap: 0.4` is too high in stress**. Swap moves at 0.067 of managed money in the
worst weeks and adds to net long in 3 of 13 markets. That is `producer_merchant` behaviour,
not mid-table behaviour. But routine turnover puts it at 0.305, and a single weight cannot be
both. The honest reading is that one number for swap is doing incoherent work, exactly as the
handoff said, and that the incoherence is between regimes rather than between markets.

## 8. Corrections to the handoff

Per §4's last bullet.

**§0, "Cocoa — Swap Dealer holds the largest net long."** True on 2026-07-28 and a minority
configuration historically. Across 1,051 Disaggregated weeks, the largest net long is held by:

| category | share of weeks |
|---|---|
| Managed Money | 64.3% |
| Swap | 23.1% |
| Other Reportable | 10.9% |
| Producer/Merchant | 1.6% |

Swap holds it 23.1% of the time. This is the same failure §B31 recorded from the other
direction, where cocoa did not currently show the shape the appendix draws from it; here
cocoa currently shows a shape it usually does not have. A premise read off the latest week is
a premise about one week.

**§2 could not be executed at all.** It asks for a recompute of the §B33-B36 headline figures
across `w_SD ∈ {0.2, 0.4, 0.7}`. **§B33 through §B36 do not exist** in
`docs/design/amendments-2026-08-02.md`, which ends at §B32, and `A_agnostic`, "template rate
by stratum" and §3's cited "22 of 39 markets / cocoa 0.976 then 0.100" appear nowhere in
`docs/design/`. This is a second blocker, independent of the cotdata dependency the header
names, and it lives in this repo. It is recorded in the handoff's §5.

**§3's classification-instability caveat is unverifiable for the same reason.** It cites §B36.
Nothing was inherited from it, so no conclusion here rests on template classification. That
turned out to be cheap: §2 was the only part that needed it.

## 9. What remains unresolved, which is most of the original question

**Metals cannot be resolved this way, ever.** Gold, silver and copper are outside Supplemental
coverage, and the handoff's second motivating case, a swap dealer sitting on the immovable
physical-hedging side, is a metals case. Nothing measured here transfers: these are 13
agricultural markets, and §3 required an argument for any transfer that this data cannot
supply. The gold half of the question is exactly where it was before this document.

Also unresolved: whether the regime split in §7 should become two weights, a
stress-conditional weight, or nothing at all. That is a design decision and it needs the §2
sensitivity work, which needs §B33-B36 to exist first.

## 10. Bottom line, in plain language

The Supplemental report was supposed to answer whether the sticky part of a swap dealer's
book can be identified by how much of it is index money. Measured over twenty years and
thirteen agricultural markets, it cannot. Index money and swap money behave almost the same:
index is marginally steadier week to week, swap is marginally more persistent quarter to
quarter, and under the worst price weeks the swap book actually moves less than the index
book. Both are dramatically steadier than managed money, which is the distinction the weight
table already makes.

So this is a **genuine null on the question as asked**, and it retires the per-market idea
rather than leaving it open. It is not an empty result, because it turned up something the
handoff was not looking for: the swap book behaves like a hedger in a crisis and like a
mid-table trader in normal weeks, and a single weight of 0.4 cannot express both. That is a
real finding about `swap: 0.4`, but it is about regimes rather than about markets, and it
would be found in metals or anywhere else without needing this report at all.

And the largest piece of the original question is untouched. Gold is not in this data and
never will be.
