"""crowdmon-futures: a COT positioning and forced-flow monitor.

Measures crowding and forced-exit risk in futures markets. Consumes `cotdata` (CFTC
positioning) and `marketdata` (bars), and ships **no strategy**.

**Why this is its own package.** Everything from normalisation onward is a JOINER: net
contracts times a multiplier times a price, scaled by a volatility. crucible-stack
ADR-0007 split `cotdata` and `marketdata` precisely because almost nothing joined the two
domains, and a normalisation layer living in either one would drag the other back across
that seam. The only home that does not violate it is the consumer, which is this.

The build order and the design are in docs/design/. Layers 1 and 2 (this package's
ingestion and normalisation) are what everything else consumes, so nothing downstream is
trustworthy until they are right.

**Standing caution, carried from the module spec §9.4.** The CTA replication model, when
it exists, estimates *other people's* positions. It is calibrated to reproduce CONSENSUS
positioning, so trading it directly means deliberately joining the crowded trade this
system exists to warn about. It must not become a signal by drift, and any directional
strategy derived from it needs separate out-of-sample validation through `crucible` and
its own document. That is why `tests/test_boundaries.py` refuses an import of `crucible`
from this package: a monitor that can render its own verdict has stopped being a monitor.
"""
__version__ = "0.1.0"
