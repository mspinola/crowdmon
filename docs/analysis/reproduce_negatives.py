"""Reproducer for §5 of `docs/handoffs/2026-08-03-report-layer.md`, the pre-registered
negatives, and for `docs/design/amendments-2026-08-03.md` §C30.

    COTDATA_STORE=/tmp/anything python docs/analysis/reproduce_negatives.py

**Needs no store**, unlike every other reproducer here: everything it counts is a document
or a module. The env var is set only because `cotdata` guards on it at import. That is the
point of the finding rather than a convenience: §5's negative #3 is about hand-maintained
strings, and a string is not something the store can confirm or deny.

Deterministic, and it re-derives every figure §C30 quotes rather than restating them.
"""
import re
from pathlib import Path

from crowdmon.futures import brief as module
from crowdmon.futures.brief import READING_INSTRUCTIONS
from crowdmon.futures.composite import SCORE_STATES, UNWIND_STATES

REPO = Path(__file__).resolve().parents[2]

#: The four outcomes §5 pre-registered, in its order, with the section that settled each.
NEGATIVES = {
    1: ("most caveats are not row-computable (R<=3, E==0)",
        "FALSE. §C20-§C24 measured R=4, E=1 strict and R=5, E=2 lenient"),
    2: ("the brief adds nothing the modules do not already give",
        "TRUE, and discharged. §C24: E=1, so the footer labels the assembly convenience"),
    3: ("the caveats cannot be carried without going stale anyway",
        "TRUE, and was NOT discharged until §C30. Measured below"),
    4: ("the brief carries some caveats and silently omits others",
        "TRUE of the outcome, met by §5's escape clause: it names its gaps on every render"),
}


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def readme_entries() -> list[tuple[str, str]]:
    """The numbered reading instructions in `README.md`, as (number, finding)."""
    text = (REPO / "README.md").read_text(encoding="utf-8")
    section = text[text.index("### Reading `D` on live output"):]
    section = section[:section.index("**These ")]
    starts = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^\*\*(\d+b?)\.\s", section)]
    out = []
    for (number, lo), (_, hi) in zip(starts, starts[1:] + [("", len(section))]):
        out.append((number, re.findall(r"\(`(20\d{2}-\d{2}-\d{2} §[A-Z]\d+)`\)",
                                       section[lo:hi])[0]))
    return out


def c30_the_ledger_is_a_copy(entries: list[tuple[str, str]]) -> None:
    """§C30. What the brief's safety case is actually made of, counted."""
    rule("C30. The enumeration is a copy of a living document, and nothing diffed it")
    shipped = [c.ref for c in READING_INSTRUCTIONS]
    readme = [ref for _, ref in entries]

    print(f"{'README':<8} {'finding':<18} {'ledger position':<16} same order?")
    for number, ref in entries:
        position = shipped.index(ref) + 1 if ref in shipped else None
        print(f"{number:<8} {ref:<18} {str(position):<16} "
              f"{'yes' if position == readme.index(ref) + 1 else 'NO'}")

    print(f"\nREADME instructions {len(readme)}, ledger entries {len(shipped)}, "
          f"set equal: {set(readme) == set(shipped)}, sequence equal: {readme == shipped}")
    print("  -> the copy had already drifted in the one respect nothing was checking, and")
    print("     the drift is harmless. A dropped entry is the same failure and is not.")


def c30_three_copies_and_thirteen_citations() -> None:
    """§C30. Negative #3's "a hand-maintained string somewhere", counted rather than agreed."""
    rule("C30. Three hand-maintained copies, and where each one's source lives")
    copies = [
        ("READING_INSTRUCTIONS", len(READING_INSTRUCTIONS), "README.md, prose"),
        ("SCORE_STATE_NOTES", len(module.SCORE_STATE_NOTES),
         "composite.SCORE_STATES, a tuple"),
        ("UNWIND_NOTES", len(module.UNWIND_NOTES), "composite.UNWIND_STATES, a tuple"),
    ]
    for name, size, source in copies:
        print(f"  {name:<22} {size} entries   copied from {source}")
    print(f"\n  SCORE_STATE_NOTES covers SCORE_STATES: "
          f"{set(module.SCORE_STATE_NOTES) == set(SCORE_STATES)}")
    print(f"  UNWIND_NOTES covers UNWIND_STATES:     "
          f"{set(module.UNWIND_NOTES) == set(UNWIND_STATES)}")

    paths, reproducers, unresolved = 0, 0, []
    for caveat in READING_INSTRUCTIONS:
        for part in (p.strip() for p in caveat.source.split(",")):
            if "::" in part:
                reproducers += 1
                path, function = (p.strip() for p in part.split("::"))
                target = REPO / path
                if not (target.exists() and re.search(
                        rf"(?m)^def {re.escape(function)}\b",
                        target.read_text(encoding="utf-8"))):
                    unresolved.append(part)
            elif part.split(" ")[0].endswith(".md"):
                # The path is the first token; the `§C8, §C23` that follow are what
                # `tests/test_references.py` already resolves.
                paths += 1
                if not (REPO / part.split(" ")[0]).exists():
                    unresolved.append(part)

    print(f"\ncitation fragments carried into the artifact: {paths} document paths, "
          f"{reproducers} reproducer functions")
    print(f"  unresolved right now: {len(unresolved)} {unresolved}")
    print("  every one is checked by tests/test_reading_instructions.py, and none was")
    print("  checked before it: test_references.py resolves the §C3 half of a citation and")
    print("  test_brief.py asserts 'docs/' and '::' appear, which a rename passes.")


def negatives_adjudicated() -> None:
    """§5's four outcomes, each answered. The handoff exists to find out which is true."""
    rule("§5 of the handoff: which of the pre-registered negatives was true")
    for number, (claim, verdict) in NEGATIVES.items():
        print(f"\n  #{number} {claim}")
        print(f"      {verdict}")
    print("\n  -> more than one is true at once, which the handoff did not anticipate: it")
    print("     lists them as alternatives. #2 and #4 were adjudicated when the brief")
    print("     shipped; #3 was not, and it is the one that can turn #4 back on later.")


def main() -> None:
    entries = readme_entries()
    c30_the_ledger_is_a_copy(entries)
    c30_three_copies_and_thirteen_citations()
    negatives_adjudicated()


if __name__ == "__main__":
    main()
