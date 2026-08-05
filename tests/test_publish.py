"""The writer, against fixtures: dtypes, atomicity, and the two states a boolean must carry.

Every assertion here runs offline. The figures that need the real store are in
`test_publish_live.py`, and the split is the usual one: this file pins the CONTRACT (what a
reader is promised), that one pins the NUMBERS.

The dtype assertions look fussy and are not. An artifact is read by a package that cannot
import this one, so a column that silently changes type is a defect the consumer discovers
at render time and attributes to itself.
"""
import json

import pandas as pd
import pytest

from crowdmon.futures import brief, publish
from crowdmon.futures.publish import (
    BOOLEAN_COLUMNS,
    PANEL_COLUMNS,
    SCHEMA_VERSION,
    DamageBuild,
    PublishError,
    panel_manifest,
    publish_panel,
    store_root,
)

WEEK = pd.Timestamp("2026-07-28")


def _row(code, **kw):
    """One panel row carrying every declared column, so a test frame is a legal panel."""
    row = dict.fromkeys(PANEL_COLUMNS, None)
    row.update(report_date=WEEK, market_code=code, report_type="disaggregated",
               combined=False, market_name=f"MARKET {code}", symbol=f"S{code}",
               asset_class="Grains", damage_sell_pct=0.9, damage_buy_pct=0.2,
               score_state_sell="scored", score_state_buy="scored",
               dtl_sell=3.0, dtl_buy=4.0)
    row.update(kw)
    return row


def _build(rows=None, blocks=None) -> DamageBuild:
    frame = pd.DataFrame(rows or [_row("001"), _row("002")])
    for column in BOOLEAN_COLUMNS:
        frame[column] = frame[column].astype("boolean")
    return DamageBuild(panel=frame, blocks=blocks or {}, report_date=WEEK,
                       provenance={"crowdmon_version": "test"})


# ── the column contract ─────────────────────────────────────────────────────
def test_the_declared_columns_survive_a_round_trip(tmp_path):
    publish_panel(_build(), tmp_path)
    back = pd.read_parquet(tmp_path / "damage" / "2026-07-28" / "panel.parquet")
    assert list(back.columns) == list(PANEL_COLUMNS)


def test_a_pool_disagreement_and_an_unchecked_pool_do_not_collapse(tmp_path):
    """`False` means the observed pool is on the other side; `NA` means nobody checked.

    `2026-08-04 §D10` is explicit that these carry opposite implications, and a numpy `bool`
    column renders both as `False`. This is the assertion that keeps the nullable dtype from
    being "simplified" away by someone who sees a two-valued column in a fixture.
    """
    build = _build([_row("001", trigger_sell_pool_agrees=False),
                    _row("002", trigger_sell_pool_agrees=None),
                    _row("003", trigger_sell_pool_agrees=True)])
    publish_panel(build, tmp_path)
    back = pd.read_parquet(tmp_path / "damage" / "2026-07-28" / "panel.parquet")
    got = back.set_index("market_code")["trigger_sell_pool_agrees"]
    assert got["001"] is False or got["001"] == False        # noqa: E712
    assert pd.isna(got["002"])
    assert bool(got["003"]) is True
    assert str(back["trigger_sell_pool_agrees"].dtype) == "boolean"


# ── the manifest is generated, not written ──────────────────────────────────
def test_the_manifest_carries_the_live_reading_instructions(tmp_path):
    """Not "resembles": equals.

    The manifest is the fifth place `READING_INSTRUCTIONS` appears, after the README, the
    tuple in `brief.py`, `tests/test_reading_instructions.py` and the rendered brief. A
    hand-written copy here would be the one nothing checks, which is exactly the failure
    `2026-08-04 §C30` records.
    """
    from dataclasses import asdict

    got = panel_manifest(_build())["reading_instructions"]
    assert got == [asdict(c) for c in brief.READING_INSTRUCTIONS]


@pytest.mark.parametrize("key,module_constant", [
    ("score_states", "SCORE_STATES"), ("unwind_states", "UNWIND_STATES"),
    ("flow_states", "FLOW_STATES"), ("strata", "STRATA"),
])
def test_every_vocabulary_comes_from_its_owning_module(key, module_constant):
    """A consumer drives its rendering off these, so they may not be typed out here."""
    from crowdmon.futures import composite, flow, stratum

    owner = {"SCORE_STATES": composite, "UNWIND_STATES": composite,
             "FLOW_STATES": flow, "STRATA": stratum}[module_constant]
    assert panel_manifest(_build())["vocabulary"][key] == list(
        getattr(owner, module_constant))


def test_the_quadrant_and_its_threshold_travel_together():
    """A consumer plotting the four cells needs both, and `CLOSE_SIGMA` is the one that
    would otherwise be hard-coded as 1.5 in a chart nobody re-reads."""
    from crowdmon.futures.report import CLOSE_SIGMA, QUADRANT

    got = panel_manifest(_build())
    assert got["close_sigma"] == CLOSE_SIGMA
    assert sorted(got["quadrant"]) == ["00", "01", "10", "11"]
    assert set(got["quadrant"].values()) == set(QUADRANT.values())


def test_the_schema_version_is_in_the_manifest_and_the_meta(tmp_path):
    publish_panel(_build(), tmp_path)
    base = tmp_path / "damage"
    assert json.loads((base / "manifest.json").read_text())[
        "schema_version"] == SCHEMA_VERSION
    assert json.loads((base / "2026-07-28" / "meta.json").read_text())[
        "schema_version"] == SCHEMA_VERSION


# ── the write is atomic and the manifest is last ────────────────────────────
def test_a_failed_write_leaves_no_partial_week(tmp_path, monkeypatch):
    """A half-written directory that a manifest already names is the failure mode rsync
    turns into a page rendering nonsense. The staging directory has to go."""
    monkeypatch.setattr(publish, "panel_manifest",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        publish_panel(_build(), tmp_path)
    leftovers = [p.name for p in (tmp_path / "damage").iterdir()
                 if p.name.startswith(".")]
    assert not leftovers, f"staging directories survived a failure: {leftovers}"


def test_the_manifest_lists_the_weeks_that_are_actually_there(tmp_path):
    publish_panel(_build(), tmp_path)
    later = _build()
    later = DamageBuild(panel=later.panel.assign(report_date=pd.Timestamp("2026-08-04")),
                        blocks={}, report_date=pd.Timestamp("2026-08-04"), provenance={})
    publish_panel(later, tmp_path)
    got = json.loads((tmp_path / "damage" / "manifest.json").read_text())
    assert got["available_report_dates"] == ["2026-07-28", "2026-08-04"]
    assert got["current_report_date"] == "2026-08-04"


def test_old_weeks_are_pruned(tmp_path):
    for day in ("2026-06-30", "2026-07-07", "2026-07-14"):
        b = _build()
        publish_panel(DamageBuild(panel=b.panel.assign(report_date=pd.Timestamp(day)),
                                  blocks={}, report_date=pd.Timestamp(day),
                                  provenance={}), tmp_path, keep_weeks=2)
    got = json.loads((tmp_path / "damage" / "manifest.json").read_text())
    assert got["available_report_dates"] == ["2026-07-07", "2026-07-14"]


# ── the short-panel refusal ─────────────────────────────────────────────────
def test_a_short_panel_is_refused_rather_than_published(tmp_path):
    """The publisher's own version of `--profile live`.

    `bin/live-tests.sh` records a run that read the store mid-write and reported 480/12
    against the usual 487/5. A test suite fails loudly in that case. A publisher would write
    a panel with a third of the markets missing and nothing downstream would say so, because
    a short panel is a perfectly well-formed panel.
    """
    publish_panel(_build([_row(f"{n:03d}") for n in range(10)]), tmp_path)
    with pytest.raises(PublishError, match="below the"):
        publish_panel(_build([_row("001"), _row("002")]), tmp_path)


def test_the_first_publish_has_nothing_to_compare_against(tmp_path):
    publish_panel(_build([_row("001")]), tmp_path)          # must not raise


# ── the store root ──────────────────────────────────────────────────────────
def test_an_unset_store_raises_rather_than_defaulting(monkeypatch):
    """Same discipline as COTDATA_STORE and CMRDATA_STORE. A store that defaults is one a
    scheduled job writes to the wrong place without ever failing."""
    monkeypatch.delenv("CROWDMON_STORE", raising=False)
    with pytest.raises(PublishError, match="CROWDMON_STORE"):
        store_root()


def test_an_explicit_root_beats_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("CROWDMON_STORE", "/nowhere")
    assert store_root(tmp_path) == tmp_path


# ── the blocks ──────────────────────────────────────────────────────────────
def test_blocks_are_json_serialisable_with_timestamps_and_nulls(tmp_path):
    """`damage_block` returns `pd.Timestamp` and `pd.NA`, neither of which `json` accepts.
    A publisher that raises here on one market has lost the whole week."""
    blocks = {"001": {"sell": {"block": {"report_date": WEEK, "damage_pct": None,
                                         "offside": {"distance_sigma": None}},
                               "band": "unscored", "markdown": "x"}}}
    publish_panel(_build(blocks=blocks), tmp_path)
    back = json.loads(
        (tmp_path / "damage" / "2026-07-28" / "blocks.json").read_text())
    assert back["001"]["sell"]["block"]["report_date"] == "2026-07-28"
    assert back["001"]["sell"]["block"]["damage_pct"] is None


def test_the_manifest_carries_a_wall_clock_build_time():
    """`built_at` answers a question `current_report_date` cannot.

    A panel can be current on the report week and months old on the clock, because COT is
    weekly and a schedule that quietly stopped produces no new week to notice. The consumer
    reads this with `.get()`, so its absence degrades **silently** to a provenance line with
    one fewer field, which is how it went missing in the first place: it lived only in a
    worktree, was never committed, and the merged publisher shipped without it.
    """
    prov = panel_manifest(_build())["provenance"]
    assert "built_at" in prov, "a manifest with no build time cannot report a dead schedule"
    stamp = pd.Timestamp(prov["built_at"])
    assert stamp.tzinfo is not None, "a naive timestamp is ambiguous across the sync hop"
