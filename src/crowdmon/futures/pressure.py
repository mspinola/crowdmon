"""Exit pressure: how long does the forced side take to get out? (appendix A.5, spec §8)

The full form is

    T = Q / (kappa · V)

days to liquidate, where `Q` is the fragility-weighted position that must exit, `V` is
daily volume, and `kappa` (0.2) is the share of it a forced seller can take before the
impact assumption stops holding.

**`V` does not exist in this workspace.** There is no per-contract volume source: ADR-0007
step 2, which would move the price side into `marketdata` and open the door to one, is on
ice and nobody owns it. So this module does two things and refuses a third:

1. **Now**: rank on `Q_sell / OI` and `Q_buy / OI`. Open interest is a defensible depth
   proxy — it is exactly known, published weekly beside the positioning it is being
   compared against, and it needs no join. It is a *stock* where volume is a *flow*, so it
   says how large the forced position is relative to the market rather than how many days
   it takes to leave, and the ranking it produces is ordinal, not a duration.
2. **Later**: `volume` is an optional argument and `T` is returned the moment one is
   passed. Nothing else has to change.
3. **Never**: estimate a volume. A fabricated denominator under the headline number of the
   whole system is worse than a missing one, because a missing number is visibly missing
   and an estimated one is not. `days_to_liquidate` is `None` when there is no volume, and
   the column is present and null rather than absent, so a caller who forgets to check
   gets nulls rather than a plausible figure.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg


class PressureError(ValueError):
    """The inputs cannot support an exit-capacity estimate."""


def exit_pressure(q: float, open_interest: float, *, volume: float | None = None,
                  kappa: float = cfg.KAPPA) -> dict:
    """One side's exit pressure. `days_to_liquidate` is `None` without a volume.

    `q` is one direction's fragility-weighted size (`Q_sell` **or** `Q_buy`, never their
    sum), which is why this takes a scalar: passing a combined figure has to be a
    deliberate act rather than something the signature invites.
    """
    if q is None or pd.isna(q) or q < 0:
        raise PressureError(
            f"q must be a non-negative one-sided quantity, got {q!r}. Q_sell and Q_buy are "
            f"both magnitudes; a negative value means a sign convention was lost.")
    oi = float(open_interest) if open_interest and open_interest > 0 else None
    return {
        "q": float(q),
        "open_interest": oi,
        "q_over_oi": (float(q) / oi) if oi else None,
        # The real figure, and it stays None until there is a volume to divide by.
        "days_to_liquidate": (float(q) / (kappa * float(volume)))
        if volume and volume > 0 else None,
        "kappa": kappa,
        "volume": float(volume) if volume else None,
    }


def rank_markets(fragility: pd.DataFrame, *, volume: pd.Series | None = None,
                 kappa: float = cfg.KAPPA) -> pd.DataFrame:
    """Add the OI-denominated pressure ratios to a `market_fragility` frame.

    Both directions, separately and always. The asymmetry between them is frequently the
    most informative single number available: it is what distinguishes a market whose longs
    can be forced out from one whose shorts can be squeezed, and collapsing it into one
    figure throws away the only part that names a direction.

    `volume` is an optional Series aligned to `fragility`'s index, in contracts per day.
    When present, `dtl_sell` and `dtl_buy` are populated; when absent they are null columns
    rather than missing ones, so a downstream `.sort_values("dtl_sell")` fails loudly on
    nulls instead of silently ranking on something else.
    """
    if fragility.empty:
        return fragility
    out = fragility.copy()
    oi = pd.to_numeric(out["open_interest"], errors="coerce")
    valid = oi > 0
    for side in ("sell", "buy"):
        q = pd.to_numeric(out[f"q_{side}"], errors="coerce")
        out[f"q_{side}_over_oi"] = (q / oi).where(valid)
        if volume is None:
            out[f"dtl_{side}"] = pd.NA
        else:
            v = pd.to_numeric(volume, errors="coerce").reindex(out.index)
            out[f"dtl_{side}"] = (q / (kappa * v)).where(v > 0)
    # The ratio of the two, which is the shape of the market in one number: above 1 the
    # long side is the fragile one, below 1 the short side is. Null where the denominator
    # is zero rather than infinite, because "no fragile shorts at all" is a statement about
    # coverage more often than about the market.
    qb = pd.to_numeric(out["q_buy"], errors="coerce")
    out["sell_to_buy"] = (pd.to_numeric(out["q_sell"], errors="coerce") / qb).where(qb > 0)
    return out


def top_by(fragility: pd.DataFrame, column: str, *, n: int = 10,
           min_open_interest: float = 0) -> pd.DataFrame:
    """The `n` largest markets on `column`, with the floor stated rather than assumed.

    `min_open_interest` matters more than it looks. `Q/OI` is a ratio, and a market with
    600 contracts of open interest can post an extreme one on a rounding error, so an
    unfiltered ranking of 279 markets is a ranking of the smallest ones. The floor is an
    argument with a default of 0 so that its effect on any published table is visible in
    the call rather than baked in here.
    """
    if fragility.empty or column not in fragility.columns:
        raise PressureError(f"cannot rank on {column!r}; have {list(fragility.columns)}")
    df = fragility
    if min_open_interest:
        df = df[pd.to_numeric(df["open_interest"], errors="coerce") >= min_open_interest]
    return df.sort_values(column, ascending=False).head(n).reset_index(drop=True)
