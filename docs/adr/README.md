# Architecture decision records

Empty so far. Nothing in this package has needed one yet: the decisions that shaped it were
taken elsewhere and are recorded elsewhere, and duplicating them here would create a second
copy to drift.

| Decision | Recorded in |
|---|---|
| `cotdata` is COT-only; bars live in `marketdata` | [crucible-stack ADR-0007](https://github.com/mspinola/crucible-stack/blob/main/docs/adr/ADR-0007-cotdata-is-cot-only-bars-live-in-marketdata.md) |
| Vintage provenance stays inside the cotdata boundary | crucible-stack ADR-0008 |
| Why crowdmon is a separate package at all | [../../README.md](../../README.md), enforced by `tests/test_boundaries.py` |
| The `core` / `futures` split | [2026-08-01 handoff §1](../handoffs/2026-08-01-flow-decomposition.md), from module spec §12 |

## When to write one here

When a choice is **structural, contested, and expensive to reverse** — and is this package's
to make. Some that are visible on the horizon:

- whether the CTA replication model lives here at all, given the §9.4 standing caution that
  it must not become a trading signal by drift
- which market universe the cross-market engine means, now that the Disaggregated report has
  measured at 76% ICE Energy Division and Nodal power and gas basis rather than the classic
  outrights the spec discusses throughout
- whether flow decomposition belongs here or in `cotdata`, which currently has its own
  implementation of the same spec section

Format: `ADR-NNNN-kebab-title.md`, with context, decision, consequences, and a status of
`proposed` / `accepted` / `superseded by ADR-NNNN`. **Accepted ADRs are not edited.** A
decision that changed is a new ADR that supersedes the old one, because the reason the old
one was taken is usually the most useful thing in the file.
