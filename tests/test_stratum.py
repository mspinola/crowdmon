"""Which population a market is in, §4 of `docs/handoffs/2026-08-03-report-layer.md`.

The arithmetic is trivial; what is worth asserting is the two things `2026-08-03 §C14`
found the obvious classifier gets wrong, and the one property §4 demanded of any classifier
built here.

- **A venue split alone is not enough.** It puts differentials on the outright side because
  they trade on NYMEX and COMEX, and a differential is not a small outright: the ladder
  computes a position value and a spread does not have one.
- **A venue split is not optional either.** Several certificate names carry tokens that
  would otherwise read as a differential, so the venue test has to run first.
- **No count may be hardcoded** (§4's degenerate input): the covered universe is report-week
  dependent and spans two report types, so a classifier carrying a number is wrong on
  arrival. `stratum_summary` derives the split from whatever frame it is handed.
"""
import pandas as pd
import pytest

from crowdmon.futures import (
    BAND_ADVICE,
    BAND_REQUIRED,
    DIFFERENTIAL_TOKENS,
    STRATA,
    classify,
    differential_matches,
    format_strata,
    stratum_summary,
    venue,
)
from crowdmon.futures.stratum import StratumError

#: One of each, plus the two cases the naive classifiers get wrong.
NAMES = {
    "088691": ("GOLD - COMMODITY EXCHANGE INC.", "outright"),
    "023651": ("NATURAL GAS - NEW YORK MERCANTILE EXCHANGE", "outright"),
    "0676A5": ("WTI HOUSTON ARGUS/WTI TR MO - NEW YORK MERCANTILE EXCHANGE",
               "differential"),
    "86565A": ("GULF # 6 FUEL OIL CRACK - NEW YORK MERCANTILE EXCHANGE", "differential"),
    "064Z01": ("TRANSCO ZONE 6 BASIS - ICE FUTURES ENERGY DIV", "certificate"),
    "0642V1": ("PJM.N ILLINOIS HUB PEAK - NODAL EXCHANGE", "certificate"),
}


def _panel() -> pd.DataFrame:
    return pd.DataFrame([{"market_code": code, "market_name": name}
                         for code, (name, _) in NAMES.items()])


def test_each_population_is_labelled_the_way_C14_partitions_them():
    out = classify(_panel()).set_index("market_code")
    for code, (_, expected) in NAMES.items():
        assert out.loc[code, "stratum"] == expected, code
    assert set(out["stratum"]) <= set(STRATA)


def test_a_venue_split_alone_would_put_differentials_on_the_outright_side():
    """`§C14`'s correction, asserted rather than described.

    Both differentials here trade on NYMEX, so nothing about their venue distinguishes them
    from crude or gold. A classifier that stopped at the venue would call them outrights and
    a `D` on them would look ordinary.
    """
    out = classify(_panel())
    diffs = out[out["stratum"] == "differential"]
    assert len(diffs) == 2
    assert (diffs["venue"] == "NEW YORK MERCANTILE EXCHANGE").all(), (
        "the whole point of the correction is that the venue does NOT separate these")


def test_the_venue_test_runs_first_because_certificate_names_carry_the_tokens():
    """A certificate on a certificate venue stays a certificate however its name reads."""
    tricky = pd.DataFrame([{
        "market_code": "0642V9",
        "market_name": "PJM.N ILLINOIS HUB PEAK VS OFF PEAK - NODAL EXCHANGE"}])
    out = classify(tricky)
    assert out["stratum"].iloc[0] == "certificate"


def test_only_the_certificate_side_requires_the_band():
    """`§C8`'s rule, as a value a consumer reads rather than prose beside the code."""
    assert BAND_REQUIRED == {"certificate"}
    assert set(BAND_ADVICE) == set(STRATA), "every stratum needs a reading, or none is safe"
    assert "PUBLISH" in BAND_ADVICE["certificate"]
    assert "footnote" in BAND_ADVICE["outright"]
    assert "does not have one" in BAND_ADVICE["differential"]


def test_the_summary_derives_its_counts_and_carries_none():
    """§4: a classifier that hardcodes a count is wrong on arrival."""
    full = stratum_summary(classify(_panel()))
    assert dict(zip(full["stratum"], full["markets"])) == {
        "outright": 2, "certificate": 2, "differential": 2}
    assert full["share"].sum() == pytest.approx(1.0)

    half = stratum_summary(classify(_panel().head(2)))
    assert dict(zip(half["stratum"], half["markets"])) == {
        "outright": 2, "certificate": 0, "differential": 0}
    assert half.loc[half["stratum"] == "certificate", "band_required"].all()


def test_the_summary_counts_markets_and_not_market_weeks():
    """A stratum is a property of an instrument; per-week counts say only how long a panel
    is, which is the same keying error `coverage.py` exists to avoid."""
    repeated = pd.concat([_panel().assign(report_date=d)
                          for d in pd.date_range("2026-01-06", periods=9, freq="7D")])
    assert stratum_summary(classify(repeated))["markets"].sum() == len(NAMES)


def test_which_token_caught_each_differential_is_reportable():
    """`DIFFERENTIAL_TOKENS` is pattern matching over a display label and nothing more."""
    matches = differential_matches(classify(_panel())).set_index("market_code")
    assert matches.loc["0676A5", "matched_on"] == "/"
    assert "CRACK" in matches.loc["86565A", "matched_on"]
    assert set(matches.index) == {"0676A5", "86565A"}


def test_the_venue_is_everything_after_the_last_separator():
    names = pd.Series(["COCOA - ICE FUTURES U.S.", "NO SEPARATOR HERE"])
    assert list(venue(names)) == ["ICE FUTURES U.S.", "NO SEPARATOR HERE"]


def test_a_name_that_does_not_split_keeps_its_whole_self_rather_than_going_null():
    """A null venue reads as "no venue"; the truth is "the venue is unknown"."""
    out = classify(pd.DataFrame([{"market_code": "X", "market_name": "MYSTERY"}]))
    assert out["venue"].iloc[0] == "MYSTERY"
    assert out["stratum"].iloc[0] == "outright"


def test_a_missing_name_is_null_rather_than_guessed():
    out = classify(pd.DataFrame([{"market_code": "X", "market_name": None}]))
    assert pd.isna(out["stratum"].iloc[0])
    summary = stratum_summary(out)
    assert "unknown" in set(summary["stratum"]), "an unclassified market must be reported"


def test_classifying_never_drops_a_row():
    panel = _panel()
    assert len(classify(panel)) == len(panel)
    assert set(panel.columns) <= set(classify(panel).columns)


def test_a_frame_without_a_name_is_refused():
    with pytest.raises(StratumError, match="market_name"):
        classify(pd.DataFrame([{"market_code": "X"}]))


def test_the_split_renders_with_the_band_flag_visible():
    text = format_strata(stratum_summary(classify(_panel())))
    assert "BAND REQUIRED" in text
    assert text.count("BAND REQUIRED") == 1, "only the certificate side carries it"


def test_every_token_is_a_substring_test_and_none_is_empty():
    """An empty token would match every name and silently make the whole panel a spread."""
    assert all(token for token in DIFFERENTIAL_TOKENS)
    assert len(set(DIFFERENTIAL_TOKENS)) == len(DIFFERENTIAL_TOKENS)
