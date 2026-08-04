"""Which population a market belongs to, so `2026-08-03 §C8`'s rule can be applied.

§4 of [`../../../docs/handoffs/2026-08-03-report-layer.md`](../../../docs/handoffs/2026-08-03-report-layer.md).
`§C8` ends with an operating rule:

> Anyone publishing a `D` percentile on a power or gas basis market should publish the band
> beside it; on a classic outright the band is a footnote.

Until this module existed the rule was written down, measured, and **structurally
unenforceable**: the classification lived only in `docs/analysis/reproduce.py::_spec_class`,
where no consumer could reach it. `2026-08-03 §C11` is the precedent for why that matters —
`rank_markets` documented an alignment requirement instead of checking it, and the
requirement was then found unmet.

## Three populations, not two, and the middle one is the correction

`2026-08-03 §C14` measured this and the obvious cut gets it wrong. A **venue** split alone
puts 41 codes on the outright side because they trade on NYMEX and COMEX rather than on
Nodal, and seven of those are differentials. A differential is not a small outright: the
normalisation ladder computes a position value and a spread does not have one, so
`P . M . F` on a spread whose `F` oscillates around zero is not a smaller notional, it is
not a notional at all. Same class of error as the `backadj` trap: a number is produced, it
is finite, and it means nothing.

| stratum | what it is | what `§C8` says |
|---|---|---|
| `outright` | a classic tradeable contract | the `w_SD` band is a footnote |
| `certificate` | RECs, carbon allowances, PJM and ERCOT zones, gas basis | **publish the band** |
| `differential` | a spread, crack or basis-versus pair | the ladder cannot value it at all |

## What this deliberately does not decide

**It classifies; it does not gate.** Nothing here drops a row, and `D` is unchanged. §A.9
has no term for a stratum, as it has none for §A.6 or §A.8.

**The obligation is vacuous today and the classification is not.** `2026-08-03 §C23`
measured that no panel currently holds both a `pct(D)` and a market on the band-required
side: the current-state panel is 1,051 weeks and zero certificates, the vintage panel has
the certificates and is short of the percentile's `min_periods`. So nobody has to publish a
band yet. That is a fact about coverage rather than about this function, which still answers
the reader's question on every row — "does the band bind here?" — and answers it `no` with a
reason. See `2026-08-03 §C29`.

## The heuristic is a heuristic, and it is auditable on purpose

`DIFFERENTIAL_TOKENS` is pattern matching over `market_name`, which is the only signal the
COT rows carry. It reproduces `§C13` and `§C14` exactly on the real panel
(`tests/test_stratum_live.py`), and `differential_matches` exists so the token that caught
each market can be read rather than trusted. `/` in particular is broad: it is there because
`WTI HOUSTON ARGUS/WTI TR MO` needs it, and any future outright with a slash in its name
would be caught by it wrongly.

No count is hardcoded anywhere here, per §4's degenerate input: the covered universe is 45
markets across two report types rather than 25 (`§C12`), the number is report-week
dependent, and a classifier carrying a count is wrong on arrival. `stratum_summary` derives
the split from the frame and prints what it derived.
"""
from __future__ import annotations

import pandas as pd

#: Venues whose whole book is environmental or power certificates: RECs, carbon allowances,
#: PJM and ERCOT zones, gas basis. `2026-08-02 §B31` measures these at 76% of the
#: Disaggregated universe, which is why a "cross-market" result over that panel is mostly
#: about ERCOT and PJM rather than about futures.
CERTIFICATE_VENUES = frozenset({"ICE FUTURES ENERGY DIV", "NODAL EXCHANGE"})

#: Substrings that make a name a spread rather than a position, matched against the name
#: with its venue suffix removed. From `2026-08-03 §C14`, where the seven codes they catch
#: are the complete list on the vintage panel rather than examples.
DIFFERENTIAL_TOKENS = (" VS ", " VS.", "/", " SPR", "CRACK", "BALMO", " PL ")

#: Every value `stratum` can take, in the order `stratum_summary` reports them.
STRATA = ("outright", "certificate", "differential")

#: `§C8`'s operating rule, one line per stratum, as a value rather than as prose beside the
#: code. This is the whole point of the module: a rule a consumer can apply.
BAND_ADVICE = {
    "outright": "the w_SD band is a footnote here: across the classic outrights the two "
                "weight tables agree closely on the cross-market ranking",
    "certificate": "PUBLISH THE w_SD BAND beside this percentile. On the power, gas basis "
                   "and carbon book the two weight tables can disagree about which of this "
                   "market's own weeks were the fragile ones, to the point of inverting",
    "differential": "this is a spread, not a position. The normalisation ladder computes a "
                    "position VALUE and a differential does not have one, so a notional or "
                    "a risk-unit figure here is finite and meaningless",
}

#: Markets on this side of the split are the ones `§C8`'s obligation actually names.
BAND_REQUIRED = frozenset({"certificate"})


class StratumError(ValueError):
    """The frame cannot be classified."""


def venue(names: pd.Series) -> pd.Series:
    """The exchange half of a CFTC `market_name`, which is everything after the last ` - `.

    Parses on 100% of rows of both real panels (`2026-08-03 §C23`). Returns the whole name
    for a row with no separator rather than a null, because a name that does not split is a
    name whose venue is unknown, and a null there would be read as "no venue" instead.
    """
    return names.astype("string").str.rsplit(" - ", n=1).str[-1].str.strip()


def classify(frame: pd.DataFrame, *, column: str = "market_name") -> pd.DataFrame:
    """Add `venue` and `stratum`. Never drops a row and never inner-joins.

    Order matters and is not arbitrary: the venue test runs first, because every row on a
    certificate venue is a certificate whatever its name looks like, and several of them
    carry tokens that would otherwise read as a differential (`PJM.N ILLINOIS HUB` variants
    among them).
    """
    if column not in frame.columns:
        raise StratumError(
            f"{column!r} is missing, so a stratum cannot be derived. The COT rows carry no "
            f"other signal for this: there is no venue field, only the name.")
    out = frame.copy()
    names = out[column].astype("string")
    out["venue"] = venue(names)
    head = names.str.rsplit(" - ", n=1).str[0]

    stratum = pd.Series("outright", index=out.index, dtype=object)
    is_differential = head.fillna("").apply(
        lambda h: any(token in h for token in DIFFERENTIAL_TOKENS))
    stratum[is_differential] = "differential"
    stratum[out["venue"].isin(CERTIFICATE_VENUES)] = "certificate"
    stratum[names.isna()] = pd.NA
    out["stratum"] = stratum
    return out


def stratum_summary(frame: pd.DataFrame, *, column: str = "market_name") -> pd.DataFrame:
    """The split this frame actually has, derived and printed rather than assumed.

    §4 of the handoff asks for exactly this and gives the reason: the covered universe is
    report-week dependent and spans two report types, so a classifier that hardcoded a count
    would be wrong on arrival. Counts **markets**, because the stratum is a property of an
    instrument and repeating it per week would say more about panel length than about the
    universe.
    """
    classified = frame if "stratum" in frame.columns else classify(frame, column=column)
    if "market_code" not in classified.columns:
        raise StratumError("market_code is missing, so markets cannot be counted")
    markets = classified.drop_duplicates("market_code")
    rows = []
    for name in STRATA:
        part = markets[markets["stratum"] == name]
        rows.append({"stratum": name, "markets": len(part),
                     "share": len(part) / len(markets) if len(markets) else 0.0,
                     "band_required": name in BAND_REQUIRED,
                     "example": part[column].iloc[0] if len(part) else ""})
    unknown = int(markets["stratum"].isna().sum())
    if unknown:
        rows.append({"stratum": "unknown", "markets": unknown,
                     "share": unknown / len(markets), "band_required": False,
                     "example": ""})
    return pd.DataFrame(rows)


def differential_matches(frame: pd.DataFrame, *,
                         column: str = "market_name") -> pd.DataFrame:
    """Which token caught each differential, so the heuristic can be read not trusted.

    `DIFFERENTIAL_TOKENS` is pattern matching over a display label and nothing more. It
    reproduces `§C14`'s seven codes exactly on the real panel, and that is evidence rather
    than a guarantee: `/` is broad enough to catch a future outright whose name happens to
    carry a slash. This function is how that gets noticed.
    """
    classified = frame if "stratum" in frame.columns else classify(frame, column=column)
    diffs = classified[classified["stratum"] == "differential"].drop_duplicates("market_code")
    head = diffs[column].astype("string").str.rsplit(" - ", n=1).str[0]
    matched = head.apply(
        lambda h: ", ".join(t.strip() or "/" for t in DIFFERENTIAL_TOKENS if t in (h or "")))
    return pd.DataFrame({"market_code": diffs["market_code"].to_numpy(),
                         "market_name": diffs[column].to_numpy(),
                         "matched_on": matched.to_numpy()})


def format_strata(summary: pd.DataFrame) -> str:
    """The split as text, for a walkthrough or a run log."""
    if summary.empty:
        return "no markets"
    lines = []
    for _, row in summary.iterrows():
        # Flagged only where there is something to flag. On a panel with no certificates
        # the label beside a zero would read as an obligation rather than as an absence,
        # which is the same failure as a blank `D` cell reading as a low one.
        flag = "  BAND REQUIRED" if row["band_required"] and row["markets"] else ""
        lines.append(f"{row['stratum']:<13} {int(row['markets']):>4} markets  "
                     f"{row['share']:>6.1%}{flag}")
        if row["example"]:
            lines.append(f"              e.g. {row['example']}")
    return "\n".join(lines)
