"""Roll windows, and what they do to an exit-capacity estimate.

**This is NOT module spec §379's roll congestion, and nothing here satisfies §13 step 4.**
§379 asks for calendar spread volatility, bid-ask behaviour during roll windows, and the OI
migration rate front to next. All three need per-expiry data that does not exist anywhere in
this workspace:

| §379 component | needs | status |
|---|---|---|
| calendar spread volatility | two contract prices at once | no per-expiry price source (ADR-0007) |
| bid-ask behaviour | quote data | nothing in the stack carries quotes |
| OI migration front to next | per-expiry open interest | **the `Open Interest` column is whole-market** |

That last one looks available and is not. `cotdata.get_prices` returns an `Open Interest`
column which reads exactly like the front-contract figure a migration rate needs. Measured
against COT's whole-market total over 1,051 weeks per market, the ratio is **1.000** for GC,
SI, CL, ZC, NG, ZS, ZW and HG, with p5 no lower than 0.998. It is the same number COT reports.

**Two columns on one frame both look per-contract and neither is.** `volume.py` already
documents that `front` is whole-market despite the name; `Open Interest` is not even named
`front` and is also whole-market. A reader who has internalised the first will not expect the
second.

**What IS observable is the roll window's footprint in volume**, which is §379's "measurable,
predictable tax" arriving through the one door the data leaves open. The spread itself is
invisible; the volume around it is not.

**The number that matters is the ADV effect, not the roll-day ratio, and they differ by an
order of magnitude.** Volume on roll-window days runs a median **1.239x** baseline across 16
markets. That is a statement about roll days. `pressure.T = Q/(kappa.V)` is driven by a
*trailing mean* over 252 bars, so the effect is diluted by how few days those are. Measured
over the last four years, which is what `reproduce.py` section 17 prints:

| | median across 16 markets |
|---|---|
| roll-day volume ratio | 1.239x |
| share of bars inside a window | 21.8% |
| **ADV inflation from including them** | **1.0506x** |
| **so `T` is optimistic by** | **5.1%** |

Quoting the roll-day ratio beside `T` invites a reader to think the bias is roughly half. It
is roughly a twentieth.

**The two measures disagree in SIGN, not merely in size, so one cannot stand in for the
other.** On the last four years, **SI has MORE volume on roll days (ratio 1.244) and a LOWER
ADV from including them (0.983)**, because the ratio is a median and the ADV is a mean: the
days outside SI's window carry the fatter tail. NG does the same, 1.029 against 0.983. Anyone
reasoning from the ratio to the bias is wrong about those two in direction.

Which markets diverge depends on the lookback, so `reproduce.py` selects them from the data
rather than naming any. An earlier draft of this docstring named HO from full history, where
it diverges, and HO does not diverge over four years.

**So "optimistic by construction for every market" is false.** `T` is *pessimistic* for
**SI, NG, HO, RB and LE**, five of sixteen, which includes the refined-products complex that
a fuel-shock scenario cares most about.

**A roll-excluded ADV is a different estimator, not a cleaner one.** CL, NG, HO and RB roll
monthly, so **52-53% of all their days sit inside a 10-bar window**. Excluding them computes
crude's ADV on half the sample. Every function here reports the excluded-day share beside the
figure for that reason, and `roll_adjusted_adv` refuses rather than returns a number when too
little is left.

**Nothing here changes `pressure`'s ADV.** Moving `T` moves `I`, which moves `D`, which moves
every published figure and the §9 verdict's inputs. That is a calibration decision for a human,
and on these numbers the case is weak: **5.1% median, wrong-signed for five of sixteen
markets, and needing a half-sample estimator for the energy complex.**
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .volume import DEFAULT_ADV_WINDOW, VOLUME_SERIES

#: Bars before a roll counted as inside the window. Bars rather than calendar days, because
#: volume is a per-session quantity and a calendar window silently varies with holidays.
DEFAULT_WINDOW_BARS = 10

#: Below this share of usable days, a roll-excluded ADV is refused rather than returned. The
#: monthly-rolling energy complex sits near 0.47, so this admits it while excluding worse.
MIN_EXCLUDED_SHARE = 0.25

#: Columns `roll_window_stats` returns.
ROLL_COLUMNS = ["symbol", "rolls", "bars", "days_in_window", "share_in_window",
                "median_in", "median_out", "roll_day_ratio",
                "adv_all", "adv_excluded", "adv_inflation", "t_bias"]


class RollError(ValueError):
    """The inputs cannot support a roll-window estimate."""


def roll_calendar(symbol: str, *, index: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    """Roll dates plus bars-to-next-roll, aligned to a price index.

    Roll dates come from `cotdata.roll_dates`, which reads the Delivery Month column changing.
    That is **series-invariant**: identical across `backadj`, `unadj` and `propadj` for 47 of
    47 symbols carrying rolls (`2026-08-02 §B16`), because price adjustment rescales bars
    without moving a delivery month. It is the one place in this package where inheriting a
    default series costs nothing, and it stops being true the day rolls are inferred from
    price gaps instead.
    """
    import cotdata

    rolls = cotdata.roll_dates(symbol)
    if len(rolls) == 0:
        raise RollError(
            f"{symbol!r} has no roll dates. Either the producer did not carry a Delivery "
            f"Month, which is true of the Yahoo-sourced ETF proxies MME and MFS, or a "
            f"`Symbol` namedtuple was passed where a string was wanted, which returns empty "
            f"rather than raising. See `2026-08-02 §B16`.")
    if index is None:
        index = cotdata.get_prices(symbol, adjustment="unadj",
                                   volume=VOLUME_SERIES).index
    # Distance to the NEXT roll at or after each bar. Done with two searchsorteds rather than
    # a loop over rolls: a loop that writes a fixed span backwards from each roll lets a later
    # roll overwrite an earlier roll's countdown, which silently leaves every roll but the last
    # reading as though it were hundreds of bars away.
    roll_pos = np.unique(index.searchsorted(rolls))
    roll_pos = roll_pos[roll_pos < len(index)]
    bars_to = pd.Series(np.nan, index=index, dtype="float64")
    if len(roll_pos):
        bar = np.arange(len(index))
        nxt = np.searchsorted(roll_pos, bar, side="left")
        has_next = nxt < len(roll_pos)
        bars_to.iloc[bar[has_next]] = roll_pos[nxt[has_next]] - bar[has_next]
    out = pd.DataFrame({"bars_to_roll": bars_to}, index=index)
    out.attrs["rolls"] = len(rolls)
    out.attrs["symbol"] = symbol
    return out


def in_roll_window(symbol: str, *, window_bars: int = DEFAULT_WINDOW_BARS,
                   index: pd.DatetimeIndex | None = None) -> pd.Series:
    """Boolean mask, True on the `window_bars` bars up to and including each roll."""
    if window_bars < 1:
        raise RollError(f"window_bars must be at least 1, got {window_bars!r}.")
    cal = roll_calendar(symbol, index=index)
    return (cal["bars_to_roll"] <= window_bars) & cal["bars_to_roll"].notna()


def roll_window_stats(symbol: str, *, window_bars: int = DEFAULT_WINDOW_BARS,
                      adv_window: int = DEFAULT_ADV_WINDOW,
                      lookback_bars: int | None = None) -> pd.Series:
    """Every figure this module has, for one market, with its inputs beside it.

    Reports BOTH the roll-day ratio and the ADV effect because they are different questions
    and the first does not predict the second, even in sign. See the module docstring on HO.
    """
    import cotdata

    bars = cotdata.get_prices(symbol, adjustment="unadj", volume=VOLUME_SERIES)
    volume = pd.to_numeric(bars["Volume"], errors="coerce")
    volume = volume[volume > 0]
    if volume.empty:
        raise RollError(f"{symbol!r} has no positive volume, so no roll-window figure exists.")

    mask = in_roll_window(symbol, window_bars=window_bars, index=volume.index)
    frame = pd.DataFrame({"v": volume, "w": mask.reindex(volume.index).fillna(False)})

    tail = frame.tail(lookback_bars) if lookback_bars else frame
    inside, outside = tail.loc[tail["w"], "v"], tail.loc[~tail["w"], "v"]
    share = float(tail["w"].mean())

    # Both means over the SAME span of bars. Taking `tail(adv_window)` of each separately
    # would compare the last 252 bars against the last 252 NON-ROLL bars, which reach further
    # back, so the difference would carry a date effect as well as a roll effect.
    span = tail.tail(adv_window)
    adv_all = float(span["v"].mean())
    kept = span.loc[~span["w"], "v"]
    adv_excluded = float(kept.mean()) if len(kept) else float("nan")

    return pd.Series({
        "symbol": symbol,
        "rolls": int(mask.attrs.get("rolls", 0)) if hasattr(mask, "attrs") else np.nan,
        "bars": int(len(tail)),
        "days_in_window": int(tail["w"].sum()),
        "share_in_window": share,
        "median_in": float(inside.median()) if len(inside) else float("nan"),
        "median_out": float(outside.median()) if len(outside) else float("nan"),
        "roll_day_ratio": (float(inside.median() / outside.median())
                           if len(inside) and len(outside) and outside.median() else float("nan")),
        "adv_all": adv_all,
        "adv_excluded": adv_excluded,
        "adv_inflation": adv_all / adv_excluded if adv_excluded else float("nan"),
        "t_bias": (adv_all / adv_excluded - 1.0) if adv_excluded else float("nan"),
    })


def roll_adjusted_adv(symbol: str, *, window_bars: int = DEFAULT_WINDOW_BARS,
                      adv_window: int = DEFAULT_ADV_WINDOW) -> pd.Series:
    """ADV with roll-window bars excluded, **beside** the unadjusted one, never instead of it.

    Refuses when too little of the sample survives. A roll-excluded ADV is a different
    estimator rather than a cleaner one, and for the monthly-rolling energy complex it is
    computed on roughly half the days.
    """
    stats = roll_window_stats(symbol, window_bars=window_bars, adv_window=adv_window)
    excluded_share = 1.0 - float(stats["share_in_window"])
    if excluded_share < MIN_EXCLUDED_SHARE:
        raise RollError(
            f"{symbol!r} leaves only {excluded_share:.1%} of bars outside a {window_bars}-bar "
            f"roll window, below the {MIN_EXCLUDED_SHARE:.0%} floor. A roll-excluded ADV on "
            f"that sample is a different estimator, not a cleaner one.")
    return pd.Series({
        "symbol": symbol,
        "adv": stats["adv_all"],
        "adv_roll_excluded": stats["adv_excluded"],
        "inflation": stats["adv_inflation"],
        "excluded_share": excluded_share,
    })


def exit_collision(symbol: str, days_to_liquidate: float, *,
                   as_of=None, window_bars: int = DEFAULT_WINDOW_BARS) -> pd.Series:
    """Does a forced exit of `days_to_liquidate` sessions run into the next roll?

    `pressure.T` says how long the forced side needs. This says whether that period overlaps
    the window in which the whole market has to move anyway. It is a timing question and
    carries no claim about the cost, because the spread that would price it is not observable.
    """
    if not np.isfinite(days_to_liquidate) or days_to_liquidate < 0:
        raise RollError(f"days_to_liquidate must be a non-negative number, "
                        f"got {days_to_liquidate!r}.")
    cal = roll_calendar(symbol)
    if as_of is not None:
        cal = cal.loc[:pd.Timestamp(as_of)]
    if cal.empty:
        raise RollError(f"{symbol!r} has no bars at or before {as_of!r}.")
    bars_to = cal["bars_to_roll"].iloc[-1]
    bars_to = float(bars_to) if pd.notna(bars_to) else float("nan")
    return pd.Series({
        "symbol": symbol,
        "as_of": cal.index[-1],
        "bars_to_roll": bars_to,
        "days_to_liquidate": float(days_to_liquidate),
        "collides": bool(np.isfinite(bars_to) and days_to_liquidate >= bars_to),
        "already_in_window": bool(np.isfinite(bars_to) and bars_to <= window_bars),
    })


def format_roll_block(stats: pd.Series) -> str:
    """Every input beside its result, per house style, with the trap named in the output."""
    lines = [f"roll windows - {stats['symbol']}"]
    lines.append(f"  bars:                  {stats['bars']:>10,}   "
                 f"({stats['days_in_window']:,} inside a window, "
                 f"{stats['share_in_window']:.1%})")
    lines.append(f"  median volume in/out:  {stats['median_in']:>10,.0f} / "
                 f"{stats['median_out']:,.0f}")
    lines.append(f"  roll-day ratio:        {stats['roll_day_ratio']:>10.3f}   "
                 f"(a fact about roll DAYS, not about T)")
    lines.append(f"  ADV all / excluded:    {stats['adv_all']:>10,.0f} / "
                 f"{stats['adv_excluded']:,.0f}")
    lines.append(f"  ADV inflation:         {stats['adv_inflation']:>10.4f}   "
                 f"-> T is off by {stats['t_bias']:+.1%}")
    sign = "optimistic" if stats["t_bias"] > 0 else "PESSIMISTIC"
    lines.append(f"  so T is {sign} here. The ratio above does not predict this, "
                 f"even in sign.")
    if stats["share_in_window"] > 0.4:
        lines.append("  NOTE: monthly roller. A roll-excluded ADV here uses about half the "
                     "sample, which is a different estimator rather than a cleaner one.")
    return "\n".join(lines)
