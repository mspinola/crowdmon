"""Reproduce `amendments-2026-08-03.md` §C1-C4.

The baseline the index-share handoff's §2 cites as "§B33-B36". Those sections were cited
before they existed; this is the measurement that establishes them. Run from the repo root:

    COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce_template_stability.py

Four questions, in the order they have to be asked:

C1  Is template classification stable within its own window? §3 of the handoff asserts it is
    not, citing figures that exist nowhere. Measured here by splitting the 82 weeks in half.
C2  Does the template rate move with `w_SD` at all? §2 asks for it to be recomputed across
    three values. It cannot move, and the reason is structural rather than empirical.
C3  What DOES move with `w_SD`: `Q_sell`, `Q_buy`, and their ratio.
C4  `A_agnostic` has no definition in this package. What a defensible one would measure, and
    why the obvious reading is degenerate.
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


def c4_a_agnostic_is_undefined() -> None:
    rule("C4. `A_agnostic` has no definition in this package")
    print("Searched `src/`, `tests/` and `docs/design/`: the string appears only in the")
    print("handoff that cites it. The obvious reading is degenerate, which is worth showing")
    print("rather than asserting.")
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
    print("  So a weight-agnostic asymmetry is identically 1 and measures nothing. Any")
    print("  useful `A_agnostic` has to be a different quantity, and choosing one is a")
    print("  design decision rather than a measurement. Not invented here.")


if __name__ == "__main__":
    c1_classification_stability()
    c2_template_is_invariant_to_w_sd()
    c3_what_does_move()
    c4_a_agnostic_is_undefined()
