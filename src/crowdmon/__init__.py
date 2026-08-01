"""crowdmon: a crowding and forced-exit monitor.

**Damage = crowding x illiquidity x holder fragility.** Crowding is a property of the
position, illiquidity of the market, and fragility of the holder — and fragility is the term
that decides who actually gets hurt. Two holders can carry the same position in the same
market and behave completely differently under stress, because one of them has an exit
function written into its mandate and the other does not.

Futures first (`crowdmon.futures`), because COT resolves the four structural weaknesses of
the 13F approach: the short book is reported rather than invisible, the lag is three days
rather than forty-five, open interest is known exactly rather than estimated against an
estimated float, and trader counts and concentration ratios are published. The equity
monitor is the follow-on, and `crowdmon.core` is what the two share.

**It ships no strategy.** Every output is a statement about tail shape and forced-flow risk,
not about next week's return. Positioning extremes persist for quarters.

**Why this is its own package rather than code inside a data repo.** Everything from
normalisation onward is a JOINER: net contracts times a multiplier times a price, scaled by
a volatility. crucible-stack ADR-0007 split `cotdata` and `marketdata` precisely because
almost nothing joined the two domains, and a normalisation layer living in either one would
drag the other back across that seam. The only home that does not violate it is the
consumer, which is this.

**Standing caution, carried from the module spec §9.4.** The CTA replication model, when it
exists, estimates *other people's* positions. It is calibrated to reproduce CONSENSUS
positioning, so trading it directly means deliberately joining the crowded trade this system
exists to warn about. It must not become a signal by drift, and any directional strategy
derived from it needs separate out-of-sample validation through `crucible` and its own
document. That is why `tests/test_boundaries.py` refuses an import of `crucible` from this
package: a monitor that can render its own verdict has stopped being a monitor.
"""
__version__ = "0.1.0"
