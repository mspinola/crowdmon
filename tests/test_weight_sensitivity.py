"""Weight sensitivity: module spec §6.3 and appendix §A.11.

The point of the module is to answer "how much of this result is judgement", so the tests are
mostly about the sweep being an honest one: that the plausible class really is plausible,
that it is reproducible, and that a weighting known to be wrong is detectably wrong.
"""
import numpy as np
import pandas as pd
import pytest

from crowdmon.core import config as cfg
from crowdmon.futures import (
    flat_phi_identity,
    plausible_variants,
    reference_variants,
    summarise,
    sweep,
)
from crowdmon.futures.weight_sensitivity import SensitivityError, _spearman

ORDER = ["managed_money", "nonreportable", "other_reportable", "swap", "producer_merchant"]


def _order(weights: dict) -> list:
    return [k for k, _ in sorted(weights.items(), key=lambda kv: -kv[1])]


# ── The plausible class ─────────────────────────────────────────────────────
def test_every_variant_preserves_the_configured_ordering():
    """§6.3's judgement is an ordering before it is a set of values: a levered fund is more
    forceable than a retail account, which is more forceable than a producer. Confidence in
    that ranking is far higher than in "exactly 0.4", so the plausible class is jitter that
    keeps it. A weighting that says producers are the most forceable is a different claim,
    not a rival estimate of the same one."""
    for variant in plausible_variants(n=100, jitter=0.15, seed=1):
        assert _order(variant) == ORDER
        assert all(0 < v <= 1.0 for v in variant.values())


def test_the_sweep_is_reproducible():
    """A sensitivity result that cannot be reproduced is not evidence of anything."""
    a = plausible_variants(n=20, seed=7)
    b = plausible_variants(n=20, seed=7)
    assert a == b
    assert plausible_variants(n=20, seed=8) != a


def test_a_floor_stops_a_perturbation_becoming_an_exclusion():
    """Producer/Merchant sits at 0.1, so a naive jitter of 0.15 would zero it. A zero weight
    is not a small weight: it removes the category from every sum it belongs in, which is a
    different experiment."""
    for variant in plausible_variants(n=50, jitter=0.15, seed=2, floor=0.02):
        assert variant["producer_merchant"] >= 0.02


def test_tight_spacing_is_handled_by_retrying_not_by_truncating():
    """Closely spaced weights make an order-preserving draw rare, not impossible: with five
    weights 0.01 apart and jitter of 0.4, roughly one draw in 120 survives. The function
    retries until it has the count asked for, so the caller always gets `n` variants or an
    error, never a quietly short sample that would understate the spread."""
    tight = {"a": 0.50, "b": 0.49, "c": 0.48, "d": 0.47, "e": 0.46}
    variants = plausible_variants(tight, n=50, jitter=0.4, seed=0)
    assert len(variants) == 50
    for variant in variants:
        assert _order(variant) == ["a", "b", "c", "d", "e"]


def test_an_out_of_range_jitter_is_refused():
    with pytest.raises(SensitivityError, match=r"\(0, 0.5\]"):
        plausible_variants(n=5, jitter=0.9)


# ── The flat baseline is degenerate, and it is algebra ──────────────────────
def test_flat_weights_make_phi_a_function_of_spreading_alone(history_panel):
    """`sum_c (L_c + S_c) = 2(OI - spreading)`, so `Phi_flat = 1 - spreading/OI`.

    This is the fact that reframes what `Phi` is. Under equal weights it carries no
    cross-market information about positioning at all, which means every cross-market
    difference in a real `Phi` comes from the weight table rather than from the data. Checked
    against the store rather than asserted, because it depends on the canonical schema
    excluding spreading from the category rows.
    """
    identity = flat_phi_identity(history_panel)
    assert len(identity) > 3_000
    assert identity["residual"].abs().max() < 1e-12


def test_flat_is_reported_as_a_reference_not_included_in_the_plausible_set():
    references = reference_variants()
    assert set(references) == {"flat", "crowd_only", "inverted"}
    assert _order(references["flat"]) != ORDER or len(set(references["flat"].values())) == 1
    for variant in plausible_variants(n=30, seed=3):
        assert len(set(variant.values())) > 1


# ── The sweep detects a weighting that is actually wrong ───────────────────
def test_inverting_the_ordering_destroys_the_ranking(history_panel):
    """The wrongness check. If reversing §6.3's judgement left the ranking intact, the
    weights would not be doing anything and neither would `Phi`."""
    week = history_panel[history_panel["report_date"] == history_panel["report_date"].max()]
    results = sweep(week, reference_variants(), top_n=3).set_index("variant")
    assert results.loc["inverted", "phi_corr"] < 0, "inverted weights must anti-correlate"


def test_plausible_variants_move_the_ranking_less_than_inverting_does(history_panel):
    week = history_panel[history_panel["report_date"] == history_panel["report_date"].max()]
    plausible = sweep(week, plausible_variants(n=15, seed=4), top_n=3)
    inverted = sweep(week, {"inverted": reference_variants()["inverted"]}, top_n=3)
    assert plausible["phi_corr"].min() > inverted["phi_corr"].iloc[0]


# ── Spearman without scipy ─────────────────────────────────────────────────
def test_spearman_is_pearson_on_ranks_and_needs_no_scipy():
    """`Series.corr(method="spearman")` delegates to scipy, which is not a declared
    dependency: the boundary test allowlists pandas, numpy, pyarrow and the two siblings.
    Ranking first and taking Pearson is the definition and needs neither."""
    a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert _spearman(a, a * 3.0) == pytest.approx(1.0)       # monotone, not linear
    assert _spearman(a, -a) == pytest.approx(-1.0)
    # Two adjacent swaps in five: sum d^2 = 4, so rho = 1 - 6(4)/(5 . 24) = 0.8.
    assert _spearman(a, pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])) == pytest.approx(0.8)
    assert np.isnan(_spearman(pd.Series([1.0]), pd.Series([2.0])))


def test_no_module_in_the_package_imports_scipy():
    """Guards the reason `_spearman` exists at all."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "src" / "crowdmon"
    offenders = [p.name for p in root.rglob("*.py") if "scipy" in p.read_text()]
    assert offenders == ["weight_sensitivity.py"], (
        f"scipy referenced outside the docstring explaining its absence: {offenders}")


# ── The summary a caption needs ────────────────────────────────────────────
def test_summarise_reports_the_worst_case_not_only_the_average(history_panel):
    week = history_panel[history_panel["report_date"] == history_panel["report_date"].max()]
    out = summarise(sweep(week, plausible_variants(n=20, seed=5), top_n=3), top_n=3)
    assert out["top_n_overlap_min"] <= out["top_n_overlap_median"]
    assert out["worst_case_top_n_lost"] == 3 - out["top_n_overlap_min"]
    assert out["rank_corr_min"] <= out["rank_corr_median"]


def test_the_default_weights_are_their_own_baseline():
    """Sweeping the configured weights against themselves must be a perfect match, which is
    the sanity check that the comparison machinery is aligned at all."""
    # Two markets, not one: a single-market frame makes every correlation undefined and
    # numpy warns about the degrees of freedom rather than the test saying anything.
    rows = []
    for market, scale in (("T1", 1.0), ("T2", 0.4)):
        for category, long_, short_ in [("managed_money", 50_000, 10_000),
                                        ("producer_merchant", 20_000, 60_000),
                                        ("swap", 15_000, 12_000),
                                        ("other_reportable", 10_000, 13_000),
                                        ("nonreportable", 5_000, 5_000)]:
            rows.append({"report_date": pd.Timestamp("2026-01-06"), "market_code": market,
                         "market_name": market, "report_type": "disaggregated",
                         "combined": False, "category": category,
                         "long_contracts": int(long_ * scale),
                         "short_contracts": int(short_ * scale), "spread_contracts": 0,
                         "open_interest": 100_000})
    frame = pd.DataFrame(rows)
    out = sweep(frame, {"same": dict(cfg.DISAGGREGATED_WEIGHTS)}, top_n=1)
    assert out["top_n_overlap"].iloc[0] == 1
    assert out["phi_corr"].iloc[0] == pytest.approx(1.0)
    assert out["rank_corr"].iloc[0] == pytest.approx(1.0)
