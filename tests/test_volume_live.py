"""Volume against a REAL store. Skips when there is not one.

The offline tests check the aggregation. These check the claim the aggregation rests on:
that `cotdata`'s `volume="front"` is WHOLE-MARKET volume across every expiry, and therefore
the right denominator for a `Q` that covers every expiry.

That claim is the whole reason `T` is computable, and it contradicts the parameter's own
name, so it is asserted here two independent ways rather than believed.
"""
import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.needs_vintage


@pytest.fixture(scope="module")
def cotdata_store():
    cotdata = pytest.importorskip("cotdata")
    try:
        if cotdata.get_prices("GC", adjustment="unadj").empty:
            pytest.skip("store has no GC prices")
    except Exception as exc:                                   # noqa: BLE001
        pytest.skip(f"no readable store: {exc}")
    return cotdata


def test_price_file_open_interest_matches_the_cftc_exactly(cotdata_store):
    """Proof 1 that the price files describe the whole market, not the front month.

    Norgate collects open interest from the exchange; the CFTC collects it from clearing
    members. Two vendors, two collection paths. If the price file carried front-month data
    its open interest would be a fraction of the CFTC's; instead they agree to the contract
    on almost every market, which they could only do if both are whole-market figures.
    """
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import ContractMaster, VintageCotSource

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel.dropna(subset=["symbol"])
    report_date = panel["report_date"].max()
    panel = panel[panel["report_date"] == report_date]
    # Open interest is a market-week quantity, identical across the category rows.
    cot = panel.groupby("symbol", as_index=False)["open_interest"].max()

    ratios = {}
    for _, row in cot.iterrows():
        px = cotdata_store.get_prices(row["symbol"], adjustment="unadj")
        if px.empty or "Open Interest" not in px:
            continue
        # Zero means "not published yet", not "no open interest". Same reason volume.py
        # treats a zero volume as missing.
        oi = pd.to_numeric(px["Open Interest"], errors="coerce").replace(0, np.nan).dropna()
        asof = oi.index[oi.index <= pd.Timestamp(report_date)]
        if len(asof) == 0 or not row["open_interest"]:
            continue
        ratios[row["symbol"]] = float(oi.loc[asof[-1]]) / float(row["open_interest"])

    assert len(ratios) >= 20, f"only {len(ratios)} markets compared; too few to conclude"
    s = pd.Series(ratios)
    exact = (s.round(4) == 1.0).sum()
    assert exact >= len(s) - 1, (
        f"only {exact} of {len(s)} markets match the CFTC exactly. If Norgate has changed "
        f"what its continuous file reports, the whole-market claim in volume.py needs "
        f"re-measuring before T means anything. Worst: {s.sub(1).abs().idxmax()} "
        f"{s[s.sub(1).abs().idxmax()]:.4f}")
    assert s.median() == pytest.approx(1.0, abs=1e-4)


def test_curve_concentration_orders_as_contract_structure_predicts(cotdata_store):
    """Proof 2, and the one that rules out the alternative explanation.

    If `Volume` were front-month-only it could not exceed `FirstVolume`, let alone
    `FirstVolume + SecondVolume`. Measured, the first two contracts' share of `Volume` runs
    from 1.00 for quarterly financials down to ~0.52 for natural gas, which is exactly how
    much of each market's activity actually sits in its first two expiries. A front-month
    series would show 1.00 everywhere.
    """
    import os
    import pathlib
    root = pathlib.Path(os.environ["COTDATA_STORE"]) / "prices"

    shares = {}
    for sym in ("ZN", "ES", "GC", "SI", "ZC", "ZS", "CL", "NG"):
        p = root / f"{sym}_unadj.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if not {"FirstVolume", "SecondVolume", "Volume"} <= set(df.columns):
            pytest.skip("store predates the individual-contract volume columns")
        d = df.dropna(subset=["FirstVolume", "SecondVolume"]).tail(500)
        d = d[d["Volume"] > 0]
        if len(d) < 100:
            continue
        shares[sym] = float(((d["FirstVolume"] + d["SecondVolume"]) / d["Volume"]).mean())

    assert {"CL", "NG", "ZN"} <= set(shares), "need the extremes to make the comparison"
    # Deep-curve energy: the first two expiries are barely half the market.
    assert shares["CL"] < 0.65 and shares["NG"] < 0.65
    # Quarterly financials: essentially everything is in the front contract.
    assert shares["ZN"] > 0.95
    # And the ordering itself, which is the part a coincidence could not produce.
    assert shares["NG"] < shares["ZC"] < shares["GC"] < shares["ZN"]


def test_volume_covers_every_symbol_in_the_store(cotdata_store):
    """Coverage is not the constraint here. Every symbol has volume, over essentially its
    whole price history, back to the late 1970s for most."""
    import json
    import os
    import pathlib
    man = json.loads((pathlib.Path(os.environ["COTDATA_STORE"]) / "manifests"
                      / "prices.json").read_text())
    syms = sorted({k.rsplit("_", 1)[0] for k in man.get("prices", man)})

    covers = {}
    for sym in syms:
        try:
            df = cotdata_store.get_prices(sym, adjustment="unadj")
        except Exception:                                      # noqa: BLE001
            continue
        if df.empty or "Volume" not in df:
            continue
        v = pd.to_numeric(df["Volume"], errors="coerce").replace(0, np.nan).dropna()
        covers[sym] = len(v) / len(df)

    assert len(covers) >= 40
    assert min(covers.values()) > 0.90, f"worst coverage: {min(covers, key=covers.get)}"
    assert pd.Series(covers).median() > 0.99


def test_the_subset_series_really_is_smaller_in_the_deep_curve_markets(cotdata_store):
    """The concrete cost of reaching for `reconstructed` because it sounds more complete."""
    for sym in ("CL", "NG"):
        whole = pd.to_numeric(
            cotdata_store.get_prices(sym, adjustment="unadj", volume="front")["Volume"],
            errors="coerce").replace(0, np.nan).dropna().tail(500)
        subset = pd.to_numeric(
            cotdata_store.get_prices(sym, adjustment="unadj",
                                     volume="reconstructed")["Volume"],
            errors="coerce").replace(0, np.nan).dropna().tail(500)
        ratio = subset.mean() / whole.mean()
        assert ratio < 0.70, (
            f"{sym}: the subset series is {ratio:.2f} of whole-market volume. If this has "
            f"converged, re-measure before relaxing volume.py's guard.")


def test_days_to_liquidate_on_the_real_panel_is_plausible_and_reorders_the_proxy(cotdata_store):
    """End to end, and the justification for the join existing at all.

    If `T` ranked markets the same way `Q/OI` does, the volume would be decoration. It does
    not: the rank correlation is well below 1, because open interest is a stock and volume
    is a flow, and the ratio between them differs by market.
    """
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import (
        ContractMaster,
        VintageCotSource,
        add_volume,
        fragility_frame,
        rank_markets,
        volume_coverage,
    )

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel[panel["report_date"] == panel["report_date"].max()]
    frag = fragility_frame(panel).merge(
        panel[["market_code", "symbol"]].drop_duplicates(), on="market_code", how="left")
    frag = add_volume(frag)

    cov = volume_coverage(frag)
    assert cov["total"] == len(frag)                        # nothing dropped
    assert cov["with_volume"] >= 20
    assert cov["no_volume_within_tolerance"] == 0, (
        "every symbol that maps to a contract should have same-week volume")

    ranked = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"])
    live = ranked.dropna(subset=["dtl_sell"])

    # A forced side that needs months to leave, or minutes, means the denominator is wrong.
    assert live["dtl_sell"].between(0.05, 60).all(), (
        f"implausible days-to-liquidate: {live['dtl_sell'].min():.2f} to "
        f"{live['dtl_sell'].max():.2f}")
    assert live["dtl_sell_stress"].notna().all()

    corr = live["q_sell_over_oi"].rank(ascending=False).corr(
        live["dtl_sell"].rank(ascending=False))
    assert corr < 0.95, (
        f"T and the Q/OI proxy rank markets almost identically (corr={corr:.3f}), which "
        f"would make the volume join redundant. It measured 0.585 when written.")


def test_stress_volume_is_not_reliably_the_conservative_one(cotdata_store):
    """Recorded because it is counterintuitive and shapes how the output must be read. A
    stress-conditioned denominator sounds strictly more cautious; in some markets panic
    brings volume, so `T_stress` is SHORTER. Both figures are reported and neither is
    labelled "the" answer for exactly this reason."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import ContractMaster, VintageCotSource, add_volume, fragility_frame

    panel = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    panel = panel[panel["report_date"] == panel["report_date"].max()]
    frag = add_volume(fragility_frame(panel).merge(
        panel[["market_code", "symbol"]].drop_duplicates(), on="market_code", how="left"))
    live = frag.dropna(subset=["adv", "adv_stress"])

    ratio = live["adv_stress"] / live["adv"]
    assert (ratio > 1).any(), "no market trades more under stress; re-measure the docs"
    assert (ratio < 1).any(), "no market thins under stress; that would be surprising"
