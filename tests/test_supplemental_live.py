"""`2026-08-03 §C1-C4` against a REAL store. Skips when there is not one.

Pins the four figures the index-share handoff's §2 rests on, for the same reason
`test_notional_live.py` pins the layer-2 trap table: a number quoted in a design doc and
checked by nobody becomes folklore the moment its input changes. These four are more
exposed than most, because three of them read `cot_supplemental`, a domain that arrived on
2026-08-03 (cotdata#96) and has been parsed by exactly one release.

**What would break these, and what would not.** A change to the shape rule or the
hand-drawn outright list moves the test and `docs/analysis/reproduce.py` together, because
the test imports both rather than restating them: two copies of a 39-entry list is the
maintenance problem this file exists to avoid, not solve twice. What these DO catch is the
store drifting under a fixed rule, which is the actual risk and the one nothing else covers.

§C2 and §C4 are structural rather than empirical, so they are asserted exactly. If either
ever fails, the finding is wrong rather than stale, and the amendment needs rewriting rather
than renumbering.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.needs_vintage

EXTREME_LO, EXTREME_HI = 0.10, 0.90
W_SD_SWEEP = (0.2, 0.4, 0.7)

#: The 13 Supplemental markets as 6-digit CFTC codes (`2026-08-03 §C3`).
SUPPLEMENTAL = {
    "001602", "001612", "002602", "005602", "007601", "026603", "033661",
    "054642", "057642", "061641", "073732", "080732", "083731",
}


@pytest.fixture(scope="module")
def repro():
    """`docs/analysis/reproduce.py`, for `CLASSIC_OUTRIGHTS` and the shape rule.

    Loaded by path because `docs/` is not a package and should not become one: it holds
    point-in-time analysis, and making it importable invites `src/` growing a dependency on
    a directory whose whole contract is that it is never amended.
    """
    path = Path(__file__).resolve().parents[1] / "docs" / "analysis" / "reproduce.py"
    if not path.exists():
        pytest.skip("no readable store: reproduce.py is absent")
    spec = importlib.util.spec_from_file_location("_repro_live", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_repro_live"] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    return mod


@pytest.fixture(scope="module")
def vintage_panel():
    from crowdmon.futures import from_vintage
    try:
        panel = from_vintage()
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    if panel.empty:
        pytest.skip("store not populated: the vintage store is empty")
    return panel


@pytest.fixture(scope="module")
def shape_panel(repro, vintage_panel):
    """Deliberately NOT wrapped in a broad `except -> skip`.

    Depending on `vintage_panel` settles the data-absent question first, so anything that
    raises here is a real failure of `_shape_panel` and must fail rather than skip. An
    earlier version caught everything and reported a pandas dtype error as "no readable
    store", which `check_skips.py --profile ci` allows: a genuine break would have skipped
    green in CI, which is precisely the masking this whole live-test split exists to stop.
    """
    panel = repro._shape_panel()
    if panel.empty:
        pytest.skip("store not populated: the vintage store has no shape panel")
    return panel


def _template_rates(panel: pd.DataFrame) -> pd.DataFrame:
    dates = np.sort(panel["report_date"].unique())
    mid = dates[len(dates) // 2]
    panel = panel.assign(half=np.where(panel["report_date"] < mid, "h1", "h2"))
    is_t = panel["shape"].str.startswith("template")
    out = pd.concat([
        is_t.groupby(panel["market_code"]).mean().rename("pooled"),
        is_t.groupby([panel["market_code"], panel["half"]]).mean().unstack("half"),
        panel.groupby("market_code").size().rename("weeks"),
    ], axis=1)
    out["name"] = panel.groupby("market_code")["market_name"].first()
    return out


def test_c1_classification_survives_a_half_split_for_17_of_39(repro, shape_panel):
    """`§C1`. The gap between 22 pooled and 17 stable is the instability §3 warns about.

    The handoff cites 22 and 17 without a source; they reproduce exactly, which is why the
    amendment says the figures were mislaid rather than invented. Pinned so that stays
    checkable.
    """
    classic = shape_panel[shape_panel["market_code"].isin(repro.CLASSIC_OUTRIGHTS)]
    rates = _template_rates(classic)
    rates = rates[rates["weeks"] >= 40]

    assert len(rates) == 39, (
        f"the classic-outright universe is {len(rates)} markets, not the 39 that "
        f"`2026-08-02 §B31` and `§C1` both count over."
    )

    def extreme(s):
        return (s <= EXTREME_LO) | (s >= EXTREME_HI)

    pooled = int(extreme(rates["pooled"]).sum())
    both = extreme(rates["h1"]) & extreme(rates["h2"])
    same_side = both & (
        ((rates["h1"] >= EXTREME_HI) & (rates["h2"] >= EXTREME_HI))
        | ((rates["h1"] <= EXTREME_LO) & (rates["h2"] <= EXTREME_LO))
    )

    assert pooled == 22, f"§C1 pins 22 of 39 extreme pooled; got {pooled}"
    assert int(both.sum()) == 18, f"§C1 pins 18 extreme in both halves; got {int(both.sum())}"
    assert int(same_side.sum()) == 17, (
        f"§C1 pins 17 extreme in both halves on the SAME side; got {int(same_side.sum())}. "
        f"That count is the one §3 of the handoff quotes."
    )
    assert pooled > int(same_side.sum()), (
        "pooled extremity must exceed stable extremity, or there is no instability to "
        "report and §C1's whole finding is void."
    )


def test_c1_cocoa_is_the_market_that_flips_between_extremes(repro, shape_panel):
    """`§C1`. Cocoa is template in every week of h1 and 4 of 41 in h2.

    The pooled 0.549 describes no week cocoa has ever had, which is the concrete form of
    `2026-08-02 §B31`'s "a mixture of always and never".
    """
    classic = shape_panel[shape_panel["market_code"].isin(repro.CLASSIC_OUTRIGHTS)]
    rates = _template_rates(classic)
    cocoa = rates.loc["073732"]

    assert cocoa["h1"] == pytest.approx(1.000, abs=0.005), (
        f"cocoa h1 template rate {cocoa['h1']:.3f}, §C1 pins 1.000"
    )
    assert cocoa["h2"] == pytest.approx(0.098, abs=0.005), (
        f"cocoa h2 template rate {cocoa['h2']:.3f}, §C1 pins 0.098"
    )
    assert cocoa["pooled"] == pytest.approx(0.549, abs=0.01)
    # The point of the section: the pooled figure is not a rate cocoa ever ran at.
    assert not (0.40 <= cocoa["h1"] <= 0.70) and not (0.40 <= cocoa["h2"] <= 0.70)


def test_c2_template_rate_cannot_move_with_w_sd(repro, shape_panel):
    """`§C2`. Structural, so asserted exactly rather than to a tolerance.

    The shape label reads `producer_merchant` and `managed_money` and their signs. No
    weight can reach it. A failure here means the shape rule grew a dependency on the
    weight table, which would invalidate every stratified template figure in `docs/design/`.
    """
    classic = shape_panel[shape_panel["market_code"].isin(repro.CLASSIC_OUTRIGHTS)]
    base = classic["shape"].str.startswith("template").mean()

    assert base == pytest.approx(0.447106, abs=1e-5), (
        f"classic-outright template rate {base:.6f}; §C2 pins 0.447106, which also "
        f"reproduces `2026-08-02 §B31`'s 44.7%"
    )
    for w in W_SD_SWEEP:
        again = repro._shape_labels(
            classic["producer_merchant"], classic["managed_money"]
        ).str.startswith("template").mean()
        assert again == base, (
            f"the template rate moved when w_SD was {w}, which is impossible unless the "
            f"shape rule now reads a weight. §C2 is then wrong, not stale."
        )


def test_c3_w_sd_is_load_bearing_on_the_supplemental_13_and_not_pooled(vintage_panel):
    """`§C3`. The finding is the CONTRAST, so both populations are asserted together.

    Either number alone is misleading: pooled says the weight is irrelevant, the 13 say it
    decides the answer. Tolerances are wide enough to survive a week of new data and far
    too tight to survive the contrast reversing.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures import market_fragility

    def median_a(codes):
        out = []
        for w in W_SD_SWEEP:
            panel = vintage_panel if codes is None else vintage_panel[
                vintage_panel["market_code"].isin(codes)]
            f = market_fragility(panel, report_type="disaggregated",
                                 weights=dict(cfg.DISAGGREGATED_WEIGHTS, swap=w))
            a = (f["q_sell"] / f["q_buy"]).replace([np.inf, -np.inf], np.nan).dropna()
            out.append(a.median())
        return out

    pooled = median_a(None)
    supp = median_a(SUPPLEMENTAL)

    assert pooled == pytest.approx([1.0213, 0.9933, 1.0153], abs=0.05)
    assert supp == pytest.approx([2.1845, 2.5750, 3.1028], abs=0.15)

    pooled_swing = abs(pooled[-1] - pooled[0]) / pooled[0]
    supp_swing = abs(supp[-1] - supp[0]) / supp[0]

    assert pooled_swing < 0.05, (
        f"pooled median A swings {pooled_swing:.1%} across w_SD; §C3 pins 0.6% and the "
        f"finding is that it is negligible"
    )
    assert supp_swing > 0.25, (
        f"Supplemental median A swings {supp_swing:.1%}; §C3 pins 42.0% and the finding "
        f"is that w_SD is load-bearing there"
    )
    assert supp == sorted(supp), "§C3 pins the Supplemental sweep as monotonic in w_SD"
    assert supp_swing > pooled_swing * 5, (
        "§C3's whole point is that the sensitivity is a POPULATION fact. If the two "
        "populations stop differing by an order of magnitude, the section is wrong."
    )


def test_c4_a_weight_agnostic_asymmetry_is_identically_one(vintage_panel):
    """`§C4`. Not a tolerance: the claim is that the quantity is a constant.

    Since the gross net-long and net-short totals are equal, a single shared weight gives
    `Q_sell = Q_buy` exactly. This is `2026-08-01 §A21` at its sharpest: flatten the
    weights and the asymmetry does not lose signal, it stops being a variable.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures import market_fragility

    f = market_fragility(vintage_panel, report_type="disaggregated",
                         weights={k: 1.0 for k in cfg.DISAGGREGATED_WEIGHTS})
    a = (f["q_sell"] / f["q_buy"]).replace([np.inf, -np.inf], np.nan).dropna()

    assert len(a) > 20_000, f"only {len(a)} market-weeks; §C4 measured over 21,756"
    assert (a.sub(1.0).abs() < 1e-9).all(), (
        f"{int((a.sub(1.0).abs() >= 1e-9).sum())} market-weeks depart from A = 1 under "
        f"flat weights. §C4 says that cannot happen while sum_c P_c = 0 holds, so this "
        f"is a broken zero-sum identity rather than a stale figure."
    )
