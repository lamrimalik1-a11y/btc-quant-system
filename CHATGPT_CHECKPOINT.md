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
