# Handoff: coverage reporting, which rung dropped a market and why

**Status:** claimed, not started
**Date:** 2026-08-02
**Claimed by:** the session that built `commonality.py`, `impact.py`, `volume.py`,
`riskunits.py` and wrote §4, §5 and §7 of the validation pre-registration
**Blocked on:** nothing. Every input exists

> **This file exists to announce the work before it starts**, per this directory's convention.
> If you were about to start it, say so and I will drop it. Nothing has been written yet.

---

## Why this is next

The §10 evaluator found that **two of 27 markets in the scored panel produce no `D` in any
week, ever**, and that nothing in the package says so
([`2026-08-02 §B17`](../design/amendments-2026-08-02.md)). It was caught by counting units,
not by reading any output the package emits.

The direct consequence is already on the record: §7.3's ags episode named six markets and ran
on **five**, silently. Neither builder session would have found it.

**This is the prerequisite for the three unclaimed build items**, macro-book PCA, trend
alignment and roll congestion. Each of them produces a cross-market result, and each will do it
over a panel that can contain markets present in every input and absent from every output.

---

## What is actually broken

`coverage_report` answers "does this market have a price". `risk_coverage_report` answers "does
it have a volatility". **Neither answers the question that decides whether a market can appear
in a result at all**, which is how many weeks survive after every window has been stacked.

### A count is necessary and not sufficient: the two failures are at different rungs

| code | weeks | `dtl_sell` non-null | `damage_sell` non-null | dies at |
|---|---|---|---|---|
| 058643 | 880 | **24** | 0 | the price / notional join |
| 058644 | 178 | **178** | 0 | the extremity window, 75 weeks of `z` against a 104 minimum |

`058644` has complete exit-capacity coverage in **every one of its 178 weeks** and still scores
nothing. A report that says only "0 scoreable weeks" sends a maintainer to look at prices,
where there is nothing wrong. **The report has to name the rung.**

There is no near-miss band to tune a threshold against. Below the two lumber codes the next
markets are oats at **555** and the two wheats at **742**. It is zero or it is hundreds.

### The trap that would make the fix worse than the bug

Found by the other session while checking the figures above, and it belongs here because it is
a defect in the obvious implementation.

Group by `(market_code, market_name)` and the panel reports **six** zero-scoring rows. Four are
**phantoms**, pre-migration names sitting inside a code that scores 742 weeks:

| code | pre-migration name | code actually scores |
|---|---|---|
| 033661 | COTTON NO. 2 - NEW YORK BOARD OF TRADE | 742 |
| 073732 | COCOA - NEW YORK BOARD OF TRADE | 742 |
| 080732 | SUGAR NO. 11 - NEW YORK BOARD OF TRADE | 742 |
| 083731 | COFFEE C - NEW YORK BOARD OF TRADE | 742 |

**11 of 27 codes carry more than one `market_name`.** Heating oil (`022651`) carries five.

So a coverage report keyed on name **invents unscoreable markets in the same panel where it is
meant to find the real ones, and the invented ones outnumber the real ones three to two.**

**Key on `market_code`. Carry `market_name` as a display label only.**

And do not reach for string normalisation instead. Two of heating oil's five spellings are
`NY HARBOR ULSD` and `NY HARBOR USLD`, which differ by a transposition, so one of them is a
**typo in the CFTC source**. Any cleaner good enough to merge those is good enough to merge
things that should stay apart.

---

## Scope

**In:**

- a per-market coverage frame keyed on `market_code`, reporting scoreable weeks for `D` and the
  rung at which a market drops out
- the rungs, in the order they bite: price join, notional, volatility, volume, extremity
  window, composite window
- surfacing markets with zero scoreable weeks as a **loud** result rather than an absence,
  following the package's existing habit of raising rather than returning a plausible number
- a test that a market whose name changes mid-history appears **once**, in the shape of A.8's
  pooling-trap test

**Out:**

- changing any window, minimum or threshold. This reports what the current settings do; it does
  not argue about them
- anything touching frozen §7 or the appended §9 outcome
- back-filling lumber. Whether 27 markets should be 25 is a question for whoever reads the
  report, not for the report

## Two decisions this needs, flagged rather than defaulted

1. **Does a zero-scoring market stay in the panel?** Dropping it silently is what produced the
   ags episode running on five of six. Raising on it would break every existing caller. The
   likely answer is a loud report plus an opt-in filter, but this is exactly how `kappa` and
   `gamma` arrived and it should not be defaulted.
2. **Is the rung sequence a fixed list or derived?** A fixed list is simpler and goes stale the
   moment a rung is added, which this package has done four times in two days.

## Prior art to follow

`weight_sensitivity.sweep` and `flow.tolerance_sensitivity` for the shape. `2026-08-01 §A13`
for the standard: a coverage claim carries a measured number, not an assurance.
