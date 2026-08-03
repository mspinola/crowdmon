# Handoff: index share and the swap-dealer weight

**Status:** **blocked, and blocked on two things rather than the one it names.** Not started.
Verification appended below as §5
**Date:** 2026-08-03
**Lives at:** `crowdmon/docs/handoffs/2026-08-03-index-share.md`
**Target:** Claude Code session, `crowdmon` worktree
**Depends on:** `cotdata/docs/handoffs/2026-08-03-cit-supplemental.md`
**Deliverable:** an empirical basis for the Swap Dealer weight, or a stated finding that none
exists

Update `Status:` to `complete (PR #NN)` when executed.

---

## 0. The question

Swap Dealer currently carries a single `w = 0.4`. Two markets show that number failing in
opposite directions:

* Cocoa — Swap Dealer holds the largest net long, so fragile capital is underweighted at 0.4
* Gold — Swap Dealer is the immovable physical-hedging side, so robust capital is
  overweighted at 0.4

A swap dealer's net is the residual of hedged client positions. Its fragility depends on the
clients: unlevered index funds are sticky, levered accounts are not. The Supplemental report
separates index flow, so for the markets it covers the question is answerable rather than a
matter of judgement.

Read §3 before planning the work. The constraints are severe and shape what can honestly be
concluded.

## 1. Measure

Restricted to the 13 Supplemental markets, over the full 2006→present history.

Index prominence:

```
index_gross_share = (L_IT + S_IT) / (2 · OI)
index_long_share  = L_IT / L_total
index_net         = L_IT − S_IT
```

Persistence — the property that actually matters for fragility. Index positions should be
sticky if they are what they claim to be:

* Autocorrelation of `index_net` at 1, 4 and 12 weeks
* Standard deviation of weekly `Δindex_net / OI`, compared against the same statistic for
  Managed Money and for Swap Dealer in the Disaggregated report on the same markets
* Behaviour during the sharpest drawdown weeks in each market: does index positioning fall,
  hold, or rise? This is the single most informative measurement in the handoff — stickiness
  under stress is precisely what a low fragility weight asserts.

Relationship to Swap Dealer — inference across reports, not identity:

* Correlation between `index_gross_share` (Supplemental) and `swap_gross_share`
  (Disaggregated) per market, and week-to-week within market
* Where they diverge, note it. A market where the swap book is large and the index book is
  small is where `w_SD = 0.4` is most likely wrong in the fragile direction.

Cocoa and live cattle in full. Cocoa motivated the question; live cattle is the appendix's
worked example. Give each a complete walkthrough in the established house style: numbers
carried through, arithmetic shown, prose reading at the end.

## 2. Weight sensitivity

Recompute the §B33–B36 headline figures — template rate by stratum, `A_agnostic` median,
`Q_sell`/`Q_buy` — across `w_SD ∈ {0.2, 0.4, 0.7}`, restricted to Supplemental markets so
results are comparable to the index measurement.

Report how much each conclusion moves. If the template rate is insensitive to `w_SD` across
that range, the weight matters less than the effort implies and that is worth knowing. If it
is highly sensitive, the weight is load-bearing and needs justifying rather than asserting.

Do not change the weight table in this session. Produce the evidence; the decision is
separate and follows.

## 3. Constraints — read before concluding anything

Thirteen agricultural markets only. No metals. Gold, silver and copper — three of the seven
always-template markets, and the case where a swap dealer sits on the immovable side — are
outside coverage and cannot be resolved this way, ever, by this report. Whatever is concluded
for ag does not transfer to metals without an argument that is not in this data.

Combined futures-and-options, against a futures-only Disaggregated store. Different basis,
different denominators. Compare ratios within each report; never difference across them. Any
cross-report statement is an inference and should be labelled as one.

Legacy taxonomy. Index Traders is carved from both commercial and non-commercial, so it does
not nest inside Swap Dealer. `index_gross_share` and `swap_gross_share` are two views of
overlapping populations, not a decomposition.

Classification instability from §B36. 22 of 39 markets are extreme over the pooled window but
only 17 in both halves; cocoa runs 0.976 then 0.100. Any conclusion tied to template
classification inherits that instability. Prefer statements about position behaviour over
statements about classification.

## 4. Report back

* Index prominence and persistence tables, per market
* The stress-week behaviour result, called out separately
* Index-versus-swap relationship, with the cross-report caveat carried
* Cocoa and live cattle walkthroughs
* Weight sensitivity: how much each headline conclusion moves across `w_SD ∈ {0.2, 0.4, 0.7}`
* An explicit statement of what remains unresolved for metals, which is most of the original
  question
* Anything contradicting this handoff, corrected in place

A negative result is a real outcome. If index positioning turns out not to be meaningfully
stickier than swap positioning generally, that retires the premise for a per-market weight
and is worth reporting plainly.

---

## 5. Blocking verification, 2026-08-03. Not started

Appended by the session that filed this handoff, per the append-never-edit rule. The body
above is preserved as issued. Nothing in §1 or §2 was executed.

**The block is real, and §4's last bullet applies to the handoff's own dependencies.** Both
were checked rather than assumed, and the second one is not the one the header names.

### The stated dependency: CIT Supplemental ingestion

Absent at every level checked, and the ingestion is not merely unmerged, it is unwritten.

| Checked | Result |
|---|---|
| `cotdata/docs/handoffs/2026-08-03-cit-supplemental.md` | **does not exist.** `cotdata` has no `docs/handoffs/` directory at all |
| `cotdata.get_cot(report=...)` | accepts `legacy`, `disagg`, `tff`. Anything else raises `ValueError` |
| `cotdata/src/cotdata/store.py` domains | `prices`, `metadata`, `cot`, `cot_legacy`, `cot_disagg`, `cot_tff` |
| `~/code/cotdata_store/manifests/cot.json` | `cot_disagg` 27 markets, `cot_legacy` 95, `cot_tff` 24. No supplemental domain |
| `cotdata/docs/design/cot_vintage.md` §29 | "all **futures-only, all annual zips**. No combined, no supplemental, no Socrata" |

The vintage spec's line is the load-bearing one: **futures-only annual zips are the only thing
the producer ingests**, and the Supplemental report is combined futures-and-options. So this
is not a matter of pointing the loader at another file in a format it already parses. §3
anticipated the basis difference as an analytical caveat; it is also an ingestion cost, and
that cost sits in `cotdata` behind an ADR-0007 seam that currently has nobody on it.

**Consequence for scheduling: this handoff has no path to being unblocked and no owner for
the work that would unblock it.** A dependency on a document that was never written will not
clear on its own. Whoever wants this answered files the `cotdata` handoff first.

### The unstated dependency: §B33–B36 do not exist

§2 is the part that looks runnable today, because the weight sensitivity recompute reads the
Disaggregated store, which is present with 27 markets. It is not runnable, for a different
reason.

`docs/design/amendments-2026-08-02.md` **ends at §B32.** There is no §B33, §B34, §B35 or
§B36, in that file or any other. Grepped across all of `docs/design/`:

| §2 and §3 cite | found |
|---|---|
| §B33–B36 | nothing |
| `A_agnostic` | nothing |
| "template rate by stratum" | nothing |
| §B36's "22 of 39 markets", cocoa "0.976 then 0.100" | nothing |

So §2 asks for a recompute of headline figures that have never been computed, and §3's
classification-instability caveat cites a measurement that has not been made. **§2 is blocked
on work in this repo, not on `cotdata`**, and that is a separate blocker from the one in the
header. It would have been discovered only after a session had set up the whole Supplemental
comparison, which is exactly the ordering this directory's claim-before-starting convention
exists to prevent.

The nearest existing work is §B31 and §B32, which measure the template shape by population on
Disaggregated and TFF respectively. Whether those are what §2 meant by "the §B33–B36 headline
figures" under different numbers is **not** something to guess: §B31 is about population split
and §B32 about TFF reachability, neither reports a stratum template rate or an `A_agnostic`
median, and the cited figures do not appear in either. A future session should treat the
§B33–B36 baseline as **to be established**, not as mislabelled.

### What was not done, deliberately

No measurement from §1 or §2 was run and no partial result is reported. §2 restricted to
Supplemental markets is not a well-defined computation without §1's market set and without the
§B33–B36 baseline, and running it against a substitute would have produced a number that looks
like an answer to the handoff and is not one.

The weight table is unchanged, per §2's instruction, and `swap: 0.4` in
`src/crowdmon/core/config.py` stands with no new evidence either way.

**Status: blocked, not started.** Unblocking requires, in order: a `cotdata` handoff for
Supplemental ingestion including the combined futures-and-options basis, then §B33–B36
established here, then this.
