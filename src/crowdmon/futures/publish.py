"""The damage panel as a published artifact: this package's first and only writer.

`core/store.py` is deliberately absent and stays absent. This is not that: it writes one
versioned output directory for consumers to read, and it reads nothing back. The distinction
is the whole argument of `docs/adr/ADR-0001-crowdmon-publishes-a-panel-rather-than-being-imported.md`,
and the short form is that a store is state this package would then depend on, while an
artifact is a statement this package makes once a week and forgets.

## Why an artifact rather than letting a consumer import this package

The consumer that motivated it is `cot-analyzer`, the only UI in the workspace. It cannot
import `crowdmon` for four independent reasons and the fourth is fatal:

1. It records in three places that it **computes no metrics of its own**
   (`cot-analyzer/README.md:9`, `:50`, `cot-analyzer/docs/ARCHITECTURE.md:45`).
2. `brief.py` refuses the same shape from this side: *"a derivation in the rendering is how
   the next engine gets built by accident"*.
3. The ladder needs `unadj` **and** `propadj` prices plus `contract_specs`, all Norgate, and
   `cot-analyzer/server-side/README.md` states the Linux server cannot produce prices however
   it is provisioned.
4. **That server runs Python 3.9** and `pyproject.toml` here declares `>=3.10`.

So the seam is a file, and the consumer needs `pandas` and nothing else.

## What the artifact has to carry, beyond the numbers

**The vocabularies and the prose travel as data.** A consumer that hard-codes `"warmup"` or
the four `QUADRANT` strings has made a copy of a living document in a repo with weaker guards
than this one, which is the failure `2026-08-04 §C30` and the 104-line spec loss are both
about. Every enum and every note in `panel_manifest()` is read from the live constant at publish
time; `tests/test_publish_live.py` asserts the serialised `READING_INSTRUCTIONS` equal
`brief.READING_INSTRUCTIONS` rather than merely resembling them.

**The blocks are pre-rendered.** `report.format_damage_block` prints the three factors every
time and appends `format_offside`, which suppresses the quadrant when the observed pool is on
the other side (`2026-08-04 §D10`). A consumer assembling its own layout from the structured
dict would have rebuilt the `include_caveats=False` flag that `brief.py` deliberately does not
have. So both go out: the markdown for a reader, the dict for a chart axis.

## Three things about the panel that a consumer cannot infer

- **`offside` is the latest week only, by design.** `trigger.add_trigger_distance` is a
  point-in-time overlay because a full history is roughly 95,000 price-store reads against 90
  for one week. `damage_*_pct` has full history; the trigger columns are null on every earlier
  row. That is why `blocks` covers one week and `panel` covers all of them.
- **The pool column is supplied here rather than left null.** `add_trigger_distance` accepts
  `pool_column` and the reproducer's own build omits it, which leaves every `*_pool_agrees`
  null. The observed pool and the price signal disagree on a third of (market, horizon) pairs
  (`2026-08-04 §D10`), so publishing without it would ship a trigger that cannot say whether
  the book it would force is actually there.
- **Both report types, concatenated.** Disaggregated alone is a commodity panel; the
  financials reach a reader only through TFF, and `2026-08-04 §D7` is the argument for why
  Legacy is not a substitute (the two reports agree on open interest and non-reportables and
  on nothing else).
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import pandas as pd

from .. import __version__
from . import brief as brief_mod
from .commonality import CommonalityError, commonality_betas, illiquidity_panel
from .composite import (
    CROWDING_CATEGORY,
    SCORE_STATES,
    UNWIND_STATES,
    add_composite,
    add_score_state,
    add_unwind_state,
    damage_block,
)
from .contract_master import ContractMaster
from .extremity import add_extremity
from .flow import FLOW_STATES, decompose
from .fragility import contributions, market_fragility
from .io import from_current_store
from .notional import add_notional
from .pressure import rank_markets
from .report import (
    CLOSE_SIGMA,
    COLUMN_DEFINITIONS,
    DAMAGE_BANDS,
    FACTOR_QUESTIONS,
    QUADRANT,
    damage_band,
    format_damage_block,
)
from .riskunits import add_risk_units
from .stratum import BAND_ADVICE, STRATA, classify
from .trigger import TRIGGER_DISTANCE_COLUMNS, add_trigger_distance
from .volume import add_volume

#: Bumped whenever `PANEL_COLUMNS` or the manifest shape changes in a way a reader must
#: notice. A consumer refuses a version it does not know rather than rendering columns it
#: half-understands, so this is a contract and not a build number.
#:
#: **An additive optional key is NOT such a change, and bumping for one takes the consumer
#: down.** `cot-analyzer` degrades the whole `/damage` page to an "unavailable" card on a
#: version it does not recognise, so a bump shipped ahead of a consumer release loses the
#: page rather than losing the new key, while a reader that has never heard of the key
#: simply does not render it. `column_definitions` was added under version 1 for exactly
#: that reason. Bump when an existing key changes MEANING, shape or units.
SCHEMA_VERSION = 1

#: The environment variable naming the output root. **Raises when unset rather than
#: defaulting**, matching `COTDATA_STORE` and npf's `CMRDATA_STORE`: a store that silently
#: defaults is one a scheduled job writes to the wrong place without failing. The launcher
#: (`bin/publish_damage.sh`) defaults it, because launchd reads no shell profile.
STORE_ENV = "CROWDMON_STORE"

#: The reports that carry configured fragility weights. Legacy is absent on purpose and
#: `2026-08-04 §D7` is why.
DEFAULT_REPORTS = ("disaggregated", "tff")

#: The published column contract, declared rather than "whatever the chain happened to
#: emit". A reader asserts against this list, so an accidental rename fails at read time
#: instead of rendering an empty column.
PANEL_COLUMNS: tuple[str, ...] = (
    # identity
    "report_date", "market_code", "report_type", "combined", "market_name", "symbol",
    "asset_class",
    # the delivered number and its three factors
    "damage_sell_pct", "damage_buy_pct", "damage_sell", "damage_buy",
    "crowding_long", "crowding_short", "illiquidity_sell", "illiquidity_buy",
    "phi", "phi_pct", "fragility",
    # the levels, because a percentile cannot say a level is trivial (`2026-08-04 §D2`)
    "dtl_sell", "dtl_buy", "q_sell", "q_buy", "open_interest",
    # why a null is null, and what a fall means
    "score_state_sell", "score_state_buy", "unwind_state_sell", "flow_state",
    "d_damage_sell_pct",
    # the caveat carriers that are not in the composite chain
    "beta", "beta_bar", "stratum", "venue",
    # the offside overlay: latest week only
    *TRIGGER_DISTANCE_COLUMNS,
    "pool_net", "pool_category",
)

#: Columns written as pandas nullable `boolean`. A numpy `bool` renders `pd.NA` as `False`,
#: and `False` on `trigger_sell_pool_agrees` means "the pool is on the other side" while
#: `NA` means "nobody checked". `2026-08-04 §D10` is explicit that collapsing those two is a
#: real error, so the dtype has to carry three states.
BOOLEAN_COLUMNS = ("combined", "trigger_sell_pool_agrees", "trigger_buy_pool_agrees",
                   "trigger_horizons_disagree")

#: Weeks of history kept under the output root. Older directories are pruned on publish.
#: History exists so a failed run cannot destroy the last good panel, not as an archive.
DEFAULT_KEEP_WEEKS = 8

#: A publish carrying fewer scored markets than this fraction of the previous run is
#: refused. `bin/live-tests.sh` records a real 2026-08-03 incident where reading the store
#: mid-write made panels momentarily unreadable; a test run fails loudly in that case and a
#: publisher would quietly write a short panel and call it the week's findings.
MIN_MARKET_RATIO = 0.8


class PublishError(RuntimeError):
    """The panel cannot be built, or must not be written."""


@dataclass(frozen=True)
class DamageBuild:
    """One run's output, before it touches a disk."""

    panel: pd.DataFrame
    #: `{market_code: {"block": <damage_block dict>, "markdown": <format_damage_block>}}`,
    #: per side, for `report_date` only. See the module docstring on why this is one week.
    blocks: dict
    report_date: pd.Timestamp
    provenance: dict = field(default_factory=dict)


# ── the chain ───────────────────────────────────────────────────────────────
def annotated_panel(report_type: str) -> pd.DataFrame:
    """The canonical panel with the contract-master columns on it, loaded once.

    Separate from `_scored` because the Amihud panel behind `beta` needs
    `(symbol, point_value)` pairs off the same annotation, and loading the store twice to
    get them is the most expensive avoidable thing in the build.
    """
    return ContractMaster.load().annotate(from_current_store(report_type=report_type))


def _scored(panel: pd.DataFrame, report_type: str, *,
            betas: pd.Series | None = None) -> pd.DataFrame:
    """The full composite for one report type, with every caveat carrier attached.

    This is the chain that `docs/analysis/reproduce_single_number.py` and
    `docs/analysis/reproduce_brief.py` each wrote their own copy of. It lives here now and
    they import it, because three copies of a fourteen-line chain is how two of them end up
    passing different arguments to `add_trigger_distance` without anyone noticing.
    """
    per_category = add_volume(add_extremity(add_risk_units(add_notional(panel))))

    # Volume, sigma and the spec columns are market properties that arrive on the category
    # frame, so lift them back to one row per market-week.
    agg = (per_category.groupby(["report_date", "market_code"])
           .agg(adv=("adv", "max"), adv_stress=("adv_stress", "max"),
                sigma_daily=("sigma_daily", "max"), symbol=("symbol", "first"),
                asset_class=("asset_class", "first"))
           .reset_index())
    per_market = market_fragility(panel).merge(
        agg, on=["report_date", "market_code"], how="left")
    ranked = rank_markets(per_market, volume=per_market["adv"],
                          stress_volume=per_market["adv_stress"])

    if betas is not None and len(betas):
        from .commonality import add_commonality
        ranked = add_commonality(ranked, betas)

    scored = add_composite(ranked, per_category)
    scored = _add_pool_net(scored, panel, report_type)
    scored = add_trigger_distance(scored, pool_column="pool_net")
    scored = add_score_state(scored)
    scored = add_unwind_state(scored, decompose(panel))
    return classify(scored)


def _add_pool_net(scored: pd.DataFrame, panel: pd.DataFrame,
                  report_type: str) -> pd.DataFrame:
    """Attach the observed net of the forceable category, per market-week.

    This is the column that turns `trigger_*_pool_agrees` from null into an answer. The
    category is the same one `composite.CROWDING_CATEGORY` takes `C` from, which is the
    point: the trigger has to describe the pool whose extremity the composite is measuring,
    or the two halves of a reading are about different books.
    """
    category = CROWDING_CATEGORY.get(report_type)
    if category is None:
        out = scored.copy()
        out["pool_net"] = pd.NA
        out["pool_category"] = pd.NA
        return out

    contrib = contributions(panel, report_type=report_type)
    pool = (contrib[contrib["category"] == category]
            .groupby(["report_date", "market_code"], as_index=False)["net"].first()
            .rename(columns={"net": "pool_net"}))
    out = scored.merge(pool, on=["report_date", "market_code"], how="left")
    out["pool_category"] = category
    return out


def _betas(panels: dict[str, pd.DataFrame]) -> pd.Series:
    """§A.6's `beta_i` over the covered universe, or an empty Series when it cannot be formed.

    **This is the one expensive step, and it is on by default deliberately.** README reading
    instruction 4 says `D` assumes exits are independent across markets and measures that
    they are not (milk and hogs near 0.07, the wheats above 1.0), and the composite chain
    never calls `add_commonality`. A panel published without `beta` carries a `D` whose
    fourth reading instruction has no per-row carrier at all.
    """
    frames = [p[["symbol", "point_value"]] for p in panels.values()
              if {"symbol", "point_value"} <= set(p.columns)]
    if not frames:
        return pd.Series(dtype="float64")
    specs = (pd.concat(frames, ignore_index=True).dropna(subset=["symbol", "point_value"])
             .drop_duplicates("symbol"))
    pairs = list(specs.itertuples(index=False, name=None))
    try:
        return commonality_betas(illiquidity_panel(pairs, start="2015-01-01"))
    except (CommonalityError, ValueError):
        # A store that cannot support an Amihud panel yields a panel with a null `beta`
        # column rather than no panel. The null is visible and named; a missing column
        # would fail the reader's contract check for an unrelated reason.
        return pd.Series(dtype="float64")


def build_damage_panel(*, reports=DEFAULT_REPORTS,
                       with_commonality: bool = True) -> DamageBuild:
    """Every report type, concatenated, with the latest week's blocks pre-rendered."""
    panels = {report_type: annotated_panel(report_type) for report_type in reports}
    betas = _betas(panels) if with_commonality else pd.Series(dtype="float64")
    frames = [_scored(panels[rt], rt, betas=betas) for rt in reports]
    panel = pd.concat(frames, ignore_index=True)
    panel["report_date"] = pd.to_datetime(panel["report_date"])

    for column in PANEL_COLUMNS:
        if column not in panel.columns:
            panel[column] = pd.NA
    panel = panel.reindex(columns=list(PANEL_COLUMNS))
    panel = _coerce(panel)

    stamp = panel["report_date"].max()
    if pd.isna(stamp):
        raise PublishError(
            "the panel carries no report_date, so there is no week to publish. Check that "
            f"the store holds {list(reports)} under COTDATA_STORE.")

    return DamageBuild(
        panel=panel.sort_values(["market_code", "report_date"]).reset_index(drop=True),
        blocks=_blocks(panel, stamp),
        report_date=stamp,
        provenance={
            "crowdmon_version": __version__,
            "reports": list(reports),
            "with_commonality": bool(with_commonality and len(betas)),
            "n_betas": int(len(betas)),
        },
    )


def _coerce(panel: pd.DataFrame) -> pd.DataFrame:
    """Pin the dtypes the artifact promises, rather than inheriting the store's.

    `report_type` currently arrives as an Arrow-backed string depending on how cotdata read
    the parquet that week. An artifact whose dtypes track an upstream backend is one whose
    consumer breaks on a day nothing here changed.
    """
    out = panel.copy()
    for column in BOOLEAN_COLUMNS:
        if column in out.columns:
            out[column] = out[column].astype("boolean")
    for column in ("market_code", "report_type", "market_name", "symbol", "asset_class",
                   "score_state_sell", "score_state_buy", "unwind_state_sell",
                   "flow_state", "stratum", "venue", "pool_category"):
        if column in out.columns:
            out[column] = out[column].astype("object").where(out[column].notna(), None)
            out[column] = out[column].map(lambda v: None if v is None else str(v))
    return out


def _blocks(panel: pd.DataFrame, stamp: pd.Timestamp) -> dict:
    """`damage_block` plus its rendered markdown, per market and side, for one week."""
    week = panel[panel["report_date"] == stamp]
    out: dict = {}
    for code in sorted(week["market_code"].dropna().unique()):
        entry: dict = {}
        for side in ("sell", "buy"):
            try:
                block = damage_block(panel, str(code), side=side, report_date=stamp)
            except Exception as exc:                                    # noqa: BLE001
                # One unrenderable market must not cost the other forty-four. The reason
                # travels so a reader sees a named failure rather than an absence.
                entry[side] = {"error": f"{type(exc).__name__}: {exc}"}
                continue
            entry[side] = {
                "block": _jsonable(block),
                "band": damage_band(block.get("damage_pct")),
                "markdown": format_damage_block(block),
            }
        out[str(code)] = entry
    return out


def _jsonable(value):
    """Timestamps, numpy scalars and `pd.NA` into things `json.dump` accepts."""
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


# ── the manifest ────────────────────────────────────────────────────────────
def panel_manifest(build: DamageBuild, *, available=()) -> dict:
    """The reader's only entry point, built from live constants and never hand-written.

    Every vocabulary and every note below is read from the module that owns it. That is the
    difference between an artifact and a fifth copy of a living document: add a sixth reading
    instruction to `brief.READING_INSTRUCTIONS` and the next publish carries it with no edit
    here, while a hand-maintained JSON block would silently not.
    """
    panel = build.panel
    week = panel[panel["report_date"] == build.report_date]
    return {
        "schema_version": SCHEMA_VERSION,
        "current_report_date": build.report_date.date().isoformat(),
        "available_report_dates": sorted(available),
        # `built_at` is stamped HERE rather than in `build_damage_panel`, so that it exists
        # on every manifest however the `DamageBuild` was assembled. It answers a question
        # `current_report_date` cannot: COT is weekly, so a schedule that quietly stopped
        # produces no new report week to notice, and a panel can be current on the week and
        # months old on the clock. The consumer reads it with `.get()`, which means its
        # absence degrades SILENTLY to a provenance line one field shorter. It went missing
        # exactly that way once: it lived only in a worktree, was never committed, and the
        # merged publisher shipped without it while the page kept rendering.
        "provenance": {
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **build.provenance,
        },
        "counts": {
            "markets": int(week["market_code"].nunique()),
            "rows": int(len(panel)),
            "scored_sell": int((week["score_state_sell"] == "scored").sum()),
            "scored_buy": int((week["score_state_buy"] == "scored").sum()),
            "trigger_sell": int(week["trigger_sell_sigma"].notna().sum()),
            "trigger_buy": int(week["trigger_buy_sigma"].notna().sum()),
        },
        "vocabulary": {
            "score_states": list(SCORE_STATES),
            "unwind_states": list(UNWIND_STATES),
            "flow_states": list(FLOW_STATES),
            "strata": list(STRATA),
        },
        "factor_questions": dict(FACTOR_QUESTIONS),
        "column_definitions": dict(COLUMN_DEFINITIONS),
        "damage_bands": [[float(floor), label] for floor, label in DAMAGE_BANDS],
        "quadrant": {f"{int(close)}{int(severe)}": text
                     for (close, severe), text in QUADRANT.items()},
        "close_sigma": float(CLOSE_SIGMA),
        "notes": {
            "score_state": dict(brief_mod.SCORE_STATE_NOTES),
            "unwind_state": dict(brief_mod.UNWIND_NOTES),
            "no_delta": brief_mod.NO_DELTA_NOTE,
            "band_advice": dict(BAND_ADVICE),
        },
        "reading_instructions": [asdict(c) for c in brief_mod.READING_INSTRUCTIONS],
        "standing": list(STANDING),
        "columns": list(PANEL_COLUMNS),
    }


#: What a reader must be told on every render, in the artifact rather than in the consumer's
#: prose. These are the statements that are true of the whole panel and therefore cannot be
#: a per-row column; the per-row ones are already columns.
STANDING = (
    "D describes the shape of a conditional loss distribution, not its location. It "
    "informs tail risk, expected shortfall and gap risk. It is not a forecast of return "
    "and must never be traded directly (appendix A.10).",
    "D is a product of three percentiles, so it is dominated by its smallest term. Read "
    "C, I and Phi beside it or a middling D_pct on a record I looks like a broken measure.",
    "Phi's effect on D_pct is NOT monotone. A below-median Phi moved corn up and sterling "
    "down in the same week, because the percentile of a product is not monotone in each "
    "factor's percentile. 'More fragile means more damage' is not a sentence anyone may "
    "write (2026-08-04 D6).",
    "D_pct is a rank among this market's own past weeks. It is not a probability and it "
    "is not comparable as a level to another market's.",
    "The offside distance is a moving level, not a countdown. The reference bar F_(t-k) "
    "moves 1.68x as much as spot, so most of the variation in distance-to-trigger is last "
    "year's bars rolling off rather than price approaching anything (2026-08-04 D12).",
    "T_side covers every category on that side weighted by forceability; the trigger "
    "fires only the trend-following slice of the levered pool. Quoted together they "
    "describe two different populations (2026-08-04 D12).",
    "Q_sell and Q_buy are never added. Forced longs sell and forced shorts buy; their sum "
    "describes an event that cannot happen.",
)


# ── writing ─────────────────────────────────────────────────────────────────
def store_root(explicit: str | os.PathLike | None = None) -> pathlib.Path:
    """The output root, from an argument or `CROWDMON_STORE`. Raises when neither is set."""
    if explicit:
        return pathlib.Path(explicit).expanduser()
    value = os.environ.get(STORE_ENV)
    if not value:
        raise PublishError(
            f"{STORE_ENV} is unset. It names where the damage panel is written, and it is "
            f"deliberately a different store from COTDATA_STORE: this is a consumer's "
            f"output, not the producer's data. Set it, or pass --out. "
            f"bin/publish_damage.sh defaults it to ~/code/crowdmon_store because launchd "
            f"reads no shell profile.")
    return pathlib.Path(value).expanduser()


def publish_panel(build: DamageBuild, root: str | os.PathLike | None = None, *,
            keep_weeks: int = DEFAULT_KEEP_WEEKS) -> pathlib.Path:
    """Write one dated directory and repoint the manifest at it, atomically.

    Order is the guarantee: everything lands in a temp directory, `os.replace` moves it into
    place, and `manifest.json` is rewritten last. A reader that finds a manifest naming a
    directory which is not there has caught a partial sync and can say so, which is why
    there is no `latest` symlink to be half-copied instead.
    """
    base = store_root(root) / "damage"
    base.mkdir(parents=True, exist_ok=True)
    stamp = build.report_date.date().isoformat()

    _refuse_a_short_panel(build, base)

    staging = pathlib.Path(tempfile.mkdtemp(prefix=f".{stamp}.", dir=base))
    try:
        build.panel.to_parquet(staging / "panel.parquet", index=False,
                               compression="snappy")
        # Sanitised HERE and not only in `_blocks`, because this is the last line before
        # the disk. A `Timestamp` reaching `json.dumps` raises after the whole panel has
        # been computed, so the cheap defensive pass costs milliseconds and the alternative
        # costs the week.
        (staging / "blocks.json").write_text(
            json.dumps(_jsonable(build.blocks), indent=1, sort_keys=True),
            encoding="utf-8")
        (staging / "meta.json").write_text(
            json.dumps({"schema_version": SCHEMA_VERSION, "report_date": stamp,
                        **build.provenance}, indent=1, sort_keys=True), encoding="utf-8")
        target = base / stamp
        if target.exists():
            shutil.rmtree(target)
        os.replace(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    available = _weeks(base)
    for old in available[:-keep_weeks] if keep_weeks else []:
        shutil.rmtree(base / old, ignore_errors=True)
    available = _weeks(base)

    (base / "manifest.json").write_text(
        json.dumps(panel_manifest(build, available=available), indent=1, sort_keys=True),
        encoding="utf-8")
    return base / stamp


def _weeks(base: pathlib.Path) -> list[str]:
    """The dated directories present, oldest first. Derived, never cached in the manifest
    from a previous run: the manifest is rewritten from the directory every publish."""
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


def _refuse_a_short_panel(build: DamageBuild, base: pathlib.Path) -> None:
    """Refuse a run that scored materially fewer markets than the last one.

    A publisher is not a test suite: a run that reads the store mid-write produces a short
    panel rather than an error, and a short panel published on schedule becomes "this week's
    findings" with nothing to say it is wrong. `bin/live-tests.sh` documents the observed
    incident this guards against.
    """
    previous = base / "manifest.json"
    if not previous.exists():
        return
    try:
        was = int(json.loads(previous.read_text(encoding="utf-8"))["counts"]["markets"])
    except (ValueError, KeyError, TypeError):
        return
    week = build.panel[build.panel["report_date"] == build.report_date]
    now = int(week["market_code"].nunique())
    if was and now < was * MIN_MARKET_RATIO:
        raise PublishError(
            f"this run carries {now} markets against {was} in the previous publish, below "
            f"the {MIN_MARKET_RATIO:.0%} floor. That is the shape of a store read while it "
            f"was being written (see bin/live-tests.sh). Check the store's mtimes against "
            f"this run before overriding; publishing would replace a good panel with a "
            f"short one and nothing downstream would say so.")
