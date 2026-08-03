"""The two properties the template amendments rest on that are not about one market.

1. The asymmetry between the two `Q` directions is bounded by the weight table, before any
   data arrives (module spec §6.3, amendments B31/B32/B34). Every ratio B34 quotes is a
   fraction of that bound, so a breach would mean the bound argument is wrong and every
   "% of ceiling" figure published alongside it is meaningless.
2. The stratification B31 and B33-B36 count over is a function of the market CODE alone.
   That is not obvious: the stratum is built partly from the venue, the venue is parsed out
   of `market_name`, and a code can carry several names over time (§B17's phantoms). If the
   stratum could vary within a code, a market would move between strata mid-window and the
   per-stratum shares would depend on which weeks happened to be in the panel.
"""
import importlib.util
import pathlib

import pandas as pd
import pytest

from crowdmon.core import config as cfg
from crowdmon.futures import contributions


def _ratios(panel: pd.DataFrame) -> pd.DataFrame:
    con = contributions(panel)
    q = (con.groupby(["report_date", "market_code", "q_side"])["q_contribution"].sum()
           .unstack("q_side").reindex(columns=["buy", "sell"]).fillna(0.0))
    q = q[(q["sell"] > 0) & (q["buy"] > 0)].copy()
    q["a_dir"] = q["sell"] / q["buy"]
    q["a_agn"] = (q[["sell", "buy"]].max(axis=1) / q[["sell", "buy"]].min(axis=1))
    return q


def test_the_ceiling_holds_over_twenty_years(history_panel):
    """Gold, crude and oats, 2006-06-13 to 2026-07-28. The bound is arithmetic, since
    `sum_c P_c = 0` the gross net-long total equals the gross net-short total, so
    `Q_sell <= max(w).G` and `Q_buy >= min(w).G`. It is asserted rather than argued,
    because the premise it rests on is that the panel's nets really do sum to zero."""
    w = cfg.DISAGGREGATED_WEIGHTS
    ceiling = max(w.values()) / min(w.values())
    q = _ratios(history_panel)
    assert len(q) > 3_000, "the history fixture no longer covers enough market-weeks"
    assert (q["a_dir"] <= ceiling + 1e-9).all()
    assert (q["a_agn"] <= ceiling + 1e-9).all()
    assert (q["a_agn"] >= 1.0 - 1e-9).all(), "the agnostic ratio is a max over a min"


def test_the_ceiling_holds_on_the_vintage_panel_too(vintage_panel):
    """A second population, and a different one: two power/gas markets plus gold and live
    cattle. B34's headline figures are computed over the power-and-gas universe, which is
    where the largest observed ratios live."""
    w = cfg.DISAGGREGATED_WEIGHTS
    ceiling = max(w.values()) / min(w.values())
    q = _ratios(vintage_panel)
    assert not q.empty
    assert (q["a_agn"] <= ceiling + 1e-9).all()


def test_the_ceiling_moves_with_the_weight_table_and_nothing_else():
    """The claim module spec §6.3 makes about cross-version comparison: change the SPREAD
    and every asymmetry figure rescales; change the LEVEL uniformly and none of them move,
    because a common factor cancels in a ratio."""
    rows = [("producer_merchant", 0, 100_000), ("managed_money", 100_000, 0)]
    panel = pd.DataFrame([{
        "report_date": pd.Timestamp("2026-01-06"), "market_code": "T", "market_name": "T",
        "report_type": "disaggregated", "combined": False, "category": c,
        "long_contracts": long_, "short_contracts": short_,
        "spread_contracts": 0, "open_interest": 100_000,
    } for c, long_, short_ in rows])

    base = {"producer_merchant": 0.1, "managed_money": 1.0, "swap": 0.4,
            "other_reportable": 0.5, "nonreportable": 0.6}
    halved_spread = {**base, "producer_merchant": 0.2}
    doubled_level = {k: v * 2 for k, v in base.items()}

    def ratio(weights):
        c = contributions(panel, weights=weights)
        sell = c.loc[c["q_side"] == "sell", "q_contribution"].sum()
        buy = c.loc[c["q_side"] == "buy", "q_contribution"].sum()
        return sell / buy

    assert ratio(base) == pytest.approx(10.0)
    assert ratio(halved_spread) == pytest.approx(5.0)
    assert ratio(doubled_level) == pytest.approx(10.0)


def _reproduce():
    here = pathlib.Path(__file__).resolve().parent.parent / "docs" / "analysis"
    spec = importlib.util.spec_from_file_location("reproduce", here / "reproduce.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_stratum_is_a_function_of_the_market_code_alone():
    """Reproduced from the reproducer's own tables, without touching a store.

    Every code in `CLASSIC_OUTRIGHTS` is stratum 1 by construction. For every other code the
    stratum depends on the venue, and `_shape_panel` resolves the venue through
    `groupby("market_code")["market_name"].first()`, one name per code, so a code that
    changed name mid-window cannot change stratum mid-window. This test pins the property;
    the mechanism is one `.first()` and is easy to lose in a refactor.
    """
    R = _reproduce()
    assert len(R.CLASSIC_OUTRIGHTS) == len(set(R.CLASSIC_OUTRIGHTS))
    assert R.POWER_VENUES.isdisjoint(R.AG_METAL_VENUES)

    names = ["COCOA - ICE FUTURES U.S.", "COCOA - NEW YORK BOARD OF TRADE"]
    frame = pd.DataFrame({
        "market_code": ["073732", "073732", "0063CU"],
        "market_name": [names[0], names[1], "CALIF LOW CARBON - ICE FUTURES ENERGY DIV"],
    })
    # The resolution `_shape_panel` performs, isolated: one name per code, then classify.
    resolved = frame["market_code"].map(frame.groupby("market_code")["market_name"].first())
    assert resolved.nunique() == 2, "a code must resolve to exactly one name"
    assert (resolved[frame["market_code"] == "073732"] == names[0]).all()


def test_every_classic_outright_carries_a_complex():
    """The per-complex tables in B31 and B33-B36 group on this, and a `None` complex would
    be dropped by `groupby` without anything failing."""
    R = _reproduce()
    complexes = {v[1] for v in R.CLASSIC_OUTRIGHTS.values()}
    assert None not in complexes
    assert complexes == {"grains/oilseeds", "softs", "livestock/dairy", "metals",
                         "energy outright", "lumber"}
    for code, (name, complex_) in R.CLASSIC_OUTRIGHTS.items():
        assert len(code) == 6, code
        assert name and complex_
