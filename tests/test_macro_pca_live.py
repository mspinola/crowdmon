"""Macro-book PCA against a REAL store. Skips when there is not one.

`test_macro_pca.py` checks the arithmetic on constructed panels. This file checks the claims
the module rests on, which is the pattern every other engine here follows and the one that
caught the defects in notional, riskunits, volume, impact, trigger and coverage.

The three that matter:

- **95.7% cell coverage yields ZERO complete weeks**, so selection is not optional
- **PC1 is the grain complex on Disaggregated and the macro book on TFF**, so §7's
  "aggregate systematic book" is true of one panel and false of the other
- **the panel reaches 2008**, which `D` structurally cannot
"""
import numpy as np
import pytest

pytestmark = pytest.mark.needs_vintage


def _panel_for(report_type):
    from crowdmon.futures import (
        ContractMaster,
        add_extremity,
        add_notional,
        add_risk_units,
        from_current_store,
        positioning_panel,
    )

    raw = from_current_store(report_type=report_type)
    per_category = add_extremity(add_risk_units(
        add_notional(ContractMaster.load().annotate(raw))))
    return per_category, positioning_panel(per_category)


@pytest.fixture(scope="module")
def disagg():
    pytest.importorskip("cotdata")
    try:
        return _panel_for("disaggregated")
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")


@pytest.fixture(scope="module")
def tff():
    pytest.importorskip("cotdata")
    try:
        return _panel_for("tff")
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no readable TFF panel: {exc}")


def test_high_cell_coverage_still_gives_no_complete_weeks(disagg):
    """**Why `select_markets` exists.** The holes are spread across markets rather than
    concentrated in weeks, so a coverage figure that reads as nearly complete is unusable."""
    _, panel = disagg
    coverage = float(panel.notna().mean().mean())
    complete = int(panel.dropna().shape[0])
    assert coverage > 0.90, f"cell coverage fell to {coverage:.1%}"
    assert complete == 0, (
        f"{complete} weeks are complete across every market; if the panel has genuinely "
        f"filled in, this test has outlived the finding and should be rewritten")


def test_dropping_two_markets_buys_the_whole_panel(disagg):
    """Measured: 25 markets gives 746 weeks ending 2023, 24 gives 947 ending 2026, because
    the 25th delists and truncates everything to it."""
    from crowdmon.futures import select_markets

    _, panel = disagg
    chosen = select_markets(panel)
    complete = panel[chosen].dropna()
    assert 20 <= len(chosen) <= panel.shape[1] - 1
    assert len(complete) > 800, f"only {len(complete)} complete weeks on {len(chosen)} markets"
    # Keeping one more market must not do better, or the selection rule is wrong.
    order = panel.notna().sum().sort_values(ascending=False)
    wider = list(order.index[:len(chosen) + 1])
    assert len(panel[wider].dropna()) <= len(complete)


def test_the_panel_reaches_2008_and_the_composite_does_not(disagg):
    """The property that makes this module worth more than another reading beside `D`.

    `C = pct(z)` stacks two three-year windows so `D` starts 2010-05-25. This needs one.
    """
    import pandas as pd

    from crowdmon.futures import select_markets

    _, panel = disagg
    first = panel[select_markets(panel)].dropna().index.min()
    assert first < pd.Timestamp("2009-01-01"), f"panel starts {first.date()}, expected 2008"
    assert first < pd.Timestamp("2010-05-25"), "must predate D's floor or the claim is empty"


def test_absorption_beats_its_shuffled_null_on_both_panels(disagg, tff):
    """A variance share is floored at `1/n` and always positive, so the observed figure alone
    says nothing. The gap to the null is the part that is about crowding."""
    from crowdmon.futures import absorption_ratio, select_markets, shuffled_null

    for name, (_, panel) in (("disaggregated", disagg), ("tff", tff)):
        cols = select_markets(panel)
        if len(cols) < 8:
            pytest.skip(f"{name} panel too narrow")
        observed = absorption_ratio(panel[cols])["absorption"]
        null = shuffled_null(panel[cols], draws=40)
        assert observed > float(null.quantile(0.95)), (
            f"{name}: absorption {observed:.3f} is inside its own null "
            f"(p95 {null.quantile(0.95):.3f}), so there is no measured co-movement")


def test_pc1_is_the_grain_complex_on_disaggregated(disagg):
    """**§7 says PC1 approximates the aggregate systematic book. On this panel it does not.**

    It is the grain trade. Same shape as `2026-08-01 §A14`: a cross-market statistic named
    for something broader than the universe supports.
    """
    from crowdmon.futures import absorption_ratio, select_markets

    per_category, panel = disagg
    cols = select_markets(panel)
    result = absorption_ratio(panel[cols])
    symbols = per_category.drop_duplicates("market_code").set_index("market_code")["symbol"]
    top = [str(symbols.get(c)) for c in
           result["loadings"].abs().sort_values(ascending=False).head(6).index]

    grains = {"ZS", "ZC", "ZL", "ZM", "ZW", "KE"}
    assert len(grains.intersection(top)) >= 4, (
        f"expected the grain complex to dominate PC1, top six were {top}")


def test_pc1_is_the_macro_book_on_tff(tff):
    """And on TFF it is exactly what §7 describes: risk appetite. Long the equity indices,
    long the commodity currency, **short the dollar**."""
    from crowdmon.futures import absorption_ratio, select_markets

    per_category, panel = tff
    cols = select_markets(panel)
    if len(cols) < 8:
        pytest.skip("TFF panel too narrow")
    result = absorption_ratio(panel[cols])
    symbols = per_category.drop_duplicates("market_code").set_index("market_code")["symbol"]
    by_symbol = {str(symbols.get(c)): float(result["loadings"][c]) for c in cols}

    equity = [by_symbol[s] for s in ("ES", "NQ", "YM") if s in by_symbol]
    assert len(equity) >= 2 and all(np.sign(e) == np.sign(equity[0]) for e in equity), (
        f"the equity indices should load together, got {equity}")
    if "DX" in by_symbol:
        assert np.sign(by_symbol["DX"]) != np.sign(equity[0]), (
            f"the dollar index should oppose equity on a risk-appetite factor, "
            f"got DX {by_symbol['DX']:+.2f} against equity {equity[0]:+.2f}")


def test_rolling_rotation_carries_no_sign_artifacts(disagg):
    """**The defect this module shipped with for one run.**

    A signed cosine reported 8 of 843 weeks at ~1.99 against a median of 0.0004. `1 - |cos|`
    is bounded in `[0, 1]` and those weeks read as the non-events they were.
    """
    from crowdmon.futures import rolling_absorption, select_markets

    _, panel = disagg
    got = rolling_absorption(panel, markets=select_markets(panel))
    assert len(got) > 500
    rotation = got["rotation"].dropna()
    assert rotation.between(0.0, 1.0).all(), (
        f"rotation left [0, 1]: max {rotation.max():.4f}. A value near 2 means the sign "
        f"convention leaked back in.")
    assert float(rotation.median()) < 0.01
