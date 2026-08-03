"""Reproducer for every figure in 2026-07-28-tff-financial-futures.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_tff.py

Deterministic: no sampling, no seeds, no fitting. Pinned to report week 2026-07-28.

Separate from `reproduce.py` because it covers a different report. TFF and Disaggregated are
different populations with different categories and different fragility weights, and a
single script over both would invite exactly the cross-report comparison this analysis
argues is invalid.

The asset-class taxonomy below lives here rather than in `src/` on purpose. It is a reading
of CFTC market names for one week's analysis, not a contract the package should offer:
`crowdmon.futures` knows about categories and market codes, and teaching it "crypto" would
be a claim about a taxonomy nobody has agreed.
"""
import re

import pandas as pd

from crowdmon.core import config as cfg
from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    contributions,
    decompose,
    decompose_breadth,
    from_vintage,
    latest,
    market_fragility,
    oi_identity,
    oi_identity_summary,
    rank_markets,
)

#: The three "Consolidated" equity index markets. Each is an AGGREGATE of its own
#: components, exactly (see §2), so including them alongside those components counts the
#: same open interest twice.
CONSOLIDATED = {"13874+", "20974+", "12460+"}

#: Consolidated market -> (full-size component, micro component). The micro contracts are
#: one tenth the size, which is the divisor the aggregation uses.
CONSOLIDATED_PARTS = {
    "13874+": ("13874A", "13874U", "S&P 500"),
    "20974+": ("209742", "209747", "NASDAQ-100"),
    "12460+": ("124603", "124608", "DJIA"),
}

#: The US rates complex: the nine contracts the cash-futures basis trade runs through.
RATES_COMPLEX = ["134741", "044601", "043602", "042601", "045601",
                 "043607", "020604", "020601", "134742"]


def asset_class(name: str) -> str:
    """Bucket a CFTC market name. Order matters: crypto is tested first because several
    crypto contracts are listed on CME alongside the rates and FX complex."""
    n = name.upper()
    if "COINBASE" in n or re.search(
            r"BITCOIN|ETHER|SOLANA|\bSOL\b|XRP|DOGE|CARDONA|POLKADOT|CHAINLINK|AVALANCHE"
            r"|STELLAR|LITECOIN|SHIB|HEDERA|NEAR |ONDO|ZCASH|SUI|PAX GOLD|CRYPTO", n):
        return "crypto"
    if re.search(r"SOFR|UST |FED FUNDS|ULTRA|ERIS|SHORT TERM RATE|CREDIT FUTURES", n):
        return "rates/credit"
    if re.search(r"EURO FX|YEN|DOLLAR|POUND|PESO|REAL|FRANC|RAND|USD INDEX|XRATE", n):
        return "fx"
    if re.search(r"BBG COMMODITY", n):
        return "commodity index"
    return "equity index"


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 40)

    panel = from_vintage(report_type="tff")
    last = panel[panel["report_date"] == panel["report_date"].max()]
    week = last["report_date"].iloc[0].date()

    rule(f"1. THE UNIVERSE — TFF, report week {week}")
    print(f"panel: {len(panel):,} rows, {panel['market_code'].nunique()} markets, "
          f"{panel['report_date'].min().date()} to {panel['report_date'].max().date()}")
    print(f"latest week: {last['market_code'].nunique()} markets")
    venue = last.drop_duplicates("market_code")["market_name"].str.split(" - ").str[-1]
    print("\nvenues:")
    print(venue.value_counts().to_string())

    rule("2. TRAP ONE — the Consolidated markets are aggregates, not markets")
    oi = last.drop_duplicates("market_code").set_index("market_code")["open_interest"]
    for cons, (big, micro, name) in CONSOLIDATED_PARTS.items():
        calc = oi[big] + oi[micro] / 10
        flag = "EXACT" if abs(calc - oi[cons]) < 1 else "NO"
        print(f"  {name:<11} {oi[cons]:>10,.0f}  vs  {oi[big]:,.0f} + {oi[micro]:,.0f}/10 "
              f"= {calc:>12,.1f}   {flag}")
    print("\n  So a cross-market ranking including both double-counts the index.")

    rule("3. TRAP TWO — the OI identity is exact EXCEPT in those same three")
    print(to_markdown(oi_identity_summary(panel).reset_index(drop=True)))
    ident = oi_identity(panel)
    broken = ident[~ident["balanced"]]
    print(f"\nunbalanced market-weeks: {len(broken)} of {len(ident)}")
    print(broken.groupby("market_code").agg(
        weeks=("imbalance", "size"),
        worst=("imbalance", lambda s: s.abs().max())).to_string())
    print(f"\nall within CFTC's own rounding tolerance: "
          f"{int(ident['within_tolerance'].sum())} / {len(ident)}")

    # Everything below drops the aggregates.
    frag = rank_markets(market_fragility(last))
    frag["asset_class"] = frag["market_name"].map(asset_class)
    universe = frag[~frag["market_code"].isin(CONSOLIDATED)].copy()

    rule("4. FRAGILITY BY ASSET CLASS (consolidated aggregates dropped)")
    by_class = universe.groupby("asset_class").agg(
        markets=("market_code", "size"), open_interest=("open_interest", "sum"),
        phi_median=("phi", "median"), phi_max=("phi", "max"),
        q_sell_oi_median=("q_sell_over_oi", "median"),
        q_buy_oi_median=("q_buy_over_oi", "median")).sort_values(
            "open_interest", ascending=False).round(4)
    print(to_markdown(by_class.reset_index()))

    rule("5. TRAP THREE — Phi is NOT comparable across report types")
    disagg = market_fragility(latest())
    print(f"  TFF   Phi: median {universe['phi'].median():.3f}, "
          f"mean {universe['phi'].mean():.3f}, max {universe['phi'].max():.3f}")
    print(f"  DISAGG Phi: median {disagg['phi'].median():.3f}, "
          f"mean {disagg['phi'].mean():.3f}, max {disagg['phi'].max():.3f}")
    print("\nwhere the gross sits, and what it contributes:")
    for name, rows in (("TFF", contributions(last)),
                       ("DISAGG", contributions(latest()))):
        rows = rows.assign(gross_share=rows["gross"] / (2 * rows["open_interest"]))
        summary = rows.groupby("category").agg(
            gross_share=("gross_share", "mean"),
            phi_contribution=("phi_contribution", "mean")).round(4)
        print(f"\n  {name}:")
        print(summary.sort_values("gross_share", ascending=False).to_string())

    print("\nthe weight-free comparison, which IS valid:")
    for name, rows, cat in (("TFF leveraged", contributions(last), "leveraged"),
                            ("DISAGG managed_money", contributions(latest()),
                             "managed_money")):
        total_gross = 2 * rows.groupby("market_code")["open_interest"].max().sum()
        share = rows.loc[rows["category"] == cat, "gross"].sum() / total_gross
        print(f"  {name:<22} holds {share:.1%} of all gross open interest at weight 1.0")

    rule("6. THE RATES COMPLEX — the cash-futures basis trade")
    rates = contributions(last[last["market_code"].isin(RATES_COMPLEX)])
    pivot = rates.pivot_table(index="market_name", columns="category",
                              values="net", aggfunc="sum")
    pivot["open_interest"] = rates.groupby("market_name")["open_interest"].max()
    cols = ["asset_manager", "leveraged", "dealer", "other_reportable",
            "nonreportable", "open_interest"]
    print(pivot[cols].sort_values("open_interest", ascending=False).to_string())
    print("\ntotal net across all nine contracts:")
    print(rates.groupby("category")["net"].sum().sort_values().to_string())

    print("\nexit pressure, same nine:")
    rf = frag[frag["market_code"].isin(RATES_COMPLEX)]
    print(to_markdown(rf[["market_name", "open_interest", "q_sell", "q_buy",
                          "q_sell_over_oi", "q_buy_over_oi", "phi", "sell_to_buy"]]
                      .sort_values("open_interest", ascending=False)))

    rule("7. IS THE BASIS TRADE GROWING?")
    hist = contributions(panel[panel["market_code"].isin(RATES_COMPLEX)])
    lev = hist[hist["category"] == "leveraged"].groupby("report_date")["net"].sum()
    am = hist[hist["category"] == "asset_manager"].groupby("report_date")["net"].sum()
    trend = pd.DataFrame({"leveraged_net": lev, "asset_manager_net": am}).tail(14)
    trend["leveraged_change"] = trend["leveraged_net"].diff()
    print(trend.round(0).to_string())
    span = lev.max() - lev.min()
    print(f"\npanel range: {lev.min():,.0f} to {lev.max():,.0f}")
    print(f"latest {lev.iloc[-1]:,.0f}, which is "
          f"{(lev.iloc[-1] - lev.min()) / span:.0%} up from the most-short reading")

    print("\nUST 10Y, leveraged, last 8 weeks:")
    flows = decompose(panel[panel["market_code"] == "043602"])
    print(to_markdown(flows[flows["category"] == "leveraged"].tail(8)[
        ["report_date", "long_contracts", "short_contracts",
         "d_long", "d_short", "d_net", "flow_state"]]))

    print("\nUST 10Y, leveraged SHORT side, breadth-depth:")
    breadth = decompose_breadth(panel[panel["market_code"] == "043602"], side="short")
    print(to_markdown(breadth[breadth["category"] == "leveraged"].tail(6)[
        ["report_date", "position", "traders", "avg_position", "d_position",
         "d_traders", "d_avg", "dominant_term", "quadrant"]]))

    rule("8. CRYPTO — where Phi and Q point opposite ways")
    crypto = universe[universe["asset_class"] == "crypto"]
    print(f"{len(crypto)} of {len(universe)} markets, "
          f"{crypto['open_interest'].sum():,.0f} contracts "
          f"({crypto['open_interest'].sum() / universe['open_interest'].sum():.1%} of TFF OI)")
    print("\nhighest Phi in the whole TFF set:")
    print(to_markdown(universe.nlargest(5, "phi")[
        ["market_name", "open_interest", "phi", "q_sell_over_oi", "q_buy_over_oi",
         "top_phi_category", "top_phi_share"]]))

    nano = contributions(last[last["market_code"] == "133LM1"])
    print("\nNano Bitcoin, the second-highest Phi:")
    print(to_markdown(nano[["category", "long_contracts", "short_contracts", "net",
                            "gross", "weight", "phi_contribution"]]))
    lev_row = nano[nano["category"] == "leveraged"].iloc[0]
    market_oi = nano["open_interest"].iloc[0]
    print(f"\n  leveraged gross {lev_row['gross']:,.0f} = "
          f"{lev_row['gross'] / (2 * market_oi):.1%} of 2xOI")
    print(f"  leveraged net   {lev_row['net']:,.0f} = "
          f"{abs(lev_row['net']) / market_oi:.1%} of OI")
    print("  Phi near its ceiling, Q/OI near the floor. Different questions.")


def _tff_shape_labels(stable: pd.Series, fragile: pd.Series) -> pd.Series:
    """Six mutually exclusive outcomes of a (stable, fragile) category pair.

    Same construction as `reproduce.template_shape_stratified`, and explicit rather than
    fall-through for the same reason: a market with no position at all in one leg is a
    distinct outcome, not a variety of "the other leg is flat".
    """
    out = pd.Series(pd.NA, index=stable.index, dtype=object)
    out = out.mask((stable < 0) & (fragile > 0), "cocoa direction (stable short, fragile long)")
    out = out.mask((stable > 0) & (fragile < 0), "MIRROR (stable long, fragile short)")
    out = out.mask((stable < 0) & (fragile < 0), "same side (both short)")
    out = out.mask((stable > 0) & (fragile > 0), "same side (both long)")
    out = out.mask((stable != 0) & (fragile == 0), "fragile flat")
    out = out.mask(stable == 0, "no stable side")
    if out.isna().any():
        raise ValueError(f"{int(out.isna().sum())} market-weeks fell through every mask.")
    return out


def template_shape_tff() -> None:
    """Amendment B32: the cocoa template on TFF, where it cannot exist in the same form.

    B31 answered "do real markets show the cocoa shape" for Disaggregated. TFF is the other
    half of the COT universe and the half the macro book lives in, and the template is not
    merely rare there: **there is no producer category at all**. The nearest structural
    analogue is the lowest-weighted holder (Asset Manager, 0.3) opposed to the weight-1.0
    holder (Leveraged Funds), and the question becomes which way round they sit.

    Respects the three traps §2 of the TFF analysis establishes: the consolidated aggregates
    are dropped, the identity is not re-litigated here, and every figure is stratified by
    asset class because crypto is a third of the market COUNT and 2% of the open interest.
    """
    rule("THE COCOA TEMPLATE ON TFF, WHERE IT CANNOT EXIST IN THE SAME FORM (B32)")

    full = from_vintage(report_type="tff")
    full = full[~full["market_code"].isin(CONSOLIDATED)]
    full = full.assign(net=full["long_contracts"] - full["short_contracts"])
    n = (full.groupby(["report_date", "market_code", "category"])["net"].sum()
             .unstack("category").reset_index())
    nm = full.groupby("market_code")["market_name"].first()
    n["market_name"] = n["market_code"].map(nm)
    n["asset_class"] = n["market_name"].map(asset_class)
    oi = (full.groupby(["report_date", "market_code"])["open_interest"].max()
              .rename("open_interest"))
    n = n.merge(oi, on=["report_date", "market_code"], how="left")

    weeks = n["report_date"].nunique()
    print(f"\n{weeks} report weeks, {n['market_code'].nunique()} markets "
          f"(3 consolidated aggregates dropped), {len(n):,} market-weeks")

    print("\n  Disaggregated weights: producer_merchant 0.1 is the floor, and it is a")
    print("  PHYSICAL hedger. TFF has no such category. Its floor is asset_manager at 0.3,")
    print("  a pension or insurance book: unlevered and slow, but not standing for")
    print("  delivery. The analogue is structural, not exact, and that is the finding.")

    for stable, label in [("asset_manager", "asset_manager (w=0.3, the TFF floor)"),
                          ("dealer", "dealer (w=0.4)")]:
        n["shape"] = _tff_shape_labels(n[stable], n["leveraged"])
        print(f"\n--- {label} against leveraged (w=1.0), all {weeks} weeks, by asset class ---")
        ct = pd.crosstab(n["asset_class"], n["shape"])
        pct = (ct.div(ct.sum(axis=1), axis=0) * 100).map(lambda v: f"{v:.1f}%")
        print(to_markdown(pct.assign(**{"market-weeks": ct.sum(axis=1)}).reset_index()))

        # By count the report is a third crypto and by open interest it is 2%, so the
        # unweighted row above is not the whole story (§2 of the TFF analysis).
        w = (n.assign(_oi=n["open_interest"])
              .groupby("shape")["_oi"].sum().pipe(lambda s: s / s.sum()))
        print("  same table weighted by open interest rather than market count:")
        for k, v in w.sort_values(ascending=False).items():
            print(f"    {k:<46s} {v:6.1%}")

    n["shape"] = _tff_shape_labels(n["asset_manager"], n["leveraged"])
    print("\n--- the rates complex specifically, all weeks ---")
    r = n[n["market_code"].isin(RATES_COMPLEX)]
    print(f"  {r['market_code'].nunique()} contracts, {len(r):,} market-weeks: "
          f"{r['shape'].value_counts().to_dict()}")
    print(f"  leveraged net SHORT in {(r['leveraged'] < 0).mean():.1%} of them, "
          f"asset_manager net LONG in {(r['asset_manager'] > 0).mean():.1%}")

    print("\n--- is the shape a property of the market, as on Disaggregated? ---")
    g = n.groupby("market_code")
    mkt = pd.DataFrame({
        "asset_class": g["asset_class"].first(), "weeks": g.size(),
        "mirror": g["shape"].apply(
            lambda s: (s == "MIRROR (stable long, fragile short)").mean()),
        "cocoa": g["shape"].apply(
            lambda s: (s == "cocoa direction (stable short, fragile long)").mean())})
    mkt = mkt[mkt["weeks"] >= 40]
    extreme = ((mkt["mirror"] <= .1) | (mkt["mirror"] >= .9)).mean()
    print(f"  {len(mkt)} markets with >=40 weeks; {extreme:.1%} sit at one extreme of the")
    print("  mirror share (never or always), against 64.0% on Disaggregated.")
    print(f"  markets always MIRROR (>=90% of weeks): {int((mkt['mirror'] >= .9).sum())}")
    print(f"  markets always cocoa-direction (>=90%): {int((mkt['cocoa'] >= .9).sum())}")

    print("\n--- the asymmetry ceiling is TIGHTER on TFF, and by a factor of three ---")
    w_tff = cfg.weights_for("tff")
    w_dis = cfg.weights_for("disaggregated")
    c_tff = max(w_tff.values()) / min(w_tff.values())
    c_dis = max(w_dis.values()) / min(w_dis.values())
    print(f"  TFF            max/min = {max(w_tff.values())}/{min(w_tff.values())} "
          f"= {c_tff:.3f}")
    print(f"  Disaggregated  max/min = {max(w_dis.values())}/{min(w_dis.values())} "
          f"= {c_dis:.3f}")
    con = contributions(full, report_type="tff")
    q = (con.groupby(["report_date", "market_code", "q_side"])["q_contribution"].sum()
           .unstack("q_side").fillna(0.0))
    sell_over_buy = (q["sell"] / q["buy"].replace(0, pd.NA)).dropna().astype(float)
    buy_over_sell = (q["buy"] / q["sell"].replace(0, pd.NA)).dropna().astype(float)
    print(f"  {len(sell_over_buy):,} market-weeks with both sides live")
    print(f"    Q_sell/Q_buy: max {sell_over_buy.max():.4f}, "
          f"breaches of {c_tff:.3f}: {int((sell_over_buy > c_tff + 1e-9).sum())}")
    print(f"    Q_buy/Q_sell: max {buy_over_sell.max():.4f}, "
          f"breaches of {c_tff:.3f}: {int((buy_over_sell > c_tff + 1e-9).sum())}")
    print(f"    median Q_sell/Q_buy {sell_over_buy.median():.3f} "
          f"(Disaggregated median is 0.993)")
    print(f"\n  §A.2's cocoa asymmetry is 9.05x. On TFF the arithmetic maximum is "
          f"{c_tff:.2f}x,")
    print("  so no TFF market can reach it in any state of the world. The example is not")
    print("  merely unrepresentative of financial futures, it is out of their range.")


if __name__ == "__main__":
    main()
    template_shape_tff()
