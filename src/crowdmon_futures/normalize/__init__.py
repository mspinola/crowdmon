"""Layer 2, normalisation. Everything downstream consumes these units.

Built so far: the contract master (market code to multiplier) and notional (contracts to
USD). Vol-scaled risk units are next.

The load-bearing fact across this layer is that the two factors of ``net_notional x sigma``
come from DIFFERENT price series, on purpose: notional from ``unadj``, because only that
carries tradeable price levels, and volatility from ``backadj``, because only that carries
correct returns. ``notional.add_notional`` refuses any other adjustment rather than
documenting the requirement, since the error it prevents is exactly zero on recent data.
"""
from .contract_master import (
    CONTRACT_COUNT_COLUMNS,
    SPEC_COLUMNS,
    ContractMaster,
    ContractMasterError,
    ContractSpec,
)
from .notional import (
    DEFAULT_MAX_STALENESS_DAYS,
    NOTIONAL_ADJUSTMENT,
    NOTIONAL_COLUMNS,
    NotionalError,
    add_notional,
    coverage_report,
)

__all__ = ["ContractMaster", "ContractSpec", "ContractMasterError", "SPEC_COLUMNS",
           "CONTRACT_COUNT_COLUMNS",
           "add_notional", "coverage_report", "NotionalError", "NOTIONAL_COLUMNS",
           "NOTIONAL_ADJUSTMENT", "DEFAULT_MAX_STALENESS_DAYS"]
