# Handoff: correlation clustering, spec §369

**Status:** **COMPLETE**, shipped as `futures/clustering.py`. Findings in `2026-08-02 §B21`
**Date:** 2026-08-02
**Claimed by:** the session that built `composite.py`, `trigger.py`, `reflexivity.py`,
`roll.py`, `alignment.py`, `extremity.py`, `seasonal.py`, `concentration.py` and
`weight_sensitivity.py`
**Blocked on:** nothing. Measured below

> Announced before the first line of code, per this directory's convention. If you were about
> to start it, say so and I will drop it.

---

## Scope

Module spec §369:

> **Correlation clustering.** Cluster markets by return correlation rather than by sector
> label. "Long energy" and "short JPY" can be the same macro trade in a given regime; sector
> taxonomy hides that, empirical clustering does not.

## Measured before claiming, and the spec's own example does not hold

44 markets, daily `propadj` log returns, 2016 onward, 2,730 days.

### Sector taxonomy is mostly right, which the section does not concede

| | mean correlation |
|---|---|
| **within** an asset class (107 pairs) | **0.410** |
| **across** asset classes (839 pairs) | **0.077** |

**5.3x higher within than across.** So sector labels capture most of the structure, and any
claim that they "hide" the relationships has to be a claim about a minority of pairs rather
than about the taxonomy in general. Worth stating plainly because §369 reads as though the
taxonomy were actively misleading, and on this data it is mostly a good first approximation.

### The section's illustrative pair is not in the data

"Long energy and short JPY can be the same macro trade":

| pair | correlation |
|---|---|
| 6J vs CL | **-0.140** |
| 6J vs HO | -0.144 |
| 6J vs RB | -0.106 |
| 6J vs NG | -0.044 |

Essentially nothing, and the sign is the opposite of what the phrasing implies.

### The real cross-class cluster is the yen with the whole US rates complex

| pair | correlation |
|---|---|
| **6J vs ZF** | **0.540** |
| 6J vs ZN | 0.535 |
| 6J vs ZT | 0.508 |
| 6J vs ZB | 0.464 |
| HG vs 6A | 0.442 |
| EMD vs 6M | 0.415 |

**6J-with-rates exceeds the average within-class pair (0.410).** So §369's *thesis* is
supported and its *example* is not: there is a macro trade that sector taxonomy hides, and it
is carry funding against duration rather than anything to do with energy. That is exactly the
Aug 2024 yen carry unwind the spec's own §443 replay list names, arriving from the price side.

### "In a given regime" overstates the instability

| | |
|---|---|
| correlation of the pairwise correlation structure, 2016-2020 against 2021-2026 | **r = 0.857** on 1,980 pairs |
| 6J vs ZN, 2016-2020 | 0.577 |
| 6J vs ZN, 2021-2026 | 0.516 |

The structure moves, but it is far more persistent than "in a given regime" suggests. A
rolling clustering is still the right shape, because the point is to *detect* the change, but
nobody should expect the membership to churn.

## The constraint that decides the implementation

**`tests/test_boundaries.py` allowlists `pandas`, `numpy`, `pyarrow`, `cotdata` and
`marketdata`. There is no `scipy` and no `sklearn`**, which is where clustering normally comes
from. That is deliberate: a new dependency belongs in `pyproject.toml` as a decision, not
discovered by an import that happened to work.

So the clustering is written in numpy. **Agglomerative, not k-means**, and the reason is
governance rather than taste: k-means needs a random initialisation, and `crucible/AGENTS.md`
requires randomized procedures to take an explicit seed and reproduce. Agglomerative
hierarchical clustering on a correlation distance is **deterministic**, which removes the
question entirely.

`alignment.py` already carries the same pattern: `_rank_corr` computes Pearson-on-ranks because
`Series.corr(method="spearman")` delegates to scipy.

## Four decisions to flag rather than default

1. **How many clusters.** The one genuinely free parameter, and there is no principled value.
   It gets reported across a range rather than fixed, in the spirit of `weight_sensitivity`.
2. **Linkage.** Average linkage is the defensible default for a correlation distance; single
   linkage chains and complete linkage is dominated by one bad pair. To be stated and swept.
3. **The window.** Full-sample clustering is lookahead and regime-blind. Trailing only.
4. **Distance.** `d = 1 - rho` or `sqrt(2(1 - rho))`, the latter being a true metric. They give
   different dendrograms and only one satisfies the triangle inequality.

## What this must not do

- **Must not be wired into `D`.** §A.9 has no term for it, as with §A.6, §A.8 and §368.
- **Must not use anything but `propadj`** for returns, per `riskunits` and `trigger`.
- **Must not look at 2008**, on the same terms as `alignment.py` and the macro-book PCA. This
  engine will also reach it, which makes three, and the episode is spent the first time any of
  them is sliced by a named window.

---

## Outcome, appended 2026-08-02

Shipped as `futures/clustering.py`, 17 tests. Findings in `2026-08-02 §B21`, reproducer
`docs/analysis/reproduce.py` section 19.

**Every measurement in this handoff held**, and the clustering vindicated the finding that
motivated it: **at `k = 8` the partition puts `{6J, ZB, ZF, ZN, ZT}` in a cluster of its own**,
so the yen-with-rates link is not just a pair table, it survives as a group.

**One claim in the first draft of the module was wrong.** `cluster_sweep`'s docstring said high
agreement with the taxonomy was the expected result, reasoning from 0.410 against 0.077.
Measured, agreement is **0.132 at k=2** rising to **0.802 at k=10**: lowest exactly where the
claim predicted it highest. Average linkage produces one large cluster plus singletons, so at
small `k` the partition disagrees with the taxonomy on nearly every pair. A pair-average gap
does not become partition agreement. Corrected, with a test asserting the direction.

**All four flagged decisions were taken as flagged.** `k` swept rather than fixed; average
linkage stated with `single` and `complete` available; trailing rather than full-sample; and
the distance defaulting to the true metric `sqrt(2(1-rho))` with `1-rho` offered and its
triangle-inequality failure pinned by a test on a constructed correlation matrix rather than
hoped for in a sample.

**The prohibitions held.** Not wired into `D`, `propadj` refused for anything else, and
**2008 has not been looked at**. This is the third engine that can reach it.

**Status: closed.**
