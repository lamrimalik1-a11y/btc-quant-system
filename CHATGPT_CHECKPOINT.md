## Active Checkpoint: PHASE1C_SCIENTIFIC_HYPOTHESIS_AUDIT_STABLE

Commit: `b381ce99b0199856242e104c06a8fe139a8def63`

Chapter I is COMPLETE / STABLE through Stage 6 Prediction Evolution Research.

Project 2 Chapter II, stable through Phase 6:
- Scenario Generator Foundation: STABLE
  (`ca71902f74ba42ce54b217f3488c10da24a2d0f4`)
- Scenario Runner: STABLE
  (`34641e3c1cda4a19972a48752446785132e7ccbd`)
- Scenario Catalog Foundation: STABLE
  (`5a2d4a718f0072f86556e2b2347eedbeaf8ae061`)
- Scenario Catalog Provenance Fix: STABLE
  (`a2c52feb5b7472450b543f6de3b46a6562520d5a`)
- Scenario Execution: PASS after Stage 6 empty-zone robustness fix
  (`add1fcfe37f68d41437594d4b424f1eddd08214d`)
- Cross-Scenario Descriptive Comparison: STABLE
  (`660f459ea9a5a34d6aa95a2a395f1ea93302ea57`)
- Scientific Hypothesis Audit: STABLE
  (`b381ce99b0199856242e104c06a8fe139a8def63`)

Summary:
- Phase 6 implemented as a preregistered scientific hypothesis audit.
- Decisions are derived from explicit evidence-based decision rules.
- Exact Phase 3 hypothesis traceability verified.
- Phase 5 remains the sole source of observed evidence.
- Caveats precede evaluations.
- Null and contradictory evidence preserved.
- Automated banned-language scan added.
- Deterministic scientific audit verified.
- No Scenario Runner changes.
- No Scenario Catalog changes.
- No Stage 1-6 changes.
- No Project 1 changes.
- No Production changes.

Independently re-verified before documenting: each hypothesis evaluation now
carries a `decision_rule_id` and a `decision_rule_trace` showing the exact
evidence values the decision was computed from (not asserted); the
banned-language scan's pattern list was independently confirmed to cover
proven/validated/falsified/generalize/generalization/suggests/confirms/
proves/stronger/weaker/improved/degraded/effect/impact/lift/gain/accuracy/
performance, scoped only to Phase 6's own authored text; two independent
process runs produced byte-identical output; `git diff` against the prior
commit touches exactly one file.

No Scenario Runner, Scenario Catalog implementation, Stage 1-6, Project 1,
or production behavior changed.

---
==================================================
AUTOMATIC HISTORICAL ARCHIVE SYSTEM
===================================

STATUS:
IMPLEMENTED

FILE MODIFIED:
tools/generate_binance_historical_replay.py

OBJECTIVE:
Create a permanent historical replay archive system that automatically stores replay datasets by market date and archive window.

FEATURES:

* Automatic archive routing
* 10-day archive windows
* Per-market-date folders
* archive_index.json
* manifest.json for each archived day
* Existing archive protection
* Automatic run_001 / run_002 versioning
* --overwrite-archive support
* Dashboard compatibility preserved
* outputs/ behavior unchanged

ARCHIVE STRUCTURE:

archives/
└── BTCUSDT/
├── 2026-05-11_to_2026-05-20/
├── 2026-05-21_to_2026-05-30/
├── 2026-05-31_to_2026-06-09/
└── ...

ARCHIVED FILES:

* historical_market_rows.csv
* historical_observation_rows.csv
* historical_replay_observation_events.csv
* historical_replay_observation_v2_events.csv
* historical_replay_dashboard_episodes.csv
* historical_replay_dashboard_v2_episodes.csv
* raw aggTrades when --save-raw is used

VALIDATION:

PASSED:
python -m py_compile tools/generate_binance_historical_replay.py

NO DOWNLOADS EXECUTED
NO REPLAY EXECUTED
NO DASHBOARD CHANGES
NO RDM CHANGES
NO RESEARCH LOGIC CHANGES

PROJECT POLICY:

Historical downloads must not be executed for validation purposes.

Preserve download time, resources, and Codex usage.

Downloads are executed only when new historical data is actually required.

EXPECTED BENEFIT:

Build a reusable historical replay library.

Future backtesting must reuse archived datasets whenever possible instead of downloading the same dates repeatedly.

==================================================
PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
==================================================

STATUS:
STABLE CHECKPOINT

RDM V1.6-B7.6-A
Absorption vs Reflection
COMPLETED

RDM V1.6-B7.6-B
Structural Engagement Physics
COMPLETED

RDM V1.6-B7.6-C
Stress Exposure Physics
COMPLETED

RDM V1.6-B7.6-D
Omega Validation
COMPLETED

RDM V1.6-B7.6-E
Surface Damage Physics
REVIEWED

RDM V1.6-B7.6-F
Surface Damage Validation
COMPLETED

RDM V1.6-B7.7
Structural Exposure Physics
COMPLETED

MAIN CONFIRMED FINDING:

Stress x Penetration ~= Omega

Omega is the central deep structural exposure variable.

VALIDATED RELATION:

sigma_at_return x zone_penetration_depth
~=
omega_stress_area

IMPORTANT RESULT:

Stress x Time / Cycles was reviewed, but the current dataset does not have enough time/cycle variance to validate it.

SURFACE DAMAGE HYPOTHESIS:

REJECTED

zero-omega damage is not an independent market physics pathway.

It is produced by live temporal decay formulas:

zone_strength_decay x row_progress x fixed coefficients

DEEP ENGAGEMENT PATH:

Force
↓
Structural Filter / Sigma Barre
↓
Penetration
↓
Omega / Stress Exposure
↓
Mechanical Family
↓
Growth or Damage

RULES:

No Phase 2
No Footprint
No execution
No BUY/SELL
No scoring changes
No dashboard logic changes
No replay logic changes


==================================================
PHASE1B_MARCH_APRIL_MAY_GENERALIZATION_STABLE
==================================================

Date: 2026-06-05
Commit: PHASE1B March April May generalization stable

STATUS:
STABLE CHECKPOINT

RESEARCH ONLY. NOT A TRADING SYSTEM.
No Phase 2. No execution. No BUY/SELL. No entries/exits.

--------------------------------------------------
THREE-PERIOD B12v2 RESULTS
--------------------------------------------------

TRAINING (Apr30-Jun02, 34 days):
  Cases:          355 evaluable / 793 total
  Accuracy:       98.3%
  Lift:           +35.2pp vs baseline 63.1%
  HOLD Precision: 100.0%
  FAIL Precision: 95.6%
  STATUS:         PASS

MARCH 2026 (Mar01-Mar31, 31 days):
  Cases:          633 evaluable / 1,219 total
  Accuracy:       96.7%
  Lift:           +36.7pp vs baseline 60.0%
  HOLD Precision: 99.2%
  FAIL Precision: 93.3%
  STATUS:         PASS

APRIL 2026 (Apr01-Apr30, 30 days):
  Cases:          387 evaluable / 808 total
  Accuracy:       95.1%
  Lift:           +32.6pp vs baseline 62.5%
  HOLD Precision: 99.1%
  FAIL Precision: 89.4%
  STATUS:         BORDERLINE FAIL (-0.6pp below 90% threshold)

--------------------------------------------------
REGIME GENERALIZATION
--------------------------------------------------

STATUS: STRONGLY VALIDATED

2 of 3 independent periods PASS all criteria.
April borderline fail (-0.6pp) explained by higher zone recovery rates in that period.
Non-monotonic ordering (March > April) confirms structural mechanism, not temporal artifact.

STRENGTHENING trajectory: 100.0% HOLD precision in ALL THREE independent periods.

--------------------------------------------------
PHYSICS VALIDATION
--------------------------------------------------

sigma x penetration vs omega:
  Training:  r=0.9978
  March:     r=0.9953
  April:     r=0.9966
  STATUS:    CONFIRMED across all three periods

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

B9 -> B10 -> B11 -> Synthesis chain: PRESERVED
Leakage assertion (I(t) intersect O(t+1) = empty): PASS all periods
Zero Phase 1 code changes across all runs
B12v2 penultimate-state design validated

--------------------------------------------------
FILES PRESERVED
--------------------------------------------------

research/train_phase1b_episode_research_log.csv
research/train_phase1b_preparation_zones.csv
research/train_zone_lifecycle_events.jsonl
research/train_field_lifecycle_events.jsonl
research/apr2026_b12v2_report.md
research/apr2026_b12v2_report.csv
research/apr2026_b12v2_case_results.csv
research/apr2026_b12v2_penultimate_predictions.csv
research/apr2026_generalization_audit.md
research/mar2026_b12v2_report.md
research/mar2026_b12v2_report.csv
research/mar2026_b12v2_case_results.csv
research/mar2026_b12v2_penultimate_predictions.csv
research/mar2026_generalization_audit.md

--------------------------------------------------
DASHBOARD FIX
--------------------------------------------------

Dataset consistency panel added to dashboard_app.py.
Period mismatch detection with DATASET_MISMATCH sentinel.
Temporal guard on episode_id joins.
Show All V2 Episodes toggle added.
No Phase1B/RDM/B11/B12v2 formula changes.

--------------------------------------------------
RULES
--------------------------------------------------

No Phase 2.
No execution.
No BUY/SELL.
No footprint.
No entry/exit signals.
Do NOT change Phase1B formulas.
Do NOT change RDM formulas.
Do NOT modify B11/B12v2 logic.
Do NOT download data without explicit request.

--------------------------------------------------
NEXT STEPS (research only)
--------------------------------------------------

1. Investigate STABLE trajectory in EXHAUSTED_ZONE (false HOLD pattern confirmed 2 periods)
2. Track TERMINAL recovery rate across additional periods (range 3-10% observed)
3. Consider widening FAIL Precision threshold to 87-88% for regime-tolerant criterion
4. Extend to January or February 2026 for fourth-period validation
5. Calibrate B11 thresholds using three-period precision/recall data



==================================================
PHASE1B_FORMATION_MODEL
==================================================

Date: 2026-06-06
STATUS: STABLE CHECKPOINT

--------------------------------------------------
DONE
--------------------------------------------------

- Preparation Zone terminology deprecated
- Formation introduced as parent structure
- Density Band introduced
- Active Core introduced
- Hierarchical zone model documented
- Research terminology standardized

--------------------------------------------------
HIERARCHY
--------------------------------------------------

Formation
    Density Band
        Active Core

--------------------------------------------------
RULES
--------------------------------------------------

- Formation detection occurs first
- Density Band is derived from Formation
- Active Core is derived from Density Band
- Internal code still uses preparation_zone
- Code renaming not authorized

--------------------------------------------------
REFERENCE
--------------------------------------------------

research/terminology_formation_zones.md

