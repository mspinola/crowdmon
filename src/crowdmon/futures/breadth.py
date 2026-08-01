"""Breadth versus depth: did the crowd get wider, or did it get levered? (spec §6.2)

A category's position is `P = N · q`: how many traders, times the average position each
holds. The same `ΔP` can come from either term, and they are different events.

    ΔP = N₀·Δq  +  q₀·ΔN  +  ΔN·Δq
         └depth┘   └breadth┘  └joint┘

- **breadth** (`q₀·ΔN`) — new participants at the existing average size. The crowd got
  wider. Wide and shallow positions grind rather than break.
- **depth** (`N₀·Δq`) — the same participants holding more each. Existing holders levering
  into it, which is the configuration that unwinds violently.
- **joint** (`ΔN·Δq`) — the interaction, and it is not a rounding term. When both move the
  same way it is the signature of a crowd that is broadening *and* levering at once, which
  the spec's quadrant table names the most dangerous cell.

**`N₀` and `q₀` are the prior week's values, not period means.** That is what makes the
identity exact rather than approximate: `N₁q₁ − N₀q₀ = N₀Δq + q₀ΔN + ΔNΔq` is an algebraic
rearrangement with no residual, and `decompose_breadth` asserts it closes. A mean-based
version leaves a remainder that has to be either reported or hidden, and hiding it in a
decomposition whose whole purpose is attribution defeats the decomposition.

**Trader counts are suppressed often, and null is a real state.** CFTC withholds a count
where too few traders would be individually identifiable. Measured on the latest
Disaggregated week, 44% of Managed Money long counts and 47% of short counts are null, and
non-reportables have no count at all by definition. A suppressed count is not a zero: this
module returns nulls rather than imputing, because an imputed trader count feeds straight
into an average position per trader, which is the number the quadrant is read off.
"""
from __future__ import annotations

import pandas as pd

SERIES_KEY = ["market_code", "report_type", "combined", "category"]


class BreadthError(ValueError):
    """The frame cannot support a breadth-depth decomposition."""


def decompose_breadth(panel: pd.DataFrame, *, side: str = "long") -> pd.DataFrame:
    """Split each week's position change into breadth, depth and joint terms.

    `side` is `"long"` or `"short"`, because a trader count is published per side and there
    is no such thing as the number of traders holding a *net* position: a category's longs
    and shorts are different traders. Asking for the breadth of a net position is a
    category error, so the side is required rather than defaulted from the sign.
    """
    if side not in ("long", "short"):
        raise BreadthError(f"side must be 'long' or 'short', got {side!r}. Trader counts "
                           f"are published per side; a NET position has no trader count "
                           f"because the longs and the shorts are different traders.")
    pos_col, n_col = f"{side}_contracts", f"trader_count_{side}"
    missing = [c for c in SERIES_KEY + ["report_date", pos_col, n_col]
               if c not in panel.columns]
    if missing:
        raise BreadthError(f"missing columns for breadth-depth: {missing}")

    df = panel.copy()
    df["report_date"] = pd.to_datetime(df["report_date"])
    df = df.sort_values(SERIES_KEY + ["report_date"], kind="mergesort")
    df["position"] = pd.to_numeric(df[pos_col], errors="coerce")
    df["traders"] = pd.to_numeric(df[n_col], errors="coerce")
    # Null where the count is suppressed OR zero. Zero traders holding a position is not a
    # small crowd, it is an inconsistency, and dividing by it would produce an infinite
    # average position that then dominates every ranking it enters.
    df["avg_position"] = (df["position"] / df["traders"]).where(df["traders"] > 0)

    g = df.groupby(SERIES_KEY, dropna=False, sort=False)
    df["prior_traders"] = g["traders"].shift(1)
    df["prior_avg"] = g["avg_position"].shift(1)
    df["d_position"] = g["position"].diff()
    df["d_traders"] = g["traders"].diff()
    df["d_avg"] = g["avg_position"].diff()
    df["days_elapsed"] = g["report_date"].diff().dt.days

    df["depth_term"] = df["prior_traders"] * df["d_avg"]
    df["breadth_term"] = df["prior_avg"] * df["d_traders"]
    df["joint_term"] = df["d_traders"] * df["d_avg"]
    df["residual"] = (df["d_position"]
                      - df["depth_term"] - df["breadth_term"] - df["joint_term"])

    df["dominant_term"] = _dominant(df)
    df["quadrant"] = _quadrant(df)
    out = df[SERIES_KEY + ["report_date", "market_name", "days_elapsed",
                           "position", "traders", "avg_position",
                           "d_position", "d_traders", "d_avg",
                           "depth_term", "breadth_term", "joint_term", "residual",
                           "dominant_term", "quadrant"]]
    out = out[out["d_position"].notna()].reset_index(drop=True)
    _assert_identity(out)
    return out


def _dominant(df: pd.DataFrame) -> pd.Series:
    """Which of the three terms carries the change. Null where any term is unknown.

    Restricted to fully-known rows before `idxmax` rather than after: a suppressed trader
    count makes all three terms null, and `idxmax` raises on an all-null row rather than
    returning null. Those rows are common (44% of Managed Money long counts are suppressed
    in the latest week), so this is the normal path, not an edge case.
    """
    terms = df[["depth_term", "breadth_term", "joint_term"]].abs()
    known = df["d_position"].notna() & terms.notna().all(axis=1)
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    if known.any():
        out.loc[known] = (terms.loc[known].idxmax(axis=1)
                          .str.replace("_term", "", regex=False))
    return out


def _quadrant(df: pd.DataFrame) -> pd.Series:
    """The spec §6.2 quadrant, which predicts the character of an unwind where the net
    position alone does not.

    A rising average position with a flat or falling trader count is "narrow and deep":
    existing holders levering into an existing position, and the violent one. Rising on
    both axes is broader and deeper at once, which is the most dangerous cell.
    """
    n_up = df["d_traders"] > 0
    q_up = df["d_avg"] > 0
    known = df["d_traders"].notna() & df["d_avg"].notna()
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    out = out.mask(known & n_up & q_up, "broadening_and_levering")
    out = out.mask(known & ~n_up & q_up, "narrow_and_deep")
    out = out.mask(known & n_up & ~q_up, "wide_and_shallow")
    out = out.mask(known & ~n_up & ~q_up, "distributing")
    return out


def _assert_identity(out: pd.DataFrame) -> None:
    """The decomposition is exact, so the residual must be zero to floating point.

    Asserted rather than tested only, because the failure it catches is a silent one: a
    residual that grows means the terms are being computed against the wrong base period,
    and the attribution would still look plausible while assigning the change to the wrong
    term. Tolerance scales with the position size, since these are contract counts in the
    millions and a fixed epsilon would fire on rounding alone.
    """
    r = pd.to_numeric(out["residual"], errors="coerce").abs()
    scale = pd.to_numeric(out["position"], errors="coerce").abs().clip(lower=1.0)
    bad = out[(r > 1e-6 * scale) & r.notna()]
    if not bad.empty:
        row = bad.iloc[0]
        raise BreadthError(
            f"{len(bad)} row(s) where breadth + depth + joint does not reconstruct "
            f"d_position, worst residual {bad['residual'].abs().max():.6g} "
            f"({row['market_code']} {row['report_date']}). The identity is algebraic, so "
            f"a residual means the base period is wrong (period means rather than the "
            f"prior week's values).")
