"""The composite: `D = C x I x Phi`. Appendix §A.9, and the first output that is the system.

    D    = C x I x Phi
    C    = pct(z_t)                              crowding
    I    = pct(T_eff)                            illiquidity
    Phi  = pct( sum_c w_c (L_c + S_c) / (2 . OI) )   holder fragility

**Multiplicative, not additive, and that is the whole argument.** If any single term is near
zero the damage is near zero. A large position in a liquid market held by unconstrained
hedgers is safe; a modest position in a thin market held entirely by levered vol-targeters is
not. An additive score would let a single extreme term carry a market into the danger zone on
its own, which is exactly the reasoning the thesis exists to replace.

**Report `D` as a percentile of its own history, never as an absolute level** (§A.10). The
raw product has no meaning across markets, only its position within its own distribution
does, so `damage_sell_pct` is the number to read and `damage_sell` is shown beside it for
audit rather than for comparison.

**Four things about reading `D` are not discoverable from the number** and are gathered in
the README's "Reading `D` on live output": it falls during an unwind and that is correct;
`Phi` has no signal independent of the weight table; the rankings survive the weights being
wrong but not reordered; and `D` assumes exits are independent across markets when they
measurably are not, so `commonality_betas` belongs beside it.

**`D` carries no first-moment content.** §A.10 is explicit: the system estimates a property
of the conditional loss distribution and not its location. `D` informs tail shape, expected
shortfall, downside skew and gap risk, and it must never be traded directly. This module
computes it; `tests/test_boundaries.py` is what stops it becoming a signal by drift.

---

## Three readings of the formula that had to be settled

**1. `C = pct(z_t)`, not `pct(x_t)`.** Taken literally, and the two are not the same. `z` is
already standardised against a trailing window, so its percentile asks "how extreme is
today's standardised score against past standardised scores", which is a second
standardisation. `extremity` emits both, and `net_risk_usd_pct` is `pct(x)`. This module
uses the percentile OF the z-score, which is what §A.9 says and what §A.4's "surfaced as a
percentile of its own history" means when the thing being surfaced is `z_t`.

**2. `Phi` enters as a percentile, following §A.9's preamble rather than its formula.** The
preamble says "each term expressed as a percentile of its own history so the product is
dimensionless"; the formula shows `C` and `I` wrapped in `pct()` and `Phi` written out in
full. They disagree, and the measurement decided it.

Built the literal way first, `Phi` did almost none of the work: correlation with `D` of
**0.145**, against 0.857 for `I` and 0.796 for `C`. The cause is structural rather than
empirical. `C` and `I` are percentiles and therefore uniform on `[0, 1]` with a standard
deviation near 0.29, while a raw `Phi` is a share of gross open interest, which is a stable
property of a market's participant mix: it spans 0.18 to 0.70 across twenty years with a
standard deviation of **0.082**. Two terms varied roughly four times as much as the third, so
`D` was close to `C x I` with a mild tilt, and the package is named for the term that
nearly disappeared.

Percentile-ising `Phi` gives all three terms the same spread and lets holder fragility carry
its share. `phi_percentile=False` restores the literal formula, and both `phi` and `phi_pct`
are emitted either way so the choice is visible in the output rather than only in the call.
See `docs/design/amendments-2026-08-01.md` §A15.

**3. `T_eff` does not exist yet, so `T` is used.** §A.6 defines
`T_eff = T . (1 + gamma . beta_bar)` from a liquidity-commonality regression, and it is not
built: it needs an Amihud panel, and `gamma` is given no value anywhere in the appendix.

*Agreed split, 2026-08-01*: §A.6 is being built as a separate `futures/commonality.py`
exporting `beta_bar` and `t_effective`, and this module is wired to it afterwards rather
than as part of that work. Whoever does the wiring inherits the calibration questions in
amendments §A15-A17 along with it, which is why the two were kept apart. `gamma` will be a
**third** configured constant after `kappa` (0.2) and `Y` (0.75), and unlike those two the
appendix sanctions no range for it, so it needs a sensitivity sweep before `D` consumes it:
`flow.tolerance_sensitivity` and `weight_sensitivity.sweep` are the pattern.
**Built 2026-08-01, and it turns out it cannot reach this module.** §A.6 now exists as
`futures/commonality.py`, and the composition of the two sections is a **no-op**: with a
constant `beta_bar`, `T_eff` is a positive scalar multiple of `T`, and a percentile is
invariant under any monotonic transform, so `pct(T_eff) == pct(T)` bit-identically. Measured
maximum absolute difference **0.00e+00** at `gamma = 0.5` and at `gamma = 2.0`. The same holds
for a per-market constant `beta_i`, because `I` is a percentile taken within a market.

So wiring `t_effective` in here would change nothing about `D`. Only a **time-varying**
`beta_bar_t` reaches the composite at all, and barely: on a rolling 252-day estimate the
resulting multiplier spans 1.21 to 1.39, a 1.15x range, against `T`'s own 13x spread across
markets in a single week, and `pct(T_eff)` correlates **0.985** with `pct(T)`.

`I` therefore stays `pct(T)`, deliberately rather than for want of the input. See
`docs/design/amendments-2026-08-02.md` §B2.

What remains true is the caution, and it is now sharper: **`D` is computed as though exits
were independent across markets**, and §A.6 measures that they are not. Excluding the own
market from the basket, `beta_bar` is 0.634, with milk and hogs near 0.07 (their own door) and
the wheats above 1.0 (the same door as everyone). §A.9 has no term that can carry that, which
is a gap in the appendix rather than in this module.

---

## Direction is preserved, because damage has one

`Q_sell` and `Q_buy` are never added anywhere in this package, and the composite does not
break that. Two damages are produced:

    damage_sell = C_long  x pct(T_sell) x pct(Phi)   a crowded LONG forced to sell
    damage_buy  = C_short x pct(T_buy)  x pct(Phi)   a crowded SHORT forced to buy

with `C_long = pct(z)` and `C_short = 1 - pct(z)`. That mirror is required by the literal
reading: `z` is signed, so a high `pct(z)` is a crowded long and a low one is a crowded
short. Using `pct(z)` alone would score an extreme short as `D ~ 0` and report a squeezable
market as safe.
"""
from __future__ import annotations

import pandas as pd

from ..core.aggregate import (
    DEFAULT_MIN_PERIODS,
    DEFAULT_WINDOW,
    rolling_percentile,
    standardise,
)
from .flow import FLOW_STATES, GAP, LONG_LIQUIDATION, MIXED, QUIET, SHORT_COVERING

#: One row per market-week: `Phi` and `T` are market properties.
MARKET_KEY = ["report_date", "market_code", "report_type", "combined"]

#: The category whose extremity supplies `C`, per report type. The weight-1.0 category in
#: each weight set: it is by definition the most forceable holder, it is the one the cocoa
#: example means by "positioning at a five-year extreme", and the whole framework is about
#: whose exit is involuntary. Configurable, because "which crowd" is a real question and a
#: caller may reasonably ask about Swap Dealers instead.
CROWDING_CATEGORY = {"disaggregated": "managed_money", "tff": "leveraged"}

COMPOSITE_COLUMNS = ["crowding_long", "crowding_short", "illiquidity_sell",
                     "illiquidity_buy", "phi", "phi_pct", "fragility",
                     "damage_sell", "damage_buy", "damage_sell_pct", "damage_buy_pct"]

#: Why a `damage_*_pct` cell is not a number, when it is not one. `warmup` and the three
#: `no_*` states are the two unrelated causes `2026-08-03 §C20` separates, and they mean
#: opposite things to a reader: a young series that will score later, against a market that
#: is missing a term and may never.
SCORE_STATES = ("scored", "warmup", "no_crowding", "no_illiquidity", "no_fragility")

#: The term behind each `no_*` state, in the order a tie is resolved. Order matters only
#: when more than one is absent at once; the label names the first, and the frame still
#: carries all three columns for a reader who wants the rest.
SCORE_TERMS = (("crowding", "no_crowding"), ("illiquidity", "no_illiquidity"),
               ("fragility", "no_fragility"))

#: What a falling `D` means, per `2026-08-01 §A17`, once the flow state is beside it.
UNWIND_STATES = ("not_falling", "mid_exit", "falling_not_exit", "indeterminate")

#: The flow state that IS the crowded holder leaving, per side. `damage_sell` is a crowded
#: LONG forced to sell, so its exit shows up as `long_liquidation`; `damage_buy` is a
#: crowded short forced to buy, which is `short_covering`.
EXIT_FLOW_STATE = {"sell": LONG_LIQUIDATION, "buy": SHORT_COVERING}

#: Flow states that carry nothing about whether a fall is an exit, so a marker resting on
#: them must say `indeterminate` out loud rather than go blank.
#:
#: `gap` and `quiet` are `flow.py`'s own two honest refusals. `mixed` is a real flow state
#: and is here on measurement rather than by definition: `2026-08-03 §C21` puts it at 58.2%
#: of falling-`D` weeks with a median `ΔD` of exactly 0.0000 and a 46.6% falling share,
#: which is a coin flip. Reproducer
#: `docs/analysis/reproduce_report_gate.py::c21_a17_is_partial`.
SILENT_FLOW_STATES = frozenset({MIXED, QUIET, GAP})

#: Every state left over answers the question. Derived rather than listed, so a new state
#: added to `flow.py` has to be classified here instead of landing in one bucket by luck.
DECISIVE_FLOW_STATES = frozenset(FLOW_STATES) - SILENT_FLOW_STATES


class CompositeError(ValueError):
    """The inputs cannot support a composite."""


def add_composite(fragility: pd.DataFrame, extremity: pd.DataFrame, *,
                  category: str | None = None,
                  phi_percentile: bool = True,
                  window: str | int = DEFAULT_WINDOW,
                  min_periods: int = DEFAULT_MIN_PERIODS) -> pd.DataFrame:
    """`D = C x I x Phi` per market-week, both directions.

    `fragility` is a `rank_markets(market_fragility(...))` frame carrying `phi` and the
    `dtl_*` durations; `extremity` is an `add_extremity(...)` frame carrying
    `net_risk_usd_z`. They arrive at different grains on purpose (fragility is per market,
    extremity per market-category) and this is where they are joined.

    Rows missing any term keep their place with a null `D` rather than being dropped or
    having the missing term treated as 1.0. A composite silently computed from two of three
    factors is not the composite, and would rank a market with no volume data above one with
    a genuinely low reading.
    """
    _require(fragility, ["phi", "dtl_sell", "dtl_buy", *MARKET_KEY], "fragility")
    _require(extremity, ["net_risk_usd_z", "category", *MARKET_KEY], "extremity")

    report_type = _single_report_type(fragility)
    wanted = category or CROWDING_CATEGORY.get(report_type)
    if wanted is None:
        raise CompositeError(
            f"no crowding category configured for report_type {report_type!r}; "
            f"have {sorted(CROWDING_CATEGORY)}. Pass category= explicitly.")
    available = set(extremity["category"].unique())
    if wanted not in available:
        raise CompositeError(
            f"category {wanted!r} is absent from the extremity frame (have "
            f"{sorted(available)}), so C cannot be computed.")

    out = fragility.copy()
    out["report_date"] = pd.to_datetime(out["report_date"])

    # C: the percentile OF the z-score, per market, from one category's series.
    crowd = extremity[extremity["category"] == wanted].copy()
    crowd["report_date"] = pd.to_datetime(crowd["report_date"])
    crowd = standardise(crowd, "net_risk_usd_z", by=["market_code", "report_type",
                                                     "combined"],
                        date_column="report_date", window=window,
                        min_periods=min_periods, winsor=0.0)
    out = out.merge(crowd[[*MARKET_KEY, "net_risk_usd_z_pct"]], on=MARKET_KEY, how="left")
    out["crowding_long"] = out.pop("net_risk_usd_z_pct")
    out["crowding_short"] = 1.0 - out["crowding_long"]

    # I: the percentile of days-to-liquidate, per market, per direction.
    for side in ("sell", "buy"):
        out[f"illiquidity_{side}"] = _percentile_by_market(
            out, f"dtl_{side}", window=window, min_periods=min_periods)

    # Phi, both ways. `fragility` is whichever one D actually uses, named so a reader of
    # the output can see which reading produced the number without re-reading the call.
    out["phi_pct"] = _percentile_by_market(out, "phi", window=window,
                                           min_periods=min_periods)
    out["fragility"] = out["phi_pct"] if phi_percentile else pd.to_numeric(
        out["phi"], errors="coerce")

    # D, and its own percentile, which is the number A.10 says to report.
    out["damage_sell"] = out["crowding_long"] * out["illiquidity_sell"] * out["fragility"]
    out["damage_buy"] = out["crowding_short"] * out["illiquidity_buy"] * out["fragility"]
    for side in ("sell", "buy"):
        out[f"damage_{side}_pct"] = _percentile_by_market(
            out, f"damage_{side}", window=window, min_periods=min_periods)

    _assert_bounds(out)
    return out


def add_score_state(scored: pd.DataFrame, *,
                    sides: tuple[str, ...] = ("sell", "buy")) -> pd.DataFrame:
    """Name why each `damage_*_pct` cell is null, per row, rather than per panel.

    **The one caveat this package had measured and no output stated** (`2026-08-03 §C20`,
    `§C24`). `damage_report` already counts the causes across a panel and no column names
    the cause of a particular cell, so a reader holding one market-week has to supply the
    inference rule from prose. That is the entire `E = 1` of the §2 gate in
    [`../../../docs/handoffs/2026-08-03-report-layer.md`](../../../docs/handoffs/2026-08-03-report-layer.md);
    every other row-computable caveat is already attached by a shipped function.

    **The two causes mean opposite things and a blank cell says neither.** A null because the
    third rolling window has not filled is a young series that will score later. A null
    because a term is missing is a market that may never score, and `coverage.drops_at`
    names the rung. Rendered identically, "not yet scoreable" reads as "scored, and low",
    which is the first degenerate input §2 of that handoff lists.

    The separating rule is `all three terms present AND the percentile null => warm-up`, and
    `§C20` measures **zero exceptions** on the 27,194-week current-state panel: after the
    `damage_sell_pct` floor, 797 of 19,160 rows are still null and none of them has all three
    terms. Nothing here is fitted or thresholded; it is a classification of columns the frame
    already carries.

    Adds `score_state_<side>` per side, taking one of `SCORE_STATES`. Reproducer:
    `docs/analysis/reproduce_report_gate.py::c20_warmup_is_row_computable`.
    """
    out = scored.copy()
    for side in sides:
        if side not in ("sell", "buy"):
            raise CompositeError(f"side must be 'sell' or 'buy', got {side!r}")
        crowding = "crowding_long" if side == "sell" else "crowding_short"
        columns = {"crowding": crowding, "illiquidity": f"illiquidity_{side}",
                   "fragility": "fragility"}
        _require(out, [f"damage_{side}", f"damage_{side}_pct", *columns.values()],
                 "scored")

        pct = pd.to_numeric(out[f"damage_{side}_pct"], errors="coerce")
        raw = pd.to_numeric(out[f"damage_{side}"], errors="coerce")
        state = pd.Series("scored", index=out.index, dtype=object)
        state[pct.isna() & raw.notna()] = "warmup"
        # Reversed so the FIRST term in `SCORE_TERMS` wins a row missing more than one.
        for term, label in reversed(SCORE_TERMS):
            missing = pd.to_numeric(out[columns[term]], errors="coerce").isna()
            state[pct.isna() & missing] = label
        _assert_states_explain_the_nulls(state, pct, side)
        out[f"score_state_{side}"] = state
    return out


def add_unwind_state(scored: pd.DataFrame, flows: pd.DataFrame, *,
                     side: str = "sell",
                     category: str | None = None) -> pd.DataFrame:
    """`2026-08-01 §A17` as a per-row marker: is this fall a market mid-exit?

    §A17 is the reading instruction that a falling `D` is **not** a market getting safer, it
    may be a market halfway out of the door. The proposed carrier was `ΔD` beside the
    crowding category's flow state, and §2 of
    [`../../../docs/handoffs/2026-08-03-report-layer.md`](../../../docs/handoffs/2026-08-03-report-layer.md)
    said to test that rather than assign it. `2026-08-03 §C21` tested it and it is **half
    right**, which is why this function emits an explicit `indeterminate` rather than a
    blank.

    - **Right at the extremes.** `long_liquidation` weeks fall 84% of the time against
      `new_longs` at 15%, with opposite median `ΔD`. A fall under liquidation is a different
      event from a fall under accumulation, exactly as §A17 says.
    - **Silent three times in five.** `mixed` covers 58.2% of falling-`D` weeks at a median
      `ΔD` of exactly 0.0000, and `quiet` (the "genuinely safer" arm the handoff named)
      occurs 3 times in 27,167 market-weeks and never on a falling week. Only 40.2% of
      falling weeks carry a decisive state.

    A marker that is right when it speaks and blank otherwise reads as complete, which is
    §5's negative #4 arriving one level down. So `indeterminate` is a value here, not an
    absence, and `format_brief` prints it.

    `flows` is a `decompose(panel)` frame. `category` defaults to the same one that supplies
    `C` (`CROWDING_CATEGORY`), because the crowd whose exit §A17 describes is the crowd `C`
    measures. Adds `d_damage_<side>_pct`, `flow_state` and `unwind_state_<side>`.
    Reproducer: `docs/analysis/reproduce_report_gate.py::c21_a17_is_partial`.
    """
    if side not in ("sell", "buy"):
        raise CompositeError(f"side must be 'sell' or 'buy', got {side!r}")
    _require(scored, [f"damage_{side}_pct", *MARKET_KEY], "scored")
    _require(flows, ["report_date", "market_code", "category", "flow_state"], "flows")

    wanted = category or CROWDING_CATEGORY.get(_single_report_type(scored))
    if wanted is None:
        raise CompositeError(
            f"no crowding category configured for this report type; "
            f"have {sorted(CROWDING_CATEGORY)}. Pass category= explicitly.")
    available = set(flows["category"].dropna().unique())
    if wanted not in available:
        raise CompositeError(
            f"category {wanted!r} is absent from the flows frame (have {sorted(available)}), "
            f"so §A17's marker has no flow state to read.")

    out = scored.copy()
    out["report_date"] = pd.to_datetime(out["report_date"])
    ordered = out.sort_values(["market_code", "report_date"], kind="mergesort")
    values = pd.to_numeric(ordered[f"damage_{side}_pct"], errors="coerce")
    delta = values.groupby([ordered["market_code"], ordered["report_type"],
                            ordered["combined"]], dropna=False, sort=False).diff()
    out[f"d_damage_{side}_pct"] = delta.reindex(out.index)

    state = flows[flows["category"] == wanted][["report_date", "market_code", "flow_state"]]
    state = state.copy()
    state["report_date"] = pd.to_datetime(state["report_date"])
    if state.duplicated(subset=["report_date", "market_code"]).any():
        raise CompositeError(
            f"the flows frame has more than one {wanted!r} row per market-week, so the join "
            f"would multiply rows. Pass a single report type and `combined` setting.")
    out = out.drop(columns=["flow_state"], errors="ignore").merge(
        state, on=["report_date", "market_code"], how="left")

    d = pd.to_numeric(out[f"d_damage_{side}_pct"], errors="coerce")
    flow = out["flow_state"]
    unwind = pd.Series("indeterminate", index=out.index, dtype=object)
    decisive = flow.isin(DECISIVE_FLOW_STATES)
    unwind[d.notna() & (d >= 0)] = "not_falling"
    unwind[d.notna() & (d < 0) & decisive] = "falling_not_exit"
    unwind[d.notna() & (d < 0) & (flow == EXIT_FLOW_STATE[side])] = "mid_exit"
    out[f"unwind_state_{side}"] = unwind
    return out


def damage_report(scored: pd.DataFrame) -> pd.DataFrame:
    """Coverage, and which factor is responsible for each gap.

    Kept apart because the three have different fixes and different owners: `no_crowding` is
    an extremity/history question, `no_illiquidity` a volume question, `no_phi` a category
    mapping one. A single "not scored" count would hide which.
    """
    for column in ("crowding_long", "illiquidity_sell", "fragility", "damage_sell"):
        if column not in scored.columns:
            raise CompositeError(f"{column!r} missing; run `add_composite` first")
    has = {name: pd.to_numeric(scored[name], errors="coerce").notna()
           for name in ("crowding_long", "illiquidity_sell", "fragility", "damage_sell")}
    return pd.Series({
        "scored": int(has["damage_sell"].sum()),
        "no_crowding": int((~has["crowding_long"]).sum()),
        "no_illiquidity": int((~has["illiquidity_sell"]).sum()),
        "no_fragility": int((~has["fragility"]).sum()),
        "total": len(scored),
    }).to_frame("rows")


def top_damage(scored: pd.DataFrame, *, side: str = "sell", n: int = 10,
               report_date=None) -> pd.DataFrame:
    """The highest `D` percentiles in one week, with every factor shown beside it.

    The factors are printed rather than summarised because a composite that does not show
    its terms is unauditable: `D` near zero because the market is liquid and `D` near zero
    because nobody fragile holds it are different statements, and only the decomposition
    distinguishes them.
    """
    if side not in ("sell", "buy"):
        raise CompositeError(f"side must be 'sell' or 'buy', got {side!r}")
    stamp = scored["report_date"].max() if report_date is None else pd.Timestamp(report_date)
    rows = scored[(scored["report_date"] == stamp)
                  & scored[f"damage_{side}_pct"].notna()]
    crowding = "crowding_long" if side == "sell" else "crowding_short"
    cols = ["market_name", "market_code", crowding, f"illiquidity_{side}", "fragility",
            "phi", f"damage_{side}", f"damage_{side}_pct", f"dtl_{side}"]
    return (rows.sort_values(f"damage_{side}_pct", ascending=False).head(n)
            [[c for c in cols if c in rows.columns]].reset_index(drop=True))


# ── internals ───────────────────────────────────────────────────────────────
def _percentile_by_market(frame: pd.DataFrame, column: str, *, window, min_periods):
    """Trailing percentile of `column`, per market, aligned back to `frame`'s index."""
    parts = []
    ordered = frame.sort_values(["market_code", "report_date"], kind="mergesort")
    for _, group in ordered.groupby(["market_code", "report_type", "combined"],
                                    dropna=False, sort=False):
        series = group.set_index("report_date")[column]
        parts.append(rolling_percentile(series, window=window,
                                        min_periods=min_periods).set_axis(group.index))
    return pd.concat(parts).reindex(frame.index) if parts else pd.NA


def _require(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise CompositeError(
            f"{name} frame is missing {missing}. Expected `rank_markets(market_fragility(..))` "
            f"with volume for fragility, and `add_extremity(..)` for extremity.")


def _single_report_type(frame: pd.DataFrame) -> str:
    kinds = frame["report_type"].dropna().unique()
    if len(kinds) != 1:
        raise CompositeError(
            f"frame spans report types {sorted(kinds)}. The crowding category differs per "
            f"report and the categories do not correspond, so one call cannot cover both.")
    return str(kinds[0])


def _assert_states_explain_the_nulls(state: pd.Series, pct: pd.Series, side: str) -> None:
    """Every null percentile carries a reason, checked on each computation.

    The point of the state column is that a reader never has to guess, so a row labelled
    `scored` with nothing to score would be worse than the blank cell it replaces. It cannot
    happen while `damage` is the product of three terms (null iff a term is null), which is
    exactly the property a future change to `add_composite` might break.
    """
    unexplained = int((pct.isna() & (state == "scored")).sum())
    if unexplained:
        raise CompositeError(
            f"{unexplained} rows have a null damage_{side}_pct and no missing term, so "
            f"neither warm-up nor a missing factor explains them. `damage_{side}` is the "
            f"product of three factors, so this means one of them stopped propagating null.")


def _assert_bounds(out: pd.DataFrame) -> None:
    """Every factor and every product lies in `[0, 1]`, checked on each computation.

    Cheap, and it pins the definition the way `fragility`'s Phi bound does. All three terms
    are bounded by construction (two percentiles and a share), so a breach means one of them
    stopped being what it claims: a raw duration leaking into `I`, or a `Phi` built from nets.
    """
    for column in ("crowding_long", "crowding_short", "illiquidity_sell",
                   "illiquidity_buy", "fragility", "damage_sell", "damage_buy"):
        values = pd.to_numeric(out[column], errors="coerce").dropna()
        if values.empty:
            continue
        if values.min() < 0.0 or values.max() > 1.0:
            raise CompositeError(
                f"{column} left [0, 1] (min {values.min():.4f}, max {values.max():.4f}). "
                f"Every factor is a percentile or a bounded share, so this means one of "
                f"them is no longer what it claims to be.")
