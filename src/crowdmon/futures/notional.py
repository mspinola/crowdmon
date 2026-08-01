"""Positioning in USD: contracts to notional. Module spec §5.2 rung 3.

    net_notional = net_contracts x point_value x price

Three decisions in that one line, and the first is the one that matters.

**1. The price must be UNADJUSTED, and this module refuses anything else.**

A back-adjusted continuous series is not a series of prices. It is a series of price
*changes* anchored at the present, so its historical levels are whatever makes the recent
end line up. Multiplying a contract count by one of those levels produces a number in no
units at all. Measured against the real store:

| Market | Date | Back-adjusted | Unadjusted | Notional error |
|---|---|---|---|---|
| GC | 2002-05-30 | 1282.00 | 325.50 | **+294%** |
| CL | 2004-12-13 | 146.48 | 41.01 | **+257%** |
| ZC | 2002-04-10 | 587.50 | 199.75 | **+194%** |
| GC | 2026-07-30 | 4100.10 | 4100.10 | +0.0% |

The last row is why this is a guard rather than a comment. **The error is exactly zero at
the present date and grows monotonically backwards**, because back-adjustment anchors on
the most recent contract. Every spot check anyone would actually run, on recent data,
passes perfectly, while the entire history a backtest is evaluated over is corrupted. The
offset is measurable directly: for CL it is 0.0000 today and 105.47 on 2004-12-13.

The sharpest single example in the store is crude on **2020-04-21**. Unadjusted it traded
at **+11.57**, an ordinary positive price. Back-adjusted the same bar reads **-27.52**.
The enormous roll gap out of the May 2020 contract, which had settled at -37.63 the day
before, is propagated backwards through every earlier bar. Crude actually traded below
zero on exactly ONE day; the back-adjusted series is below zero on 64.

A negative price is therefore not by itself a sign of the wrong series, and nothing here
rejects one: 2020-04-20 is real, and on that day a LONG position genuinely had negative
notional. What distinguishes the artifact is that it reports a negative price on days the
market was positive.

`cotdata`'s own API says so plainly: `unadj` is "raw front-month prices (absolute price /
point-value sizing)". This module simply refuses to be pointed anywhere else.

Volatility is the opposite case and belongs in `riskunits`: it needs correct percentage
RETURNS, which means the **ratio-adjusted** (`propadj`) series. So the two factors of
`net_notional x sigma` come from two different series, on purpose.

An earlier version of this paragraph said volatility wanted `backadj`. That was wrong.
Additive back-adjustment preserves absolute price CHANGES, not percentage returns, and its
accumulated roll gaps corrupt the denominator of every historical return: annualised vol
from `backadj` percent returns is 201x too high for soybeans, 182x too high for the 10-year
note, and 0.47x too LOW for gold, which never goes negative and so passes every
implausibility check. `riskunits` refuses it, with the full table and the reproducer.

**2. The price is taken as of the REPORT date, not the release date.** The positions were
held on the Tuesday, so that is what values them. Using the Friday price would silently turn
notional into a three-day mark-to-market, which is a different quantity that happens to look
like this one. No lookahead is introduced: the Tuesday price is known by the Friday release.

**3. Spreading never enters the net.** A spread position is a matched long and short held by
one trader, so it cancels by construction. It is reported separately as gross exposure,
because "how much risk is on" and "how much directional risk is on" are different questions
and only the second one nets.
"""
from __future__ import annotations

import pandas as pd

#: Columns ``add_notional`` adds.
NOTIONAL_COLUMNS = ["price", "price_date", "price_staleness_days", "net_contracts",
                    "net_notional_usd", "long_notional_usd", "short_notional_usd",
                    "gross_notional_usd", "oi_notional_usd"]

#: The only adjustment that yields a tradeable price level. See the module docstring.
NOTIONAL_ADJUSTMENT = "unadj"

#: How far back an as-of price lookup may reach. A Tuesday report date can fall on a market
#: holiday, so some tolerance is required, but a stale price silently valuing a position at
#: last month's level is worse than no answer. Five calendar days spans a long weekend plus
#: a holiday without reaching into the previous week's data.
DEFAULT_MAX_STALENESS_DAYS = 5


class NotionalError(RuntimeError):
    """The inputs would produce a number that is not notional."""


def _price_series(symbol: str, adjustment: str, price_field: str) -> pd.Series:
    import cotdata

    bars = cotdata.get_prices(symbol, adjustment=adjustment)
    if bars is None or bars.empty:
        return pd.Series(dtype="float64")
    if price_field not in bars.columns:
        raise NotionalError(
            f"{symbol}: price field {price_field!r} not in {list(bars.columns)}")
    s = pd.to_numeric(bars[price_field], errors="coerce").dropna()
    # Force nanosecond resolution on both sides of the later as-of join. The vintage store
    # round-trips report_date through parquet as datetime64[us] while the price index is
    # datetime64[ns], and merge_asof refuses mismatched resolutions outright rather than
    # coercing: "incompatible merge keys, must be the same type". Same pandas 2/3
    # resolution split that has bitten this stack before, and it only appears against a
    # real parquet-backed store, never against an in-memory fixture.
    s.index = pd.to_datetime(s.index).astype("datetime64[ns]")
    # Bars are stored float32. Widen once here so the multiplication below is float64 and
    # a multi-billion-dollar notional is not carrying float32's ~7 significant digits.
    return s.astype("float64").sort_index()


def add_notional(annotated: pd.DataFrame, *,
                 adjustment: str = NOTIONAL_ADJUSTMENT,
                 price_field: str = "Close",
                 price_on: str = "report_date",
                 max_staleness_days: int = DEFAULT_MAX_STALENESS_DAYS) -> pd.DataFrame:
    """Add USD notional to a frame already annotated by :class:`ContractMaster`.

    ``annotated`` needs ``symbol`` and ``point_value`` (from ``ContractMaster.annotate``)
    plus the canonical contract columns. Rows with no ``symbol``, no ``point_value``, or no
    price within ``max_staleness_days`` get null notional rather than being dropped: the
    same rule the contract master follows, so a partial panel is never silently returned as
    a whole one.

    ``price_on`` selects which date to value at, and defaults to ``report_date`` for the
    reason in the module docstring. ``release_date`` is available for a deliberate
    mark-to-market, and is not the same quantity.
    """
    if adjustment != NOTIONAL_ADJUSTMENT:
        raise NotionalError(
            f"refusing to compute notional from adjustment={adjustment!r}. Only "
            f"{NOTIONAL_ADJUSTMENT!r} carries tradeable price LEVELS. A back-adjusted "
            f"series carries price CHANGES anchored at the present, so its historical "
            f"levels are an artifact: measured error is +294% for gold in 2002 and +257% "
            f"for crude in 2004, and crude's series reaches -27.52, which is not a price. "
            f"The error is EXACTLY ZERO today and grows monotonically backwards, so no "
            f"spot check on recent data will ever catch it. Volatility is the opposite "
            f"case and belongs in riskunits, which wants back-adjusted returns.")

    required = {"symbol", "point_value", "long_contracts", "short_contracts", price_on}
    missing = sorted(required - set(annotated.columns))
    if missing:
        raise NotionalError(
            f"missing columns {missing}. Run ContractMaster.annotate first: notional needs "
            f"the multiplier, and the contract counts it applies to must already be scaled "
            f"to today's contract definition.")
    if annotated.empty:
        return annotated.assign(**{c: pd.Series(dtype="float64") for c in NOTIONAL_COLUMNS})

    out = annotated.copy()
    out[price_on] = pd.to_datetime(out[price_on]).astype("datetime64[ns]")

    # As-of join per symbol. merge_asof needs both sides globally sorted, and doing it per
    # symbol keeps each price series a single contiguous read rather than one giant frame.
    # float("nan"), not pd.NA: filling a float64 Series with pd.NA raises, and a numeric
    # column that silently became object dtype would make every downstream sum a surprise.
    price = pd.Series(float("nan"), index=out.index, dtype="float64")
    price_date = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    tol = pd.Timedelta(days=max_staleness_days)
    for sym, idx in out.groupby("symbol", dropna=True, sort=False).groups.items():
        series = _price_series(str(sym), adjustment, price_field)
        if series.empty:
            continue
        want = out.loc[idx, [price_on]].sort_values(price_on)
        merged = pd.merge_asof(
            want, pd.DataFrame({"_pd": series.index, "_px": series.to_numpy()}),
            left_on=price_on, right_on="_pd", direction="backward", tolerance=tol)
        merged.index = want.index
        price.loc[merged.index] = merged["_px"].to_numpy()
        price_date.loc[merged.index] = merged["_pd"].to_numpy()

    out["price"] = price
    out["price_date"] = price_date
    # How far the as-of lookup actually reached. Emitted rather than assumed: a holiday
    # week legitimately shifts it by a day or two, and anything larger means the price
    # series has a hole the caller should know about before trusting the number.
    out["price_staleness_days"] = (out[price_on] - out["price_date"]).dt.days

    lo = pd.to_numeric(out["long_contracts"], errors="coerce")
    sh = pd.to_numeric(out["short_contracts"], errors="coerce")
    sp = pd.to_numeric(out.get("spread_contracts"), errors="coerce") \
        if "spread_contracts" in out.columns else pd.Series(0.0, index=out.index)
    pv = pd.to_numeric(out["point_value"], errors="coerce")
    px = pd.to_numeric(out["price"], errors="coerce")
    unit = pv * px                       # USD per contract

    # A NEGATIVE price is not an error and must not be guarded against. WTI settled at
    # -$37.63 on 2020-04-20, and the unadjusted series records exactly that. On such a day
    # a LONG position genuinely has negative notional: the holder would pay to be relieved
    # of it. Anything downstream that assumes sign(notional) == sign(position) is wrong on
    # real data, which is why nothing here clips, absolutes, or rejects it.

    out["net_contracts"] = lo - sh
    out["net_notional_usd"] = out["net_contracts"] * unit
    out["long_notional_usd"] = lo * unit
    out["short_notional_usd"] = sh * unit
    # Gross INCLUDES spreading on both legs, because a spread is real exposure that has to
    # be rolled and margined even though it nets to nothing directionally.
    out["gross_notional_usd"] = (lo + sh + 2 * sp.fillna(0)) * unit
    out["oi_notional_usd"] = pd.to_numeric(
        out.get("open_interest"), errors="coerce") * unit
    return out


def coverage_report(with_notional: pd.DataFrame) -> pd.Series:
    """Why rows have no notional, counted. Meant to be printed beside any aggregate.

    A notional panel that silently covers 40% of its rows is not a panel, and the three
    reasons are different problems: no spec is a registry-universe question, no price is a
    vendor-coverage question, and a stale price is a data-hole question.
    """
    if with_notional.empty:
        return pd.Series(dtype="int64")
    have = with_notional["net_notional_usd"].notna()
    no_symbol = with_notional["symbol"].isna()
    no_price = ~no_symbol & with_notional["price"].isna()
    return pd.Series({
        "with_notional": int(have.sum()),
        "no_contract_spec": int(no_symbol.sum()),
        "no_price_within_tolerance": int(no_price.sum()),
        "total": len(with_notional),
    })
