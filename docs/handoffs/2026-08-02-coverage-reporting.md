# Handoff: coverage reporting, which rung dropped a market and why

**Status:** complete (PR #15), corrected twice the same day (PR #17, **PR #19**). Closed out
2026-08-02, see [Close-out](#close-out-2026-08-02).
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


---

## Outcome, 2026-08-02

Shipped as `futures/coverage.py`: `coverage_ladder`, `unscoreable`, `coverage_summary`,
`format_coverage`. 19 new tests, 13 offline and 6 live. Full suite 367 passed, 2 skipped.

**Both decisions were taken the way the handoff proposed, and are recorded here rather than
left implicit.**

1. **A zero-scoring market stays in the panel.** `unscoreable` returns them; nothing filters.
   Silently dropping is what let the pre-registration's ags episode name six markets and run
   on five, and a `raise` would break every existing caller for a condition that has been
   true for the whole life of the package.
2. **The rung sequence is a hand-written list**, `LADDER`, because the columns live at two
   different grains and no single frame knows the whole chain. That is itself part of why the
   gap survived. The staleness a hand-written list invites is caught by
   `test_the_ladder_covers_every_column_the_composite_consumes`, which fails when a rung is
   added upstream and not added here.

### What the ladder actually reports

    058643  RANDOM LENGTH LUMBER   weeks=880  price=37   extremity_z=0   DROPS AT extremity_z
    058644  LUMBER                 weeks=178  price=178  extremity_z=75  DROPS AT composite

**The handoff's premise was right and its detail was slightly wrong.** It predicted `058643`
would drop at the price join. It drops at `extremity_z`: 37 weeks of price out of 880 is not
enough to ever fill a standardisation window, so the first rung that reaches **zero** is two
rungs later than the rung that caused it. The distinction matters for how the output reads,
and `drops_at` names the first zero rather than the root cause, so the full ladder has to be
printed beside it. `format_coverage` does.

`058644` behaves exactly as predicted: complete at every rung including `exit_duration=178`,
then `composite=0`.

### The rename trap, measured on the real panel

    codes carrying more than one name : 11 of 27
    zero-scoring, keyed on code       : 2
    zero-scoring, keyed on code+name  : 6

The four phantoms are the pre-migration NYBOT names for cotton, cocoa, sugar and coffee, each
inside a code scoring 742 weeks. Pinned by `test_a_market_that_changed_name_appears_once`, in
the shape of A.8's pooling-trap test.

Reproducer: `docs/analysis/reproduce.py` section 17.


---

## Correction, 2026-08-02, same day

`2026-08-02 §B18`, filed by the other session against `§B17` which it also wrote, found two
defects in what shipped in #15. Both verified here before fixing.

**1. `LADDER` skipped the three terms `D` is built from.** It went straight from `extremity_z`
to `damage_{side}`, omitting `phi_pct`, `illiquidity_{side}` and `crowding_{long,short}`. So
`058644` was reported as dropping at `composite` when it drops one rung earlier at `crowding`.

**The guard test had the same blind spot as the ladder it guarded**, which is why it passed:
it checked the columns `add_composite` *emits* and not the ones it *computes*. It now checks
both, and that is the more useful half.

**2. The ladder is not monotonic, and the live test asserted that it was.** `holder_fragility`
is price-free, so a market starved of prices can carry far more weeks of it than of anything
downstream of one: `058643` has **880** weeks of `phi` against **24** of `dtl_sell`, a 36x
rise in the middle of the ladder. `PRICE_FREE` now declares those rungs, `format_coverage`
stars them, and the live test pins that a rise **occurs** rather than asserting it cannot.

Corrected output:

    058643  weeks=880  extremity_z=0   holder_fragility*=880  illiquidity=0   DROPS AT extremity_z
    058644  weeks=178  extremity_z=75  holder_fragility*=178  illiquidity=75  DROPS AT crowding

**Both terminate at `crowding`, for unrelated reasons.** That is the strongest argument for
this module's design rather than against it: a label naming one rung is insufficient precisely
because two markets can share it and mean different things, which is why the full ladder is
printed beside it.


---

## Close-out, 2026-08-02

Everything above is preserved as issued. This records what the status line was missing and
one measurement taken at close-out, so the next reader is not left with an open question the
handoff never knew it had.

### A third correction was never recorded

The status line said "complete (PR #15), corrected same day (PR #17)". There was a **third**
correction, **PR #19** (`7ff5d06`), which touched `coverage.py` and is the only one of the
three that changed what the module *says about itself*:

> The module docstring's table said `058643` "dies at the price join". `drops_at` returns
> `extremity_z` for it, and `price` is 37 of 880 rather than 0, so the ladder cannot report
> it at the price join in its own vocabulary. §B18 had already corrected the handoff that
> guessed it; the docstring kept the guess.

It also settled a contradiction a reader would otherwise hit head-on. §B18 says the two
lumber codes "fail at the SAME rung". That is true of the **terminal** rung and false of
`drops_at`, which is the first zero and is two rungs earlier for `058643`. Both statements
are now on the record with the distinction named.

Status line corrected. Nothing else in the body is touched.

### The rename trap has a mirror image, and it was measured rather than assumed

The module keys on `market_code`, which kills the four phantoms (one code, several names).
It does **not** handle the opposite shape, one instrument carrying several codes, and
[`§B26`](../design/amendments-2026-08-02.md) and `§B27` established after this handoff closed
that **the two unscoreable markets are the two halves of one migrated contract**: `058643`
and `058644` overlap in 7 weeks of 1051 and both carry symbol `LBR`.

That raises a question this handoff could not have asked: **is "2 of 27 score nothing" a real
finding, or an artifact of the split?** Separately the codes hold 37 and 178 priced weeks;
merged they hold **208 contiguous** priced weeks, twice the 104-week extremity window, which
makes "artifact" look like the obvious answer.

Measured end to end, it is not:

| rung | `058643` | `058644` | merged |
|---|---|---|---|
| `price` | 37 | 178 | **208** |
| `extremity_z` | 0 | 75 | **96** |
| `illiquidity` | 0 | 75 | **92** |
| `crowding` | 0 | 0 | **0** |

Every rung rises substantially and the verdict does not move. `C = pct(z)` stacks a second
three-year window on the 96 z values and 96 does not fill it. **Lumber is unscoreable because
it has four years of prices against a measure needing six, not because its code changed.**
The headline moves from "2 of 27" to "1 of 26" purely by counting one instrument once.

Full detail, including the plausible wrong answer that survives one round of checking, is
[`§B30`](../design/amendments-2026-08-02.md). Reproducer:
`docs/analysis/reproduce.py`, the `lumber_is_one_instrument` block.

### No code change follows, deliberately

Teaching `coverage` to merge migrated codes would change the report's row count and no
conclusion in it, and this handoff's own Scope puts "changing any window, minimum or
threshold" out of bounds. It is a build item for whoever wants it, not a correction, and it
is now backed by a measurement saying what it would and would not buy.

### Both flagged decisions stand

The two decisions §"Two decisions this needs" refused to default are unchanged four PRs
later: a zero-scoring market still stays in the panel and nothing filters it, and `LADDER` is
still a hand-written list guarded by
`test_the_ladder_covers_every_column_the_composite_consumes`. That guard has since earned its
place: §B18 found the ladder skipping three rungs, and the same test now checks the columns
`add_composite` **computes** and not only those it emits, which is the half that was blind.

**Nothing is left open.**
