"""Layer 1, ingestion. Everything downstream depends only on the canonical schema."""
from .cot_adapter import (
    PROVENANCE_ORDER,
    RECORDED_SOURCES,
    CotAdapterError,
    CotSource,
    VintageCotSource,
    provenance_summary,
)

__all__ = ["CotSource", "VintageCotSource", "CotAdapterError", "PROVENANCE_ORDER",
           "RECORDED_SOURCES", "provenance_summary"]
