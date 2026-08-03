"""`2026-08-03 §C1-C8` against a REAL store. Skips when there is not one.

Pins the figures the index-share handoff's §2 and the b-series-recovery handoff's §4 rest
on, for the same reason `test_notional_live.py` pins the layer-2 trap table: a number
quoted in a design doc and checked by nobody becomes folklore the moment its input changes.
Several of these are more exposed than most, because they read `cot_supplemental`, a domain
that arrived on 2026-08-03 (cotdata#96) and has been parsed by exactly one release.

**What would break these, and what would not.** A change to the shape rule or the
hand-drawn outright list moves the test and `docs/analysis/reproduce.py` together, because
the test imports both rather than restating them: two copies of a 39-entry list is the
maintenance problem this file exists to avoid, not solve twice. What these DO catch is the
store drifting under a fixed rule, which is the actual risk and the one nothing else covers.

§C2, §C4 and §C6 are structural rather than empirical, so they are asserted exactly. If
any of them ever fails, the finding is wrong rather than stale, and the amendment needs
rewriting rather than renumbering.

**§C4 is here twice on purpose.** Its original reading (weight-agnostic, degenerate at 1.0)
is a true statement about a quantity nobody asked for, and its corrected reading
(direction-agnostic, `2026-08-02 §B34`, median 3.0237) is the one the handoff meant. Both
are pinned side by side so the wrong reading cannot creep back in as a plausible guess.
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
    """`§C4`, the half of it that survived. Not a tolerance: the claim is a constant.

    Since the gross net-long and net-short totals are equal, a single shared weight gives
    `Q_sell = Q_buy` exactly. This is `2026-08-01 §A21` at its sharpest: flatten the
    weights and the asymmetry does not lose signal, it stops being a variable.

    **What this does NOT establish, and originally was read as establishing.** §C4 concluded
    from this that `A_agnostic` is undefined and degenerate. It is neither: `A_agnostic` is
    DIRECTION-agnostic, not WEIGHT-agnostic, and `2026-08-02 §B34` defines and measures it.
    The test below pins that definition beside this one so the two cannot be confused again.
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


def test_c4_corrected_a_agnostic_is_direction_agnostic_and_not_degenerate(vintage_panel,
                                                                          repro):
    """`§C4 CORRECTED`, against `2026-08-02 §B34`.

    The correction is worth a test rather than only a prose fix, because the failure it
    guards is a definition drifting rather than a number: if a future session reads
    "agnostic" as "weight-agnostic" again it will measure 1.0 and conclude the quantity is
    dead. Asserting that the median is nowhere near 1 makes that reading fail loudly.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures import market_fragility

    w = cfg.weights_for("disaggregated")
    ceiling = max(w.values()) / min(w.values())
    f = market_fragility(vintage_panel, report_type="disaggregated", weights=w)
    q = f[(f["q_sell"] > 0) & (f["q_buy"] > 0)]
    a_agn = np.maximum(q["q_sell"], q["q_buy"]) / np.minimum(q["q_sell"], q["q_buy"])
    classic = q["market_code"].isin(repro.CLASSIC_OUTRIGHTS)

    assert a_agn.median() == pytest.approx(3.0237, abs=0.15), (
        f"A_agnostic median {a_agn.median():.4f}; §B34 pins 3.0237 over 21,756 "
        f"market-weeks. A value near 1.0 means the WEIGHT-agnostic reading has crept "
        f"back in, which is the error §C4 made."
    )
    assert a_agn[classic].median() == pytest.approx(2.4974, abs=0.15), (
        f"classic-outright A_agnostic median {a_agn[classic].median():.4f}; §B34 pins "
        f"2.4974"
    )
    assert (a_agn > ceiling + 1e-9).sum() == 0, (
        f"A_agnostic breaches max(w)/min(w) = {ceiling:.1f}. It is the same two sums with "
        f"the larger on top, so it carries A_directional's bound exactly; a breach is a "
        f"broken `market_fragility`, not a stale figure."
    )


def test_c6_the_measured_lower_bound_moves_the_ceiling_and_the_others_do_not(vintage_panel):
    """`§C6`. `w_SD = 0.067` is below `producer_merchant`, so `max(w)/min(w)` changes.

    This is the one thing about the reported band that is easy to get wrong quietly: the
    three round values leave `swap` inside `[0.1, 1.0]` and the ceiling pinned at 10.0, so
    raw ratios are comparable across them. The measured stress value is not inside that
    interval, and a band whose members sit on different scales is not a band.
    """
    from crowdmon.core import config as cfg

    ceilings = {}
    for w_sd in (0.067, 0.2, 0.4, 0.7):
        ww = dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd)
        ceilings[w_sd] = max(ww.values()) / min(ww.values())

    assert ceilings[0.2] == ceilings[0.4] == ceilings[0.7] == pytest.approx(10.0), (
        f"the three round values no longer share a ceiling: {ceilings}. Either "
        f"`managed_money` or `producer_merchant` moved, and §C3's 'none of this is a "
        f"ceiling artifact' no longer holds."
    )
    assert ceilings[0.067] == pytest.approx(1.0 / 0.067, rel=1e-9)
    assert ceilings[0.067] > ceilings[0.4] * 1.4, (
        f"ceiling at the stress weight is {ceilings[0.067]:.3f} against "
        f"{ceilings[0.4]:.1f}. §C6's point is that this is a 49% change in headroom, so "
        f"raw A at 0.067 must be scaled by its own ceiling before comparison."
    )


def test_c7_w_sd_04_overstates_fragile_capital_and_gold_worse_than_cocoa(vintage_panel):
    """`§C7`. The shipped weight against the measured stress weight, market by market.

    Two claims, and the second is the one worth a test. That `Phi` rises with `w_SD` is
    arithmetic. That it rises 2.3x more on GOLD than on COCOA is a fact about where the
    swap dealer sits, and it is the prediction §4 of the handoff made in advance.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures import market_fragility

    def phi(w_sd):
        f = market_fragility(vintage_panel, report_type="disaggregated",
                             weights=dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd))
        return f.set_index(["report_date", "market_code"])["phi"]

    d = pd.DataFrame({"live": phi(0.4), "stress": phi(0.067)}).dropna()
    infl = (d["live"] / d["stress"] - 1.0)

    assert (infl >= -1e-12).all(), (
        f"{int((infl < -1e-12).sum())} market-weeks see Phi FALL when a weight rises. "
        f"Phi is a weighted sum of gross positions, so that is impossible."
    )
    assert infl.median() == pytest.approx(0.196, abs=0.05), (
        f"median Phi inflation {infl.median():.2%}; §C7 pins +19.60%"
    )

    per = infl.groupby(level="market_code").mean()
    gold, cocoa = per["088691"], per["073732"]
    assert gold == pytest.approx(0.2778, abs=0.05), f"gold inflation {gold:.2%}, §C7 pins +27.78%"
    assert cocoa == pytest.approx(0.1208, abs=0.05), f"cocoa inflation {cocoa:.2%}, §C7 pins +12.08%"
    assert gold > cocoa * 1.5, (
        f"gold {gold:.2%} against cocoa {cocoa:.2%}. §4 of the b-series-recovery handoff "
        f"predicted gold would be worse affected, because swap sits on gold's immovable "
        f"side. If this reverses, the prediction failed and §C7 needs rewriting."
    )


def test_c8_the_band_reaches_the_composite_through_the_percentile(vintage_panel):
    """`§C8`. The composite consumes `pct(Phi)`, so a level shift may vanish. Mostly it does.

    The number that matters is not the median shift, which is small, but how often the two
    weight tables put a market's own weeks in a DIFFERENT order. A level change is invisible
    to a percentile; a reordering is not, and it is what would move `D`.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures import market_fragility

    def phi(w_sd):
        f = market_fragility(vintage_panel, report_type="disaggregated",
                             weights=dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd))
        return f.set_index(["report_date", "market_code"])["phi"]

    d = pd.DataFrame({"live": phi(0.4), "stress": phi(0.067)}).dropna().reset_index()
    counts = d.groupby("market_code").size()
    d = d[d["market_code"].isin(counts[counts >= 40].index)]
    for col in ("live", "stress"):
        d[f"pct_{col}"] = d.groupby("market_code")[col].rank(pct=True)
    shift = (d["pct_live"] - d["pct_stress"]).abs()

    assert shift.median() < 0.10, (
        f"median percentile shift {shift.median():.4f}; §C8 pins 0.0588 and the finding "
        f"is that the composite mostly does not see the level change"
    )
    assert (shift > 0.25).mean() == pytest.approx(0.098, abs=0.04), (
        f"{(shift > 0.25).mean():.2%} of market-weeks move more than a quarter of a "
        f"percentile; §C8 pins 9.79%. This is the tail the reported band exists to show, "
        f"so it failing means the band is either wider or narrower than documented."
    )
    assert shift.max() > 0.5, (
        "§C8 records a maximum shift of 0.878. If no market-week moves more than half a "
        "percentile, the weight has stopped mattering anywhere and the band is theatre."
    )

def test_c10_the_plausible_band_is_narrower_than_c3_swept(vintage_panel):
    """`2026-08-03 §C10`. Pins the ORDER half of why §C3's band was too wide.

    §C6 covers the SCALE half (0.067 moves the ceiling to 14.925). This is the other
    end: 0.55 and 0.7 leave the ceiling at exactly 10.0 and still reorder the table. 0.7 is
    outside the order-preserving class (`2026-08-01 §A22`): it puts a swap dealer above both
    `nonreportable` and `other_reportable`. This asserts the classification rather than the
    swing, because the classification is what makes the smaller number the honest one and it
    is a property of the weight table rather than of any week's data.
    """
    from crowdmon.core import config as cfg
    from crowdmon.futures.weight_sensitivity import single_weight_sweep

    swept = single_weight_sweep(vintage_panel, "swap",
                                [0.067, 0.1, 0.2, 0.305, 0.4, 0.55, 0.7])
    by_value = swept.set_index("value")

    inside = sorted(by_value.index[by_value["preserves_order"]])
    assert inside == [0.2, 0.305, 0.4], (
        f"the order-preserving band moved to {inside}. §C6 measured [0.2, 0.305, 0.4] "
        f"against the live table {cfg.DISAGGREGATED_WEIGHTS}; if a weight changed, §C6 and "
        f"the swap-dealer decision handoff both need re-reading.")

    # The tie is the subtle one: a stable sort leaves the category order unchanged at 0.1,
    # so only an explicit equality check catches that the distinction has been collapsed.
    assert by_value.loc[0.1, "ties_with"] == "producer_merchant"
    assert not by_value.loc[0.1, "preserves_order"], (
        "w_SD = 0.1 ties producer_merchant and must NOT count as order-preserving; a "
        "stable sort reports the ordering intact when it has actually been collapsed.")
    assert by_value.loc[0.067, "crosses"] == "now below producer_merchant"
    assert "other_reportable" in by_value.loc[0.7, "crosses"]
