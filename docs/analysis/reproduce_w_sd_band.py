#!/usr/bin/env python3
"""The `w_SD` band sweep: 0.067 to 0.7, both populations, both quantities.

Extends `2026-08-03 §C3`, which swept {0.2, 0.4, 0.7}. The band here is the one the regime
finding implies: **0.067** is swap's measured stress-week behaviour against Managed Money at
1.0, **0.305** is its routine-turnover behaviour, and 0.7 is the top of §C3's grid.

Two quantities, because only one of them can answer:

- the **template rate**, which `2026-08-03 §C2` establishes cannot respond to `w_SD` at all.
  Swept over the wider band anyway, since the structural claim is cheap to re-check and the
  question has now been asked twice.
- **`A = Q_sell/Q_buy`**, which is weight-dependent by construction.

Runs through `weight_sensitivity.single_weight_sweep` rather than re-deriving the sweep, so
that this script and `§C3`'s cannot drift apart.

    COTDATA_STORE=$HOME/code/cotdata_store python docs/analysis/reproduce_w_sd_band.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

from crowdmon.core import config as cfg
from crowdmon.futures import from_vintage
from crowdmon.futures.weight_sensitivity import single_weight_sweep

# Same import dance as reproduce_template_stability.py, and for the same reason: reproduce.py
# owns the shape rule and the hand-drawn CLASSIC_OUTRIGHTS list, and a second copy would be a
# second thing to keep in step with B31's pinned figures.
_spec = importlib.util.spec_from_file_location(
    "_repro", Path(__file__).with_name("reproduce.py"))
_repro = importlib.util.module_from_spec(_spec)
sys.modules["_repro"] = _repro
_spec.loader.exec_module(_repro)

#: The band. 0.067 is the stress-week reading, 0.1 is `producer_merchant` exactly (the
#: ordering boundary), 0.305 is the routine-turnover reading, 0.4 is live, 0.7 tops §C3.
BAND = (0.067, 0.1, 0.2, 0.305, 0.4, 0.55, 0.7)

#: The 13 Supplemental markets, as 6-digit CFTC codes. Copied from
#: reproduce_template_stability.py so the two populations are literally the same set.
SUPPLEMENTAL = {
    "001602", "001612", "002602", "005602", "007601", "026603", "033661",
    "054642", "057642", "061641", "073732", "080732", "083731",
}


def rule(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def template_rate_across_the_band(panel: pd.DataFrame) -> None:
    """§C2 over the full band. The rate cannot move, and this shows that it does not."""
    rule("Template rate across the full 0.067-0.7 band (extends C2's {0.2, 0.4, 0.7})")
    print("The label is `_shape_labels(producer_merchant, managed_money)`: two category")
    print("nets and their signs. `swap` is not one of the two, and no weight of any kind")
    print("enters the rule, so the rate is invariant to `w_SD` BY CONSTRUCTION.\n")

    shaped = _repro._shape_panel()
    classic = shaped[shaped["market_code"].isin(_repro.CLASSIC_OUTRIGHTS)]

    print(f"{'w_SD':>8}  {'template rate':>14}")
    rates = []
    for w in BAND:
        # Recomputed inside the loop precisely so that a dependence, if one existed, could
        # show up. Threading `w` through the shape rule is impossible: it takes two Series.
        del w
        rate = (_repro._shape_labels(classic["producer_merchant"],
                                     classic["managed_money"])
                .str.startswith("template").mean())
        rates.append(rate)
    for w, rate in zip(BAND, rates):
        print(f"{w:>8}  {rate:>14.6f}")

    spread = max(rates) - min(rates)
    print(f"\nSpread across the band: {spread:.9f}")
    print("Zero, to every figure pandas will print. This is not an insensitivity that")
    print("licenses an inference about the weight: a quantity that CANNOT respond to a")
    print("parameter is not evidence about that parameter (C2). See the next block for one")
    print("that can.")


def asymmetry_across_the_band(panel: pd.DataFrame) -> None:
    """§C3 over the full band, both populations, with the ordering flagged."""
    rule("A = Q_sell/Q_buy across the full band, via single_weight_sweep")
    for label, codes in (("all vintage market-weeks", None),
                         ("the 13 Supplemental markets", SUPPLEMENTAL)):
        sub = panel if codes is None else panel[panel["market_code"].isin(codes)]
        swept = single_weight_sweep(sub, "swap", BAND)
        print(f"\n--- {label} ---\n")
        cols = ["value", "median_q_sell", "median_q_buy", "median_a", "p90_a",
                "weight_ceiling", "preserves_order", "ties_with", "crosses"]
        print(swept[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

        ok = swept[swept["preserves_order"]]
        lo, hi = ok["median_a"].min(), ok["median_a"].max()
        print(f"\n  order-preserving part of the band: w_SD in "
              f"[{ok['value'].min()}, {ok['value'].max()}], median A {lo:.4f} to {hi:.4f}, "
              f"a swing of {(hi / lo - 1) * 100:.1f}%")
        bad = swept[~swept["preserves_order"]]
        if not bad.empty:
            for _, b in bad.iterrows():
                # `or` is wrong here: a missing cell is NaN, and NaN is truthy, so the
                # fallback never fires and the reason prints as "nan".
                why = (b["crosses"] if not pd.isna(b["crosses"]) else
                       f"ties with {b['ties_with']}, which COLLAPSES the distinction "
                       f"rather than reweighting it")
                print(f"  OUTSIDE the plausible class at w_SD={b['value']}: {why}")
            full_lo = swept["median_a"].min()
            full_hi = swept["median_a"].max()
            print(f"  including them, median A spans {full_lo:.4f} to {full_hi:.4f} "
                  f"({(full_hi / full_lo - 1) * 100:.1f}%), but those rows are a different "
                  f"claim rather than a rival value (A22)")


if __name__ == "__main__":
    panel = from_vintage(report_type="disaggregated")
    print("# w_SD band sweep\n")
    print(f"Panel: {len(panel):,} rows, {panel['market_code'].nunique()} markets, "
          f"{panel['report_date'].min().date()} to {panel['report_date'].max().date()}")
    print(f"Live weight table: {cfg.DISAGGREGATED_WEIGHTS}")
    template_rate_across_the_band(panel)
    asymmetry_across_the_band(panel)
