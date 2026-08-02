"""Which markets can produce a score at all, and where the ones that cannot drop out.

Every other coverage helper in this package answers one rung's question. `notional`'s asks
"does this row have a price", `riskunits`' asks "does it have a volatility", `volume`'s asks
"does it have an ADV". **None of them answers the question that decides whether a market can
appear in a cross-market result**, which is how many weeks survive after every window has been
stacked on top of every join.

That gap was found by the §10 evaluator, not by this package: two of the 27 markets in the
scored Disaggregated panel produce **no `D` in any week, ever**, and nothing said so. Module
spec §10's own replay list names an ags/lumber episode, and the pre-registration's version of
it listed six markets and ran on five (`2026-08-02 §B17`).

---

## Two things this module exists to get right

**1. A count is necessary and not sufficient, because the two known failures are at different
rungs.** Both lumber codes score nothing, for unrelated reasons:

| code | weeks | `dtl_sell` | `damage_sell` | dies at |
|---|---|---|---|---|
| 058643 | 880 | 24 | 0 | the price join |
| 058644 | 178 | **178** | 0 | the stacked percentile windows |

`058644` has a complete exit duration in **every one of its weeks** and still scores nothing.
A report that says only "0 scoreable weeks" sends a maintainer to look at prices, where there
is nothing wrong. So the ladder reports every rung and names the one that bites.

**2. Key on `market_code`. `market_name` is a display label and nothing else.**

11 of the 27 codes carry more than one name, because markets migrate venue and the CFTC
restates the label without changing the code. Group on `(market_code, market_name)` and the
panel reports **six** unscoreable markets rather than two: cotton, cocoa, sugar and coffee each
show a zero-scoring block under a pre-migration NYBOT name, inside a code that scores 742
weeks. **The invented markets outnumber the real ones three to two.**

Do not reach for string normalisation instead. Heating oil (`022651`) carries five spellings,
two of which are ``NY HARBOR ULSD`` and ``NY HARBOR USLD``. That is a transposition, so one of
them is a typo in the CFTC source, and any cleaner able to merge those two is able to merge
things that must stay apart.

---

## What this module does not do

It reports what the configured windows and joins actually produce. **It does not argue about
them**, does not change a minimum, and does not drop a market. Whether a 27-market panel should
be a 25-market panel is a question for whoever reads the report, and `unscoreable` returns the
list so a caller can decide explicitly rather than by accident.
"""
from __future__ import annotations

import pandas as pd

#: Grain key. Never `market_name`: see the module docstring.
MARKET_KEY = ["market_code"]

#: The ladder, in the order the rungs bite. Each entry is `(rung, column, grain)` where grain
#: is ``"category"`` for the per-market-category frame that carries the joins and the
#: normalisation rungs, and ``"market"`` for the per-market frame that carries exit capacity
#: and the composite.
#:
#: **A list rather than something derived**, because the columns live at two different grains
#: and no single frame knows the whole chain. That is itself part of why the gap survived.
#:
#: **This list shipped incomplete and was corrected in the same day** (`2026-08-02 §B18`). It
#: went straight from `extremity_z` to the composite, skipping the three terms `D` is actually
#: built from, so `058644` was reported as dropping at `composite` when it drops one rung
#: earlier at `crowding`. The guard test that was supposed to catch exactly this checked only
#: the columns `add_composite` *emits*, not the ones it *computes*, and so had the same blind
#: spot as the ladder it guarded. It now checks both.
LADDER: tuple[tuple[str, str, str], ...] = (
    ("contract_spec", "symbol", "category"),
    ("price", "price", "category"),
    ("notional", "net_notional_usd", "category"),
    ("volatility", "sigma_daily", "category"),
    ("risk_units", "net_risk_usd", "category"),
    ("volume", "adv", "category"),
    ("extremity_z", "net_risk_usd_z", "category"),
    # Price-free, and the reason the ladder is NOT monotonic. See PRICE_FREE below.
    ("holder_fragility", "phi", "market"),
    ("exit_duration", "dtl_{side}", "market"),
    # The three terms `D` is the product of. Omitting these was the defect in the first cut.
    ("fragility_pct", "phi_pct", "market"),
    ("illiquidity", "illiquidity_{side}", "market"),
    ("crowding", "crowding_{crowd}", "market"),
    ("composite", "damage_{side}", "market"),
    ("composite_percentile", "damage_{side}_pct", "market"),
)

#: Rungs that need no price, no multiplier and no volatility.
#:
#: **The ladder is not a chain of filters and coverage does not only fall down it.** `phi` is
#: computed from columns the canonical schema already carries, so a market starved of prices
#: can have far more weeks of `holder_fragility` than of anything downstream of a price:
#: `058643` has **880** weeks of `phi` against **24** of `dtl_sell`, a rise of 36x in the
#: middle of the ladder.
#:
#: Anyone assuming monotonicity will mis-locate every failure of this shape, which is why this
#: set exists and why `coverage_ladder` reports the branch rather than implying a single chain.
PRICE_FREE: frozenset[str] = frozenset({"holder_fragility", "fragility_pct"})

#: The rung a market must reach to appear in a cross-market result at all.
TERMINAL_RUNG = "composite_percentile"


class CoverageError(ValueError):
    """The frames cannot support a coverage ladder."""


def _weeks_with(frame: pd.DataFrame, column: str) -> pd.Series:
    """Distinct report weeks per market in which `column` is non-null for at least one row.

    "At least one row" rather than "all rows" on purpose: at category grain a market-week has
    five rows and a missing category is a different finding from a missing join. This asks
    whether the market could be scored that week, not whether every category was.
    """
    if column not in frame.columns:
        return pd.Series(dtype="int64")
    ok = frame[frame[column].notna()]
    if ok.empty:
        return pd.Series(dtype="int64")
    return ok.groupby(MARKET_KEY[0])["report_date"].nunique()


def _labels(*frames: pd.DataFrame) -> pd.Series:
    """One display label per code: the most recent name it was seen under.

    Most recent rather than most frequent, because a market that migrated venue years ago has
    its old name in the majority of rows and its current name is the useful one.
    """
    parts = [f[["market_code", "market_name", "report_date"]]
             for f in frames if f is not None and not f.empty
             and {"market_code", "market_name", "report_date"} <= set(f.columns)]
    if not parts:
        return pd.Series(dtype="object")
    allrows = pd.concat(parts, ignore_index=True)
    allrows = allrows.sort_values("report_date")
    return allrows.groupby("market_code")["market_name"].last()


def coverage_ladder(per_category: pd.DataFrame,
                    per_market: pd.DataFrame | None = None, *,
                    side: str = "sell") -> pd.DataFrame:
    """Weeks surviving each rung, per market, plus the rung that bites.

    `per_category` is the frame carrying the joins and normalisation, i.e. the output of
    `add_volume(add_extremity(add_risk_units(add_notional(ContractMaster.load().annotate(
    panel)))))`. `per_market` is the composite frame from `add_composite`, and may be omitted
    to report only the rungs that exist before it.

    Returns one row per `market_code`, never per name. `drops_at` is the **first** rung whose
    surviving-week count is zero, or `None` for a market that reaches the end.

    `weeks` is the market's total distinct report weeks in `per_category`, which is the
    denominator every other column should be read against.

    **`drops_at` names the first zero, not the root cause, and the two differ.** `058643`
    reports `illiquidity` while the cause is a price series covering 24 of its 880 weeks,
    two rungs earlier: a market can limp through a rung on thin coverage and only reach zero
    once a window is stacked on it. That is why the full ladder is meant to be printed beside
    the label, which `format_coverage` does, and why `PRICE_FREE` matters when reading it.
    """
    if side not in ("sell", "buy"):
        raise CoverageError(f"side must be 'sell' or 'buy', got {side!r}")
    if per_category.empty:
        return pd.DataFrame(columns=["market_code", "market_name", "weeks", "drops_at"])
    for required in ("market_code", "report_date"):
        if required not in per_category.columns:
            raise CoverageError(
                f"per_category is missing {required!r}, so coverage cannot be keyed. "
                f"Have {sorted(per_category.columns)[:12]}...")

    frames = {"category": per_category, "market": per_market}
    total = per_category.groupby("market_code")["report_date"].nunique().rename("weeks")
    out = total.to_frame()

    # `D_sell` is driven by LONG crowding and `D_buy` by short: the forced side is whoever
    # holds the position, not whoever is buying. `composite.py` names the columns that way.
    crowd = "long" if side == "sell" else "short"

    reached: list[str] = []
    for rung, column, grain in LADDER:
        frame = frames.get(grain)
        if frame is None or frame.empty:
            continue
        wanted = column.format(side=side, crowd=crowd)
        if wanted not in frame.columns:
            continue
        counts = _weeks_with(frame, wanted)
        out[rung] = counts.reindex(out.index).fillna(0).astype("int64")
        reached.append(rung)

    def _first_zero(row: pd.Series) -> str | None:
        for rung in reached:
            if row[rung] == 0:
                return rung
        return None

    out["drops_at"] = out.apply(_first_zero, axis=1) if reached else None
    out.insert(0, "market_name", _labels(per_category, per_market).reindex(out.index))
    return out.reset_index()


def unscoreable(per_category: pd.DataFrame,
                per_market: pd.DataFrame | None = None, *,
                side: str = "sell") -> pd.DataFrame:
    """The markets that produce nothing, and the rung each one dies at.

    Returned rather than dropped. A caller that wants them gone should filter explicitly:
    silently dropping is what let the pre-registration's ags episode name six markets and run
    on five.
    """
    ladder = coverage_ladder(per_category, per_market, side=side)
    if ladder.empty:
        return ladder
    return ladder[ladder["drops_at"].notna()].reset_index(drop=True)


def coverage_summary(per_category: pd.DataFrame,
                     per_market: pd.DataFrame | None = None, *,
                     side: str = "sell") -> pd.Series:
    """One line per rung: how many markets still have at least one week when it is applied.

    The shape the other coverage helpers use, for printing beside an aggregate. Counts
    **markets**, not rows, because the question this module exists for is which markets can
    appear in a cross-market result.
    """
    ladder = coverage_ladder(per_category, per_market, side=side)
    if ladder.empty:
        return pd.Series(dtype="int64")
    rungs = [r for r, _, _ in LADDER if r in ladder.columns]
    summary = {"markets": len(ladder)}
    summary.update({rung: int((ladder[rung] > 0).sum()) for rung in rungs})
    summary["unscoreable"] = int(ladder["drops_at"].notna().sum())
    return pd.Series(summary)


def format_coverage(ladder: pd.DataFrame, *, only_unscoreable: bool = False) -> str:
    """A printable ladder. `only_unscoreable=True` prints just the markets that die."""
    if ladder.empty:
        return "no markets"
    rows = ladder[ladder["drops_at"].notna()] if only_unscoreable else ladder
    if rows.empty:
        return "every market reaches the end of the ladder"
    rungs = [r for r, _, _ in LADDER if r in rows.columns]
    lines = []
    for _, row in rows.iterrows():
        head = f"{row['market_code']}  {str(row['market_name'])[:44]:<44}"
        # A `*` marks a price-free rung, because those can and do exceed the rungs before
        # them and a reader scanning for a monotonic fall will otherwise mis-locate the fault.
        counts = "  ".join(f"{r}{'*' if r in PRICE_FREE else ''}={int(row[r])}"
                           for r in rungs)
        tail = f"  DROPS AT {row['drops_at']}" if row["drops_at"] else ""
        lines.append(f"{head} weeks={int(row['weeks']):>4}  {counts}{tail}")
    lines.append("* price-free: coverage can RISE here. The ladder is not a chain of filters.")
    return "\n".join(lines)
