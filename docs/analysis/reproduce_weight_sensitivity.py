"""Reproducer for every figure in 2026-07-28-weight-sensitivity.md.

    COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_weight_sensitivity.py

Deterministic given the seeds below. Module spec §6.3 and appendix §A.11 both require this
and neither had been run; four analyses in this directory rank on `Phi`, `Q_sell` or `D`
without it.
"""
import warnings

import pandas as pd

from crowdmon.core import config as cfg
from crowdmon.core.report import to_markdown
from crowdmon.futures import (
    flat_phi_identity,
    from_current_store,
    latest,
    plausible_variants,
    reference_variants,
    summarise,
    sweep,
)

SEED = 0
N_VARIANTS = 200
JITTER = 0.15

#: The rankings actually published in docs/analysis/, so the sweep answers the question a
#: reader of those documents would ask rather than a generic one.
PUBLISHED_RANKINGS = ["q_sell_over_oi", "q_buy_over_oi", "phi"]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    warnings.filterwarnings("ignore")
    pd.set_option("display.width", 235)

    cross = latest()
    week = cross["report_date"].max().date()

    rule(f"1. THE CONFIGURED WEIGHTS — {len(cross['market_code'].unique())} markets, {week}")
    print(pd.Series(cfg.DISAGGREGATED_WEIGHTS).sort_values(ascending=False).to_string())
    print("\nThe judgement is an ORDERING before it is a set of values, so the plausible")
    print("class below is order-preserving jitter.")

    rule("2. THE FLAT BASELINE IS DEGENERATE, ALGEBRAICALLY")
    print("sum_c (L_c + S_c) = 2(OI - spreading), so Phi_flat = 1 - spreading/OI\n")
    identity = flat_phi_identity(cross)
    print(f"  market-weeks checked : {len(identity):,}")
    print(f"  max |residual|       : {identity['residual'].abs().max():.2e}")
    print(f"  median Phi_flat      : {identity['phi'].median():.4f}")
    print(f"  std  Phi_flat        : {identity['phi'].std():.4f}")
    print("\n  Under equal weights Phi measures the spreading share and nothing else, so")
    print("  every cross-market difference in a real Phi comes from the weight table.")

    history = flat_phi_identity(from_current_store())
    print(f"\n  same check over twenty years ({len(history):,} market-weeks): "
          f"max |residual| {history['residual'].abs().max():.2e}")

    rule("3. REFERENCE WEIGHTINGS — order-violating, reported not swept")
    print(to_markdown(sweep(cross, reference_variants()).round(4)))
    print("\n`inverted` is the wrongness check: if reversing §6.3's judgement left the")
    print("ranking intact, the weights would not be doing anything.")

    rule(f"4. THE PLAUSIBLE SWEEP — {N_VARIANTS} order-preserving variants, "
         f"jitter +/-{JITTER}")
    variants = plausible_variants(n=N_VARIANTS, jitter=JITTER, seed=SEED)
    for column in PUBLISHED_RANKINGS:
        swept = sweep(cross, variants, column=column)
        print(f"\n--- ranking on {column} ---")
        print(summarise(swept).round(4).to_string())
        counts = swept["top_n_overlap"].value_counts().sort_index()
        print(f"  top-10 overlap distribution: {counts.to_dict()}")

    rule("5. HOW FAR DOES A SINGLE WEIGHT HAVE TO MOVE TO MATTER?")
    print("one weight at a time, everything else held at the configured value\n")
    rows = {}
    for category, base in sorted(cfg.DISAGGREGATED_WEIGHTS.items(), key=lambda kv: -kv[1]):
        for delta in (-0.2, -0.1, 0.1, 0.2):
            value = round(min(max(base + delta, 0.02), 1.0), 3)
            if value == base:
                continue
            label = f"{category} {base} -> {value}"
            rows[label] = {**cfg.DISAGGREGATED_WEIGHTS, category: value}
    one_at_a_time = sweep(cross, rows).sort_values("phi_corr")
    print(to_markdown(one_at_a_time.round(4)))

    rule("6. DOES THE ANSWER DEPEND ON THE WEEK?")
    panel = from_current_store()
    variants_small = plausible_variants(n=40, jitter=JITTER, seed=SEED)
    for stamp in ("2012-06-26", "2018-06-26", "2026-07-28"):
        one_week = panel[panel["report_date"] == stamp]
        if one_week.empty:
            continue
        swept = sweep(one_week, variants_small, top_n=5)
        summary = summarise(swept, top_n=5)
        print(f"  {stamp}  top-5 overlap min {summary['top_n_overlap_min']:.0f}/5  "
              f"median {summary['top_n_overlap_median']:.0f}/5  "
              f"rank corr min {summary['rank_corr_min']:.3f}")


if __name__ == "__main__":
    main()
