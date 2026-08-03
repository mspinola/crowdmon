"""The six-outcome shape classifier, and the two failures it exists to prevent.

`shape_labels` is the classifier every template amendment from B28 onward counts with, so an
error in it moves published percentages rather than crashing. Both known failures are silent:
labelling by fall-through mislabels a market with no hedger side, and a partial label map
turns an outcome into a null that a later `value_counts` simply omits.
"""
import pandas as pd
import pytest

from crowdmon.futures import SHAPE_KEYS, shape_labels
from crowdmon.futures.fragility import FragilityError


def label(stable, fragile, **kw):
    return shape_labels(pd.Series([stable]), pd.Series([fragile]), **kw).iloc[0]


@pytest.mark.parametrize("stable,fragile,expected", [
    (-100, +50, "fragile_long"),      # the cocoa / template direction
    (+100, -50, "fragile_short"),     # inverted, and TFF's MIRROR
    (-100, -50, "both_short"),
    (+100, +50, "both_long"),
    (-100, 0, "fragile_flat"),
    (+100, 0, "fragile_flat"),
    (0, +50, "no_stable_side"),
    (0, -50, "no_stable_side"),
    (0, 0, "no_stable_side"),
])
def test_every_sign_pair_gets_the_right_label(stable, fragile, expected):
    assert label(stable, fragile) == expected


def test_no_stable_side_is_never_reported_as_fragile_flat():
    """The MICRO GOLD bug, pinned. `stable == 0` is a market where the template is
    INEXPRESSIBLE, not false, and the fund there is large and directional. Fall-through
    labelling reported it as a fund-flat market, which is the opposite of what is true.

    Both orders are checked: `stable == 0` must win whatever the fragile leg does, including
    when the fragile leg is also flat.
    """
    for fragile in (+84_000, -84_000, 0):
        assert label(0, fragile) == "no_stable_side"
    assert label(-1, 0) == "fragile_flat"


def test_the_masks_are_exhaustive_over_a_grid():
    """Exhaustiveness is asserted rather than argued: nothing may fall through."""
    values = [-2, -1, 0, 1, 2]
    grid = pd.DataFrame([(a, b) for a in values for b in values], columns=["s", "f"])
    got = shape_labels(grid["s"], grid["f"])
    assert got.notna().all()
    assert set(got.unique()) <= set(SHAPE_KEYS)


def test_the_outcomes_are_disjoint_and_cover_the_frame():
    """What §1 of the handoff needs from a conditioning variable: the subsets a reader is
    invited to compare must partition the rows, not merely describe them."""
    grid = pd.DataFrame([(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)],
                        columns=["s", "f"])
    got = shape_labels(grid["s"], grid["f"])
    masks = {key: (got == key) for key in SHAPE_KEYS}
    # Exhaustive: every row is in some mask. Disjoint: no row is in two.
    stacked = pd.DataFrame(masks)
    assert (stacked.sum(axis=1) == 1).all()
    assert stacked.sum().sum() == len(grid)


def test_a_null_net_raises_rather_than_being_labelled():
    """A missing measurement is not a flat position. Silently calling it flat would put a
    market with no data into whichever bucket the sign comparison happened to reach."""
    with pytest.raises(FragilityError, match="exhaustive"):
        shape_labels(pd.Series([None], dtype="float64"), pd.Series([1.0]))


def test_a_partial_label_map_raises():
    """A map missing one key would `map` that outcome to NaN, which `value_counts` drops
    from a published table without anything failing."""
    partial = {k: k for k in SHAPE_KEYS if k != "no_stable_side"}
    with pytest.raises(FragilityError, match="no_stable_side"):
        shape_labels(pd.Series([0]), pd.Series([1]), labels=partial)


def test_a_full_label_map_renames_without_changing_the_classification():
    names = {k: k.upper() for k in SHAPE_KEYS}
    assert label(-100, 50, labels=names) == "FRAGILE_LONG"
    assert label(0, 50, labels=names) == "NO_STABLE_SIDE"


def test_the_two_reproducer_label_maps_are_complete_and_distinct():
    """`reproduce.py` and `reproduce_tff.py` each carry a display map for the same six
    outcomes. They were separate implementations until B33-B37; the maps that replaced them
    must stay complete, or a shape silently vanishes from a published crosstab."""
    import importlib.util
    import pathlib

    here = pathlib.Path(__file__).resolve().parent.parent / "docs" / "analysis"
    maps = {}
    for module, name in (("reproduce", "DISAGG_SHAPE_LABELS"),
                         ("reproduce_tff", "TFF_SHAPE_LABELS")):
        spec = importlib.util.spec_from_file_location(module, here / f"{module}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        maps[name] = getattr(mod, name)

    for name, mapping in maps.items():
        assert set(mapping) == set(SHAPE_KEYS), name
        assert len(set(mapping.values())) == len(SHAPE_KEYS), f"{name}: duplicate display name"
