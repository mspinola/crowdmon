# Handoff: a contradicted trigger row is described as an absence, and it is not one

**Status:** **CLOSED UNSTARTED 2026-08-08. The decision went the other way and the page is
gone.** See §8. Nothing below was executed and the work order is preserved verbatim.

*The previous marker, kept because the outcome only makes sense against it:*

> **open, BLOCKED on one decision. Do not start it until that decision is made.**
> `crowdmon` was deprecated 2026-08-07 ([`../../DEPRECATED.md`](../../DEPRECATED.md) §3). This
> is a copy fix to a page whose future is undecided: **worth doing if `cot-analyzer`'s
> `/damage` page keeps being read, moot if it does not**, in which case close it unstarted
> rather than leaving it open. Nothing in the work below changed; only whether it is worth
> doing.
>
> The register's rule is that a handoff without a completion status gets executed by a future
> session, so this marker exists to stop that happening to a page that may be on its way out.

Written 2026-08-06. Released by §6 of
[`2026-08-06-forced-flow-respecification.md`](2026-08-06-forced-flow-respecification.md),
which is a specification correction and deliberately not executable. **This one is a work
order**, and it is the only part of that lineage that can be acted on without a re-run.

---

## 1. What this asks

> When `trigger_{side}_pool_agrees` is `False`, both renderers say the level "would force a
> book that is not there". Make the copy say what was measured instead.

A copy and vocabulary change across two repos. **No data change, no threshold change, no
change to `D`, no new column, and no change to what is suppressed.** If a diff touches a
number, it is out of scope.

---

## 2. Why, and the line between what may and may not be said

`npf/docs/crowdmon/2026-08-06-forced-flow-mechanism-verdict.md` measured what follows a
crossing in each group. The relevant part, and **only** this part, is what the new copy may
rest on:

- Flow follows a crossing whether or not the named pool is present. Within-group, crossing
  weeks against non-crossing weeks, the Disaggregated sell side moves **-0.0190** where the
  pool agrees and **-0.0184** where it is contradicted (verdict §4 and
  `ffm-per-side-2026-08-06.csv`).
- The crossing-specific difference between the groups is **small**: a
  difference-in-differences of **-0.0014 (p 0.047)** and **-0.0027 (p 0.0099)**, against
  headline group differences of 4.5% and 4.0% of the pool.

**What may NOT be said, and this is the sharp edge of this handoff.** The composition split in
§3 of the respecification, that the contradicted pool adds fresh exposure while the agreeing
pool liquidates, is a **descriptive crosstab of published labels with no inference behind it
and a known mechanical confound**. It is motivation for a future test. A rendered surface
asserting it would convert an advisory number into a published claim, which is the failure
this whole lineage has been correcting. Copy that says "flow still follows, and the difference
is small" is supported. Copy that says "it arrives as fresh shorts" is not.

---

## 3. What is actually wrong, precisely

**The row is not hidden**, and an earlier draft of the respecification's §6 said it was. It is
plotted with a hollow marker, it is named in the legend, and it gets a grid cell. Three pieces
of copy are wrong, all in the same way: they describe an absence where there is an event.

| where | today | why it is wrong |
|---|---|---|
| `report.format_offside`, [`../../src/crowdmon/futures/report.py`](../../src/crowdmon/futures/report.py) | "this level would force a book that is not there. Signal-implied, not held." | true of the forced book, implies nothing follows |
| `damage.py` legend, cot-analyzer | "pool on the other side, **no cell**" | names the missing label, not the state |
| `damage.py` grid cell, cot-analyzer | "(pool on the other side)" | reads as a null beside three populated columns |

---

## 4. What must not change

Five things, each of which someone could plausibly touch while doing this and must not.

1. **The quadrant suppression stays.** Reading instruction 1 of the damage page is correct:
   the quadrant's severe axis is `D`, a conditional severity for the **named** pool, so
   placing a contradicted row in a cell attaches the wrong pool's severity to a real level.
   This handoff gives the row a description, not a cell.
2. **`SCHEMA_VERSION` must NOT be bumped.** `publish.py` is explicit that a bump shipped ahead
   of a consumer release loses the whole `/damage` page rather than the new key, and no
   existing key changes meaning here. Copy is additive.
3. **No countdown, no forecast.** The reference bar moves faster than spot (on 6C, 1.68x), so
   distance closes without the market doing anything. Both docstrings already say this and
   neither surface does.
4. **`D` stays non-directional** and stays unmultiplied by the distance.
5. **Nothing real-time actionable.** The verdict is a mechanism claim on revised first
   differences. Copy implying a reader could have acted voids it.

---

## 5. The structural fix, which is the actual work

The obvious version of this task is editing three strings. That would leave the same defect
that made it possible.

`cot-analyzer/tests/test_damage_vocabulary.py` guards crowdmon's vocabulary against being
typed into the consumer: `SCORE_STATES`, `UNWIND_STATES`, `STRATA`, the `QUADRANT` phrases and
`DAMAGE_BANDS`. **"pool on the other side" is not on that list**, and it is authored locally in
`damage.py` in two places, even though it carries crowdmon's reading exactly as the `QUADRANT`
phrases do. So a session that changes only crowdmon's copy will ship a producer saying one
thing and a page saying the old thing, with every test green.

The work is therefore, in order:

1. **crowdmon**: give the contradicted state a named constant beside `QUADRANT`, put its
   phrasing in `COLUMN_DEFINITIONS`, and publish it in the manifest with the rest of the
   vocabulary. `format_offside` renders the constant.
2. **cot-analyzer**: read that string from the manifest in both places, delete both local
   copies, and **add its fragments to `FRAGMENTS`** so the next copy cannot come back.

Step 2's guard extension is the part that makes this stick, and it is the reason this is a
handoff rather than a three-line patch.

---

## 6. Proposed copy, as a proposal

Wording is the executing session's call; these carry the constraints of §2 and §4.

- **The state**: "level live, pool on the other side". It names what is true rather than what
  is missing.
- **The explanation**, `format_offside`: "The level is real and the pool the trigger names is
  not on that side. Flow of a similar size has historically followed a crossing either way,
  with the difference between the two groups small; what this flag says is which book is
  positioned there, not whether anything happens."
- **`pool_agrees` itself**, in `COLUMN_DEFINITIONS`: state that it is the sign of `pool_net`
  compared with the price signal, that it has **no lookback dependence**, and that it has
  three states, of which "nobody checked" is not "no".

---

## 7. Acceptance

- `cot-analyzer`: `pytest tests/test_damage_vocabulary.py` passes with the new fragments
  added, and fails if either local copy is reintroduced. Verify by reintroducing one and
  watching it fail.
- `crowdmon`: full suite, plus whatever asserts the manifest's shape.
- The published `SCHEMA_VERSION` is unchanged, checked rather than assumed.
- The `/damage` page renders against the pinned 2026-07-28 panel with no blank markers and no
  market dropped, per reading instruction 3.
- A diff review confirming no number moved anywhere.

**Order matters**: crowdmon ships first, because the consumer reads the string from the
manifest and cannot render what has not been published. A cot-analyzer PR merged first would
render an empty state.

---

## 8. Outcome

**Closed unstarted, 2026-08-08. No code was written and none of §5 was executed.**

§1's own condition decided this rather than a judgment made here. The handoff said it was
worth doing if `cot-analyzer`'s `/damage` page kept being read and moot if it did not, with
the instruction to close it unstarted in the second case. On 2026-08-08 that page was removed
(`cot-analyzer` PR #22): `pages/analytics/damage.py`, `components/crowdmon_artifact.py` and
both test files are gone, and the two macOS launchd jobs that published the panel and ran the
live suite were unloaded and deleted the same day. `DEPRECATED.md` §3 had listed exactly those
three things as the open question, and it has now been answered.

**Both surfaces this handoff names are gone, so there is nothing left to make consistent.**
`report.format_offside` still carries the contradicted-state copy in this package, and it is
left exactly as it was: crowdmon is frozen, not retracted, and editing a renderer nobody calls
would be a change for its own sake.

**What does not survive the closure, recorded so it is not rediscovered as new.** §5 was the
part worth keeping and it is now unreachable:

- The defect it identified was real. `pool on the other side` was authored locally in
  `damage.py` in two places and was absent from `test_damage_vocabulary.py`'s `FRAGMENTS`, so
  a session changing only crowdmon's copy would have shipped a producer and a page saying
  different things with every test green. That gap died with the file rather than being fixed.
- The generalisable lesson outlived both. `cot-analyzer`'s `docs/ARCHITECTURE.md` keeps it in
  the note that replaced its crowdmon section: a producer's vocabulary travels in the
  artifact's own manifest and is never typed into the consumer, with a test that fails if it
  is. That is the pattern to copy if another published artifact ever arrives there.

**What this closure does NOT do.** It retracts nothing. The measurements in §2 stand, the
verdict they cite (`npf/docs/crowdmon/2026-08-06-forced-flow-mechanism-verdict.md`) stands, and
the sharp edge in §2 about what may not be said stands for anyone who reopens this. The five
constraints in §4 remain correct statements about the system they describe. Per
`DEPRECATED.md` §4, none of the three conditions for revisiting this package is met by
removing a page, so this closure is not evidence about the thesis in either direction.

**If the page ever returns**, this handoff is executable as written apart from step 2 of §5,
which names files that no longer exist. Start from §5 step 1, which is entirely within this
package and unaffected.
