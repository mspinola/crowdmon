"""How much of a fragility result is the weights? Module spec §6.3 and appendix §A.11.

Both documents ask for this and neither had been run. §6.3: weights are "configured,
documented as judgement, and subjected to sensitivity analysis rather than presented as
estimates". §A.11, listing known biases: "`w_c` are judgement, not estimates. The fragility
weights are configured, not fitted, and results should be reported with sensitivity analysis
across plausible weightings."

Four analyses in `docs/analysis/` rank markets on `Phi`, `Q_sell` or `D` without one. This
module is that debt.

## What "plausible" means, and why flat weights are not

The judgement in §6.3's table is an **ordering** before it is a set of values. A levered fund
is more forceable than a retail account, which is more forceable than a swap dealer, which is
more forceable than a producer hedging physical. The confidence in that ranking is much
higher than the confidence that Managed Money is exactly 1.0 and Swap Dealer exactly 0.4.

So the plausible class here is **order-preserving jitter**: move every weight by a random
amount, keep them in `[0, 1]`, and reject any draw that reorders the categories. A weighting
that says producers are more forceable than levered funds is not a rival judgement, it is a
different claim, and averaging over it would answer a question nobody asked.

Order-violating weightings are still worth reporting as **reference points** rather than as
plausible alternatives, which is what `REFERENCE_WEIGHTINGS` is for.

## The flat baseline is degenerate, algebraically

Setting every weight to 1.0 looks like the natural null. It is not, and the reason is an
identity rather than an empirical fact. In the Disaggregated report the category rows exclude
spreading, so

    sum_c (L_c + S_c) = 2 . (OI - spreading)

and therefore

    Phi_flat = 2 . (OI - spreading) / (2 . OI) = 1 - spreading / OI

which depends on nothing except the spreading share. Measured on the latest week the median
is 0.942, and the cross-sectional variation that remains is variation in spreading, not in
positioning.

**So `Phi` carries no cross-market information independent of the weight table.** It is not a
measurement that the weights adjust; it is a weighted restatement of the category mix. That
is worth knowing before reading any `Phi` ranking, and it is why the flat case is excluded
from the plausible set rather than used as a null. `flat_phi_identity` checks the algebra
against real data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import config as cfg
from .fragility import market_fragility
from .pressure import rank_markets, top_by

#: Named weightings that do NOT preserve the §6.3 ordering. Reported as reference points, and
#: deliberately kept out of the plausible set: each answers a different question rather than
#: offering a rival judgement about the same one.
REFERENCE_WEIGHTINGS = {
    "flat": "every category 1.0. Degenerate, see `flat_phi_identity`",
    "crowd_only": "the weight-1.0 category alone, everything else 0",
    "inverted": "the §6.3 ordering reversed. A wrongness check, not an alternative",
}


class SensitivityError(ValueError):
    """The sweep cannot be run as asked."""


def plausible_variants(weights: dict[str, float] | None = None, *, n: int = 200,
                       jitter: float = 0.15, seed: int = 0,
                       floor: float = 0.02) -> list[dict[str, float]]:
    """`n` order-preserving perturbations of the configured weights.

    Each weight is moved by a uniform draw in `[-jitter, +jitter]`, clipped into
    `[floor, 1]`, and the draw is rejected and retried unless the resulting order matches the
    original. `floor` keeps a category from being zeroed out entirely, which would silently
    turn a perturbation into a category exclusion.

    Deterministic given `seed`, because a sensitivity result that cannot be reproduced is not
    evidence of anything.
    """
    base = dict(weights or cfg.DISAGGREGATED_WEIGHTS)
    if not 0 < jitter <= 0.5:
        raise SensitivityError(f"jitter must be in (0, 0.5], got {jitter}")
    order = [k for k, _ in sorted(base.items(), key=lambda kv: -kv[1])]
    rng = np.random.default_rng(seed)

    out: list[dict[str, float]] = []
    attempts = 0
    while len(out) < n:
        attempts += 1
        if attempts > 200 * n:
            raise SensitivityError(
                f"could only build {len(out)} of {n} order-preserving variants in "
                f"{attempts} draws at jitter={jitter}. The configured weights are too "
                f"closely spaced for that much movement to keep their ordering.")
        draw = {k: float(np.clip(v + rng.uniform(-jitter, jitter), floor, 1.0))
                for k, v in base.items()}
        if [k for k, _ in sorted(draw.items(), key=lambda kv: -kv[1])] == order:
            out.append(draw)
    return out


def reference_variants(weights: dict[str, float] | None = None,
                       crowd_category: str = "managed_money") -> dict[str, dict[str, float]]:
    """The named order-violating weightings, for reporting beside the plausible sweep."""
    base = dict(weights or cfg.DISAGGREGATED_WEIGHTS)
    ranked = sorted(base.items(), key=lambda kv: -kv[1])
    inverted = {k: v for (k, _), (_, v) in zip(ranked, reversed(ranked))}
    return {
        "flat": {k: 1.0 for k in base},
        "crowd_only": {k: (1.0 if k == crowd_category else 0.0) for k in base},
        "inverted": inverted,
    }


def sweep(panel: pd.DataFrame, variants, *, column: str = "q_sell_over_oi",
          top_n: int = 10, baseline: dict[str, float] | None = None) -> pd.DataFrame:
    """Re-rank the panel under each weighting and measure the movement against the baseline.

    Three numbers per variant, because they fail in different ways:

    - `top_n_overlap` — how many of the baseline's top `n` survive. What a reader of a
      published table actually cares about.
    - `rank_corr` — Spearman across every market. Catches wholesale reordering that a stable
      top-10 would hide.
    - `phi_corr` — Pearson on `Phi` itself, which isolates the weights' effect from the
      positioning the ranking column also depends on.
    """
    base_weights = dict(baseline or cfg.DISAGGREGATED_WEIGHTS)
    ref = rank_markets(market_fragility(panel, weights=base_weights))
    if column not in ref.columns:
        raise SensitivityError(f"cannot rank on {column!r}; have {sorted(ref.columns)}")
    ref_top = set(top_by(ref, column, n=top_n)["market_code"])
    ref_rank = ref.set_index("market_code")[column]
    ref_phi = ref.set_index("market_code")["phi"]

    named = variants.items() if isinstance(variants, dict) else enumerate(variants)
    rows = []
    for label, weights in named:
        got = rank_markets(market_fragility(panel, weights=weights))
        got_rank = got.set_index("market_code")[column]
        got_phi = got.set_index("market_code")["phi"]
        rows.append({
            "variant": label,
            "median_phi": float(got["phi"].median()),
            "top_n_overlap": len(set(top_by(got, column, n=top_n)["market_code"]) & ref_top),
            "rank_corr": _spearman(ref_rank, got_rank),
            "phi_corr": float(ref_phi.corr(got_phi)),
        })
    return pd.DataFrame(rows)


def _spearman(a: pd.Series, b: pd.Series) -> float:
    """Spearman as Pearson on ranks, which is its definition.

    `Series.corr(method="spearman")` delegates to scipy, and scipy is not a dependency of
    this package: `tests/test_boundaries.py` allowlists pandas, numpy, pyarrow and the two
    siblings, and a new dependency belongs in `pyproject.toml` as a deliberate choice rather
    than arriving through a keyword argument. Ranking first and taking Pearson needs neither.
    """
    joined = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(joined) < 2:
        return float("nan")
    left, right = joined.iloc[:, 0].rank(), joined.iloc[:, 1].rank()
    return float(left.corr(right))


def summarise(swept: pd.DataFrame, *, top_n: int = 10) -> pd.Series:
    """Reduce a plausible sweep to the numbers a caption needs."""
    return pd.Series({
        "variants": len(swept),
        "top_n_overlap_min": swept["top_n_overlap"].min(),
        "top_n_overlap_median": swept["top_n_overlap"].median(),
        "top_n_overlap_p05": swept["top_n_overlap"].quantile(0.05),
        "rank_corr_min": swept["rank_corr"].min(),
        "rank_corr_median": swept["rank_corr"].median(),
        "phi_corr_min": swept["phi_corr"].min(),
        "phi_corr_median": swept["phi_corr"].median(),
        "worst_case_top_n_lost": top_n - swept["top_n_overlap"].min(),
    })


def flat_phi_identity(panel: pd.DataFrame) -> pd.DataFrame:
    """Check `Phi_flat == 1 - spreading/OI` against real data, per market-week.

    The algebra is in the module docstring; this is the check that the schema actually obeys
    it, which is the same identity `io.oi_identity` verifies from the other direction. If it
    holds, `Phi` under equal weights measures the spreading share and nothing else, and every
    cross-market difference in a real `Phi` is the weight table speaking.
    """
    flat = market_fragility(panel, weights={c: 1.0 for c in panel["category"].unique()})
    oi = pd.to_numeric(flat["open_interest"], errors="coerce")
    spread = pd.to_numeric(flat["spread_total"], errors="coerce")
    out = flat[["report_date", "market_code", "phi"]].copy()
    out["predicted"] = 1.0 - (spread / oi)
    out["residual"] = out["phi"] - out["predicted"]
    return out
