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
