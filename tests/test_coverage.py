"""Coverage ladder arithmetic on constructed frames.

`test_coverage_live.py` checks the claims against the real store. This file pins the two
traps that make the module necessary, both of which produce a confident wrong answer:

- **a market whose name changes mid-history must appear once**, not once per name
- **a market that survives every join and dies at a window** must report the window, not the
  join, because the two send a maintainer to different places
"""
import pandas as pd
import pytest

from crowdmon.futures.coverage import (
    LADDER,
    CoverageError,
    coverage_ladder,
    coverage_summary,
    format_coverage,
    unscoreable,
)

WEEKS = pd.date_range("2020-01-07", periods=10, freq="7D")


def _category(code="000001", name="A MARKET", *, weeks=WEEKS, **columns):
    """One market, one category, `weeks` rows, every ladder column present by default."""
    n = len(weeks)
    base = {"symbol": "XX", "price": 100.0, "net_notional_usd": 1e6,
            "sigma_daily": 0.01, "net_risk_usd": 1e4, "adv": 5e4,
            "net_risk_usd_z": 0.5}
    base.update(columns)
    return pd.DataFrame({"market_code": code, "market_name": name,
                         "report_date": weeks,
                         **{k: [v] * n if not isinstance(v, list) else v
                            for k, v in base.items()}})


def _market(code="000001", name="A MARKET", *, weeks=WEEKS, **columns):
    n = len(weeks)
    base = {"dtl_sell": 3.0, "phi": 0.4, "phi_pct": 0.5, "illiquidity_sell": 0.5,
            "crowding_long": 0.5, "damage_sell": 0.4, "damage_sell_pct": 0.6}
    base.update(columns)
    return pd.DataFrame({"market_code": code, "market_name": name,
                         "report_date": weeks,
                         **{k: [v] * n if not isinstance(v, list) else v
                            for k, v in base.items()}})


# ── the rename trap: the reason this is keyed on market_code ────────────────
def test_a_market_that_changed_name_appears_once():
    """The defect that would make the fix worse than the bug.

    On the real panel, grouping on `(market_code, market_name)` reports six unscoreable
    markets rather than two: cotton, cocoa, sugar and coffee each show a zero-scoring block
    under a pre-migration NYBOT name inside a code that scores 742 weeks. **The invented
    markets outnumber the real ones three to two.**
    """
    old = _category(name="COTTON NO. 2 - NEW YORK BOARD OF TRADE", weeks=WEEKS[:4])
    new = _category(name="COTTON NO. 2 - ICE FUTURES U.S.", weeks=WEEKS[4:])
    per_category = pd.concat([old, new], ignore_index=True)
    per_market = pd.concat([
        _market(name="COTTON NO. 2 - NEW YORK BOARD OF TRADE", weeks=WEEKS[:4]),
        _market(name="COTTON NO. 2 - ICE FUTURES U.S.", weeks=WEEKS[4:]),
    ], ignore_index=True)

    got = coverage_ladder(per_category, per_market)
    assert len(got) == 1, f"one code must give one row, got {len(got)}"
    assert got["weeks"].iloc[0] == len(WEEKS)
    assert got["drops_at"].isna().all(), "a fully covered market must not be flagged"
    # The label is the CURRENT name, not the one it carried for most of its history.
    assert got["market_name"].iloc[0] == "COTTON NO. 2 - ICE FUTURES U.S."
    assert unscoreable(per_category, per_market).empty


def test_two_genuinely_different_codes_stay_apart():
    """The rename fix must not merge markets that really are distinct. Both lumber codes
    are real and separate, and a coverage report that collapsed them would hide one."""
    per_category = pd.concat([_category("058643", "RANDOM LENGTH LUMBER"),
                              _category("058644", "LUMBER")], ignore_index=True)
    got = coverage_ladder(per_category)
    assert sorted(got["market_code"]) == ["058643", "058644"]


# ── the two-rung finding: a count alone sends you to the wrong place ────────
def test_a_market_that_dies_at_the_join_reports_the_join():
    """058643's shape: almost no usable price, so it never reaches a notional."""
    per_category = _category("058643", price=[100.0] + [None] * 9,
                             net_notional_usd=[1e6] + [None] * 9)
    got = coverage_ladder(per_category)
    row = got.iloc[0]
    assert row["price"] == 1 and row["notional"] == 1
    assert row["drops_at"] is None or row["drops_at"] not in ("contract_spec",)


def test_a_market_with_full_exit_duration_that_still_scores_nothing_reports_the_window():
    """**058644's shape, and the reason a bare count is not enough.**

    Complete `dtl_sell` in every week, and no composite at all, because the percentile
    windows stack on top of the extremity window. A report saying only "0 scoreable weeks"
    sends a maintainer to look at prices, where nothing is wrong.
    """
    per_category = _category("058644")
    per_market = _market("058644", crowding_long=None, damage_sell=None,
                         damage_sell_pct=None)

    got = coverage_ladder(per_category, per_market)
    row = got.iloc[0]
    assert row["exit_duration"] == len(WEEKS), "exit duration is complete"
    assert row["composite"] == 0
    assert row["drops_at"] == "crowding", (
        f"must name the rung that bites, got {row['drops_at']!r}. Before 2026-08-02 §B18 the "
        f"ladder skipped the composite's own terms and reported 'composite', one rung late")

    flagged = unscoreable(per_category, per_market)
    assert len(flagged) == 1 and flagged["drops_at"].iloc[0] == "crowding"


def test_drops_at_names_the_first_zero_not_the_last():
    """A market failing early fails everything after it, so the report must name the cause
    rather than the final symptom."""
    per_category = _category(symbol=None, net_notional_usd=None, net_risk_usd=None,
                             net_risk_usd_z=None)
    per_market = _market(damage_sell=None, damage_sell_pct=None)
    got = coverage_ladder(per_category, per_market)
    assert got["drops_at"].iloc[0] == "contract_spec"


# ── shape, and staleness of the hand-written ladder ─────────────────────────
def test_the_ladder_covers_every_term_the_composite_is_built_from():
    """The ladder is a hand-written list, so this is what stops it going stale.

    **The first version of this test had the same blind spot as the ladder it guarded.** It
    checked the columns `add_composite` EMITS and not the ones it COMPUTES, so it passed
    while `LADDER` skipped all three factors of `D = C x I x Phi`. The consequence was that
    `058644` reported dropping at `composite` when it drops a rung earlier, at `crowding`
    (`2026-08-02 §B18`).

    Both halves are checked now. Four rungs were added to this package in two days, so a
    ladder that silently omits one reports a market as covered while it produces nothing.
    """
    from crowdmon.futures import composite

    ladder_columns = {c.format(side="sell", crowd="long") for _, c, _ in LADDER}

    # What the composite EMITS.
    for emitted in ("damage_sell", "damage_sell_pct"):
        assert emitted in ladder_columns, f"{emitted} emitted by composite but not in LADDER"
    assert "damage_sell_pct" in composite.COMPOSITE_COLUMNS

    # What it COMPUTES: the three factors of D, and the inputs they come from. Missing any of
    # these makes `drops_at` name a rung later than the one that actually bit.
    for factor in ("crowding_long", "illiquidity_sell", "phi_pct", "phi", "dtl_sell"):
        assert factor in ladder_columns, (
            f"{factor} is a term D is built from but is absent from LADDER; a market failing "
            f"there will be reported as failing at a later rung")


def test_the_ladder_is_not_assumed_monotonic():
    """`holder_fragility` is price-free, so it can exceed every price-dependent rung.

    Measured on the real panel: `058643` has **880** weeks of `phi` against **24** of
    `dtl_sell`, a 36x rise in the middle of the ladder. Anyone assuming coverage only falls
    will mis-locate every failure of this shape, so the price-free rungs are declared.
    """
    from crowdmon.futures.coverage import PRICE_FREE

    assert "holder_fragility" in PRICE_FREE
    assert PRICE_FREE <= {r for r, _, _ in LADDER}, "PRICE_FREE names a rung that is not real"

    per_category = _category(price=None, net_notional_usd=None, sigma_daily=None,
                             net_risk_usd=None, adv=None, net_risk_usd_z=None)
    per_market = _market(dtl_sell=None, damage_sell=None, damage_sell_pct=None,
                         phi=0.4, phi_pct=0.5, illiquidity_sell=None, crowding_long=None)
    got = coverage_ladder(per_category, per_market)
    row = got.iloc[0]
    assert row["price"] == 0 and row["holder_fragility"] == len(WEEKS), (
        "a price-free rung must survive a market with no prices at all")
    assert row["drops_at"] == "price"


def test_buy_side_uses_buy_columns():
    per_category = _category()
    per_market = _market().rename(columns={"dtl_sell": "dtl_buy",
                                           "damage_sell": "damage_buy",
                                           "damage_sell_pct": "damage_buy_pct"})
    got = coverage_ladder(per_category, per_market, side="buy")
    assert got["composite_percentile"].iloc[0] == len(WEEKS)


def test_an_absent_composite_frame_reports_the_rungs_that_exist():
    got = coverage_ladder(_category())
    assert "extremity_z" in got.columns
    assert "composite" not in got.columns
    assert got["drops_at"].isna().all()


def test_summary_counts_markets_not_rows():
    per_category = pd.concat([_category("000001"), _category("000002", price=None,
                                                             net_notional_usd=None)],
                             ignore_index=True)
    got = coverage_summary(per_category)
    assert got["markets"] == 2
    assert got["contract_spec"] == 2
    assert got["price"] == 1
    assert got["unscoreable"] == 1


def test_bad_side_raises():
    with pytest.raises(CoverageError, match="side must be"):
        coverage_ladder(_category(), side="both")


def test_missing_key_raises_rather_than_returning_a_plausible_frame():
    with pytest.raises(CoverageError, match="market_code"):
        coverage_ladder(_category().drop(columns=["market_code"]))


def test_empty_input_is_an_empty_frame_not_a_crash():
    assert coverage_ladder(pd.DataFrame()).empty
    assert format_coverage(pd.DataFrame()) == "no markets"


def test_format_only_unscoreable():
    per_category = pd.concat([_category("000001"), _category("000002", symbol=None)],
                             ignore_index=True)
    text = format_coverage(coverage_ladder(per_category), only_unscoreable=True)
    assert "000002" in text and "000001" not in text
    assert "DROPS AT contract_spec" in text
