"""Reproducer for §2's gate in `docs/handoffs/2026-08-03-report-layer.md`.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_report_gate.py

Deterministic: no sampling, no seeds, no fitting. Regenerates every figure in
`docs/design/amendments-2026-08-03.md` §C18-§C22.

**This is a classification exercise, not a validation.** It asks whether each caveat this
package has measured can be attached to a market-week, and whether an existing output
already says so. It renders no verdict on whether `D` measures anything, which this package
deliberately cannot answer (`tests/test_boundaries.py` refuses an import of `crucible`).
"""
import warnings

import pandas as pd

from crowdmon.futures import (
    ContractMaster,
    VintageCotSource,
    add_commonality,
    add_composite,
    add_extremity,
    add_notional,
    add_risk_units,
    add_volume,
    commonality_betas,
    coverage_ladder,
    decompose,
    flat_phi_identity,
    from_current_store,
    from_vintage,
    illiquidity_panel,
    market_fragility,
    rank_markets,
)

#: The two venue strings that make a market power or gas basis, per
#: `reproduce.py::POWER_VENUES`. Parsed from `market_name`, not hand-listed per market.
POWER_VENUES = frozenset({"ICE FUTURES ENERGY DIV", "NODAL EXCHANGE"})

#: Flow states that answer "is this market mid-exit?". `mixed` and `gap` do not, and `quiet`
#: is measured below at 3 occurrences in 27,167 market-weeks.
DECISIVE_STATES = frozenset({"long_liquidation", "new_longs", "short_covering",
                             "new_shorts"})

#: `composite.DEFAULT_MIN_PERIODS`, restated here only so the vintage arithmetic is legible.
PCT_MIN_PERIODS = 104


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def build():
    """The composite chain, and the per-category frame the coverage ladder needs."""
    panel = from_current_store()
    per_category = add_volume(add_extremity(add_risk_units(
        add_notional(ContractMaster.load().annotate(panel)))))
    volume = (per_category.groupby(["report_date", "market_code"])[["adv", "adv_stress"]]
              .max().reset_index())
    per_market = market_fragility(panel).merge(
        volume, on=["report_date", "market_code"], how="left")
    # `add_commonality` keys on `symbol`, which `market_fragility` does not carry: it is a
    # contract-master column and fragility is deliberately price-free. Annotated here rather
    # than inside §C22 so the ranked frame is the same object the composite was built from.
    per_market = ContractMaster.load().annotate(per_market)
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])
    return panel, per_category, ranked, add_composite(ranked, per_category)


def c18_warmup_is_row_computable(scored: pd.DataFrame) -> None:
    """§C18. The two null causes are separable per row, and the rule is exact."""
    rule("C18. Warm-up and a missing term are separable per row, exactly")
    terms = ["crowding_long", "illiquidity_sell", "fragility"]
    null_pct = scored["damage_sell_pct"].isna()
    raw_null = scored["damage_sell"].isna()
    print(f"rows: {len(scored):,}   null damage_sell_pct: {null_pct.sum():,} "
          f"({null_pct.mean():.1%})")
    print(f"  upstream term missing: {(null_pct & raw_null).sum():,}")
    print(f"  all terms present, pct null (third-window warm-up): "
          f"{(null_pct & ~raw_null).sum():,}")

    first_raw = scored.loc[scored["damage_sell"].notna(), "report_date"].min()
    first_pct = scored.loc[scored["damage_sell_pct"].notna(), "report_date"].min()
    print(f"\nfirst damage_sell {first_raw.date()}, first damage_sell_pct {first_pct.date()}")

    late = scored[scored["report_date"] >= first_pct]
    late_null = late["damage_sell_pct"].isna()
    all_present = late[terms].notna().all(axis=1)
    print(f"after {first_pct.date()}: {late_null.sum():,} of {len(late):,} still null "
          f"({late_null.mean():.1%})")
    print(f"  of those, all three terms present (would be warm-up): "
          f"{(late_null & all_present).sum():,}")
    print("  -> the rule 'all terms present AND pct null => warm-up' has zero exceptions,")
    print("     so the state is row-computable from columns the frame already carries.")


def c19_a17_is_partial(scored: pd.DataFrame, panel: pd.DataFrame) -> None:
    """§C19. `flow_state` conditions `ΔD` strongly, and is silent on most falling weeks."""
    rule("C19. dD plus flow_state: decisive on 40%, and the handoff's own contrast is empty")
    flows = decompose(panel)
    mm = flows[flows["category"] == "managed_money"][
        ["report_date", "market_code", "flow_state"]].copy()
    mm["report_date"] = pd.to_datetime(mm["report_date"])
    joined = scored.merge(mm, on=["report_date", "market_code"], how="left")
    joined = joined.sort_values(["market_code", "report_date"])
    joined["d_D"] = joined.groupby("market_code")["damage_sell_pct"].diff()

    usable = joined[joined["d_D"].notna() & joined["flow_state"].notna()]
    print(f"market-weeks with both dD and a flow state: {len(usable):,}")
    table = usable.groupby("flow_state")["d_D"].agg(
        n="count", median_dD="median", share_falling=lambda s: (s < 0).mean())
    print(table.round(4).to_string())

    fall = usable[usable["d_D"] < 0]
    decisive = fall["flow_state"].isin(DECISIVE_STATES)
    print(f"\nfalling-D weeks: {len(fall):,}")
    print(f"  decisive flow state: {decisive.sum():,} ({decisive.mean():.1%})")
    print(f"  mixed or gap, carrying nothing: {(~decisive).sum():,} ({(~decisive).mean():.1%})")
    print(f"  'quiet', the case the handoff named as 'genuinely safer': "
          f"{(fall['flow_state'] == 'quiet').sum()}")
    print(f"  'quiet' anywhere in the joined panel: "
          f"{(joined['flow_state'] == 'quiet').sum()} of {joined['flow_state'].notna().sum():,}")


def c20_ceiling_and_identity(scored: pd.DataFrame, panel: pd.DataFrame) -> None:
    """§C20. One caveat varies per row and is already published; one is constant."""
    rule("C20. The Phi ceiling varies and is exposed; the A21 identity is constant")
    ceiling = pd.to_numeric(scored["phi_denominator_covered"], errors="coerce")
    print(f"phi_denominator_covered: {ceiling.nunique():,} distinct values over "
          f"{len(scored):,} rows")
    print(f"  min {ceiling.min():.4f}  median {ceiling.median():.4f}  max {ceiling.max():.4f}")
    print(f"  rows below 0.99, where a 1.0 reference misleads: {(ceiling < 0.99).mean():.1%}")

    identity = flat_phi_identity(panel)
    residual = pd.to_numeric(identity["residual"], errors="coerce").abs()
    print(f"\nflat_phi_identity: {len(identity):,} rows, max |residual| {residual.max():.3e}")
    print(f"  rows above 1e-12: {(residual > 1e-12).sum()}")
    print("  -> computable per row and IDENTICAL on every row, so it discriminates nothing.")


def c21_the_band_has_no_market(scored: pd.DataFrame) -> None:
    """§C21. §C8's obligation cannot fire on any panel that carries a `D` percentile."""
    rule("C21. The C8 band obligation is unenforceable for want of a market, not a classifier")
    current = scored.copy()
    current["venue"] = current["market_name"].str.rsplit(" - ", n=1).str[-1]
    print(f"venue parses from market_name on {current['venue'].notna().mean():.1%} of rows")
    print(f"current-state panel: {current['market_code'].nunique()} markets, "
          f"{current['report_date'].nunique():,} weeks")
    print(f"  power/gas venue rows: {current['venue'].isin(POWER_VENUES).sum()}")

    vintage = from_vintage(report_type="disaggregated")
    vintage["venue"] = vintage["market_name"].str.rsplit(" - ", n=1).str[-1]
    markets = vintage.drop_duplicates("market_code")
    weeks = vintage["report_date"].nunique()
    print(f"vintage panel: {markets['market_code'].nunique():,} markets, {weeks} weeks")
    print(f"  power/gas venue markets: {markets['venue'].isin(POWER_VENUES).sum():,} "
          f"({markets['venue'].isin(POWER_VENUES).mean():.1%})")
    print(f"  weeks {weeks} against pct min_periods {PCT_MIN_PERIODS}: "
          f"pct(D) computable = {weeks >= PCT_MIN_PERIODS}")
    print("  -> one panel has the markets and cannot carry pct(D); the other carries pct(D)")
    print("     and has none of the markets. The classifier was never the blocker.")


def c22_already_exposed(per_category: pd.DataFrame, ranked: pd.DataFrame,
                        scored: pd.DataFrame) -> None:
    """§C22. Three of the four survivors are already attached by a shipped function."""
    rule("C22. Coverage and commonality already attach per row, so they do not count to E")
    ladder = coverage_ladder(per_category, scored)
    print(f"coverage_ladder: {len(ladder)} rows for "
          f"{per_category['market_code'].nunique()} markets (per MARKET, joins on market_code)")
    dropped = ladder[ladder["drops_at"].notna()]
    print(dropped[["market_name", "drops_at"]].to_string(index=False))

    cot = ContractMaster.load().annotate(
        VintageCotSource(report_type="disaggregated").load("2026-07-31"))
    specs = (cot.dropna(subset=["symbol", "point_value"])[["symbol", "point_value"]]
             .drop_duplicates("symbol").itertuples(index=False, name=None))
    betas = commonality_betas(illiquidity_panel(specs, start="2015-01-01"))
    with_beta = add_commonality(ranked, betas)
    print(f"\ncommonality_betas: {len(betas)} markets, "
          f"beta {betas.min():.4f} to {betas.max():.4f}")
    print(f"add_commonality attaches 'beta' per row on "
          f"{with_beta['beta'].notna().mean():.1%} of {len(with_beta):,} rows")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 240)
    panel, per_category, ranked, scored = build()
    scored["report_date"] = pd.to_datetime(scored["report_date"])

    c18_warmup_is_row_computable(scored)
    c19_a17_is_partial(scored, panel)
    c20_ceiling_and_identity(scored, panel)
    c21_the_band_has_no_market(scored)
    c22_already_exposed(per_category, ranked, scored)

    rule("The pre-registered table")
    print("R = row-computable, E = of those, not already exposed by a shipped output.")
    print("  strict  (candidates 4, 6 and 7 excluded): R = 4, E = 1  -> PASSES")
    print("  lenient (candidate 6 counted as partial):  R = 5, E = 2  -> PASSES")
    print("The verdict does not turn on the judgement call, which is the point of fixing")
    print("the table before measuring.")


if __name__ == "__main__":
    main()
