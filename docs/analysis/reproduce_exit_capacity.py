"""Reproducer for every figure in 2026-07-28-exit-capacity.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_exit_capacity.py

Deterministic: no sampling, no seeds, no fitting. Pinned to report week 2026-07-28,
released 2026-07-31.

Separate from `reproduce.py` for the same reason `reproduce_tff.py` is: this document
covers **both** report types, and the one thing it must never do is let a reader compare a
Disaggregated `Q_sell` against a TFF one as though they were the same quantity. Keeping the
two in one script with the report type carried on every row makes the seam visible in the
output rather than in a footnote.

Blocks are numbered and ordered to match the document's sections:

  2.       coverage: how many codes exist, how many reach a live `dtl_sell`, and why not
  3.       the T ranking over both reports, sorted by `T_sell` descending
  4.       the thin-fund screen, `|P_fragile| / OI < 0.05`
  6.1/6.2  the STORE choice: whether the vintage store was needed at all (it was not)
  6.6      release-indexed against current-state, i.e. whether revisions moved anything
  6.3-6.7  what the reports must carry, and the vintage lineage behind this week
  7.       the stress denominator, and where it inverts the calm reading
  8.       week on week, 2026-07-21 into 2026-07-28, decomposed into dQ and dV

Nothing here computes anything new. Every number is `latest` / `VintageCotSource.load` ->
`ContractMaster.annotate` -> `fragility_frame` -> `add_volume` -> `rank_markets`, plus
`contributions` for the fragile-category net and `volume_coverage` for the census.
"""
import pandas as pd

from crowdmon.core import config as cfg
from crowdmon.futures import (
    ContractMaster,
    VintageCotSource,
    add_volume,
    contributions,
    fragility_frame,
    latest,
    provenance_summary,
    rank_markets,
    volume_coverage,
)

#: The release that published report week 2026-07-28.
RELEASE = "2026-07-31"

#: The report week before the scored one. Used only by §8, and read from the current-state
#: store rather than the vintage one, per §6.2: both weeks must come from the same source
#: or the comparison acquires a store difference it cannot separate from a market move.
PRIOR_WEEK = "2026-07-21"

#: The two reports with configured fragility weights. Legacy is deliberately absent, for
#: the reason `core/config.py` gives: its `noncommercial` bucket merges levered funds with
#: everything else non-commercial, which is the distinction the weights exist to make.
REPORTS = ("disaggregated", "tff")

#: The weight-1.0 fragile category per report. This is the `P_MM` of the thin-fund screen,
#: and it is a DIFFERENT category in each report, which is why the screen is computed per
#: report rather than once over a concatenated frame.
FRAGILE_CATEGORY = {"disaggregated": "managed_money", "tff": "leveraged"}

#: Below this share of open interest a market has effectively no fragile capital, so a `T`
#: computed over it is well formed and says nothing. Stated here rather than inline so its
#: effect on the published table is visible in one place.
THIN_FUND = 0.05


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def _score(panel: pd.DataFrame, report_type: str) -> pd.DataFrame:
    """The whole chain, on one report's panel. Existing modules only."""
    panel = ContractMaster.load().annotate(panel)
    spec = panel[["market_code", "symbol"]].drop_duplicates("market_code")
    frag = add_volume(fragility_frame(panel).merge(spec, on="market_code", how="left"))
    ranked = rank_markets(frag, volume=frag["adv"], stress_volume=frag["adv_stress"])

    # The fragile category's NET, which is what the thin-fund screen is about. Taken from
    # `contributions` rather than recomputed, so it cannot drift from the Phi decomposition.
    contrib = contributions(panel, report_type=report_type)
    net = (contrib[contrib["category"] == FRAGILE_CATEGORY[report_type]]
           .set_index("market_code")["net"].astype("float64"))
    oi = pd.to_numeric(ranked["open_interest"], errors="coerce")
    ranked["p_fragile"] = ranked["market_code"].map(net)
    ranked["p_fragile_over_oi"] = (ranked["p_fragile"].abs() / oi).where(oi > 0)
    ranked["thin_fund"] = ranked["p_fragile_over_oi"] < THIN_FUND
    ranked["kv"] = cfg.KAPPA * ranked["adv"]
    ranked["report"] = report_type
    return ranked


def by_release() -> dict[str, pd.DataFrame]:
    """Release-indexed: the panel as it was knowable at the 2026-07-31 release."""
    out = {}
    for rt in REPORTS:
        raw = VintageCotSource(report_type=rt).load(RELEASE)
        raw = raw[raw["report_date"] == raw["report_date"].max()].reset_index(drop=True)
        out[rt] = _score(raw, rt).assign(
            pit_complete=bool(raw["pit_complete"].all()),
            observed_at=raw["observed_at"].min())
    return out


def by_current_state() -> dict[str, pd.DataFrame]:
    """Current-state: the same week with every revision the store now holds applied."""
    return {rt: _score(latest(report_type=rt), rt) for rt in REPORTS}


def coverage(scored: dict[str, pd.DataFrame]) -> None:
    rule("2. COVERAGE: which markets can be scored at all")
    for rt, f in scored.items():
        print(f"\n--- {rt}, report week {f['report_date'].max().date()} ---")
        print(volume_coverage(f).to_string())
        print(f"live dtl_sell: {int(f['dtl_sell'].notna().sum())} of "
              f"{f['market_code'].nunique()} codes")


def ranking(live: pd.DataFrame) -> pd.DataFrame:
    rule("3. T = Q / (kappa V), both reports, sorted by T_sell descending")
    show = live[["report", "market_code", "market_name", "symbol", "q_sell", "q_buy",
                 "kv", "dtl_sell", "dtl_buy", "phi", "thin_fund"]].copy()
    show["market_name"] = show["market_name"].str.slice(0, 34)
    print(show.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    print(f"\nkappa = {cfg.KAPPA}. T_sell {live['dtl_sell'].min():.2f} to "
          f"{live['dtl_sell'].max():.2f} days, median {live['dtl_sell'].median():.2f}")
    print(f"volume staleness: max {int(live['volume_staleness_days'].max())} day(s)")
    return show


def thin_funds(live: pd.DataFrame) -> None:
    rule(f"4. THIN FUND: |P_fragile| / OI < {THIN_FUND}")
    t = live[live["thin_fund"]][
        ["report", "symbol", "market_name", "p_fragile", "open_interest",
         "p_fragile_over_oi", "dtl_sell"]]
    print(t.to_string(index=False, float_format=lambda x: f"{x:,.6f}"))
    print(f"\n{len(t)} of {len(live)} flagged. Rank of the flagged markets on T_sell: "
          f"{sorted(live.reset_index(drop=True).index[live['thin_fund'].to_numpy()] + 1)}")
    band = live[(live["p_fragile_over_oi"] > 0.04) & (live["p_fragile_over_oi"] < 0.07)]
    print("\nborderline band 0.04 to 0.07, where the cut is doing real work:")
    print(band[["symbol", "p_fragile_over_oi", "thin_fund"]].to_string(
        index=False, float_format=lambda x: f"{x:,.6f}"))


def stress(live: pd.DataFrame) -> None:
    rule("7. THE STRESS DENOMINATOR, and where it inverts the calm reading")
    s = live[["report", "symbol", "dtl_sell", "dtl_sell_stress", "dtl_buy",
              "dtl_buy_stress"]].copy()
    s["v_ratio"] = (live["adv_stress"] / live["adv"]).round(3)
    print(s.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
    more = live["adv_stress"] > live["adv"]
    print(f"\nstress volume ABOVE calm: {int(more.sum())} of {len(live)} pooled")
    for rt, g in live.groupby("report"):
        print(f"  {rt}: {int((g['adv_stress'] > g['adv']).sum())} of {len(g)}")
    print(f"T_sell_stress > T_sell (stress is the binding case): "
          f"{int((live['dtl_sell_stress'] > live['dtl_sell']).sum())} of {len(live)}")


def release_vs_current(rel: pd.DataFrame, now: pd.DataFrame) -> None:
    rule("6.6 RELEASE-INDEXED vs CURRENT-STATE REVISIONS: does the read differ?")
    j = rel.merge(now, on=["report", "market_code"], suffixes=("_rel", "_now"))
    rows = []
    for c in ("q_sell", "q_buy", "phi", "dtl_sell", "dtl_buy", "open_interest",
              "p_fragile"):
        d = (j[f"{c}_rel"] - j[f"{c}_now"]).abs()
        rows.append({"column": c, "markets_differing": int((d > 1e-9).sum()),
                     "max_abs_diff": float(d.max())})
    print(f"{len(j)} markets matched")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"live only at release: {sorted(set(rel['market_code']) - set(now['market_code']))}")
    print(f"live only now:        {sorted(set(now['market_code']) - set(rel['market_code']))}")


def store_choice(vintage: pd.DataFrame) -> None:
    """§6.1 and §6.2: the vintage store was not required, measured rather than argued.

    `latest()` routes to `from_vintage`, which is the normally correct instinct on a
    cross-market ranking because the vintage store carries 346 Disaggregated codes against
    the current-state parquets' 27. It is the wrong instinct for `T`, and this block is the
    proof: the binding constraint is the contract-spec join, every code that clears it is
    already in the current-state store, and that store carries 1,051 weeks instead of 82.
    """
    from crowdmon.futures import from_current_store, from_vintage

    rule("6.1 / 6.2 STORE CHOICE: does T need the vintage store at all?")

    frames = []
    for rt in REPORTS:
        cur = from_current_store(report_type=rt)
        cur = cur[cur["report_date"] == cur["report_date"].max()]
        frames.append(_score(cur, rt))
    current = pd.concat(frames, ignore_index=True).dropna(subset=["dtl_sell"])

    print(f"live markets: vintage {len(vintage)}, current-state {len(current)}")
    rows = []
    j = vintage.merge(current, on=["report", "market_code"], suffixes=("_v", "_c"))
    for c in ("q_sell", "q_buy", "phi", "dtl_sell", "dtl_buy", "open_interest",
              "p_fragile"):
        d = (j[f"{c}_v"] - j[f"{c}_c"]).abs()
        rows.append({"column": c, "markets_differing": int((d > 1e-9).sum()),
                     "max_abs_diff": float(d.max())})
    print(f"{len(j)} matched")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"live only in vintage: "
          f"{sorted(set(vintage['market_code']) - set(current['market_code']))}")
    print(f"live only in current: "
          f"{sorted(set(current['market_code']) - set(vintage['market_code']))}")

    print("\n--- why the extra vintage breadth cannot help: it dies at the spec join ---")
    rows = []
    for rt in REPORTS:
        fv, fc = from_vintage(report_type=rt), from_current_store(report_type=rt)
        liv = set(vintage.loc[vintage["report"] == rt, "market_code"])
        rows.append({"report": rt,
                     "vintage_codes": fv["market_code"].nunique(),
                     "vintage_weeks": fv["report_date"].nunique(),
                     "vintage_from": str(fv["report_date"].min().date()),
                     "current_codes": fc["market_code"].nunique(),
                     "current_weeks": fc["report_date"].nunique(),
                     "current_from": str(fc["report_date"].min().date()),
                     "live_T": len(liv),
                     "live_in_current": len(liv & set(fc["market_code"]))})
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nEvery live-T code is already in the current-state store, which holds 1,051 "
          "weeks\nagainst the vintage store's 82. Breadth past the registry is exactly the "
          "breadth\nthat has no contract spec, so it cannot reach a T.")


def week_on_week() -> None:
    """§8: report week 2026-07-21 against 2026-07-28, both from the current-state store.

    The point of the block is the DECOMPOSITION, not the ranking. `T = Q / (kappa V)` has
    two factors that move on completely different timescales: `Q` is a fresh weekly
    observation while `V` is a 252-day trailing mean, so a one-week `dV` is bounded at
    roughly 1/252 of a normal day's deviation. Printing `dQ%` and `dV%` beside `dT%` is
    what stops a reader attributing a positioning move to a liquidity move.
    """
    from crowdmon.futures import from_current_store

    rule(f"8. WEEK ON WEEK: {PRIOR_WEEK} into 2026-07-28")

    weeks = {}
    for wk in (PRIOR_WEEK, "2026-07-28"):
        parts = []
        for rt in REPORTS:
            p = from_current_store(report_type=rt)
            p = p[p["report_date"] == pd.Timestamp(wk)]
            parts.append(_score(p, rt))
        weeks[wk] = pd.concat(parts, ignore_index=True).dropna(subset=["dtl_sell"])

    a, b = weeks[PRIOR_WEEK], weeks["2026-07-28"]
    print(f"live markets: {PRIOR_WEEK} {len(a)}, 2026-07-28 {len(b)}")
    print(f"live only in {PRIOR_WEEK}: "
          f"{sorted(set(a['market_code']) - set(b['market_code']))}")
    print(f"live only in 2026-07-28: "
          f"{sorted(set(b['market_code']) - set(a['market_code']))}")

    key = ["report", "market_code", "symbol"]
    cols = ["q_sell", "dtl_sell", "adv", "phi", "p_fragile", "p_fragile_over_oi",
            "thin_fund", "open_interest"]
    j = a[key + cols].merge(b[key + cols], on=key, suffixes=("_a", "_b"))
    j["rank_a"] = j["dtl_sell_a"].rank(ascending=False).astype(int)
    j["rank_b"] = j["dtl_sell_b"].rank(ascending=False).astype(int)
    j["d_rank"] = j["rank_a"] - j["rank_b"]
    for c in ("dtl_sell", "q_sell", "adv"):
        j[f"d_{c}_pct"] = 100 * (j[f"{c}_b"] - j[f"{c}_a"]) / j[f"{c}_a"]

    print("\n--- every market, ordered by the scored week ---")
    print(j.sort_values("dtl_sell_b", ascending=False)[
        ["report", "symbol", "rank_a", "rank_b", "d_rank", "dtl_sell_a", "dtl_sell_b",
         "d_dtl_sell_pct", "d_q_sell_pct", "d_adv_pct", "phi_a", "phi_b"]].to_string(
        index=False, float_format=lambda x: f"{x:,.2f}"))

    corr = j["dtl_sell_a"].rank().corr(j["dtl_sell_b"].rank())
    print(f"\nrank correlation T_sell: {corr:.4f}")
    print(f"median |dT|: {j['d_dtl_sell_pct'].abs().median():.2f}%   "
          f"max |rank move|: {int(j['d_rank'].abs().max())}   "
          f"markets moving <= 2 places: {int((j['d_rank'].abs() <= 2).sum())} of {len(j)}")
    print(f"max |dV|: {j['d_adv_pct'].abs().max():.2f}%   "
          f"markets with |dV| < 0.7%: {int((j['d_adv_pct'].abs() < 0.7).sum())} of {len(j)}")
    print("A 252-day trailing mean cannot move much in a week, so dT tracks dQ and a "
          "week-on-week\nT move is a positioning statement rather than a liquidity one.")

    print("\n--- thin-fund membership, which is 7 in both weeks and not the same 7 ---")
    crossed = j[j["thin_fund_a"] != j["thin_fund_b"]]
    print(crossed[["report", "symbol", "p_fragile_a", "p_fragile_b",
                   "p_fragile_over_oi_a", "p_fragile_over_oi_b",
                   "thin_fund_a", "thin_fund_b"]].to_string(
        index=False, float_format=lambda x: f"{x:,.4f}"))
    for wk, f in weeks.items():
        print(f"  {wk}: {sorted(f.loc[f['thin_fund'], 'symbol'].dropna())}")


def vintage_requirement() -> None:
    """§6.3 to §6.7: what the reports must carry, and what only vintage can do."""
    from cotdata import vintage_ingest as vi

    rule("6.3 - 6.7 THE COT REQUIREMENT: what T actually reads")

    obs = vi.read_observations()
    print("--- the whole vintage store ---")
    print(obs.groupby("report_type").agg(
        rows=("market_code", "size"), codes=("market_code", "nunique"),
        weeks=("report_date", "nunique"), first=("report_date", "min"),
        last=("report_date", "max")).to_string())
    print(f"\nnatural key: {vi.NATURAL_KEY}")
    print(f"columns: {list(obs.columns)}")
    print(f"combined values held: {sorted(obs['combined'].unique())}   "
          f"tombstones: {int(obs['is_tombstone'].sum())}")

    print("\n--- what the scored week is made of ---")
    week = obs[(obs["report_date"] == "2026-07-28")
               & obs["report_type"].isin(REPORTS)]
    print(week.groupby(["report_type", "snapshot_id", "observed_at", "release_date",
                        "release_date_source"]).size().to_string())
    per_key = week.groupby(vi.NATURAL_KEY).size().value_counts().to_dict()
    print(f"\nvintages per natural key: {per_key}")
    print("provenance:", provenance_summary(week).to_dict())

    print("\n--- capture history: why the release read is not pit_complete ---")
    hist = obs[obs["report_type"].isin(REPORTS)]
    print(hist.groupby("report_date")["observed_at"].agg(["min", "nunique"]).tail(6)
          .to_string())
    print("\nThe 2026-07-31 01:15Z capture PREDATES the 15:30 ET release of that day, so "
          "the\nfirst capture holding report week 2026-07-28 is the one on 2026-08-01.")

    print("\n--- columns T needs, of the 22 the store carries ---")
    needed = ["report_date", "market_code", "report_type", "combined", "category",
              "market_name", "long_contracts", "short_contracts", "spread_contracts",
              "open_interest", "release_date", "release_date_source", "observed_at",
              "snapshot_id"]
    unused = [c for c in obs.columns if c not in needed]
    print(f"read:   {needed}")
    print(f"unread: {unused}")


def main() -> None:
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.max_rows", 300)

    rel_by_report = by_release()
    now_by_report = by_current_state()

    coverage(rel_by_report)

    rel = pd.concat(rel_by_report.values(), ignore_index=True)
    now = pd.concat(now_by_report.values(), ignore_index=True)
    live = rel.dropna(subset=["dtl_sell"]).sort_values(
        "dtl_sell", ascending=False).reset_index(drop=True)

    # Ordered to match the document's sections, so a reader can follow one against the
    # other. The blocks are independent; only the printed order changes.
    ranking(live)
    thin_funds(live)
    store_choice(live)
    release_vs_current(rel.dropna(subset=["dtl_sell"]), now.dropna(subset=["dtl_sell"]))
    vintage_requirement()
    stress(live)
    week_on_week()


if __name__ == "__main__":
    main()
