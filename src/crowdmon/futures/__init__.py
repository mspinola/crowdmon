"""The COT-specific monitor: ingestion, normalisation, and the positioning engines.

Everything here knows about CFTC reporting categories, market codes and open interest, and
none of it would serve the equity monitor unchanged. That is the line between this package
and `crowdmon.core`.

`flow` and `fragility` need no prices, no contract master and no normalisation: every input
is a column the canonical schema already carries. That is deliberate and it is what makes
them the right first consumers of that schema — a failure in either one is a schema failure
and cannot be anything else. `pressure` is the exception and says so: its full form needs a
volume this workspace has no source for, so it returns the OI-denominated ranking now and
`None` where the real figure belongs.

Two data-loading modules rather than the one the handoff sketches, because they answer
different questions and only the first is about lookahead:

- `cot_adapter` — the `CotSource` seam. "What was knowable on date *t*", with release-date
  indexing and provenance filtering. Layer 1.
- `io` — the flat panels the engines consume, plus the open-interest identity as a reported
  rate. The handoff's §2.

**The load-bearing fact across the normalisation half** (`contract_master`, `notional`,
`riskunits`) is that the two factors of `net_notional x sigma` come from DIFFERENT price
series, on purpose, and each module refuses the other's:

- **notional wants `unadj`**, because only raw front-month prices are tradeable price
  LEVELS. Its error is +294% for gold in 2002 and **exactly zero today**, growing
  monotonically backwards, so no spot check on recent data catches it.
- **riskunits wants `propadj`**, because only ratio adjustment preserves percentage
  RETURNS. `backadj` inflates annualised vol by 201x for soybeans and 182x for the 10-year
  note, and *understates* gold by half while never going negative, so no implausibility
  screen catches that one either.

An earlier version of this paragraph said volatility wanted `backadj`. That was wrong:
additive back-adjustment preserves absolute price CHANGES, not percentage returns, and it
drives 52.3% of soybean closes and 41.2% of Class III Milk closes to or below zero, where a
percentage return is undefined. Module spec §5.1 had it right all along ("ratio-adjusted
(not difference-adjusted) so returns are correct"). Measured in
`docs/design/amendments-2026-08-01.md`, asserted in `tests/test_riskunits_live.py`.

Both modules refuse rather than document, because both errors are invisible to the check a
reasonable person would actually run. That asymmetry is also why `riskunits` belongs here
beside `notional` rather than in `crowdmon.core`: it is a fact about futures
continuous-contract construction, not a general one.
"""
from .alignment import (
    ALIGNMENT_COLUMNS,
    DEFAULT_METHOD,
    DEFAULT_MIN_MARKETS,
    AlignmentError,
    alignment_series,
    blend_sensitivity,
    blended_tsmom,
    format_alignment_block,
    max_attainable,
    momentum_panel,
)
from .breadth import decompose_breadth
from .clustering import (
    DEFAULT_MIN_OBS,
    DISTANCES,
    LINKAGES,
    ClusteringError,
    agglomerate,
    cluster_sweep,
    clusters_at,
    correlation_distance,
    cross_class_pairs,
    format_cluster_block,
    return_panel,
)
from .commonality import (
    COMMONALITY_COLUMNS,
    DEFAULT_GAMMA,
    CommonalityError,
    add_commonality,
    commonality_betas,
    gamma_sensitivity,
    illiquidity_panel,
    rolling_betas,
    t_effective,
)
from .composite import (
    COMPOSITE_COLUMNS,
    SCORE_STATES,
    UNWIND_STATES,
    CompositeError,
    add_composite,
    add_score_state,
    add_unwind_state,
    damage_report,
    top_damage,
)
from .concentration import (
    CONCENTRATION_COLUMNS,
    ConcentrationError,
    add_concentration_extremity,
    concentration_vs_fragility,
    market_concentration,
    quadrant,
)
from .continuity import (
    CONTINUITY_COLUMNS,
    DEFAULT_TOLERANCE_DAYS,
    ContinuityError,
    continuity,
    format_continuity,
    migrations,
    unexplained_gaps,
)
from .contract_master import (
    CONTRACT_COUNT_COLUMNS,
    SPEC_COLUMNS,
    ContractMaster,
    ContractMasterError,
    ContractSpec,
)
from .cot_adapter import (
    PROVENANCE_ORDER,
    RECORDED_SOURCES,
    CotAdapterError,
    CotSource,
    VintageCotSource,
    provenance_summary,
)
from .coverage import (
    LADDER,
    TERMINAL_RUNG,
    CoverageError,
    coverage_ladder,
    coverage_summary,
    format_coverage,
    unscoreable,
)
from .extremity import (
    EXTREMITY_COLUMNS,
    ExtremityError,
    add_extremity,
    extremity_report,
    latest_extremes,
)
from .flow import FLOW_STATES, decompose, state_distribution, tolerance_sensitivity
from .fragility import (
    SHAPE_KEYS,
    contributions,
    fragility_frame,
    market_fragility,
    shape_labels,
)
from .impact import (
    DEFAULT_AMIHUD_WINDOW,
    IMPACT_COLUMNS,
    add_impact,
    amihud_series,
    impact_coverage,
)
from .io import (
    PanelError,
    from_current_store,
    from_vintage,
    latest,
    oi_identity,
    oi_identity_summary,
)
from .macro_pca import (
    BOOK_CATEGORY,
    DEFAULT_MAX_CONCURRENT_SHARE,
    MACRO_PCA_COLUMNS,
    PANEL_INPUT,
    RISK_PANEL_INPUT,
    MacroPcaError,
    absorption_ratio,
    format_absorption,
    loading_rotation,
    merge_migrated_codes,
    positioning_panel,
    rolling_absorption,
    select_markets,
    shuffled_null,
    window_sensitivity,
)
from .macro_pca import (
    DEFAULT_WINDOW as PCA_DEFAULT_WINDOW,
)
from .notional import (
    DEFAULT_MAX_STALENESS_DAYS,
    NOTIONAL_ADJUSTMENT,
    NOTIONAL_COLUMNS,
    NotionalError,
    add_notional,
    coverage_report,
)
from .pressure import exit_pressure, rank_markets, top_by
from .reflexivity import (
    DEFAULT_TREND_FRACTION,
    LG_CEILING,
    STAIRCASE_COLUMNS,
    ReflexivityError,
    bracket,
    effective_lambda,
    headline,
    implied_gross_pool,
    staircase,
)

# Aliased rather than shadowing trigger's `format_block`, the same way riskunits'
# `coverage_report` is aliased below. The two render different blocks and a caller silently
# getting the wrong one would print a cascade where they asked for a trigger.
from .reflexivity import format_block as format_cascade_block
from .riskunits import (
    DEFAULT_MIN_PERIODS,
    DEFAULT_VOL_WINDOW,
    RISK_ADJUSTMENT,
    RISK_COLUMNS,
    RiskUnitsError,
    add_risk_units,
    sigma_series,
)
from .riskunits import coverage_report as risk_coverage_report
from .roll import (
    DEFAULT_WINDOW_BARS,
    MIN_EXCLUDED_SHARE,
    ROLL_COLUMNS,
    RollError,
    exit_collision,
    format_roll_block,
    in_roll_window,
    roll_adjusted_adv,
    roll_calendar,
    roll_window_stats,
)
from .seasonal import (
    DEFAULT_MIN_YEARS,
    SeasonalError,
    deseasonalise,
    seasonal_profile,
    seasonality_report,
    week_of_year,
)
from .trigger import (
    DEFAULT_LOOKBACKS,
    TriggerError,
    format_block,
    trigger_block,
    trigger_prices,
    vol_shock_reduction,
)
from .volume import (
    DEFAULT_ADV_WINDOW,
    DEFAULT_STRESS_LOOKBACK,
    STRESS_DECILE,
    VOLUME_COLUMNS,
    VOLUME_SERIES,
    VolumeError,
    add_volume,
    adv_series,
    stress_adv_series,
    volume_coverage,
)
from .weight_sensitivity import (
    REFERENCE_WEIGHTINGS,
    SensitivityError,
    flat_phi_identity,
    plausible_variants,
    reference_variants,
    single_weight_sweep,
    summarise,
    sweep,
)

__all__ = [
    # ingestion
    "CotSource", "VintageCotSource", "CotAdapterError", "PROVENANCE_ORDER",
    "RECORDED_SOURCES", "provenance_summary",
    "PanelError", "from_vintage", "latest", "from_current_store",
    "oi_identity", "oi_identity_summary",
    # normalisation
    "ContractMaster", "ContractSpec", "ContractMasterError", "SPEC_COLUMNS",
    "CONTRACT_COUNT_COLUMNS",
    "add_notional", "coverage_report", "NotionalError", "NOTIONAL_COLUMNS",
    "NOTIONAL_ADJUSTMENT", "DEFAULT_MAX_STALENESS_DAYS",
    # `coverage_report` above is notional's and keeps the bare name it shipped with.
    # riskunits' is aliased rather than shadowing it: the two answer different questions
    # (no price vs no volatility) and a caller silently getting the wrong one would read a
    # full panel as complete.
    "add_risk_units", "risk_coverage_report", "RiskUnitsError", "RISK_COLUMNS",
    "RISK_ADJUSTMENT", "DEFAULT_VOL_WINDOW", "DEFAULT_MIN_PERIODS",
    # engines
    "trigger_prices", "trigger_block", "format_block", "vol_shock_reduction",
    "TriggerError", "DEFAULT_LOOKBACKS",
    "staircase", "bracket", "headline", "implied_gross_pool", "effective_lambda",
    "format_cascade_block", "ReflexivityError", "STAIRCASE_COLUMNS",
    "DEFAULT_TREND_FRACTION", "LG_CEILING",
    "roll_calendar", "in_roll_window", "roll_window_stats", "roll_adjusted_adv",
    "exit_collision", "format_roll_block", "RollError", "ROLL_COLUMNS",
    "DEFAULT_WINDOW_BARS", "MIN_EXCLUDED_SHARE",
    "return_panel", "correlation_distance", "agglomerate", "clusters_at",
    "cross_class_pairs", "cluster_sweep", "format_cluster_block", "ClusteringError",
    "DISTANCES", "LINKAGES", "DEFAULT_MIN_OBS",
    "blended_tsmom", "momentum_panel", "alignment_series", "max_attainable",
    "blend_sensitivity", "format_alignment_block", "AlignmentError",
    "ALIGNMENT_COLUMNS", "DEFAULT_MIN_MARKETS", "DEFAULT_METHOD",
    "seasonal_profile", "deseasonalise", "seasonality_report", "week_of_year",
    "SeasonalError", "DEFAULT_MIN_YEARS",
    "plausible_variants", "reference_variants", "sweep", "single_weight_sweep", "summarise",
    "flat_phi_identity", "SensitivityError", "REFERENCE_WEIGHTINGS",
    "market_concentration", "add_concentration_extremity",
    "concentration_vs_fragility", "quadrant", "ConcentrationError",
    "CONCENTRATION_COLUMNS",
    "add_composite", "damage_report", "top_damage", "CompositeError",
    "COMPOSITE_COLUMNS",
    # the two per-row caveat carriers, here rather than in the report layer because
    # `composite` owns `D` and a derivation in a rendering is how the next engine gets
    # built by accident. `add_score_state` is the one caveat no other output states.
    "add_score_state", "add_unwind_state", "SCORE_STATES", "UNWIND_STATES",
    "add_extremity", "extremity_report", "latest_extremes", "ExtremityError",
    "EXTREMITY_COLUMNS",
    "decompose", "state_distribution", "tolerance_sensitivity", "FLOW_STATES",
    "market_fragility", "fragility_frame", "contributions",
    "shape_labels", "SHAPE_KEYS",
    "decompose_breadth",
    "exit_pressure", "rank_markets", "top_by",
    # exit COST, distinct from exit duration. A.9's composite term is pct(T_eff), which is
    # `T`; this is A.5's square-root law and is reported beside it, not inside D.
    # A.6 commonality. NOT wired into the composite: with a constant beta_bar, pct(T_eff)
    # is bit-identical to pct(T), so wiring it is a decision about what A.9's I should be.
    "illiquidity_panel", "commonality_betas", "rolling_betas", "t_effective",
    "add_commonality", "gamma_sensitivity", "CommonalityError", "COMMONALITY_COLUMNS",
    "DEFAULT_GAMMA",
    "add_impact", "amihud_series", "impact_coverage", "IMPACT_COLUMNS",
    "DEFAULT_AMIHUD_WINDOW", "sigma_series",
    # the denominator of T = Q/(kappa V). `VOLUME_SERIES` is "front" and is WHOLE-MARKET;
    # the series named "reconstructed" is the narrower one. volume.py has the measurements.
    "add_volume", "adv_series", "stress_adv_series", "volume_coverage", "VolumeError",
    "VOLUME_COLUMNS", "VOLUME_SERIES", "DEFAULT_ADV_WINDOW", "DEFAULT_STRESS_LOOKBACK",
    "STRESS_DECILE",
    # Which markets can be scored AT ALL, and where the ones that cannot drop out. The rung
    # helpers above each answer one join; this answers the whole chain, keyed on market_code
    # because 11 of 27 codes carry more than one name and grouping on the name invents four
    # unscoreable markets that do not exist. See coverage.py.
    "coverage_ladder", "unscoreable", "coverage_summary", "format_coverage",
    "CoverageError", "LADDER", "TERMINAL_RUNG",
    # §7's macro-book PCA: PC1's share of variance in positioning CHANGES, the futures
    # absorption ratio. NOT a PCA over commonality's illiquidity panel, which is the nearer
    # object and a different quantity. Reaches 2008; `D` starts 2010-05-25.
    "positioning_panel", "select_markets", "absorption_ratio", "rolling_absorption",
    "loading_rotation", "shuffled_null", "window_sensitivity", "format_absorption",
    "MacroPcaError", "MACRO_PCA_COLUMNS", "PANEL_INPUT", "RISK_PANEL_INPUT", "BOOK_CATEGORY",
    "PCA_DEFAULT_WINDOW",
    # A market split across two codes by a venue migration is dropped TWICE by
    # `select_markets`, which maximises complete weeks and only sees a matrix. Merging is
    # opt-in because it changes which markets the PCA runs over, and it happens on LEVELS
    # before the difference or the old code's final position vanishes into a NaN.
    "merge_migrated_codes", "DEFAULT_MAX_CONCURRENT_SHARE",
    # One layer under coverage: a market_code is not an instrument, and a code's series can
    # have a hole in the middle. Either makes a long-lived market look young, which is what
    # every stacked window here refuses to score. Keyed on SYMBOL, deliberately the opposite
    # of coverage's key, because the question is which codes serve one instrument. A hole is
    # not always a migration: `gap_filled_by` separates a venue seam (RTY) from a market that
    # genuinely stopped reporting (oats, Nikkei). See continuity.py.
    "continuity", "migrations", "unexplained_gaps", "format_continuity",
    "ContinuityError", "CONTINUITY_COLUMNS", "DEFAULT_TOLERANCE_DAYS",
]
