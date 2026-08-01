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
