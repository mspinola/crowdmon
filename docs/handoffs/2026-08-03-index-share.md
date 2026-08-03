# Handoff: index share and the swap-dealer weight

**Status:** open. The `cotdata` blocker cleared on 2026-08-03 when the CIT Supplemental
ingestion merged as cotdata#96 (`730f3ac`), so this is unblocked and unclaimed
**Date:** 2026-08-03
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-index-share.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** `cotdata/docs/handoffs/2026-08-03-cit-supplemental.md`
**Deliverable:** an empirical basis for the Swap Dealer weight, or a stated finding that none exists

> Update `Status:` to `complete (PR #NN)` when executed.

---

## 0. The question

Swap Dealer currently carries a single `w = 0.4`. Two markets show that number failing in opposite directions:

- **Cocoa** — Swap Dealer holds the largest net long, so fragile capital is underweighted at 0.4
- **Gold** — Swap Dealer is the immovable physical-hedging side, so robust capital is overweighted at 0.4

A swap dealer's net is the residual of hedged client positions. Its fragility depends on the clients: unlevered index funds are sticky, levered accounts are not. The Supplemental report separates index flow, so for the markets it covers the question is answerable rather than a matter of judgement.

**Read §3 before planning the work.** The constraints are severe and shape what can honestly be concluded.

---

## 1. Measure

Restricted to the 13 Supplemental markets, over the full 2006→present history.

**Index prominence:**

```
index_gross_share = (L_IT + S_IT) / (2 · OI)
index_long_share  = L_IT / L_total
index_net         = L_IT − S_IT
```

**Persistence** — the property that actually matters for fragility. Index positions should be sticky if they are what they claim to be:

- Autocorrelation of `index_net` at 1, 4 and 12 weeks
- Standard deviation of weekly `Δindex_net / OI`, compared against the same statistic for Managed Money and for Swap Dealer in the Disaggregated report on the same markets
- Behaviour during the sharpest drawdown weeks in each market: does index positioning fall, hold, or rise? **This is the single most informative measurement in the handoff** — stickiness under stress is precisely what a low fragility weight asserts.

**Relationship to Swap Dealer** — inference across reports, not identity:

- Correlation between `index_gross_share` (Supplemental) and `swap_gross_share` (Disaggregated) per market, and week-to-week within market
- Where they diverge, note it. A market where the swap book is large and the index book is small is where `w_SD = 0.4` is most likely wrong in the fragile direction.

**Cocoa and live cattle in full.** Cocoa motivated the question; live cattle is the appendix's worked example. Give each a complete walkthrough in the established house style: numbers carried through, arithmetic shown, prose reading at the end.

---

## 2. Weight sensitivity

Recompute the §B33–B36 headline figures — template rate by stratum, `A_agnostic` median, `Q_sell`/`Q_buy` — across `w_SD ∈ {0.2, 0.4, 0.7}`, restricted to Supplemental markets so results are comparable to the index measurement.

Report how much each conclusion moves. If the template rate is insensitive to `w_SD` across that range, the weight matters less than the effort implies and that is worth knowing. If it is highly sensitive, the weight is load-bearing and needs justifying rather than asserting.

**Do not change the weight table in this session.** Produce the evidence; the decision is separate and follows.

---

## 3. Constraints — read before concluding anything

**Thirteen agricultural markets only.** No metals. Gold, silver and copper — three of the seven always-template markets, and the case where a swap dealer sits on the *immovable* side — are outside coverage and cannot be resolved this way, ever, by this report. Whatever is concluded for ag does not transfer to metals without an argument that is not in this data.

**Combined futures-and-options, against a futures-only Disaggregated store.** Different basis, different denominators. Compare ratios within each report; never difference across them. Any cross-report statement is an inference and should be labelled as one.

**Legacy taxonomy.** Index Traders is carved from both commercial and non-commercial, so it does not nest inside Swap Dealer. `index_gross_share` and `swap_gross_share` are two views of overlapping populations, not a decomposition.

**Classification instability from §B36.** 22 of 39 markets are extreme over the pooled window but only 17 in both halves; cocoa runs 0.976 then 0.100. Any conclusion tied to template classification inherits that instability. Prefer statements about position behaviour over statements about classification.

---

## 4. Report back

- Index prominence and persistence tables, per market
- **The stress-week behaviour result**, called out separately
- Index-versus-swap relationship, with the cross-report caveat carried
- Cocoa and live cattle walkthroughs
- Weight sensitivity: how much each headline conclusion moves across `w_SD ∈ {0.2, 0.4, 0.7}`
- **An explicit statement of what remains unresolved for metals**, which is most of the original question
- Anything contradicting this handoff, corrected in place

A negative result is a real outcome. If index positioning turns out not to be meaningfully stickier than swap positioning generally, that retires the premise for a per-market weight and is worth reporting plainly.

---

## 5. Outcome, 2026-08-03. §1 executed, §2 blocked

Appended per the append-never-edit rule; §0-§4 above are preserved as issued.

Executed by a session that reached this handoff from the work order rather than from the
repo, and so filed its own copy before noticing cotdata#97 had already been adopted here as
PR #36. The body above is main's adopted copy. **That collision is itself the finding this
directory's "a handoff can also be a claim" section exists to prevent**, and it cost two
duplicate filings rather than two duplicate modules only because the second session checked
the remote before merging.

Full measurements: [docs/analysis/2026-08-03-index-share.md](../analysis/2026-08-03-index-share.md).
Reproducer: [docs/analysis/reproduce_index_share.py](../analysis/reproduce_index_share.py).
`cot_supplemental` was ingested into the real store on 2026-08-03 (13 markets, 1,074 weeks
from 2006-01-03; soybean meal 696, having entered 2013).

### The verdict is the negative result §4 named in advance

§4's closing paragraph: "If index positioning turns out not to be meaningfully stickier than
swap positioning generally, that retires the premise for a per-market weight." That is what
happened.

| measure | index | swap | reading |
|---|---|---|---|
| autocorrelation, 12 weeks (median) | 0.777 | **0.826** | swap is the more persistent |
| `sd(Δnet/OI)` (median ratio index/swap) | **0.862** | | index 14% steadier |
| stress-week mean `Δnet/OI` | -0.00336 | **-0.00167** | swap moves LESS when it matters |

Index is more persistent than swap in **4 of 13** markets and steadier in 10 of 13, by 14%.
The two statistics disagree on direction. Against Managed Money both agree emphatically
(index 0.265 of MM turnover, swap 0.305), which is the distinction the weight table already
draws.

**The mechanism fails in the specific place the handoff put it.** Index flow was to be the
sticky part of the swap book; in the worst 5% of weeks the swap book is steadier than the
index book, and swap **adds** to net long in 3 of 13 markets where index never does.

### What §1 turned up that §0 did not anticipate

Relative to Managed Money at 1.0: routine turnover puts swap at **0.305**, close to the
assigned 0.4; stress-week behaviour puts it at **0.067**, far closer to
`producer_merchant: 0.1`. One weight cannot be both. **The incoherence in `swap: 0.4` is
between regimes, not between markets**, which is the opposite of the per-market direction
this handoff was built to explore, and it would show up in metals or anywhere else without
needing the Supplemental report at all.

### §2 was not run, and the reason is in this repo rather than in cotdata

§2 asks for a recompute of the **§B33-B36** headline figures. Those sections **do not
exist**: `docs/design/amendments-2026-08-02.md` ends at **§B32**, and `A_agnostic`,
"template rate by stratum" and §3's cited "22 of 39 markets / cocoa 0.976 then 0.100" appear
nowhere in `docs/design/`. Nothing in §2 was run and no substitute baseline was invented.

The cited figures are not fabricated, which was worth checking before saying so: `2026-08-02
§B31`'s classic-outright row gives 33.3% never plus 23.1% always over 39 markets, which is
**22 of 39** exactly. The pooled half of §3's caveat is derivable from §B31; the half-split
half is a measurement nobody has recorded.

### Corrections, per §4's last bullet

**§0's cocoa premise is read off one week.** "Swap Dealer holds the largest net long" is true
on 2026-07-28 and holds in only **23.1%** of 1,051 Disaggregated weeks; Managed Money holds
it 64.3%. Same failure as `2026-08-02 §B31` in mirror image, where cocoa did not show the
shape the appendix draws from it.

**§3's classification-instability caveat could not be checked**, per the section above. No
conclusion here rests on template classification, so nothing was inherited from it.

**Metals are exactly where they were.** §3 said this and it survives execution unchanged: the
gold case, a swap dealer on the immovable side, is outside Supplemental coverage permanently.
Most of §0's original question is still open and is not answerable by this report.

**Status: §1 complete, §2 blocked on §B33-B36. The weight table is unchanged**, per §2's
instruction.
