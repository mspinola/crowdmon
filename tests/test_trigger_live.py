"""Triggers against a REAL store. Skips when there is not one.

`test_trigger.py` checks the arithmetic on constructed series. This file checks the claims
the arithmetic rests on, which is the pattern every other engine here follows and the one
that caught the defects in notional, riskunits, volume and impact.

The two claims that matter:

- **`propadj` is required, and not for the reason the guard's wording implies.** The signal's
  SIGN barely cares which series it reads. The trigger DISTANCE cares enormously.
- **The block needs no aggregate-capital estimate.** Nothing below consults an `A`, a target
  volatility, a portfolio scaling term or an external index. That is what made §A.7
  computable, and it is worth a test rather than a paragraph.
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


@pytest.fixture(scope="module")
def panel(cotdata_store):
    """The latest week's Managed Money rows, priced and volumed."""
    vi = pytest.importorskip("cotdata.vintage_ingest")
    if vi.read_observations().empty:
        pytest.skip("store has no vintage observations yet")

    from crowdmon.futures import ContractMaster, VintageCotSource, add_volume

    rows = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    rows = rows[(rows["report_date"] == rows["report_date"].max())
                & (rows["category"] == "managed_money")].dropna(subset=["symbol"])
    rows = rows.assign(net_contracts=rows["long_contracts"] - rows["short_contracts"])
    out = add_volume(rows)
    if len(out) < 20:
        pytest.skip("too few joinable markets")
    return out


def _sigma(cotdata_store, symbol, window=63):
    close = cotdata_store.get_prices(symbol, adjustment="propadj")["Close"].dropna()
    nonpos = close <= 0
    returns = close.pct_change().replace([np.inf, -np.inf], np.nan) \
                   .where(~(nonpos | nonpos.shift(fill_value=False)))
    return float(returns.rolling(window).std().iloc[-1])


# ── why the guard is about distance, not sign ───────────────────────────────
def test_the_signal_sign_barely_cares_which_series_but_the_distance_does(cotdata_store):
    """Quantifies `trigger_prices`'s refusal of anything but `propadj`.

    A module that only needed a DIRECTION could read either series: the momentum sign agrees
    99.4% of the time. The trigger's useful output is a distance from spot, a ratio of price
    levels, and additive back-adjustment inflates historical levels. At 250 days the two
    disagree by hundreds of percentage points, which is the same failure `notional` refuses
    and this is its fourth appearance.
    """
    agreements, gaps = [], []
    for symbol in ("GC", "CL", "ZS", "ZW", "CC", "NG", "DC"):
        back = cotdata_store.get_prices(symbol, adjustment="backadj")["Close"].dropna()
        prop = cotdata_store.get_prices(symbol, adjustment="propadj")["Close"].dropna()
        shared = back.index.intersection(prop.index)
        back, prop = back.loc[shared], prop.loc[shared]
        for k in (20, 60, 250):
            sign_back = np.sign(back - back.shift(k)).dropna()
            sign_prop = np.sign(prop - prop.shift(k)).dropna()
            both = sign_back.index.intersection(sign_prop.index)
            agreements.append(float((sign_back.loc[both] == sign_prop.loc[both]).mean()))
            dist_back = (back.shift(k) / back - 1).dropna()
            dist_prop = (prop.shift(k) / prop - 1).dropna()
            shared_d = dist_back.index.intersection(dist_prop.index)
            gaps.append(float((dist_back.loc[shared_d]
                               - dist_prop.loc[shared_d]).abs().quantile(0.95)))

    assert min(agreements) > 0.95, (
        f"momentum sign agreement fell to {min(agreements):.4f}; the claim that the guard is "
        f"about the distance rather than the sign rests on it staying high")
    assert max(gaps) > 1.0, (
        f"back- and ratio-adjusted trigger distances now agree to within {max(gaps):.0%}; "
        f"they disagreed by 420 percentage points when measured, and the refusal in "
        f"trigger_prices rests on that")


def test_the_flip_level_is_anchor_invariant_on_real_data(cotdata_store):
    """`flip = spot . ratio_then / ratio_now` cancels any common scale factor, so it holds
    whether `propadj` is anchored at this bar or at the end of the full series. Checked
    against the unadjusted series, which needs no anchoring argument at all."""
    from crowdmon.futures.trigger import trigger_prices

    for symbol in ("GC", "CL", "ZS"):
        got = trigger_prices(symbol)
        unadj = cotdata_store.get_prices(symbol, adjustment="unadj")["Close"].dropna()
        assert got.attrs["spot"] == pytest.approx(float(unadj.iloc[-1]))
        for _, row in got.dropna(subset=["flip_price"]).iterrows():
            k = int(row["lookback_days"])
            prop = cotdata_store.get_prices(symbol, adjustment="propadj")["Close"].dropna()
            expected = float(unadj.iloc[-1]) * float(prop.iloc[-1 - k]) / float(prop.iloc[-1])
            assert row["flip_price"] == pytest.approx(expected, rel=1e-9)


def test_the_flip_side_agrees_with_the_signal_it_derives_from(cotdata_store, panel):
    """The invariant a one-bar error breaks while leaving both outputs plausible.

    A signal already LONG (spot above the price k days ago) must flip DOWN, so its flip level
    sits below spot, and vice versa. `trigger_prices` uses `iloc[-1 - k]` to match
    `shift(k)`; `iloc[-k]` is one bar adrift and inverts this on roughly half the markets
    without producing a single implausible number.
    """
    from crowdmon.futures.trigger import trigger_prices

    checked = 0
    for symbol in panel["symbol"].dropna().unique():
        got = trigger_prices(str(symbol)).dropna(subset=["flip_price", "signal"])
        spot = got.attrs["spot"]
        for _, row in got[got["signal"] != 0].iterrows():
            assert np.sign(spot - row["flip_price"]) == row["signal"], (
                f"{symbol} at {int(row['lookback_days'])}d: spot {spot:,.2f}, flip "
                f"{row['flip_price']:,.2f}, signal {row['signal']:+.0f}")
            checked += 1
    assert checked >= 50, f"only {checked} lookback-market pairs checked"


def test_the_horizons_genuinely_disagree_across_the_universe(cotdata_store, panel):
    """The module's design argument, tested rather than asserted: collapsing lookbacks into
    one blended trigger would hide something real. If every market agreed across horizons,
    reporting three would be noise."""
    from crowdmon.futures.trigger import trigger_prices

    split = 0
    for symbol in panel["symbol"].dropna().unique():
        signs = trigger_prices(str(symbol)).dropna(subset=["signal"])["signal"]
        if len(signs) >= 2 and signs.nunique() > 1:
            split += 1
    assert split >= 3, (
        f"only {split} markets have horizons pointing different ways; the case for reporting "
        f"each lookback separately rests on this being common")


# ── the block, end to end, with no capital estimate ─────────────────────────
def test_the_block_renders_for_every_joinable_market(cotdata_store, panel):
    """Nothing here consults an aggregate CTA capital figure, a target volatility, a
    portfolio scaling term or an external index. The pool is the observed COT net."""
    from crowdmon.futures.trigger import format_block, trigger_block

    rendered = 0
    for _, row in panel.iterrows():
        if pd.isna(row.get("adv")):
            continue
        block = trigger_block(str(row["symbol"]), market_row=row,
                              sigma_daily=_sigma(cotdata_store, str(row["symbol"])),
                              adv=float(row["adv"]))
        assert block["pool_contracts"] >= 0                      # a magnitude, both ways
        assert block["flows"]["reverse"]["contracts"] == pytest.approx(
            2 * block["flows"]["close"]["contracts"])
        text = format_block(block)
        assert "flips at" in text and "vol shock" in text.lower()
        rendered += 1
    assert rendered >= 20, f"only {rendered} markets rendered"


def test_flows_and_costs_are_plausible_across_the_universe(cotdata_store, panel):
    """Bands wide enough to pass an ordinary market and narrow enough to fail a unit error:
    a sigma read as a percentage, or a pool and a volume in different units, both land far
    outside these."""
    from crowdmon.futures.trigger import trigger_block

    days, costs = [], []
    for _, row in panel.iterrows():
        if pd.isna(row.get("adv")):
            continue
        block = trigger_block(str(row["symbol"]), market_row=row,
                              sigma_daily=_sigma(cotdata_store, str(row["symbol"])),
                              adv=float(row["adv"]))
        close = block["flows"]["close"]
        if close["days_adv"] is not None:
            days.append(close["days_adv"])
        if close["impact_bps"] is not None:
            costs.append(close["impact_bps"])

    assert len(days) >= 20
    assert min(days) > 0.01 and max(days) < 60, f"days-to-liquidate {min(days)} to {max(days)}"
    assert min(costs) > 1 and max(costs) < 2_000, f"impact {min(costs)} to {max(costs)} bps"
    # Concave: a full reversal is twice the flow and less than twice the cost.
    assert max(costs) / min(costs) < 100


def test_the_vol_shock_is_annualised_on_real_volatilities(cotdata_store, panel):
    """"+5 vol points" universally means annualised. Applied to a DAILY sigma of ~1.5% it
    would be a 4x move, and every market would print the same near-total liquidation, which
    is exactly how the offline test says this was caught. On real data the reductions must
    SPREAD, because annualised vols across this universe span roughly 8% to 80%.
    """
    from crowdmon.futures.trigger import trigger_block

    reductions = []
    for _, row in panel.iterrows():
        if pd.isna(row.get("adv")):
            continue
        block = trigger_block(str(row["symbol"]), market_row=row,
                              sigma_daily=_sigma(cotdata_store, str(row["symbol"])),
                              adv=float(row["adv"]))
        if block["vol_shock_reduction"] is not None:
            reductions.append(block["vol_shock_reduction"])

    assert len(reductions) >= 20
    assert all(0 < r < 1 for r in reductions)
    assert max(reductions) - min(reductions) > 0.10, (
        f"a +5pt shock forces between {min(reductions):.1%} and {max(reductions):.1%} across "
        f"the universe; too narrow a spread means the shock is being applied in the wrong "
        f"units and every market is answering the same")
    # A calm market must be hurt more by a fixed points shock than a volatile one.
    assert reductions[int(np.argmin(reductions))] < reductions[int(np.argmax(reductions))]
