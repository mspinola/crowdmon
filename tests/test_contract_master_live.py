"""Contract master against a REAL store. Skips when there is not one.

The synthetic tests prove the logic; these prove it against the universe it will actually
meet, which is the only place the coverage numbers mean anything. CI has no store, so
everything here skips there and runs locally on the Mac replica.
"""
import pytest

pytestmark = pytest.mark.needs_vintage


@pytest.fixture(scope="module")
def live():
    cotdata = pytest.importorskip("cotdata")
    try:
        specs = cotdata.store.read_metadata()
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    if specs is None or specs.empty:
        pytest.skip("store has no contract_specs table")
    from crowdmon.futures import ContractMaster
    return ContractMaster.load()


def test_every_registry_symbol_but_the_uncovered_ones_joins(live):
    """Measured 2026-07-31: 47 of 49, the two failures being MSCI EAFE and Emerging
    Markets, which Norgate carries neither specs nor prices for. Both are `Role: heldout`
    in the deployed params.yaml, so coverage does not bind on anything traded.

    Asserted as a FLOOR rather than an equality: adding a market should not fail this.
    """
    cov = live.coverage()
    joinable = int(cov["joinable"].sum())
    assert joinable >= 47, f"coverage regressed to {joinable} of {len(cov)}"
    not_joinable = set(cov.loc[~cov["joinable"], "symbol"])
    assert not_joinable <= {"MFS", "MME"}, f"new uncovered symbols: {not_joinable - {'MFS', 'MME'}}"


def test_a_joinable_symbol_has_both_price_tiers(live):
    """Notional needs `unadj`. Volatility needs `propadj`, which cotdata DERIVES from
    `unadj` + `backadj`, so both stored tiers are the precondition for the one derived
    tier. A symbol with only one is not joinable for layer 2 even though it looks fine in a
    spec table."""
    cov = live.coverage()
    ok = cov[cov["joinable"]]
    assert ok["has_unadj_price"].all() and ok["has_backadj_price"].all()


def test_gold_resolves_to_a_sane_multiplier(live):
    """A spot check with a value anyone can verify: COMEX gold is 100 troy ounces, so the
    point value is 100 dollars per dollar of price."""
    gc = live.spec("088691")
    assert gc is not None and gc.symbol == "GC"
    assert gc.point_value == 100.0
    assert gc.currency == "USD"
    assert gc.contract_scale == 1.0 and gc.is_historical_code is False


def test_the_unmatched_share_of_a_real_panel_is_large_and_reported(live):
    """The number that justifies refusing to inner-join. On the real 2026 capture, 371 of
    418 market codes and about 87% of ROWS have no spec: Nodal Exchange power zones, minor
    grains, and everything else CFTC publishes that nobody here trades.

    An inner join would drop all of it in silence, and a 'cross-market' result computed
    afterwards would quietly describe the 13% that survived.
    """
    vi = pytest.importorskip("cotdata.vintage_ingest")
    obs = vi.read_observations()
    if obs.empty:
        pytest.skip("store has no vintage observations yet")

    annotated = live.annotate(obs)
    matched = annotated["symbol"].notna()
    assert matched.any(), "nothing matched at all, which means the join is broken"
    assert (~matched).sum() > matched.sum(), (
        "expected most of a real panel to be outside the registry universe")

    report = live.unmatched(obs)
    assert len(report) > 100
    assert int(report["rows"].sum()) == int((~matched).sum())   # the report is complete
    assert "market_name" in report.columns                      # and legible


def test_nothing_is_lost_by_annotating(live):
    """The property that makes the coverage report trustworthy: annotate adds columns and
    never removes rows unless explicitly told to."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    obs = vi.read_observations()
    if obs.empty:
        pytest.skip("store has no vintage observations yet")
    assert len(live.annotate(obs)) == len(obs)
    assert len(live.annotate(obs, drop_unmatched=True)) < len(obs)
