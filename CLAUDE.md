# CLAUDE.md — crowdmon

Guidance for Claude Code working in this repo. Workspace-wide rules are in
`../CLAUDE.md` and the governance they point at (`npf/AGENTS.md`, `crucible/AGENTS.md`);
this file covers what is specific to this package.

> **Renamed from `crowdmon-futures` on 2026-08-01**, directory, remote and package
> together. The old name survives only where it is historically correct: `cotdata`'s design
> docs describe "the crowdmon-futures step-1 build", which is what it was called at the
> time, and `crowdmon_futures_cot_module.md` is a real filename in that repo. Neither is a
> stale reference to fix.

## The thesis, in one sentence

**Damage = crowding x illiquidity x holder fragility** — crowding is a property of the
position, illiquidity of the market, and fragility of the holder, and fragility is the term
that decides who actually gets hurt.

Futures are zero-sum, so "everyone is long" is impossible and net imbalance alone says
almost nothing: every long is somebody's short. What differs between the two sides is who is
holding and whether their exit is discretionary. That is the whole reason this package
exists rather than another positioning index.

**It ships no strategy.** Every output is a statement about tail shape and forced-flow risk,
not about next week's return. Positioning extremes persist for quarters.

## Design docs, and which one wins

| Document | Where |
|---|---|
| [`crowdmon_plain_language_summary.md`](docs/design/crowdmon_plain_language_summary.md) — the argument in prose, **and the authoritative appendix** | here |
| [`crowdmon_futures_cot_module.md`](docs/design/crowdmon_futures_cot_module.md) — the primary spec, §13 build order | here |
| [`amendments-2026-08-01.md`](docs/design/amendments-2026-08-01.md) — A1-A22, **closed** | here |
| [`amendments-2026-08-02.md`](docs/design/amendments-2026-08-02.md) — B1-B37, commonality through the template follow-ups and §A.2's real worked example. **Closed** | here |
| [`amendments-2026-08-03.md`](docs/design/amendments-2026-08-03.md) — C1 onward, template classification stability, the `w_SD` sweep, the report-layer gate and the brief. **The open file** | here |
| `crowdmon_step2_normalisation.md` — layer 2, **accepted and shipped**. History, not instructions | `../cotdata/docs/design/` |
| `cot_vintage.md` — the vintage store this reads | `../cotdata/docs/design/` |

**The appendix of `crowdmon_plain_language_summary.md` (§A.1-A.11) is the authoritative
statement of every formula.** Where a handoff and the appendix disagree, the appendix wins.

**Keep it a clean statement of the concept.** It is what someone reads to understand what
this package is for, so measured corrections and wrong paths belong in the dated amendment
files, not inline. The appendix carries one pointer to them and nothing more. Anyone building
from a formula there should read the amendments alongside it, and several sections need that:
§A.6's regression is vacuous as literally written, and §A.9's preamble and formula disagree.

It is written in LaTeX, which renders on GitHub and not in every viewer. The source is plain
text either way, so read the file rather than a rendering if the math matters.

**Its worked example is executed, not just read** ([`tests/test_appendix.py`](tests/test_appendix.py)),
and **it is now a real market**: LIVE CATTLE, report week 2026-07-28, carried through §A.2,
§A.5, §A.7 and §A.9 (2026-08-02 §B37). That buys a second failure mode worth having, since
the figures can now drift because the store changed rather than only because the code did,
so [`tests/test_appendix_live.py`](tests/test_appendix_live.py) re-derives them from the real
store. The constructed cocoa table is retained beside it, labelled, with its position stated:
`Q_sell/Q_buy = 9.045` is **90.5% of a ceiling set by `core/config.py`**, not an empirical
extreme.

Places where the appendix was right about its example and wrong about real data, all now
corrected in place: spreading and "a single category dominating is typical" (2026-08-01 §A6,
measured at 29% of markets); the cocoa **shape** itself, a minority configuration
concentrated in metals and livestock rather than in the harvest markets the example was drawn
from, and which cocoa has not held since early 2026 (§B31, §B36); its complete absence from
financial futures, where the mirror image is 77% of open interest and 9.05x is arithmetically
unreachable (§B32); and the reading that the median market has no asymmetry, which is
direction cancelling rather than symmetry (§B34).

Precedence: **a measurement beats a doc, the appendix beats a handoff, and a handoff beats
your own judgement about what would be nicer.**

Both were copied in on 2026-08-01. **This repo's copies are canonical**, and cotdata's copy of
the module spec is a pointer here, so there is one of each and no "do not edit both" hazard
left. The plain-language summary never existed in cotdata at all; an earlier version of this
paragraph said it did.

> **The copy lost 104 lines and nobody noticed for a day.** The 2026-08-01 copy of
> `crowdmon_futures_cot_module.md` took a version predating the 2026-07-30 vintage
> amendments, so this repo's "canonical" copy carried **zero** of the four amendment blocks
> while cotdata's carried all four. The diff was strictly one-way: 104 lines only in cotdata,
> zero only here. Restored 2026-08-01, before cotdata's copy became a pointer, because a
> pointer to the inferior copy would have made the loss permanent and invisible.
>
> The lesson is procedural rather than about this file. **Duplicating a living document opens
> a silent-regression window that closes only when someone diffs the copies**, and the only
> reason anyone diffed these was an unrelated cleanup task. If a document must appear in two
> repos, one of them is a pointer from the first commit, not eventually.

## Doc lifecycle — four directories, four different rules

| Directory | Lifecycle |
|---|---|
| `docs/design/` | **living.** Amended as measurements land. Amendments are **one dated file per day** (`amendments-YYYY-MM-DD.md`), because a shared section counter collided three times in one afternoon across parallel sessions |
| `docs/handoffs/` | **append-only.** Dated work orders, status-tracked. Preserved verbatim; append an outcome, never edit the body |
| `docs/analysis/` | **point-in-time.** Computed against a named report week. **Never amended** — a later week gets a new file |
| `docs/adr/` | **immutable once accepted.** Superseded by a new ADR rather than edited |

The distinction that matters most is design versus analysis. A design doc that says
something the data disproved is a bug to fix; an analysis document that says something later
weeks disproved is a correct record of what was true then, and editing it to match the
present erases the evidence that anything changed.

**A handoff without a completion status will be re-executed by a future session.** Closing
one out is what stops the same analysis being run twice with different results.

## Working agreement

- **Measure, do not assume.** Probing the actual files has overturned a written assumption in
  nearly every session, and the dated amendment files are the record. **Deliberately not a
  count here**: a running total in a file nobody updates goes stale silently, which is the
  same failure the amendments themselves keep catching. Two worth internalising: the Oct-Nov
  2025 shutdown left report dates completely intact (it broke release dates instead), and
  Managed Money dominates the Phi numerator in only 29% of markets rather than typically.
- **Specs are amendable.** If a measurement contradicts a doc, fix the doc in the same PR
  and say so. Where the doc lives in a sibling checkout, record it in
  `docs/design/amendments-*.md` rather than editing a shared working tree, and say that too.
- **Additive only.** `current/` output stays byte-identical.
- **Every quoted figure carries a reproducer.** `docs/analysis/reproduce.py` regenerates
  every number in the analysis documents; `tests/fixtures/build_fixtures.py` regenerates the
  committed test data.
- **Cite results by PATH plus REPRODUCER, never by a bare section ID.** `§B34` names neither
  a repo nor a file, so a session with no context cannot resolve it and cannot tell "does
  not exist" from "exists somewhere I did not look". Write both halves:

  ```
  docs/design/amendments-2026-08-02.md §B34
  docs/analysis/reproduce.py::template_direction_agnostic
  ```

  This is not a style preference. Three sessions in a row concluded `§B33-B36` did not exist
  because nothing in the citation said where to look; they were one `git show` away on an
  unpushed branch, and the second of those sessions re-derived the work and recorded a wrong
  definition of `A_agnostic` from the guess (`2026-08-03 §C4`). The bare form is not banned,
  because 368 of them already exist and rewriting prose is not the fix. Instead
  [`tests/test_references.py`](tests/test_references.py) resolves every one against the
  sections `docs/design/amendments-*.md` actually defines, so it **fails loudly** rather than
  silently. **A reference that cannot be located is marked, never deleted**: it goes in that
  file's `KNOWN_UNRESOLVED` with a reason and a place to look, and the entry itself fails
  once the gap closes. Deleting an unresolvable citation is what made the last one invisible.
- **Before concluding a thing does not exist, search all refs, not `main`.**
  `git log --all --oneline -- <path>`, and grep for the reproducer FUNCTION name rather than
  the section ID: the numbers are the asset and the prose is replaceable.
- **House style: worked numbers over abstract restatement, everywhere.** Carry the numbers
  through each formula in sequence, show the arithmetic rather than only its result, end in
  prose. A formula whose inputs are never printed is one nobody has ever checked.
  `futures.report.format_q_block` exists for exactly this.
- No em dashes in any output, chat or committed prose. The one exception is a handoff body,
  which is preserved as issued.
- Any response reporting results ends with a plain-language recap of the bottom line
  alongside the technical answer, not replacing it.

## The boundaries, and why they are not arbitrary

Enforced by [`tests/test_boundaries.py`](tests/test_boundaries.py), in both directions.

| May import | May not | Why not |
|---|---|---|
| `cotdata`, `marketdata` | `cotmetrics` | a peer consumer of the same store computing a different unitless index. Two disagreeing answers to one question |
| | `npf`, `livebook` | strategy and execution, the layers above |
| | `crucible`, `crucible_stack` | you are the intern, crucible is the judge. A monitor that can render a verdict on its own output has stopped being a monitor |

Neither producer may import this package either. That direction breaks nothing here, so it
would be found last, which is why it is checked from here.

Third-party imports are allowlisted too (`pandas`, `numpy`, `pyarrow` and the two siblings).
Reaching for anything else fails the boundary test on purpose: a new dependency belongs in
`pyproject.toml` as a deliberate choice, not discovered by an import that happened to work.

## Layout

```
src/crowdmon/
  core/                     asset-class agnostic — shared with the equity monitor (spec §12)
    aggregate.py            trailing z-scores and percentiles. No lookahead by construction
    config.py               fragility weights, kappa, tolerances. Configured, never fitted
    impact.py               A.5 square-root law + Amihud. Knows nothing about contracts
    report.py               markdown rendering. Knows nothing about categories
  futures/                  COT-specific. Knows about categories, market codes, open interest
    cot_adapter.py          the CotSource seam: refuses lookahead, filters on provenance
    io.py                   canonical panels + the OI identity as a reported rate
    contract_master.py      market code to multiplier, never an inner join
    notional.py             rung 3, contracts to USD. Refuses anything but unadj
    riskunits.py            rung 4, notional x sigma. Refuses anything but propadj
    flow.py                 A.3 flow decomposition
    fragility.py            A.2 Q_sell / Q_buy / Phi, and `shape_labels`: the six-outcome
                            (stable, fragile) classification, by explicit mask never
                            fall-through. Lives here because both reproducers had a copy
    breadth.py              §6.2 breadth-depth quadrant
    concentration.py        §6.2 CR4/CR8. Published, never null, needs nothing else
    impact.py               A.5 exit COST. Amihud needs the multiplier, see A20
    commonality.py          A.6 beta_bar and T_eff. NOT wired into the composite, see below
    weight_sensitivity.py   §6.3 / A.11. Phi has NO signal independent of the weights
    seasonal.py             §5.4. Measured at <=1.4% of variance; adjustment defaults OFF
    trigger.py              §9.3 / A.7. F*=F_{t-k}, from an OBSERVED pool not a fitted AUM
    extremity.py            §6.1 / A.4 vol-scaled positioning vs 3y of own history
    volume.py               A.5 denominator: whole-market ADV + stress V. Refuses anything
                            but "front", because `reconstructed` is not whole-market
    pressure.py             A.5 exit capacity. T = Q/(kappa V) is a real duration now
    composite.py            A.9 D = C x I x Phi. The whole system in one number, plus the
                            two per-row caveat carriers: `add_score_state` (why a null D is
                            null) and `add_unwind_state` (A17, and it says `indeterminate`)
    reflexivity.py          A.8 cascade. g is a STAIRCASE, and up/down never merge
    macro_pca.py            §7 cross-market. PC1 is the SUBJECT, and differs by report type
    clustering.py           §369 correlation clusters, not sector labels. Finds the yen carry
    alignment.py            §368 positioning against blended 20/60/250d TSMOM. Cannot reach 1
    roll.py                 roll-window volume, NOT §379: all three of its parts are blocked
    coverage.py             which markets can be scored at all, and at which rung they die
    continuity.py           a market code is not an instrument. Migrations, keyed on the code
    stratum.py              outright / certificate / differential, so C8's band rule is a
                            value a consumer reads. Classifies, never gates
    report.py               the COT-specific half of the report layer. Knows categories
    brief.py                one market-week, assembled. Computes NOTHING, and NAMES the
                            reading instructions it cannot carry rather than omitting them
```

`riskunits.py` sits **here beside `notional.py`, not in `core/`**: it needs `propadj` where
notional needs `unadj`, and that asymmetry is a fact about futures continuous-contract
construction rather than a general one.

**The rule for `core/`: only what is genuinely asset-class agnostic.** When in doubt it goes
in `futures/` and can be promoted later, which is cheap; demoting something after the equity
monitor has grown a dependency on it is not.

`core/aggregate.py` arrived with extremity: it is the first thing in `core/` to earn its
place rather than be assumed into it, and it is genuinely agnostic (it knows nothing about
markets or categories).

`core/impact.py` arrived once `futures/volume.py` supplied a whole-market volume. It holds
the two formulas and nothing else: `I = Y.sigma.sqrt(Q/V)` and Amihud are true of any market
with a price, a volatility and a volume. The unit conversions that need a CONTRACT stay in
`futures/impact.py`, and one of them is load-bearing (see A20: Amihud without the multiplier
is a different ranking, not a rescaled one).

`core/store.py` is still **absent rather than stubbed**. Nothing needs it yet, an empty module
invites being imported, and it wants history the vintage store does not have.

One knowing exception to the agnostic rule: the fragility weights in `core/config.py` are
keyed by Disaggregated and TFF category names. The handoff places them there, and the
*shape* is what the equity monitor will need too, with 13F holder types. If that lands, this
file grows a second table or the weights split per asset class.

## Things that will bite you

- **Two stores, different shapes.** The vintage store holds 346 markets but only from
  2025-01-07; the current-state parquets hold 27 markets back to 2006. Breadth and depth are
  in different places. `futures.from_vintage` and `futures.from_current_store` are separately
  named for this reason — do not add a flag that hides which one you got.
- **Nothing is point-in-time before 2026-07-31.** Vintages accumulate forward only, so any
  earlier week is a current value with revisions applied. Fine for descriptive work and for
  flow decomposition (a first difference on revised values is the *better* input). Not fine
  for evaluating a rule, which must go through `VintageCotSource.load` and filter on
  `pit_complete`.
- **`open_interest` is the market total repeated on every category row.** Summing it across
  categories multiplies it by five and silently divides every ratio in the system.
- **`Q_sell` and `Q_buy` must never be added.** Forced longs sell and forced shorts buy;
  their sum describes an event that cannot happen. `q_gross` exists and is named so it
  cannot be mistaken for a flow.
- **Phi uses gross over `2·OI`, never nets over OI.** Nets sum to zero across categories and
  cannot form a share. The wrong form is unbounded; the bound is asserted on every
  computation precisely to stop a regression to it.
- **Trader counts are suppressed routinely**, not exceptionally — 44% of Managed Money long
  counts in the latest week, and non-reportables have none by definition. Null is a real
  state. Never impute one: it feeds straight into the average position per trader.
- **Editable installs mean the installed package is the working tree.** A `git checkout` in
  `../cotdata` changes this package's behaviour with no change here, and other sessions share
  those checkouts.

## Layer 2 trap, now coded and guarded

The two factors of `net_notional × σ` come from **three different price series**, and each
module refuses the others. All three refusals are measured, not asserted, and each is a
`raise` rather than a warning because each error is invisible to the check a reasonable
person would actually run.

| Module | Wants | Refuses, and why it slips past a spot check |
|---|---|---|
| `notional` | `unadj` | `backadj` notional is wrong by +294% (gold 2002), +257% (crude 2004), and **exactly 0% today**, growing monotonically backwards |
| `riskunits` | `propadj` | `backadj` percent vol is 201x too high for ZS, 182x for ZN, and **0.47x for gold**, which never goes negative and passes every implausibility screen |
| `riskunits` | `propadj` | `unadj` full-sample vol looks fine (GC 1.01x) while a 63-day window spanning a roll is up to 9.84x off; crude's worst roll day is a fabricated 130.7% move |

`test_notional_live.py` and `test_riskunits_live.py` pin every one of those numbers against
the real store, and `docs/analysis/reproduce.py` prints them. If cotdata's adjustment logic
changes, they fail and the docstrings get corrected rather than quietly becoming folklore.

**An earlier version of this file said volatility wanted `backadj`. That was wrong.**
Additive back-adjustment preserves absolute price CHANGES, not percentage returns. Module
spec §5.1 had it right ("ratio-adjusted (not difference-adjusted) so returns are correct").
See `docs/design/amendments-2026-08-01.md` A8.

**`crowdmon_step2_normalisation.md` in `../cotdata` carried the same error**, naming `backadj`
for volatility in four places and calling it "the one real trap". Corrected on cotdata `main`
in `ff2b755`, which also fixed the cause: its availability table listed `unadj` and `backadj`
and omitted `propadj` entirely, so anyone reasoning from it was choosing between two options
when there were three. That is why the table above lists that document as history rather than
instructions. **This table is authoritative on the three series; that one is not.**

A negative price is **not** by itself a sign of the wrong series, in any of the three
adjustments. WTI settled at -37.63 on 2020-04-20; `unadj` records it faithfully and `propadj`
carries it through at -24.11, because ratio adjustment scales by a positive factor and so
preserves the underlying sign. Only the **rate** distinguishes an event from an artifact:
across all 47 symbols `propadj` has exactly one non-positive close (0.009% of crude) against
`backadj`'s 52.3% for soybeans. Nothing clips or rejects a negative price, `riskunits` masks
only the returns touching one, and anything downstream assuming `sign(notional) ==
sign(position)` is wrong on real data. See amendment A9: this assumption has now been made
and corrected three times in this codebase's short history.

## Commands

```bash
uv venv --python 3.11 && uv pip install -e ".[dev]" -e ../cotdata -e ../marketdata
```

Tests run fully offline against committed fixtures, but `cotdata` guards on the store env
var at import, so it must be set even when unused:

```bash
COTDATA_STORE=/tmp/crowdmon_test .venv/bin/python -m pytest tests/ -q -rs
```

```bash
.venv/bin/python -m ruff check src tests bin
```

**That fixture run skips 75 assertions, and they are the valuable ones.** Every
`tests/*_live.py` needs the real store, so CI has never executed the layer-2 trap-table
figures, the appendix's live-cattle arithmetic (`test_appendix_live.py`, `2026-08-02 §B37`),
the volume and trigger measurements, or
`2026-08-03 §C1-C8` (`test_supplemental_live.py`, the most exposed of the set: three of its
assertions read `cot_supplemental`, a domain one release old). From the
**main checkout**, against `~/code/cotdata_store`, the same suite is **590 passed / 5
skipped** rather than **515 / 80**.

**These four numbers are measured, so re-measure them rather than adjusting them by hand.**
Any PR that adds or removes a `tests/*_live.py` assertion moves all four, and two PRs in
flight at once each move them from a base that does not include the other. Whichever merges
second re-runs both commands and updates this paragraph, `bin/check_skips.py`'s header and
`bin/live-tests.sh`'s. This note exists because that has already happened once.

> **All four were stale by exactly +2 when `2026-08-03 §C11-C14` measured them** (they read
> 535 / 468 / 533 / 466 against a measured 537 / 470 / 535 / 468), so a PR had already moved
> them without updating this paragraph, which is the thing the paragraph above asks for. The
> figures here now include that drift plus the two fixture tests §C11 adds. A **fixture**
> test moves all four as surely as a live one does, and the paragraph above named only
> `tests/*_live.py`; it is the total that is quoted, so any added test counts.

> **From a worktree those two figures are 588 / 7 and 513 / 82**, because `test_boundaries`
> resolves `../cotdata` and `../marketdata` relative to the test file and finds neither,
> so the two producer-direction checks skip. Quote the main-checkout numbers: a worktree
> reports two fewer passes and has one real seam unguarded. This note exists because an
> earlier version of this paragraph quoted the worktree pair without saying so, which is
> hazard 5 of the editable-install list arriving as a documentation bug rather than a test
> failure.

The data cannot be committed to close the gap: `manifests/prices.json` records
`"source": "norgate"` for both the bars and `contract_specs`, Norgate is a commercial
subscription and this repo is public, and the vintage store accumulates forward only from
2026-07-31 so no download reconstructs it. The split is therefore permanent:

```bash
bin/live-tests.sh          # the 75, against the real store. Scheduled 09:15 daily
```

`--profile live` is the load-bearing part. A run whose store is missing or unsynced would
otherwise skip its way to a green exit having verified nothing, so a data-absent skip is a
failure there. CI runs the same checker under `--profile ci`, which allows those skips but
fails on a **new** reason, which is how a pin silently stops running. Both live in
[`bin/check_skips.py`](bin/check_skips.py); the schedule is
`bin/com.mspinola.crowdmon-live-tests.plist.example`.

Regenerate the analysis figures (needs the real store):

```bash
COTDATA_STORE=$HOME/code/cotdata_store .venv/bin/python docs/analysis/reproduce.py
```
