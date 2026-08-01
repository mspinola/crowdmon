"""The CotSource seam: lookahead refusal, provenance filtering, validation on load."""
import datetime as dt

import pandas as pd
import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("COTDATA_STORE", str(tmp_path))
    return tmp_path


def _canon(report_date, *, long_mm=400, market="088691"):
    """One market-week of Disaggregated rows, balanced by construction."""
    cats = {
        "producer_merchant": (100, 400, None),
        "swap": (200, 150, 30),
        "managed_money": (long_mm, 100, 50),
        "other_reportable": (150, 200, 20),
        "nonreportable": (50, 50, None),
    }
    long_total = sum(v[0] for v in cats.values()) + sum(v[2] or 0 for v in cats.values())
    # keep the identity exact: park the difference on producer_merchant's short leg
    short_base = sum(v[1] for v in cats.values()) + sum(v[2] or 0 for v in cats.values())
    cats["producer_merchant"] = (100, 400 + (long_total - short_base), None)
    rows = []
    for cat, (lo, sh, sp) in cats.items():
        rows.append({
            "report_date": pd.Timestamp(report_date), "market_code": market,
            "report_type": "disaggregated", "combined": False, "category": cat,
            "market_name": "GOLD", "long_contracts": lo, "short_contracts": sh,
            "spread_contracts": sp if sp is not None else pd.NA,
            "trader_count_long": pd.NA, "trader_count_short": pd.NA,
            "open_interest": long_total,
            "cr4_net_long": pd.NA, "cr4_net_short": pd.NA,
            "cr8_net_long": pd.NA, "cr8_net_short": pd.NA,
        })
    return pd.DataFrame(rows)


def _ingest(canonical, *, snapshot_id, observed_at, release_date, source):
    from cotdata import vintage_ingest as vi
    vi.ingest_canonical(canonical, snapshot_id=snapshot_id, observed_at=observed_at)
    # stamp the release date the way `cotdata-schedule backfill` would
    for part in (vi._obs_dir()).glob("report_year=*/observations.parquet"):
        df = pd.read_parquet(part)
        m = df["release_date"].isna()
        df.loc[m, "release_date"] = pd.Timestamp(release_date)
        df.loc[m, "release_date_source"] = source
        df.to_parquet(part)


def test_indexes_on_release_date_and_refuses_lookahead(store):
    """The Tuesday as-of date embeds a three-day lookahead, and three days is exactly the
    window in which the largest moves happen."""
    from crowdmon.futures import VintageCotSource
    _ingest(_canon("2026-07-21"), snapshot_id="s1",
            observed_at="2026-07-24T19:00:00Z", release_date="2026-07-24",
            source="published")
    src = VintageCotSource()

    assert src.available_releases() == [dt.date(2026, 7, 24)]
    assert len(src.load("2026-07-24")) == 5      # available the day it was published
    assert src.load("2026-07-23").empty          # and not one day before


def test_a_weaker_release_date_source_can_be_excluded(store):
    """`derived` is a guess that fails on exactly the weeks that matter, so anything doing
    strict point-in-time evaluation has to be able to drop it."""
    from crowdmon.futures import VintageCotSource
    _ingest(_canon("2026-07-21"), snapshot_id="s1",
            observed_at="2026-07-24T19:00:00Z", release_date="2026-07-24",
            source="derived")

    assert len(VintageCotSource().load("2026-07-24")) == 5
    strict = VintageCotSource(min_source="scheduled")
    assert strict.load("2026-07-24").empty
    assert strict.available_releases() == []


def test_pit_complete_distinguishes_as_published_from_a_later_stand_in(store):
    """Vintages accumulate forward only, so a week predating first capture is served by a
    current-state value with revisions already applied. Callers must be able to tell."""
    from crowdmon.futures import VintageCotSource
    # captured a year after the fact, as a historical backfill would be
    _ingest(_canon("2025-07-15"), snapshot_id="s1",
            observed_at="2026-07-31T19:00:00Z", release_date="2025-07-18",
            source="scheduled")
    got = VintageCotSource().load("2025-07-18")
    assert len(got) == 5
    assert not got["pit_complete"].any()   # published then, but not captured until 2026


def test_the_zero_sum_identity_is_checked_on_every_load(store):
    """A category mapping that silently broke would otherwise surface as a strange result
    months later."""
    from crowdmon.futures import CotAdapterError, VintageCotSource
    broken = _canon("2026-07-21")
    broken.loc[broken["category"] == "managed_money", "long_contracts"] = 999999
    _ingest(broken, snapshot_id="s1", observed_at="2026-07-24T19:00:00Z",
            release_date="2026-07-24", source="published")

    with pytest.raises(CotAdapterError, match="zero-sum"):
        VintageCotSource().load("2026-07-24")
    assert len(VintageCotSource(validate=False).load("2026-07-24")) == 5


def test_an_empty_store_answers_rather_than_raising(store):
    """First run, before any capture. Returning nothing is the honest answer."""
    from crowdmon.futures import VintageCotSource
    src = VintageCotSource()
    assert src.available_releases() == []
    assert src.load("2026-07-24").empty


def test_an_unknown_provenance_tier_is_refused_at_construction(store):
    from crowdmon.futures import CotAdapterError, VintageCotSource
    with pytest.raises(CotAdapterError, match="unknown release-date source"):
        VintageCotSource(min_source="probably_fine")


def test_provenance_summary_orders_worst_last(store):
    from crowdmon.futures import provenance_summary
    frame = pd.DataFrame({"release_date_source": ["derived", "published", "derived",
                                                  "scheduled"]})
    assert list(provenance_summary(frame).index) == ["published", "scheduled", "derived"]


def test_the_adapter_satisfies_the_declared_protocol(store):
    from crowdmon.futures import CotSource, VintageCotSource
    assert isinstance(VintageCotSource(), CotSource)
