"""The appendix's own worked example, executed.

`docs/design/crowdmon_plain_language_summary.md` §A.1-A.11 is the authoritative statement of
every formula in this package: where a handoff and the appendix disagree, the appendix wins.
An authoritative document whose worked example is never run is a document nobody has checked,
so this file runs it.

Every figure asserted below is transcribed from §A.2 and §A.5, not computed and then written
down. If one of these fails, the implementation has drifted from the specification and the
implementation is what is wrong.

The example is cocoa-shaped and deliberately synthetic: the appendix says it was constructed
to be structurally realistic rather than drawn from data. Whether real markets share that
shape is a separate question, measured in `docs/analysis/` and answered "about half of them"
(`docs/design/amendments-2026-08-01.md` §A4).
"""
import pandas as pd
import pytest

from crowdmon.core import config as cfg
from crowdmon.futures import contributions, exit_pressure, market_fragility

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

    True in the example. The appendix calls a single category dominating "typical", and that
    part does NOT hold on real data: measured across the 279-market Disaggregated universe,
    Managed Money is the top contributor in 81 markets (29%). See amendments §A3. This test
    pins the example, not the generalisation.
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
