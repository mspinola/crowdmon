# Seasonality: how much of an extremity reading is the crop calendar?

**Report** Disaggregated, futures-only. **Universe** 27 markets, 2006-2026; 11 ags against 16 others.
**Reproducer** `COTDATA_STORE=~/code/cotdata_store python docs/analysis/reproduce_seasonal.py`.
**Code** `crowdmon.futures.seasonal`, module spec §5.4.

§5.4 makes three claims and offers no measurement:

> Commercial and producer-merchant positioning in agricultural markets is strongly seasonal.
> Raw z-scores on those categories are **dominated by seasonality** and will produce spurious
> extremes every year at the same time. Apply a seasonal decomposition before z-scoring
> commercial categories in ags. **Managed Money is less affected** but not immune.

Measured over twenty years, **one holds, one is false, and one is backwards for the category
it names.** This was an open caveat in two published analyses; it is now closed.

---

## 1. Two statistics, and only one of them is sound

`seasonality_report` emits both because they disagree, and the disagreement is the story.

- **`variance_share`** — between-week variance over total. How much of what you actually
  observe the calendar explains. **The one to use.**
- **`mean_spread`** — max minus min of the ~53 weekly means. Intuitive, and **badly biased
  upward by noise**, because it is the range of 53 noisy estimates.

On a synthetic pair with *identical* true seasonal amplitude, adding noise moved `mean_spread`
from 20.7 to **64.2** while `variance_share` correctly fell from 0.98 to 0.13. The two rank
the real categories almost in reverse.

**This matters because my own first pass used `mean_spread` and got the answer wrong.** The
finding reported at the time, "ags carry roughly twice the seasonal swing and Managed Money is
the most seasonal category in ags", does not survive the correct statistic. What follows is
the corrected version.

---

## 2. §5.4's claim, on the statistic that settles it

Week-of-year variance share of extremity `z`, ags against everything else:

| category | ag | non-ag | ratio |
|---|---|---|---|
| other_reportable | 0.0074 | 0.0028 | **2.65x** |
| swap | 0.0141 | 0.0065 | **2.17x** |
| nonreportable | 0.0059 | 0.0056 | 1.04x |
| **producer_merchant** | **0.0046** | **0.0049** | **0.95x** |
| managed_money | 0.0016 | 0.0042 | **0.39x** |

Sample sizes are comparable (197 against 248 observations per week), so this is not a
power artifact.

**Producer/Merchant — the category §5.4 names — is not more seasonal in ags than anywhere
else.** Ratio 0.95, which is to say identical. The categories that genuinely are more seasonal
in ags are Swap and Other Reportable, neither of which the spec mentions.

**Managed Money is less affected, as §5.4 says**, and most clearly so in ags: 0.0016 is the
lowest figure in the table by a factor of three. That claim holds.

---

## 3. Nothing is "dominated by seasonality"

The largest week-of-year variance share anywhere in the panel is **0.0141**. Pooled across
everything it is 0.0087.

**Seasonality explains at most 1.4% of the variation in any category, in any group.**
"Dominated" is not a defensible description of a 1.4% component, and the practical consequence
follows: seasonality cannot be producing the spurious annual extremes §5.4 warns about,
because a 1.4% component cannot move a percentile far enough to manufacture one.

### The mean_spread bias, in its most concrete form

`mean_spread` for ag Producer/Merchant is 0.692 z-units. Where does it come from?

| | week | mean z | observations |
|---|---|---|---|
| peak | 2 | +0.095 | 198 |
| trough | **53** | **−0.597** | **33** |

**ISO week 53 exists only in some years**, so it carries a sixth of the sample and its mean is
correspondingly noisy. Drop weeks with under 50 observations, and:

    spread 0.692  ->  0.275 z-units
    trough moves from week 53 to week 30 at -0.180

against a non-ag figure of 0.334 computed the same way. So on well-sampled weeks the ag swing
is **smaller** than the non-ag one, and the "2x more seasonal" reading was one rare partial
week.

Two independent lines now agree: the variance share (0.95x ratio) and the sparse-week-adjusted
spread. §5.4's central claim about Producer/Merchant in ags is not supported.

---

## 4. Deseasonalising makes the series worse

The decisive practical test. Applying the trailing profile to ag extremity `z`:

| | |
|---|---|
| rows with a profile | 43,395 of 57,805 (75.1%) |
| std **before** | 1.2489 |
| std **after** | **1.3212** |
| correlation | 0.9599 |
| median absolute change | 0.228 z-units |
| rows moved more than 0.5 z | 15.7% |

**The adjustment increases the standard deviation.** That is the whole argument in one line: a
trailing week-of-year mean is an *estimate* with its own error, and when the component being
removed is worth ≤1.4% of variance, the estimation error exceeds the signal. Subtracting it
adds noise.

It is not a small intervention either — 15.7% of rows move by more than half a z-unit, and it
costs a three-year warm-up on top of extremity's own. So it would meaningfully change readings
while making them less informative.

`deseasonalise` therefore exists and is **off by default**. Turning it on trades a visible
caveat for an invisible transformation, which is the worse of the two.

---

## 5. The lookahead this module refuses

A seasonal profile feels like a property of the calendar rather than an estimate from data,
which is why full-sample seasonal adjustment is so common and so wrong: subtracting a week-34
average computed from years that had not happened yet is straightforward use of the future.

`seasonal_profile` is trailing and excludes the current observation. Verified the same way as
every other window in this package: the profile computed on 2006-2018 is identical to the same
rows computed from the full panel. First non-null value is 2009-06-09 against data beginning
2006-06-13, which is the three-year `min_years` cost.

**One limitation no bucketing fixes.** The third Tuesday of August falls in ISO week 34, 33,
33, 33, 34 over 2020-2024; `dayofyear // 7` gives 33, 32, 32, 32, 33. A fixed point in the crop
calendar drifts by ±1 week against any weekly index because 52 weeks is not 365 days. That
smears the profile by about a week in each direction and is a floor on how sharply any of this
can resolve seasonality.

---

## 6. What this closes and what it does not

**Closes:** the caveat carried in
[extremity](2026-07-28-extremity.md) ("real but modest, unmeasured for CR") and
[concentration](2026-07-28-concentration.md) ("five of six markets extreme against own history
are short-side ags, exactly what §5.4 predicts as an artifact"). The concentration reading in
particular is **not** a seasonal artifact: at ≤1.4% of variance, seasonality cannot lift five
markets to the top of a percentile ranking.

**Does not close:** seasonality of the CR series itself was measured only for extremity `z`.
And this is the Disaggregated 27-market panel — the ICE/Nodal power and REC universe has its
own calendar (compliance years, delivery periods) which is likely stronger and is unmeasured,
since those markets have too little history for a three-year profile anyway.

---

## Bottom line

§5.4 asks for a seasonal decomposition before z-scoring ag commercials. Measured, the
correction is not worth applying and the premise is mostly wrong.

**Seasonality explains at most 1.4% of the variance anywhere**, so nothing is "dominated" by
it. **Producer/Merchant, the category the spec names, is no more seasonal in ags than
elsewhere** (ratio 0.95). Managed Money is genuinely less affected, which is the one claim that
holds. And applying the adjustment **raises** the standard deviation from 1.249 to 1.321,
because a trailing week-of-year mean is an estimate whose error exceeds a 1.4% signal.

The methodological lesson is larger than the finding. My first pass at this used `mean_spread`
and reported that ags were twice as seasonal and that Managed Money led them. Both were wrong:
`mean_spread` is inflated by noise, and more than half the ag figure came from ISO week 53, a
partial week with a sixth of the sample. **The statistic that felt intuitive ranked the
categories nearly in reverse from the one that was sound.**

**In plain terms: the crop-calendar effect is real, systematic, and far too small to matter,
and correcting for it would do more harm than leaving it alone.** The open caveat in two
earlier analyses is closed, and the readings they flagged as possibly seasonal are not.
