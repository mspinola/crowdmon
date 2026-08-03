# Handoff: contract specs for ICE Europe WTI and the Henry Hub complex

**Status:** open, blocked on the Norgate producer (Windows box). Nothing to do in `crowdmon`
**Date:** 2026-08-03
**Target:** whoever runs the Norgate producer, plus a follow-up `crowdmon` session
**Depends on:** PR #46 (the inventory that identified these five)
**Evidence:** [`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C14, §C15
**Reproducer:** [`../analysis/reproduce.py`](../analysis/reproduce.py)`::variant_codes_are_not_duplicates`

---

## 0. What is being asked for, and what is NOT

Add five CFTC market codes to crowdmon's covered universe, taking it from 45 markets to 50.
They are the head of the §C14 backlog by open interest.

**This handoff writes no code and changes no coverage.** Every one of the three artifacts
required per symbol comes from the Norgate producer, which runs on the Windows box only. It
is filed here so the producer run is mechanical and checkable rather than exploratory, and so
the next `crowdmon` session finds a claim rather than starting the analysis over.

**Do not add the registry entries ahead of the producer run.** §C15 records the reason with a
worked example: `MME` and `MFS` are registry symbols with `norgate: null`, and they report
`missing: specs,unadj_price,backadj_price` and are invisible to coverage. Five more inert
rows would look like progress and change nothing.

## 1. The five codes

| CFTC code | market name | mean OI | proposed symbol |
|---|---|---|---|
| `067411` | CRUDE OIL, LIGHT SWEET-WTI, ICE Futures Europe | 798,670 | `CLI` |
| `023A55` | HENRY HUB LAST DAY FIN, NYMEX | 420,336 | `HHL` |
| `03565B` | HENRY HUB, NYMEX | 362,655 | `HH` |
| `023A56` | HENRY HUB PENULTIMATE FIN, NYMEX | 253,028 | `HHPF` |
| `03565C` | HENRY HUB PENULTIMATE NAT GAS, NYMEX | 153,896 | `HHP` |

Symbols are **proposals, not decisions.** They must not collide with the 49 existing registry
symbols, and `HH` in particular is short enough to be worth a second look. The registry is
`cotdata/src/cotdata/registry.yaml`, grouped by asset class; these belong under `Energies`
beside `CL`, `RB`, `HO`, `NG`.

## 2. Why these five, and the objection that was raised and withdrawn

They look like variants of two already-covered flagships (`067651` NYMEX WTI as `CL`,
`023651` NAT GAS NYME as `NG`), and §C14 had advised settling micro gold before the large
backlog items precisely because a variant code duplicates a covered market.

**That objection was raised against this request and does not survive measurement.** Over the
82 vintage weeks, Managed Money net positioning correlates **negatively** with the flagship in
all five cases and week-to-week flow is near zero:

| code | `r(OI)` | `r(MM net)` | `r(ΔMM)` |
|---|---|---|---|
| `067411` | 0.771 | **-0.224** | -0.054 |
| `023A55` | -0.097 | **-0.643** | -0.164 |
| `023A56` | -0.146 | -0.413 | -0.063 |
| `03565B` | 0.179 | **-0.621** | -0.116 |
| `03565C` | -0.424 | -0.128 | -0.234 |

Open interest tracks, which is what makes them look like duplicates; positioning does not, and
positioning is the series crowding is a property of. Detail and the general lesson in §C15.

## 3. What the producer must write, per symbol

All three, or the symbol stays invisible. `coverage()` reports `joinable` only when all are
present, and each has a distinct consumer:

| artifact | needed by | note |
|---|---|---|
| `contract_specs` row | `ContractMaster` | point value, tick size, tick value, currency, margin, exchange, group. Written by the producer's `--metadata` flag |
| `unadj` price series | `notional.py` (rung 3) | refuses anything else. Back-adjusted notional is wrong by +294% on gold in 2002 and **exactly 0% today** |
| `backadj` price series | `riskunits.py` (rung 4), indirectly | `propadj` is **derived on read from the unadj/backadj pair** (`cotdata.prices._ratio_adjust`), so both stored tiers are the precondition for the one derived tier |

**Currency must be USD or `ContractMaster.load()` raises.** All 47 current specs are USD,
which is what removes an FX layer from rung 3. ICE Europe WTI is USD-denominated, so this
should hold, but it is asserted rather than assumed and a non-USD row fails loudly rather than
producing a USD-labelled number that is not USD.

## 4. The step that has to happen first

**Confirm Norgate carries each of the five.** This is not known from the Linux side and is the
one genuine unknown in this handoff. The financially-settled Henry Hub look-alikes
(`023A55`, `023A56`, `03565C`) are the doubtful ones: Norgate's futures universe is built
around liquid outrights, and a cash-settled look-alike may simply be absent.

If Norgate does not carry a given contract, **do not substitute a proxy.** `MME`/`MFS` are
priced off ETF proxies via yahoo, which is defensible for an index and is not for these: the
whole point of a financially-settled look-alike is that it differs from the benchmark it
settles against, so pricing it off the benchmark would erase the thing being measured. Report
it as vendor-absent and it stays in the backlog.

## 5. Verification, after the producer run

From a `crowdmon` checkout against the real store:

```
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python -c "
from crowdmon.futures import ContractMaster
cov = ContractMaster.load().coverage()
print(cov[~cov['joinable']][['symbol','cftc_code','missing']].to_string(index=False))
print('joinable:', int(cov['joinable'].sum()), 'of', len(cov))
"
```

Expected before: `joinable: 47 of 49`, with `MFS` and `MME` unjoinable.
Expected after all five land: `joinable: 52 of 54`, same two unjoinable.

Then re-run the inventory and confirm the covered count moves 45 -> 50:

```
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce.py
```

## 6. What the follow-up `crowdmon` session owns

Only once the artifacts exist:

- Re-run `contract_spec_inventory` and **write a new dated file** in `docs/analysis/`. The
  existing `2026-07-28-contract-spec-inventory.md` is point-in-time and must not be amended.
- Update the covered-universe count in `CLAUDE.md` and `docs/handoffs/README.md`, both of
  which now say 45.
- Re-measure the four suite figures rather than adjusting them by hand. They were found stale
  by +2 in PR #46 and adding live assertions for new markets will move them again.
- Check `continuity.py`: `03565B` and `023651` are both Henry Hub natural gas on NYMEX under
  different codes, and whether they are one instrument or two is a question that module exists
  to answer. §C15 says their holder bases differ, which is evidence for two, not proof.

## 7. What this does NOT unblock

The other two standing energy blocks are untouched. Price limits still have no table anywhere
in the workspace, so §8's `V = 0` treatment for a limit day remains unimplementable, and
§379's OI migration is still blocked because the price frame's `Open Interest` is whole-market
(`2026-08-02 §B19`). Adding these five improves breadth and neither of those.

Nor does it change the §10 validation verdict. That closed `uninformative` on spent episodes,
and new markets supply no new clean episodes for weeks that have already happened.
