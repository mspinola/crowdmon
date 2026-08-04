"""The market-week brief: a `D` that arrives carrying what a reader must already know.

§3 of [`../../../docs/handoffs/2026-08-03-report-layer.md`](../../../docs/handoffs/2026-08-03-report-layer.md),
which ran only because §2's pre-registered gate passed at `R = 4, E = 1`
(`2026-08-03 §C20`-`§C24`). A report is the only artifact a reader receives without also
receiving the code, so the question this module answers is whether the things one must know
before reading a `D` can travel with the number instead of living in prose that goes stale.

## What it does not do

**It computes nothing.** Every figure is a column a shipped module already returns. The two
derivations it reads live in `composite.py`, which owns `D`, and not here: a derivation in
the rendering is how the next engine gets built by accident. `score_state` and
`unwind_state` are `composite.add_score_state` and `composite.add_unwind_state`, and this
module refuses to run without the first of them rather than quietly supplying it.

## Its safety case is one caveat wide, and it says so in its own output

`2026-08-03 §C24` is blunt about this and the brief repeats it rather than letting a reader
infer safety from completeness. Of the four caveats the gate found row-computable, three
were already attached by a shipped function (`coverage_ladder`, `add_commonality`, and
`phi_denominator_covered` on the fragility frame). Only the warm-up state was not. So the
assembly is convenience with exactly **one** genuine gap closed, and the footer says that.

## The ship rule, pre-registered before any of this was built

§5's negative #4 of that handoff is the outcome it calls most likely and most dangerous: a
brief carrying four warnings and silently omitting the fifth reads as complete, so the
reader stops looking, where a bare frame at least announces that it is bare. The rule fixed
in advance is that the brief ships only if it prevents every misreading on the enumerated
list, **or names in its own output the ones it does not carry**.

It does not prevent them all. `READING_INSTRUCTIONS` below is that enumeration, taken from
`README.md`'s "Reading `D` on live output", and `caveat_ledger` returns a status for every
one of the five including the three it cannot carry. A brief that cannot state its own gaps
does not ship; this one states them on every render.

Two of the three are not carried for reasons the gate measured rather than for want of
effort. `§A21` is computable on every row and **identical** on every row, so it separates
nothing (`§C22`). `§C3`'s band needs a population and a weight sweep, and `§C23` measures
that no panel available today holds both a `pct(D)` and the markets the rule names.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..core.report import to_markdown  # noqa: F401  (re-exported for walkthrough scripts)
from .composite import SCORE_STATES
from .stratum import BAND_ADVICE, STRATA

#: A caveat is `carried` when a value on this row says whether it bites, `indeterminate`
#: when the carrier exists and is silent here, and `not_carried` when no per-row value can
#: say. All three are printed. `indeterminate` is a value and not an absence, which is
#: `2026-08-03 §C21`'s finding applied: a marker that speaks only when confident reads as
#: complete the rest of the time.
CARRIED, INDETERMINATE, NOT_CARRIED = "carried", "indeterminate", "not_carried"


@dataclass(frozen=True)
class Caveat:
    """One reading instruction, and what would have to be true for a row to carry it."""

    ref: str
    #: The misreading, stated as the wrong belief rather than as the right one. §5's
    #: negative #4 is checked against this list, so it has to name what goes wrong.
    misreading: str
    #: Path plus reproducer, per this repo's citation convention. A bare section ID names
    #: neither a repo nor a file, and three sessions in a row could not resolve one.
    source: str
    #: The column that answers it on a row, or `None` where no such column can exist.
    column: str | None = None
    #: Why not, when `column` is `None`. Printed verbatim in the ledger.
    why_not: str = ""


#: The denominator for §5's negative #4, enumerated **before** the brief was built so it
#: could not be chosen to fit the result. These are exactly `README.md`'s five reading
#: instructions for `D`, and nothing else belongs here: this is the list the brief is
#: measured against, not a list of everything worth knowing.
#:
#: **It is a copy of a living document, and `tests/test_reading_instructions.py` is what
#: makes the copy fail loudly rather than drift** (`2026-08-03 §C30`, §5's negative #3).
#: Adding a sixth instruction to that README section without adding it here omits it
#: SILENTLY, and the brief goes on reading as complete, which is negative #4 arriving one
#: document away from where anyone was watching. Ordered by the date of the finding; README
#: interleaves them differently because its `3b` qualifies its `3`, so the guard is over the
#: set and the declared count rather than the sequence.
READING_INSTRUCTIONS: tuple[Caveat, ...] = (
    Caveat(
        ref="2026-08-01 §A17",
        misreading="a falling D means the market is getting safer",
        source="docs/design/amendments-2026-08-01.md §A17, "
               "docs/analysis/reproduce_report_gate.py::c21_a17_is_partial",
        column="unwind_state",
    ),
    Caveat(
        ref="2026-08-01 §A21",
        misreading="Phi measures positioning, and the weight table adjusts it",
        source="docs/design/amendments-2026-08-03.md §C22, "
               "docs/analysis/reproduce_report_gate.py::c22_ceiling_and_identity",
        why_not="computable on every row and IDENTICAL on every row, so no value "
                "distinguishes a market-week where it bites. It is a statement about the "
                "construction of Phi, and futures.weight_sensitivity.flat_phi_identity is "
                "where a reader checks it.",
    ),
    Caveat(
        ref="2026-08-01 §A22",
        misreading="the rankings survive the weights being wrong, so any number derived "
                   "from the weights is safe",
        source="docs/design/amendments-2026-08-01.md §A22, "
               "docs/analysis/reproduce_weight_sensitivity.py::main",
        why_not="a property of a pooled RANKING under a sweep of whole weight tables, so it "
                "needs a panel and a set of variants. One row has neither. Run "
                "futures.weight_sensitivity.sweep beside the ranking it qualifies.",
    ),
    Caveat(
        ref="2026-08-02 §B2",
        misreading="D already accounts for exits being correlated across markets",
        source="docs/design/amendments-2026-08-02.md §B2, "
               "docs/analysis/reproduce.py::commonality, "
               "docs/analysis/reproduce_report_gate.py::c24_already_exposed",
        column="beta",
    ),
    Caveat(
        ref="2026-08-03 §C3",
        misreading="the weight sensitivity measured over the pooled universe transfers to "
                   "this market",
        source="docs/design/amendments-2026-08-03.md §C3, §C8, §C23, §C29, "
               "docs/analysis/reproduce_w_sd_band.py::asymmetry_across_the_band, "
               "docs/analysis/reproduce_stratum.py::c29_the_rule_is_vacuous_the_split_is_not",
        column="stratum",
    ),
)

#: What a non-`scored` cell means, so that "not yet scoreable" and "scored, and low" cannot
#: render identically. That is the first degenerate input §2 of the handoff lists, and a
#: blank cell says the second.
SCORE_STATE_NOTES = {
    "scored": "",
    "warmup": "all three factors are present and the trailing percentile window has not "
              "filled. This market-week is too early, not safe. It will score later.",
    "no_crowding": "the crowding factor is null on this row, so no D was computed. See "
                   "futures.coverage.coverage_ladder for the rung this market dies at.",
    "no_illiquidity": "the illiquidity factor is null on this row, so no D was computed. "
                      "See futures.coverage.coverage_ladder for the rung this market dies "
                      "at.",
    "no_fragility": "the fragility factor is null on this row, so no D was computed. See "
                    "futures.coverage.coverage_ladder for the rung this market dies at.",
}

#: What `unwind_state` says about §A17, in words. `indeterminate` is deliberately as long
#: as the others: it is an answer, and the rendering must not make it look like a gap.
UNWIND_NOTES = {
    "not_falling": "D did not fall this week, so §A17's warning does not apply here.",
    "mid_exit": "D fell while the crowding category was liquidating. This is §A17's case: "
                "the market is partway out of the door, NOT safer.",
    "falling_not_exit": "D fell under a decisive flow state that is not the crowd leaving. "
                        "Read the flow state beside it.",
    "indeterminate": "INDETERMINATE. The flow state this week carries no answer either way, "
                     "which is the majority of falling weeks. Do NOT read the fall as "
                     "safety and do not read it as an exit.",
}

#: The other way `unwind_state` reaches `indeterminate`, and it means something different:
#: no previous scored week, so there is no change to read rather than a change nobody can
#: interpret. Both are indeterminate and a reader acts differently on each.
NO_DELTA_NOTE = ("INDETERMINATE. There is no previous scored week to difference against, so "
                 "D has no change this week. Nothing is being withheld and nothing is "
                 "reassuring.")


class BriefError(ValueError):
    """The frame cannot support a brief that states its own gaps."""


def market_brief(scored: pd.DataFrame, market_code: str, report_date=None, *,
                 side: str = "sell", ladder: pd.DataFrame | None = None) -> dict:
    """One market-week, assembled. Pure selection: nothing here is computed.

    `scored` is an `add_composite(...)` frame that has been through
    `composite.add_score_state`, and optionally `composite.add_unwind_state` and
    `commonality.add_commonality`. The first is required rather than applied here, because
    without it the brief cannot tell a market that is not yet scoreable from one that scored
    low, and a brief that gets that wrong is worse than no brief. The other two are
    optional and their absence is **declared** in the ledger rather than passed over, which
    is the whole of §5's negative #4.

    `ladder` is a `coverage.coverage_ladder(...)` frame, keyed on `market_code`. Optional
    for the same reason and reported the same way.

    Returns a dict; `format_brief` renders it. Kept apart so a caller can assert on the
    values without parsing markdown, which is how `tests/test_brief.py` checks that the
    ledger names its gaps.
    """
    if side not in ("sell", "buy"):
        raise BriefError(f"side must be 'sell' or 'buy', got {side!r}")
    state_column = f"score_state_{side}"
    if state_column not in scored.columns:
        raise BriefError(
            f"{state_column!r} is missing. Run `composite.add_score_state` first: without "
            f"it a null D renders the same whether the series is too young or a factor is "
            f"absent, and those mean opposite things (`2026-08-03 §C20`).")

    row = _one_row(scored, market_code, report_date)
    state = str(row[state_column])
    if state not in SCORE_STATES:
        raise BriefError(f"unknown score state {state!r}; expected one of {SCORE_STATES}")

    crowding = "crowding_long" if side == "sell" else "crowding_short"
    brief = {
        "market_name": row.get("market_name"),
        "market_code": market_code,
        "report_date": pd.Timestamp(row["report_date"]),
        "side": side,
        "score_state": state,
        "score_state_note": SCORE_STATE_NOTES[state],
        # `None` unless the row scored. §A.10 says report D as a percentile of its own
        # history and never as a level, so the raw product travels only as an audit term
        # beside a percentile that exists, never as a stand-in for one that does not.
        "damage_pct": _value(row, f"damage_{side}_pct") if state == "scored" else None,
        "damage": _value(row, f"damage_{side}") if state == "scored" else None,
        "crowding": _value(row, crowding),
        "illiquidity": _value(row, f"illiquidity_{side}"),
        "fragility": _value(row, "fragility"),
        "phi": _value(row, "phi"),
        "phi_ceiling": _value(row, "phi_denominator_covered"),
        # Never summed, never netted, and named by side so a total row cannot be added
        # without someone deciding to. Their sum describes an event that cannot occur.
        "q_sell": _value(row, "q_sell"),
        "q_buy": _value(row, "q_buy"),
        "flow_state": row.get("flow_state"),
        "d_damage_pct": _value(row, f"d_damage_{side}_pct"),
        "unwind_state": row.get(f"unwind_state_{side}"),
        "beta": _value(row, "beta"),
        "stratum": row.get("stratum"),
        "venue": row.get("venue"),
        "coverage": _coverage(ladder, market_code),
    }
    brief["caveats"] = caveat_ledger(brief)
    return brief


def caveat_ledger(brief: dict) -> tuple[dict, ...]:
    """A status for every one of `READING_INSTRUCTIONS`, including the ones not carried.

    The enumeration is fixed and the ledger is over all of it, so a caveat cannot drop out
    of the output by being absent from the frame: absence becomes `not_carried` with the
    reason, which is the difference between a brief that states its gaps and one that has
    them.
    """
    out = []
    for caveat in READING_INSTRUCTIONS:
        if caveat.column is None:
            status, detail = NOT_CARRIED, caveat.why_not
        elif caveat.column not in _STATUS_OF:
            # A new carrier column has to be given a status function rather than falling
            # through to a generic one: "is this value present" is not the same question as
            # "does this value answer the caveat", which is `§C22`'s whole distinction.
            raise BriefError(
                f"{caveat.ref} names carrier column {caveat.column!r} and no status "
                f"function knows how to read it. Add one to `_STATUS_OF`.")
        else:
            status, detail = _STATUS_OF[caveat.column](brief)
        out.append({"ref": caveat.ref, "misreading": caveat.misreading,
                    "status": status, "detail": detail, "source": caveat.source})
    return tuple(out)


def format_brief(brief: dict) -> str:
    """The brief as markdown, ledger and footer included. Both are mandatory, not options.

    There is no `include_caveats=False`. A flag that suppresses the ledger would turn this
    into the bare number the module exists to stop travelling on its own, and the failure
    mode §5's negative #4 names is precisely an output that looks complete.
    """
    name = brief["market_name"] or brief["market_code"]
    lines = [
        f"## {name} ({brief['market_code']}) — {brief['report_date'].date()}, "
        f"{brief['side']} side",
        "",
    ]

    if brief["score_state"] == "scored":
        lines += [
            "    D = C x I x Phi",
            f"      = {_fmt(brief['crowding'])} x {_fmt(brief['illiquidity'])} x "
            f"{_fmt(brief['fragility'])}",
            f"      = {_fmt(brief['damage'])}          (raw, for audit only)",
            f"    percentile of its own history = {_fmt(brief['damage_pct'])}   "
            f"<- the number to read",
        ]
    else:
        lines += [
            f"    D = NOT SCORED ({brief['score_state']})",
            f"        {brief['score_state_note']}",
            "        A null here is a state, not a low reading.",
        ]
    lines.append("")

    lines.append("### What this row carries")
    lines.append("")
    for label, text in _row_facts(brief):
        lines.append(f"- **{label}**: {text}")
    lines.append("")

    lines.append("### Reading instructions, and which of them this brief carries")
    lines.append("")
    lines.append("Enumerated before the brief was built, from `README.md`. A caveat this "
                 "brief cannot carry is named here rather than omitted.")
    lines.append("")
    for entry in brief["caveats"]:
        lines.append(f"- **{entry['ref']}** [{entry['status'].upper()}] misreading: "
                     f"{entry['misreading']}.")
        lines.append(f"  {entry['detail']}")
        lines.append(f"  _{entry['source']}_")
    lines.append("")

    lines += [
        "### Standing, and not derivable from the number",
        "",
        "- `D` estimates the SHAPE of a conditional loss distribution and not its location "
        "(`crowdmon_plain_language_summary.md` §A.10). It carries no first-moment content, "
        "it is not a forecast, and a ranking of it is not a trade list.",
        "- `Q_sell` and `Q_buy` are never added. Forced longs sell and forced shorts buy, "
        "so their sum describes an event that cannot occur.",
        "- This brief computes nothing: every figure is a column a shipped module returns. "
        "Exactly one of the caveats above (`score_state`) is not exposed by any other "
        "output, so the rest of the assembly is convenience rather than safety "
        "(`docs/design/amendments-2026-08-03.md` §C24).",
    ]
    return "\n".join(lines)


# ── internals ───────────────────────────────────────────────────────────────
def _row_facts(brief: dict) -> list[tuple[str, str]]:
    """The row-computable caveats, each stated or each declared absent. Never blank."""
    # The reason is spelled out in the D block above; repeating it here would bury the rest
    # of the row facts under it.
    facts = [("score state", f"`{brief['score_state']}`. D is a number on this row."
                             if brief["score_state"] == "scored" else
                             f"`{brief['score_state']}`, see the D block above.")]

    ceiling = brief["phi_ceiling"]
    facts.append((
        "Phi and its reachable ceiling",
        f"{_fmt(brief['phi'])} against a ceiling of {_fmt(ceiling)}, not 1.0. Spreading "
        f"counts toward open interest and carries no directional exit, so it sits in the "
        f"denominator and outside the numerator."
        if ceiling is not None else
        "no `phi_denominator_covered` on this frame, so the reachable ceiling is unknown "
        "and Phi must not be calibrated against 1.0."))

    q_sell, q_buy = brief["q_sell"], brief["q_buy"]
    if q_sell is not None or q_buy is not None:
        facts.append(("forceable size, by side and never combined",
                      f"Q_sell {_fmt(q_sell, 1)} contracts, Q_buy {_fmt(q_buy, 1)} "
                      f"contracts. Two separate events."))

    stratum = brief["stratum"]
    if stratum is None:
        facts.append(("stratum", "no `stratum` on this frame, so whether §C8's `w_SD` band "
                                 "binds on this market is unstated. Run "
                                 "`stratum.classify`."))
    else:
        venue_note = f" ({brief['venue']})" if brief["venue"] else ""
        facts.append(("stratum", f"`{stratum}`{venue_note}. "
                                 f"{BAND_ADVICE.get(stratum, 'no reading for this stratum')}."))

    coverage = brief["coverage"]
    if coverage is None:
        facts.append(("coverage", "no ladder supplied, so whether this market can be "
                                  "scored at all is unstated. Pass "
                                  "`coverage.coverage_ladder(...)`."))
    elif coverage.get("drops_at"):
        facts.append(("coverage", f"UNSCOREABLE: drops at `{coverage['drops_at']}`, over "
                                  f"{coverage['weeks']:,} weeks in the panel. Read "
                                  f"`drops_at` as the earliest rung with nothing left, not "
                                  f"the root cause."))
    else:
        facts.append(("coverage", f"reaches the end of the ladder, over "
                                  f"{coverage['weeks']:,} weeks in the panel."))

    unwind = brief["unwind_state"]
    if unwind is None:
        facts.append(("direction of change", "no `unwind_state` on this frame, so whether a "
                                             "fall in D is an exit is unstated here. Run "
                                             "`composite.add_unwind_state`."))
    else:
        flow = brief["flow_state"] or "none recorded"
        facts.append(("direction of change",
                      f"ΔD {_fmt(brief['d_damage_pct'])}, flow state `{flow}`, "
                      f"`{unwind}`. {_unwind_note(brief)}"))
    return facts


def _unwind_status(brief: dict) -> tuple[str, str]:
    unwind = brief.get("unwind_state")
    if unwind is None:
        return NOT_CARRIED, ("no 'unwind_state' on this frame. Run "
                             "`composite.add_unwind_state` with a `flow.decompose` frame.")
    if unwind == "indeterminate":
        return INDETERMINATE, _unwind_note(brief)
    return CARRIED, _unwind_note(brief)


def _unwind_note(brief: dict) -> str:
    if brief["unwind_state"] == "indeterminate" and brief["d_damage_pct"] is None:
        return NO_DELTA_NOTE
    return UNWIND_NOTES[brief["unwind_state"]]


def _beta_status(brief: dict) -> tuple[str, str]:
    beta = brief.get("beta")
    if beta is None:
        return NOT_CARRIED, ("no 'beta' on this frame. Run `commonality.add_commonality` "
                             "with a `commonality_betas` series to attach it.")
    return CARRIED, (f"beta = {beta:,.4f}. A high D in a market whose exits move with "
                     f"everyone else's is worse than the same D in a market with its own "
                     f"door, and nothing in the composite says so. Read it beside D, never "
                     f"inside it.")


def _stratum_status(brief: dict) -> tuple[str, str]:
    """`§C8`'s operating rule as a per-row answer, which is what §4 of the handoff asked for.

    Note what this does and does not settle. It answers "does the `w_SD` band bind on this
    market?", which is the question a reader holding one `D` actually has. It does **not**
    make the obligation live: `§C23` measured that no panel today carries both a `pct(D)`
    and a market on the band-required side, so the answer is currently `no` on every
    scoreable row. That is a fact about coverage, and `§C29` is where it is recorded.
    """
    stratum = brief.get("stratum")
    if stratum is None:
        return NOT_CARRIED, ("no 'stratum' on this frame. Run `stratum.classify` to attach "
                             "it, and `stratum.stratum_summary` to see the split it "
                             "derived.")
    if stratum not in BAND_ADVICE:
        return NOT_CARRIED, (f"stratum {stratum!r} is not one of {STRATA}, so §C8's rule "
                             f"has no reading for it.")
    return CARRIED, f"`{stratum}`. {BAND_ADVICE[stratum]}."


#: One status function per carrier column. A dict rather than a chain of `elif`, so adding a
#: carrier without deciding how to read it fails in `caveat_ledger` instead of defaulting.
_STATUS_OF = {"unwind_state": _unwind_status, "beta": _beta_status,
              "stratum": _stratum_status}


def _coverage(ladder: pd.DataFrame | None, market_code: str) -> dict | None:
    if ladder is None or ladder.empty:
        return None
    rows = ladder[ladder["market_code"] == market_code]
    if rows.empty:
        return None
    row = rows.iloc[0]
    drops = row.get("drops_at")
    return {"drops_at": None if pd.isna(drops) else str(drops),
            "weeks": int(row["weeks"]) if "weeks" in row else None}


def _one_row(scored: pd.DataFrame, market_code: str, report_date=None) -> pd.Series:
    rows = scored[scored["market_code"] == market_code]
    if rows.empty:
        raise BriefError(f"no rows for market_code {market_code!r}")
    stamp = (pd.to_datetime(rows["report_date"]).max() if report_date is None
             else pd.Timestamp(report_date))
    rows = rows[pd.to_datetime(rows["report_date"]) == stamp]
    if rows.empty:
        raise BriefError(f"no row for {market_code!r} on {stamp.date()}")
    if len(rows) > 1:
        raise BriefError(
            f"{market_code!r} has {len(rows)} rows on {stamp.date()}. A brief describes one "
            f"market-week, and a frame spanning report types or `combined` settings holds "
            f"more than one; filter before calling.")
    return rows.iloc[0]


def _value(row: pd.Series, column: str) -> float | None:
    """A float, or `None`. Never imputed and never defaulted to zero."""
    if column not in row.index:
        return None
    value = pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0]
    return None if pd.isna(value) else float(value)


def _fmt(value: float | None, decimals: int = 4) -> str:
    """`null` renders as the word, because a blank reads as a small number."""
    return "null" if value is None else f"{value:,.{decimals}f}"
