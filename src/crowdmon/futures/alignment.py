"""Trend alignment. Module spec §368, the cross-market half of §13 step 5.

    Correlate the cross-market positioning vector against a canonical time-series momentum
    vector (blended 20/60/250-day TSMOM per market). High alignment means the trend book is
    fully expressed, little dry powder, maximum vulnerability to reversal.

Both inputs already existed. `trigger.py` computes `sign(F_t - F_{t-k})` for exactly 20/60/250,
which **is** the canonical TSMOM, and the positioning panel is what every other engine consumes.
Nothing here asks the store for anything new.

**The momentum vector is weak for two markets in three, by construction rather than by
circumstance.** The blend is an equal-weight sign average, so it can only take the values
`{-1, -1/3, +1/3, +1}`, and **69.2% of markets sit at ±1/3** in the latest week because their
horizons disagree. That is the same fact `2026-08-02 §B14` recorded from the other direction
(23 of 33 markets with horizons pointing different ways), since the blend is `sum(s)/3`. Any
reading of an alignment score has to carry it: a score near zero can mean the book is
uncommitted, or it can mean the momentum vector it was measured against barely points anywhere.
`momentum_strength` exists so that is visible rather than inferred.

**This engine has no warm-up, and that makes it the earliest-starting thing in the package.**
The score is cross-sectional within a week and stacks no rolling window at all:

| engine | first scored | warm-up from the 2006-06-13 panel start |
|---|---|---|
| **trend alignment** | **2006-06-13** | **none** |
| macro-book PCA (differenced) | 2006-06-20 | one week |
| `damage_sell` | 2010-05-25 | 3.9 years |
| `damage_sell_pct` | 2012-05-15 | 5.9 years |

**Which is why a warning belongs in the module and not only in a handoff.** 2008 is the last
episode nobody in this package has looked at, and it is clean *only* because `D` could never
reach it: the §10 pre-registration's §2 declares Feb 2018, March 2020, silver 2021, the 2021
ags window, the 2022 invasion, the Aug 2024 yen carry and gold 2025 all seen, and §9 records
them spent. This engine and the macro-book PCA are the two that can see 2008.

**Do not slice this series by a named episode.** If it is worth pointing at a systemic unwind,
that test gets pre-registered and specified by a session that did not build it, exactly as §7
was. Reporting an alignment score for 2008 after choosing the window is the after-the-fact
window-picking the whole pre-registration exists to stop, and the episode cannot be un-spent.

**What the score is not.** It carries no first-moment content and must never be traded, under
the same §A.10 prohibition as `D`. §368's reading, that high alignment means vulnerability to
reversal, is a claim about the shape of a conditional loss distribution and not about its
location. It is also **not wired into `D`**: §A.9 has no term for it, exactly as it has none
for §A.6's commonality (`§B2`) or §A.8's cascade, so it is reported beside the composite.

**Momentum comes from `propadj` and nothing else**, reusing `trigger.py`'s refusal rather than
restating it: `unadj` fabricates a jump at every roll and would invent signal flips that never
happened, and `backadj` levels are not prices.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .trigger import DEFAULT_LOOKBACKS, TRIGGER_ADJUSTMENT, TriggerError

#: Markets needed in a week before a cross-sectional correlation is computed at all. Below
#: this the score is a statement about a handful of markets wearing a panel's name.
DEFAULT_MIN_MARKETS = 10

#: Rank correlation by default. Spearman is robust to one market's book dominating in size,
#: which Pearson is not: a single large position would otherwise set the score for the panel.
DEFAULT_METHOD = "spearman"

#: Columns `alignment_series` returns.
ALIGNMENT_COLUMNS = ["report_date", "n_markets", "alignment", "alignment_ceiling",
                     "alignment_vs_ceiling", "momentum_strength", "share_undecided"]


class AlignmentError(ValueError):
    """The inputs cannot support an alignment score."""


def blended_tsmom(symbol: str, *, lookbacks=DEFAULT_LOOKBACKS,
                  adjustment: str = TRIGGER_ADJUSTMENT,
                  weights=None, as_of=None) -> pd.Series:
    """The canonical TSMOM blend for one market: the weighted mean of `sign(F_t - F_{t-k})`.

    Equal weights by default, and that is a **stated prior rather than an estimate**, the same
    argument as `reflexivity`'s uniform cohort split: it asserts no knowledge that does not
    exist. §368 says "blended" and gives no weights anywhere. Sweep it, never fit it.

    Trailing by construction. `sign(F_t - F_{t-k})` at `t` uses only `t` and earlier, so the
    series carries no lookahead and `as_of` truncation is a convenience rather than a fix.
    """
    import cotdata

    if adjustment != TRIGGER_ADJUSTMENT:
        raise TriggerError(
            f"momentum needs {TRIGGER_ADJUSTMENT!r}, got {adjustment!r}. `unadj` fabricates a "
            f"jump at every roll and would invent signal flips; `backadj` levels are not "
            f"prices. Reused from `trigger.py` rather than restated.")
    lookbacks = tuple(lookbacks)
    if not lookbacks:
        raise AlignmentError("at least one lookback is needed for a momentum blend.")
    if weights is None:
        w = np.full(len(lookbacks), 1.0 / len(lookbacks))
    else:
        w = np.asarray(list(weights), dtype="float64")
        if len(w) != len(lookbacks):
            raise AlignmentError(f"got {len(w)} weights for {len(lookbacks)} lookbacks.")
        if not np.isclose(w.sum(), 1.0):
            raise AlignmentError(f"weights must sum to 1, got {w.sum():.6f}.")

    close = cotdata.get_prices(symbol, adjustment=adjustment)["Close"].dropna()
    if as_of is not None:
        close = close[close.index <= pd.Timestamp(as_of)]
    if close.empty:
        return pd.Series(dtype="float64")

    blend = sum(wi * np.sign(close - close.shift(k)) for wi, k in zip(w, lookbacks))
    return blend.rename(symbol)


def momentum_panel(symbols: dict[str, str], *, lookbacks=DEFAULT_LOOKBACKS,
                   weights=None, as_of=None) -> pd.DataFrame:
    """Blended TSMOM for many markets, keyed by `market_code`.

    `symbols` maps `market_code` to the price symbol, because the panel speaks market codes
    and the price store speaks symbols. **Keyed on the code, never on `market_name`**: 11 of 27
    codes carry more than one name, and `033661` is `COTTON NO. 2 - NEW YORK BOARD OF TRADE`
    becoming `COTTON NO. 2 - ICE FUTURES U.S.` (`2026-08-02 §B17`).
    """
    series = {}
    for code, symbol in symbols.items():
        try:
            blend = blended_tsmom(symbol, lookbacks=lookbacks, weights=weights, as_of=as_of)
        except TriggerError:
            raise
        except Exception:
            continue
        if not blend.empty:
            series[code] = blend
    if not series:
        raise AlignmentError("no market produced a momentum series.")
    return pd.DataFrame(series).sort_index()


def _rank_corr(a: pd.Series, b: pd.Series, method: str) -> float:
    """Pearson on ranks for Spearman. `Series.corr(method="spearman")` delegates to scipy,
    which is not a declared dependency and would fail the boundary test."""
    if method == "spearman":
        a, b = a.rank(), b.rank()
    elif method != "pearson":
        raise AlignmentError(f"method must be 'spearman' or 'pearson', got {method!r}.")
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a.to_numpy(), b.to_numpy())[0, 1])


def max_attainable(blend: pd.Series, *, method: str = DEFAULT_METHOD) -> float:
    """The score a **perfectly aligned** book would get against this momentum vector.

    **It is not 1, and it never can be.** The blend takes at most `len(lookbacks) + 1` distinct
    values, four under the default, so across ~25 markets it is massively tied. A rank
    correlation against a heavily tied vector is bounded well below 1, and the bound moves
    week to week with how the markets happen to split.

    Without this, 0.87 reads as "not quite aligned" when it may be the ceiling. Computed by
    correlating the blend against itself sorted, which is the best any positioning vector
    consistent with that momentum could achieve.
    """
    clean = blend.dropna()
    if len(clean) < 2:
        return float("nan")
    return _rank_corr(clean.sort_values().reset_index(drop=True),
                      pd.Series(np.arange(len(clean), dtype="float64")), method)


def alignment_series(positioning: pd.DataFrame, momentum: pd.DataFrame, *,
                     method: str = DEFAULT_METHOD,
                     min_markets: int = DEFAULT_MIN_MARKETS) -> pd.DataFrame:
    """The score per week, with the two things needed to read it.

    `positioning` and `momentum` are both weeks x market_code. Momentum is forward-filled onto
    the positioning index, because prices are daily and COT is weekly.

    Returns `alignment` plus three things needed to read it. **`alignment_ceiling`** is what a
    perfectly aligned book would score against that week's momentum, which is never 1 because
    the blend is heavily tied; **`alignment_vs_ceiling`** is the score as a fraction of it.
    **`momentum_strength`** and **`share_undecided`** say whether the momentum vector points
    anywhere at all. A low score with low strength is a different statement from a low score
    with high strength, and the raw figure alone distinguishes neither that nor the ceiling.
    """
    if positioning.empty or momentum.empty:
        raise AlignmentError("both a positioning and a momentum panel are required.")
    shared = positioning.columns.intersection(momentum.columns)
    if len(shared) < min_markets:
        raise AlignmentError(
            f"only {len(shared)} market codes appear in both panels, below the "
            f"{min_markets} needed. Check the code-to-symbol mapping rather than lowering "
            f"the floor.")

    pos = positioning[shared]
    mom = momentum[shared].reindex(pos.index, method="ffill")

    rows = []
    for stamp in pos.index:
        a, b = pos.loc[stamp], mom.loc[stamp]
        ok = a.notna() & b.notna()
        if int(ok.sum()) < min_markets:
            continue
        blend = b[ok]
        score = _rank_corr(a[ok], blend, method)
        ceiling = max_attainable(blend, method=method)
        rows.append({
            "report_date": stamp,
            "n_markets": int(ok.sum()),
            "alignment": score,
            "alignment_ceiling": ceiling,
            "alignment_vs_ceiling": (score / ceiling
                                     if ceiling and np.isfinite(ceiling) else float("nan")),
            "momentum_strength": float(blend.abs().mean()),
            "share_undecided": float((blend.abs() < 1.0).mean()),
        })
    if not rows:
        raise AlignmentError(
            f"no week had {min_markets} markets present in both panels.")
    return pd.DataFrame(rows)[ALIGNMENT_COLUMNS]


def blend_sensitivity(positioning: pd.DataFrame, momentum_by_weights: dict, *,
                      method: str = DEFAULT_METHOD) -> pd.DataFrame:
    """How much the score moves when the blend weights do.

    The weights are the one free parameter here and §368 gives no guidance, so their effect is
    reported rather than assumed away. Same pattern as `weight_sensitivity.sweep` and
    `flow.tolerance_sensitivity`.
    """
    rows = []
    base = None
    for label, panel in momentum_by_weights.items():
        series = alignment_series(positioning, panel, method=method).set_index("report_date")
        if base is None:
            base = series["alignment"]
        joined = pd.concat([base, series["alignment"]], axis=1, join="inner")
        rows.append({
            "weights": label,
            "weeks": len(series),
            "mean_alignment": float(series["alignment"].mean()),
            "corr_to_first": (float(np.corrcoef(joined.iloc[:, 0], joined.iloc[:, 1])[0, 1])
                              if len(joined) > 2 else float("nan")),
        })
    return pd.DataFrame(rows)


def format_alignment_block(series: pd.DataFrame, *, tail: int = 1) -> str:
    """Every input beside its result, per house style, with the caveat in the output."""
    if series.empty:
        raise AlignmentError("nothing to render.")
    lines = ["trend alignment (spec §368)".replace("§", "section ")]
    lines.append(f"  weeks:                 {len(series):>8,}   "
                 f"({series['report_date'].iloc[0].date()} to "
                 f"{series['report_date'].iloc[-1].date()})")
    for row in series.tail(tail).itertuples():
        lines.append(f"  {row.report_date.date()}  alignment {row.alignment:>+7.3f}   "
                     f"on {row.n_markets} markets")
        lines.append(f"       ceiling {row.alignment_ceiling:.3f} "
                     f"({row.alignment_vs_ceiling:.0%} of what a perfectly aligned book "
                     f"could score)")
        lines.append(f"       momentum strength {row.momentum_strength:.3f}, "
                     f"{row.share_undecided:.0%} of markets have horizons disagreeing")
    lines.append("  A low score with low strength is not the same statement as a low score")
    lines.append("  with high strength. The alignment figure alone cannot tell them apart.")
    lines.append("  Reported beside D, never inside it, and it carries no first-moment content.")
    return "\n".join(lines)
