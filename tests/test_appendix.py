"""The appendix's own worked examples, executed.

`docs/design/crowdmon_plain_language_summary.md` §A.1-A.11 is the authoritative statement of
every formula in this package: where a handoff and the appendix disagree, the appendix wins.
An authoritative document whose worked example is never run is a document nobody has checked,
so this file runs it.

Every figure asserted below is transcribed from the appendix, not computed and then written
down. If one of these fails, the implementation has drifted from the specification and the
implementation is what is wrong.

**Two examples, and they fail in opposite ways.** §A.2 carries a real market (LIVE CATTLE,
report week 2026-07-28) through §A.2, §A.5, §A.7 and §A.9, and beside it retains a
constructed near-maximal table that used to be presented as typical. The constructed one can
only drift if the code changes. The real one can also drift because the *store* changed, and
that is the more valuable guard: a design document quoting live figures rots silently. It is
asserted here against the committed vintage fixture, and again against the real store in
`test_appendix_live.py` so a restatement of that week is caught rather than absorbed.
"""
import pandas as pd
import pytest

from crowdmon.core import config as cfg
from crowdmon.futures import (
    add_notional,
    add_risk_units,
    contributions,
    exit_pressure,
    market_fragility,
    shape_labels,
)

#: §A.2's real example, transcribed from the appendix table: (category, long, short).
#: Report week 2026-07-28, Disaggregated, released 2026-07-31.
LIVE_CATTLE_ROWS = [
    ("producer_merchant", 41_461, 140_446),
    ("swap", 68_622, 7_026),
    ("managed_money", 84_907, 17_882),
    ("other_reportable", 13_899, 36_601),
    ("nonreportable", 25_614, 32_548),
]
LIVE_CATTLE_OI = 298_449
LIVE_CATTLE_CODE = "057642"
LIVE_CATTLE_WEEK = pd.Timestamp("2026-07-28")

#: §A.2, transcribed verbatim: (category, long, short). OI is 200,000 and there is no
#: spreading, which is what makes the appendix's gross total exactly 2 x OI.
COCOA_ROWS = [
    ("producer_merchant", 40_000, 150_000),
    ("swap", 30_000, 20_000),
    ("managed_money", 100_000, 10_000),
    ("other_reportable", 20_000, 15_000),
    ("nonreportable", 10_000, 5_000),
]
COCOA_OI = 200_000


@pytest.fixture
def cocoa() -> pd.DataFrame:
    return pd.DataFrame([{
        "report_date": pd.Timestamp("2026-01-06"), "market_code": "COCOA",
        "market_name": "COCOA (appendix A.2)", "report_type": "disaggregated",
        "combined": False, "category": category,
        "long_contracts": long_, "short_contracts": short_,
        "spread_contracts": 0, "open_interest": COCOA_OI,
    } for category, long_, short_ in COCOA_ROWS])


def test_the_example_is_internally_consistent(cocoa):
    """§A.1: `sum L_c = sum S_c = OI`, so `sum P_c = 0`.

    Checked first because every later assertion rests on it. Note this identity holds in the
    appendix because its example has no spreading; on real Disaggregated data spreading is
    excluded from `L_c` and `S_c`, so the sums fall short of OI by exactly the spreading.
    """
    assert cocoa["long_contracts"].sum() == COCOA_OI
    assert cocoa["short_contracts"].sum() == COCOA_OI
    assert (cocoa["long_contracts"] - cocoa["short_contracts"]).sum() == 0


def test_weights_match_the_appendix_table(cocoa):
    """§A.2's weight table against `core.config`. These are configured judgement, so the
    only thing that can be verified is that the code carries the documented values."""
    assert cfg.DISAGGREGATED_WEIGHTS == {
        "managed_money": 1.0,
        "nonreportable": 0.6,
        "other_reportable": 0.5,
        "swap": 0.4,
        "producer_merchant": 0.1,
    }


def test_q_sell_reproduces_the_appendix(cocoa):
    """§A.2: `0.4(10,000) + 1.0(90,000) + 0.5(5,000) + 0.6(5,000) = 99,500`."""
    assert market_fragility(cocoa)["q_sell"].iloc[0] == pytest.approx(99_500.0)


def test_q_buy_reproduces_the_appendix(cocoa):
    """§A.2: `0.1(110,000) = 11,000`.

    One term, because Producer/Merchant is the only net-short category. That is the whole
    asymmetry the example exists to show: 99,500 of forced selling faces 11,000 of forced
    buying, and the short side is a hedger who cannot be squeezed.
    """
    assert market_fragility(cocoa)["q_buy"].iloc[0] == pytest.approx(11_000.0)


def test_phi_reproduces_the_appendix(cocoa):
    """§A.2: `(0.1(190) + 0.4(50) + 1.0(110) + 0.5(35) + 0.6(15)) / 400 = 175.5/400 = 0.44`.

    Asserted against the unrounded 175,500/400,000 rather than the appendix's displayed
    0.44, since the appendix rounds for reading and the code must not.
    """
    phi = market_fragility(cocoa)["phi"].iloc[0]
    assert phi == pytest.approx(175_500 / 400_000)
    assert round(phi, 2) == 0.44


def test_managed_money_carries_the_numerator_as_the_appendix_says(cocoa):
    """§A.2: "Managed Money contributes 110,000 of the 175,500 fragility numerator".

    True in the constructed example, and it used to be called "typical" there. It is not:
    measured across the 279-market Disaggregated universe, Managed Money is the top
    contributor in 81 markets (29%), see amendments §A3, and the appendix now says so. This
    test pins the example, not the generalisation.
    """
    contrib = contributions(cocoa)
    mm = contrib[contrib["category"] == "managed_money"].iloc[0]
    assert mm["weight"] * mm["gross"] == pytest.approx(110_000.0)
    assert (contrib["weight"] * contrib["gross"]).sum() == pytest.approx(175_500.0)


def test_gross_total_is_exactly_twice_open_interest(cocoa):
    """§A.2: "Use gross positions, whose total is exactly `2 . OI`".

    Exactly true here and NOT true on real Disaggregated data, where spreading sits in open
    interest but outside `L_c + S_c`. `phi_denominator_covered` reports the shortfall, so a
    reader is not left calibrating Phi against a ceiling of 1 it cannot reach.
    """
    gross = (cocoa["long_contracts"] + cocoa["short_contracts"]).sum()
    assert gross == 2 * COCOA_OI
    assert market_fragility(cocoa)["phi_denominator_covered"].iloc[0] == pytest.approx(1.0)


#: §A.4 needs a multiplier, a price and a volatility, none of which §A.2's table carries.
#: Cocoa's real contract is 10 metric tonnes; $3,000/t and 2.5% daily are the figures the
#: appendix itself uses further down (§A.7's cascade example). They are stated here rather
#: than looked up so the ladder arithmetic below can be checked by hand.
COCOA_MULTIPLIER = 10.0
COCOA_PRICE = 3_000.0
COCOA_SIGMA = 0.025


@pytest.fixture
def cocoa_prices(monkeypatch):
    """A price series pinned at 3,000 alternating +/-2.5%, so sigma is a known 2.5%."""
    import cotdata

    dates = pd.bdate_range("2025-01-01", "2026-01-06")
    closes = [COCOA_PRICE]
    for i in range(1, len(dates)):
        closes.append(closes[-1] * (1.025 if i % 2 else 1 / 1.025))
    bars = pd.DataFrame({"Open": closes, "High": closes, "Low": closes, "Close": closes,
                         "Volume": [1.0] * len(closes)},
                        index=pd.DatetimeIndex(dates, name="Date"))

    def fake(symbol, adjustment="backadj", **kw):
        # A synthetic series has no rolls, so `unadj` and `propadj` coincide exactly: one is
        # the real level and the other is that level with a segment factor of 1. `backadj`
        # is offset so that any accidental use of it shows up as a wrong number. Serving
        # `unadj` doubled is what an earlier version of this fixture did, and it made rung 3
        # come out at exactly 2x the appendix.
        return bars * 2.0 if adjustment == "backadj" else bars

    monkeypatch.setattr(cotdata, "get_prices", fake)
    return bars


def test_the_normalisation_ladder_reproduces_the_appendix(cocoa, cocoa_prices):
    """§A.4: `P -> P/OI -> P.M.F -> P.M.F.sigma`, the last being risk units.

    Checks that `add_notional` and `add_risk_units` implement the appendix's ladder on the
    appendix's own example, rung by rung, rather than something that merely resembles it.
    Managed Money carries P = 100,000 - 10,000 = 90,000 contracts.
    """
    annotated = cocoa.assign(symbol="CC", point_value=COCOA_MULTIPLIER, currency="USD",
                             release_date=cocoa["report_date"] + pd.Timedelta(days=3))
    got = add_risk_units(add_notional(annotated))
    mm = got[got["category"] == "managed_money"].iloc[0]

    assert mm["net_contracts"] == 90_000                                    # rung 1: P
    assert mm["net_contracts"] / COCOA_OI == pytest.approx(0.45)            # rung 2: P/OI
    # rung 3: P . M . F
    assert mm["net_notional_usd"] == pytest.approx(90_000 * COCOA_MULTIPLIER * COCOA_PRICE)
    assert mm["net_notional_usd"] == pytest.approx(2.7e9)
    # rung 4: P . M . F . sigma
    assert mm["sigma_daily"] == pytest.approx(COCOA_SIGMA, rel=0.02)
    assert mm["net_risk_usd"] == pytest.approx(mm["net_notional_usd"] * mm["sigma_daily"])
    assert mm["net_risk_usd"] == pytest.approx(6.75e7, rel=0.02)


def test_days_to_liquidate_is_invariant_along_the_ladder(cocoa):
    """`T = Q/(kappa V)` is a DURATION, so it is unit-free and every rung of §A.4 must give
    the same answer, provided `Q` and `V` are expressed in the same units.

    This is the check that keeps rung 4 honest against §A.5. The failure it guards is
    available and easy: putting a vol-scaled `Q` over a contract-denominated `V` yields a
    number that is off by exactly `M . F . sigma`, which for cocoa is 750x. The appendix's
    twenty days becomes fifty-nine YEARS, and nothing in the units of the answer says so,
    because days are days.
    """
    q, v = 99_500.0, 25_000.0
    scale_notional = COCOA_MULTIPLIER * COCOA_PRICE
    scale_risk = scale_notional * COCOA_SIGMA

    contracts = exit_pressure(q, COCOA_OI, volume=v)["days_to_liquidate"]
    notional = exit_pressure(q * scale_notional, COCOA_OI,
                             volume=v * scale_notional)["days_to_liquidate"]
    risk = exit_pressure(q * scale_risk, COCOA_OI, volume=v * scale_risk)["days_to_liquidate"]

    assert contracts == pytest.approx(19.9)
    assert notional == pytest.approx(19.9)
    assert risk == pytest.approx(19.9)

    mismatched = exit_pressure(q * scale_risk, COCOA_OI, volume=v)["days_to_liquidate"]
    assert mismatched == pytest.approx(19.9 * scale_risk)
    assert mismatched / 252 > 50, "the mismatched-units failure should be absurd, not subtle"


def test_days_to_liquidate_reproduces_the_appendix(cocoa):
    """§A.5: `T = 99,500 / (0.2 x 25,000) = 19.9`, which the appendix reads as ~20 days."""
    frag = market_fragility(cocoa).iloc[0]
    out = exit_pressure(frag["q_sell"], frag["open_interest"], volume=25_000)
    assert out["days_to_liquidate"] == pytest.approx(19.9)
    assert out["kappa"] == 0.2


def test_the_unweighted_comparison_the_appendix_draws(cocoa):
    """§A.5: "Using the unweighted Managed Money net of 90,000 instead would give 18 days,
    which is close here only because that category dominates Q."

    Worth pinning because it is the appendix's own argument for why the weighting earns its
    place: the two figures diverge wherever fragility is spread more evenly, and 99,500
    against 90,000 is the narrowest that gap gets.
    """
    unweighted = exit_pressure(90_000, COCOA_OI, volume=25_000)
    assert unweighted["days_to_liquidate"] == pytest.approx(18.0)


# ── §A.2's real example: LIVE CATTLE, report week 2026-07-28 ─────────────────
@pytest.fixture
def live_cattle() -> pd.DataFrame:
    """The appendix's table, transcribed. Cross-checked against the store fixture below."""
    return pd.DataFrame([{
        "report_date": LIVE_CATTLE_WEEK, "market_code": LIVE_CATTLE_CODE,
        "market_name": "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE",
        "report_type": "disaggregated", "combined": False, "category": category,
        "long_contracts": long_, "short_contracts": short_,
        "spread_contracts": 0, "open_interest": LIVE_CATTLE_OI,
    } for category, long_, short_ in LIVE_CATTLE_ROWS])


def test_the_appendix_table_matches_the_store(vintage_panel, live_cattle):
    """The guard that makes §A.2 a real example rather than a plausible-looking one.

    Every long and short in the appendix is checked against the committed vintage fixture,
    which `tests/fixtures/build_fixtures.py` cuts straight from the store. If someone edits
    a figure in the document, or the CFTC restates that week, this fails.
    """
    got = vintage_panel[(vintage_panel["market_code"] == LIVE_CATTLE_CODE)
                        & (vintage_panel["report_date"] == LIVE_CATTLE_WEEK)]
    assert not got.empty, "the vintage fixture no longer carries the appendix's market-week"
    for category, long_, short_ in LIVE_CATTLE_ROWS:
        row = got[got["category"] == category]
        assert len(row) == 1, f"{category}: expected one row, got {len(row)}"
        assert int(row["long_contracts"].iloc[0]) == long_, category
        assert int(row["short_contracts"].iloc[0]) == short_, category
    assert int(got["open_interest"].max()) == LIVE_CATTLE_OI


def test_live_cattle_q_sell_reproduces_the_appendix(live_cattle):
    """§A.2: `1.0(67,025) + 0.4(61,596) = 91,663.4`.

    Two terms, not one. The fragile side of a real market is rarely a single category, and
    the swap book here is two thirds the size of the fund book in gross terms.
    """
    assert market_fragility(live_cattle)["q_sell"].iloc[0] == pytest.approx(91_663.4)


def test_live_cattle_q_buy_reproduces_the_appendix(live_cattle):
    """§A.2: `0.5(22,702) + 0.1(98,985) + 0.6(6,934) = 25,409.9`."""
    assert market_fragility(live_cattle)["q_buy"].iloc[0] == pytest.approx(25_409.9)


def test_live_cattle_phi_reproduces_the_appendix(live_cattle):
    """§A.2: `211,386.1 / 596,898 = 0.354`."""
    phi = market_fragility(live_cattle)["phi"].iloc[0]
    assert phi == pytest.approx(211_386.1 / 596_898)
    assert round(phi, 3) == 0.354


def test_live_cattle_asymmetry_ratio(live_cattle):
    """§A.2: "a ratio of 3.61", and §A.2's retained extreme: "at 3.61, the 70th percentile".

    Also the bound this ratio lives under, which module spec §6.3 now states: the weight
    table caps it at `max(w)/min(w)` before any data is involved.
    """
    frag = market_fragility(live_cattle).iloc[0]
    ratio = frag["q_sell"] / frag["q_buy"]
    assert ratio == pytest.approx(3.6074, abs=1e-4)

    w = cfg.DISAGGREGATED_WEIGHTS
    assert ratio <= max(w.values()) / min(w.values())


def test_the_weight_and_not_the_size_decides_the_q_buy_side(live_cattle):
    """§A.2: Producer/Merchant carries the largest net and contributes LESS than Other
    Reportable, whose net is a quarter of the size.

    This is the inversion the whole weighting exists to produce, and it does not appear in
    the constructed example, where the hedger is the only net-short category. A real example
    was chosen partly for this.
    """
    con = contributions(live_cattle)
    buy = con[con["q_side"] == "buy"].set_index("category")
    assert buy.loc["producer_merchant", "net"] == -98_985
    assert buy.loc["other_reportable", "net"] == -22_702
    assert abs(buy.loc["producer_merchant", "net"]) > 4 * abs(buy.loc["other_reportable", "net"])
    assert buy.loc["producer_merchant", "q_contribution"] == pytest.approx(9_898.5)
    assert buy.loc["other_reportable", "q_contribution"] == pytest.approx(11_351.0)
    assert (buy.loc["producer_merchant", "q_contribution"]
            < buy.loc["other_reportable", "q_contribution"])


def test_live_cattle_days_to_liquidate_reproduces_the_appendix(live_cattle):
    """§A.5 continued: `T_sell = 91,663.4 / (0.2 x 75,328.6) = 6.08` and `T_buy = 1.69`.

    The volume is the measured whole-market ADV, quoted in the appendix, and is passed in
    rather than looked up so this runs offline. `test_appendix_live.py` recomputes it.
    """
    frag = market_fragility(live_cattle).iloc[0]
    adv = 75_328.6
    assert exit_pressure(frag["q_sell"], frag["open_interest"],
                         volume=adv)["days_to_liquidate"] == pytest.approx(6.08, abs=0.01)
    assert exit_pressure(frag["q_buy"], frag["open_interest"],
                         volume=adv)["days_to_liquidate"] == pytest.approx(1.69, abs=0.01)
    # §A.5's own argument for the weighting, on this market: the unweighted fund net.
    assert exit_pressure(67_025, LIVE_CATTLE_OI,
                         volume=adv)["days_to_liquidate"] == pytest.approx(4.45, abs=0.01)


def test_live_cattle_is_the_template_shape(live_cattle):
    """§A.2 reads this market as a fragile long side facing an immovable hedged short one.

    Asserted through `shape_labels` rather than by eye, because that is the classifier every
    amendment from B28 onward counts with.
    """
    net = (live_cattle.set_index("category")["long_contracts"]
           - live_cattle.set_index("category")["short_contracts"])
    got = shape_labels(pd.Series([net["producer_merchant"]]),
                       pd.Series([net["managed_money"]]))
    assert got.iloc[0] == "fragile_long"
