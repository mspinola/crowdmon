"""Correlation clustering, spec §369.

The arithmetic is Lance-Williams. What carries the risk is determinism: no RNG is only half of
it, because a tie in the distance matrix broken by position would let the caller's column
order change the dendrogram.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.futures import clustering as cl
from crowdmon.futures.clustering import ClusteringError

DATES = pd.bdate_range("2018-01-01", periods=1200)
CLASSES = {"A1": "Alpha", "A2": "Alpha", "A3": "Alpha",
           "B1": "Beta", "B2": "Beta", "B3": "Beta"}


def blocked_returns(seed: int = 0) -> pd.DataFrame:
    """Two blocks that correlate within and not across, plus one deliberate cross-block link.

    `A3` is built from `B1`'s driver, so it carries an `Alpha` label and belongs with `Beta`.
    That is §369's claim in miniature, and the yen-with-rates pair is its real-world form.
    """
    rng = np.random.default_rng(seed)
    drivers = {"Alpha": rng.normal(size=len(DATES)), "Beta": rng.normal(size=len(DATES))}
    out = {}
    for name, klass in CLASSES.items():
        source = drivers["Beta"] if name == "A3" else drivers[klass]
        out[name] = pd.Series(0.9 * source + 0.4 * rng.normal(size=len(DATES)), index=DATES)
    return pd.DataFrame(out)


# ── Determinism, which is the whole reason it is agglomerative ──────────────
def test_column_order_does_not_change_the_labels():
    """No RNG is only half of determinism. Ties are broken by position, so an unsorted input
    would let a caller's dict ordering pick the dendrogram."""
    frame = blocked_returns()
    shuffled = frame[list(reversed(frame.columns))]
    a = cl.clusters_at(cl.correlation_distance(frame), 2)
    b = cl.clusters_at(cl.correlation_distance(shuffled), 2)
    assert a.sort_index().equals(b.sort_index())


def test_repeated_runs_are_identical():
    dist = cl.correlation_distance(blocked_returns())
    assert cl.agglomerate(dist) == cl.agglomerate(dist)


def test_no_module_in_the_package_imports_sklearn():
    """The reason this is hand-written. `test_boundaries.py` allowlists pandas, numpy and
    pyarrow, so reaching for sklearn fails the boundary test rather than the import."""
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "src" / "crowdmon"
    offenders = []
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(n.split(".")[0] in {"sklearn", "scipy"} for n in names):
                offenders.append(path.name)
    assert offenders == [], f"clustering dependencies leaked in: {offenders}"


# ── The clustering itself ───────────────────────────────────────────────────
def test_two_blocks_separate_and_the_planted_defector_goes_with_its_driver():
    """§369 in miniature: `A3` carries an Alpha label and correlates with the Beta block."""
    labels = cl.clusters_at(cl.correlation_distance(blocked_returns()), 2)
    assert labels["A1"] == labels["A2"]
    assert labels["B1"] == labels["B2"] == labels["B3"]
    assert labels["A3"] == labels["B1"], "the defector clusters by correlation, not by label"
    assert labels["A3"] != labels["A1"]


def test_k_equal_to_one_and_to_n_are_the_degenerate_ends():
    dist = cl.correlation_distance(blocked_returns())
    assert cl.clusters_at(dist, 1).nunique() == 1
    assert cl.clusters_at(dist, len(dist)).nunique() == len(dist)


def test_an_out_of_range_k_is_refused():
    dist = cl.correlation_distance(blocked_returns())
    for bad in (0, -1, len(dist) + 1):
        with pytest.raises(ClusteringError, match="k must be"):
            cl.clusters_at(dist, bad)


def test_the_merge_history_is_ordered_closest_first():
    merges = cl.agglomerate(cl.correlation_distance(blocked_returns()))
    distances = [d for _l, _r, d, _s in merges]
    assert distances == sorted(distances), "average linkage must not invert"
    assert len(merges) == len(CLASSES) - 1


# ── The distance, and why the default is the metric one ─────────────────────
def test_the_metric_distance_obeys_the_triangle_inequality_where_linear_need_not():
    """Tested on a constructed correlation matrix, not on random returns.

    The property is that `1-rho` **can** violate the inequality, not that any given sample
    does. An earlier version of this test asserted a violation in the fixture and failed,
    because that fixture happens not to contain one. Asserting a possibility by hoping the
    data exhibits it is not a test of the transform.

    `rho(A,B) = rho(B,C) = 0.5`, `rho(A,C) = -0.5` is positive semi-definite (determinant 0),
    so it is a correlation matrix a real panel could produce.
    """
    rho = np.array([[1.0, 0.5, -0.5],
                    [0.5, 1.0, 0.5],
                    [-0.5, 0.5, 1.0]])
    assert np.linalg.eigvalsh(rho).min() > -1e-12, "must be a valid correlation matrix"

    def violations(d):
        n = len(d)
        return sum(1 for i in range(n) for j in range(n) for k in range(n)
                   if d[i, j] > d[i, k] + d[k, j] + 1e-12)

    linear = 1.0 - rho
    metric = np.sqrt(np.clip(2.0 * (1.0 - rho), 0.0, None))
    np.fill_diagonal(linear, 0.0)
    np.fill_diagonal(metric, 0.0)

    assert violations(linear) > 0, "1-rho is not a metric, which is why it is not the default"
    assert violations(metric) == 0, "sqrt(2(1-rho)) is"

    # And the module's own transforms agree with those formulas.
    frame = blocked_returns()
    from_module = cl.correlation_distance(frame, distance="metric").to_numpy()
    corr = frame.reindex(sorted(frame.columns), axis=1).corr().to_numpy()
    expected = np.sqrt(np.clip(2.0 * (1.0 - corr), 0.0, None))
    np.fill_diagonal(expected, 0.0)
    assert np.allclose(from_module, expected)


def test_an_unknown_distance_or_linkage_is_refused():
    frame = blocked_returns()
    with pytest.raises(ClusteringError, match="distance must be"):
        cl.correlation_distance(frame, distance="cosine")
    with pytest.raises(ClusteringError, match="linkage must be"):
        cl.agglomerate(cl.correlation_distance(frame), linkage="ward")


def test_returns_refuse_any_series_but_propadj():
    for wrong in ("unadj", "backadj"):
        with pytest.raises(ClusteringError, match="returns need"):
            cl.return_panel(["GC"], adjustment=wrong)


def test_a_pair_with_too_little_overlap_does_not_merge_first(monkeypatch):
    """A NaN distance must not be treated as zero, which is what an unguarded argmin does."""
    frame = blocked_returns()
    dist = cl.correlation_distance(frame)
    dist.iloc[0, 1] = np.nan
    dist.iloc[1, 0] = np.nan
    merges = cl.agglomerate(dist)
    first = {merges[0][0], merges[0][1]}
    assert first != {dist.columns[0], dist.columns[1]}, "nan is not the closest pair"


# ── The output that actually matters ────────────────────────────────────────
def test_cross_class_pairs_finds_the_defector_and_not_the_within_class_pairs():
    """The partition mostly restates the labels. The exceptions are the point."""
    pairs = cl.cross_class_pairs(blocked_returns(), CLASSES, min_corr=0.4)
    assert not pairs.empty
    top = pairs.iloc[0]
    assert {top["left"], top["right"]} & {"A3"}, "the planted cross-class link ranks first"
    assert top["left_class"] != top["right_class"]


def test_cross_class_pairs_is_empty_rather_than_wrong_when_nothing_qualifies():
    pairs = cl.cross_class_pairs(blocked_returns(), CLASSES, min_corr=0.999)
    assert pairs.empty
    assert list(pairs.columns) == ["left", "left_class", "right", "right_class", "correlation"]


def test_the_sweep_reports_k_rather_than_choosing_it():
    """`k` is the one free parameter and the spec gives no value, which is how gamma and
    kappa arrived."""
    dist = cl.correlation_distance(blocked_returns())
    out = cl.cluster_sweep(dist, ks=(2, 3, 4), asset_class=CLASSES)
    assert list(out["k"]) == [2, 3, 4]
    assert set(out.columns) >= {"k", "largest_cluster", "singletons", "agreement_with_class"}


def test_agreement_with_the_taxonomy_rises_with_k_rather_than_being_high_throughout():
    """Measured on the real panel: 0.132 at k=2 rising to 0.802 at k=10.

    An earlier docstring claimed high agreement was the expected result, reasoning from the
    0.410-against-0.077 correlation gap. That is wrong. Average linkage gives one large
    cluster plus singletons, so at small `k` the partition says "nearly everything together"
    against a taxonomy that says "mostly apart", and they disagree on almost every pair. A
    pair-average gap does not translate into partition agreement at any particular `k`.
    """
    dist = cl.correlation_distance(blocked_returns())
    out = cl.cluster_sweep(dist, ks=(1, 2, 4, 6), asset_class=CLASSES)
    agreement = out["agreement_with_class"].tolist()
    assert agreement[0] < agreement[-1], "agreement must rise as the partition refines"


# ── Rendering ───────────────────────────────────────────────────────────────
def test_the_block_states_the_limit_in_the_output_not_only_the_docstring():
    frame = blocked_returns()
    labels = cl.clusters_at(cl.correlation_distance(frame), 2)
    text = cl.format_cluster_block(labels, cl.cross_class_pairs(frame, CLASSES),
                                   asset_class=CLASSES)
    assert "cut ACROSS sector labels" in text
    assert "mostly restates the labels" in text
    assert "0.410" in text and "0.077" in text
    assert "—" not in text, "house style: no em dashes in output"


def test_the_module_carries_the_2008_prohibition_like_alignment_does():
    doc = cl.__doc__
    assert "2008" in doc
    assert "third engine" in doc
    assert "pre-registration" in doc
