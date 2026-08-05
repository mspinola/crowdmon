"""Walkthrough builders for COT positioning: the tables a market writeup is made of.

The COT-specific half of the report layer. `crowdmon.core.report` renders a frame as a
readable markdown table and knows nothing about categories; this knows what a category
table and a `Q`/`Phi` block are, and could not serve the equity monitor unchanged.

House style, applied here rather than described: `q_arithmetic` returns
`1.0 x 69,007 + 0.4 x 28,129 + 0.6 x 110` alongside `80,324.6`, so a walkthrough can print
the working. The two carry the same information only if you already trust the code, and the
whole point of a written analysis is that a reader does not have to.
"""
from __future__ import annotations

import pandas as pd

from ..core.report import to_markdown  # noqa: F401  (re-exported for walkthrough scripts)
from .fragility import MARKET_KEY, contributions, market_fragility

#: Column order for the category table, which is step 1 of every walkthrough.
CATEGORY_COLUMNS = ["category", "long_contracts", "short_contracts", "net", "gross",
                    "weight", "phi_contribution", "q_side", "q_contribution"]


def category_table(panel: pd.DataFrame, market_code: str,
                   report_date=None, **kw) -> pd.DataFrame:
    """Long, short, net, gross and weight per category, for one market-week."""
    rows = _one_market(panel, market_code, report_date)
    out = contributions(rows, **kw)
    return out[CATEGORY_COLUMNS].sort_values("phi_contribution",
                                             ascending=False).reset_index(drop=True)


def q_arithmetic(panel: pd.DataFrame, market_code: str, report_date=None, **kw) -> dict:
    """`Q_sell`, `Q_buy` and `Phi` with every term spelled out.

    Returns the summed results alongside the per-term strings that produce them, so a
    walkthrough can print the working. `phi_ceiling` is included because `Phi` cannot reach
    1 in a market with any spreading: spreading counts toward open interest and carries no
    directional exit, so it sits in the denominator and outside the numerator. Printing the
    reachable ceiling beside the value stops a reader calibrating against a 1 that is not
    available.
    """
    rows = _one_market(panel, market_code, report_date)
    contrib = contributions(rows, **kw)
    frag = market_fragility(rows, **kw).iloc[0]

    def _terms(side: str) -> str:
        part = contrib[contrib["q_side"] == side].sort_values("q_contribution",
                                                              ascending=False)
        return " + ".join(f"{r.weight:g} x {abs(r.net):,.0f}" for r in part.itertuples())

    phi_terms = " + ".join(
        f"{r.weight:g} x {r.gross:,.0f}"
        for r in contrib.sort_values("phi_contribution", ascending=False).itertuples())
    return {
        "market_name": frag["market_name"],
        "market_code": market_code,
        "report_date": frag["report_date"],
        "open_interest": frag["open_interest"],
        "spread_total": frag["spread_total"],
        "q_sell": frag["q_sell"], "q_sell_terms": _terms("sell"),
        "q_buy": frag["q_buy"], "q_buy_terms": _terms("buy"),
        "q_net": frag["q_net"],
        "phi": frag["phi"], "phi_terms": phi_terms,
        "phi_denominator": 2.0 * float(frag["open_interest"]),
        "phi_ceiling": frag["phi_denominator_covered"],
        "top_phi_category": frag["top_phi_category"],
        "top_phi_share": frag["top_phi_share"],
        "q_sell_over_oi": float(frag["q_sell"]) / float(frag["open_interest"]),
        "q_buy_over_oi": float(frag["q_buy"]) / float(frag["open_interest"]),
    }


def format_q_block(arith: dict) -> str:
    """The arithmetic block as markdown, for pasting into a walkthrough."""
    a = arith
    return "\n".join([
        f"    Q_sell = {a['q_sell_terms']}",
        f"           = {a['q_sell']:,.1f} contracts",
        "",
        f"    Q_buy  = {a['q_buy_terms']}",
        f"           = {a['q_buy']:,.1f} contracts",
        "",
        f"    Phi    = ({a['phi_terms']}) / (2 x {a['open_interest']:,.0f})",
        f"           = {a['phi']:.4f}   (ceiling {a['phi_ceiling']:.4f}, "
        f"spreading is outside the numerator)",
    ])


#: What each factor of `D` is asking, in the words a reader should use for it. Kept here
#: rather than in `composite.py` because it is presentation, and kept as data rather than
#: prose in a docstring so `format_damage_block` and any future renderer say the same thing.
FACTOR_QUESTIONS = {
    "crowding": "how lopsided the forceable holders are, vs this market's own 3 years",
    "illiquidity": "how long that side would take to exit, vs its own 3 years",
    "fragility": "how much of the market sits in forceable hands, vs its own 3 years",
}

#: What each of the OTHER published columns is, in the same one-line voice. Deliberately a
#: sibling of `FACTOR_QUESTIONS` rather than more entries in it: that name means the three
#: factors of `D = C x I x Phi`, a consumer reads it that way, and folding a level or a
#: caveat carrier in beside them would say four things multiply where three do.
#:
#: Keyed by the PANEL column name, with `<side>` where the panel carries a `sell` and a
#: `buy` copy, because the reader looking a term up has the column in front of it and not
#: the concept. `publish.panel_manifest` ships this verbatim, so a UI that cannot import
#: this package still renders the producer's own words rather than its own paraphrase.
COLUMN_DEFINITIONS = {
    "damage_<side>_pct": "how damaging a forced exit on that side would be (C x I x Phi), "
                         "vs this market's own 3 years",
    "trigger_<side>_sigma": "how far spot sits from the nearest trend flip that forces this "
                            "side, in days of ordinary movement (daily sigma)",
    "trigger_<side>_pct": "the same distance as a plain percent move from spot, which reads "
                          "naturally and does not compare across markets",
    "dtl_<side>": "days for that side's fragility-weighted position to leave at 20% of a "
                  "252-day average daily volume (kappa 0.2), a level and not a percentile",
    "beta": "how much this market's illiquidity moves with the rest of the universe, 0 its "
            "own exit door and 1 the same door as everything else, and not a factor of D",
}

#: Bands for the headline. Deliberately coarse: `D_pct` is a percentile of a product of
#: percentiles, so a two-decimal reading implies a precision the construction does not have.
DAMAGE_BANDS = ((0.90, "top decile"), (0.75, "high"), (0.50, "above middling"),
                (0.25, "below middling"), (0.0, "bottom quartile"))


def damage_band(damage_pct: float) -> str:
    """The coarse band for a `D_pct`, or `unscored` for a null."""
    if damage_pct is None or pd.isna(damage_pct):
        return "unscored"
    for floor, label in DAMAGE_BANDS:
        if float(damage_pct) >= floor:
            return label
    return "bottom quartile"


def format_damage_block(block: dict) -> str:
    """`D_pct` rendered with its three factors, the arithmetic, and how to read it.

    The factors are printed **every time**, not on request. `composite.damage_block`
    records the three measured reasons; the short version is that `D` is a product, so it
    is dominated by its smallest term, and the effect of `Phi` is not monotone, so a lone
    percentile cannot be interpreted even by someone who knows the formula.

    The closing line is deliberately about what the number is NOT. Percentiles get read as
    probabilities, and this one is a rank among past weeks in one market.
    """
    b = block
    side = b["side"]
    forced = "forced longs selling" if side == "sell" else "forced shorts buying"
    c, i, f = b["crowding"], b["illiquidity"], b["fragility"]
    d, dp = b["damage"], b["damage_pct"]
    raw = b.get("raw", {})

    def _n(v, spec=".3f"):
        return "n/a" if v is None else format(v, spec)

    lines = [
        f"{b['market_name']} ({b['market_code']})  {pd.Timestamp(b['report_date']).date()}"
        f"  side: {side} ({forced})",
        "",
        f"    C   crowding     {_n(c)}   {FACTOR_QUESTIONS['crowding']}",
        f"    I   illiquidity  {_n(i)}   {FACTOR_QUESTIONS['illiquidity']}",
        f"    Phi fragility    {_n(f)}   {FACTOR_QUESTIONS['fragility']}",
        "",
    ]
    if None not in (c, i, f):
        lines += [f"    D   = {c:.3f} x {i:.3f} x {f:.3f} = {d:.4f}", ""]
    lines += [f"    D_pct = {_n(dp)}   <- the delivered number ({damage_band(dp)})", ""]
    if dp is None:
        # An empty percentage inside the sentence below rendered as "in this market,
        # looked less dangerous", which is not a sentence. A market with a null factor
        # gets its own reading, and lumber is the live case: four years of prices against
        # the six that `C = pct(z)` needs, so `D` cannot be formed while `I` and `Phi` can.
        missing = [n for n, v in (("C", c), ("I", i), ("Phi", f)) if v is None]
        lines += [
            f"  UNSCORED: {', '.join(missing)} {'is' if len(missing) == 1 else 'are'} "
            f"null, so D cannot be formed. The factors that DO",
            "  exist are above and are readable on their own; the product is not.",
            "  Usually too little history: C stacks two 3-year windows and needs six.",
        ]
    else:
        lines += [
            f"  Read as: of the last 3 years of weeks in this market, {dp:.0%} looked less",
            f"  dangerous than now for {forced}. It is a rank among this market's own past,",
            "  not a probability, not a forecast, and not comparable as a level to another",
            "  market's days-to-liquidate.",
        ]
    if raw.get("dtl") is not None:
        lines.append(
            f"  Level check: T_{side} = {raw['dtl']:.2f} days. A percentile cannot tell "
            f"you\n  whether the level is trivial; a market clearing in under half a "
            f"session\n  is not dangerous however unusual that is for it.")
    lines.append(
        "  D is a product, so the smallest factor dominates. Phi's effect is NOT\n"
        "  monotone: a below-median Phi can raise or lower D_pct depending on the\n"
        "  market's own joint history (2026-08-04, corn up and sterling down).")

    off = b.get("offside") or {}
    if off.get("distance_sigma") is not None:
        lines += ["", format_offside(off, side=side, damage_pct=dp)]
    return "\n".join(lines)


#: The four cells of (how close is the trigger) x (how bad is the exit). Publishing `D_pct`
#: and the trigger distance separately is what keeps these distinguishable; a product of the
#: two collapses all four into one scalar. Thresholds are coarse for the same reason
#: `DAMAGE_BANDS` is: both inputs are noisy and a fine grid implies precision neither has.
QUADRANT = {
    (True, True): "CLOSE and SEVERE. The cell the measure exists to find",
    (True, False): "close but not severe. Likely to fire, unlikely to hurt",
    (False, True): "severe but not close. Would hurt, is not imminent",
    (False, False): "neither close nor severe",
}

#: A trigger within this many daily sigma is "close". Roughly one ordinary day's move.
CLOSE_SIGMA = 1.5


def format_offside(offside: dict, *, side: str, damage_pct: float | None) -> str:
    """The trigger distance, rendered beside `D_pct` and explicitly not multiplied into it.

    Two things this block must not let a reader do. It must not read the distance as a
    forecast: it is the level at which a rules-based pool is mechanically forced, not a
    prediction that price gets there. And it must not be combined with `D_pct` into a single
    ranking, because `D` is a conditional severity (A.10) and because the distance is the
    trailing k-day return, which already drives `C` (`2026-08-04 §D9`). The quadrant is the
    information.
    """
    d_sigma = offside.get("distance_sigma")
    d_pct = offside.get("distance_pct")
    k = offside.get("lookback_days")
    forced = "selling" if side == "sell" else "buying"
    out = [
        f"    offside      {d_sigma:.1f} sigma   nearest {k:.0f}d flip that forces "
        f"{forced}, {d_pct:.2%} away",
    ]
    # The observed pool must actually be on the side the signal implies, or the level is
    # real and the book it would force is not. They disagree on a third of (market,
    # horizon) pairs, so this is the common case rather than the exotic one.
    agrees = offside.get("pool_agrees")
    if agrees is False:
        out.append("                 !! the OBSERVED pool is on the OTHER side, so this "
                   "level would\n                    force a book that is not there. "
                   "Signal-implied, not held.")
    elif agrees is None:
        out.append("                 (no pool supplied, so whether anyone is actually "
                   "positioned\n                    this way is unchecked)")
    if damage_pct is not None and agrees is not False:
        cell = QUADRANT[(d_sigma <= CLOSE_SIGMA, damage_pct >= 0.75)]
        out.append(f"                 -> {cell}")
    out += [
        "  Not multiplied into D, and not a forecast. D says how bad an exit would be;",
        "  this says how far price must move before the rules force one. Kept separate",
        "  because D is a conditional severity (A.10) and because F* = F_{t-k} makes this",
        "  the trailing k-day return, which already drives C (corr -0.481). Publishing",
        "  both is what keeps the four cells above distinguishable.",
    ]
    if offside.get("horizons_disagree"):
        out.append("  The 20/60/250d horizons DISAGREE here: there is a forced-buy level "
                   "too.\n  This book is not one pool with one trigger.")
    return "\n".join(out)


def flow_sequence(flows: pd.DataFrame, market_code: str, category: str,
                  weeks: int = 12) -> pd.DataFrame:
    """The trailing state sequence for one market and category.

    The sequence matters more than the single week, which is the reason this exists as its
    own function rather than a tail of the flow frame. A persistent run of `new_longs`
    against a falling trader count is the concentrating configuration; one `new_longs` week
    is noise.
    """
    rows = flows[(flows["market_code"] == market_code)
                 & (flows["category"] == category)]
    cols = [c for c in ["report_date", "days_elapsed", "long_contracts", "short_contracts",
                        "d_long", "d_short", "d_net", "flow_state", "fuel_remaining",
                        "oi_corroborates"] if c in rows.columns]
    return rows.sort_values("report_date")[cols].tail(weeks).reset_index(drop=True)


def ranking_table(fragility: pd.DataFrame, column: str, n: int = 10,
                  min_open_interest: float = 0) -> pd.DataFrame:
    """A published ranking, trimmed to the columns a reader needs to audit it."""
    from .pressure import top_by

    cols = ["market_name", "market_code", "open_interest", "q_sell", "q_buy",
            "q_sell_over_oi", "q_buy_over_oi", "phi", "top_phi_category", "sell_to_buy"]
    top = top_by(fragility, column, n=n, min_open_interest=min_open_interest)
    return top[[c for c in cols if c in top.columns]]


def _one_market(panel: pd.DataFrame, market_code: str, report_date=None) -> pd.DataFrame:
    rows = panel[panel["market_code"] == market_code]
    if rows.empty:
        raise ValueError(f"no rows for market_code {market_code!r}")
    stamp = rows["report_date"].max() if report_date is None else pd.Timestamp(report_date)
    rows = rows[rows["report_date"] == stamp]
    if rows.empty:
        raise ValueError(f"no rows for {market_code!r} on {stamp.date()}")
    if rows.duplicated(subset=MARKET_KEY + ["category"]).any():
        raise ValueError(f"{market_code!r} has duplicate category rows on {stamp.date()}")
    return rows
