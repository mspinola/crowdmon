# Handoff: crowdmon workspace bootstrap + first real analysis

**Status:** complete. Landed 2026-08-01 as [`0917eb1`](https://github.com/mspinola/crowdmon/commit/0917eb1) **with no PR number**, directly on `main`: this work predates the repo's PR workflow, and PR #1 is the very next commit. Closed out 2026-08-02, see [§10](#10-close-out).
**Date:** 2026-08-01
**Lives at:** `docs/handoffs/2026-08-01-flow-decomposition.md` (this file bootstraps the repo it belongs in — commit it as part of the initial commit)
**Target:** Claude Code session
**Depends on:** `cotdata` vintage subsystem (PR #78, merged); Disaggregated COT history 2006→present already ingested
**Deliverable:** a working `crowdmon` package with flow decomposition and fragility-weighted exit pressure, plus a written walkthrough of one real market

> Update `Status:` to `complete (PR #NN)` when executed. A handoff without a completion status will be re-executed by a future session.

> **Executed 2026-08-01.** Outcome, and the four premises below that did not survive
> measurement, are in [§9](#9-outcome). Text above and below §8 is preserved verbatim as the
> work order that was issued, including its em dashes, which the workspace prose rule would
> otherwise forbid: amending a handoff after the fact would destroy the record of what was
> actually asked.

---

## 0. Context

`crowdmon` measures crowding and forced-exit risk in futures markets. The thesis: **damage = crowding × illiquidity × holder fragility**. Crowding is a property of the position, illiquidity of the market, fragility of the holder — and fragility is the term that decides who actually gets hurt.

Design docs (commit these into the workspace if not already there):

- `crowdmon_futures_cot_module.md` — full system specification
- `crowdmon_plain_language_summary.md` — the same argument in prose, with a mathematical appendix (§A.1–A.11). **The appendix is the authoritative statement of every formula below.** Where this handoff and the appendix disagree, the appendix wins.

This task implements the two pieces that need no prices, no contract master, and no normalisation: **flow decomposition** (appendix A.3) and **fragility-weighted exit size** (A.2). It is deliberately scoped small — it is also a smoke test of whether the canonical COT schema holds up under a real consumer before larger components depend on it.

**Vintage data is not required.** Flow decomposition is a first difference on current-state values; revised values are the better input, not the worse one. Vintage matters for as-of historical evaluation, which is a later concern.

---

## 1. Workspace setup

New repo `crowdmon`, consuming `cotdata` as a dependency. Do not add analytics to `cotdata` — ADR-0007 narrows it to CFTC positioning, and `crowdmon` is the consumer.

```
crowdmon/
  pyproject.toml
  CLAUDE.md
  docs/
    design/                        # living specs; amended as measurements land
      crowdmon_futures_cot_module.md
      crowdmon_plain_language_summary.md
    handoffs/                      # dated work orders; status-tracked
      2026-08-01-flow-decomposition.md
    analysis/                      # point-in-time outputs; never amended
    adr/
  src/crowdmon/
    core/                          # asset-class agnostic
      config.py                    # weights, kappa, tolerances
      store.py                     # parquet io
      aggregate.py                 # rolling z-scores, percentiles
      impact.py                    # square-root law, Amihud
      report.py                    # walkthrough rendering
    futures/                       # COT-specific
      io.py                        # cotdata adapter → canonical frame
      flow.py                      # A.3 — flow decomposition
      fragility.py                 # A.2 — weighted exit size, Phi
      pressure.py                  # A.5 — exit capacity (OI-proxy for now)
  tests/
  notebooks/                       # exploration only, nothing load-bearing
```

**On the `core` / `futures` split.** This is not speculative structure. §12 of the module spec identifies the components shared with the equity monitor — store, z-scoring, report layer, and the square-root impact core all serve both asset classes unchanged. `core/` reflects a decision already recorded rather than a hypothetical. Only put something in `core/` when it is genuinely asset-class agnostic; when in doubt it belongs in `futures/` and can be promoted later.

For this session most modules under `core/` will be thin or empty — `impact.py` and `aggregate.py` are not needed until volume and history land. Create only what §3–§6 require, and leave the rest absent rather than stubbed.

`CLAUDE.md` should carry: the thesis sentence, pointers to both design docs, the note that the appendix is authoritative for formulas, the doc-lifecycle convention above, and the working agreement — **measure, don't assume; if a measurement contradicts a doc, fix the doc in the same PR and say so.** Also record the house style: **worked numbers over abstract restatement, everywhere.**

---

## 2. Data loading (`futures/io.py`)

Load the Disaggregated report from `cotdata`. Required columns:

```
report_date, market_code, market_name, category,
long_contracts, short_contracts, spread_contracts, open_interest
```

Constraints:

- Futures-only and futures-and-options-combined are **different series**. Pick one (futures-only, matching what `cotdata` fetches) and keep the flag in the key. Never mix within a series.
- Normalise category labels to a controlled vocabulary and **fail loudly on an unknown label** — a silently dropped or unmapped category corrupts every downstream sum.
- Assert `sum(long) == sum(short) == open_interest` per market-week, within a small tolerance for the reporting quirks that exist. **Report the exception rate rather than suppressing it** — a rising rate means the parse is wrong.

---

## 3. Flow decomposition (`futures/flow.py`) — appendix A.3

Per `(market_code, category)`, ordered by `report_date`:

```
d_long  = Δ long_contracts
d_short = Δ short_contracts
d_net   = d_long − d_short
```

**Gap handling is mandatory.** Compute deltas only across consecutive report dates 7 days apart. Where the gap differs, emit `flow_state = "gap"` and null deltas. Without this, the Oct–Nov 2025 shutdown reads as one enormous week of flow, and the 2023 ION incident produces a smaller version of the same artifact.

Classification, with a configurable dominance tolerance (start at 0.25 of the larger absolute move):

| Condition | State | Meaning |
|---|---|---|
| `d_long ↑`, `d_short ≈ 0` | `new longs` | fresh conviction |
| `d_short ↓`, `d_long ≈ 0` | `short covering` | **finite fuel** — bounded by remaining `short_contracts` |
| `d_short ↑`, `d_long ≈ 0` | `new shorts` | fresh bearish conviction |
| `d_long ↓`, `d_short ≈ 0` | `long liquidation` | position exit, not fresh selling |
| both move materially | `mixed` | |

For `short covering`, also emit `fuel_remaining = short_contracts` — the hard upper bound on how much further that flow can run.

**Sensitivity check required:** report how the state distribution shifts across tolerance values (0.15 / 0.25 / 0.40). If classifications are highly unstable across that range, the tolerance is doing more work than the data and this must be reported rather than papered over.

---

## 4. Fragility (`futures/fragility.py`) — appendix A.2

Weights, in `core/config.py`, configured not fitted:

| Category | $w_c$ |
|---|---|
| Managed Money | 1.0 |
| Non-Reportable | 0.6 |
| Other Reportable | 0.5 |
| Swap Dealer | 0.4 |
| Producer / Merchant / Processor | 0.1 |

**Directional split — do not collapse into one figure.** Forced longs sell; forced shorts buy. Summing them describes no actual flow:

```
Q_sell = Σ  w_c · P_c        over categories with P_c > 0
Q_buy  = Σ  w_c · |P_c|      over categories with P_c < 0
Phi    = Σ  w_c · (L_c + S_c) / (2 · OI)
```

`Phi ∈ [0,1]` by construction — it uses **gross** positions over `2·OI`, because nets sum to zero and cannot form a share. **Assert this bound in a test.** An earlier draft of the spec used `Σ w_c |P_c| / OI`, which is unbounded and wrong; the assertion prevents a regression to it.

Also emit, per market: each category's contribution to the `Phi` numerator. If one category dominates (Managed Money typically will), the headline number is really about that category, and the walkthrough should say so rather than implying a broad-based reading.

---

## 5. Exit pressure (`futures/pressure.py`) — appendix A.5

Full form is `T = Q / (κ·V)` with `κ = 0.2`. Volume needs the contract master, which is a later build step, so:

- **Now:** rank on `Q_sell / OI` and `Q_buy / OI`. OI is a reasonable depth proxy and avoids blocking on the contract master.
- **Structure the code so `V` slots in later** without a rewrite — take volume as an optional argument, return `T` when it is present, `None` when it isn't. Do not fabricate a volume estimate.

Emit both directions separately. The asymmetry between `Q_sell` and `Q_buy` is often the most informative single number: it is what distinguishes a market where longs can be forced out from one where shorts can be squeezed.

---

## 6. The analysis (`docs/analysis/`)

**Do not hand-pick the market.** Rank all markets in the latest report by `Q_sell / OI`, then again by `Q_buy / OI`. Take the top of each ranking. The point of a real example is that it was not selected to fit an argument — say so explicitly in the writeup, and report the full top-10 tables so the selection is auditable.

For each of the two selected markets, write a walkthrough containing:

1. **Category table** — long, short, net, gross, `w_c`, per category, with OI
2. **`Q_sell`, `Q_buy`, `Phi`** — arithmetic shown, not just results
3. **Flow decomposition** — latest week's state per category, plus the trailing 12-week sequence of states for Managed Money. The sequence matters more than the single week: a persistent run of `new longs` with a falling trader count is the concentrating configuration.
4. **Breadth–depth** — `ΔP = N̄·Δq + q̄·ΔN + ΔN·Δq` using published trader counts. Which term dominates?
5. **Reading** — plain prose. What does this positioning imply about which direction is fragile, and what would have to happen for the fragile side to be forced out?
6. **What is missing** — no volume so no real DTL, no price so no trigger level, weights are judgement.

Follow the worked-example style in the plain-language summary's appendix: numbers carried through each formula in sequence, arithmetic visible, prose reading at the end. That format is the requested house style for this project — **prefer worked numbers over abstract restatement everywhere.**

**Compare against the cocoa template** in appendix A.2. That example was constructed to be structurally realistic, not drawn from real data. State plainly whether real markets show the same shape — heavily producer-hedged short side, fragile levered long side — or whether the structure differs. **If it differs, that is the finding**, and it should be reported prominently rather than smoothed over.

---

## 7. Tests

| Test | Assertion |
|---|---|
| Gap handling | A >7-day gap yields `flow_state = "gap"`, null deltas, no spurious flow |
| Shutdown window | Oct–Nov 2025 report dates produce no anomalous flow values |
| Phi bound | `0 ≤ Phi ≤ 1` across the entire history, every market, every week |
| Directional split | `Q_sell` and `Q_buy` never combine; each sums only its own sign |
| Key integrity | Deltas never computed across differing `market_code` or `combined` |
| Classification | Synthetic fixtures for each of the four pure states |
| Category vocabulary | Unknown label raises rather than silently dropping |
| OI identity | `sum(long) == sum(short) == OI` holds, with exception rate reported |

Fixtures committed so tests run offline.

---

## 8. Report back

- The two ranking tables and the two walkthroughs
- Tolerance sensitivity results from §3
- The OI-identity exception rate, and whether it is stable over history
- **Whether real markets match the cocoa template's shape** — and if not, how they differ
- Anything in the design docs the data contradicted, with the doc amended in the same PR

Do not proceed to the contract master (spec §13 step 2) in this session. This is a small, self-contained piece whose purpose is partly to validate the schema before more is built on top of it.

---

## 9. Outcome

Executed 2026-08-01. Everything under §2 to §7 is built and passing: 91 tests, offline against
committed fixtures, ruff clean. Deliverables:

| Asked for | Landed at |
|---|---|
| ranking tables, tolerance sensitivity, OI identity | [docs/analysis/2026-07-28-first-rankings.md](../analysis/2026-07-28-first-rankings.md) |
| walkthrough, sell-side pick | [docs/analysis/2026-07-28-0063CU-calif-low-carbon.md](../analysis/2026-07-28-0063CU-calif-low-carbon.md) |
| walkthrough, buy-side pick | [docs/analysis/2026-07-28-02339S-cig-rockies.md](../analysis/2026-07-28-02339S-cig-rockies.md) |
| what the data contradicted | [docs/design/amendments-2026-08-01.md](../design/amendments-2026-08-01.md) |
| reproducer for every quoted figure | [docs/analysis/reproduce.py](../analysis/reproduce.py) |

**Headline finding, against §6's cocoa question: the structure differs, in about half the
universe.** The two markets the ranking selected are structural opposites. `0063CU` matches
the template (Managed Money purely long, Producer/Merchant hedged short); `02339S` inverts
it (Producer/Merchant net long, Managed Money purely short). Across all 279 markets,
Producer/Merchant is net long in 141 (50.5%) and short in 138. Any rule assuming producers
are short and funds are long is a coin flip on this universe.

**Four premises in this handoff did not survive measurement.** Full detail in the amendments
document; in brief:

1. **§3's shutdown rationale is wrong.** Oct-Nov 2025 report dates run weekly and unbroken —
   CFTC published the backlog with the correct as-of Tuesdays. The gap rule is still needed,
   but for thin markets dropping below the reporting threshold (oats: a 294-day interval).
   Where the shutdown did land is the *release* date, which is `derived` for every week of
   the window.
2. **§4's "Managed Money typically will [dominate Phi]" is not the typical case.** It is the
   top contributor in 81 of 279 markets (29%).
3. **§7's strict 7-day gap rule discards real flow.** 2,850 of 2,965 gap-labelled rows on the
   liquid panel are 6-and-8-day holiday shifts. Implemented as specified and made a
   parameter, with the cost measured rather than hidden.
4. **§0 and §4 name `crowdmon_plain_language_summary.md` as authoritative for every formula,
   and it does not exist** in this repo or in `cotdata`. The handoff's own formulas were used;
   the Phi bound is asserted on every computation rather than trusted. If that document
   surfaces, the Phi definition and the cocoa comparison need re-checking against it.

**Two deviations from §1's layout, both deliberate:**

- `futures/cot_adapter.py` exists beside `futures/io.py`. It is the `CotSource` seam from the
  prior layer-1 PR and answers a different question (what was knowable on date *t*, with
  release-date indexing and provenance filtering) than the flat panel loader §2 specifies.
- `report.py` is split. `core/report.py` holds the asset-class-agnostic markdown rendering;
  `futures/report.py` holds the category tables and `Q`/`Phi` arithmetic, which know about
  reporting categories and could not serve the equity monitor unchanged. §1's own rule
  ("only put something in `core/` when it is genuinely asset-class agnostic") decided this.

`core/store.py`, `core/aggregate.py` and `core/impact.py` are **absent rather than stubbed**,
per §1.

**Absorbed from `main` during the restructure.** `main` moved to `297ebb6` (notional, spec
§5.2 rung 3) after this branch's merge-base, and the `crowdmon_futures` -> `crowdmon` rename
would have landed it badly: `normalize/notional.py` into a deleted directory, and 17 tests
importing a package that no longer exists. Carried across as part of the rename, since the
rename is what breaks them:

- `notional.py` -> `src/crowdmon/futures/notional.py`, **byte-identical** (it has no
  intra-package imports, only pandas and a lazy `cotdata`)
- its six public names exported from `futures/__init__.py`
- `tests/test_notional{,_live}.py` imports rewritten, nothing else touched
- `normalize/__init__.py` deleted; its export list relocated

The guard that must survive any future move: `add_notional` **raises** on any adjustment but
`unadj`, and its docstring carries the measured reason (+294% gold 2002, +257% crude 2004,
exactly 0.0% today, growing monotonically backwards). The zero is the whole point — every
spot check on recent data passes while the entire evaluation history is corrupted.

**The rename completed 2026-08-01**, directory, remote and package together. Contained:
no other repo's venv referenced this package, so only its own editable install, the git
worktree registration, the remote URL and the workspace `CLAUDE.md` sibling table needed
updating. The old name survives in `cotdata`'s design docs where it is historically correct
("the crowdmon-futures step-1 build") and in the real filename
`crowdmon_futures_cot_module.md`; neither is a stale reference.

**Still open, needing a decision rather than more work:**

- The design docs still live in `cotdata/docs/design/`, not here as §1's tree shows. That
  checkout is shared and clean on `main`, so the amendments were recorded here instead of
  edited into the originals.
- Flow decomposition now exists twice: `cotdata.vintage_flow.decompose` (parameter-free,
  dominant-leg, no `mixed` state) and `crowdmon.futures.flow` (tolerance-based, this build).
  Real duplication, worth resolving.

---

## 10. Close-out

Appended 2026-08-02. §0 to §8 remain the work order as issued; §9 remains the outcome as
written on the day. This section records only what has changed since, so a reader who starts
at the top is not left holding a stale open item.

### The status line was never resolvable as written

The header asked for `complete (PR #NN)`. **There is no NN.** `0917eb1` was committed
straight to `main`, and PR #1 (`de01b18`, risk units) is the next commit on the first-parent
chain, so this handoff executed in the window before the repo had a PR workflow at all. The
header now records the commit instead. A future session looking for a merged PR to read will
not find one, and that is a fact about the repo's history rather than a missing link.

### §9's four failed premises: three stand, one is now resolved

Premises 1 to 3 (the shutdown left report dates intact, Managed Money dominates Phi in 29%
of markets not typically, and the strict 7-day gap rule discards 2,850 holiday-shift weeks)
stand as written, and their detail is in
[`amendments-2026-08-01.md`](../design/amendments-2026-08-01.md).

**Premise 4 is closed.** §9 recorded that `crowdmon_plain_language_summary.md` did not exist
in this repo or in `cotdata`, that the handoff's own formulas were used instead, and that
"if that document surfaces, the Phi definition and the cocoa comparison need re-checking
against it". It surfaced the same day, in `85b3e86`. Both re-checks have now happened:

| what §9 asked for | outcome |
|---|---|
| re-check the **Phi definition** | The appendix agrees with the handoff. §A.2's arithmetic is no longer merely read but **executed**, in [`tests/test_appendix.py`](../../tests/test_appendix.py): `Q_sell`, `Q_buy`, Phi, the weights table, and the `gross == 2·OI` identity all reproduce exactly, so the implementation is pinned to the spec rather than believed to match it |
| re-check the **cocoa comparison** | Done twice. The same-day note appended to [`2026-07-28-first-rankings.md` §2](../analysis/2026-07-28-first-rankings.md) confirmed the one-line characterisation used in §9 was accurate (Producer/Merchant net short 110,000 against Managed Money net long 90,000) and that the comparison stood. **A second, harder re-check on 2026-08-02 did not stand**, see below |

### §6's cocoa question has a sharper answer than §9 gave

§9's headline was "the structure differs, in about half the universe", supported by
Producer/Merchant being net long in 141 of 279 markets (50.5%). That figure is correct and
reproduces exactly. **The reasoning from it was not.** The template is a joint claim about
two categories at once, and a marginal frequency cannot address it. Measured as the
conjunction it actually asserts:

- the template shape holds in **76 of 279 markets (27.2%)**, under a third rather than half
- a rule assuming producers short and funds long is wrong in **203 of 279 (72.8%)**
- **hedger and fund sit on the SAME side in 94 markets (33.7%)**, a case the template does
  not contemplate and the margins cannot show

Full detail, including the four defects a fresh-context review found in the first draft of
that correction, is [`amendments-2026-08-02.md` §B28](../design/amendments-2026-08-02.md).
Nothing in `src/` changed: `fragility` computes `Q_sell` and `Q_buy` by sign over every
category and never assumed the template shape.

### §9's two open decisions: one resolved, one still open

- **Design docs.** Resolved. Both specs are canonical in this repo's `docs/design/`, and
  `cotdata`'s copy of the module spec is now a 52-line pointer here, so the duplicate-living-
  document hazard §9 flagged is closed rather than merely tolerated.
- **Flow decomposition exists twice.** **Still open, unclaimed.**
  `cotdata/src/cotdata/vintage_flow.py:69` `decompose` (parameter-free, dominant-leg, no
  `mixed` state) and `crowdmon.futures.flow.decompose` (tolerance-based) both exist today.
  They answer slightly different questions and the difference is that this one can decline to
  name a direction, so neither is wrong; the duplication is a maintenance liability rather
  than a correctness bug. **It needs a decision, not more measurement**, and it is the only
  thing this handoff leaves behind.
