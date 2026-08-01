"""Contract master: CFTC market code to instrument, multiplier and currency.

Module spec §5.1. This is the join that layer 2 rests on, and it has three properties that
are easy to get wrong and expensive to get wrong quietly.

**1. Coverage is an output, not a side effect.** The vintage store holds every market CFTC
publishes (418 codes in the 2026 files); the registry names 49. An inner join would
therefore discard roughly 370 markets in silence, and a "cross-market" result computed
afterwards would describe whatever survived. So nothing here drops rows. ``annotate`` adds
spec columns and leaves them null where no spec exists, and ``coverage`` / ``unmatched``
report what would have been lost, for the caller to filter deliberately.

**2. A market code is not an instrument, and the mapping moves over time.** CFTC retires
and reissues codes. `cotdata.registry` records the predecessors in ``hist_codes``, and some
of them carry a **contract-size scale**: lumber's `058643` is 4.0, because the contract was
redefined. Multiplying an old row's contract count by today's point value without that
scale is wrong by 4x, and nothing about the result looks wrong.

`cotdata.get_cot` applies the scale when it stitches history for a symbol, but the VINTAGE
path does not: the canonicalisers work off the raw zip, keyed by the raw market code, with
no registry involved. So this is the layer that has to apply it, because it is the first
one that knows both the market code and the multiplier. It is latent today (the 2026
capture contains no retired codes) and becomes live the moment anyone backfills the vintage
store over earlier years, which is precisely when nobody will be looking for it.

``annotate`` therefore applies the scale **by default**. Forgetting the argument gives the
correct answer; you have to ask for the raw counts.

**3. Currency is checked rather than assumed.** All 47 specs are USD today, which removes
an FX layer the spec's §5.2 rung 3 would otherwise need. That is a fact about the current
universe, not a property of futures, so a non-USD contract arriving raises instead of
producing a USD-labelled number that is not USD.

Reads `cotdata.store.read_metadata()`, which is the one non-``__all__`` cotdata symbol this
package touches. ADR-0007 moves `metadata/` to `marketdata` in its step 2, so this is the
single call site to repoint when that happens.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Columns ``annotate`` adds. Kept explicit so a caller can drop them again cleanly, and so
#: a downstream module can assert on their presence rather than hoping.
SPEC_COLUMNS = ["symbol", "point_value", "tick_size", "tick_value", "currency",
                "margin", "exchange", "asset_class", "contract_scale",
                "is_historical_code"]

#: Contract counts, which the size scale applies to. Concentration ratios and trader counts
#: are NOT counts of contracts and must not be scaled: a ratio is unitless, and a redefined
#: contract does not change how many traders held it.
CONTRACT_COUNT_COLUMNS = ["long_contracts", "short_contracts", "spread_contracts",
                          "open_interest"]


class ContractMasterError(RuntimeError):
    """The join cannot be built, or would produce a number that lies about its units."""


@dataclass(frozen=True)
class ContractSpec:
    """One resolved instrument, as reached from one CFTC market code."""
    symbol: str
    market_code: str
    is_historical_code: bool
    contract_scale: float
    point_value: float
    tick_size: float
    tick_value: float
    currency: str
    margin: float
    exchange: str
    group: str
    name: str
    asset_class: str
    report_type: str


class ContractMaster:
    """market_code to :class:`ContractSpec`, plus the coverage report for what is missing.

    Built once and reused: it reads the registry and one small parquet, so construction is
    cheap, but the coverage report is worth computing once and printing beside results
    rather than recomputing per call.
    """

    def __init__(self, specs: dict[str, ContractSpec], *, registry_symbols,
                 price_tiers: dict[str, set[str]]):
        self._by_code = specs
        self._symbols = list(registry_symbols)
        self._price_tiers = price_tiers

    # ── construction ────────────────────────────────────────────────────────
    @classmethod
    def load(cls, *, require_usd: bool = True) -> ContractMaster:
        from cotdata import all_symbols, load_manifest, store
        from cotdata.registry import hist_code_scales

        raw = store.read_metadata()
        if raw is None or raw.empty:
            raise ContractMasterError(
                "no contract_specs table in the store. It is written by the Norgate "
                "producer's --metadata flag on the Windows box, so a replica that has "
                "never synced one cannot build a contract master.")
        if require_usd:
            bad = sorted(set(raw["Currency"].dropna()) - {"USD"})
            if bad:
                raise ContractMasterError(
                    f"contract specs contain non-USD currencies {bad}. Notional would be "
                    f"produced in mixed units under a USD label. Add an FX layer, or pass "
                    f"require_usd=False if you know the caller handles it.")
        by_symbol = {r["Symbol"]: r for _, r in raw.iterrows()}

        # Price availability from the manifest rather than by opening 94 parquet files.
        tiers: dict[str, set[str]] = {}
        for name in load_manifest().get("prices", {}):
            sym, _, adj = str(name).rpartition("_")
            if sym:
                tiers.setdefault(sym, set()).add(adj)

        symbols = list(all_symbols())
        specs: dict[str, ContractSpec] = {}
        for sym in symbols:
            row = by_symbol.get(sym.internal)
            if row is None or not sym.cftc_code:
                continue
            # Primary code first, then predecessors. A code appearing under two symbols
            # would be a registry fault rather than something to resolve by ordering, so
            # it raises instead of letting first-or-last-wins decide silently.
            entries = [(sym.cftc_code, 1.0, False)]
            entries += [(hc, scale, True) for hc, scale in hist_code_scales(sym.hist_codes)]
            for code, scale, historical in entries:
                if code in specs and specs[code].symbol != sym.internal:
                    raise ContractMasterError(
                        f"market code {code!r} maps to both {specs[code].symbol!r} and "
                        f"{sym.internal!r}. A code identifies one instrument at a time; "
                        f"fix the registry rather than picking a winner here.")
                specs[code] = ContractSpec(
                    symbol=sym.internal, market_code=code,
                    is_historical_code=historical, contract_scale=float(scale),
                    point_value=float(row["Point Value"]),
                    tick_size=float(row["Tick Size"]),
                    tick_value=float(row["Tick Value"]),
                    currency=str(row["Currency"]),
                    margin=float(row["Margin"]),
                    exchange=str(row["Exchange"]), group=str(row["Group"]),
                    name=str(row["Name"]), asset_class=str(sym.asset_class),
                    report_type=str(sym.report_type))
        return cls(specs, registry_symbols=symbols, price_tiers=tiers)

    # ── lookup ──────────────────────────────────────────────────────────────
    def spec(self, market_code: str) -> ContractSpec | None:
        return self._by_code.get(str(market_code))

    def __len__(self) -> int:
        return len(self._by_code)

    @property
    def market_codes(self) -> set[str]:
        return set(self._by_code)

    # ── coverage, as a first-class output ───────────────────────────────────
    def coverage(self) -> pd.DataFrame:
        """One row per registry symbol: what it has, and what it is missing.

        ``joinable`` means the three things layer 2 actually needs are all present: a
        contract spec (for the multiplier), an UNADJUSTED price series (for notional, since
        back-adjusted prices are not tradeable levels), and a BACK-ADJUSTED one.

        The back-adjusted requirement is right but not for the reason an earlier version of
        this docstring gave. It is NOT that back-adjusted returns are correct; they are not,
        and `riskunits` refuses them. It is that ``propadj``, the ratio-adjusted series
        volatility actually needs, is **derived on read by cotdata from unadj + backadj**
        (see `cotdata.prices._ratio_adjust`). Both stored tiers are therefore the
        precondition for the one derived tier, and a symbol missing either cannot produce a
        volatility at all. Same check, sounder reason.
        """
        rows = []
        for sym in self._symbols:
            tiers = self._price_tiers.get(sym.internal, set())
            has_spec = any(s.symbol == sym.internal for s in self._by_code.values())
            has_unadj, has_backadj = "unadj" in tiers, "backadj" in tiers
            missing = [n for n, ok in (("specs", has_spec), ("unadj_price", has_unadj),
                                       ("backadj_price", has_backadj)) if not ok]
            rows.append({
                "symbol": sym.internal, "cftc_code": sym.cftc_code,
                "asset_class": sym.asset_class, "report_type": sym.report_type,
                "n_market_codes": sum(1 for s in self._by_code.values()
                                      if s.symbol == sym.internal),
                "has_specs": has_spec, "has_unadj_price": has_unadj,
                "has_backadj_price": has_backadj,
                "joinable": not missing, "missing": ",".join(missing),
            })
        return pd.DataFrame(rows).sort_values(["joinable", "symbol"]).reset_index(drop=True)

    def coverage_summary(self) -> str:
        cov = self.coverage()
        lines = [f"contract master: {int(cov['joinable'].sum())} of {len(cov)} registry "
                 f"symbols joinable, over {len(self)} market codes "
                 f"({sum(1 for s in self._by_code.values() if s.is_historical_code)} "
                 f"historical)."]
        for _, r in cov[~cov["joinable"]].iterrows():
            lines.append(f"  {r['symbol']:<6} missing {r['missing']}")
        return "\n".join(lines)

    def unmatched(self, canonical: pd.DataFrame) -> pd.DataFrame:
        """Market codes present in the data with no spec, and how many rows each has.

        The number that stops a partial panel being reported as a whole one. Print it.
        """
        if canonical.empty or "market_code" not in canonical.columns:
            return pd.DataFrame(columns=["market_code", "market_name", "rows"])
        miss = canonical[~canonical["market_code"].isin(self.market_codes)]
        if miss.empty:
            return pd.DataFrame(columns=["market_code", "market_name", "rows"])
        name_col = "market_name" if "market_name" in miss.columns else None
        agg = {"rows": ("market_code", "size")}
        if name_col:
            agg["market_name"] = (name_col, "first")
        out = miss.groupby("market_code", sort=False).agg(**agg).reset_index()
        return out.sort_values("rows", ascending=False).reset_index(drop=True)

    # ── annotation ──────────────────────────────────────────────────────────
    def annotate(self, canonical: pd.DataFrame, *, apply_scale: bool = True,
                 drop_unmatched: bool = False) -> pd.DataFrame:
        """Attach spec columns to canonical COT rows.

        Nothing is dropped by default: unmatched market codes keep their rows with null
        spec columns, so a caller that forgets to check still sees them rather than
        receiving a quietly shortened panel. ``drop_unmatched=True`` is the explicit
        opt-in, and pairs with :meth:`unmatched` to say what went.

        ``apply_scale`` rewrites the contract-count columns to today's contract definition,
        and defaults to True so that forgetting it produces the correct answer. Only
        genuine counts are scaled: ratios are unitless and trader counts are people.
        """
        if canonical.empty:
            return canonical.assign(**{c: pd.Series(dtype="object") for c in SPEC_COLUMNS})
        if "market_code" not in canonical.columns:
            raise ContractMasterError("canonical frame has no 'market_code' column")

        out = canonical.copy()
        # A plain Series.map over a dict yields NaN (a float) for a miss, not None, so the
        # attribute lookup below has to test the type rather than test for None. Unmatched
        # codes are the normal case here, not the exception: most of what CFTC publishes is
        # outside the registry.
        specs = out["market_code"].map(self._by_code)
        for col, attr in (("symbol", "symbol"), ("point_value", "point_value"),
                          ("tick_size", "tick_size"), ("tick_value", "tick_value"),
                          ("currency", "currency"), ("margin", "margin"),
                          ("exchange", "exchange"), ("asset_class", "asset_class"),
                          ("contract_scale", "contract_scale"),
                          ("is_historical_code", "is_historical_code")):
            out[col] = specs.map(
                lambda s, a=attr: getattr(s, a) if isinstance(s, ContractSpec) else None)

        if apply_scale:
            scale = pd.to_numeric(out["contract_scale"], errors="coerce").fillna(1.0)
            for c in CONTRACT_COUNT_COLUMNS:
                if c in out.columns:
                    out[c] = pd.to_numeric(out[c], errors="coerce") * scale
            out["contract_scale_applied"] = True
        else:
            out["contract_scale_applied"] = False

        if drop_unmatched:
            out = out[out["symbol"].notna()].reset_index(drop=True)
        return out
