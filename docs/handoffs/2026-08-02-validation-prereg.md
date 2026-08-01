# Handoff: pre-registration for §10 validation, to be executed by a cold session

**Status:** open, jointly drafted, **sections 4, 5 and 7 reserved for the commonality/impact
session**. §8 decided by the human.
**Date:** 2026-08-02
**Lives:** here, permanently. **Runs:** in `npf`, through `crucible`. See §8.
**Target:** a session that has written none of this package
**Not for:** either session that built crowdmon. See §1.

---

## 1. Why neither builder can execute this

Agreed by both sessions, on two independent grounds.

**The boundary forbids it physically.** `tests/test_boundaries.py` refuses an import of
`crucible` and says why: "a package that can import the judge can render a verdict on its own
output. Keeping the import out means a directional strategy derived from this work has to
leave the package to be validated, **which is the seam**."

Read that precisely: it forbids **importing** crucible, not **describing** a validation. What
has to leave crowdmon is the execution, not the document. See §8.

**Governance forbids it procedurally.** `npf/AGENTS.md`: "Never render the verdict on a book
you authored in the same session." Between the two sessions active on 2026-08-01 to 08-02,
every engine in this package was written. That reasoning does not stop applying because the
next build-order step happens to be labelled validation.

**What the builders can legitimately do** is pre-register: commit to the tests before results
are seen, which is the standard pattern (`livebook/docs/PREREGISTRATION.md`). §2 is the
honesty problem with that here.

---

## 2. Declared priors: what has already been looked at

**This is the section that cannot be written by anyone else, and it is the reason the split in
§3 is what it is.** A pre-registration is only worth something if it commits before results
are seen. Parts of this one cannot, and the evaluator needs to know exactly which.

### March 2020 has been examined twice, and the answer reversed

| formula reading | lead-in (Oct19-Jan20) | event (Feb-Apr20) | after |
|---|---|---|---|
| `Phi` raw, per §A.9's formula | **1.18x** baseline | 0.75x | 0.89x |
| `Phi` percentile-ised, per §A.9's preamble | **0.76x** | 0.45x | 0.68x |

Under the first reading `D` looked mildly elevated before the drawdown, which is what §10 asks
for. Under the second it is below baseline throughout. **The apparent lead was an artifact of
a near-constant term** (`2026-08-01 §A15`, §A21). The percentile-ised reading is the one that
shipped.

Anyone specifying a March 2020 test after reading that table is choosing windows and
thresholds knowing which choices produce which answer. **That is why the test specification is
not this session's to write.**

### Other windows already seen

| window | mean `D_sell` vs baseline | reading |
|---|---|---|
| 2021 ags / lumber | 1.65x | percentile-ised |
| 2022 invasion | 1.88x | percentile-ised |

Both hand-chosen after the fact, on the same data, by the session that wrote the measure.
Neither is evidence and both were labelled as such where published
(`docs/analysis/2026-07-28-composite.md` §5).

### What has NOT been looked at

- Feb 2018, Aug 2024 yen carry, silver 2021, gold 2025: **never examined at all**, by either
  session, under any formula reading. These are clean.
- No episode has been examined with `D_buy`. Every look has been the sell side.
- No episode has been examined per-market. Every figure above is a cross-sectional mean.

**Those three are where an uncontaminated test can still be specified**, and the evaluator
should weight them accordingly.

---

## 3. The split, and why it is not the obvious one

The first proposal was that the `composite.py` author write the test specification, since they
own the module and ran the episodes. **That is backwards**, for the reason §2 makes concrete:
the value of a pre-registration lives in committing before seeing, and that author has seen
the answer flip sign.

| section | owner | rationale |
|---|---|---|
| §1 why neither builder executes | both, agreed | done |
| **§2 declared priors** | **composite author** | only they know what was looked at |
| **§6 reading instructions** | **composite author** | findings about modules they built |
| §4 data availability | commonality/impact session | measured it, reserved below |
| §5 inputs inventory | commonality/impact session | reserved below |
| **§7 test specification and thresholds** | **commonality/impact session** | **uncontaminated by §2** |
| §8 where this lives, where it runs | **decided by the human**, see §8 | not either session's call |

The composite author supplies the disclosure and the reading instructions. The other session
specifies the tests. Neither runs them.

---

## 4. Data availability (RESERVED)

*For the session that measured it. Their figure, verified independently here: the vintage
store spans 2025-01-07 to 2026-07-28, so of §10's replay list only **gold 2025** is
point-in-time. Feb 2018, Mar 2020, silver 2021, ags 2021 and the Aug 2024 yen carry all
replay current-state data with revisions applied and no as-of protection, which
`cot_vintage.md` §5.3 records as permanent rather than a gap to fill. §10's mechanical test
"vintage replay reproducing historical values exactly" can only run from 2025 onward.*

---

## 5. Inputs inventory (RESERVED)

*For the same session. The point an evaluator most needs: which of the configured constants to
vary, and which variations are known to matter. `kappa` 0.2 and `Y` 0.75 have sanctioned
ranges; `gamma` has none anywhere in the appendix; the five fragility weights are judgement.
`2026-08-01 §A22` measured that rankings survive the weight VALUES (±0.15 order-preserving
jitter keeps 7-10 of the top 10) and correctly do not survive their ORDERING (inverted: 0 of
10), so an evaluator varying the wrong one learns nothing.*

---

## 6. Reading instructions the evaluator needs first

Four things about `D` that are not discoverable from the number, gathered in the README and
repeated here because an evaluator who does not know them will mis-specify a test.

1. **`D` falls during an unwind, and that is correct.** It describes a pre-condition, and both
   the position and the forceable holders leave while the event happens. A test that expects
   `D` to peak *during* a drawdown is testing the opposite of what the measure claims.
   `2026-08-01 §A17`.
2. **`Phi` has no cross-market signal independent of the weight table.** Flat weights reduce it
   exactly to `1 - spreading/OI`. `2026-08-01 §A21`.
3. **Extremity readings persist.** 10.11% of weeks sit above the nominal 5% threshold, in
   episodes averaging 4.8 weeks and running to 42, with 57.6% of hot weeks inside runs of 8+.
   **Exceedances are not independent events**, so any test treating "weeks above the 95th" as a
   sample size has an effective sample roughly a fifth of its nominal one. `2026-08-01 §A11`.
4. **`D` assumes exits are independent across markets and they are not.** `pct(T_eff) ==
   pct(T)` bit-identically, so §A.6's commonality cannot enter `D` at all and must be read
   beside it. `2026-08-02 §B2`.

Plus the scope limit: **`D` scores nothing before 2010-05-25** on a 27-market panel, because
`C = pct(z)` stacks two three-year windows. The 2008 GFC is unreachable. `2026-08-01 §A16`.

---

## 7. Test specification (RESERVED)

*For the commonality/impact session, per §3. Should specify, before any further looking: which
episodes, which windows, which statistic, which thresholds, what counts as a pass, and how the
contaminated episodes in §2 are handled differently from the clean ones.*

---

## 8. Where this lives, and where it runs (DECIDED)

**Decided by the human, 2026-08-02.** Both sessions had read the boundary as putting the
document out of scope too. It does not.

| | where | why |
|---|---|---|
| **this document** | stays here, `crowdmon/docs/handoffs/` | the boundary forbids importing `crucible`, not describing a validation |
| **the execution** | an evaluator session in `npf`, which has `crucible` | that is the seam the boundary draws |
| **the verdict** | `npf/docs/` | written where it is run, by whoever ran it |

The reasoning worth preserving: this splits the difference **without hiding a public package's
pre-registration inside a private repo**. crowdmon is public and `npf` is not. A prereg that
lives where the thing it constrains cannot be read by the same audience is a weaker prereg,
whatever directory it sits in.

Consequences for the evaluator:

- Read this file from crowdmon. Do not copy it into `npf`, because that opens exactly the
  silent-regression window CLAUDE.md describes, where a duplicated living document drifts
  until someone happens to diff the copies. Cite the path.
- The verdict document in `npf/docs/` is the new artifact, and it is the one that may cite
  `crucible`. Nothing in this repo changes when it lands.
- This handoff stays **append-only** either way (`docs/handoffs/` lifecycle). The outcome gets
  appended here with a pointer to the `npf` verdict, not written over §2 or §6.

---

## Open questions for the human

1. **Does the split in §3 stand?** It inverts the first proposal deliberately.
2. ~~Where does this document live once complete?~~ **Answered, §8.**
3. **Is §10 validation even next**, or does `2026-08-02-reflexivity.md` (§A.8, claimed, not
   started, blocked on a horizon decision) go first?
