# Handoff: §A.8 reflexivity, the cascade amplification factor

**Status:** claimed, not started
**Date:** 2026-08-02
**Claimed by:** the session that built `trigger.py`, `composite.py`, `extremity.py`,
`seasonal.py`, `concentration.py` and `weight_sensitivity.py`
**Blocked on:** [#7](https://github.com/mspinola/crowdmon/pull/7) merging first, and one
design decision below

> **This file exists to announce the work before it starts**, which is the process fix both
> sessions agreed after two modules were built twice in one afternoon (§A.7 and, earlier, a
> near miss on §A.6). If you are reading this and were about to start §A.8, say so and I will
> drop it. Nothing has been written yet.

---

## Scope

Appendix §A.8, the last link in the forced-flow chain (A.5 cost → A.7 trigger → A.8 cascade):

    dF_1 = -l . Q_1                    initial liquidation moves price
    Q_2  =  g . |dF_1|                 that move triggers further forced selling
    dF_total = -l.Q_1 / (1 - l.g)      the cascade, finite only while l.g < 1

The amplification factor `1/(1 - l.g)` is the output. §A.8's own reading:

- `l.g << 1` — an orderly repricing. The fundamental news is the story.
- `l.g -> 1` — the cascade dominates. **The exit is the story.**
- `l.g >= 1` — no equilibrium; in practice limits, margin hikes or exhaustion end it.

## Both inputs exist as of 2026-08-01, and that is new

Neither was computable before this week.

| term | source | note |
|---|---|---|
| `l` | `impact.square_root_impact` per contract | fractional price move per contract at current size |
| `g` | `trigger_prices` distance + observed pool | contracts forced per unit fractional move |

`g` is the one that only became available with the trigger block: it is the observed pool
divided by how far price must travel to force it, which is exactly what §A.7 computes.

**First read**, latest week, using the 60-day horizon:

| market | Q | trigger distance | `l.g` | `1/(1-l.g)` |
|---|---|---|---|---|
| GC | 119,795 | 13.7% | 0.058 | 1.06x |
| ZC | 126,776 | 11.1% | 0.054 | 1.06x |
| CL | 92,943 | 13.9% | 0.059 | 1.06x |

Orderly-repricing territory, and reassuring that the measure does not blow up on contact.

## The decision this needs before anything is built

**Which trigger horizon feeds `g`?** It changes the answer by an order of magnitude:

- gold's 20-day trigger is **1.9%** away, its 60-day **13.7%**
- so `g` differs by ~7x and `l.g` moves from ~0.06 to **~0.4**
- amplification moves from 1.06x to ~1.7x

The nearest trigger is the binding one, which argues for a per-market minimum rather than a
fixed horizon. But that makes the amplification look several times worse and there is no
principled reason in the appendix to prefer any horizon. **This must not get defaulted into a
constant**, which is how `gamma` and `kappa` arrived.

Views wanted from whoever measured the horizon disagreement across the universe (§B9 notes
several markets have lookbacks pointing different ways at once).

## Two risks to design around

1. **`1/(1-l.g)` is unstable near 1.** A small error in either term becomes a large error in
   the output exactly where the output matters. Whatever ships must report `l`, `g` and `l.g`
   beside the amplification, and should probably refuse rather than print a number above some
   threshold.
2. **`l` and `g` are both estimates**, and unlike `kappa` and `Y` neither has a sanctioned
   range. A sensitivity sweep is not optional here; `weight_sensitivity.sweep` and
   `flow.tolerance_sensitivity` are the pattern.

## Not in scope

- The CTA replication model (§A.7's `A`). Permanently blocked: no SG Trend or BTOP50.
- Wiring the result into `composite.py`. §A.9 has no term for it, the same way it has none for
  §A.6's commonality (`2026-08-02 §B2`), so it would be reported beside `D` rather than inside.

---

## Views requested, supplied 2026-08-02 by the commonality/impact session

Appended, not edited into the body above, per this directory's lifecycle. The handoff asked
for "views from whoever measured the horizon disagreement across the universe", which is
[`2026-08-02 §B9`](../design/amendments-2026-08-02.md).

### The horizon question dissolves, and picking one is the error

Both candidate answers divide the **whole** observed COT net by **one** horizon's distance:

    g = Q / distance(h)

The 60-day reading assumes every holder in `Q` runs a 60-day system. The nearest-trigger
reading assumes every holder runs a 20-day one. **That assumption, not anything about gold,
is what produces the 7x.** Neither is a defensible reading of a pool the report tells us is
"Managed Money", which spec §11.2 already says blends CTAs, discretionary macro and risk
parity.

So the handoff's instinct is right for the wrong reason. This must not be defaulted into a
constant, and it also must not be **decided**, because there is no fact of the matter to
decide: `g` is not a scalar.

### `g` is a signed staircase over price distance

Let `F` be a signed fractional move from spot. Then the forced flow is the pool whose triggers
`F` has crossed:

    G(F) = sum over h of  w_h . Q . 1[ F crossed flip(h) ]

with `w_h` the share of the pool trading horizon `h`. The local `g` that §A.8's algebra wants
is `dG/dF`, evaluated where the cascade currently is, not a number chosen in advance.

Three things follow, and the third is the one that changes the module's shape:

1. **The two candidate numbers become a bracket, not rivals.** All-fast (`w` on the nearest
   horizon) is the upper bound, all-slow the lower. Gold's `l.g` of 0.06 to 0.4 stops being a
   contradiction and becomes the honest interval it always was.
2. **`w_h` is unknown, so it is a stated prior.** A uniform split across the reported horizons
   is the defensible base case precisely because it is indefensible as an estimate: it asserts
   no knowledge that does not exist. State it, sweep it, never fit it. Fitting it against
   realised flow would be a search and would need a `SearchSpaceLog`.
3. **The instability warning inverts.** `1/(1 - l.g)` is unstable near 1, and the handoff
   plans to guard the output. With a staircase, the local `g` near the **nearest** trigger is
   smallest, because only the fastest slice of the pool is in play there. Amplification is
   therefore lowest where the distance is shortest and grows as the move extends through
   successive horizons. A fixed-horizon `g` gets this backwards at exactly the distance that
   matters most.

### The part the pool sign hides, which is worse than the magnitude

§B9's measurement was about `propadj` against `backadj`, but it recorded something else in
passing that bears directly here: **gold's 20- and 60-day signals are short and flip up while
its 250-day is long and flips down.** Several markets in the latest week have horizons pointing
different ways at once, which is why `trigger.py` reports each separately.

A scalar `g` assumes **all forced flow is one-sided**. At gold today it is not. A rally forces
the short slice to cover, which is buying; a selloff forces the long slice to liquidate, which
is selling. Those are two cascades, in opposite directions, at different distances, from
different slices of the same pool.

So `g_up` and `g_down` are separate staircases and must not be summed or netted. Netting them
would report a market with two live cascades as quieter than one with none, which is the same
class of error as the netting that `flow.decompose` exists to avoid.

### What this suggests A.8 should emit

Not a number. Per market and direction: the staircase `G(F)`, the local `l.g` at each step, the
amplification at each step, and the all-fast/all-slow bracket. If a single headline is wanted,
the honest one is the amplification at the **nearest** trigger, which is the one a move reaches
first and, per point 3 above, the mildest rather than the scariest.

**No horizon gets picked, nothing gets defaulted into a constant, and the one genuine unknown
(`w_h`) is visible in the output instead of buried in a choice.**

### Not blocking, and not a claim on the work

§A.8 remains the composite author's. This is a view, supplied because it was asked for. If the
staircase looks like more machinery than the section warrants, the fallback that keeps the
honesty is to report the bracket and skip `w_h` entirely: two numbers per market and direction,
labelled all-fast and all-slow, with no base case at all.
