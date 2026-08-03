"""Reproduce every figure in ``2026-08-03-index-share.md``.

Handoff: ``docs/handoffs/2026-08-03-index-share.md`` §1. Needs the real store, including
the ``cot_supplemental`` domain added by cotdata #96 (``cotdata-update --cot-supplemental``).

    COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce_index_share.py

The one methodological point worth stating up front, because it constrains every table below:
the Supplemental report is futures-and-options COMBINED and the Disaggregated store is
futures-only. Their open interest is not the same quantity. So every statistic here is a
ratio formed WITHIN one report, and any index-versus-swap comparison is an inference across
two different bases rather than a decomposition. §3 of the handoff says this; the code
enforces it by never forming a quantity that mixes the two denominators.
"""

from __future__ import annotations

import cotdata
import numpy as np
import pandas as pd

# The 13 Supplemental markets. ZM (soybean meal) entered in 2013, the other 12 run from 2006.
MARKETS = {
    "ZW_001602": ("ZW", "Chicago wheat"),
    "KE_001612": ("KE", "KC wheat"),
    "ZC_002602": ("ZC", "Corn"),
    "ZS_005602": ("ZS", "Soybeans"),
    "ZL_007601": ("ZL", "Soybean oil"),
    "ZM_026603": ("ZM", "Soybean meal"),
    "CT_033661": ("CT", "Cotton"),
    "HE_054642": ("HE", "Lean hogs"),
    "LE_057642": ("LE", "Live cattle"),
    "GF_061641": ("GF", "Feeder cattle"),
    "CC_073732": ("CC", "Cocoa"),
    "SB_080732": ("SB", "Sugar"),
    "KC_083731": ("KC", "Coffee"),
}

# CFTC ships this one with a typo ("Swap__"), and it is load-bearing: a KeyError here would
# silently become a dropped market if it were caught broadly.
SWAP_SHORT = "Swap__Positions_Short_All"


def supplemental(code: str) -> pd.DataFrame:
    """Index prominence, from the Supplemental (combined futures-and-options) report."""
    df = cotdata.get_cot(code, report="supplemental").sort_index()
    oi = df["Open_Interest_All"].astype(float)
    long_ = df["CIT_Positions_Long_All"].astype(float)
    short = df["CIT_Positions_Short_All"].astype(float)

    out = pd.DataFrame(index=df.index)
    out["oi"] = oi
    out["index_gross_share"] = (long_ + short) / (2.0 * oi)
    out["index_long_share"] = long_ / oi
    out["index_net"] = long_ - short
    out["d_index_net_oi"] = out["index_net"].diff() / oi
    return out


def disaggregated(code: str) -> pd.DataFrame:
    """Swap and Managed Money, from the Disaggregated (futures-only) report."""
    df = cotdata.get_cot(code, report="disagg").sort_index()
    oi = df["Open_Interest_All"].astype(float)

    out = pd.DataFrame(index=df.index)
    out["oi"] = oi
    for tag, lo, sh in (
        ("swap", "Swap_Positions_Long_All", SWAP_SHORT),
        ("mm", "M_Money_Positions_Long_All", "M_Money_Positions_Short_All"),
    ):
        long_ = df[lo].astype(float)
        short = df[sh].astype(float)
        out[f"{tag}_gross_share"] = (long_ + short) / (2.0 * oi)
        out[f"{tag}_net"] = long_ - short
        out[f"d_{tag}_net_oi"] = out[f"{tag}_net"].diff() / oi
    return out


def weekly_returns(symbol: str, dates: pd.DatetimeIndex) -> pd.Series:
    """Report-week return, contemporaneous with the positioning change.

    ``propadj`` and nothing else: the layer-2 trap table refuses ``backadj`` for anything
    denominated in percent, because additive back-adjustment preserves absolute price
    changes rather than percentage ones. See ``futures/riskunits.py``.

    The window is prior report date to this report date, so it lines up with ``diff()`` on
    positioning rather than leading or lagging it by a week.
    """
    px = cotdata.get_prices(symbol, adjustment="propadj").sort_index()
    close = px["Close"].astype(float)
    # Last settle at or before each Tuesday report date.
    idx = close.index.searchsorted(dates, side="right") - 1
    ok = idx >= 0
    aligned = pd.Series(np.nan, index=dates, dtype=float)
    aligned[ok] = close.to_numpy()[idx[ok]]
    # A non-positive close makes a percent return meaningless; mask rather than clip.
    aligned[aligned <= 0] = np.nan
    return aligned.pct_change()


def autocorr(s: pd.Series, lag: int) -> float:
    s = s.dropna()
    return float(s.autocorr(lag=lag)) if len(s) > lag + 2 else float("nan")


def main() -> None:
    rows, stress_rows, corr_rows = [], [], []
    panels = {}

    for code, (sym, name) in MARKETS.items():
        sup = supplemental(code)
        dis = disaggregated(code)
        ret = weekly_returns(sym, sup.index)

        panels[code] = (sup, dis, ret)

        rows.append({
            "market": name,
            "sym": sym,
            "weeks": len(sup),
            "from": sup.index.min().date(),
            "idx_gross_share": sup["index_gross_share"].mean(),
            "idx_long_share": sup["index_long_share"].mean(),
            "ac1": autocorr(sup["index_net"], 1),
            "ac4": autocorr(sup["index_net"], 4),
            "ac12": autocorr(sup["index_net"], 12),
            # Comparators. The handoff asks only for the index autocorrelation, but a level
            # series is autocorrelated for every category, so the bare number cannot
            # distinguish sticky from ordinary. These are what make it readable.
            "ac12_swap": autocorr(dis["swap_net"], 12),
            "ac12_mm": autocorr(dis["mm_net"], 12),
            # The discriminating statistic: how much the book moves week to week, as a
            # share of its own report's open interest.
            "sd_idx": sup["d_index_net_oi"].std(),
            "sd_swap": dis["d_swap_net_oi"].std(),
            "sd_mm": dis["d_mm_net_oi"].std(),
        })

        # Index vs swap prominence, on the overlapping report dates only.
        both = pd.concat(
            [sup["index_gross_share"], dis["swap_gross_share"]], axis=1, join="inner"
        ).dropna()
        corr_rows.append({
            "market": name,
            "n": len(both),
            "idx_gross": both["index_gross_share"].mean(),
            "swap_gross": both["swap_gross_share"].mean(),
            "corr_level": both.corr().iloc[0, 1],
            "corr_chg": both.diff().dropna().corr().iloc[0, 1],
        })

        # Stress weeks: the sharpest 5% of report-week drawdowns in each market.
        j = pd.concat([sup, dis.reindex(sup.index), ret.rename("ret")], axis=1)
        j = j.dropna(subset=["ret"])
        cut = j["ret"].quantile(0.05)
        stressed = j[j["ret"] <= cut]
        stress_rows.append({
            "market": name,
            "n": len(stressed),
            "cut": cut,
            "idx_all": j["d_index_net_oi"].mean(),
            "idx_stress": stressed["d_index_net_oi"].mean(),
            "mm_stress": stressed["d_mm_net_oi"].mean(),
            "swap_stress": stressed["d_swap_net_oi"].mean(),
        })

    prom = pd.DataFrame(rows).set_index("market")
    corr = pd.DataFrame(corr_rows).set_index("market")
    stress = pd.DataFrame(stress_rows).set_index("market")

    pd.set_option("display.width", 200, "display.max_columns", 40)

    print("=" * 100)
    print("1. INDEX PROMINENCE AND PERSISTENCE (Supplemental, within-report ratios)")
    print("=" * 100)
    print(prom[["sym", "weeks", "from", "idx_gross_share", "idx_long_share",
                "ac1", "ac4", "ac12"]].round(4).to_string())
    print()
    print("Autocorrelation at 12 weeks, index vs the two comparators. A level series is")
    print("autocorrelated for everyone, so the index column alone cannot separate sticky")
    print("from ordinary; these two are what make it readable.")
    print(prom[["ac12", "ac12_swap", "ac12_mm"]].round(4).to_string())
    print()
    print("  index more persistent than swap at 12w in %d of 13"
          % int((prom.ac12 > prom.ac12_swap).sum()))
    print("  index more persistent than MM   at 12w in %d of 13"
          % int((prom.ac12 > prom.ac12_mm).sum()))
    print("  medians: index %.3f, swap %.3f, MM %.3f"
          % (prom.ac12.median(), prom.ac12_swap.median(), prom.ac12_mm.median()))

    print()
    print("Weekly change volatility, sd of d(net)/OI. INDEX from Supplemental;")
    print("SWAP and MM from Disaggregated. Cross-report, so an inference (handoff §3).")
    print(prom[["sd_idx", "sd_swap", "sd_mm"]].round(5).to_string())
    print()
    print("  index steadier than swap in %d of 13 markets" % int((prom.sd_idx < prom.sd_swap).sum()))
    print("  index steadier than MM   in %d of 13 markets" % int((prom.sd_idx < prom.sd_mm).sum()))
    print("  median ratio index/swap = %.3f, index/MM = %.3f"
          % ((prom.sd_idx / prom.sd_swap).median(), (prom.sd_idx / prom.sd_mm).median()))

    print()
    print("=" * 100)
    print("2. STRESS WEEKS (worst 5% of report-week returns, propadj)")
    print("=" * 100)
    print("mean d(net)/OI, unconditional vs stressed. Positive = adding to net long.")
    print(stress.round(5).to_string())
    print()
    n_hold = int((stress.idx_stress.abs() < stress.mm_stress.abs()).sum())
    print("  index moves less than MM under stress in %d of 13 markets" % n_hold)
    print("  index mean under stress %+.5f vs unconditional %+.5f"
          % (stress.idx_stress.mean(), stress.idx_all.mean()))
    print("  MM mean under stress    %+.5f" % stress.mm_stress.mean())
    print("  swap mean under stress  %+.5f" % stress.swap_stress.mean())

    print()
    print("  Relative to Managed Money = 1.0, which is what the weight table anchors on:")
    print("    routine turnover  swap/MM %.3f   index/MM %.3f"
          % ((prom.sd_swap / prom.sd_mm).median(), (prom.sd_idx / prom.sd_mm).median()))
    print("    stress-week move  swap/MM %.3f   index/MM %.3f"
          % (stress.swap_stress.mean() / stress.mm_stress.mean(),
             stress.idx_stress.mean() / stress.mm_stress.mean()))
    print("    (turnover is not fragility: a book can trade little and still be forced.")
    print("     These bound the weight from observed behaviour, they do not set it.)")
    print("  swap ADDS to net long under stress in %d of 13 markets"
          % int((stress.swap_stress > 0).sum()))

    print()
    print("=" * 100)
    print("3. INDEX VERSUS SWAP PROMINENCE (cross-report inference, never a difference)")
    print("=" * 100)
    print(corr.round(4).to_string())
    print()
    print("  median level correlation  %.3f" % corr.corr_level.median())
    print("  median change correlation %.3f" % corr.corr_chg.median())
    print("  markets where swap book exceeds index book: %d of 13"
          % int((corr.swap_gross > corr.idx_gross).sum()))

    print()
    print("=" * 100)
    print("4. WALKTHROUGHS: cocoa and live cattle")
    print("=" * 100)
    for code in ("CC_073732", "LE_057642"):
        sup, dis, ret = panels[code]
        sym, name = MARKETS[code]
        last = sup.index.max()
        s, d = sup.loc[last], dis.loc[last]
        print()
        print("--- %s (%s), latest report date %s ---" % (name, sym, last.date()))
        print("  OI (combined)        %12.0f" % s.oi)
        print("  CIT long             %12.0f" % (s.index_long_share * s.oi))
        print("  CIT short            %12.0f" % ((s.index_long_share * s.oi) - s.index_net))
        print("  index_gross_share    %12.4f  = (L+S) / (2 x OI)" % s.index_gross_share)
        print("  index_long_share     %12.4f  = L / OI" % s.index_long_share)
        print("  index_net            %12.0f  = L - S" % s.index_net)
        print("  ---- Disaggregated (futures-only, different basis) ----")
        print("  OI (futures only)    %12.0f" % d.oi)
        print("  swap_gross_share     %12.4f" % d.swap_gross_share)
        print("  swap_net             %12.0f" % d.swap_net)
        print("  mm_gross_share       %12.4f" % d.mm_gross_share)
        print("  ---- history ----")
        print("  mean index_gross_share %10.4f" % sup.index_gross_share.mean())
        print("  ac(1/4/12)             %6.3f %6.3f %6.3f"
              % (autocorr(sup.index_net, 1), autocorr(sup.index_net, 4),
                 autocorr(sup.index_net, 12)))
        print("  sd d(index_net)/OI     %10.5f" % sup.d_index_net_oi.std())
        print("  sd d(swap_net)/OI      %10.5f" % dis.d_swap_net_oi.std())
        print("  sd d(mm_net)/OI        %10.5f" % dis.d_mm_net_oi.std())


def cocoa_premise() -> None:
    """§8: the handoff's §0 opens on cocoa's swap book holding the largest net long.

    True on the latest report date and a minority configuration over the history, which is
    the correction. Reproduced here rather than left as a shell one-liner, per the
    every-figure-carries-a-reproducer rule.
    """
    cats = {
        "Producer/Merchant": ("Prod_Merc_Positions_Long_All", "Prod_Merc_Positions_Short_All"),
        "Swap": ("Swap_Positions_Long_All", SWAP_SHORT),
        "Managed Money": ("M_Money_Positions_Long_All", "M_Money_Positions_Short_All"),
        "Other Reportable": ("Other_Rept_Positions_Long_All", "Other_Rept_Positions_Short_All"),
        "Non-Reportable": ("NonRept_Positions_Long_All", "NonRept_Positions_Short_All"),
    }
    d = cotdata.get_cot("CC_073732", report="disagg").sort_index()
    nets = pd.DataFrame(
        {k: d[lo].astype(float) - d[sh].astype(float) for k, (lo, sh) in cats.items()}
    )

    print()
    print("=" * 100)
    print("5. HANDOFF §0 PREMISE CHECK: cocoa's largest net long")
    print("=" * 100)
    print("latest report date %s:" % d.index.max().date())
    for k, v in nets.iloc[-1].sort_values(ascending=False).items():
        print("  %-18s %9s" % (k, format(v, ",.0f")))
    print("  -> largest net long today: %s" % nets.iloc[-1].idxmax())
    print()
    print("share of all %d weeks each category holds the LARGEST net long:" % len(nets))
    share = nets.idxmax(axis=1).value_counts(normalize=True).mul(100).round(1)
    for k, v in share.items():
        print("  %-18s %5.1f%%" % (k, v))
    print()
    print("  Swap holds it %.1f%% of the time. The premise is read off one week."
          % share.get("Swap", 0.0))


if __name__ == "__main__":
    main()
    cocoa_premise()
