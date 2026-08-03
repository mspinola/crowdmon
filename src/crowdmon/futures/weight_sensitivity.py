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


def single_weight_sweep(panel: pd.DataFrame, category: str, values,
                        *, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Hold the weight table, move ONE weight over a stated grid, report the level.

    `sweep` above answers a different question and cannot be made to answer this one. It
    jitters **every** weight at once and reports rank *stability* (`top_n_overlap`,
    `rank_corr`), which is the right shape for "does a published ranking survive the table
    being wrong". It is the wrong shape for "how far does the headline number move when this
    one weight moves over the range anyone would actually argue for", because a rank
    correlation is invariant to exactly the monotone rescaling a single weight induces.

    Written because that question has now been asked twice and answered ad-hoc both times:
    `2026-08-01 §A22` for `producer_merchant` (0.1 to 0.3) and `2026-08-03 §C3` for `swap`
    (0.2 to 0.7), each in a throwaway script. Twice ad-hoc is a missing function.

    One row per value, with `Q_sell`, `Q_buy` and their ratio `A` as **medians over
    market-weeks** of whatever panel is passed. Subset the panel before calling: §C3's whole
    finding is that the answer differs by population (0.6% pooled, 42.0% on the Supplemental
    13), so the population is an input to this measurement and not context around it.

    ## `preserves_order` is the column to read first

    §6.3's judgement is an **ordering** before it is a set of values, and `2026-08-01 §A22`
    measured what that distinction is worth: order-preserving jitter keeps at least 7 of the
    `Q_sell/OI` top 10, while inverting the ordering destroys it entirely (0 of 10, rank
    correlation -0.045). So a swept value that reorders the table is not a rival judgement
    about the same question, it is a different claim, and a level read off one is not
    comparable to the levels either side of it.

    This is not hypothetical for the sweep that motivated the function. `swap` sits at 0.4
    with `producer_merchant` at 0.1 beneath it, so any `w_SD < 0.1` says a swap dealer is
    **less** forceable than a producer hedging physical, which is a claim about holder
    behaviour that nobody has made. The flag is reported rather than raised, because seeing
    where the band leaves the plausible class is the point.
    """
    base = dict(weights or cfg.DISAGGREGATED_WEIGHTS)
    if category not in base:
        raise SensitivityError(
            f"{category!r} is not a weighted category; have {sorted(base)}. A typo here "
            f"would otherwise sweep a weight nothing reads and report a flat line, which "
            f"is indistinguishable from a genuine insensitivity.")
    values = [float(v) for v in values]
    if not values:
        raise SensitivityError("no values to sweep")
    if bad := sorted(v for v in values if not v > 0):
        raise SensitivityError(
            f"weights must be positive; got {bad}. Zero is not a small weight, it deletes "
            f"the category from `Q_sell` while leaving it in `2·OI`, and it makes "
            f"`weight_ceiling` undefined rather than large. A negative weight asserts that "
            f"a category ABSORBS forced flow, which is not a claim this table can express. "
            f"Both slip past `preserves_order`, which reports position and not sign.")

    others = {k: v for k, v in base.items() if k != category}
    order = [k for k, _ in sorted(base.items(), key=lambda kv: -kv[1])]

    rows = []
    for value in values:
        trial = dict(base, **{category: value})
        frag = market_fragility(panel, weights=trial)
        q_sell = pd.to_numeric(frag["q_sell"], errors="coerce")
        q_buy = pd.to_numeric(frag["q_buy"], errors="coerce")
        a = (q_sell / q_buy).where(q_buy > 0)
        rows.append({
            "category": category,
            "value": value,
            "median_q_sell": float(q_sell.median()),
            "median_q_buy": float(q_buy.median()),
            "median_a": float(a.median()),
            "p90_a": float(a.quantile(0.90)),
            "market_weeks": int(len(frag)),
            # max(w)/min(w). Reported because a level that moves only because the spread of
            # the table widened is a ceiling artifact rather than a measurement, which
            # `2026-08-02 §B31` warns is easy to mistake for one.
            "weight_ceiling": max(trial.values()) / min(trial.values()),
            "preserves_order": (
                [k for k, _ in sorted(trial.items(), key=lambda kv: -kv[1])] == order
                and not _tied_with(value, others)),
            "ties_with": ", ".join(_tied_with(value, others)) or None,
            "crosses": _crossed(base[category], value, others),
        })
    return pd.DataFrame(rows)


def _tied_with(value: float, others: dict[str, float]) -> list[str]:
    """Categories this value lands exactly on, which is neither preserved nor violated.

    A tie fails `preserves_order` here **deliberately**, and the reason is that a stable
    sort hides it: at `w_SD = 0.1` the swept category and `producer_merchant` are equal, the
    sorted key list is unchanged because Python's sort preserves insertion order, and the
    naive check reports the ordering intact. It is not intact. It has been *collapsed*: the
    table no longer distinguishes a swap dealer from a producer hedging physical, which is
    the single distinction §6.3 is most confident about.

    That is a different object from a re-weighting and it is the boundary of the plausible
    class rather than a point inside it, so it is named rather than silently admitted.
    """
    return sorted(k for k, v in others.items() if value == v)


def _crossed(base_value: float, value: float, others: dict[str, float]) -> str | None:
    """Which categories this value has moved past, named rather than merely counted.

    `preserves_order` says a line was crossed; this says whose, because "swap is now below
    producer_merchant" is a claim about holder behaviour that someone can agree or disagree
    with, and "order violated" is not.
    """
    was_below = {k for k, v in others.items() if base_value < v}
    now_below = {k for k, v in others.items() if value < v}
    parts = []
    if crossed_up := sorted(was_below - now_below):
        parts.append(f"now above {', '.join(crossed_up)}")
    if crossed_down := sorted(now_below - was_below):
        parts.append(f"now below {', '.join(crossed_down)}")
    return "; ".join(parts) or None


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
