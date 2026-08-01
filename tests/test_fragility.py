"""Fragility: the Phi bound, the directional split, and the vocabulary refusal.

The Phi bound is the assertion that pins the definition. An earlier draft of the spec used
`Σ w_c |P_c| / OI`, which is unbounded and wrong, and the bound is what stops a regression
to it being discovered as a strange result rather than as a failure.
"""
import pandas as pd
import pytest

from crowdmon.core import config as cfg
from crowdmon.futures import contributions, decompose_breadth, market_fragility
from crowdmon.futures.fragility import FragilityError


# ── The Phi bound (handoff §7) ──────────────────────────────────────────────
def test_phi_is_bounded_over_twenty_years_every_market_every_week(history_panel):
    """`0 <= Phi <= 1` across the whole committed history, not on a sample.

    Gold, crude and oats, 2006-06-13 to 2026-07-28. The bound holds because
    `Σ_c (L_c + S_c) = 2·(OI − spreading) <= 2·OI` and every weight is in `[0, 1]`, so this
    is really testing that the numerator is built from GROSS positions rather than nets.
    Nets sum to zero across categories and cannot form a share of anything.
    """
    frag = market_fragility(history_panel)
    phi = pd.to_numeric(frag["phi"], errors="coerce").dropna()
    # Market-weeks, not rows: the fixture's 15,070 rows are five category rows apiece.
    assert len(phi) > 3_000, "fixture shrank; this is meant to be a claim about history"
    assert phi.min() >= 0.0
    assert phi.max() <= 1.0


def test_phi_is_bounded_on_the_vintage_cross_section(vintage_panel):
    phi = pd.to_numeric(market_fragility(vintage_panel)["phi"], errors="coerce").dropna()
    assert phi.between(0.0, 1.0).all()


def test_the_wrong_unbounded_formula_would_be_caught(make_panel):
    """The regression this bound exists to prevent, demonstrated rather than asserted.

    `Σ w_c |P_c| / OI` exceeds 1 on a market where one heavily weighted category holds a
    net position approaching the whole open interest. The correct gross-over-2·OI form does
    not, on the same rows. If someone swaps the formula back, a crowded market trips the
    check rather than producing a number nobody questions.
    """
    panel = make_panel({
        "managed_money": [(98_000, 3_000)],
        "producer_merchant": [(2_000, 97_000)],
    }, open_interest=100_000)
    frag = market_fragility(panel)
    assert 0.0 <= frag["phi"].iloc[0] <= 1.0

    net_abs = (panel.groupby("category")
               .apply(lambda g: abs(g["long_contracts"].iloc[0] - g["short_contracts"].iloc[0]),
                      include_groups=False))
    wrong = sum(cfg.DISAGGREGATED_WEIGHTS[c] * v for c, v in net_abs.items()) / 100_000
    assert wrong > 1.0, "the counterexample stopped being one; pick larger positions"


def test_phi_reaches_its_ceiling_only_where_the_numerator_can_see_the_denominator(make_panel):
    """Spreading counts toward open interest and carries no directional exit, so it is
    outside the numerator by choice. `phi_denominator_covered` reports the resulting
    ceiling, rather than leaving a reader to wonder why Phi never approaches 1."""
    panel = make_panel({"managed_money": [(40_000, 40_000)]}, open_interest=100_000)
    panel.loc[:, "spread_contracts"] = 20_000
    frag = market_fragility(panel)
    # w=1.0, gross 80,000, denominator 200,000.
    assert frag["phi"].iloc[0] == pytest.approx(0.4)
    assert frag["phi_denominator_covered"].iloc[0] == pytest.approx(0.4)


# ── The directional split (handoff §7) ──────────────────────────────────────
def test_q_sell_and_q_buy_each_sum_only_their_own_sign(make_panel):
    """Forced longs sell and forced shorts buy. Summing them describes no actual flow.

    Managed Money is net +79,000 at weight 1.0, so it belongs entirely to `Q_sell`.
    Producer/Merchant is net -79,000 at weight 0.1, so it belongs entirely to `Q_buy`. Each
    contributes to exactly one and zero to the other, which is what makes the two numbers
    describe events that could actually happen.
    """
    panel = make_panel({
        "managed_money": [(80_000, 1_000)],
        "producer_merchant": [(5_000, 84_000)],
    }, open_interest=100_000)
    frag = market_fragility(panel)
    assert frag["q_sell"].iloc[0] == pytest.approx(1.0 * 79_000)
    assert frag["q_buy"].iloc[0] == pytest.approx(0.1 * 79_000)
    assert frag["q_net"].iloc[0] == pytest.approx(79_000 - 7_900)


def test_a_category_never_contributes_to_both_sides(history_panel):
    """On real data, over the whole history: every category row is on one side or flat."""
    contrib = contributions(history_panel)
    both = contrib[(contrib["q_side"] == "sell") & (contrib["net"] < 0)]
    assert both.empty
    assert set(contrib["q_side"]) <= {"sell", "buy", "flat"}
    assert (contrib.loc[contrib["q_side"] == "flat", "net"] == 0).all()


def test_q_sell_and_q_buy_are_never_silently_combined(history_panel):
    """`q_gross` exists and is named so it cannot be mistaken for a flow, but the two
    directional figures must not be equal to it or to each other except by coincidence."""
    frag = market_fragility(history_panel)
    assert (frag["q_gross"] == frag["q_sell"] + frag["q_buy"]).all()
    # If these ever coincided across the board, the split had collapsed.
    assert not (frag["q_sell"] == frag["q_buy"]).all()


# ── Contributions decompose Phi exactly ─────────────────────────────────────
def test_category_contributions_sum_to_phi(history_panel):
    """A decomposition, not an approximation. The walkthrough leans on this to say which
    category a headline Phi is really about."""
    frag = market_fragility(history_panel).set_index(
        ["report_date", "market_code", "report_type", "combined"])
    summed = (contributions(history_panel)
              .groupby(["report_date", "market_code", "report_type", "combined"])
              ["phi_contribution"].sum())
    joined = frag["phi"].dropna().align(summed, join="inner")
    assert len(joined[0]) > 3_000
    assert joined[0].to_numpy() == pytest.approx(joined[1].to_numpy(), rel=1e-9)


def test_the_top_contributor_is_reported_so_a_headline_is_not_over_read(vintage_panel):
    frag = market_fragility(vintage_panel)
    assert frag["top_phi_category"].notna().all()
    assert (frag["top_phi_share"] <= frag["phi"] + 1e-9).all()


# ── Vocabulary and configuration refusals (handoff §7) ─────────────────────
def test_an_unknown_category_raises_rather_than_being_dropped(make_panel):
    """The failure this prevents is invisible: an unmapped category is dropped from every
    sum it belongs in, which under-reports exit pressure without failing anywhere."""
    panel = make_panel({"managed_money": [(10, 5)], "hedge_fund_of_funds": [(10, 5)]})
    with pytest.raises(cfg.ConfigError, match="hedge_fund_of_funds"):
        market_fragility(panel)


def test_legacy_has_no_weights_and_says_why(make_panel):
    panel = make_panel({"noncommercial": [(10, 5)]}, report_type="legacy")
    with pytest.raises(cfg.ConfigError, match="Legacy is deliberately absent"):
        market_fragility(panel)


def test_a_panel_spanning_report_types_is_refused(make_panel):
    a = make_panel({"managed_money": [(10, 5)]})
    b = make_panel({"leveraged": [(10, 5)]}, report_type="tff", market_code="TFF01")
    with pytest.raises(FragilityError, match="report types"):
        market_fragility(pd.concat([a, b], ignore_index=True))


def test_a_category_missing_from_the_data_is_fine(make_panel):
    """One-directional on purpose: a market where nobody is a swap dealer is a market, not
    a parse failure. Only the reverse (data category with no weight) is an error."""
    frag = market_fragility(make_panel({"managed_money": [(10_000, 1_000)]}))
    assert len(frag) == 1


# ── Breadth-depth identity ──────────────────────────────────────────────────
def test_breadth_depth_reconstructs_the_position_change_exactly(history_panel):
    """`ΔP = N₀·Δq + q₀·ΔN + ΔN·Δq` is algebra, so the residual is floating point only.
    A growing residual means the terms use period means rather than the prior week."""
    for side in ("long", "short"):
        out = decompose_breadth(history_panel, side=side)
        known = out[out["residual"].notna()]
        assert not known.empty
        scale = known["position"].abs().clip(lower=1.0)
        assert (known["residual"].abs() <= 1e-6 * scale).all()


def test_a_suppressed_trader_count_yields_null_not_an_imputed_average(history_panel):
    """CFTC withholds counts where too few traders would be identifiable, and null is a
    routine state rather than an error. An imputed count feeds straight into the average
    position per trader, which is the number the quadrant is read off."""
    out = decompose_breadth(history_panel, side="long")
    suppressed = out[out["traders"].isna()]
    assert not suppressed.empty, "fixture no longer exercises suppression"
    assert suppressed["avg_position"].isna().all()
    assert suppressed["quadrant"].isna().all()


def test_breadth_refuses_a_net_side(history_panel):
    with pytest.raises(ValueError, match="different traders"):
        decompose_breadth(history_panel, side="net")
