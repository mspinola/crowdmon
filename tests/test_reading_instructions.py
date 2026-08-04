"""`brief.READING_INSTRUCTIONS` is a copy of a living document, and this is the diff.

**§5's negative #3 of [`../docs/handoffs/2026-08-03-report-layer.md`](../docs/handoffs/2026-08-03-report-layer.md),
which was pre-registered and never adjudicated.** It says the caveats may turn out not to be
carryable without going stale anyway, because every candidate mechanism needs a
hand-maintained string somewhere, and that this would be a real finding about the class of
artifact rather than a shortfall of the brief.

It is true. `brief.READING_INSTRUCTIONS` is five hand-written `Caveat`s whose docstring says
they are "exactly `README.md`'s five reading instructions", and **nothing checked that**.
`tests/test_references.py` resolves the `§C3` half of a citation and stops there;
`tests/test_brief.py` asserts each source contains `docs/` and `::` as substrings, which a
renamed reproducer passes. So the enumeration could gain, lose or misname an entry and every
test in the suite would stay green, and the brief would go on printing a ledger over five and
reading as complete. That is §5's negative #4 arriving through the back door, one document
removed from where anyone was watching for it.

It is the same shape as the failure this repo already has a note about: a living document
copied into a second place opens a silent-regression window that closes only when someone
diffs the copies, and `crowdmon_futures_cot_module.md` lost 104 lines that way for a day.
The fix there was a pointer instead of a copy. A `Caveat` cannot be a pointer, because it
carries a carrier column and a status function, so the fix here is the other one: **make the
copy fail loudly when it diverges.**

Measured drift at the time of writing (`2026-08-03 §C30`): the set matched, every citation
resolved, and the ORDER did not. The docstring claimed README's order; the tuple was in
date order of the finding, which README interleaves differently because `3b` qualifies `3`.
Harmless in itself, and it is the whole point: the copy had already drifted in the one
respect nothing was checking, within a day of being written.
"""
from __future__ import annotations

import re
from pathlib import Path

from crowdmon.futures import brief as module
from crowdmon.futures.brief import READING_INSTRUCTIONS

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"

#: The section of `README.md` that `brief.py` names as its source.
_HEADING = "### Reading `D` on live output"

#: `**3b. That robustness is a statement about ...**` starts an entry. `3b` is a qualifier on
#: `3` rather than a fifth instruction, which is why the section counts four instructions and
#: five findings and why both numbers are correct.
_ENTRY = re.compile(r"(?m)^\*\*(\d+b?)\.\s")

#: Each entry closes with its finding, in this repo's citation form: ``(`2026-08-01 §A17`)``.
_CITATION = re.compile(r"\(`(20\d{2}-\d{2}-\d{2} §[A-Z]\d+)`\)")

#: `**These five are the denominator, and `futures/brief.py` carries three of them.**`
_DECLARED = re.compile(r"These (\w+) are the denominator")

#: Where the numbered entries stop and the section's own summary begins. The summary cites
#: findings too, so without this the last entry swallows them and reads as citing four.
_CLOSING = "**These "

_WORDS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def _section(text: str | None = None) -> str:
    text = README.read_text(encoding="utf-8") if text is None else text
    start = text.index(_HEADING)
    rest = text[start + len(_HEADING):]
    end = rest.find("\n### ")
    return rest if end < 0 else rest[:end]


def _readme_refs(section: str) -> list[str]:
    """The finding each numbered entry cites, in the order README lists them."""
    assert _CLOSING in section, (
        f"the section no longer carries its summary paragraph ({_CLOSING!r}), so the "
        f"numbered entries have no end and the last one absorbs whatever follows")
    section = section[:section.index(_CLOSING)]
    starts = [m.start() for m in _ENTRY.finditer(section)] + [len(section)]
    refs = []
    for lo, hi in zip(starts, starts[1:]):
        found = _CITATION.findall(section[lo:hi])
        assert len(found) == 1, (
            f"README entry starting {section[lo:lo + 40]!r} cites {len(found)} findings; "
            f"each reading instruction carries exactly one, and the ledger is keyed on it")
        refs.append(found[0])
    return refs


# ── the coupling itself ─────────────────────────────────────────────────────
def test_the_ledger_enumerates_exactly_the_readme_list():
    """Add a sixth reading instruction to README and this fails, which is the whole point.

    The brief's ship condition is that it carries every misreading on the enumerated list or
    NAMES the ones it does not. That condition is only as good as the enumeration: a caveat
    README knows about and `READING_INSTRUCTIONS` does not is omitted **silently**, and a
    silent omission in an artifact designed to leave the package is the failure mode §5's
    negative #4 calls the most dangerous.
    """
    readme = _readme_refs(_section())
    shipped = [c.ref for c in READING_INSTRUCTIONS]

    missing = [r for r in readme if r not in shipped]
    extra = [r for r in shipped if r not in readme]
    assert not missing and not extra, (
        f"README's reading instructions and `brief.READING_INSTRUCTIONS` have diverged.\n"
        f"  in README, not in the ledger: {missing}\n"
        f"  in the ledger, not in README: {extra}\n"
        f"Fix the ledger, not this test. A caveat README states and the brief omits is "
        f"omitted silently, and the brief still reads as complete.")


def test_the_section_declares_the_same_count_the_ledger_carries():
    """README says its own count in prose, and the prose is what a reader believes.

    It said "Four things" in the preamble and "These five are the denominator" in the
    closing paragraph for a day. Both were defensible (four numbered instructions, five
    findings) and together they were a contradiction a reader hits before reaching either
    number, so the section now states the reconciliation and this pins the denominator.
    """
    section = _section()
    declared = _DECLARED.search(section)
    assert declared, (
        f"{README.name} no longer declares its own denominator. The sentence "
        f"'These <n> are the denominator' is what a reader counts against, and the brief's "
        f"ship condition is stated over that count.")
    word = declared.group(1).lower()
    assert word in _WORDS, f"unparsed count word {word!r}; add it to _WORDS"
    assert _WORDS[word] == len(READING_INSTRUCTIONS), (
        f"README declares {word} reading instructions and the brief enumerates "
        f"{len(READING_INSTRUCTIONS)}")


def test_every_carrier_column_has_a_status_function():
    """`caveat_ledger` raises on an unknown carrier at render time; this catches it earlier.

    "Is this value present" is not "does this value answer the caveat" (`2026-08-03 §C22`),
    so a new carrier has to be given a reading rather than falling through to a generic one.
    A brief nobody renders in a test would otherwise ship the raise.
    """
    for caveat in READING_INSTRUCTIONS:
        if caveat.column is not None:
            assert caveat.column in module._STATUS_OF, (
                f"{caveat.ref} names carrier column {caveat.column!r} with no status "
                f"function")
        else:
            assert caveat.why_not, f"{caveat.ref} carries nothing and does not say why"


def test_the_two_note_tables_cover_the_states_they_speak_for():
    """The same hand-maintained copy, one level smaller and two more instances of it.

    `SCORE_STATE_NOTES` and `UNWIND_NOTES` duplicate enumerations that live in
    `composite.py`, and both are read by subscript. A state added there and not here raises
    `KeyError` on the first row that carries it, which for a rare state means the artifact
    crashes in front of a reader rather than in CI. Cheap to pin, and it is the same finding
    as the one above: the brief rests on three copies of other people's lists.
    """
    from crowdmon.futures.composite import SCORE_STATES, UNWIND_STATES

    assert set(module.SCORE_STATE_NOTES) == set(SCORE_STATES), (
        "SCORE_STATE_NOTES and composite.SCORE_STATES have diverged; every state needs a "
        "note, because the note is the whole reason a null D is not read as a low one")
    assert set(module.UNWIND_NOTES) == set(UNWIND_STATES), (
        "UNWIND_NOTES and composite.UNWIND_STATES have diverged")
    assert all(module.SCORE_STATE_NOTES[s] for s in SCORE_STATES if s != "scored")
    assert all(module.UNWIND_NOTES.values())


# ── the citations, resolved rather than pattern-matched ─────────────────────
def test_every_cited_path_and_reproducer_actually_resolves():
    """The other half of the convention, and the half nothing checked.

    `tests/test_references.py` resolves the `§C3` half of a citation against the amendment
    files. `tests/test_brief.py` asserts the source string contains `docs/` and `::`. A
    renamed reproducer function passes both and leaves the brief's reader, who by
    construction does not have the code, with a citation that goes nowhere.
    """
    for caveat in READING_INSTRUCTIONS:
        for part in (p.strip() for p in caveat.source.split(",")):
            if "::" in part:
                path, function = (p.strip() for p in part.split("::"))
                target = REPO / path
                assert target.exists(), f"{caveat.ref} cites missing file {path}"
                assert re.search(rf"(?m)^def {re.escape(function)}\b",
                                 target.read_text(encoding="utf-8")), (
                    f"{caveat.ref} cites {part}, and {path} defines no {function}. Rename "
                    f"the citation with the function, or the reader is sent nowhere.")
            else:
                # `docs/design/amendments-2026-08-01.md §A17`: the path is the first token,
                # the section IDs after it are what `test_references.py` already resolves.
                head = part.split(" ")[0]
                if head.endswith(".md"):
                    assert (REPO / head).exists(), f"{caveat.ref} cites missing doc {head}"


# ── the guard guards ────────────────────────────────────────────────────────
def test_the_parser_would_actually_see_a_sixth_instruction():
    """A resolver that silently scanned nothing would pass every assertion above.

    Same hazard as `test_references.py::test_the_scan_actually_reaches_the_documents_it_
    claims_to`, and worth the duplication: this file's entire value is that it notices a
    change in a document, so a parser that quietly matches nothing is not a weaker guard,
    it is no guard wearing a green tick.
    """
    live = _readme_refs(_section())
    assert len(live) == len(READING_INSTRUCTIONS) >= 5, (
        f"parsed {len(live)} entries out of README; the heading, the `**n.` form or the "
        f"citation form has moved and this file has stopped guarding anything")

    section = _section()
    synthetic = section.replace(_CLOSING, (
        "**5. A sixth reading instruction nobody told the brief about.** Prose prose. "
        "(`2026-08-04 §D1`)\n\n" + _CLOSING), 1)
    assert _readme_refs(synthetic) == live + ["2026-08-04 §D1"], (
        "the parser did not pick up an added entry, so it would not catch a real one")


def test_the_brief_still_names_the_document_it_copies():
    """A copy whose source is unnamed cannot be diffed by the next reader."""
    doc = module.__doc__ or ""
    assert "README.md" in doc or "README.md" in (module.READING_INSTRUCTIONS.__doc__ or "")
    source = (REPO / "src" / "crowdmon" / "futures" / "brief.py").read_text(encoding="utf-8")
    assert "README.md" in source
    assert "tests/test_reading_instructions.py" in source, (
        "the enumeration must point at the test that couples it to README, or the next "
        "person to edit it will not know the coupling exists")
