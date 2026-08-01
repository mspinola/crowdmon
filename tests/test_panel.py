"""The canonical panel: the open-interest identity, and the loads that must refuse.

The identity is reported as a rate rather than raised on, which is the handoff's
instruction and the right call: the identity failing is information about the parse, and a
loader that refuses rather than telling you the rate has hidden the signal worth having.
"""
import pandas as pd
import pytest

from crowdmon.futures import exit_pressure, oi_identity, oi_identity_summary, rank_markets
from crowdmon.futures.io import PanelError, require_single_series
from crowdmon.futures.pressure import PressureError, top_by


# ── The open-interest identity (handoff §7) ─────────────────────────────────
def test_the_identity_holds_over_the_whole_committed_history(history_panel):
    """`Σ long == Σ short` and `Σ long + spreading == OI`, 2006 to 2026.

    Both hold exactly on Disaggregated, which is why this asserts zero exceptions rather
    than a tolerance. Every long contract in a futures market is somebody's short, and
    Disaggregated publishes spreading per category so the open-interest side closes too.
    Legacy does neither (it drops non-commercial spreading entirely), which is why Legacy
    is not loadable through this module at all.
    """
    ident = oi_identity(history_panel)
    assert len(ident) > 3_000
    assert ident["balanced"].all(), (
        f"{int((~ident['balanced']).sum())} market-weeks break the zero-sum identity. "
        f"That is a category-mapping fault, not a market event.")
    assert ident["oi_closes"].all()


def test_the_exception_rate_is_reported_and_stable_by_year(history_panel):
    """"Stable over history" is only answerable as a series: a flat zero for twenty years
    and a zero that started last month are different facts."""
    by_year = oi_identity_summary(history_panel, by_year=True)
    assert len(by_year) >= 20
    assert (by_year["unbalanced_rate"] == 0.0).all()
    assert (by_year["oi_gap_rate"] == 0.0).all()
    assert by_year["market_weeks"].min() > 0


def test_the_summary_is_a_report_not_a_gate(history_panel):
    """Corrupting one week must show up as a rate, not as an exception. A loader that
    raised here would destroy the signal it was asked to measure."""
    broken = history_panel.copy()
    row = broken.index[broken["category"] == "managed_money"][0]
    broken.loc[row, "long_contracts"] += 12_345

    summary = oi_identity_summary(broken)
    assert summary["unbalanced"].iloc[0] == 1
    assert 0 < summary["unbalanced_rate"].iloc[0] < 0.001
    assert summary["worst_abs_imbalance"].iloc[0] == 12_345


def test_open_interest_is_not_summed_across_category_rows(make_panel):
    """It is the MARKET total repeated on every category row, because that is the shape of
    the CFTC file. Summing it would multiply it by the category count and quietly divide
    every ratio in the system by five."""
    panel = make_panel({"managed_money": [(10, 5)], "swap": [(5, 10)]},
                       open_interest=999)
    assert oi_identity(panel)["open_interest"].iloc[0] == 999


# ── Loads that must refuse ──────────────────────────────────────────────────
def test_mixing_futures_only_and_combined_is_refused(make_panel):
    a = make_panel({"managed_money": [(10, 5)]}, combined=False)
    b = make_panel({"managed_money": [(10, 5)]}, combined=True, market_code="TEST02")
    with pytest.raises(PanelError, match="different series"):
        require_single_series(pd.concat([a, b], ignore_index=True))


def test_a_missing_required_column_is_named(history_panel):
    from crowdmon.futures.io import require_columns

    with pytest.raises(PanelError, match="open_interest"):
        require_columns(history_panel.drop(columns=["open_interest"]))


# ── Exit pressure (handoff §5) ──────────────────────────────────────────────
def test_days_to_liquidate_is_none_without_a_volume():
    """The refusal that matters most in this module, and it outlives a volume source
    existing. `volume.add_volume` now supplies one, but a caller who does not pass it still
    gets `None` rather than a default: a fabricated denominator under the headline number of
    the whole system is worse than a missing one, because a missing number is visibly
    missing."""
    out = exit_pressure(50_000, 200_000)
    assert out["days_to_liquidate"] is None
    assert out["volume"] is None
    assert out["q_over_oi"] == pytest.approx(0.25)


def test_days_to_liquidate_appears_the_moment_a_volume_does():
    """The structure the handoff asks for: `V` slots in without a rewrite."""
    out = exit_pressure(50_000, 200_000, volume=25_000)
    assert out["days_to_liquidate"] == pytest.approx(50_000 / (0.2 * 25_000))


def test_a_negative_q_is_refused():
    """`Q_sell` and `Q_buy` are both magnitudes, so a negative value means a sign
    convention was lost somewhere upstream."""
    with pytest.raises(PressureError, match="non-negative"):
        exit_pressure(-1, 100)


def test_rank_markets_keeps_the_two_directions_apart(vintage_panel):
    from crowdmon.futures import market_fragility

    ranked = rank_markets(market_fragility(vintage_panel))
    assert "q_sell_over_oi" in ranked and "q_buy_over_oi" in ranked
    # rank_markets was called WITHOUT a volume, so the duration columns must be null. Not
    # because no volume source exists (one does now), but because this call did not pass it.
    assert ranked["dtl_sell"].isna().all(), "no volume was passed; this must stay null"
    # The asymmetry is the informative number, so it must not collapse to a constant.
    assert ranked["sell_to_buy"].nunique() > 1


def test_the_open_interest_floor_is_an_argument_not_a_default(vintage_panel):
    """`Q/OI` is a ratio, so an unfiltered ranking of a wide universe tends to rank the
    smallest markets. The floor exists, defaults to 0, and its effect on any published
    table is therefore visible in the call rather than baked into the function."""
    from crowdmon.futures import market_fragility

    ranked = rank_markets(market_fragility(vintage_panel))
    assert len(top_by(ranked, "q_sell_over_oi", n=5)) == 5
    floored = top_by(ranked, "q_sell_over_oi", n=5, min_open_interest=10**9)
    assert floored.empty
