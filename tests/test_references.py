"""Every `§B34`-style amendment reference in this repo resolves to a section that exists.

**Why this test exists, and it is the whole of §3 of the b-series-recovery handoff.**
`§B33` names neither a repo nor a file. Three sessions in a row read that citation, searched
`git log` on `main`, found nothing, and concluded the sections did not exist. They did: they
were one `git show` away on a branch nobody thought to check, and the second of those
sessions spent itself re-deriving work that was already done and then recorded a wrong
definition of `A_agnostic` because the right one was on that branch (`2026-08-03 §C4`).

The convention going forward is **path plus reproducer**:

    docs/design/amendments-2026-08-02.md §B34
    docs/analysis/reproduce.py::template_direction_agnostic

Both are checkable by a session with no context. But 368 bare `§X##` references already
exist across 42 files, and rewriting prose is not the fix; making the bare form *fail
loudly* is. So this test resolves every one of them against the sections actually defined in
`docs/design/amendments-*.md`, and fails on any that does not land.

**Unresolvable references are marked, never deleted.** A reference that cannot be located is
a visible gap and a finding: deleting it makes the gap invisible, which is exactly how this
one survived three sessions. `KNOWN_UNRESOLVED` below carries each with a reason and a place
to look, and an entry that becomes resolvable fails too, so the allowlist cannot rot.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: Files worth scanning. Amendment IDs appear in prose, in module docstrings and in test
#: assertion messages, and the last of those is where a stale one does the most damage.
SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".claude", "node_modules", ".ruff_cache"}

#: `## B34. The median asymmetry ...` in a dated amendments file defines `B34`.
#: **Any letter, not `[ABC]`.** The series letter advances with the date (A is 08-01, B is
#: 08-02, C is 08-03), so a hardcoded set means the first amendment file of a new day defines
#: nothing this resolver can see and every citation into it silently stops being checked.
#: Found on 2026-08-04, when `D1` was the first section of a new file (`2026-08-04 §D1`).
_DEFINITION = re.compile(r"(?m)^##\s+([A-Z]\d+)\.")

#: `§B34`, `§B33-B37`, `§C1-C4`, `§A21-A22`, `§B33-§B37`. Deliberately does NOT match the
#: appendix's `§A.2`, which is a section of `crowdmon_plain_language_summary.md` and a
#: different namespace: the dot is the whole distinction and it is load-bearing.
_REFERENCE = re.compile(r"§§?([A-Z])(\d+)(?:\s*[-–]\s*§?([A-Z])?(\d+))?")

#: Bare IDs that genuinely do not resolve in this checkout, each with where it lives.
#: An entry here is a RECORDED GAP, not a suppression: the test below also fails if one
#: becomes resolvable, so a merge that closes a gap forces the note to be removed.
KNOWN_UNRESOLVED: dict[str, str] = {
    # Recorded per this file's own instruction: found before being listed, and where it
    # went is named. `D11` is taken by crowdmon#63 (branch
    # `claude/backlog-tranche-landed`, "handoff §6: the tranche landed"), open and unmerged
    # when `§D12` was written. Both branches could see the number was claimed, so `§D12`
    # skips it rather than creating the fifth counter collision this repo has had. When #63
    # merges, `test_the_known_gaps_are_still_gaps` fails and forces this line out.
    "D11": "crowdmon#63, branch claude/backlog-tranche-landed, unmerged. See §D12's header.",
    # Empty, and that is the healthy state. The last entry was `C5`, which lived on
    # crowdmon#42 while this test was being written and resolved when that PR merged, at
    # which point `test_the_known_gaps_are_still_gaps` failed and forced its removal. That
    # is the mechanism working: an allowlist nobody prunes becomes a list of lies.
}


def _scan_files() -> list[Path]:
    out = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(REPO).parts):
            continue
        out.append(path)
    return sorted(out)


def _defined_sections() -> set[str]:
    found: set[str] = set()
    for path in sorted((REPO / "docs" / "design").glob("amendments-*.md")):
        found.update(_DEFINITION.findall(path.read_text(encoding="utf-8")))
    return found


def _referenced_sections() -> dict[str, set[str]]:
    """Every referenced ID, mapped to the files referencing it. Ranges are expanded."""
    refs: dict[str, set[str]] = {}
    for path in _scan_files():
        if path.name == Path(__file__).name:
            continue  # this file names IDs as data, not as citations
        text = path.read_text(encoding="utf-8", errors="ignore")
        for letter, first, end_letter, last in _REFERENCE.findall(text):
            ids = [f"{letter}{first}"]
            if last and (not end_letter or end_letter == letter):
                lo, hi = int(first), int(last)
                # A sane range only. `§B31-2026` is not a range, and neither is a hyphen
                # that happens to precede a number in running prose.
                if lo < hi <= lo + 40:
                    ids = [f"{letter}{n}" for n in range(lo, hi + 1)]
            for sid in ids:
                refs.setdefault(sid, set()).add(str(path.relative_to(REPO)))
    return refs


def test_the_amendment_files_define_a_contiguous_run_per_letter():
    """A hole in the numbering is either a lost section or an unrecorded one.

    Both have happened. `B33-B37` went missing for a day because they were never pushed,
    and this is the cheapest check that would have caught it from the other side: `B32`
    followed by nothing while four handoffs cited `B33`.
    """
    defined = _defined_sections()
    assert defined, "no amendment sections found at all; the heading format must have moved"
    for letter in sorted({sid[0] for sid in defined}):
        nums = sorted(int(sid[1:]) for sid in defined if sid[0] == letter)
        assert nums[0] == 1, f"{letter}-series starts at {letter}{nums[0]}, not {letter}1"
        holes = [f"{letter}{n}" for n in range(1, nums[-1]) if n not in nums]
        unexplained = [h for h in holes if h not in KNOWN_UNRESOLVED]
        assert not unexplained, (
            f"{letter}-series has unexplained gaps: {unexplained}. A missing section is "
            f"either work that was lost or work that landed on another branch. Find it "
            f"before adding it to KNOWN_UNRESOLVED, and record where it went."
        )


def test_every_amendment_reference_in_the_repo_resolves():
    """The bare `§B34` form must fail loudly rather than silently, which is §3's whole ask."""
    defined = _defined_sections()
    referenced = _referenced_sections()

    unresolved = {sid: files for sid, files in referenced.items() if sid not in defined}
    unexpected = {sid: files for sid, files in unresolved.items()
                  if sid not in KNOWN_UNRESOLVED}

    assert not unexpected, (
        "amendment references that resolve to nothing:\n"
        + "\n".join(f"  §{sid}  cited in {sorted(files)}" for sid, files in
                    sorted(unexpected.items()))
        + "\n\nEither the section was never written, or it exists on an unmerged branch. "
          "Search ALL refs before concluding the former:\n"
          "  git log --all --oneline -- docs/design/amendments-*.md\n"
          "If it is genuinely elsewhere, add it to KNOWN_UNRESOLVED with a reason and a "
          "place to look. Do NOT delete the citation: an unresolvable reference is a "
          "finding, and deleting it is what made the last one invisible for three sessions."
    )


def test_the_known_gaps_are_still_gaps():
    """An allowlist nobody prunes becomes a list of lies. This prunes it by failing.

    Not parametrized over `KNOWN_UNRESOLVED`, deliberately. An empty dict would make
    `pytest.mark.parametrize` emit a SKIP, and `bin/check_skips.py` would then see a skip
    reason no profile allows: a test that guards an empty allowlist must PASS, not vanish.
    """
    defined = _defined_sections()
    resolved_now = sorted(sid for sid in KNOWN_UNRESOLVED if sid in defined)
    assert not resolved_now, (
        "these KNOWN_UNRESOLVED entries now resolve, so they are stale and must be removed "
        "along with any prose explaining the gap:\n"
        + "\n".join(f"  §{sid}: {KNOWN_UNRESOLVED[sid]}" for sid in resolved_now)
    )


def test_the_scan_actually_reaches_the_documents_it_claims_to():
    """A resolver that silently scanned nothing would pass every assertion above."""
    referenced = _referenced_sections()
    files = {f for files in referenced.values() for f in files}

    assert len(referenced) > 50, (
        f"only {len(referenced)} distinct sections referenced; the repo carried 66 defined "
        f"and hundreds of citations when this was written, so the regex or the walk broke"
    )
    assert len(files) > 25, f"only {len(files)} files carry a reference; expected 40-odd"
    for expected in ("docs/design/amendments-2026-08-02.md",
                     "docs/design/crowdmon_futures_cot_module.md",
                     "CLAUDE.md"):
        assert any(f == expected for f in files), f"{expected} was not scanned"
