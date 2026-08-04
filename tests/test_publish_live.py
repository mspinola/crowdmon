"""The published panel against the real store: the numbers, and the two §D9/§D10 counts.

Skipped without `COTDATA_STORE` pointing at a populated store, which is every CI run. See
`bin/check_skips.py` for why a data-absent skip is a failure under `--profile live` and
merely allowed under `--profile ci`.

**Why the figures are pinned here rather than described.** The panel is read by a package
that cannot import this one, so the only place a schema or a count can be checked against
the code that produced it is this repo. A consumer discovering that `trigger_sell_sigma`
went null would attribute it to its own reader.
"""
import pandas as pd
import pytest

from crowdmon.futures.publish import (
    PANEL_COLUMNS,
    build_damage_panel,
    panel_manifest,
    publish_panel,
)
from crowdmon.futures.report import CLOSE_SIGMA

WEEK = "2026-07-28"

#: One guard for the whole chain, because the chain is the unit: this file's figures come
#: from a panel that joins COT, contract specs, two price tiers, volume and an Amihud panel,
#: and a store missing any one of them produces no panel rather than a partial one. The
#: reason string is matched by `bin/check_skips.py`'s `DATA_ABSENT`, so it is a failure under
#: `--profile live` and merely allowed under `ci`.
NO_PANEL = "the damage panel cannot be built from this store"


@pytest.fixture(scope="module")
def build():
    try:
        return build_damage_panel(with_commonality=True)
    except Exception as exc:                                            # noqa: BLE001
        pytest.skip(f"{NO_PANEL}: {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def week(build):
    return build.panel[build.panel["report_date"] == build.report_date]


def test_the_panel_is_the_declared_columns_and_nothing_else(build):
    assert list(build.panel.columns) == list(PANEL_COLUMNS)


def test_both_report_types_are_present_so_the_financials_are_reachable(week):
    """Disaggregated alone is a commodity panel.

    `2026-08-04 §D7` is the argument for why Legacy cannot stand in for TFF here: the two
    agree on open interest and non-reportables and on nothing else, and sterling reports
    non-commercial short 64,814 while leveraged funds are long 41,097. So equities,
    currencies and rates reach a reader through TFF or not at all.
    """
    assert set(week["report_type"].dropna()) == {"disaggregated", "tff"}
    classes = set(week["asset_class"].dropna())
    assert {"Equities", "Currencies", "Fixed Income"} <= classes, sorted(classes)
    assert len(classes) == 10, sorted(classes)


def test_the_universe_is_the_47_covered_markets(week):
    """`2026-08-04 §D11` landed the backlog tranche at 47 covered markets."""
    assert week["market_code"].nunique() == 47
    assert int((week["score_state_sell"] == "scored").sum()) == 43


def test_the_trigger_counts_reproduce_d9(week):
    """37 forced-sell levels and 35 forced-buy, week ending 2026-07-28 (`2026-08-04 §D9`)."""
    assert str(pd.Timestamp(week["report_date"].iloc[0]).date()) == WEEK
    assert int(week["trigger_sell_sigma"].notna().sum()) == 37
    assert int(week["trigger_buy_sigma"].notna().sum()) == 35


def test_the_pool_column_is_supplied_so_the_agreement_flag_is_not_null(week):
    """The whole point of publishing rather than reusing the reproducer's build.

    `docs/analysis/reproduce_single_number.py` calls `add_trigger_distance` with no
    `pool_column`, which leaves every `*_pool_agrees` null and ships a trigger that cannot
    say whether the book it would force is actually there. Here it is supplied, and
    `2026-08-04 §D10` measures that the answer is often no.
    """
    agrees = week["trigger_sell_pool_agrees"]
    assert agrees.notna().sum() == 37, "a pool answer for every market with a sell trigger"
    assert bool((agrees == False).any()), "no disagreements at all means the pool went unsupplied"  # noqa: E712


def test_the_pool_check_removes_half_of_d9s_close_and_severe_cell(week):
    """§D9 named four CLOSE-and-SEVERE markets; §D10's pool check leaves two.

    This is the two amendments composed, and it is the reason `format_offside` suppresses
    the quadrant rather than annotating it. Class III milk and DJIA are the two that fall
    out, and DJIA is one of the three markets §D10 measures as pool-opposite on EVERY
    horizon, as well as being §D2's level-floor case at a 0.27-day exit.
    """
    frame = week.copy()
    frame["sigma"] = pd.to_numeric(frame["trigger_sell_sigma"], errors="coerce")
    frame["d"] = pd.to_numeric(frame["damage_sell_pct"], errors="coerce")
    frame = frame.dropna(subset=["sigma", "d"])
    cell = frame[(frame["sigma"] <= CLOSE_SIGMA) & (frame["d"] >= 0.75)]

    names = sorted(n.split(" - ")[0] for n in cell["market_name"])
    assert names == ["CORN", "DJIA x $5", "MILK, Class III", "SOYBEAN MEAL"], names

    survives = cell[cell["trigger_sell_pool_agrees"] != False]          # noqa: E712
    assert sorted(n.split(" - ")[0] for n in survives["market_name"]) == [
        "CORN", "SOYBEAN MEAL"]


def test_beta_is_attached_because_the_composite_chain_never_attaches_it(week, build):
    """README reading instruction 4 has no per-row carrier unless the publisher adds one."""
    assert build.provenance["with_commonality"] is True
    assert int(week["beta"].notna().sum()) >= 40
    assert float(week["beta"].min()) < 0.5 < float(week["beta"].max())


def test_the_offside_columns_are_the_latest_week_only(build):
    """A point-in-time overlay, by cost rather than by correctness.

    `add_trigger_distance` is ~95,000 price-store reads over full history against 90 for
    one week. A consumer must not plot a trigger history, and this is what says so.
    """
    earlier = build.panel[build.panel["report_date"] < build.report_date]
    assert earlier["trigger_sell_sigma"].notna().sum() == 0


def test_the_score_state_split_names_two_opposite_causes(week):
    """`2026-08-04 §C26` one level up: a blank cell is not a low value."""
    states = set(week["score_state_sell"].dropna())
    assert "scored" in states
    assert states <= {"scored", "warmup", "no_crowding", "no_illiquidity", "no_fragility"}


def test_a_published_panel_reads_back_identical(build, tmp_path):
    publish_panel(build, tmp_path)
    back = pd.read_parquet(tmp_path / "damage" / build.report_date.date().isoformat()
                           / "panel.parquet")
    assert list(back.columns) == list(PANEL_COLUMNS)
    assert len(back) == len(build.panel)
    assert str(back["trigger_sell_pool_agrees"].dtype) == "boolean"


def test_the_manifest_counts_match_the_panel_it_ships_with(build):
    got = panel_manifest(build)
    week = build.panel[build.panel["report_date"] == build.report_date]
    assert got["counts"]["markets"] == int(week["market_code"].nunique())
    assert got["counts"]["rows"] == len(build.panel)
    assert got["current_report_date"] == WEEK
