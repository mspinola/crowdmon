"""Exit pressure: how long does the forced side take to get out? (appendix A.5, spec §8)

The full form is

    T = Q / (kappa · V)

days to liquidate, where `Q` is the fragility-weighted position that must exit, `V` is
daily volume, and `kappa` (0.2) is the share of it a forced seller can take before the
impact assumption stops holding.

**`V` now exists**, and this module's header used to say it did not. `volume.py` supplies it
from exchange volume `cotdata` already stores, so `T` is a real duration for every market
that joins.

What changed is a measurement, not a dependency. ADR-0007 step 2 is still on ice and nobody
owns it, and that was never what blocked this. Whole-market volume was always in the store,
under a `cotdata` parameter named `front` that reads like front-month and is not. See
`volume.py` for the two proofs: open interest matching the CFTC to the contract on 25 of 26
markets, and curve concentration ordering exactly as contract structure predicts.

So this module now does three things and still refuses the fourth:

1. **`T = Q/(kappa V)`**, the real figure, whenever a volume is supplied. `volume.add_volume`
   supplies both a calm trailing ADV and §A.5's stress-conditioned `V_stress`, and neither is
   today's realised volume: during a selloff realised volume rises, so a spot denominator
   makes `T` *fall* exactly as liquidity is being consumed.
2. **`Q_sell / OI` and `Q_buy / OI` remain**, and are still what ranks a market with no volume
   join. Open interest is exactly known and needs no join, but it is a *stock* where volume is
   a *flow*, so it says how large the forced position is relative to the market rather than
   how many days it takes to leave. The two are **not** interchangeable: measured on the
   latest panel their rank correlation is 0.585, and Class III Milk sits 19th by `Q/OI` and
   2nd by `T`. That divergence is the whole argument for the join.
3. **Both denominators are reported and neither is "the" answer.** Stress volume is not
   reliably the conservative one: 9 of 25 markets trade MORE under stress, so `T_stress` is
   shorter than `T_calm` there. Which one binds is a property of the market.
4. **Never estimate a volume.** A fabricated denominator under the headline number of the
   whole system is worse than a missing one, because a missing number is visibly missing and
   an estimated one is not. `days_to_liquidate` is `None` without a volume, and the column is
   present and null rather than absent, so a caller who forgets to check gets nulls rather
   than a plausible figure.
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
                 stress_volume: pd.Series | None = None,
                 kappa: float = cfg.KAPPA) -> pd.DataFrame:
    """Add the OI-denominated pressure ratios to a `market_fragility` frame.

    Both directions, separately and always. The asymmetry between them is frequently the
    most informative single number available: it is what distinguishes a market whose longs
    can be forced out from one whose shorts can be squeezed, and collapsing it into one
    figure throws away the only part that names a direction.

    `volume` and `stress_volume` are optional Series aligned to `fragility`'s index, in
    contracts per day, as `volume.add_volume` emits them. When present, `dtl_sell`/`dtl_buy`
    and `dtl_sell_stress`/`dtl_buy_stress` are populated; when absent they are null columns
    rather than missing ones, so a downstream `.sort_values("dtl_sell")` fails loudly on
    nulls instead of silently ranking on something else.

    Neither denominator may be a spot volume. Both of `add_volume`'s outputs are trailing
    aggregates for that reason (§A.5's volume-spike trap), and passing today's reading here
    would reintroduce exactly the artifact they exist to avoid.
    """
    if fragility.empty:
        return fragility
    out = fragility.copy()
    oi = pd.to_numeric(out["open_interest"], errors="coerce")
    valid = oi > 0
    for side in ("sell", "buy"):
        q = pd.to_numeric(out[f"q_{side}"], errors="coerce")
        out[f"q_{side}_over_oi"] = (q / oi).where(valid)
        for suffix, source in (("", volume), ("_stress", stress_volume)):
            if source is None:
                out[f"dtl_{side}{suffix}"] = pd.NA
            else:
                v = pd.to_numeric(source, errors="coerce").reindex(out.index)
                out[f"dtl_{side}{suffix}"] = (q / (kappa * v)).where(v > 0)
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
