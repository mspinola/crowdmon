"""Appendix §A.2's real worked example against a REAL store. Skips when there is not one.

`test_appendix.py` asserts the published figures against the committed fixture, so it runs
offline and catches an edit to the document. It cannot catch the other failure: the CFTC
restating report week 2026-07-28, or the volume window drifting far enough that §A.5's
quoted six days stops being what the store says. A design document carrying live figures
rots quietly, and the whole point of putting a real market in the appendix is lost if
nothing ever recomputes it.

The split is deliberate. Anything derived only from the COT rows is asserted exactly,
because a past report week does not move unless it is restated. Anything derived from a
trailing price window is asserted within a band, because it moves every day by design, and
the band exists to say when the document needs updating rather than to pin a number.
"""
import pandas as pd
import pytest

from crowdmon.futures import contributions, exit_pressure, market_fragility

pytestmark = pytest.mark.needs_vintage

CODE = "057642"
WEEK = pd.Timestamp("2026-07-28")
#: Every figure the appendix prints for this market, in the order §A.2 prints them.
PUBLISHED = {
    "open_interest": 298_449,
    "q_sell": 91_663.4,
    "q_buy": 25_409.9,
    "phi_numerator": 211_386.1,
    "phi": 211_386.1 / 596_898,
    "ratio": 3.6074,
    "mm_share_of_phi_numerator": 0.486,
    "adv": 75_328.6,
    "t_sell": 6.08,
    "t_buy": 1.69,
}


@pytest.fixture(scope="module")
def market():
    """The appendix's market-week, as of the release date the appendix names."""
    pytest.importorskip("cotdata")
    try:
        from crowdmon.futures import VintageCotSource

        panel = VintageCotSource(report_type="disaggregated").load("2026-07-31")
    except Exception as exc:                                      # noqa: BLE001
        pytest.skip(f"no readable vintage store: {exc}")
    got = panel[(panel["market_code"] == CODE) & (panel["report_date"] == WEEK)]
    if got.empty:
        pytest.skip("store does not carry the appendix's market-week")
    return got


def test_the_cot_figures_still_say_what_the_appendix_says(market):
    """The exact half. A restatement of this week fails here, which is what should happen:
    an analysis document is a record and must not be edited to match, but a DESIGN document
    quoting live figures must be, and this is what tells someone to do it."""
    frag = market_fragility(market).iloc[0]
    assert int(frag["open_interest"]) == PUBLISHED["open_interest"]
    assert frag["q_sell"] == pytest.approx(PUBLISHED["q_sell"])
    assert frag["q_buy"] == pytest.approx(PUBLISHED["q_buy"])
    assert frag["phi"] == pytest.approx(PUBLISHED["phi"])
    assert frag["q_sell"] / frag["q_buy"] == pytest.approx(PUBLISHED["ratio"], abs=1e-4)

    con = contributions(market)
    numerator = float((con["weight"] * con["gross"]).sum())
    assert numerator == pytest.approx(PUBLISHED["phi_numerator"], abs=0.1)
    mm = con[con["category"] == "managed_money"].iloc[0]
    assert (mm["weight"] * mm["gross"] / numerator
            == pytest.approx(PUBLISHED["mm_share_of_phi_numerator"], abs=5e-4))


def test_the_weight_beats_size_inversion_is_still_in_the_data(market):
    """§A.2 rests a paragraph on Producer/Merchant carrying the largest short net and the
    smaller `Q_buy` contribution. If that ever reverses, the paragraph is wrong even though
    every number in the table is still right."""
    buy = contributions(market).set_index("category")
    assert buy.loc["producer_merchant", "net"] < buy.loc["other_reportable", "net"]
    assert (buy.loc["producer_merchant", "q_contribution"]
            < buy.loc["other_reportable", "q_contribution"])


def test_the_volume_the_appendix_quotes_has_not_drifted_far(market):
    """The banded half. `adv` is a trailing whole-market window and moves every session, so
    this is not a pin: 5% is the point at which §A.5's "6.08 days" stops rounding to what
    the store would print, and the failure message is an instruction, not a bug report."""
    from crowdmon.futures import ContractMaster, add_volume, fragility_frame

    annotated = ContractMaster.load().annotate(market)
    frag = add_volume(fragility_frame(annotated).merge(
        annotated[["market_code", "symbol"]].drop_duplicates(),
        on="market_code", how="left"))
    row = frag.iloc[0]
    if pd.isna(row["adv"]):
        pytest.skip("store has no LE volume; §A.5's figures cannot be rechecked")

    assert row["adv"] == pytest.approx(PUBLISHED["adv"], rel=0.05), (
        f"whole-market ADV has moved from the {PUBLISHED['adv']:,.1f} appendix §A.5 quotes "
        f"to {row['adv']:,.1f}. Update §A.5, §A.7 and this constant together.")
    for side, expected in (("sell", PUBLISHED["t_sell"]), ("buy", PUBLISHED["t_buy"])):
        got = exit_pressure(row[f"q_{side}"], row["open_interest"],
                            volume=row["adv"])["days_to_liquidate"]
        assert got == pytest.approx(expected, rel=0.05), f"T_{side}"


def test_live_cattle_carries_the_shape_in_every_week_the_store_holds(market):
    """§A.2's claim that this market is not a lucky week: Producer/Merchant net short and
    Managed Money net long in all 82 vintage weeks. B36 measured that the per-market
    classification is much less stable than pooling suggests, so the example was chosen from
    the set that holds in both halves of the window rather than over the pooled 82.

    Takes `market` only for its store guard, not its rows.
    """
    from crowdmon.futures import from_vintage, shape_labels

    panel = from_vintage(market_code=CODE)
    net = (panel.assign(net=panel["long_contracts"] - panel["short_contracts"])
                .groupby(["report_date", "category"])["net"].sum().unstack("category"))
    assert len(net) >= 82
    shapes = shape_labels(net["producer_merchant"], net["managed_money"])
    assert (shapes == "fragile_long").all(), (
        f"live cattle no longer carries the template in every week: "
        f"{shapes.value_counts().to_dict()}")
