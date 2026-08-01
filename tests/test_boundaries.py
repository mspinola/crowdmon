"""The seams this package exists to sit on.

crowdmon is a MONITOR. It reads data and produces measurements. Two things follow,
and neither is self-enforcing, because both fail silently: one convenient import and the
boundary is gone until somebody trips over it months later.

**Downward:** it may consume `cotdata` and `marketdata`, and nothing else from the
workspace. Not `cotmetrics` (which computes a different, unitless positioning index over
the same source, so importing it would give two disagreeing answers to one question), not
`npf` or `livebook` (strategy and execution, the layers above), and not `crucible` or
`crucible_stack`.

The `crucible` prohibition is the one worth explaining, because it looks arbitrary and is
not. The module spec's §9.4 standing caution says the CTA replication model must not become
a trading signal by drift: it is calibrated to reproduce CONSENSUS positioning, so trading
it means joining the crowded trade the system exists to warn about. The workspace rule is
"you are the intern, crucible is the judge", and a package that can import the judge can
render a verdict on its own output. Keeping the import out means a directional strategy
derived from this work has to leave the package to be validated, which is the seam.

**Upward:** neither `cotdata` nor `marketdata` may import this. They are producers; a
producer that knows about a consumer has stopped being one. That direction is checkable
from here because they are sibling checkouts on disk, so it is checked.

Modelled on crucible-stack/tests/test_boundaries.py (ADR-0004 action item 9), including
its canary: a guard that silently stops seeing its target passes forever.
"""
import ast
import pathlib

import pytest

PKG = pathlib.Path(__file__).resolve().parent.parent / "src" / "crowdmon"
WORKSPACE = pathlib.Path(__file__).resolve().parents[2]

# Workspace packages this one may NOT import. Note cotmetrics is here: it is a peer
# consumer of the same store, not a layer below.
FORBIDDEN_ROOTS = ("npf", "livebook", "cotmetrics", "crucible", "crucible_stack",
                   "cot_analyzer", "cotanalyzer", "npf_books", "cmr")

# The only workspace packages this one reaches for, plus the scientific-Python floor.
# Anything else is a new dependency and belongs in pyproject.toml as a deliberate choice,
# not discovered here by an import that happened to work on one machine.
ALLOWED_THIRD_PARTY = {"pandas", "numpy", "pyarrow", "cotdata", "marketdata"}


def _modules(root: pathlib.Path):
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in str(p))


def _imports(path: pathlib.Path) -> set[str]:
    """Every module name a file imports, INCLUDING function-local imports.

    Function-local ones matter more than usual here: the tempting way to sneak past a
    boundary is a deferred import inside the one function that needs it, which never shows
    up at the top of the file where a reader would notice it.
    """
    names = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def test_there_is_something_to_check():
    """A guard that silently stops seeing its target passes forever."""
    mods = _modules(PKG)
    assert len(mods) >= 3, f"boundary test stopped seeing the package: {len(mods)} modules"


@pytest.mark.parametrize("path", _modules(PKG), ids=lambda p: p.name)
def test_no_module_imports_a_strategy_or_a_peer_consumer(path):
    for name in _imports(path):
        root = name.split(".")[0]
        assert root not in FORBIDDEN_ROOTS, (
            f"{path.name} imports {name!r}. crowdmon is a monitor: it consumes "
            f"cotdata and marketdata and nothing else in the workspace. See this module's "
            f"docstring for why {root!r} in particular is out.")


@pytest.mark.parametrize("path", _modules(PKG), ids=lambda p: p.name)
def test_no_module_reaches_for_an_undeclared_dependency(path):
    import sys
    for name in _imports(path):
        root = name.split(".")[0]
        if root in sys.stdlib_module_names or root == "crowdmon":
            continue
        assert root in ALLOWED_THIRD_PARTY, (
            f"{path.name} imports {root!r}, which is neither stdlib nor declared. Add it "
            f"to pyproject.toml and to ALLOWED_THIRD_PARTY, or do not use it.")


@pytest.mark.parametrize("sibling", ["cotdata", "marketdata"])
def test_the_producers_do_not_import_this_consumer(sibling):
    """The other half of the seam. A producer that knows about a consumer is no longer a
    producer, and this is the direction that would be found last, because it breaks
    nothing here."""
    root = WORKSPACE / sibling / "src" / sibling
    if not root.exists():
        pytest.skip(f"{sibling} not checked out beside this repo")
    offenders = [p.name for p in _modules(root)
                 if any(n.split(".")[0] == "crowdmon" for n in _imports(p))]
    assert not offenders, (
        f"{sibling} imports crowdmon in {offenders}. The dependency runs one way: "
        f"producers write a store, consumers read it.")
