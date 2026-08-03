# Handoff: contract specs for the §C14 backlog

**Status:** open, blocked on the Norgate producer (Windows box). Nothing to do in `crowdmon`
**Date:** 2026-08-03
**Target:** whoever runs the Norgate producer, plus a follow-up `crowdmon` session
**Depends on:** PR #46 (the inventory that identified these codes)
**Evidence:** [`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C14-§C17
**Reproducer:** `../analysis/reproduce.py::variant_codes_are_not_duplicates`, `::ag_dairy_backlog_priority`

> **Two tranches. §1-§7 are the five energy codes and were written first; [§8](#8-second-tranche-appended-2026-08-03-the-ag-and-dairy-backlog)
> is the ag and dairy tranche, appended later.** The title of this file said "ICE Europe WTI
> and the Henry Hub complex" while §1-§7 were the whole of it; it is broadened here because a
> single producer run covers both and the operator should not have to find two documents.
> **§8.3 corrects a statistic §2 leads with**, so read it before quoting §2's table.

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

---

# §8. Second tranche, appended 2026-08-03: the ag and dairy backlog

**Appended after the body above was written, not an edit to it.** §1-§7 concern the five
energy codes. This section adds the ag and dairy tranche, so a single producer run covers
both. Its evidence is
[`../design/amendments-2026-08-03.md`](../design/amendments-2026-08-03.md) §C16 and §C17;
reproducer `../analysis/reproduce.py::ag_dairy_backlog_priority`.

## 8.1 The answer is mostly "do not"

Asked to prioritise the ten ag and dairy codes in the §C14 backlog, the measured answer is
that **six should not be specced at all** and one more is marginal. Ranking by open interest,
which is how §C14 printed the backlog, gets the order close to backwards.

| priority | code | market | why |
|---|---|---|---|
| **1** | `039601` | ROUGH RICE | **the only clear yes.** MM share 0.433, 3.2x the covered median and the highest of the ten; flow independent of corn (0.047, inside the noise band); all 82 weeks |
| 2 | `001626` | WHEAT-HRSpring | MM share 0.278, but flow 0.338 against wheat-SRW is above the noise band. Worth it only if a third wheat class is wanted for its own sake |
| 3 | `135731` | CANOLA | largest of the ten at 271,205 OI and the **most duplicative on flow** (0.584 against soybean oil). Size and value point opposite ways |
| 4 | `063642` | CHEESE | only dairy code with real Managed Money (0.076), and 0.520 correlated with Class III milk, which is priced off cheese |
| - | `037021` `050642` `052642` `052644` | palm oil, butter, NFDM, Class IV milk | **do not spec.** MM share 0.012 to 0.048, an order of magnitude under the covered median, 106 to 1,147 contracts absolute. Hedger markets with no levered holder to force out |
| - | `052645` `005603` | dry whey, mini soybeans | **do not spec.** 14 and 13 weeks of 82. Mini soybeans also has a median Managed Money net of exactly zero |

**If only one thing is added from this tranche, add rough rice.** Norgate almost certainly
carries it (`ZR`, a standard CBOT contract), which makes it the cheapest item in the whole
backlog as well as the best justified.

## 8.2 Why the dairy block is a refusal rather than a deferral

Butter, non fat dry milk, Class IV milk and dry whey are not "small markets we will get to".
They are markets **this monitor has nothing to say about**. Damage is crowding x illiquidity x
holder fragility, and with Managed Money at 1.2% to 3.5% of open interest there is no fragile
holder for the fragility term to describe. Adding them would grow the covered count while
lowering the share of coverage the thesis applies to, which is exactly the failure §C13's gate
was built to catch, arriving from the inside instead of the outside.

This is worth stating because the natural next request is "then do the metals and the
remaining energy codes", and the same test should be run first. Cobalt, lithium hydroxide and
the two aluminium codes are all plausible members of the same category.

## 8.3 One methodological correction that changes §2 of this handoff

§2 above argues the energy five are not duplicates, and leads with Managed Money **level**
correlations. `§C16` measures that statistic and finds it spurious: positioning levels have
lag-1 autocorrelation of 0.956, and an **independent random walk** scanned against the covered
25 posts a maximum level correlation of **0.773 half the time**.

**§2's conclusion survives, on its second statistic.** The first-differenced correlations it
also reported (-0.054 to -0.234) sit inside a noise band of p90 = 0.229, so the energy five
really are flow-independent of `CL` and `NG`. But the bolded negative numbers in §2's table
are noise and should not be quoted. Any future variant test uses first differences.
