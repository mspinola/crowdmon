"""Fragility-weighted exit size (appendix A.2, module spec §6.3).

The thesis is `damage = crowding x illiquidity x holder fragility`, and fragility is the
term that decides **who** gets hurt. Futures are zero-sum: every long is somebody's short,
so "everyone is long" is impossible and a net imbalance on its own says almost nothing.
What differs between the two sides of a market is the holder. A producer hedging a physical
crop can stand for delivery; a levered fund running a volatility target has an exit
function written into its mandate. Same contract, same size, opposite behaviour under
stress.

Three numbers per market, and the first rule is that the first two never combine.

    Q_sell = Σ  w_c · P_c        over categories with P_c > 0   (forced longs sell)
    Q_buy  = Σ  w_c · |P_c|      over categories with P_c < 0   (forced shorts buy)
    Phi    = Σ  w_c · (L_c + S_c) / (2 · OI)

**Why the directional split.** Adding `Q_sell` and `Q_buy` describes no flow that could
ever occur. Forced longs sell and forced shorts buy, so the sum of the two is the total
volume of a stress event in which both sides are simultaneously liquidated against each
other, which is not a market event. The *difference* between them is the informative
number: it is what separates a market where longs can be forced out from one where shorts
can be squeezed.

**Why `Phi` uses gross over `2·OI`.** Nets sum to zero across categories, by construction,
so `Σ w_c · P_c` is not a share of anything and a "fragile share of open interest" built
from nets is meaningless. Gross positions do sum to something: `Σ_c (L_c + S_c)` counts
every contract twice, once from each side, hence the `2` in the denominator. That makes
`Phi ∈ [0, 1]` by construction, which is asserted in the tests.

An earlier draft of the spec used `Σ w_c |P_c| / OI`, which is unbounded and wrong. The
bound assertion exists to prevent a regression to it, and is the reason `Phi` is defined
here rather than left to a caller.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg

MARKET_KEY = ["report_date", "market_code", "report_type", "combined"]

OUT_COLUMNS = MARKET_KEY + [
    "market_name", "open_interest", "spread_total",
    "q_sell", "q_buy", "q_net", "q_gross",
    "phi", "phi_denominator_covered",
    "top_phi_category", "top_phi_share",
]


class FragilityError(ValueError):
    """The frame cannot support a fragility calculation."""


def market_fragility(panel: pd.DataFrame, *, report_type: str | None = None,
                     weights: dict[str, float] | None = None) -> pd.DataFrame:
    """`Q_sell`, `Q_buy` and `Phi` per market-week.

    `panel` is the canonical long schema. Every category present must have a weight, or
    this raises: an unmapped category is silently dropped from every sum it belongs in,
    which under-reports exit pressure without failing anywhere. That is the worst available
    failure mode for a monitor whose job is reporting exit pressure.
    """
    if panel.empty:
        return pd.DataFrame(columns=OUT_COLUMNS)
    _require_columns(panel)

    rt = report_type or _single_report_type(panel)
    w = dict(weights) if weights is not None else cfg.weights_for(rt)
    if weights is None:
        cfg.check_vocabulary(panel["category"].unique(), rt)
    else:
        unknown = sorted(set(panel["category"].unique()) - set(w))
        if unknown:
            raise FragilityError(
                f"categories {unknown} have no weight in the supplied map (known: "
                f"{sorted(w)}). An unmapped category is dropped from every sum silently.")

    df = panel.copy()
    for c in ("long_contracts", "short_contracts", "spread_contracts", "open_interest"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = pd.NA
    df["weight"] = df["category"].map(w).astype("float64")
    df["net"] = df["long_contracts"] - df["short_contracts"]
    df["gross"] = df["long_contracts"] + df["short_contracts"]

    # The split, at the row level, so that the two can never accidentally be added: a
    # category contributes to exactly one of these and zero to the other.
    df["w_sell"] = (df["weight"] * df["net"]).where(df["net"] > 0, 0.0)
    df["w_buy"] = (df["weight"] * df["net"].abs()).where(df["net"] < 0, 0.0)
    df["w_gross"] = df["weight"] * df["gross"]

    g = df.groupby(MARKET_KEY, dropna=False, sort=False)
    out = g.agg(market_name=("market_name", "first"),
                open_interest=("open_interest", "max"),
                spread_total=("spread_contracts", "sum"),
                q_sell=("w_sell", "sum"),
                q_buy=("w_buy", "sum"),
                w_gross=("w_gross", "sum"),
                gross_total=("gross", "sum")).reset_index()

    # The asymmetry, and it is often the single most informative number in the block: a
    # market where q_net is strongly positive is one where longs can be forced out, and a
    # market where it is strongly negative is one where shorts can be squeezed.
    out["q_net"] = out["q_sell"] - out["q_buy"]
    # Emitted for completeness and named so it cannot be mistaken for a flow. It is the
    # sum of two opposing forced flows and therefore describes no event.
    out["q_gross"] = out["q_sell"] + out["q_buy"]

    oi = pd.to_numeric(out["open_interest"], errors="coerce")
    denom = 2.0 * oi
    out["phi"] = (out["w_gross"] / denom).where(denom > 0)
    # Spreading is a matched long and short in one trader's hands, so it counts toward open
    # interest but carries no directional exit: it is deliberately outside the numerator.
    # The cost is that `Phi`'s denominator holds contracts its numerator cannot see, which
    # is the same arithmetic the module spec flags as a defect for Legacy — the difference
    # is that here it is a choice rather than a missing column, so it is reported. At
    # weight 1.0 everywhere, `Phi` could reach only this value, not 1.
    out["phi_denominator_covered"] = (out["gross_total"] / denom).where(denom > 0)

    top = contributions(panel, report_type=rt, weights=w)
    if not top.empty:
        best = (top.sort_values("phi_contribution", ascending=False)
                   .groupby(MARKET_KEY, dropna=False, sort=False).head(1)
                   .rename(columns={"category": "top_phi_category",
                                    "phi_contribution": "top_phi_share"}))
        out = out.merge(best[MARKET_KEY + ["top_phi_category", "top_phi_share"]],
                        on=MARKET_KEY, how="left")

    _assert_phi_bound(out)
    return out.reindex(columns=OUT_COLUMNS)


def contributions(panel: pd.DataFrame, *, report_type: str | None = None,
                  weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Each category's contribution to the `Phi` numerator, and its side of `Q`.

    The handoff asks for this by name, and the reason is that `Phi` is a single number over
    five categories with a 10x weight spread. If Managed Money is carrying nearly all of
    it — which is what the weights are designed to produce — then the headline is a
    statement about Managed Money, and a walkthrough that reads it as a broad-based measure
    of the whole market is overstating what was measured.

    `phi_contribution` sums to `phi` across categories exactly, by construction, so this is
    a decomposition and not an approximation.
    """
    if panel.empty:
        return pd.DataFrame()
    _require_columns(panel)
    rt = report_type or _single_report_type(panel)
    w = dict(weights) if weights is not None else cfg.weights_for(rt)

    df = panel.copy()
    for c in ("long_contracts", "short_contracts", "open_interest"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["weight"] = df["category"].map(w).astype("float64")
    df["net"] = df["long_contracts"] - df["short_contracts"]
    df["gross"] = df["long_contracts"] + df["short_contracts"]

    oi = df.groupby(MARKET_KEY, dropna=False, sort=False)["open_interest"].transform("max")
    df["phi_contribution"] = (df["weight"] * df["gross"] / (2.0 * oi)).where(oi > 0)
    df["q_contribution"] = df["weight"] * df["net"].abs()
    df["q_side"] = pd.Series("flat", index=df.index).mask(
        df["net"] > 0, "sell").mask(df["net"] < 0, "buy")
    return df[MARKET_KEY + ["market_name", "category", "weight",
                            "long_contracts", "short_contracts", "net", "gross",
                            "open_interest", "phi_contribution", "q_contribution",
                            "q_side"]].reset_index(drop=True)


def fragility_frame(panel: pd.DataFrame, **kw) -> pd.DataFrame:
    """`market_fragility` plus the OI-denominated pressure ratios, in one call.

    Convenience only: it is `pressure.rank_markets(market_fragility(panel))`, which is what
    every caller wanted anyway.
    """
    from .pressure import rank_markets

    return rank_markets(market_fragility(panel, **kw))


# ── internals ───────────────────────────────────────────────────────────────
def _require_columns(panel: pd.DataFrame) -> None:
    need = MARKET_KEY + ["category", "long_contracts", "short_contracts", "open_interest"]
    missing = [c for c in need if c not in panel.columns]
    if missing:
        raise FragilityError(f"missing columns for fragility: {missing}")


def _single_report_type(panel: pd.DataFrame) -> str:
    kinds = panel["report_type"].dropna().unique()
    if len(kinds) != 1:
        raise FragilityError(
            f"panel spans report types {sorted(kinds)}. Weights are per report type and "
            f"the categories do not correspond across them, so one call cannot cover both. "
            f"Pass report_type= explicitly, or split the panel.")
    return str(kinds[0])


def _assert_phi_bound(out: pd.DataFrame) -> None:
    """`0 <= Phi <= 1`, checked on every computation and not only in the tests.

    Cheap, and it is the assertion that pins the definition. The bound holds because
    `Σ_c (L_c + S_c) = 2·(OI − spreading) <= 2·OI` and every weight is in `[0, 1]`, so any
    breach means one of those two premises moved — a weight above 1, or a numerator that
    started counting nets. The wrong formula (`Σ w_c |P_c| / OI`) is unbounded and would
    trip this on the first crowded market rather than on the hundredth.
    """
    phi = pd.to_numeric(out["phi"], errors="coerce").dropna()
    bad = out.loc[phi.index[(phi < 0) | (phi > 1)]]
    if not bad.empty:
        r = bad.iloc[0]
        raise FragilityError(
            f"{len(bad)} market-week(s) have Phi outside [0, 1], worst "
            f"{r['market_code']} {r['report_date']} phi={r['phi']:.4f}. Phi is a share of "
            f"gross open interest and is bounded by construction, so this means either a "
            f"weight above 1.0 or a numerator built from nets rather than gross.")
