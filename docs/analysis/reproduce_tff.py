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


if __name__ == "__main__":
    main()
