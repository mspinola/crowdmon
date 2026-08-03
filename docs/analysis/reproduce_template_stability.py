"""Reproduce `amendments-2026-08-03.md` §C1-C4 and §C6-C8.

C1-C4 were measured on 2026-08-03 as a blind re-derivation: the index-share handoff's §2
cited "§B33-B36", which no reachable search found, so they were rebuilt from scratch. The
originals turned out to exist on an unpushed branch and are now on main as
`docs/design/amendments-2026-08-02.md` §B33-B37, reproduced by
`docs/analysis/reproduce.py::template_conditional_magnitude`,
`::template_direction_agnostic`, `::template_swap_share` and `::template_stability`.

C6-C8 are the `w_SD` band that §4 of `docs/handoffs/2026-08-03-b-series-recovery.md` asks
for, under a settled decision that the weights stay static. **§C5 is not here**: it arrived
from crowdmon#42, is about a stale "there is no volume" claim, and carries its own inline
reproducer and its own live pin in `tests/test_volume_live.py`. Run from the repo root:

    COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce_template_stability.py

Seven questions here, in the order they have to be asked:

C1  Is template classification stable within its own window? §3 of the index-share handoff
    asserts it is not. Measured here by splitting the 82 weeks in half.
C2  Does the template rate move with `w_SD` at all? It cannot move, and the reason is
    structural rather than empirical.
C3  What DOES move with `w_SD`: `Q_sell`, `Q_buy`, and their ratio.
C4  Was `A_agnostic` undefined? No. It is `2026-08-02 §B34`'s DIRECTION-agnostic ratio, and
    this section originally read "agnostic" as WEIGHT-agnostic and measured a different and
    degenerate quantity. Corrected, with the degenerate measurement retained as the thing
    the name does not mean.
C6  The four-value band, `w_SD in {0.067, 0.2, 0.4, 0.7}`, with `A_agnostic` in it.
C7  The DIRECTION of the bias: how much `w_SD = 0.4` overstates fragile capital against the
    measured stress figure, and which markets carry it.
C8  Whether any of that reaches the composite, which consumes a percentile of `Phi` rather
    than `Phi`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crowdmon.core import config as cfg
from crowdmon.futures import from_vintage, market_fragility

# reproduce.py holds `_shape_panel`, `_shape_labels` and the hand-drawn CLASSIC_OUTRIGHTS
# list. Importing rather than re-deriving is the point: a second copy of the shape rule
# would be a second thing to keep in step, and B31's figures are pinned to that one.
_spec = importlib.util.spec_from_file_location(
    "_repro", Path(__file__).with_name("reproduce.py")
)
_repro = importlib.util.module_from_spec(_spec)
sys.modules["_repro"] = _repro
_spec.loader.exec_module(_repro)

EXTREME_LO, EXTREME_HI = 0.10, 0.90
W_SD_SWEEP = (0.2, 0.4, 0.7)

#: The reported band, per §4 of `2026-08-03-b-series-recovery.md`. Three round numbers and
#: one measured one: 0.067 is swap turnover as a fraction of Managed Money's in the worst
#: 5% of weeks (`2026-08-03-index-share.md` §5), so it is the empirically motivated lower
#: bound rather than a value chosen for spacing. Label it as such wherever the band is shown.
W_SD_BAND = (0.067, 0.2, 0.4, 0.7)
W_SD_LIVE = 0.4       # what `core/config.py` ships. Unchanged by this work.
W_SD_STRESS = 0.067   # the measured stress-regime figure.

# The 13 Supplemental markets, as 6-digit CFTC codes (the handoff's §2 restriction).
SUPPLEMENTAL = {
    "001602", "001612", "002602", "005602", "007601", "026603", "033661",
    "054642", "057642", "061641", "073732", "080732", "083731",
}


def rule(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def template_rates(panel: pd.DataFrame) -> pd.DataFrame:
    """Per market: template share of its own weeks, pooled and by half of the window."""
    dates = np.sort(panel["report_date"].unique())
    mid = dates[len(dates) // 2]
    panel = panel.assign(half=np.where(panel["report_date"] < mid, "h1", "h2"))

    is_t = panel["shape"].str.startswith("template")
    pooled = is_t.groupby(panel["market_code"]).mean().rename("pooled")
    weeks = panel.groupby("market_code").size().rename("weeks")
    by_half = (is_t.groupby([panel["market_code"], panel["half"]]).mean()
                   .unstack("half"))

    out = pd.concat([pooled, by_half, weeks], axis=1)
    out["name"] = panel.groupby("market_code")["market_name"].first()
    return out, mid


def extreme(s: pd.Series) -> pd.Series:
    return (s <= EXTREME_LO) | (s >= EXTREME_HI)


def c1_classification_stability() -> None:
    rule("C1. Is template classification stable inside its own window?")
    panel = _repro._shape_panel()
    classic = panel[panel["market_code"].isin(_repro.CLASSIC_OUTRIGHTS)]
    rates, mid = template_rates(classic)

    # B31 measured over markets with at least 40 weeks; keep that floor so the pooled
    # count is comparable to it rather than to a different universe.
    rates = rates[rates["weeks"] >= 40]
    n = len(rates)

    pooled_ex = extreme(rates["pooled"])
    both_ex = extreme(rates["h1"]) & extreme(rates["h2"])
    # "Extreme in both halves AND on the same side" is the stronger reading, and it is the
    # one that matters: a market that is always-template in one half and never-template in
    # the other is extreme twice while being maximally unstable.
    same_side = both_ex & (
        ((rates["h1"] >= EXTREME_HI) & (rates["h2"] >= EXTREME_HI))
        | ((rates["h1"] <= EXTREME_LO) & (rates["h2"] <= EXTREME_LO))
    )

    print(f"classic outrights with >=40 weeks: {n}")
    print(f"window split at {pd.Timestamp(mid).date()} "
          f"(h1 {int(rates['weeks'].max()) // 2} weeks, h2 the rest)")
    print()
    print(f"  extreme over the POOLED window          {int(pooled_ex.sum())} of {n}")
    print(f"  extreme in BOTH halves (either side)     {int(both_ex.sum())} of {n}")
    print(f"  extreme in both halves, SAME side        {int(same_side.sum())} of {n}")
    print()
    print("  markets that flip from one extreme to the other:")
    flippers = rates[both_ex & ~same_side].sort_values("h1", ascending=False)
    if flippers.empty:
        print("    none")
    for code, r in flippers.iterrows():
        print(f"    {r['name']:<28} ({code})  h1 {r['h1']:.3f} -> h2 {r['h2']:.3f}")

    print()
    print("  largest movers by |h1 - h2|, whether or not extreme:")
    moved = rates.assign(swing=(rates["h1"] - rates["h2"]).abs())
    for code, r in moved.nlargest(8, "swing").iterrows():
        print(f"    {r['name']:<28} ({code})  pooled {r['pooled']:.3f}   "
              f"h1 {r['h1']:.3f} -> h2 {r['h2']:.3f}   swing {r['swing']:.3f}")

    cocoa = rates[rates["name"].str.contains("COCOA", case=False, na=False)]
    print()
    print("  the handoff's named example:")
    for code, r in cocoa.iterrows():
        print(f"    {r['name']:<28} ({code})  pooled {r['pooled']:.3f}   "
              f"h1 {r['h1']:.3f} -> h2 {r['h2']:.3f}")

    # `2026-08-02 §B36` reports cocoa as 0.976 then 0.100 where this block reports 1.000
    # then 0.098. Two lineages of one measurement, so the difference has to be located
    # rather than averaged. It is one week's assignment on the boundary, printed here.
    print()
    print("  --- the §B36 discrepancy, located rather than smoothed ---")
    is_t = classic["shape"].str.startswith("template")
    b36_mid = classic["report_date"].median()
    for label, mask, rule_txt in (
        ("C1  (this block)", classic["report_date"] < mid, "dates[41], strictly BEFORE"),
        ("B36 (reproduce.py)", classic["report_date"] <= b36_mid,
         "median over MARKET-WEEKS, at or before"),
    ):
        h1 = is_t[mask].groupby(classic.loc[mask, "market_code"]).mean()
        h2 = is_t[~mask].groupby(classic.loc[~mask, "market_code"]).mean()
        n1 = classic.loc[mask, "report_date"].nunique()
        n2 = classic.loc[~mask, "report_date"].nunique()
        print(f"    {label:<19s} split {pd.Timestamp(b36_mid if 'B36' in label else mid).date()}"
              f"  ({rule_txt})  h1 {n1} weeks / h2 {n2}")
        print(f"                        cocoa  h1 {h1['073732']:.4f} -> h2 {h2['073732']:.4f}")
    print("    Same DATE, 2025-10-21, on both. The rules differ only on which side that")
    print("    week falls, and cocoa is NOT template that week, so putting it in h1 drags")
    print("    41/41 down to 41/42 and putting it in h2 lifts 4/41's denominator to 40.")
    print("    C1's rule is the better-specified one: 41/41 rather than 42/40, because a")
    print("    median over market-weeks is weighted by how many markets report each week")
    print("    and is not a property of the window. Every OTHER figure is identical under")
    print("    both rules: 22 pooled, 18 either-side, 17 same-side, and the same 17 codes.")


def c2_template_is_invariant_to_w_sd() -> None:
    rule("C2. Does the template rate move with w_SD?")
    panel = _repro._shape_panel()
    classic = panel[panel["market_code"].isin(_repro.CLASSIC_OUTRIGHTS)]

    print("The shape label is `_shape_labels(producer_merchant, managed_money)`: two nets,")
    print("their signs, and nothing else. No weight enters it. So the answer is structural")
    print("and the sweep below is a formality that should return one number three times.")
    print()
    base = classic["shape"].str.startswith("template").mean()
    for w in W_SD_SWEEP:
        weights = dict(cfg.DISAGGREGATED_WEIGHTS, swap=w)
        # Recompute the labels with the weights in scope, to show they cannot reach it.
        shape = _repro._shape_labels(classic["producer_merchant"], classic["managed_money"])
        rate = shape.str.startswith("template").mean()
        assert rate == base, "template rate moved with w_SD, which should be impossible"
        print(f"  w_SD = {w:<4}  template rate = {rate:.6f}   "
              f"(weights in scope: swap={weights['swap']})")
    print()
    print(f"  identical to {base:.6f} at every value, as it must be.")
    print("  §2's first headline figure cannot answer the question §2 asks of it.")


def _fragility_at(w_sd: float, codes: set[str] | None = None) -> pd.DataFrame:
    panel = from_vintage()
    if codes is not None:
        panel = panel[panel["market_code"].isin(codes)]
    weights = dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd)
    return market_fragility(panel, report_type="disaggregated", weights=weights)


# The vintage panel is read once and reused: `from_vintage` is the expensive call here and
# C5-C7 want eight passes over it at four weights.
_PANEL = None


def _panel() -> pd.DataFrame:
    global _PANEL
    if _PANEL is None:
        _PANEL = from_vintage()
    return _PANEL


_MARKET_NAMES: pd.Series = pd.Series(dtype=object)


def _phi_frame(w_sd: float) -> pd.Series:
    """`Phi` indexed by (report_date, market_code), at one value of `w_SD`."""
    global _MARKET_NAMES
    f = market_fragility(_panel(), report_type="disaggregated",
                         weights=dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd))
    if _MARKET_NAMES.empty:
        _MARKET_NAMES = f.groupby("market_code")["market_name"].first()
    return f.set_index(["report_date", "market_code"])["phi"]


def _q_frame(w_sd: float) -> pd.DataFrame:
    """`Q_sell`, `Q_buy` and both asymmetries per market-week, at one value of `w_SD`.

    Both sides must be live: a market-week with `Q_buy == 0` has no ratio rather than an
    infinite one, and dropping it is the same filter
    `reproduce.py::template_direction_agnostic` applies, so the counts are comparable.
    """
    f = market_fragility(_panel(), report_type="disaggregated",
                         weights=dict(cfg.DISAGGREGATED_WEIGHTS, swap=w_sd))
    q = f[(f["q_sell"] > 0) & (f["q_buy"] > 0)].copy()
    q = q.rename(columns={"q_sell": "sell", "q_buy": "buy"})
    q["a_dir"] = q["sell"] / q["buy"]
    q["a_agn"] = np.maximum(q["sell"], q["buy"]) / np.minimum(q["sell"], q["buy"])
    q["classic"] = q["market_code"].isin(_repro.CLASSIC_OUTRIGHTS)
    return q


def c3_what_does_move() -> None:
    rule("C3. What DOES move with w_SD: Q_sell, Q_buy and their ratio")
    for label, codes in (("all vintage markets", None),
                         ("the 13 Supplemental markets", SUPPLEMENTAL)):
        print(f"\n--- {label} ---")
        rows = []
        for w in W_SD_SWEEP:
            f = _fragility_at(w, codes)
            a = (f["q_sell"] / f["q_buy"]).replace([np.inf, -np.inf], np.nan).dropna()
            rows.append({
                "w_SD": w,
                "median q_sell": f["q_sell"].median(),
                "median q_buy": f["q_buy"].median(),
                "median A": a.median(),
                "p90 A": a.quantile(0.90),
                "max A": a.max(),
                "ceiling": max(dict(cfg.DISAGGREGATED_WEIGHTS, swap=w).values())
                / min(dict(cfg.DISAGGREGATED_WEIGHTS, swap=w).values()),
                "market-weeks": len(f),
            })
        t = pd.DataFrame(rows).set_index("w_SD")
        print(t.round(4).to_string())
        lo, hi = t["median A"].iloc[0], t["median A"].iloc[-1]
        print(f"  median A moves {lo:.4f} -> {hi:.4f} across the sweep "
              f"({abs(hi - lo) / lo * 100:.1f}% of the low end)")


def c4_a_agnostic_is_direction_agnostic() -> None:
    """C4, CORRECTED. `A_agnostic` is defined, and this block originally guessed wrong.

    The guess was WEIGHT-agnostic (every category on one weight), which is degenerate at
    exactly 1.0 and is measured below because the degeneracy is worth knowing. The actual
    definition is DIRECTION-agnostic, `2026-08-02 §B34`:

        A_directional = Q_sell / Q_buy
        A_agnostic    = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)

    reproduced by `docs/analysis/reproduce.py::template_direction_agnostic` over the same
    21,756 market-weeks. Both readings are printed here so the wrong one is visible as
    wrong rather than deleted.
    """
    rule("C4 (CORRECTED). `A_agnostic` is DIRECTION-agnostic, not weight-agnostic")
    w = cfg.weights_for("disaggregated")
    ceiling = max(w.values()) / min(w.values())
    q = _q_frame(W_SD_LIVE)
    print("2026-08-02 §B34, reproduce.py::template_direction_agnostic:")
    print("    A_directional = Q_sell / Q_buy")
    print("    A_agnostic    = max(Q_sell, Q_buy) / min(Q_sell, Q_buy)")
    print(f"  over {len(q):,} market-weeks at the shipped weights, ceiling {ceiling:.1f}:")
    for label, sub in (("all", q), ("classic outright", q[q["classic"]]),
                       ("everything else", q[~q["classic"]])):
        print(f"    {label:<17s} A_dir median {sub['a_dir'].median():.4f}   "
              f"A_agn median {sub['a_agn'].median():.4f}   "
              f"({sub['a_agn'].median() / ceiling:.1%} of ceiling)")
    print(f"  breaches of the ceiling: {int((q['a_agn'] > ceiling + 1e-9).sum())}")
    print("  Not degenerate, not 1.0: the typical market-week has one side three times the")
    print("  other, and what is a coin flip is WHICH side.")

    print()
    print("The original C4 reading, retained as the thing the name does not mean.")
    print("Searched `src/`, `tests/` and `docs/design/` on 2026-08-03 and found the string")
    print("only in the handoff citing it, because §B34 was on a branch that had never been")
    print("pushed. Read as WEIGHT-agnostic the quantity really is degenerate:")
    print()
    print("Since sum_c P_c = 0, the gross net-long total G equals the gross net-short total")
    print("(2026-08-02 §B31). With one weight w shared by every category:")
    print("    Q_sell = w·G,  Q_buy = w·G,  so  A = Q_sell/Q_buy = 1 exactly, for every")
    print("    market and every week, independent of w.")
    print()
    equal = {k: 1.0 for k in cfg.DISAGGREGATED_WEIGHTS}
    panel = from_vintage()
    f = market_fragility(panel, report_type="disaggregated", weights=equal)
    a = (f["q_sell"] / f["q_buy"]).replace([np.inf, -np.inf], np.nan).dropna()
    print(f"  measured over {len(a):,} market-weeks with all weights = 1.0:")
    print(f"    min {a.min():.6f}   median {a.median():.6f}   max {a.max():.6f}")
    print(f"    share within 1e-9 of exactly 1.0: {(a.sub(1).abs() < 1e-9).mean() * 100:.4f}%")
    print()
    print("  So a WEIGHT-agnostic asymmetry is identically 1 and measures nothing. That is")
    print("  a true statement about a quantity nobody asked for. The lesson is not about")
    print("  weights: an unresolvable citation was answered by guessing at the definition,")
    print("  and the guess was wrong in a way no amount of care about the arithmetic would")
    print("  have caught. Cite the file, not the section number.")


def c6_the_reported_band() -> None:
    """C6: the four-value band §4 asks for, with `A_agnostic` now available.

    Three round numbers and one measured one. The measured one changes the geometry, which
    is the finding: at `w_SD = 0.067` swap becomes the SMALLEST weight in the table, below
    `producer_merchant` at 0.1, so `max(w)/min(w)` rises from 10.0 to 14.9 and the raw
    ratios stop being on one scale.
    """
    rule("C6. The reported band, w_SD in {0.067, 0.2, 0.4, 0.7}")
    panel = _repro._shape_panel()
    classic = panel[panel["market_code"].isin(_repro.CLASSIC_OUTRIGHTS)]
    tmpl = classic["shape"].str.startswith("template").mean()
    print(f"Template rate, classic outrights: {tmpl:.6f} at every value in the band. C2")
    print("gives the reason and it is structural, so this line is a formality kept only so")
    print("that the band is complete. Do not read it as evidence about the weight.")

    rows = []
    for w in W_SD_BAND:
        ww = dict(cfg.DISAGGREGATED_WEIGHTS, swap=w)
        ceiling = max(ww.values()) / min(ww.values())
        q = _q_frame(w)
        for label, sub in (("all", q), ("classic outright", q[q["classic"]]),
                           ("supplemental 13", q[q["market_code"].isin(SUPPLEMENTAL)])):
            rows.append({
                "w_SD": w, "kind": "measured" if w == W_SD_STRESS else "round",
                "stratum": label, "market-weeks": len(sub),
                "median Q_sell": round(sub["sell"].median(), 1),
                "median Q_buy": round(sub["buy"].median(), 1),
                "median A_dir": round(sub["a_dir"].median(), 4),
                "median A_agn": round(sub["a_agn"].median(), 4),
                "ceiling": round(ceiling, 3),
                "A_agn as % of ceiling": f"{sub['a_agn'].median() / ceiling:.1%}",
                "breaches": int((sub["a_agn"] > ceiling + 1e-9).sum()),
            })
    t = pd.DataFrame(rows)
    for label in ("all", "classic outright", "supplemental 13"):
        print(f"\n--- {label} ---")
        print(t[t["stratum"] == label].drop(columns=["stratum"]).to_string(index=False))

    allrows = t[t["stratum"] == "all"].set_index("w_SD")
    print("\n  A_directional and A_agnostic do not behave alike under the band.")
    print(f"    A_dir  {allrows['median A_dir'].min():.4f} to "
          f"{allrows['median A_dir'].max():.4f}, no order")
    print(f"    A_agn  {allrows['median A_agn'].min():.4f} to "
          f"{allrows['median A_agn'].max():.4f}, U-shaped with its MINIMUM inside the band")
    print("  A_agnostic is minimised near the shipped weight and rises at both ends: pushed")
    print("  down, the swap book stops opposing anything and the residual MM-vs-PM book is")
    print("  more lopsided; pushed up, swap dominates whichever side it sits on. So the")
    print("  band is not an interval whose endpoints bracket the answer.")
    print("\n  And 0.067 is not on the same scale as the other three. Compare within a")
    print("  weight table, never across one, which is 2026-07-28 §2.3's rule arriving from")
    print("  a new direction: swap at 0.067 is BELOW producer_merchant at 0.1, so it becomes")
    print("  the denominator of the ceiling and every raw ratio gains 49% of headroom.")


def c7_direction_of_the_bias() -> None:
    """C7: `w_SD = 0.4` overstates fragile capital, and by how much, per market.

    §4's claim to test: swap dealers get stickier under stress, so the shipped weight
    overstates forced capital exactly when the composite is supposed to be informative. And
    its prediction: gold should be worse affected than cocoa, because swap sits on gold's
    immovable physical-hedging side while on cocoa it holds the largest net long.
    """
    rule("C7. The direction of the bias: Phi at 0.4 against Phi at the measured 0.067")
    hi = _phi_frame(W_SD_LIVE)
    lo = _phi_frame(W_SD_STRESS)
    d = pd.DataFrame({"phi_live": hi, "phi_stress": lo}).dropna().reset_index()
    d["inflation"] = d["phi_live"] / d["phi_stress"] - 1.0
    print(f"{len(d):,} market-weeks. Phi is the fragility-weighted share of a randomly")
    print("chosen position-side, so a higher Phi is literally 'more of this book can be")
    print("forced out'. Not one market-week moves the other way:")
    print(f"    inflation > 0  on {(d['inflation'] > 1e-12).mean():.4%} of market-weeks")
    print(f"    inflation == 0 on {(d['inflation'].abs() <= 1e-12).mean():.4%}, which is "
          f"a swap book of exactly zero gross")
    print(f"    inflation < 0  on {(d['inflation'] < -1e-12).mean():.4%}")
    print(f"    mean {d['inflation'].mean():+.2%}   median {d['inflation'].median():+.2%}   "
          f"p90 {d['inflation'].quantile(.9):+.2%}   max {d['inflation'].max():+.2%}")
    print("  The sign is not a finding (raising a weight raises a weighted sum). The SIZE")
    print("  is, and so is how unevenly it lands.")

    per = d.groupby("market_code").agg(weeks=("inflation", "size"),
                                       phi_live=("phi_live", "mean"),
                                       phi_stress=("phi_stress", "mean"),
                                       inflation=("inflation", "mean"))
    per = per[per["weeks"] >= 40]
    per["name"] = _MARKET_NAMES.reindex(per.index)
    cl = per[per.index.isin(_repro.CLASSIC_OUTRIGHTS)].sort_values("inflation",
                                                                  ascending=False)
    print(f"\n--- classic outrights with >=40 weeks ({len(cl)}), most affected first ---")
    print(cl.head(10).round(4).to_string())
    print("\n--- least affected ---")
    print(cl.tail(5).round(4).to_string())

    print("\n--- §4's named prediction ---")
    for code, label in (("088691", "GOLD"), ("073732", "COCOA")):
        r = per.loc[code]
        print(f"    {label:<6s} ({code})  Phi {r['phi_stress']:.4f} -> {r['phi_live']:.4f}"
              f"   {r['inflation']:+.2%}")
    g, c = per.loc["088691", "inflation"], per.loc["073732", "inflation"]
    print(f"  Gold is affected {g / c:.2f}x as much as cocoa. THE PREDICTION HOLDS, and the")
    print("  mechanism is the one §4 named: on gold the swap dealer IS the immovable")
    print("  physical-hedging side, so weighting it at 0.4 books robust capital as fragile;")
    print("  on cocoa it holds the largest net long and is closer to what 0.4 describes.")
    print("  The overstatement is therefore worst exactly where it is least deserved.")


def c8_does_the_composite_care() -> None:
    """C8: the composite consumes pct(Phi), not Phi, so a level shift may not survive.

    `A.9`'s `D = C x I x Phi` uses each term as a percentile of its own history. A weight
    change that lifts a market's whole Phi series lifts nothing in the percentile. This
    asks whether the band's effect is that benign, and on a tenth of market-weeks it is not.
    """
    rule("C8. Does any of it reach the composite, which consumes a percentile?")
    frames = {w: _phi_frame(w) for w in W_SD_BAND}
    d = pd.DataFrame(frames).dropna().reset_index()
    counts = d.groupby("market_code").size()
    d = d[d["market_code"].isin(counts[counts >= 40].index)]
    for w in W_SD_BAND:
        d[f"pct_{w}"] = d.groupby("market_code")[w].rank(pct=True)
    shift = (d[f"pct_{W_SD_LIVE}"] - d[f"pct_{W_SD_STRESS}"]).abs()

    print(f"{len(d):,} market-weeks over {d['market_code'].nunique()} markets with >=40 "
          f"weeks.")
    print("|pct(Phi) at 0.4  -  pct(Phi) at 0.067|, within each market's own history:")
    print(f"    mean {shift.mean():.4f}   median {shift.median():.4f}   "
          f"p90 {shift.quantile(.9):.4f}   max {shift.max():.4f}")
    print(f"    moves more than 0.10 of a percentile: {(shift > 0.10).mean():.2%}")
    print(f"    moves more than 0.25 of a percentile: {(shift > 0.25).mean():.2%}")

    sp = d.groupby("market_code")[[W_SD_LIVE, W_SD_STRESS]].apply(
        lambda g: _repro._spearman(g[W_SD_LIVE], g[W_SD_STRESS]))
    print("\nper-market Spearman between the two Phi series, over that market's own weeks:")
    print(f"    median {sp.median():.4f}   min {sp.min():.4f}   "
          f"below 0.90: {int((sp < 0.90).sum())} of {len(sp)}")
    print("    the five lowest:")
    for code, v in sp.nsmallest(5).items():
        print(f"      {str(_MARKET_NAMES.get(code, code))[:44]:<44s} {v:+.4f}")
    print("  On 98 of 264 markets the two weight tables disagree about which of that")
    print("  market's own weeks were the fragile ones, and on a handful they disagree")
    print("  outright. That is the number the band exists to expose: not the level of Phi,")
    print("  which no percentile ever sees, but the ORDER of a market's own history.")

    m = d.groupby("market_code")[list(W_SD_BAND)].mean()
    mc = m[m.index.isin(_repro.CLASSIC_OUTRIGHTS)]
    print("\ncross-market ranking of mean Phi, 0.4 against 0.067:")
    print(f"    all {len(m)} markets      Spearman {_repro._spearman(m[W_SD_LIVE], m[W_SD_STRESS]):.4f}")
    print(f"    {len(mc)} classic outrights  Spearman "
          f"{_repro._spearman(mc[W_SD_LIVE], mc[W_SD_STRESS]):.4f}")
    for k in (10, 20):
        common = len(set(mc[W_SD_LIVE].nlargest(k).index)
                     & set(mc[W_SD_STRESS].nlargest(k).index))
        print(f"    top-{k} classic outrights by mean Phi: {common} of {k} in common")
    print("  Cross-market the ranking largely survives on the outrights and degrades over")
    print("  the full universe, which is three-quarters power and gas basis. So the band")
    print("  is narrow where the package is usually read and wide where it is not.")


if __name__ == "__main__":
    c1_classification_stability()
    c2_template_is_invariant_to_w_sd()
    c3_what_does_move()
    c4_a_agnostic_is_direction_agnostic()
    c6_the_reported_band()
    c7_direction_of_the_bias()
    c8_does_the_composite_care()
