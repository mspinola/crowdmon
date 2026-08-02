# Handoff: macro-book PCA, the futures absorption ratio

**Status:** complete (PR #20)
**Date:** 2026-08-02
**Claimed by:** the session that built `commonality.py`, `impact.py`, `volume.py`,
`riskunits.py` and `coverage.py`
**Blocked on:** nothing. Measured below

> **Announcing before the first line of code**, per this directory's convention. If you were
> about to start it, say so and I will drop it. Nothing has been written yet.

---

## Scope: the PCA the spec names, not the one nearest to hand

Module spec §7:

> **Macro-book PCA.** PCA on positioning *changes*. PC1 approximates the aggregate systematic
> book; its variance share is the futures absorption ratio. Loading rotation indicates the book
> being redefined.

**The trap, flagged before starting because both sessions have already walked into its
sibling.** `commonality.py` builds an **illiquidity** panel, and a PCA over it is the closer
object by a wide margin: the panel already exists. It is not this. §7's PCA runs on
**positioning changes** and its PC1 share is the absorption ratio. Building the reachable one
and reporting it under the spec's label for the other is the error the README nearly shipped,
and the one the other session made in `§B16` four hours after warning me about it.

---

## What is available, measured 2026-08-02

Panel: Managed Money `net_risk_usd_z`, per §7's "matrix of z-scored Managed Money positioning,
markets x weeks", differenced to get changes.

| | |
|---|---|
| raw matrix | **948 weeks x 26 markets** |
| cells present | 95.7% |
| **weeks with no missing market** | **0** |

**A naive listwise PCA returns nothing.** 95.7% coverage sounds complete and yields an empty
rectangle, because the holes are spread across markets rather than concentrated in weeks.

### Dropping two markets buys the entire panel. Dropping one fewer costs two and a half years

| markets kept | complete weeks | span |
|---|---|---|
| 26 | **0** | n/a |
| 25 | 746 | 2008-06-10 to **2023-12-26** |
| **24** | **947** | 2008-06-10 to **2026-07-28** |
| 22 | 947 | same |

The 25th market ends in 2023 and truncates the panel to it. Below 24 nothing further is
bought. So the choice is 24 markets and the full span, and it should be **derived from
`coverage.py` rather than hand-picked**, which is what that module was built for.

### It reaches 2008, and `D` structurally cannot

The differenced panel starts **2008-06-10**. `D` starts **2010-05-25**, because `C = pct(z)`
stacks two three-year windows (`2026-08-01 §A16`). This PCA needs one window, not two.

**So the absorption ratio can say something about the 2008 crisis that the composite is
structurally unable to reach.** That is the single most valuable property of this module and it
was not obvious before measuring. It also means this is the only engine in the package whose
history covers a genuine systemic unwind.

---

## Decisions this needs, flagged rather than defaulted

This is how `kappa` and `gamma` arrived. None of these gets a silent default.

1. **Which 24 markets, and by what rule?** Derived from coverage, not chosen. The rule must be
   stated and stable, because changing it changes every loading.
2. **Trailing window or full sample?** A full-sample PCA is lookahead: the absorption ratio at
   2010 would be computed from 2026 data. It must be trailing, and the window length is a
   parameter with no sanctioned value in the appendix, so it needs a sweep in the shape of
   `weight_sensitivity.sweep`.
3. **Correlation or covariance matrix?** The inputs are already z-scored per market, so the two
   nearly coincide. Nearly is not exactly, and the difference is a scale choice that must be
   stated.
4. **Sign convention for PC1.** Eigenvector sign is arbitrary. Without a pin, "loading rotation"
   will report a flip that is an artifact of `numpy` rather than the book being redefined.
   Pin it to a fixed anchor and test it.

## Risks to design around

- **Loading rotation needs a rolling PCA**, so cost is `O(weeks x window)`. Measure before
  reporting per-week loadings across 947 weeks.
- **`D` and this share no floor.** Anything comparing them must state which window applies,
  or a 2008 absorption reading will be silently compared against a `D` that does not exist.
- **The absorption ratio is a variance share, so it is bounded and always positive.** It will
  look plausible on any data, including noise. It needs a null: PC1's share on a shuffled
  panel, reported beside it.

## Out of scope

- Trend alignment (§7, unclaimed) and correlation clustering (§7, unclaimed).
- Wiring into `composite.py`. §A.9 has no term for it, the same way it has none for §A.6's
  commonality (`2026-08-02 §B2`), so it is reported beside `D` rather than inside.

## Prior art

`commonality.py` for panel construction and the own-market exclusion argument, `coverage.py`
for the market selection, `weight_sensitivity.sweep` for the parameter sweep shape.


---

## Outcome, 2026-08-02

Shipped as `futures/macro_pca.py`: `positioning_panel`, `select_markets`, `absorption_ratio`,
`rolling_absorption`, `loading_rotation`, `shuffled_null`, `window_sensitivity`,
`format_absorption`. 28 tests, 21 offline and 7 live. Amendments `B21`-`B23`.

**All four flagged decisions were taken as proposed**, with one correction found by measuring.

| decision | taken |
|---|---|
| which markets | derived from coverage counts, ties break toward more markets |
| trailing or full sample | trailing. `absorption_ratio` over a whole panel is marked descriptive-only and a test pins that truncating the future does not move a reading |
| correlation or covariance | correlation, columns standardised inside each window |
| PC1 sign | pinned to sum positive **for presentation**, and rotation made sign-invariant instead. See below |

### The one thing that had to change

`loading_rotation` shipped as `1 - cos` and was wrong. An eigenvector's sign is not
identified, so the positive-sum pin flips whenever that sum crosses zero, and **8 of 843
readings came back at ~1.99 against a median of 0.0004**. `1 - |cos|` is bounded in `[0, 1]`
and those weeks read ~0.002, which is what they always were. `B23`.

The handoff predicted this in the abstract ("without a pin, loading rotation will report a
flip that is an artifact of `numpy`"). It got the remedy wrong: a pin is not enough, because
the pin itself is what flips. The measure has to not care.

### The finding that changes what the module is for

**PC1 is the grain complex on Disaggregated and risk appetite on TFF** (`B21`). §7's
"PC1 approximates the aggregate systematic book" is true of one panel and false of the other.
So the report type is the subject of this engine rather than a parameter to it.

### Not done, deliberately

The panel reaches **2008-06-10** against `D`'s 2010-05-25, so this is the only engine here
whose history covers a genuine systemic unwind. **No episode in it has been examined.**
Pointing it at 2008 is the after-the-fact window-picking §7 of the pre-registration exists to
prevent, and by now this session is the wrong one to specify that test.
