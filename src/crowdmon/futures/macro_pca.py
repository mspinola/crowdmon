"""The macro-book PCA: how much of the systematic book moves as one thing.

Module spec §7:

    Macro-book PCA. PCA on positioning *changes*. PC1 approximates the aggregate systematic
    book; its variance share is the futures absorption ratio. Loading rotation indicates the
    book being redefined.

`D` asks how much damage a market could do. This asks a different question that no
per-market number can: **when Managed Money moves, does it move everywhere at once?** A high
absorption ratio means one trade is being expressed across many markets, so an exit is not 27
independent exits. That is the assumption `D` explicitly makes and cannot check
(`2026-08-02 §B2`), which is why this is reported beside `D` and never inside it.

---

## The object this is NOT

`commonality.py` builds an **illiquidity** panel, and a PCA over it is far closer to hand
because the panel already exists. **It is a different quantity and only one of them is the
absorption ratio.** §7's PCA runs on positioning changes; §A.6's commonality runs on liquidity
changes. Building the reachable one and reporting it under the spec's label for the other is
an error both sessions working on this package have now made or nearly made, in `§B16` and in
a README paragraph, within four hours of each other.

---

## Three things measured before this module was written

**1. A naive listwise PCA returns nothing.** The Managed Money panel is 948 weeks x 26 markets
at **95.7%** cell coverage, and **zero weeks have no missing market**. The holes are spread
across markets rather than concentrated in weeks, so a coverage figure that reads as "nearly
complete" yields an empty rectangle. `select_markets` exists because of this, and it is
derived rather than hand-picked.

**2. Dropping two markets buys the entire panel; dropping one fewer costs two and a half
years.** 25 markets gives 746 complete weeks ending 2023-12-26, because the 25th market
delists and truncates everything to it. 24 gives **947** weeks ending 2026-07-28. Below 24
nothing further is bought.

**3. This reaches 2008 and `D` does not.** The differenced panel starts **2008-06-10** against
`D`'s **2010-05-25**, because `C = pct(z)` stacks two three-year windows (`2026-08-01 §A16`)
and this needs one. **It is the only engine here whose history covers a genuine systemic
unwind.** That is also a hazard: it invites exactly the after-the-fact window-picking the §10
pre-registration exists to prevent. **No episode in this module's history has been examined by
its author.** If it is to be pointed at 2008, that test belongs in a pre-registration written
by someone else.

---

## "PC1 approximates the aggregate systematic book" is true on TFF and false on Disaggregated

Measured on both report types, 947 weeks from 2008-06-10, 24 and 16 markets:

| panel | absorption | null | what PC1 actually is |
|---|---|---|---|
| Disaggregated | 0.143 | 0.054 | ZS +0.35, ZC +0.30, ZL +0.30, KE +0.27, ZM +0.26. **The grain complex** |
| TFF | 0.128 | 0.077 | YM +0.37, 6A +0.36, ES +0.36, NQ +0.35, 6S +0.29, **DX -0.26** |

TFF's first component is risk appetite in textbook form: long the equity indices, long the
commodity currency, **short the dollar**. That is the aggregate systematic book. Disaggregated's
first component is the grain trade, and calling it a macro book would be wrong in the same way
`2026-08-01 §A14`'s finding is wrong to ignore, that 76% of the Disaggregated universe is ICE
Energy and Nodal power so a "cross-market" result over it is mostly about ERCOT and PJM.

**So the report type is not a parameter here, it is the subject.** Run this on Disaggregated
and the absorption ratio is a statement about how together the ag complex moves, which is a
real and useful thing that is not what §7 names it.

**And absorption must be read against its own null, never across panels.** TFF's null is 0.077
against Disaggregated's 0.054 purely because a variance share is floored at `1/n` and TFF has
16 markets to Disaggregated's 24. Raw, TFF looks less crowded; against its null it is not.

---

## Four choices that are choices, stated rather than defaulted

- **Trailing, never full-sample.** `rolling_absorption` uses only data up to each week. A
  full-sample PCA would compute the 2010 reading from 2026 data, which is lookahead of the
  plainest kind. `absorption_ratio` on the whole panel is offered for description only and
  says so.
- **Correlation, not covariance.** Columns are standardised inside each window. The inputs are
  already z-scored per market so the two nearly coincide, and nearly is not exactly.
- **PC1's sign is pinned.** An eigenvector's sign is arbitrary, so without a convention
  "loading rotation" reports `numpy` flips as the book being redefined. Pinned so the loadings
  sum positive, with a deterministic fallback when that sum is zero.
- **The ratio is bounded and always positive, so it looks plausible on noise.** `shuffled_null`
  gives PC1's share on a panel with the cross-sectional structure destroyed and the marginals
  kept. Report it beside the figure or the figure means nothing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: The category whose positioning is the systematic book, per report type. Managed Money for
#: Disaggregated; TFF's equivalent is Leveraged Funds. Same reasoning as `composite`'s
#: `CROWDING_CATEGORY`: it is the weight-1.0 holder in `core/config.py`.
BOOK_CATEGORY: dict[str, str] = {"disaggregated": "managed_money", "tff": "leveraged"}

#: What is z-scored and then differenced. Risk units rather than contracts, because module
#: spec §5.2 makes vol-scaled notional the default unit for any cross-market comparison, and a
#: PCA over raw contracts would load on market size.
PANEL_INPUT = "net_risk_usd_z"

#: Trailing window for `rolling_absorption`, in report weeks. 156 is three years, matching the
#: `1095D` the rest of the package standardises over. **The appendix sanctions no value**, so
#: it is a parameter and `window_sensitivity` reports what other choices would do.
DEFAULT_WINDOW = 156

#: Weeks required inside a window before a reading is emitted.
DEFAULT_MIN_PERIODS = 104

#: Fewest markets a PCA will run on. Below this "the aggregate book" is a phrase about a
#: handful of markets.
DEFAULT_MIN_MARKETS = 8

#: Draws for `shuffled_null`. Deterministic given `seed`.
DEFAULT_NULL_DRAWS = 200
DEFAULT_SEED = 20260802

MACRO_PCA_COLUMNS = ["report_date", "absorption", "rotation", "n_markets", "n_weeks"]


class MacroPcaError(ValueError):
    """The inputs cannot support a macro-book PCA."""


# ── panel ───────────────────────────────────────────────────────────────────
def positioning_panel(per_category: pd.DataFrame, *,
                      category: str | None = None,
                      column: str = PANEL_INPUT,
                      difference: bool = True) -> pd.DataFrame:
    """Wide matrix of positioning CHANGES, weeks x markets.

    `per_category` is an `add_extremity(...)` frame. `difference=False` returns the level
    panel instead, which is §7's "matrix of z-scored positioning" and is **not** what the PCA
    consumes: §7 is explicit that the PCA runs on changes.

    Keyed on `market_code`, never on `market_name`: 11 of 27 codes carry more than one name
    (`coverage.py`).
    """
    for required in ("report_date", "market_code", "category"):
        if required not in per_category.columns:
            raise MacroPcaError(
                f"panel is missing {required!r}; expected an add_extremity(...) frame")
    if column not in per_category.columns:
        raise MacroPcaError(
            f"panel has no {column!r} column. That comes from `add_extremity`, which needs "
            f"`add_risk_units` before it.")

    report_types = set(per_category.get("report_type", pd.Series(dtype=object)).unique())
    wanted = category
    if wanted is None:
        if len(report_types) != 1:
            raise MacroPcaError(
                f"cannot infer the book category across report types {sorted(report_types)}; "
                f"pass category= explicitly.")
        rt = next(iter(report_types))
        wanted = BOOK_CATEGORY.get(str(rt))
        if wanted is None:
            raise MacroPcaError(
                f"no book category configured for report_type {rt!r}; "
                f"have {sorted(BOOK_CATEGORY)}. Pass category= explicitly.")

    rows = per_category[per_category["category"] == wanted]
    if rows.empty:
        raise MacroPcaError(
            f"category {wanted!r} is absent from the panel (have "
            f"{sorted(per_category['category'].unique())[:6]}...)")

    wide = rows.pivot_table(index="report_date", columns="market_code", values=column)
    wide.index = pd.to_datetime(wide.index)
    wide = wide.sort_index()
    return wide.diff() if difference else wide


def select_markets(panel: pd.DataFrame, *,
                   min_markets: int = DEFAULT_MIN_MARKETS) -> list[str]:
    """The market set giving the most listwise-complete weeks. Derived, never hand-picked.

    **Measured motivation:** the full 26-market panel yields **zero** complete weeks at 95.7%
    cell coverage, because the holes are spread across markets. Dropping two buys 947 weeks;
    dropping one fewer buys 746 and truncates the panel to 2023 because the 25th market
    delists.

    Ties are broken toward MORE markets, so the rule never drops a market it did not have to.
    """
    if panel.empty:
        return []
    order = panel.notna().sum().sort_values(ascending=False)
    best: tuple[int, int] = (-1, -1)
    chosen: list[str] = []
    for k in range(len(order), max(min_markets - 1, 0), -1):
        cols = list(order.index[:k])
        complete = int(panel[cols].dropna().shape[0])
        # maximise complete weeks; on a tie prefer the wider panel
        if (complete, k) > best:
            best, chosen = (complete, k), cols
    return chosen


# ── one PCA ─────────────────────────────────────────────────────────────────
def _pin_sign(loadings: np.ndarray) -> np.ndarray:
    """Fix PC1's arbitrary sign so rotation measures the book and not `numpy`.

    Convention: the loadings sum positive. When that sum is exactly zero, which a symmetric
    eigenvector can produce, fall back to the largest-magnitude loading being positive. That
    is still deterministic, which is the only property that matters.
    """
    total = float(loadings.sum())
    if total < 0:
        return -loadings
    if total == 0.0 and loadings[int(np.argmax(np.abs(loadings)))] < 0:
        return -loadings
    return loadings


def absorption_ratio(matrix: pd.DataFrame, *,
                     min_markets: int = DEFAULT_MIN_MARKETS) -> dict:
    """PC1's share of variance, and its loadings, on one complete rectangle.

    **Descriptive only.** Run over a whole history this is lookahead: the reading it produces
    is informed by every week in the frame, including later ones. `rolling_absorption` is the
    point-in-time form and is what any time series of this should come from.
    """
    block = matrix.dropna()
    if block.shape[1] < min_markets or block.shape[0] <= block.shape[1]:
        raise MacroPcaError(
            f"need at least {min_markets} markets and more weeks than markets, got "
            f"{block.shape[0]} weeks x {block.shape[1]} markets after dropping incomplete rows")

    sd = block.std(ddof=1)
    if (sd <= 0).any():
        dead = list(sd.index[sd <= 0])
        raise MacroPcaError(f"markets {dead} have zero variance in this block")
    z = (block - block.mean()) / sd
    corr = np.corrcoef(z.to_numpy(), rowvar=False)

    values, vectors = np.linalg.eigh(corr)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    total = float(values.sum())
    if total <= 0:
        raise MacroPcaError("correlation matrix has non-positive total variance")

    loadings = _pin_sign(vectors[:, 0])
    return {
        "absorption": float(values[0] / total),
        "loadings": pd.Series(loadings, index=block.columns, name="pc1"),
        "eigenvalues": pd.Series(values, name="eigenvalue"),
        "n_markets": int(block.shape[1]),
        "n_weeks": int(block.shape[0]),
    }


def loading_rotation(a: pd.Series, b: pd.Series) -> float:
    """How far PC1's AXIS turned between two windows: `1 - |cos|`, bounded in `[0, 1]`.

    0.0 is the same book, 1.0 is orthogonal, and larger is the book being redefined.

    **The absolute value is the whole point and it is not a convenience.** An eigenvector's
    sign is not identified: PC1 and -PC1 describe the same axis and the same book. A signed
    cosine therefore reports a pin flip as a 180-degree rotation, and `_pin_sign`'s
    positive-sum convention flips whenever that sum passes through zero, which happens on real
    data whether or not anything about the book changed.

    Measured on the 24-market panel before this was fixed: **8 of 843 weeks reported a
    rotation of ~1.99 against a median of 0.0004**, 200x the p95, every one of them an
    artifact. Under `1 - |cos|` the same weeks read ~0.002, which is what they always were.
    """
    shared = a.index.intersection(b.index)
    if len(shared) < 2:
        return float("nan")
    x, y = a.loc[shared].to_numpy(), b.loc[shared].to_numpy()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denom == 0:
        return float("nan")
    return float(1.0 - abs(np.dot(x, y) / denom))


# ── the point-in-time form ──────────────────────────────────────────────────
def rolling_absorption(panel: pd.DataFrame, *,
                       markets: list[str] | None = None,
                       window: int = DEFAULT_WINDOW,
                       min_periods: int = DEFAULT_MIN_PERIODS,
                       min_markets: int = DEFAULT_MIN_MARKETS) -> pd.DataFrame:
    """Trailing absorption ratio and loading rotation, one row per report week.

    **Point-in-time by construction**: the reading at week `t` uses only weeks up to and
    including `t`. Nothing here consults a later row, which is what separates it from
    `absorption_ratio` over a whole panel.
    """
    if panel.empty:
        return pd.DataFrame(columns=MACRO_PCA_COLUMNS)
    cols = markets if markets is not None else select_markets(panel,
                                                              min_markets=min_markets)
    if len(cols) < min_markets:
        raise MacroPcaError(
            f"only {len(cols)} markets survive selection, below min_markets={min_markets}")

    block = panel[cols]
    rows: list[dict] = []
    previous: pd.Series | None = None
    index = block.index
    for i in range(len(index)):
        start = max(0, i - window + 1)
        chunk = block.iloc[start:i + 1].dropna()
        if len(chunk) < min_periods:
            continue
        try:
            got = absorption_ratio(chunk, min_markets=min_markets)
        except MacroPcaError:
            continue
        rows.append({"report_date": index[i], "absorption": got["absorption"],
                     "rotation": (loading_rotation(previous, got["loadings"])
                                  if previous is not None else float("nan")),
                     "n_markets": got["n_markets"], "n_weeks": got["n_weeks"]})
        previous = got["loadings"]
    return pd.DataFrame(rows, columns=MACRO_PCA_COLUMNS)


# ── the null, without which the number means nothing ────────────────────────
def shuffled_null(matrix: pd.DataFrame, *,
                  draws: int = DEFAULT_NULL_DRAWS,
                  seed: int = DEFAULT_SEED,
                  min_markets: int = DEFAULT_MIN_MARKETS) -> pd.Series:
    """PC1's share with the cross-sectional structure destroyed and the marginals kept.

    **A variance share is bounded in `[1/n, 1]` and always positive, so it looks plausible on
    noise.** Shuffling each market's column independently breaks the co-movement while leaving
    every market's own distribution intact, so the difference between the observed figure and
    this is the only part that is about crowding.

    Deterministic given `seed`.
    """
    block = matrix.dropna()
    if block.shape[1] < min_markets:
        raise MacroPcaError(f"need at least {min_markets} markets, got {block.shape[1]}")
    rng = np.random.default_rng(seed)
    values = block.to_numpy()
    out = []
    for _ in range(draws):
        shuffled = np.column_stack([rng.permutation(values[:, j])
                                    for j in range(values.shape[1])])
        frame = pd.DataFrame(shuffled, columns=block.columns)
        try:
            out.append(absorption_ratio(frame, min_markets=min_markets)["absorption"])
        except MacroPcaError:                                    # pragma: no cover
            continue
    return pd.Series(out, name="absorption_null")


def window_sensitivity(panel: pd.DataFrame, *,
                       windows: tuple[int, ...] = (104, 156, 260),
                       markets: list[str] | None = None) -> pd.DataFrame:
    """What the trailing window is doing to the answer.

    The appendix sanctions no window length here, so a reading that moves with it is a
    reading about the window. Same pattern as `flow.tolerance_sensitivity` and
    `weight_sensitivity.sweep`.
    """
    rows = []
    for w in windows:
        try:
            got = rolling_absorption(panel, markets=markets, window=w,
                                     min_periods=min(DEFAULT_MIN_PERIODS, w))
        except MacroPcaError:
            continue
        if got.empty:
            continue
        rows.append({"window": w, "n_readings": len(got),
                     "absorption_mean": float(got["absorption"].mean()),
                     "absorption_last": float(got["absorption"].iloc[-1]),
                     "rotation_mean": float(got["rotation"].mean(skipna=True))})
    return pd.DataFrame(rows)


def format_absorption(result: dict, null: pd.Series | None = None) -> str:
    """A printable block. `null` is not optional in spirit: see `shuffled_null`."""
    lines = [f"absorption ratio   {result['absorption']:.3f}"
             f"   ({result['n_markets']} markets, {result['n_weeks']} weeks)"]
    if null is not None and not null.empty:
        p = float((null >= result["absorption"]).mean())
        lines.append(f"shuffled null      {null.mean():.3f} mean, "
                     f"{null.quantile(0.95):.3f} at p95   (p = {p:.3f})")
    top = result["loadings"].abs().sort_values(ascending=False).head(5)
    lines.append("largest |loadings| " + ", ".join(
        f"{code} {result['loadings'][code]:+.2f}" for code in top.index))
    return "\n".join(lines)
