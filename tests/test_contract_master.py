"""Contract master: the code-to-instrument join, its scale factor, and its coverage report.

Offline. `cotdata.store.read_metadata` and `load_manifest` are patched so the join is
exercised against a known universe rather than whatever the machine's store happens to
hold; the real-store numbers are asserted separately in `test_contract_master_live.py`.
"""
import pandas as pd
import pytest


@pytest.fixture()
def master(monkeypatch, tmp_path):
    """A contract master over two symbols, one of which has a scaled historical code."""
    monkeypatch.setenv("COTDATA_STORE", str(tmp_path))
    from cotdata import store
    from cotdata.registry import Symbol

    specs = pd.DataFrame([
        {"Symbol": "GC", "Norgate_Symbol": "&GC", "Name": "Gold", "Exchange": "COMEX",
         "Group": "Metals", "Contract Size": 100.0, "Tick Size": 0.1, "Tick Value": 10.0,
         "Point Value": 100.0, "Currency": "USD", "Margin": 12000.0},
        {"Symbol": "LBR", "Norgate_Symbol": "&LBR", "Name": "Lumber", "Exchange": "CME",
         "Group": "Softs", "Contract Size": 27500.0, "Tick Size": 0.5, "Tick Value": 55.0,
         "Point Value": 110.0, "Currency": "USD", "Margin": 3300.0},
        # a spec with no price series, to prove coverage reports it rather than hiding it
        {"Symbol": "MME", "Norgate_Symbol": "&MME", "Name": "MSCI EM", "Exchange": "ICE",
         "Group": "Equities", "Contract Size": 50.0, "Tick Size": 0.05, "Tick Value": 2.5,
         "Point Value": 50.0, "Currency": "USD", "Margin": 5000.0},
    ])
    syms = [
        Symbol(internal="GC", norgate="&GC", asset_class="Metals", is_equity=False,
               report_type="disagg", cftc_code="088691", yahoo=None, databento=None,
               price_source=None, hist_codes=()),
        # lumber's contract was redefined: the old code counts a QUARTER-size contract
        Symbol(internal="LBR", norgate="&LBR", asset_class="Softs", is_equity=False,
               report_type="disagg", cftc_code="058644", yahoo=None, databento=None,
               price_source=None, hist_codes=(("058643", 4.0),)),
        Symbol(internal="MME", norgate="&MME", asset_class="Equities", is_equity=True,
               report_type="tff", cftc_code="244042", yahoo=None, databento=None,
               price_source=None, hist_codes=()),
    ]
    manifest = {"prices": {"GC_unadj": {}, "GC_backadj": {},
                           "LBR_unadj": {}, "LBR_backadj": {}}}

    monkeypatch.setattr(store, "read_metadata", lambda: specs)
    import cotdata
    monkeypatch.setattr(cotdata, "all_symbols", lambda: syms)
    monkeypatch.setattr(cotdata, "load_manifest", lambda: manifest)

    from crowdmon.futures import ContractMaster
    return ContractMaster.load()


def _cot(market_code, *, long_c=1000, oi=5000):
    return pd.DataFrame([{
        "report_date": pd.Timestamp("2026-07-21"), "market_code": market_code,
        "report_type": "disaggregated", "combined": False, "category": "managed_money",
        "market_name": "SOMETHING", "long_contracts": long_c, "short_contracts": 200,
        "spread_contracts": 50, "open_interest": oi,
        "trader_count_long": 40, "cr4_net_long": 20.5,
    }])


def test_a_historical_market_code_resolves_to_the_same_instrument(master):
    assert master.spec("058644").symbol == "LBR"
    assert master.spec("058643").symbol == "LBR"
    assert master.spec("058644").is_historical_code is False
    assert master.spec("058643").is_historical_code is True


def test_the_contract_size_scale_is_applied_by_default(master):
    """Lumber's contract was redefined, so an old row counts quarter-size contracts.
    Multiplying those by today's point value without the scale is wrong by 4x, and
    nothing about the result looks wrong. cotdata.get_cot applies this when it stitches
    history; the VINTAGE path does not, so this layer has to."""
    scaled = master.annotate(_cot("058643", long_c=1000, oi=5000))
    assert scaled["long_contracts"].iloc[0] == 4000      # 1000 quarter-size contracts
    assert scaled["open_interest"].iloc[0] == 20000
    assert scaled["contract_scale"].iloc[0] == 4.0
    assert bool(scaled["contract_scale_applied"].iloc[0]) is True

    raw = master.annotate(_cot("058643", long_c=1000), apply_scale=False)
    assert raw["long_contracts"].iloc[0] == 1000
    assert bool(raw["contract_scale_applied"].iloc[0]) is False


def test_the_current_code_is_never_scaled(master):
    got = master.annotate(_cot("058644", long_c=1000))
    assert got["long_contracts"].iloc[0] == 1000
    assert got["contract_scale"].iloc[0] == 1.0


def test_only_genuine_contract_counts_are_scaled(master):
    """A ratio is unitless and a trader count is people. Scaling either would be a
    category error that quietly corrupts concentration and breadth metrics."""
    got = master.annotate(_cot("058643"))
    assert got["cr4_net_long"].iloc[0] == 20.5     # unchanged
    assert got["trader_count_long"].iloc[0] == 40  # unchanged
    assert got["spread_contracts"].iloc[0] == 200  # 50 * 4, a real count


def test_unmatched_market_codes_are_kept_and_reported_not_silently_dropped(master):
    """The vintage store holds every market CFTC publishes (418 codes in 2026) while the
    registry names 49. An inner join would discard ~370 in silence and a 'cross-market'
    result would then describe whatever survived."""
    frame = pd.concat([_cot("088691"), _cot("999999"), _cot("999999")], ignore_index=True)
    got = master.annotate(frame)

    assert len(got) == 3                             # nothing dropped
    assert got["symbol"].isna().sum() == 2           # but clearly marked
    rep = master.unmatched(frame)
    assert list(rep["market_code"]) == ["999999"]
    assert int(rep["rows"].iloc[0]) == 2

    explicit = master.annotate(frame, drop_unmatched=True)
    assert len(explicit) == 1                        # only when asked


def test_coverage_names_what_each_symbol_is_missing(master):
    cov = master.coverage()
    assert set(cov["symbol"]) == {"GC", "LBR", "MME"}
    by = cov.set_index("symbol")
    assert bool(by.loc["GC", "joinable"]) is True
    assert bool(by.loc["MME", "joinable"]) is False
    assert by.loc["MME", "missing"] == "unadj_price,backadj_price"
    assert int(by.loc["LBR", "n_market_codes"]) == 2   # primary plus the historical one
    assert "2 of 3" in master.coverage_summary()
    assert "MME" in master.coverage_summary()


def test_both_price_tiers_are_required_to_be_joinable(monkeypatch, master):
    """Layer 2 needs BOTH: notional from unadj, because back-adjusted prices are not
    tradeable levels, and volatility from backadj, because only that has correct returns."""
    cov = master.coverage().set_index("symbol")
    assert bool(cov.loc["GC", "has_unadj_price"]) and bool(cov.loc["GC", "has_backadj_price"])


def test_a_non_usd_contract_raises_rather_than_mislabelling_units(monkeypatch, tmp_path):
    """All 47 specs are USD today, which removes an FX layer. That is a fact about the
    current universe, not a property of futures."""
    monkeypatch.setenv("COTDATA_STORE", str(tmp_path))
    import cotdata
    from cotdata import store
    from cotdata.registry import Symbol
    specs = pd.DataFrame([
        {"Symbol": "FX", "Norgate_Symbol": "&FX", "Name": "Euro thing", "Exchange": "EUREX",
         "Group": "Rates", "Contract Size": 1.0, "Tick Size": 0.01, "Tick Value": 10.0,
         "Point Value": 1000.0, "Currency": "EUR", "Margin": 2000.0}])
    monkeypatch.setattr(store, "read_metadata", lambda: specs)
    monkeypatch.setattr(cotdata, "all_symbols", lambda: [
        Symbol(internal="FX", norgate="&FX", asset_class="Rates", is_equity=False,
               report_type="tff", cftc_code="111111", yahoo=None, databento=None,
               price_source=None, hist_codes=())])
    monkeypatch.setattr(cotdata, "load_manifest", lambda: {"prices": {}})

    from crowdmon.futures import ContractMaster, ContractMasterError
    with pytest.raises(ContractMasterError, match="non-USD"):
        ContractMaster.load()
    assert len(ContractMaster.load(require_usd=False)) == 1


def test_a_market_code_claimed_by_two_symbols_raises(monkeypatch, tmp_path):
    """A code identifies one instrument at a time. Letting first-or-last-wins decide would
    silently attach one instrument's multiplier to another's positions."""
    monkeypatch.setenv("COTDATA_STORE", str(tmp_path))
    import cotdata
    from cotdata import store
    from cotdata.registry import Symbol
    specs = pd.DataFrame([
        {"Symbol": s, "Norgate_Symbol": f"&{s}", "Name": s, "Exchange": "CME",
         "Group": "G", "Contract Size": 1.0, "Tick Size": 0.1, "Tick Value": 1.0,
         "Point Value": 10.0, "Currency": "USD", "Margin": 100.0} for s in ("AA", "BB")])
    monkeypatch.setattr(store, "read_metadata", lambda: specs)
    monkeypatch.setattr(cotdata, "all_symbols", lambda: [
        Symbol(internal="AA", norgate="&AA", asset_class="X", is_equity=False,
               report_type="disagg", cftc_code="123456", yahoo=None, databento=None,
               price_source=None, hist_codes=()),
        Symbol(internal="BB", norgate="&BB", asset_class="X", is_equity=False,
               report_type="disagg", cftc_code="654321", yahoo=None, databento=None,
               price_source=None, hist_codes=("123456",))])
    monkeypatch.setattr(cotdata, "load_manifest", lambda: {"prices": {}})

    from crowdmon.futures import ContractMaster, ContractMasterError
    with pytest.raises(ContractMasterError, match="maps to both"):
        ContractMaster.load()


def test_an_empty_frame_still_gains_the_spec_columns(master):
    from crowdmon.futures import SPEC_COLUMNS
    got = master.annotate(pd.DataFrame())
    assert all(c in got.columns for c in SPEC_COLUMNS)


def test_a_missing_contract_specs_table_says_where_it_comes_from(monkeypatch, tmp_path):
    monkeypatch.setenv("COTDATA_STORE", str(tmp_path))
    from cotdata import store
    monkeypatch.setattr(store, "read_metadata", lambda: pd.DataFrame())
    from crowdmon.futures import ContractMaster, ContractMasterError
    with pytest.raises(ContractMasterError, match="Norgate producer"):
        ContractMaster.load()
