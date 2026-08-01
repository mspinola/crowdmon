"""Asset-class agnostic core: configuration, rendering, and (later) aggregation and impact.

Module spec §12 records which components the futures monitor and the equity monitor share
unchanged — the store, rolling z-scoring, the report layer, and the square-root impact
core. This package is that decision made structural, not a guess about what might be reused.

**The rule for adding to it: only what is genuinely asset-class agnostic.** When in doubt it
belongs in `crowdmon.futures` and can be promoted later, which is a cheap move; demoting
something from `core` after the equity monitor has grown a dependency on it is not.

`aggregate.py` arrived with extremity (module spec §6.1): trailing-window z-scores and
percentiles, which know nothing about markets or categories and are the first thing here to
earn its place rather than be assumed into it.

Still deliberately absent rather than stubbed, because nothing needs them yet and an empty
module invites being imported: `store.py` (parquet io) and `impact.py` (square-root law,
Amihud). The first wants history the vintage store does not yet have and the second wants a
volume source that does not exist in this workspace at all.

One deliberate exception to the agnostic rule, in `config.py`: the COT fragility weights are
keyed by Disaggregated and TFF category names. The layer-3 handoff places them here, and the
*shape* (a holder-type to forced-exit-propensity map) is what the equity monitor will need
too, with 13F holder types instead. If that second map ever lands, this file either grows a
second table or the weights split out per asset class.
"""
from . import aggregate, config, report

__all__ = ["aggregate", "config", "report"]
