# ADR-0001: crowdmon publishes a damage panel; consumers read it rather than importing crowdmon

**Status:** accepted, 2026-08-04
**Context:** [../../README.md](../../README.md) (why this is a separate package),
[../../tests/test_boundaries.py](../../tests/test_boundaries.py), crucible-stack ADR-0007
**Supersedes:** nothing

## Decision, in one line

`crowdmon` writes a versioned **damage panel** to `CROWDMON_STORE`, and a consumer that
wants `D` reads that file. Importing `crowdmon` is not the supported integration.

## Context

Every boundary this package has was written in the *downward* direction: what `crowdmon` may
import. `tests/test_boundaries.py` enforces it, and its upward check is scoped to the two
**producers**, `cotdata` and `marketdata`, on the argument that a producer which knows about
a consumer has stopped being one.

Nothing was ever decided about **consumers**. `cot_analyzer` appears in `FORBIDDEN_ROOTS`,
but that is the outbound direction: this package may not import the UI. The reverse, the UI
importing this package, is unenforced rather than permitted, and it became a live question
the moment there was something worth showing: `composite.damage_block` plus
`report.format_damage_block` and `report.format_offside` now deliver one self-describing
reading per market-week, and it had no reader.

`cot-analyzer` is the only UI in the workspace and the obvious consumer. It **cannot** import
this package, for four independent reasons, and the fourth is not negotiable:

1. It records in three places that it **computes no metrics of its own**
   (`cot-analyzer/README.md:9`, `:50`, `cot-analyzer/docs/ARCHITECTURE.md:45`). Calling
   `add_composite` in a Dash callback contradicts that directly.
2. This package refuses the same shape from its own side. `brief.py`: *"a derivation in the
   rendering is how the next engine gets built by accident."*
3. The ladder needs `unadj` **and** `propadj` prices plus a `contract_specs` table, all
   Norgate-sourced. `cot-analyzer/server-side/README.md` states that its Linux host *"cannot
   produce prices as configured, however it is provisioned"*, and crucible-stack ADR-0007
   records that every existing cot-analyzer price read is `backadj` only.
4. **That host runs Python 3.9.** `pyproject.toml` here declares `requires-python = ">=3.10"`.

Reasons 1 to 3 are arguments. Reason 4 is arithmetic.

## Decision

The seam is a file, and the direction of knowledge is unchanged: this package writes an
artifact and learns nothing about who reads it.

- `futures/publish.py` builds the panel and writes it. `bin/publish_damage.{py,sh}` drive it.
- The output root is **`CROWDMON_STORE`**, deliberately a different store from
  `COTDATA_STORE`, following npf's `CMRDATA_STORE`. A consumer's output does not belong
  inside the producer's data.
- The artifact carries a `schema_version`. A reader refuses a version it does not know.
- **The vocabularies and the prose travel as data**, generated from the live constants at
  publish time: `SCORE_STATES`, `UNWIND_STATES`, `FLOW_STATES`, `STRATA`, `FACTOR_QUESTIONS`,
  `DAMAGE_BANDS`, `QUADRANT`, `CLOSE_SIGMA`, `BAND_ADVICE`, and `brief.READING_INSTRUCTIONS`
  serialised whole.
- The latest week's `format_damage_block` output is **pre-rendered** into the artifact.

## Why this is an artifact and not `core/store.py`

`core/store.py` is deliberately absent and stays absent, and this does not quietly introduce
it. The distinction is direction: a **store** is state this package would read back and
therefore depend on; an **artifact** is a statement this package makes once a week and
forgets. `publish.py` has no reader. Nothing in `src/` opens `CROWDMON_STORE`, and the one
thing that looks like a read (`_refuse_a_short_panel` checking the previous manifest's market
count) is a safety interlock on the write, not an input to any computation.

## The two consequences that are load-bearing

**1. The prose must be generated, never hand-copied.** `brief.READING_INSTRUCTIONS` already
exists twice, in `README.md` as prose and in `brief.py` as a tuple, and
`tests/test_reading_instructions.py` exists solely because a caveat the README states and the
brief omits is omitted **silently** while the brief still reads complete (`2026-08-04 §C30`).
This package also lost 104 lines of a duplicated spec for a day and only found it by an
unrelated diff. A hand-written JSON block would be the copy nothing checks.
`tests/test_publish_live.py` therefore asserts **equality** with the live tuple, not
resemblance.

**2. The consumer must not hold this package's vocabulary.** A page that hard-codes
`"warmup"` or the four `QUADRANT` strings has made another copy, in the repo with the weakest
guards. The obligation this ADR places on a consumer is one grep test: no crowdmon string
literal in its source. That is what makes the artifact a contract rather than a convention.

## Consequences, ordinary

- The publisher is the **first writer in this package**, so `pyarrow` moves from a transitive
  read dependency to a declared write path. It was already in `ALLOWED_THIRD_PARTY`.
- `tests/test_boundaries.py` now walks `bin/` as well as `src/crowdmon`. A driver was
  previously free to import anything at all while every module it drove stayed clean, which
  is the same hole that file's own `_imports` docstring warns about, one directory up.
- Publication is scheduled beside `bin/live-tests.sh` at 09:15, chosen there to sit clear of
  observed store-write windows. That timing matters more for a publisher than for tests: a
  run that reads the store mid-write yields a **short panel**, which is a perfectly
  well-formed panel that nothing downstream would question. `publish._refuse_a_short_panel`
  is the interlock.
- The panel is ~4 MB for 49,377 market-weeks. It syncs to the production host as a fourth,
  **optional** payload of `cot-analyzer/scripts/push_data_cache_to_server.sh`; the three
  existing hard-required payloads keep their preflight unchanged.
- A schema change is a breaking change for a consumer that cannot import this package to
  find out. `SCHEMA_VERSION` and the reader's column assertion are the whole mitigation.

## What this does not decide

Whether any **aggregation** of `D` across markets is publishable. `composite.py` is explicit
that `D` is a percentile of its own history and that the raw product has no meaning across
markets, so an asset-class rollup is new surface with its own argument to make. It is filed
as a claim in [../handoffs/2026-08-04-damage-publication.md](../handoffs/2026-08-04-damage-publication.md)
with a pre-registered gate, deliberately not settled here.

One thing about that rollup **is** settled here, because it would otherwise be "fixed" in
both directions by successive sessions: a rollup does **not** add a sixth entry to README's
"Reading `D` on live output" and therefore not to `brief.READING_INSTRUCTIONS`. That tuple is
the denominator for the *brief's* pre-registered ship rule over a **market-week**. "A count
across markets is not a probability, and it inherits §B2" is a property of a class-week and
belongs in the rollup's own docstring. `tests/test_reading_instructions.py` and
`tests/test_references.py` would otherwise pull against each other whichever way it was done.
