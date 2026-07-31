"""COT ingestion: the `CotSource` seam over cotdata's vintage store.

Module spec §4 envisaged an "adapter shim" normalising whatever `cotdata` emits into a
canonical schema. **That shim turned out to be thin**, because the vintage subsystem built
in cotdata adopted the canonical schema directly: natural key
`(report_date, market_code, report_type, combined, category)`, one row per category, with
`release_date` and `release_date_source` already resolved. So this module is not a schema
translator. What it actually owns is the three things the spec asked for and the store
cannot do on its own:

1. **Refusing lookahead.** Index on release date, never on report date (§5.3). Using the
   Tuesday as-of date embeds a three-day lookahead, and three days is precisely the window
   in which the largest moves happen, so it flatters every historical result in the wrong
   direction.
2. **Making provenance a filter rather than a footnote.** `release_date` carries a source
   in `published > observed > announced > scheduled > derived`, and `derived` is a GUESS
   that fails on exactly the weeks that matter: holiday shifts and publication backlogs.
   A release date without provenance is worse than none, so callers can exclude by source
   and every frame says which sources it contains.
3. **Validating on every load** (§4 adapter contract), because a category mapping that
   silently broke would be discovered as a strange result months later.

**The point-in-time asymmetry, stated up front.** Vintages accumulate forward only: CFTC
serves current state and there is no archive, so the vintage series begins at first
capture. For any week before that, the stored value is the CURRENT one with revisions
already applied. Both are returned, and `pit_complete` says which each row is. Anything
evaluating a rule must filter on it rather than assume.
"""
from __future__ import annotations

import datetime as dt
from typing import Protocol, runtime_checkable

import pandas as pd

# Ordered best to worst. `derived` is last because it is not a record of anything: it is
# "the Friday after the Tuesday", which is right in a normal week and wrong in every week
# anyone actually needs a release date for.
PROVENANCE_ORDER = ("published", "observed", "announced", "scheduled", "derived", "unknown")

#: Sources that record an actual publication rather than inferring one. The sensible
#: default floor for anything doing strict point-in-time evaluation.
RECORDED_SOURCES = ("published", "observed", "announced", "scheduled")


class CotAdapterError(RuntimeError):
    """The store cannot answer the question as asked."""


@runtime_checkable
class CotSource(Protocol):
    """Module spec §4. Two implementations were envisaged, `LocalCotData` wrapping the
    existing module and `CftcApiCotData` for backfill. Only the first exists, and the
    second has no reason to: cotdata already retains raw bytes for every capture."""

    def available_releases(self) -> list[dt.date]: ...

    def load(self, release_date) -> pd.DataFrame: ...


class VintageCotSource:
    """`CotSource` over `cotdata.vintage_ingest`.

    ``min_source`` drops rows whose release date is weaker-sourced than the given tier.
    It defaults to None (keep everything) so that a first look at the data is not silently
    filtered, but anything evaluating a rule should set ``min_source="scheduled"`` at
    least, which is the boundary between a recorded date and an inferred one.
    """

    def __init__(self, *, report_type: str = "disaggregated",
                 min_source: str | None = None, validate: bool = True):
        if min_source is not None and min_source not in PROVENANCE_ORDER:
            raise CotAdapterError(
                f"unknown release-date source {min_source!r}; expected one of "
                f"{PROVENANCE_ORDER}")
        self.report_type = report_type
        self.min_source = min_source
        self.validate = validate

    # ── loading ─────────────────────────────────────────────────────────────
    def _all(self) -> pd.DataFrame:
        from cotdata import vintage_ingest

        obs = vintage_ingest.read_observations()
        if obs.empty:
            return obs
        obs = obs[obs["report_type"] == self.report_type]
        if self.min_source is not None:
            keep = set(PROVENANCE_ORDER[:PROVENANCE_ORDER.index(self.min_source) + 1])
            obs = obs[obs["release_date_source"].isin(keep)]
        return obs

    def available_releases(self) -> list[dt.date]:
        """Every release date the store can answer for, ascending.

        Rows with no resolved release date are absent rather than defaulted. A row that
        cannot say when it became public cannot be placed in time, and inventing a date
        for it is the failure this class exists to prevent.
        """
        obs = self._all()
        if obs.empty:
            return []
        rel = pd.to_datetime(obs["release_date"], errors="coerce").dropna()
        return sorted({d.date() for d in rel})

    def load(self, release_date) -> pd.DataFrame:
        """The panel as it was knowable on ``release_date``.

        Two filters, and the difference between them is the whole point:

        - ``release_date <= t`` is what CFTC had PUBLISHED by then. It holds over all
          history and is the one that refuses lookahead.
        - ``observed_at <= t`` is what this store had CAPTURED by then. It is the stronger
          claim and the only one that is truly as-published, but it is empty before first
          capture.

        Applying only the second would silently return nothing for historical weeks;
        applying only the first would quietly hand back revised values as though they were
        the originals. So both are computed, the latest vintage knowable at ``t`` is
        preferred where one exists, and ``pit_complete`` marks each row as either a genuine
        as-published value or a later-captured stand-in.
        """
        from cotdata import vintage_ingest as vi

        t = pd.Timestamp(release_date)
        obs = self._all()
        if obs.empty:
            return obs
        published = obs[pd.to_datetime(obs["release_date"], errors="coerce") <= t]
        if published.empty:
            return published

        captured = published[published["observed_at"] <= t.normalize() + pd.Timedelta(days=1)]
        latest_captured = vi._latest_by_key(captured)
        known_keys = set(map(tuple, latest_captured[vi.NATURAL_KEY].to_numpy())) \
            if not latest_captured.empty else set()

        # For keys with no vintage captured by t, fall back to the EARLIEST vintage held,
        # not the latest. The earliest is the closest thing the store has to what was
        # originally published; the latest is the most revised, which is the value most
        # contaminated by hindsight.
        rest = published[~published.apply(
            lambda r: tuple(r[k] for k in vi.NATURAL_KEY) in known_keys, axis=1)] \
            if known_keys else published
        earliest = (rest.sort_values(["observed_at", "snapshot_id"], kind="mergesort")
                    .groupby(vi.NATURAL_KEY, dropna=False, sort=False).head(1)
                    if not rest.empty else rest)

        latest_captured = latest_captured.assign(pit_complete=True)
        earliest = earliest.assign(pit_complete=False)
        out = pd.concat([latest_captured, earliest], ignore_index=True)
        out = out.sort_values(vi.NATURAL_KEY, kind="mergesort").reset_index(drop=True)
        if self.validate:
            self._check(out)
        return out

    # ── validation (§4 adapter contract) ────────────────────────────────────
    @staticmethod
    def _check(frame: pd.DataFrame) -> None:
        """Schema conformance plus the zero-sum identity, on every load.

        The identity (long total == short total across categories, since every long is
        somebody's short) is the strongest check the schema admits and needs no external
        data. cotdata measured it at 149,412 of 149,412 weeks over 40 years, so a break
        here means the category mapping moved, not that the market did something unusual.
        """
        from cotdata import vintage_flow, vintage_ingest

        missing = [c for c in vintage_ingest.NATURAL_KEY if c not in frame.columns]
        if missing:
            raise CotAdapterError(f"canonical schema lost columns: {missing}")
        if frame.empty:
            return
        z = vintage_flow.zero_sum_check(frame)
        broken = z[~z["within_tolerance"]]
        if not broken.empty:
            worst = int(broken["imbalance"].abs().max())
            raise CotAdapterError(
                f"{len(broken)} market-week(s) break the zero-sum identity by up to "
                f"{worst} contracts, beyond CFTC's own rounding tolerance. Long and short "
                f"totals must match by construction, so this is a category-mapping fault "
                f"rather than a data anomaly. Worst: "
                f"{broken.iloc[0]['market_code']} {broken.iloc[0]['report_date']}.")


def provenance_summary(frame: pd.DataFrame) -> pd.Series:
    """How many rows came from each release-date source, worst-sourced last.

    Meant to be printed beside any result rather than checked once and forgotten. A panel
    that is 90% `derived` is not a point-in-time panel, however correct the code that
    produced it.
    """
    if frame.empty or "release_date_source" not in frame.columns:
        return pd.Series(dtype="int64")
    counts = frame["release_date_source"].value_counts()
    order = [s for s in PROVENANCE_ORDER if s in counts.index]
    return counts.reindex(order)
