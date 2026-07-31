# Design docs

New crowdmon design work is authored **here**, under this repo's `docs/`, from the first
keystroke (workspace governance: never drafted in an agent scratchpad).

Three documents predate this package and still live in `cotdata`, because they were written
while it did not exist. They are about crowdmon, not about cotdata, so they belong here and
should migrate. Not moved yet: they are linked from merged PRs and from
`cotdata/docs/design/cot_vintage.md`, and moving them now would rot those links for no
gain. Move them when something else brings that file back open.

| Document | Where | What |
|---|---|---|
| `crowdmon_futures_cot_module.md` | cotdata | full system description v0.1, and the §13 build order. The primary spec |
| `crowdmon_step2_normalisation.md` | cotdata | contract master and normalisation: **proposed and measured, not accepted**. Read before starting layer 2 |
| `cot_vintage.md` | cotdata | the vintage store this package reads. §9 records two adversarial reviews and one deliberately unmet acceptance criterion |

## What is settled, and what is not

**Settled.** This package is the right home for everything from normalisation onward,
because normalisation joins COT to prices and crucible-stack ADR-0007 exists to keep those
domains apart everywhere else. The boundary is enforced in `tests/test_boundaries.py`.

**Measured, and better than the proposal assumed.** All 42 `Role: deploy` markets in the
deployed `params.yaml` join cleanly to contract specs and unadjusted prices; the only two
failures are held-out markets Norgate does not cover. Coverage is not a constraint.

**The trap to avoid in layer 2.** Notional must be computed from **unadjusted** prices and
volatility from **back-adjusted** returns, so the two factors of `net_notional × σ` come
from different series. Computed off back-adjusted, notional is wrong by +294% for gold in
2002 and +257% for crude in 2004, and crude's back-adjusted series reaches -27.52, which is
not a price. The error is **exactly zero at the present date** and grows monotonically
backwards, so it passes every spot check anyone would run while corrupting the entire
history a backtest is evaluated over. Pin it with a test, not a comment.

**Not settled.** Roll calendar, first notice date and daily price limits are blocked on
data rather than code: there is no per-expiry price source in the stack and none is being
built. Anything needing a calendar spread is blocked on that, not on this package.
