"""Concentration: CR4 and CR8, the numbers CFTC gives away. Module spec §6.2.

    CR4 = share of the net long (or short) side held by the four largest traders
    CR8 = the same for the eight largest

Published directly in every Disaggregated and TFF file, **zero percent null across the whole
twenty-year history and across all 279 markets in the latest week**, and unused by this
package until now. Module spec §6.2 calls this "the metric set that COT gives away free and
that has no cheap equity equivalent", and it is right: a 13F filer's concentration cannot be
observed at all, and here it arrives weekly at no cost and needs no prices, no volume and no
contract master.

**Concentration is not fragility, and the two answer different questions.** `Phi` asks what
*kind* of holder is on each side, weighting a category by how forceable it is. CR4 asks how
*few* holders there are, without knowing anything about who they are. A market can be
concentrated in patient hands (high CR4, low Phi) or diffuse among levered ones (low CR4,
high Phi), and the pair distinguishes cases that either number alone cannot.

**It is also not breadth-depth.** `breadth.decompose_breadth` counts traders per *category*
and asks whether a position grew by adding traders or by each holding more. CR4 counts the
largest traders in the *market* regardless of category, which is the only view here that
crosses category lines at all. A category can broaden while the market concentrates, if the
new arrivals are small and the existing giants keep growing.

## Two things to know before reading a CR number

**1. It is a share of the NET side, not of open interest.** CFTC computes CR on net
positions, so the denominator is the net long (or net short) total rather than gross or OI. A
CR4 of 45% does not mean four traders hold 45% of the market; it means they hold 45% of one
side's net. In a market where the net is small relative to gross, a high CR can describe a
modest absolute position.

**2. `CR8 >= CR4` always**, which makes their difference meaningful in its own right.
`cr8_minus_cr4` is the share held by traders five through eight, and it separates two very
different shapes: a market where four giants hold everything and nobody else matters (large
CR4, small gap) from one where eight comparable large traders share the side (moderate CR4,
large gap). The first has a single-point-of-failure problem; the second does not.

Measured on the latest Disaggregated week: median CR4 net long **45.7%**, median CR8
**61.8%**. Four traders hold nearly half of one side in the median market.
"""
from __future__ import annotations

import pandas as pd

from ..core.aggregate import DEFAULT_MIN_PERIODS, DEFAULT_WINDOW, standardise

#: One row per market-week. Concentration is a market property, repeated on every category
#: row in the canonical schema exactly as `open_interest` is, and it must not be summed
#: across categories for the same reason.
MARKET_KEY = ["report_date", "market_code", "report_type", "combined"]

#: The four published columns, as percentages in `[0, 100]`.
CR_COLUMNS = ["cr4_net_long", "cr4_net_short", "cr8_net_long", "cr8_net_short"]

CONCENTRATION_COLUMNS = ["cr4_net_long", "cr4_net_short", "cr8_net_long", "cr8_net_short",
                         "cr8_minus_cr4_long", "cr8_minus_cr4_short",
                         "cr4_max_side", "cr4_side"]


class ConcentrationError(ValueError):
    """The panel cannot support a concentration view."""


def market_concentration(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per market-week with the published ratios and the derived gap.

    Takes the canonical panel (category rows) and reduces it, using `max` rather than `sum`
    on every CR column: they are market properties repeated on each category row, and summing
    would multiply them by five and put CR4 above 100%.
    """
    missing = [c for c in [*MARKET_KEY, *CR_COLUMNS] if c not in panel.columns]
    if missing:
        raise ConcentrationError(
            f"missing columns for concentration: {missing}. CR4/CR8 are populated for "
            f"Disaggregated and TFF and absent from Legacy.")

    frame = panel.copy()
    for column in CR_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    out = frame.groupby(MARKET_KEY, dropna=False, sort=False).agg(
        market_name=("market_name", "first"),
        **{c: (c, "max") for c in CR_COLUMNS}).reset_index()

    # Traders five through eight. See the module docstring for why the gap is its own number.
    out["cr8_minus_cr4_long"] = out["cr8_net_long"] - out["cr4_net_long"]
    out["cr8_minus_cr4_short"] = out["cr8_net_short"] - out["cr4_net_short"]

    # The more concentrated side, and which one it is. A market is only as robust as its
    # thinner side, so the max is the one to rank on; the label stops it being read as a
    # direction, which it is not.
    out["cr4_max_side"] = out[["cr4_net_long", "cr4_net_short"]].max(axis=1)
    out["cr4_side"] = pd.Series("long", index=out.index).where(
        out["cr4_net_long"] >= out["cr4_net_short"], "short")

    _assert_bounds(out)
    return out


def add_concentration_extremity(concentration: pd.DataFrame, *,
                                column: str = "cr4_max_side",
                                window: str | int = DEFAULT_WINDOW,
                                min_periods: int = DEFAULT_MIN_PERIODS) -> pd.DataFrame:
    """Trailing z-score and percentile of concentration, per market.

    Concentration levels are not comparable across markets: a CR4 of 45% is unremarkable in a
    thin contract and would be a record in a deep one. What is comparable is where a market
    sits against its own history, which is the same argument `extremity` makes for
    positioning and the same machinery.
    """
    if column not in concentration.columns:
        raise ConcentrationError(f"{column!r} not present; run `market_concentration` first")
    return standardise(concentration, column,
                       by=["market_code", "report_type", "combined"],
                       date_column="report_date", window=window,
                       min_periods=min_periods, winsor=0.0)


def concentration_vs_fragility(concentration: pd.DataFrame,
                               fragility: pd.DataFrame) -> pd.DataFrame:
    """Join the two, so "few holders" and "forceable holders" can be read together.

    The four combinations are genuinely different markets, and neither number alone separates
    them:

    | | low `Phi` | high `Phi` |
    |---|---|---|
    | **low CR4** | diffuse and patient. The benign case | a broad crowd of forceable holders |
    | **high CR4** | a few large patient holders, often a hedger | **few holders, all forceable** |

    The bottom-right cell is the one worth finding, and it is the only cell that requires both
    measures to identify.
    """
    for name, frame, needed in (("concentration", concentration, "cr4_max_side"),
                                ("fragility", fragility, "phi")):
        if needed not in frame.columns:
            raise ConcentrationError(f"{name} frame is missing {needed!r}")
    keep = [*MARKET_KEY, "cr4_max_side", "cr4_side", "cr8_minus_cr4_long",
            "cr8_minus_cr4_short"]
    merged = fragility.merge(concentration[[c for c in keep if c in concentration.columns]],
                             on=MARKET_KEY, how="left")
    return merged


def quadrant(joined: pd.DataFrame, *, cr_threshold: float | None = None,
             phi_threshold: float | None = None) -> pd.Series:
    """Label each market-week by the table in `concentration_vs_fragility`.

    Thresholds default to the **cross-sectional medians of the frame passed in**, so the
    split is relative to the universe being looked at rather than to an absolute level nobody
    has justified. That makes the labels comparative by construction: exactly half the
    markets are "high CR4" in any week. Pass explicit values to fix them across runs, which
    is what a time series of quadrant membership would need.
    """
    cr = pd.to_numeric(joined["cr4_max_side"], errors="coerce")
    phi = pd.to_numeric(joined["phi"], errors="coerce")
    cr_cut = cr.median() if cr_threshold is None else cr_threshold
    phi_cut = phi.median() if phi_threshold is None else phi_threshold

    high_cr, high_phi = cr >= cr_cut, phi >= phi_cut
    known = cr.notna() & phi.notna()
    out = pd.Series(pd.NA, index=joined.index, dtype="object")
    out = out.mask(known & high_cr & high_phi, "few_and_forceable")
    out = out.mask(known & high_cr & ~high_phi, "few_and_patient")
    out = out.mask(known & ~high_cr & high_phi, "broad_and_forceable")
    out = out.mask(known & ~high_cr & ~high_phi, "diffuse_and_patient")
    return out


def _assert_bounds(out: pd.DataFrame) -> None:
    """CR values are percentages in `[0, 100]` and `CR8 >= CR4` by definition.

    Both hold on every row of the real store, so a breach means the columns were mapped from
    the wrong fields or summed rather than reduced. Checked on every computation, because the
    failure would otherwise surface as a plausible-looking ranking.
    """
    for column in CR_COLUMNS:
        values = pd.to_numeric(out[column], errors="coerce").dropna()
        if not values.empty and (values.min() < 0 or values.max() > 100):
            raise ConcentrationError(
                f"{column} outside [0, 100] (min {values.min():.2f}, max "
                f"{values.max():.2f}). CR columns are market properties repeated on every "
                f"category row; summing rather than reducing them produces exactly this.")
    for side in ("long", "short"):
        gap = pd.to_numeric(out[f"cr8_minus_cr4_{side}"], errors="coerce").dropna()
        if not gap.empty and gap.min() < 0:
            raise ConcentrationError(
                f"CR8 < CR4 on the {side} side by {-gap.min():.2f} points, which is "
                f"impossible: the eight largest traders include the four largest.")
