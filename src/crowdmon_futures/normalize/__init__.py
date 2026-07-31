"""Layer 2, normalisation. Everything downstream consumes these units.

Built so far: the contract master. Notional and vol-scaled risk units are next, and the
one thing to get right on the first line is that they draw on DIFFERENT price series:
notional from ``unadj``, volatility from ``backadj``. See docs/design/README.md.
"""
from .contract_master import (
    CONTRACT_COUNT_COLUMNS,
    SPEC_COLUMNS,
    ContractMaster,
    ContractMasterError,
    ContractSpec,
)

__all__ = ["ContractMaster", "ContractSpec", "ContractMasterError", "SPEC_COLUMNS",
           "CONTRACT_COUNT_COLUMNS"]
