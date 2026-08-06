# Handoff: does `Phi` or `I` carry information NPF does not already have?

**Status:** open

Written 2026-08-05, before computing any statistic below. Companion to
[2026-08-05-forced-flow-mechanism-test.md](2026-08-05-forced-flow-mechanism-test.md); the two
are independent and may run in either order.

---

## 1. What this asks, and what it refuses to ask

> Before any book change: is `Phi` or `I` **linearly and rank-independent** of what NPF's trend
> book already reads?

It is null-first on purpose. If the answer is no, the question closes for the price of a
measurement and nothing in `npf` is touched.

**What it refuses to ask, and the refusal is load-bearing:** whether NPF should trade `D`, or
gate an entry on it, or size on it. `crowdmon` ships no strategy and every output is a
statement about tail shape rather than about next week's return (§A.10). **A positive result
here is not permission to trade it.** It is permission to write a second, separately
pre-registered piece of work that has to pay its own variant cost.

---

## 2. Why the question is worth asking, and why the answer is not obvious

The motivation is a collinearity that rules out the other two terms.

**The trigger distance is out.** `2026-08-04 §D9` established `move_from_spot` is an identity
with the trailing `k`-day return. NPF's book is Donchian 55/20 with an EMA 50/100 regime gate,
so as an entry input the trigger distance would largely re-express momentum the book already
trades. `composite.damage_block` already refuses to multiply it into `D` for the same reason
(correlation -0.481 with `C`).

**`C` is out.** NPF's winning arm is `index_oinorm`, the OI-normalised cotmetrics COT index.
`C` is vol-scaled positioning extremity against three years of a market's own history.
Different formula, same underlying quantity, and `cotmetrics` and `crowdmon` are deliberately
kept as peer consumers so there are not two disagreeing answers to one question. Feeding both
into one book relocates that disagreement inside the book.

**`Phi` and `I` are the survivors.** Fragility is about *who holds*, not how much or which way.
Illiquidity is microstructure. Neither is a function of momentum or of net extremity.

**But do not assume the trigger case generalises, because it is measured not to.**
`nearest_trigger`'s docstring records that the trigger is **time-series momentum, not a
breakout**: on 6C the TSMOM trigger sits +4.14% from spot while the Donchian 250d high is
+5.31% and the low -0.77%. NPF uses the breakout, crowdmon uses TSMOM, and on the one market
where both were measured they are not the same level. So even the strongest collinearity claim
in this document is partial, and Stage 1 must **measure** the spanning rather than assert it.

---

## 3. The governance cost, which is why Stage 1 gates Stage 2

The trend book's v1 record, from `config/trend/donchian_ls_regime_index.yaml` and the frozen
pre-registration at `npf/docs/trend_following/trend_following_cot.md`:

> gauntlet **3/4 FAIL at `n_variants=12`**. REAL / STRONG / DURABLE pass; **GENERAL fails** the
> conservative WRC (0.061 long, 0.078 both) while the more powerful SPA passes (0.008, 0.001).

**Every variant tried, including discards, feeds `n_variants`.** So adding a crowdmon arm and
searching over it would raise the multiple-testing denominator on a book whose GENERAL pillar
**already fails at the strict bar with p = 0.061**. A search that adds arms does not merely cost
compute here; it can convert a marginal pass into a fail on a pillar unrelated to the thing
being tested.

Both stages below are therefore designed to add **zero arms**:

- Stage 1 produces no trades at all.
- Stage 2 annotates the book's **existing** trade log rather than generating a new one.

If a future session wants an arm, that is the separate work in §1, and it opens with an honest
statement of what it does to `n_variants`.

---

## 4. Data availability, measured 2026-08-05

Against `~/code/crowdmon_store/damage/2026-07-28/panel.parquet`:

| column | non-null rows | distinct weeks |
|---|---|---|
| `phi`, `phi_pct` | 51,316 | 1,051 |
| `illiquidity_sell` | 43,522 | 948 |
| `dtl_sell` | 48,848 | 1,051 |

Range 2006-06-13 to 2026-07-28, 53 market codes.

**No import and no new dependency direction.** The panel is read from `CROWDMON_STORE` as a
parquet, exactly as `cot-analyzer` does, per
[ADR-0001](../adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md). Do not add
`crowdmon` to npf's dependency graph for this work.

**Universe overlap must be measured, not assumed.** crowdmon scores 48 market codes; NPF's
universe comes from `cotmetrics-config/params.yaml` (47 named markets, 7 `heldout`). The
intersection is the study universe and its size is reported in the outcome. A market absent
from either side is dropped and counted, never imputed.

---

## 5. The `Phi` caveat that can invalidate a positive result

`Phi` has a known, unresolved calibration issue, and the evaluator must handle it or the study
is uninterpretable.

- `2026-08-03 §C6-C8` / `weight_sensitivity` / §A.11: **`Phi` has no signal independent of the
  weights.** The weights are configured, never fitted.
- `swap: 0.4` was measured as **incoherent between regimes**: swap sits at 0.305 of Managed
  Money on routine turnover and 0.067 under stress. The weight table was deliberately left
  unchanged (`2026-08-03-swap-dealer-weight-decision.md`, decided as option (a)).
- `§C7`: moving `w_SD` inflates median `Phi` by 19.6%, worst on gold at +27.8%, and precisely
  during stress weeks.

So a result of the form "`Phi` is orthogonal to NPF's features" may be reporting nothing more
than "**the weight table is orthogonal to momentum**", which is trivially true and worth
nothing.

**Required, not optional.** Stage 1 is re-run over the order-preserving band
`w_SD ∈ [0.2, 0.4]` (`§C10`), using `single_weight_sweep`, and the conclusion must **survive at
both ends**. If the answer flips inside the band, the finding is about the weights and must be
reported as such rather than as a finding about fragility.

`§C8`'s operating rule applies to the reporting: on classic outrights the band is a footnote
(Spearman 0.954), on the ERCOT and PJM book it can invert a market's own history (Transco Zone 6
at -0.416). NPF's universe is classic outrights, so the band is expected to be a footnote here.
Expected is not measured; report it.

---

## 6. Test specification, frozen

### 6.1 The existing feature set, fixed here

What NPF's book already reads, per (market, week):

1. Donchian 55/20 channel position.
2. EMA 50/100 regime state.
3. The `index_oinorm` COT arm value from `cotmetrics`.

Candidates: `phi`, `phi_pct`, `illiquidity_sell`, `illiquidity_buy`.

Nothing is added to either list once results are visible.

### 6.2 Stage 1, spanning. Target-free

No returns, no trades, no outcome variable. The question is purely whether the candidate is
already determined by the existing features.

**Statistic: partial Spearman rank correlation.** Rank-based rather than OLS `R^2` because
`phi_pct` is a percentile, `phi` is a bounded share, and `I` is right-skewed; a linear fit on
these measures the wrong thing.

For each market, for each candidate, compute the residual rank variance of the candidate after
projecting out the three features, expressed as a share of its total rank variance. Report the
**median across markets** and the interquartile range, per report type, never pooled across
report types.

| outcome | criterion |
|---|---|
| **spanned, question closes** | median residual share **< 0.25** |
| **independent, proceed to Stage 2** | median residual share **> 0.50** **and** the conclusion survives both ends of the `w_SD` band (§5) |
| **uninformative** | anything between, or a band that flips the answer |

Time-series and cross-sectional versions are both run and both reported. They answer different
questions and disagreement between them is a finding, not a defect.

### 6.3 Stage 2, conditional separation. Only if Stage 1 clears

**Annotation of an existing log, not a new search.** Take the trend book's existing trade log
unchanged. Join the candidate at each trade's entry date. Split at the candidate's in-sample
median. Compare the two `R` distributions.

- **Release lag applied conservatively:** the candidate is taken from the report week **before**
  the entry date, never the same week, because a Tuesday report is not public until Friday. This
  costs information and removes a lookahead channel; the trade is deliberate.
- Statistic: difference in mean `R` between the high and low groups.
- Inference: block bootstrap over calendar time, 13-week blocks taking all trades in a block,
  10,000 draws, `seed=20260805`. Trades cluster in time and an IID bootstrap over trades is
  **forbidden**.

| outcome | criterion |
|---|---|
| **separating** | difference in mean `R` with block-bootstrap raw p < 0.05, sign stable across both halves of the sample |
| **not separating** | anything else |

**Pre-committed, before looking:** `separating` is **descriptive**, not a validated edge. It
uses revised COT and an in-sample median split, and it is not a `TradeLog` produced by a rule.
It may not be reported as an edge, a signal, or a reason to change the book. The only thing it
licenses is the separately pre-registered work in §1.

### 6.4 What is forbidden

- **Creating a new arm, config, or book variant.** Both stages are read-only against existing
  artifacts.
- **Sweeping the split point** in Stage 2. Median, fixed.
- **Sweeping the feature set** in Stage 1, or dropping a feature that makes the candidate look
  more independent.
- **Pooling report types**, or pooling `sell` and `buy` illiquidity.
- **Reporting the IID bootstrap.**
- **Running Stage 2 when Stage 1 returns `spanned` or `uninformative`.**
- **Describing any Stage 2 result as an edge**, per §6.3.
- Adding `crowdmon` to npf's dependency graph, per §4.

### 6.5 Variant count

Stage 1 and Stage 2 as specified add **zero** variants to the trend book's `SearchSpaceLog`,
because neither produces a `TradeLog` from a rule. That is a design property, and the outcome
section must state it explicitly so the next gauntlet run is not silently mis-denominated.

The `w_SD` band re-run of §5 is a robustness requirement, not a search, and does not count
either. If the evaluator runs anything beyond this specification, the outcome says what and the
count is stated.

### 6.6 Store pinning

Same discipline as §5.9 of the mechanism handoff and §0 of the §10 verdict: pin the store,
commit a SHA-256 manifest of every parquet read, and measure how many store files moved after
the run began. `Phi` is price-free and therefore immune to the Norgate restatement channel, but
`I` is not, and the two are reported side by side.

---

## 7. Where this lives, and where it runs (DECIDED)

**Lives here** for the same reason as its companion: this directory's README is the status
register that stops a handoff being executed twice, and `npf` has none.

This one is **npf-owned work** despite living here, which is a wrinkle worth naming. It asks a
question about npf's book, and `crowdmon` must not be read as commissioning strategy research.
It is filed here because it is tracked here and because §1's refusal is a crowdmon invariant.
If `npf` grows its own `docs/handoffs/` with a status register, this is the first thing that
should move.

**Runs in `npf`.** Not necessarily by a cold session, since Stage 1 renders no verdict on a
book. **Stage 2 does**, so whoever runs Stage 2 must not be the session that later proposes the
book change, per the generator/evaluator split.

**The verdict is written in `npf`**, as
`npf/docs/crowdmon/YYYY-MM-DD-fragility-orthogonality.md`, with a reproducer beside it. The
outcome below gets a pointer and a one-line result, never a copy.

**Do not edit this body after execution.** Append §8.

---

## 8. Outcome

*To be appended by the executing session. Leave `Status: open` until then.*
