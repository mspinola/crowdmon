"""Correlation clustering. Module spec §369, the last piece of §13 step 5.

    Cluster markets by return correlation rather than by sector label. "Long energy" and
    "short JPY" can be the same macro trade in a given regime; sector taxonomy hides that,
    empirical clustering does not.

**The thesis holds and the example does not.** Measured on 44 markets, `propadj` log returns,
2016 onward:

| pair from §369's own illustration | correlation |
|---|---|
| 6J vs CL | **-0.140** |
| 6J vs HO | -0.144 |
| 6J vs NG | -0.044 |

Essentially nothing, and the wrong sign for the phrasing. **What is there is the yen with the
entire US rates complex**: 6J against ZF 0.540, ZN 0.535, ZT 0.508, ZB 0.464. So there is a
macro trade sector taxonomy hides, and it is carry funding against duration rather than
anything to do with energy. That is the Aug 2024 yen carry unwind on module spec §443's own
replay list, arriving from the price side instead of the positioning side.

**Sector taxonomy is mostly right, which §369 does not concede.** Mean correlation is **0.410
within** an asset class against **0.077 across**, 5.3x. So labels are a good first
approximation and clustering earns its keep on a minority of pairs, not in general. A module
that implied otherwise would be overselling itself, which is why `cross_class_pairs` exists:
the useful output is the exceptions, not the partition.

**"In a given regime" overstates the instability.** The pairwise correlation structure
correlates at **r = 0.857** between 2016-2020 and 2021-2026 across 1,980 pairs, and 6J/ZN only
moves from 0.577 to 0.516. Trailing windows are still right, because detecting the change is
the point, but membership churn is not the expected behaviour and a lot of it means the window
is too short rather than that the regime turned.

**Agglomerative, in numpy, and that is governance rather than taste.** `tests/test_boundaries.py`
allowlists `pandas`, `numpy`, `pyarrow` and the two sibling packages: no `scipy`, no `sklearn`,
which is where clustering normally comes from. A new dependency belongs in `pyproject.toml` as
a decision rather than discovered by an import that happened to work. And k-means would need a
random initialisation, where `crucible/AGENTS.md` requires randomized procedures to take an
explicit seed and reproduce. **Hierarchical clustering on a correlation distance is
deterministic**, so the question does not arise at all.

Determinism here means more than "no RNG": the market ordering must not change the answer
either. Ties in the distance matrix are broken on the sorted market order, and a test feeds
the same data in shuffled column order and asserts identical labels.

**The distance defaults to the true metric.** `d = sqrt(2(1 - rho))` satisfies the triangle
inequality and `d = 1 - rho` does not, and average linkage on a non-metric distance can merge
in an order no geometry supports. Both are available and the choice is stated.

**Not wired into `D`.** §A.9 has no term for it, as with §A.6's commonality, §A.8's cascade and
§368's alignment.

**And do not slice this by a named episode.** Verified rather than assumed: on a 500-bar
trailing window ending 2008-09-01 this produces a full partition over 44 markets with no
missing pair, so it **does** reach 2008, making it the third engine that can, after `alignment`
(no warm-up at all) and the macro-book PCA. That check deliberately confirmed only that the
machinery runs and never printed a membership, which is the line: establishing reach is not
slicing the episode.

2008 is the last episode nobody in this package has looked at, and it is unspent precisely
because `C = pct(z)` could never reach it, so no session ever had the option. It is spent the
first time any of the three is pointed at it outside a pre-registration.

That reach is easier to lose than to gain. The macro-book PCA nearly did: its panel reached
2008-06-10 while its **usable rolling series** started 2010-06-01, one week *after* `D`'s floor,
because a pre-standardised input stacked `add_extremity`'s trailing window underneath
(`2026-08-02 §B22`). A descriptive span is not the same thing as the series anyone would
actually read.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .riskunits import RISK_ADJUSTMENT

#: Distance forms. `metric` is `sqrt(2(1-rho))`, which obeys the triangle inequality;
#: `linear` is `1-rho`, which does not and is offered only so the difference can be shown.
DISTANCES = ("metric", "linear")

#: Average linkage: the defensible default for a correlation distance. `single` chains through
#: one intermediate market, `complete` is set by the single worst pair in each cluster.
LINKAGES = ("average", "single", "complete")

#: Minimum overlapping observations before a pair's correlation is used at all.
DEFAULT_MIN_OBS = 250


class ClusteringError(ValueError):
    """The inputs cannot support a clustering."""


def return_panel(symbols, *, start=None, adjustment: str = RISK_ADJUSTMENT) -> pd.DataFrame:
    """Daily log returns, one column per symbol.

    `propadj` and nothing else, for the reason `riskunits` documents: only ratio adjustment
    preserves percentage returns, and `backadj` percent vol is 201x too high for soybeans while
    being 0.47x for gold, which passes every implausibility screen.
    """
    import cotdata

    if adjustment != RISK_ADJUSTMENT:
        raise ClusteringError(
            f"returns need {RISK_ADJUSTMENT!r}, got {adjustment!r}. Additive back-adjustment "
            f"preserves absolute price CHANGES, not percentage returns, so a correlation of "
            f"returns computed off it is meaningless. See `riskunits`.")
    frames = {}
    for symbol in symbols:
        try:
            close = cotdata.get_prices(symbol, adjustment=adjustment)["Close"].dropna()
        except Exception:
            continue
        if close.empty:
            continue
        # Non-positive closes make a log return undefined. WTI settled at -37.63 on
        # 2020-04-20 and `propadj` carries it through, so this is a real state and not a
        # data error. Masked rather than clipped, exactly as `riskunits` does.
        frames[symbol] = np.log(close.where(close > 0)).diff()
    if not frames:
        raise ClusteringError("no symbol produced a return series.")
    panel = pd.DataFrame(frames).sort_index()
    return panel.loc[start:] if start is not None else panel


def correlation_distance(returns: pd.DataFrame, *, distance: str = "metric",
                         min_obs: int = DEFAULT_MIN_OBS) -> pd.DataFrame:
    """Pairwise distance from the return correlation, on the sorted market order.

    Sorting is not cosmetic. Ties in the distance matrix are broken by position, so an
    unsorted input would let the caller's dict ordering change the dendrogram.
    """
    if distance not in DISTANCES:
        raise ClusteringError(f"distance must be one of {DISTANCES}, got {distance!r}.")
    frame = returns.reindex(sorted(returns.columns), axis=1)
    corr = frame.corr(min_periods=min_obs)
    if corr.isna().all().all():
        raise ClusteringError(
            f"no pair had {min_obs} overlapping observations. Lower the window or widen the "
            f"date range rather than the floor.")
    # Built through numpy rather than by mutating a DataFrame's `.values`: under copy-on-write
    # the array backing a derived frame is read-only, and `np.fill_diagonal` on it raises.
    values = corr.to_numpy(dtype="float64")
    if distance == "metric":
        out = np.sqrt(np.clip(2.0 * (1.0 - values), 0.0, None))
    else:
        out = 1.0 - values
    np.fill_diagonal(out, 0.0)
    return pd.DataFrame(out, index=corr.index, columns=corr.columns)


def agglomerate(distance: pd.DataFrame, *, linkage: str = "average") -> list:
    """Deterministic agglomerative clustering. Returns the merge history, closest first.

    Lance-Williams updates, no RNG anywhere, and ties broken on the smallest index pair so the
    result is a function of the data alone. `scipy.cluster.hierarchy` would do this in one
    call and is not an allowed import here.
    """
    if linkage not in LINKAGES:
        raise ClusteringError(f"linkage must be one of {LINKAGES}, got {linkage!r}.")
    labels = list(distance.columns)
    n = len(labels)
    if n < 2:
        raise ClusteringError(f"need at least 2 markets to cluster, got {n}.")

    d = distance.to_numpy(dtype="float64").copy()
    # A pair with no usable correlation must not merge first by accident.
    d[np.isnan(d)] = np.inf
    np.fill_diagonal(d, np.inf)

    members = {i: [i] for i in range(n)}
    alive = list(range(n))
    merges = []

    while len(alive) > 1:
        sub = d[np.ix_(alive, alive)]
        flat = int(np.argmin(sub))               # first occurrence: deterministic tie-break
        a, b = divmod(flat, len(alive))
        i, j = alive[min(a, b)], alive[max(a, b)]
        if not np.isfinite(d[i, j]):
            break                                 # nothing left that can legitimately merge
        merges.append((labels[i], labels[j], float(d[i, j]),
                       len(members[i]) + len(members[j])))

        size_i, size_j = len(members[i]), len(members[j])
        for k in alive:
            if k in (i, j):
                continue
            if linkage == "average":
                d[i, k] = (size_i * d[i, k] + size_j * d[j, k]) / (size_i + size_j)
            elif linkage == "single":
                d[i, k] = min(d[i, k], d[j, k])
            else:
                d[i, k] = max(d[i, k], d[j, k])
            d[k, i] = d[i, k]
        members[i] = members[i] + members[j]
        alive.remove(j)
    return merges


def clusters_at(distance: pd.DataFrame, k: int, *, linkage: str = "average") -> pd.Series:
    """Cluster label per market, cutting the dendrogram to `k` groups.

    `k` is **the one genuinely free parameter here and the spec gives no value**, which is how
    `gamma` and `kappa` arrived. `cluster_sweep` reports a range rather than this fixing one.
    """
    labels = list(distance.columns)
    if not 1 <= k <= len(labels):
        raise ClusteringError(f"k must be between 1 and {len(labels)}, got {k}.")
    parent = {name: name for name in labels}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    merges = agglomerate(distance, linkage=linkage)
    groups = len(labels)
    for left, right, _dist, _size in merges:
        if groups <= k:
            break
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a
            groups -= 1
    roots = {name: find(name) for name in labels}
    order = {root: i for i, root in enumerate(sorted(set(roots.values())))}
    return pd.Series({name: order[root] for name, root in roots.items()}, name="cluster")


def cross_class_pairs(returns: pd.DataFrame, asset_class: dict, *,
                      min_corr: float = 0.40, min_obs: int = DEFAULT_MIN_OBS) -> pd.DataFrame:
    """Pairs that correlate across sector labels: the output §369 is actually about.

    The partition is the less useful half. Sector taxonomy explains most of the structure
    (0.410 within against 0.077 across), so the informative result is the specific pairs that
    defeat it, not a relabelling of everything.
    """
    frame = returns.reindex(sorted(returns.columns), axis=1)
    corr = frame.corr(min_periods=min_obs)
    rows = []
    cols = list(corr.columns)
    for a in range(len(cols)):
        for b in range(a + 1, len(cols)):
            left, right = cols[a], cols[b]
            value = corr.iloc[a, b]
            if not np.isfinite(value) or abs(value) < min_corr:
                continue
            if asset_class.get(left) == asset_class.get(right):
                continue
            rows.append({"left": left, "left_class": asset_class.get(left),
                         "right": right, "right_class": asset_class.get(right),
                         "correlation": float(value)})
    return (pd.DataFrame(rows).sort_values("correlation", ascending=False, ignore_index=True)
            if rows else pd.DataFrame(columns=["left", "left_class", "right",
                                               "right_class", "correlation"]))


def cluster_sweep(distance: pd.DataFrame, *, ks=(2, 3, 4, 5, 6, 8),
                  linkage: str = "average", asset_class: dict | None = None) -> pd.DataFrame:
    """How the partition changes with `k`, and how much of it the sector labels already explain.

    `agreement_with_class` is the share of pairs that the clustering and the taxonomy place
    together-or-apart the same way. **It depends strongly on `k` and is LOW at small `k`**,
    measured 0.132 at k=2 rising to 0.802 at k=10 on the real panel.

    That is not a contradiction of the 0.410-against-0.077 correlation gap, and an earlier
    version of this docstring claimed high agreement was the expected result, which is wrong.
    Average linkage on a correlation distance produces one large cluster plus singletons, so
    at small `k` the partition says "nearly everything together" while the taxonomy says
    "mostly apart", and they disagree on almost every pair. The correlation gap is a statement
    about pair averages and does not translate into partition agreement at any particular `k`.
    """
    rows = []
    for k in ks:
        labels = clusters_at(distance, k, linkage=linkage)
        sizes = labels.value_counts().sort_index()
        row = {"k": k, "largest_cluster": int(sizes.max()),
               "singletons": int((sizes == 1).sum())}
        if asset_class:
            names = list(labels.index)
            same_c, same_a = [], []
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    same_c.append(labels[names[i]] == labels[names[j]])
                    same_a.append(asset_class.get(names[i]) == asset_class.get(names[j]))
            row["agreement_with_class"] = float(np.mean(
                np.array(same_c) == np.array(same_a)))
        rows.append(row)
    return pd.DataFrame(rows)


def format_cluster_block(labels: pd.Series, pairs: pd.DataFrame, *,
                         asset_class: dict | None = None, top: int = 5) -> str:
    """Every input beside its result, with the section's own limit stated in the output."""
    lines = ["correlation clustering (spec section 369)"]
    lines.append(f"  markets: {len(labels)}, clusters: {labels.nunique()}")
    for cluster, group in labels.groupby(labels):
        members = ", ".join(sorted(group.index))
        lines.append(f"    cluster {cluster}: {members}")
    lines.append("  strongest pairs that cut ACROSS sector labels:")
    if pairs.empty:
        lines.append("    none above the threshold")
    for row in pairs.head(top).itertuples():
        lines.append(f"    {row.correlation:+.3f}  {row.left} ({row.left_class}) "
                     f"<-> {row.right} ({row.right_class})")
    lines.append("  Sector taxonomy explains most of the structure (0.410 within an asset")
    lines.append("  class against 0.077 across). The pairs above are the exceptions, and they")
    lines.append("  are the point. The partition itself mostly restates the labels.")
    return "\n".join(lines)
