"""The COT-specific monitor: ingestion, normalisation, and the positioning engines.

Everything here knows about CFTC reporting categories, market codes and open interest, and
none of it would serve the equity monitor unchanged. That is the line between this package
and `crowdmon.core`.

`flow` and `fragility` need no prices, no contract master and no normalisation: every input
is a column the canonical schema already carries. That is deliberate and it is what makes
them the right first consumers of that schema — a failure in either one is a schema failure
and cannot be anything else. `pressure` is the exception and says so: its full form needs a
volume this workspace has no source for, so it returns the OI-denominated ranking now and
`None` where the real figure belongs.

Two data-loading modules rather than the one the handoff sketches, because they answer
different questions and only the first is about lookahead:

- `cot_adapter` — the `CotSource` seam. "What was knowable on date *t*", with release-date
  indexing and provenance filtering. Layer 1.
- `io` — the flat panels the engines consume, plus the open-interest identity as a reported
  rate. The handoff's §2.

**The load-bearing fact across the normalisation half** (`contract_master`, `notional`, and
`riskunits` when it lands) is that the two factors of `net_notional x sigma` come from
DIFFERENT price series, on purpose: notional from `unadj`, because only that carries
tradeable price levels, and volatility from `backadj`, because only that carries correct
returns (unadjusted returns carry a fake jump at every roll). `notional.add_notional`
refuses any other adjustment rather than documenting the requirement, because the error it
prevents is **exactly zero on recent data** and grows monotonically backwards. That is also
why `riskunits` belongs here beside `notional` rather than in `crowdmon.core`: the
asymmetry is a fact about futures continuous-contract construction, not a general one.
"""
from .breadth import decompose_breadth
from .contract_master import (
    CONTRACT_COUNT_COLUMNS,
    SPEC_COLUMNS,
    ContractMaster,
    ContractMasterError,
    ContractSpec,
)
from .cot_adapter import (
    PROVENANCE_ORDER,
    RECORDED_SOURCES,
    CotAdapterError,
    CotSource,
    VintageCotSource,
    provenance_summary,
)
from .flow import FLOW_STATES, decompose, state_distribution, tolerance_sensitivity
from .fragility import contributions, fragility_frame, market_fragility
from .io import (
    PanelError,
    from_current_store,
    from_vintage,
    latest,
    oi_identity,
    oi_identity_summary,
)
from .notional import (
    DEFAULT_MAX_STALENESS_DAYS,
    NOTIONAL_ADJUSTMENT,
    NOTIONAL_COLUMNS,
    NotionalError,
    add_notional,
    coverage_report,
)
from .pressure import exit_pressure, rank_markets, top_by

__all__ = [
    # ingestion
    "CotSource", "VintageCotSource", "CotAdapterError", "PROVENANCE_ORDER",
    "RECORDED_SOURCES", "provenance_summary",
    "PanelError", "from_vintage", "latest", "from_current_store",
    "oi_identity", "oi_identity_summary",
    # normalisation
    "ContractMaster", "ContractSpec", "ContractMasterError", "SPEC_COLUMNS",
    "CONTRACT_COUNT_COLUMNS",
    "add_notional", "coverage_report", "NotionalError", "NOTIONAL_COLUMNS",
    "NOTIONAL_ADJUSTMENT", "DEFAULT_MAX_STALENESS_DAYS",
    # engines
    "decompose", "state_distribution", "tolerance_sensitivity", "FLOW_STATES",
    "market_fragility", "fragility_frame", "contributions",
    "decompose_breadth",
    "exit_pressure", "rank_markets", "top_by",
]
