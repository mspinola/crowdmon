"""Coverage against a REAL store. Skips when there is not one.

`test_coverage.py` checks the arithmetic on constructed frames. This file checks the claims
the module rests on, which is the pattern every other engine here follows and the one that
caught the defects in notional, riskunits, volume, impact and trigger.

The three claims that matter, all of them from `2026-08-02 §B17` and the measurements behind
the handoff that claimed this work:

- **two markets in the scored panel produce nothing, ever**, and they are the lumber codes
- **they die at different rungs**, so a bare count sends a maintainer to the wrong place
- **keying on the name invents four markets that do not exist**, outnumbering the real ones
"""
import pytest

pytestmark = pytest.mark.needs_vintage


@pytest.fixture(scope="module")
def panels():
    """The whole chain, at both grains, exactly as `reproduce_composite.build` assembles it."""
    pytest.importorskip("cotdata")
    from crowdmon.futures import (
        ContractMaster,
        add_composite,
        add_extremity,
        add_notional,
        add_risk_units,
        add_volume,
        from_current_store,
        market_fragility,
        rank_markets,
    )

    try:
        panel = from_current_store()
    except Exception as exc:                                    # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    if panel.empty or panel["market_code"].nunique() < 20:
        pytest.skip("store too small for a coverage panel")

    per_category = add_volume(add_extremity(add_risk_units(
        add_notional(ContractMaster.load().annotate(panel)))))
    volume = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
              .max().reset_index())
    per_market = market_fragility(panel).merge(
        volume, on=["report_date", "market_code"], how="left")
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    return per_category, add_composite(ranked, per_category)


def test_the_panel_contains_markets_that_score_nothing_at_all(panels):
    """The finding the §10 evaluator surfaced and this module exists to make visible.

    Caught by counting units, not by any output the package emitted. Both lumber codes
    produce no `D` in any week of their history.
    """
    from crowdmon.futures import unscoreable

    per_category, per_market = panels
    dead = unscoreable(per_category, per_market)

    assert not dead.empty, (
        "no unscoreable markets found; if the panel genuinely has none now, this test has "
        "outlived the finding and should be rewritten rather than deleted")
    codes = set(dead["market_code"])
    assert {"058643", "058644"} <= codes, (
        f"expected both lumber codes among the unscoreable, got {sorted(codes)}")
    # A hole, not a collapse. If most of the panel is unscoreable something else broke.
    assert len(dead) <= 5, f"{len(dead)} unscoreable markets is a different problem"


def test_the_two_dead_markets_die_at_different_rungs(panels):
    """**Why a count is necessary and not sufficient.**

    `058643` never gets a price. `058644` has a complete exit duration in every one of its
    weeks and still scores nothing, because the percentile windows stack. A report saying
    only "0 scoreable weeks" would send a maintainer to look at prices for both, and for one
    of them there is nothing wrong with the prices.
    """
    from crowdmon.futures import coverage_ladder

    per_category, per_market = panels
    ladder = coverage_ladder(per_category, per_market).set_index("market_code")

    early, late = ladder.loc["058643"], ladder.loc["058644"]
    assert early["price"] < early["weeks"] * 0.10, (
        f"058643 should be starved of prices, has {early['price']} of {early['weeks']}")
    assert late["exit_duration"] == late["weeks"], (
        f"058644 should have a complete exit duration, has {late['exit_duration']} of "
        f"{late['weeks']}")
    assert late["composite_percentile"] == 0
    assert early["drops_at"] != late["drops_at"], (
        f"both report {early['drops_at']!r}; the whole point is that they differ")


def test_keying_on_the_name_invents_markets_that_do_not_exist(panels):
    """The trap that would have made this module worse than the gap it closes.

    Markets migrate venue and the CFTC restates the label without changing the code, so a
    pre-migration name looks like a market that scores nothing. Measured: the invented ones
    outnumber the real ones.
    """
    per_category, per_market = panels
    scored = per_market.dropna(subset=["damage_sell_pct"])

    by_code = per_market.groupby("market_code")["damage_sell_pct"].apply(
        lambda s: s.notna().sum())
    by_pair = per_market.groupby(["market_code", "market_name"])["damage_sell_pct"].apply(
        lambda s: s.notna().sum())

    real = int((by_code == 0).sum())
    apparent = int((by_pair == 0).sum())
    assert apparent > real, (
        f"name-keying reported {apparent} zero-scoring rows against {real} real ones; the "
        f"module's choice of key rests on this gap")

    phantoms = [(c, n) for (c, n), v in by_pair.items() if v == 0 and by_code[c] > 0]
    assert phantoms, "expected pre-migration names inside codes that score fine"
    assert len(phantoms) >= real, (
        f"{len(phantoms)} invented against {real} real: the claim that the invented ones "
        f"outnumber the real ones no longer holds")
    assert not scored.empty


def test_many_codes_carry_more_than_one_name(panels):
    """The mechanism behind the trap above, measured rather than asserted."""
    per_category, _ = panels
    names = per_category.groupby("market_code")["market_name"].nunique()
    renamed = int((names > 1).sum())
    assert renamed >= 5, (
        f"only {renamed} codes carry multiple names; the case for keying on the code rests "
        f"on renaming being common")
    # Heating oil is the extreme case and includes a transposition typo in the CFTC source,
    # which is why string normalisation is not the alternative to code-keying.
    assert names.max() >= 4


def test_the_ladder_is_monotone_and_bounded_by_the_week_count(panels):
    """Every rung is a filter on the one before it, so counts can only fall."""
    from crowdmon.futures import LADDER, coverage_ladder

    per_category, per_market = panels
    ladder = coverage_ladder(per_category, per_market)
    rungs = [r for r, _, _ in LADDER if r in ladder.columns]

    for _, row in ladder.iterrows():
        assert row[rungs[0]] <= row["weeks"] + 0
        for a, b in zip(rungs, rungs[1:]):
            # Grain changes between the category rungs and the market rungs, so allow the
            # boundary to rise; within a grain the ladder must not.
            if a == "extremity_z" and b == "exit_duration":
                continue
            assert row[b] <= row[a], (
                f"{row['market_code']}: {b}={row[b]} exceeds {a}={row[a]}")


def test_most_of_the_panel_survives_the_whole_ladder(panels):
    """A guard against the module reporting a catastrophe because a rung name went stale."""
    from crowdmon.futures import coverage_summary

    per_category, per_market = panels
    summary = coverage_summary(per_category, per_market)
    assert summary["markets"] >= 20
    assert summary["composite_percentile"] >= summary["markets"] - 5
    assert summary["unscoreable"] == summary["markets"] - summary["composite_percentile"]
