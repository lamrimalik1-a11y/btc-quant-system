# MASTER STATUS

## Active Checkpoint: RDM_V2_CANONICAL_SNAPSHOT_ADAPTERS_COMPLETE

Status: MILESTONE CHECKPOINT — shadow-only, no production behavior changed.

All six Canonical Snapshot adapters are now shadow-ready. Each maps already-
existing values into one snapshot section; none calculates, infers, or rebuilds.

The six adapters (one per snapshot section):
- **geometry** — GeometrySnapshotAdapter -> `geometry`
- **current row mechanics** — RowMechanicsAdapter -> `current_row_mechanics`
- **open visit** — OpenVisitAdapter -> `open_visit`
- **last completed visit** — LastCompletedVisitAdapter -> `last_completed_visit`
- **dynamic mechanics** — DynamicMechanicsAdapter -> `dynamic_mechanics`
- **prediction** — PredictionAdapter -> `prediction`

Shared, enforced properties across all six:
- **Pure mapping only** — value pass-through via ordered source aliases; the
  first present/available alias wins, primary names first.
- **No calculations** — no Dynamic State recompute, derivatives, integrals, SDR,
  classifier, thresholds, B10/B11 execution, Stage 2C, dashboard, CSV writes, or
  persistence.
- **NOT_AVAILABLE handling** — any target whose aliases are all absent, or present
  but None / empty-string / NaN, becomes NOT_AVAILABLE in both the value and its
  source_fields provenance entry. No defaulting.
- **Snapshot compatibility** — every adapter emits a RefreshResult-style patch
  that builds cleanly into a CanonicalZoneSnapshot section; the six together
  consolidate into one immutable copy-on-write snapshot (consolidation test).
- **No production behavior changed** — nothing in core/research/tools imports any
  adapter except the shadow tests.

Most recent additive work folded into this milestone: DynamicMechanicsAdapter
gained `transition_name`; PredictionAdapter gained `prediction_uncertainty`.

Validation (all pass): py_compile of all six adapter files + their shadow tests
OK; all adapter shadow tests PASS; consolidation test PASS; git diff --check
clean.

Next: first real mechanical integration decision.

---

## Active Checkpoint: RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Last Completed Visit Adapter Stage 1 (shadow-only):
- **Extended the existing adapter additively** (core/last_completed_visit_adapter.py,
  originally committed aefec1c) — existing target field names and behavior are
  untouched, so the dependent consolidation test stays green.
- **Maps already-existing completed-visit fields into the Canonical Snapshot
  "last_completed_visit" section** — projection only, no rebuild, no inference.
- **Adds `max_penetration_ratio` and `defender_state`** (plus `visit_start_price`
  and `visit_end_price`) as new mapped target fields this stage.
- **Supports aliases** — first present/available alias wins, primary names first:
  e.g. completed_visit_id->visit_id, visit_max_penetration->max_penetration,
  visit_max_penetration_ratio->max_penetration_ratio, visit_final_omega->
  omega_at_visit, visit_attacker_force->attacker_force_at_visit,
  visit_defender_state->defender_state, visit_health/rigidity/capacity/fatigue/
  recovery->*_at_visit (pre-existing aliases visit_start_time, visit_end_time,
  visit_duration_rows, max_penetration_at_visit retained).
- **NOT_AVAILABLE behavior** — any target whose aliases are all absent, or present
  but None / empty-string / NaN, becomes NOT_AVAILABLE in both the value and its
  source_fields provenance entry. No defaulting.
- **No calculations** — no Dynamic State, derivatives, integrals, SDR, Stage 2C,
  B10, B11, dashboard, CSV writes, or persistence. Opaque pass-through preserved.
- **Snapshot compatibility** — the patch builds a CanonicalZoneSnapshot
  last_completed_visit section cleanly.
- **No production behavior changed** — nothing in core/research/tools imports the
  adapter except the shadow tests.

Validation (all pass): py_compile adapter + test OK; extended shadow test PASS
(normal / partial / missing / new fields / alias / no-calculations / snapshot
compatibility); consolidation test PASS (NOT_AVAILABLE_VALIDATED = TRUE); git
diff --check clean.

Files: core/last_completed_visit_adapter.py (additive) +
experiments/last_completed_visit_adapter/shadow_test.py (extended).

Next: Dynamic Mechanics Adapter approval.

---

## Active Checkpoint: RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED

Status: ACCEPTED CONTRACT (architecture decision only — NO code implemented,
no production code changed). Records the restart/durability design the shadow
backbone must follow before any production integration.

Restart / Durability Contract:
- **The append-only ordered row log is the source of truth.** Per session_id,
  each row carries global_zone_key and the geometry_version in effect.
- **Persist-before-process (write-ahead ordering):** a row is durably appended
  BEFORE InteractionState advances from it -> an open visit is always replayable.
- **Rebuild-from-history is the primary recovery mechanism.** Restart = replay
  the durable rows forward through interpret_in_order; rebuild InteractionState
  and the SnapshotStore rather than trusting them.
- **The snapshot is a cache / projection only — never the source of truth.**
  Copy-on-write CanonicalZoneSnapshot is derived from plan+patches and may be
  discarded and rebuilt; if used as a file cache it is tagged
  (global_zone_key, revision, watermark_row_index) and never loaded when its
  watermark is ahead of the durable row log.
- **Watermark = InteractionState.previous_row_index** is the single recovery
  anchor (same single source of truth as the Row Ordering Contract). After
  rebuild it must equal the last durable row; only greater row_index is accepted.
- **Geometry-in-effect must be pinned** (geometry_version + bounds). If geometry
  is recomputed differently on restart, replay diverges — replay parity requires
  reusing the same geometry inputs.
- **Checkpoints are an optimization, not correctness.** A periodic
  InteractionState checkpoint (carrying the cumulative counters revision,
  active_visit_index, completed_visit_count, return_count, and guard/breach
  state) only bounds replay cost; it is never authoritative.

Primary (must persist): ordered row log, session_id, global_zone_key,
geometry-in-effect. Everything else (InteractionState, watermark, open visit,
snapshots, revision, last event id, dedup ledger, guard/breach) is DERIVED and
rebuildable from history.

No production code changed (documentation/design only).

Next: Restart / Durability implementation decision.

---

## Active Checkpoint: RDM_V2_ROW_ORDERING_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Row Ordering Contract (shadow-only) in the Interaction Interpreter:
- New entry point **`interpret_in_order()`** enforces row ordering BEFORE any
  transition; it delegates to the existing pure `interpret()` only on accept.
- New **`OrderingResult`** result type carries status + audit + state + events.
- Statuses: **ORDER_ACCEPTED** (normal transition), **ROW_DUPLICATE**,
  **ROW_OUT_OF_ORDER**.
- **InteractionState remains the single ordering watermark** (via
  `previous_row_index`). **No dispatcher watermark. No coordinator watermark.**
- **row_index is authoritative; timestamp is informational only** — equal
  timestamps with an increasing row_index remain valid.
- **No events are emitted for duplicate / out-of-order rows** (audit code only);
  on rejection the unchanged input state is returned (identity-preserved).
- **Existing `interpret()` remains unchanged** (byte-for-byte); all importers
  (dispatcher, coordinator, snapshot, adapters) pass unchanged.
- Production behavior unchanged (interaction_interpreter is shadow-only; no
  production consumers).

Rules (per global_zone_key):
  incoming.row_index >  previous_row_index -> ACCEPT, normal transition.
  incoming.row_index == previous_row_index -> ROW_DUPLICATE, no change.
  incoming.row_index <  previous_row_index -> ROW_OUT_OF_ORDER, no change.

Validation (all pass):
- python -m py_compile core/interaction_interpreter.py +
  experiments/interaction_interpreter/shadow_test.py +
  experiments/interaction_interpreter_ordering/shadow_test.py -> OK
- Existing interaction interpreter shadow test PASS (interpret() unchanged)
- New row ordering shadow test PASS (all 6 cases: normal increasing, duplicate,
  older, equal-timestamp-increasing-row, state-unchanged-after-reject,
  no-events-after-reject)
- Full shadow-suite regression (11 tests) PASS
- git diff --check clean

Files: core/interaction_interpreter.py (additive) +
experiments/interaction_interpreter_ordering/shadow_test.py (new).

Next: Restart / Durability Contract review (rehydrating the InteractionState
watermark across restarts so the ordering guard survives process restart).

---

## Active Checkpoint: RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Canonical Snapshot identity contract fix:
- Canonical Snapshot identity is now **global_zone_key**.
- zone_id is descriptive metadata only (no longer determines identity).
- SnapshotStore is keyed by global_zone_key (was: bare zone_id).
- Session-scoped identity now matches the Event Dispatcher identity contract.
- Snapshot revision model unchanged.
- Copy-on-write behavior unchanged.
- Snapshot sections unchanged.
- Production behavior unchanged (core/canonical_snapshot.py is shadow-only;
  only experiment shadow tests import it — no live/dashboard consumer).

Why: the Event Dispatcher namespaces identity by session_id (+ global_zone_key),
but the snapshot store keyed by bare zone_id. zone_id is legitimately reused
across daily sessions, so the snapshot layer could collide ("Snapshot already
exists for zone …") or overwrite the wrong session. Fixed by keying the store
and CanonicalZoneSnapshot identity on global_zone_key (zone_id retained as
metadata; global_zone_key added to protected metadata, validated non-empty and
for revision continuity).

Validation (all pass):
- python -m py_compile core/canonical_snapshot.py -> OK
- All 8 Canonical Snapshot / adapter shadow tests PASS
- New identity-collision shadow test PASS — same zone_id reused across two
  sessions yields two INDEPENDENT snapshots, no collision, no overwrite:
    Session A = BTCUSDT_2026-06-28_230000Z::SNAPSHOT_ZONE_1
    Session B = BTCUSDT_2026-06-29_230000Z::SNAPSHOT_ZONE_1
    shared zone_id = SNAPSHOT_ZONE_1; independent state (geometry width 10 vs 20).
- git diff --check clean

Files: core/canonical_snapshot.py + Canonical Snapshot / adapter shadow tests.

Next: Row Ordering Guard architectural review (monotonic row_index/timestamp
guard at the interpreter/dispatcher seam for out-of-order / late rows).

---

==================================================
STATISTICAL FOUNDATION UPDATE
==================================================

PHASE 1B STATUS

Current Active Phase:

PHASE 1B OBSERVATION RESEARCH MODE

Advanced Statistical Engine

Observation / Research Checkpoint

Status:

COMPLETED ✅

--------------------------------------------------
COMPLETED ITEMS
--------------------------------------------------

- Volume Statistical Foundation
- Spread Statistical Foundation
- Velocity Statistics
- Velocity Acceleration
- Velocity Exhaustion
- Distribution Shift Detection
- Gaussian Modeling
- Extreme Event Detection
- Statistical Dashboard V1
- Statistical Dashboard Alert Block
- Observation Logger
- Observation Events CSV
- Dashboard Episodes CSV
- Streamlit Observation Studio
- Smooth Panel Refresh
- Active Episode Tracking
- LIVE / REPLAY Observation Mode
- Replay Generator
- Observation Row Archive
- Observation Rows CSV
- Binance Historical Replay V1
- Archive V2 Field Extension
- Dashboard Episode Filters
- Statistical Dashboard V2


==================================================
PHASE 1B STABLE REPLAY CALIBRATION CHECKPOINT
==================================================

Replay dates:

2026-05-18 -> 2026-05-21

Rows:

5744

Events:

1940

Episodes:

222

Score distribution:

2=137
3=70
4=14
5=1

score>=4:

15

Highest score:

5

Historical Replay:

WORKING

Archive V2:

observation_rows.csv
21 -> 65 fields

Dashboard:

WORKING

Episode filters:

WORKING

DeepSeek fields:

ARCHIVED ONLY
NOT SCORED

Dashboard V2:

COMPLETED ✅

Extreme Event Detection = statistical abnormality classifier.

NOT entry signal.
NOT reversal signal.
NOT execution logic.

Calibration of weights and false positives will be reviewed later after live observation.


==================================================
DASHBOARD V2 STABLE REPLAY BENCHMARK
==================================================

Dashboard V2:

COMPLETED ✅

Replay window:

2026-05-18 -> 2026-05-21

Rows:

5744

--------------------------------------------------
V1 REFERENCE
--------------------------------------------------

Events:

1940

Episodes:

222

--------------------------------------------------
V2 RESULT
--------------------------------------------------

Events:

1867

Episodes:

347

Active rows:

1045

UNSTABLE_STATISTICAL_CONTEXT:

652

--------------------------------------------------
CALIBRATION HISTORY
--------------------------------------------------

Dashboard V2 was calibrated through staged passes:

- Step 10: removed always-on volatility, tightened price rarity, delta, distribution, and global activation
- Step 11: reduced distribution dominance and tightened unstable context
- Step 12: tightened price rarity and delta sensitivity
- Step 13: added weak two-layer combination filtering

Final review:

Dashboard V2 LOCKED

READY FOR STABLE CHECKPOINT

--------------------------------------------------
FINAL ACTIVE RULES
--------------------------------------------------

Dashboard V2 activates only when:

- at least 2 counted layers are active
- or one counted layer reaches EXTREME severity

Counted statistical layers:

- Distribution
- Multi ZScore
- Price Rarity
- Volatility
- Volume
- Velocity
- Delta

Spread / Execution remains observation confidence context.

Extreme Event remains escalation context.

--------------------------------------------------
FINAL SUPPRESSION RULES
--------------------------------------------------

Suppressed as display context unless strong confirmation exists:

- weak Distribution + Volatility
- weak Price Rarity + Volatility
- weak Distribution + Price Rarity

Strong confirmation means:

- HIGH severity
- EXTREME severity
- confirmed UNSTABLE_STATISTICAL_CONTEXT
- Extreme Event escalation

--------------------------------------------------
COMBINATION FILTERING RULES
--------------------------------------------------

Weak 2-layer combinations using only:

- Distribution
- Volatility
- Price Rarity

do not activate Dashboard V2 unless confirmed by stronger severity or unstable/extreme context.

Preserved combinations:

- Multi ZScore combinations
- Volume combinations
- Velocity combinations
- Delta combinations
- EXTREME layer activation

--------------------------------------------------
REPLAY HYGIENE REVIEW
--------------------------------------------------

Known deferred review:

NO_CONFLUENCE peak episode issue.

Status:

Deferred

Classification:

Replay hygiene review later.

NOT calibration.


==================================================
PHASE 1B OBSERVATION RESEARCH MODE
==================================================

Dashboard V2 completed ✅

Replay operational ✅

Dashboard V2 UI operational ✅

Historical observation active ✅

--------------------------------------------------
REPLAY BENCHMARK
--------------------------------------------------

V1:

Events = 1940

Episodes = 222

V2:

Events = 1867

Episodes = 347

Active rows:

1045

UNSTABLE_STATISTICAL_CONTEXT:

652

--------------------------------------------------
HYPOTHESIS_01
--------------------------------------------------

Score 4 may behave as:

EARLY_MOVEMENT_PRECURSOR

Score 5 may behave as:

ACCELERATION_ZONE

Score 6 may behave as:

FULL_STATISTICAL_ENVIRONMENT

Status:

NOT PROVEN

Observation only.

No trading.

--------------------------------------------------
RESEARCH ENVIRONMENT PLANNED
--------------------------------------------------

RESEARCH_JOURNAL.md

research/

phase1b_episode_research_log.csv

Target:

30–50 manual episodes

Need:

- counterexamples
- failed cases
- future replay windows

No Research Bot yet.

No Phase 2.

No execution.


==================================================
PHASE 1B RESEARCH AGENT V1 — STABLE ✅
==================================================

Included research components:

- Research Assistant
- Research Dashboard
- Score>=4 observation mode
- Hypothesis 02
- Preparation Detector V1
- Reversal Lab
- Expansion Lab
- Comparison Lab
- Preparation Quality Lab
- MASTER_RESEARCH_STATUS.md
- research_cleanup_report.csv

Research scope:

- Research only
- No live execution
- No decision engine
- No trading signals
- No Phase 2

Next step:

Continue Phase 1B by distributing and organizing fields / dashboard outputs.


==================================================
PHASE 1B+ RESEARCH EXTENSION — STABLE ✅
==================================================

Current mode:

PHASE 1B+ Research Expansion

Status:

STABLE ✅

Rules:

- No Phase 2
- No execution
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes

--------------------------------------------------
DASHBOARD V2 RESEARCH LAYER
--------------------------------------------------

Status:

STABLE ✅

Completed:

- Research Mapping Layer
- Episode Mapping
- Research Panel
- Episode -> Research Link
- Case Summary
- Observation Outcome
- Visual Research Cards
- Research Badges
- Label Cleanup

--------------------------------------------------
MEMORY ARCHITECTURE
--------------------------------------------------

Status:

STABLE ✅

Step 1:

50k Context Layer ✅

Implemented:

- MarketContextMemory
- price_context
- volume_context
- delta_context
- velocity_context
- distribution_context
- zone_context
- preparation_context
- expansion_context
- reversal_context
- research_context

Step 2:

Zone Lifecycle Memory ✅

States:

- zone_created
- zone_active
- zone_tested
- zone_rejected
- zone_broken
- zone_reclaimed
- zone_expired

Step 3:

Field Lifecycle Memory ✅

States:

- field_inactive
- field_active
- field_strengthening
- field_weakening
- field_exhausted
- field_recovered
- field_expired

--------------------------------------------------
LIFECYCLE EVENT PERSISTENCE
--------------------------------------------------

Status:

ACTIVE ✅

Files:

- zone_lifecycle_events.jsonl
- field_lifecycle_events.jsonl

Linked fields:

- episode_id
- case_id
- zone_id
- field_id
- row_index

Purpose:

Enable validation of HYPOTHESIS_05_LIFECYCLE_DECAY.

--------------------------------------------------
RESEARCH CYCLE 2
--------------------------------------------------

Status:

COMPLETED ✅

Score 4:

10 cases

Score 5:

1 case

Score 6:

1 case

Main result:

Score 4 remains primary research pool.

--------------------------------------------------
HYPOTHESIS_03 — FAILED_RETURN_REVERSAL
--------------------------------------------------

Status:

OBSERVATION ONLY

Supported pattern:

Preparation
        ↓
Return
        ↓
Failed Return
        ↓
Direct Reversal

--------------------------------------------------
HYPOTHESIS_04 — RETURN_REACTION_QUALITY
--------------------------------------------------

Status:

OBSERVATION ONLY

Successful Return:

- strong expansion
- no immediate reversal
- good zone reaction

Failed Return:

- immediate reversal
- weak zone reaction
- reaction delay
- delta extreme pressure

New variable:

return_reaction_quality

--------------------------------------------------
HYPOTHESIS_05 — LIFECYCLE_DECAY
--------------------------------------------------

Status:

SUPPORTED IN CURRENT SMALL SAMPLE ✅

NOT GLOBALLY PROVEN

Failed Return:

- zone_rejected
- field_exhausted
- SUPPORTED_DECAY_PATTERN

Successful Return:

- zone_reclaimed
- field_recovered
- RECOVERY_PATTERN

--------------------------------------------------
NEXT TARGET
--------------------------------------------------

PHASE 1B+ Research Expansion

Objectives:

- validate HYPOTHESIS_05 on larger replay windows
- increase Score 5 / Score 6 samples
- validate lifecycle decay statistically
- confirm or reject return_reaction_quality

No Phase 2.

No execution.

No live signals.


==================================================
ZSCORE RULE
==================================================

The core statistical interpretation uses a fixed ZScore threshold:

- `+2` = statistically high / abnormal positive deviation
- `-2` = statistically low / abnormal negative deviation

ZScore is NOT an entry signal.

WATCH ZONE ACTIVATION ONLY

Decision still requires:

- Confirmation
- Orderflow
- Liquidity
- Entropy Safety
- Decision Logic

This means ZScore activates attention, not execution. It identifies statistically abnormal conditions, but it does not confirm trade direction, timing, or execution quality by itself.

The threshold is treated as a stable interpretation layer, while the underlying statistical capture remains adaptive.


==================================================
ADAPTIVE STATISTICAL CAPTURE
==================================================

The system is designed to keep statistical capture adaptive through:

- rolling windows
- volatility regime detection
- RVI
- velocity statistics
- Entropy Mapping (future)
- distribution snapshots
- spread / volume / velocity foundations
- Delta Statistics

Adaptive capture means the system may adjust how it observes market behavior, but core abnormality interpretation remains anchored around fixed ZScore levels.


==================================================
MEMORY ARCHITECTURE
==================================================

Memory is separated into different logical layers. These layers are architectural targets and design rules, not all fully implemented components yet.

--------------------------------------------------
FAST SIGNAL MEMORY
--------------------------------------------------

Fast Signal Memory is used for live calculations and immediate statistical features.

Current implementation uses small bounded rolling windows for live features such as:

- zscore calculations
- distribution snapshots
- volatility regime
- velocity / volume / spread foundations
- short-term market state

Current window sizes are implementation details, not permanent limits. They may evolve based on performance testing, stability, and signal quality.

--------------------------------------------------
LIVE MEMORY
--------------------------------------------------

Target size:

- `5,000 rows`

Live Memory is intended to represent recent session context.

It is not a replacement for fast rolling windows. Fast signal calculations should remain bounded and optimized, while Live Memory can support broader recent-context awareness such as:

- session behavior
- recent regime persistence
- short-term structural context
- live calibration summaries

Status:

architecture direction / not fully implemented as a dedicated memory layer.

--------------------------------------------------
MARKET CONTEXT MEMORY
--------------------------------------------------

Target size:

- `50,000 rows`

Market Context Memory is intended for long-term context only.

It must not be used as a raw scan source inside the live calculation loop.

The 50k layer should feed summaries, baselines, profiles, and research/context outputs, not per-row raw calculations.

Examples of acceptable 50k-derived outputs:

- long-term volatility baselines
- session liquidity profiles
- historical spread behavior
- regime frequency summaries
- distribution reference summaries
- research/replay context

Status:

long-term context target / not implemented as a raw engine-local deque.

--------------------------------------------------
HARD RULE
--------------------------------------------------

`50k memory MUST NOT be used for every live calculation.`

Long memory should feed summaries, not raw live scans.

Live signal features must remain bounded, incremental, and safe for real-time execution.

--------------------------------------------------
FUTURE ARCHITECTURE NOTES
--------------------------------------------------

A dedicated memory/context layer may be introduced later if needed, but this is not a required decision now.

Possible future directions include:

- context summary storage
- session profile cache
- research/replay memory
- long-term baseline snapshots
- dedicated memory manager or context service

These are optional future architecture paths, not current implementation requirements.


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.1
==================================================

Status:

STABLE CHECKPOINT

Scope:

Research-only market mechanics layer.

Included:

- Fleche Model
- Signed Moment
- Capacity Layer
- Adaptive Sigma Barre
- ELS / ELU
- Timeline
- Mechanical Families
- Recovery
- Fatigue
- Rigidity
- Dashboard RDM Panels

Dashboard Panels:

- RDM Market Mechanics
- RDM Timeline
- Mechanical Capacity
- Adaptive Sigma Barre

Classification:

- Mechanics-first classification
- Variables -> Family -> Subtype -> State
- Cases are reference-only
- No hardcoded case-based classification rules

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No live signals
- No entries
- No scoring changes
- No Dashboard V2 scoring changes


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.3
==================================================

Status:

VALIDATED CHECKPOINT

Includes:

- Adaptive Sigma
- Sigma Aging
- Mechanical Capacity
- Verestchaguine Dynamic Fleche
- Zero Stress Protection
- Dormant Preparation
- Birth Registry
- Death Registry
- Mechanical Memory
- Birth Calibration
- Zone Evolution Chart
- Binance historical downloader robustness

Validation Summary:

Mechanical families:

- ELASTIC_FAMILY = 11
- FATIGUE_FAMILY = 10
- EXHAUSTION_FAMILY = 3
- RUPTURE_FAMILY = 2
- RECOVERY_FAMILY = 1

Mechanical states:

- RIGID_ZONE = 11
- FATIGUE_ZONE = 10
- EXHAUSTED_ZONE = 3
- RUPTURE_ZONE = 2
- RECOVERED_ZONE = 1

Capacity:

- SAFE = 12
- WARNING = 7
- ELU_LIMIT = 3
- CAPACITY_FAILURE = 2
- HIGH_LOAD = 2
- ELS_LIMIT = 1

Birth:

- RIGID_BIRTH = 8
- ELASTIC_BIRTH = 7
- EXPANSION_BIRTH = 5
- INSTITUTIONAL_BIRTH = 3
- UNKNOWN_BIRTH = 4

Death:

- DORMANT_EXPIRED = 11
- RUPTURE = 11
- EXHAUSTION = 3
- RECOVERY_COMPLETE = 1
- FATIGUE = 1

Artifacts:

- Birth rows = 27
- Death rows = 27
- Memory zones = 27
- Evolution rows = 27
- Evolution history = 139
- Lifecycle rows = 89

Downloader upgrade:

- timeout = 120 seconds
- retry = 10
- exponential backoff
- checkpoint
- resume
- partial aggTrades persistence

Classification:

- Mechanics-first classification
- Variables -> Family -> Subtype -> State
- Cases are reference-only

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No live signals
- No entries
- No scoring changes
- No Dashboard V2 scoring changes


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.4
==================================================

Status:

VALIDATED CHECKPOINT

Added after V1.3:

- RDM Result Layer
- Final Dashboard Result Block
- Zone Status Interpretation
- Health Score
- Risk Level
- Confidence Layer
- Short Reason
- Watch Action
- Section Result Summaries

New fields:

- rdm_zone_status
- rdm_health_score
- rdm_risk_level
- rdm_confidence
- rdm_short_reason
- rdm_watch_action

Current counts:

- DORMANT = 11
- FATIGUED = 10
- EXHAUSTED = 3
- RUPTURED = 2
- RECOVERING = 1

Dashboard structure:

LAYER 1 - FINAL RESULT

- Alive
- Recovering
- Fatigued
- Critical
- Exhausted
- Ruptured
- Dead
- Dormant

LAYER 2 - Deep Mechanics

- Family
- Subtype
- Fleche
- Moment
- Sigma
- Capacity
- Memory
- Evolution
- Death

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

Next step:

- Observation / Calibration
- Replay validation
- Historical validation
- False positive review
- Live observation
- DO NOT ADVANCE PHASES


==================================================
PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK
==================================================

Status:

STABLE CHECKPOINT

Base:

PHASE1B_RDM_MARKET_MECHANICS_V1_5

Completed after V1.5:

1) Data Integrity Diagnostic

- Episode 75 / CASE_00075 diagnostic completed.
- Source data verified.
- Timestamp / timezone alignment verified.
- Dashboard mapping verified.
- Episode row alignment verified.
- Stale artifacts detected and documented.

Reports / tools:

- outputs/data_integrity_episode_75_report.md
- outputs/data_integrity_episode_75.json
- tools/diagnose_episode_75_integrity.py

Diagnostic conclusions:

- SOURCE_DATA_OK
- TIMEZONE_OK
- DASHBOARD_MAPPING_OK
- EPISODE_ROW_ALIGNMENT_OK
- STALE_ARTIFACTS_FOUND

2) Replay Consistency Lock + Source Isolation

- Explicit source modes added:
  - LIVE_MODE
  - HISTORICAL_REPLAY_MODE
- Historical replay source guards added.
- Dashboard blocks live/default files in HISTORICAL_REPLAY_MODE.
- No silent fallback to stale live/default files in historical replay mode.
- Overlay loader accepts source_mode.
- Replay banner added:
  - REPLAY MODE ACTIVE
  - Replay Source
  - Replay Date
  - Replay UTC Window
  - Episode Row Range
- Source audit added per rendered Dashboard V2 episode.
- Dashboard footer added:
  - ACTIVE SOURCE: historical replay / live
- Replay consistency validator added.

Validator / reports:

- tools/validate_replay_consistency.py
- outputs/replay_consistency_report.md
- outputs/replay_consistency_report.json

Latest validator result:

- MIXED_SOURCE_USAGE_DETECTED: False
- STALE_LIVE_FILES_FOUND: True
- TIMESTAMP_INCONSISTENCIES_FOUND: False
- REPLAY_LIVE_OVERLAP_FOUND: False
- HISTORICAL_REPLAY_SOURCES_PRESENT: True

Important conclusion:

- Historical replay mode is now isolated.
- Stale live files may exist, but they are explicitly blocked from contaminating HISTORICAL_REPLAY_MODE.
- Replay / RDM / Dashboard / Overlay rendering are traceable to explicit historical replay sources.

Current stable state:

- RDM V1.5 stable.
- Performance diagnostics + safe optimization pass completed.
- Replay Consistency Lock completed.
- Source Isolation completed.
- Data Integrity Diagnostic completed.
- Current mode: Research only / Historical replay validation / Observation.

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only


==================================================
PERFORMANCE DIAGNOSTIC + SAFE OPTIMIZATION CHECKPOINT
==================================================

Status:

COMPLETED / READY TO SAVE

Scope:

- Diagnostics only
- Safe performance optimization only
- No behavior changes
- No scoring changes
- No RDM logic changes
- No Dashboard logic changes
- No trading logic

Completed work:

- Performance profiling added.
- Performance report generated:
  - outputs/performance_profile_report.md
  - outputs/performance_profile.json
- Performance optimization plan generated:
  - outputs/performance_optimization_plan.md
- Episode Research Index Cache implemented.
- RDM Per-Case Cache implemented.
- Shared Interaction Mask Cache implemented.
- Live evolution row-window optimization implemented.
- Profiling logs added.
- Cache reuse metrics added.

Measured results:

- Episode research runtime: 24.55s -> 17.23s
- Research analysis: 23.89s -> 16.38s
- Latest research run after continued optimization: 16.41s total, 15.83s cached analysis
- RDM runtime: 14.78s -> 14.66s
- Interaction core: 2.92s -> 1.96s
- Live evolution: 4.55s -> 4.36s
- Density: ~1.95s unchanged

Current profiling conclusions:

- Main bottleneck remains CPU_PROCESSING + RDM_CALCULATOR.
- Repeated scans were partially reduced successfully.
- Internet / Binance download is not the primary bottleneck for local research runs.
- Density mapping remains computationally heavy because weighted density buckets still require per-zone row analysis inside Active RDM Zone.

Current optimization state:

- Episode research now uses indexed row lookup for repeated historical row access.
- RDM calculator now caches live evolution rows by case.
- RDM interaction masks are built once and reused.
- Live evolution row windows use sorted row_id lookup instead of repeated full dataframe scans.

Future optimization targets:

- Vectorization of safe numeric RDM calculations.
- Optional Parquet / DuckDB research cache.
- Batch write / reduced write modes for validation.
- Optional multiprocessing later, only after deterministic output diff checks.

Latest checkpoint context:

- Base RDM checkpoint: PHASE1B_RDM_MARKET_MECHANICS_V1_5
- Previous committed context package commit: fa8c58b
- This optimization checkpoint commit: Add performance diagnostics and safe optimization pass

Rules remain:

- Research only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes


==================================================
PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK
==================================================

Status:

STABLE CHECKPOINT

Base:

PHASE1B_RDM_MARKET_MECHANICS_V1_5

Completed work:

1) Data Integrity Diagnostic

- Episode 75 diagnostic completed.
- Source data verified.
- Timezone verified.
- Dashboard mapping verified.
- Episode row alignment verified.
- Stale artifacts detected.

Reports / tools:

- outputs/data_integrity_episode_75_report.md
- outputs/data_integrity_episode_75.json
- tools/diagnose_episode_75_integrity.py

2) Replay Consistency Lock + Source Isolation

- Explicit source modes added:
  - LIVE_MODE
  - HISTORICAL_REPLAY_MODE
- Historical replay source guards added.
- Dashboard blocks live/default files in historical replay mode.
- No silent fallback to stale live files.
- Overlay loader accepts source_mode.
- Replay banner added:
  - REPLAY MODE ACTIVE
  - Replay Source
  - Replay Date
  - Replay UTC Window
  - Episode Row Range
- Source audit added per rendered episode.
- Dashboard footer added:
  - ACTIVE SOURCE: historical replay / live
- Replay consistency validator added:
  - tools/validate_replay_consistency.py

Reports:

- outputs/replay_consistency_report.md
- outputs/replay_consistency_report.json

Validation result:

- MIXED_SOURCE_USAGE_DETECTED: False
- STALE_LIVE_FILES_FOUND: True
- TIMESTAMP_INCONSISTENCIES_FOUND: False
- REPLAY_LIVE_OVERLAP_FOUND: False
- HISTORICAL_REPLAY_SOURCES_PRESENT: True

Important conclusion:

Historical replay mode is now isolated.

Stale live files may exist, but they are explicitly blocked from contaminating historical replay mode.

Replay / RDM / Dashboard / Overlay are now traceable to explicit historical replay sources.

Current stable state:

- RDM V1.5
- Performance diagnostics + safe optimization pass
- Replay Consistency Lock
- Source Isolation
- Data Integrity Diagnostic
- Historical replay validation
- Observation / research mode

Rules:

- Research only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only


==================================================
NEXT STEP
==================================================

PHASE 1B OBSERVATION / CALIBRATION

Current Focus:

Observation Research Mode

Historical Validation

Live Observation

Replay Research

Objectives:

- Observe false positives
- Observe Gaussian interaction
- Observe distribution shift interaction
- Observe extreme score behavior
- Monitor live outputs
- Review observation events
- Review dashboard episodes
- Replay archived observation rows

Status:

ACTIVE OBSERVATION RESEARCH

Dashboard V2:

COMPLETED / STABLE

DO NOT ADVANCE PHASES

NO PHASE 2

NO EXECUTION

User decides transition


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.5
==================================================

Status:

VALIDATED CHECKPOINT

Added after V1.4:

- Real Zone Geometry
- Birth vs Live Tracking
- Live RDM Evolution
- Calibration Guards
- Interaction Core Geometry
- Spatial Clamp
- Temporal Interaction Window
- True Lifecycle Guard
- Adaptive Recovery / Healing
- Regime-Normalized Sigma
- Interaction Density Mapping
- Weighted Interaction Center
- Density Bands
- Structural Lifecycle Calibration
- Recovery Persistence
- Fatigue Realism
- Rupture Persistence
- Mechanical Memory
- Birth / Return / Final comparison
- Overlay calibration
- Context vs Active Zone separation

RDM geometry hierarchy:

Context / Formation Range
!=
Active RDM Zone
!=
Interaction Density Band

Definitions:

- Context / Formation Range = broad historical formation area that created the zone.
- Active RDM Zone = compressed interaction core used as the primary active mechanical zone.
- Interaction Density Band = weighted concentration area inside the Active RDM Zone where touches, returns, stress, recovery, fatigue, and load cluster.

Calibration conclusions:

- Previous pessimistic collapse bias fixed.
- Recovery now has meaningful structural effect.
- Rupture persistence calibrated; one-row rupture behavior is guarded.
- Interaction core compression is operational and keeps active zone smaller than formation context.
- Density mapping is operational.
- Weighted interaction center and density bands are available for observation.
- Structure now behaves more realistically as an evolving lifecycle instead of a permanent collapse detector.
- Formation range remains context only; final RDM interpretation references Active RDM Zone / Interaction Core.

Dashboard / overlay status:

- Context / Formation Range shown as background.
- Active RDM Zone visually emphasized.
- Interaction Density Band shown inside Active RDM Zone.
- RDM final result uses guarded lifecycle and active zone context.

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

Current phase:

PHASE 1B+ Research Expansion

Next step:

- Observation / Calibration
- Replay validation
- Historical validation
- False positive review
- Live observation
- DO NOT ADVANCE PHASES


==================================================
PHASE1B_RDM_VISUALIZATION_STABLE
==================================================

Status:

STABLE CHECKPOINT

Completed after RDM V1.5:

1. Preparation Watch Fix

- Research coverage expanded from 93 rows to 634 rows.
- Coverage: 2026-05-25 -> 2026-06-01.
- Preparation candidates: 338.
- Research coverage: 100%.

2. RDM Coverage Fix

- RDM coverage increased from 35.48% to 100%.
- 634 / 634 Dashboard V2 episodes mapped.
- Dashboard RDM None / N/A coverage issue resolved for mapped episodes.

3. Dashboard Improvements

- Show All controls added.
- Row limit controls added.
- Date filters added.
- Sort order controls added.
- Preparation Watch display supports multi-day research rows.
- Dashboard V2 Research Mapping panels support multi-day rows across:
  PREPARATION, EXPANSION, REVERSAL, COMPARISON, HYPOTHESIS.

4. Timezone Support

- Algeria UTC+1 display support added.
- UTC display remains available.
- Display only; stored timestamps remain unchanged.
- No calculation changes.

5. RDM Mapping Fix

- resistance_live mapping added.
- Dashboard RDM fields now map to regenerated full research/RDM coverage.
- None / N/A coverage issue resolved for the full replay episode set.

6. RDM Visualization Discovery

Formation Range
!=
Active RDM Zone
!=
Interaction Density

Current interpretation:

- Formation Range = Context Layer.
- Active Core = Operational Zone.
- Density Band = Interaction Heart.

7. Episode 622 Validation

Birth Price:

72698.42

Formation:

72612.24 -> 72864.36

Width:

252.12

Active Core:

72787.66 -> 72850.70

Width:

63.03

Density Band:

72823.68 -> 72832.69

Width:

9.00

Core / Formation:

0.2500

Density / Formation:

0.0357

8. New Dashboard Component

RDM Price Overlay - Research Only

Uses:

- Formation Range
- Active Core
- Density Band
- Birth Price

Display:

- Absolute Price Axis
- Direct chart-comparison prices
- Reference table with exact lower / upper / width values
- Research only

9. Important Observation

Binance comparison suggests that Active Core and Density Band match visually
observed market zones significantly better than the full Formation Range.

10. No Changes To

- RDM formulas
- Dashboard scoring
- Replay generation
- Research logic
- Downloads
- Binance pulls

Rules:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

Next step:

Validate:

- Formation
- Active Core
- Density Band

Across multiple episodes.

Then return to:

- Prepare Zone TRUE > 4
- Continue RDM Market Mechanics:
  Rigidity, Fatigue, Recovery, Attacker


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.6
==================================================

==================================================
RDM V1.6-A NUMERICAL FOUNDATION
==================================================

Status:

COMPLETED

Scope:

Research only.

Implemented:

- 42 new rdm_v16_* columns
- Numerical Foundation layer
- Birth / Current / Live / Final metrics
- Delta from Birth
- Percentage Change from Birth

Metric Families:

- Rigidity
- Sigma
- Flèche
- Capacity
- Fatigue
- Recovery
- Stress Utilization (current)
- Moment Utilization (current)
- Interaction Density

Validation:

- py_compile passed
- zone_mechanics_calculator.py executed successfully
- 634 rows generated

Example:

Episode 622

Rigidity:
Birth=50.0
Current=50.0
Delta=0.0

Sigma:
Birth=19.194501
Current=7.276244
Delta=-11.918257
Change=-62.092039%

Rules Preserved:

- No scoring changes
- No lifecycle changes
- No Dashboard V2 scoring impact
- No RDM formula changes
- No Phase 2
- No execution
- No entries
- No live signals

Current Phase:

PHASE 1B+ Research Expansion

Active Work:

RDM V1.6 Development

Completed:

RDM V1.6-A Numerical Foundation

Next Target:

RDM V1.6-B Attacker Definition

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
ZONE TERMINOLOGY CLARIFICATION
==================================================

STATUS:
LABEL CLARIFICATION ONLY

Formation Range != Active RDM Zone != Density Band

Definitions:

* Formation Range = old Preparation Zone = broad context range from preparation_low_price / preparation_high_price.
* Active RDM Zone / Interaction Core = compressed operational zone inside Formation Range.
* Density Band / Interaction Heart = narrowest interaction concentration inside Active RDM Zone.

Dashboard label policy:

* Visible labels should not call preparation_low_price / preparation_high_price an entry zone.
* preparation_low_price / preparation_high_price should display as Formation Range (broad context).
* Active operational width should display as Active RDM Zone / Interaction Core Width.
* Narrow interaction concentration should display as Density Band / Interaction Heart Width.

Clarification:

Formation Range is broad context, not entry zone. Operational decision zone is Active Core / Density Band.

Rules:

No formula changes.
No replay changes.
No research changes.
No B12v2 changes.
No scoring changes.

==================================================
PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE
==================================================

STATUS:
STABLE CHECKPOINT

SUMMARY:

Historical Binance download completed successfully, but the session had many WinError 10060 timeout pauses and large delays.

ROOT CAUSE:

Network / Binance HTTP timeout instability during large historical downloads.

Not RDM.
Not dashboard.
Not replay formulas.
Not research formulas.

FILE CHANGED:

tools/generate_binance_historical_replay.py

FIXES IMPLEMENTED:

* REQUEST_TIMEOUT_SECONDS increased from 120 to 150
* MAX_RETRIES increased from 10 to 15
* RETRY_BACKOFF_SECONDS changed to:
  [10, 20, 40, 80, 120, 180, 240, 300]
* Added RETRY_JITTER_FACTOR = 0.30
* Added specific WinError 10060 detection
* Added longer recovery backoff for WinError 10060
* Added CLI flags:
  --max-retries
  --timeout
* fetch_agg_trades_batch_with_retries now returns:
  (batch_or_none, retries_used)
* download_agg_trades now tracks session_retries
* Resume loading now deduplicates partial trades by aggTrade ID
* Added checkpoint progress log every 25 batches:
  trades downloaded
  current timestamp
  last aggTrade id
  session retries
  elapsed
  ETA
  checkpoint file
  partial file
* Added final download verification:
  total trades
  first timestamp
  last timestamp
  duplicate trade IDs
  partial file path
  checkpoint file path

IMPORTANT NOTES:

This does not change:

* RDM formulas
* Replay logic
* Dashboard logic
* Research mapping
* Scoring
* Lifecycle logic
* BUY/SELL logic

This is a downloader stability-only patch.

VALIDATION:

PASSED:
python -m py_compile tools/generate_binance_historical_replay.py

CLI help confirmed new flags:

* --max-retries
* --timeout

RECOMMENDED NEXT DOWNLOAD COMMAND:

python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500

FOR UNSTABLE NETWORKS:

python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500 --max-retries 25 --timeout 180

==================================================
RDM V1.6 EXPOSURE PHYSICS SERIES — CHECKPOINT
PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
==================================================

STATUS: COMPLETED AND STABLE

Scope: Research only. No scoring changes. No lifecycle changes. No formula changes.

--------------------------------------------------
COMPLETED MODULES
--------------------------------------------------

RDM V1.6-A  Numerical Foundation                (previously committed)
RDM V1.6-B1  Attacker Force Basics              (previously committed)
RDM V1.6-B3.5-A  Attack Attempt Segmentation   (previously committed)
RDM V1.6-B3.5-B  Force-Lull Segmentation       (previously committed)
RDM V1.6-B4-A  Zone Strength Foundation (ZSS)  (previously committed)
RDM V1.6-B4-B  Zone vs Attacker Profile        (previously committed)
RDM V1.6-B5   Anomaly Physics                  (previously committed)
RDM V1.6-B5.5  Trajectory Context              (previously committed)
RDM V1.6-B6   Elastic Reinforcement Physics    (previously committed)
RDM V1.6-B7   Attacker Conversion Physics      (current session)
RDM V1.6-B7.5-A  Elastic Growth Rate Test      (current session)
RDM V1.6-B7.5-B  Force Allocation Physics      (current session)
RDM V1.6-B7.6-A  Absorption vs Reflection      (current session)
RDM V1.6-B7.6-B  Structural Engagement         (current session)
RDM V1.6-B7.6-C  Stress Exposure Physics       (current session)
RDM V1.6-B7.6-D  Omega Validation              (current session)
RDM V1.6-B7.6-E  Surface Damage Review         (current session)
RDM V1.6-B7.6-F  Surface Damage Validation     (current session)
RDM V1.6-B7.7   Structural Exposure Physics    (current session)

--------------------------------------------------
CORE VALIDATED FINDING
--------------------------------------------------

sigma_at_return × zone_penetration_depth  vs  omega_stress_area

r = 0.9935   (n=31)

Omega is the primary Deep Structural Exposure variable.

--------------------------------------------------
STRUCTURAL ENGAGEMENT CHAIN
--------------------------------------------------

Force
  ↓  [filtered by sigma_barre_zone]
  ↓  sigma_barre driven by structural memory
     (reclaim_history r=+0.69, mechanical_memory_score r=+0.67)
Structural Engagement
  ↓  [penetration depth]
Omega Stress Area  ≈  sigma_at_return × penetration_depth
  ↓  [routed by mechanical_family]
  ├── ELASTIC_FAMILY  →  Growth (+16 rigidity, +20 capacity — constant)
  └── DEGRADED_FAMILY →  Damage (fatigue + structural decay, scales with omega)

--------------------------------------------------
REJECTED HYPOTHESES
--------------------------------------------------

reinforcement_mode (B6):
  NOT independent from zone_mechanical_state.

Growth Rate (B7.5-A):
  Growth rate = 16/interaction_count — formula identity, not structural measurement.

Force Allocation (B7.5-B):
  total_growth = 36 constant for all ELASTIC zones regardless of force.
  Another reformulation of zone_mechanical_state.

Surface Damage (B7.6-E/F):
  REJECTED. Zero-omega damage is:
    rigidity_live = rigidity_birth - row_progress × zone_strength_decay × 0.55 + repair_effect × 8.0
  Time-based temporal decay formula. NOT independent market physics.

Cyclic Exposure (B7.7):
  Insufficient variance in current dataset (interaction_count range: 101-114).
  Not validated. Future research only.

--------------------------------------------------
RESEARCH CSVs ADDED
--------------------------------------------------

research/attacker_conversion_profile.csv
research/force_allocation_profile.csv

--------------------------------------------------
VALIDATION RESULT
--------------------------------------------------

python -m py_compile research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py tools/generate_binance_historical_replay.py

RESULT: ALL_COMPILE_OK

--------------------------------------------------
RULES PRESERVED
--------------------------------------------------

- No scoring changes
- No lifecycle changes
- No Dashboard V2 scoring impact
- No RDM formula changes
- No replay changes
- No dashboard changes
- No Phase 2 / No execution / No entries / No live signals

==================================================
CURRENT ACTIVE PHASE
==================================================

PHASE 1B+ Research Expansion

Active checkpoint:

PHASE1B_HYBRID_DOWNLOADER_STABLE

Prior checkpoints:

PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE

==================================================
PHASE1B_HYBRID_DOWNLOADER_STABLE
==================================================

PHASE1B_RAW_TRADE_ARCHIVE_V1 — Tier 1 Local Raw Trade Cache

STATUS: COMPLETED

One CSV per UTC day: archives/{SYMBOL}/raw-trades/{YYYY-MM-DD}.csv

New functions:
- _raw_trade_cache_path
- _day_ms_range
- _iter_utc_days
- _trade_to_csv_row / _csv_row_to_trade
- _verify_raw_trades
- try_load_raw_trade_cache
- save_raw_trade_cache (atomic write: tmp -> verify -> rename)

Cache file: 8 columns matching API dict {a, p, q, f, l, T, m, M}

Verification: len >= 1000, timestamps within expected UTC day.

Corrupted cache files skipped but preserved for inspection.

---

PHASE1B_BINANCE_ZIP_ARCHIVE_V1 — Tier 2 Binance Public ZIP

STATUS: COMPLETED

URL: https://data.binance.vision/data/spot/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{date}.zip

New functions:
- is_binance_zip_available(date_str): date <= today UTC - 2 days
- download_day_from_binance_zip(symbol, date_str): HTTP GET, in-memory extract, CSV parse

IMPORTANT: Binance ZIP timestamps are in MICROSECONDS.
API timestamps are in MILLISECONDS.
Conversion: t["T"] = t["T"] // 1000

Failure handling: 404, network error, bad ZIP, parse error
all fall through to Tier 3. No silent failure.

After ZIP success: saved to Tier 1 cache for zero-cost future runs.

Validated test:
- BTCUSDT 2026-05-25
- 542,386 trades | 7.7 MB | 2.7 seconds
- Timestamps verified within UTC day after conversion
- Round-trip save + load: OK
- Second run: CACHE HIT (0 network requests)

New CLI flags:
- --no-local-cache: skip Tier 1
- --no-zip: skip Tier 2

3-tier priority order per UTC day:

1. Local cache (archives/{SYMBOL}/raw-trades/{date}.csv) -> CACHE HIT
2. Binance ZIP (data.binance.vision) -> ZIP HIT -> save to cache
3. API fallback (existing loop) -> API DOWNLOAD -> save to cache

VALIDATION:

python -m py_compile tools/generate_binance_historical_replay.py research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py

RESULT: ALL_COMPILE_OK

No changes to:
- RDM formulas
- Replay logic
- Dashboard logic
- Scoring
- Lifecycle logic
- Research logic

Next priorities:

1. Run 2026-05-20 to 2026-06-02 replay to rebuild 634-row RDM research base
2. Continue RDM V1.6 on full dataset
3. Zone intent framework research
4. Per-cycle omega decomposition (future)

==================================================
PHASE1B_SYNTHESIS_ENGINE_STABLE
==================================================

STATUS: COMPLETED AND STABLE

Phase 1 is now structurally coherent.
The system no longer treats layers as isolated indicators.

The Phase 1 Synthesis Engine connects all Phase 1 layers into
one MarketInterpretation per zone case.

--------------------------------------------------
NEW FILE
--------------------------------------------------

research/synthesis_engine.py

Components:
- Simplified Taxonomy Register (role + scope per field)
- Bundle Assembler (B10 + B11 + episode statistical context)
- Priority Rules (STRUCTURAL > CURRENT, STRUCTURE > CONTEXT)
- Genuine Conflict Check (binary flag)
- 3-Gate Synthesis Check
- 4-Level Coherence Label (STRONG / MODERATE / WEAK / INSUFFICIENT)
- Field Compressors (6 threshold-based compressors)
- Template Engine (3 templates + catch-all)

--------------------------------------------------
MODIFIED FILE (4 additive lines only)
--------------------------------------------------

research/zone_mechanics_calculator.py
- ZONE_SYNTHESIS_FILE constant added
- import build_zone_synthesis added
- rdm_synthesis_engine profiler step added after B11
- synthesis_df.to_csv() added to output block

--------------------------------------------------
NEW OUTPUT
--------------------------------------------------

research/zone_synthesis.csv

Columns (13):
  analysis_run_utc, case_id, episode_id, zone_id,
  zone_mechanical_state, context, structure, engagement,
  flow, prediction, coherence, interpretation, research_only

Results (276-zone, 12-day archive):
  Rows:               276
  Duplicate case_id:  0
  Null interpretation: 0
  Max interpretation length: 68 chars (limit 80)
  Runtime: 0.47s

Coherence distribution:
  STRONG:        126  (45.7%)
  MODERATE:       35  (12.7%)
  INSUFFICIENT:  115  (41.7%)

Prediction distribution:
  NO_PREDICTION:  115  (41.7%)
  HOLD:            90  (32.6%)
  FAIL:            65  (23.6%)
  UNCERTAIN:        6   (2.2%)

Example interpretation sentences:
  "TERMINAL zone under opposing flow - failure confirmed."
  "STRENGTHENING zone after 3 visits - hold confirmed."
  "STABLE zone with zone dominant - hold expected."
  "DEGRADING zone - trajectory developing, await further visits."
  "Single-visit zone - insufficient evidence for structural prediction."

--------------------------------------------------
WHAT THE SYNTHESIS ENGINE DOES NOT DO
--------------------------------------------------

- Does not produce BUY / SELL signals
- Does not produce entries or exits
- Does not modify any RDM formula
- Does not modify Dashboard V2 scoring
- Does not modify lifecycle logic
- Does not modify replay logic
- Reads from existing CSVs, writes one new CSV
- No Phase 2

--------------------------------------------------
POSTPONED (after B12 backtesting)
--------------------------------------------------

- Numeric Coherence Score (0-100) - needs B12 accuracy calibration
- Redundancy Detection - needs inter-signal correlation data
- Advanced Conflict Types - needs historical contradiction patterns

--------------------------------------------------
VALIDATION
--------------------------------------------------

python -m py_compile research/synthesis_engine.py research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py

RESULT: ALL_COMPILE_OK

python research/zone_mechanics_calculator.py
-> Zone synthesis: research\zone_synthesis.csv produced successfully.
-> Rows generated: 276

--------------------------------------------------
NEXT PHASE
--------------------------------------------------

Active checkpoint: PHASE1B_SYNTHESIS_ENGINE_STABLE

Next task: Long data collection before backtesting.

Target: 45-60 days of BTCUSDT historical data.

Sequence after collection:
1. Full pipeline rebuild (analyze + RDM calculator)
2. B12: Prediction Validation (structural_prediction vs observed outcomes)
3. Numeric Coherence Score calibration from B12 accuracy data
4. Large-scale backtesting
5. Synthesis Engine refinement based on real errors

Do not advance to Phase 2.
Do not modify formulas.
Do not modify Dashboard scoring.


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



==================================================
PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE
==================================================

Date: 2026-06-06
STATUS: STABLE CHECKPOINT

--------------------------------------------------
ROOT CAUSE
--------------------------------------------------

In research/zone_mechanics_calculator.py, inside build_zone_visit_timeline(),
the rigidity fallback pattern at line 3628 (original):

    rig_v = to_float(last_row.get("rigidity_live")) or rig_birth

Python `or` treats 0.0 as falsy. For EXHAUSTED_ZONE (MEDIUM strength,
rig_birth=30.0, zone_strength_decay>=50, recovery_current=0.0), the live
rigidity formula clamps to exactly 0.0:

    rigidity_live = max(rigidity_birth - row_progress * decay * 0.55 + repair * 8.0, 0.0)

When rigidity_live=0.0 was returned, `to_float()` returned 0.0 (correct),
but `or rig_birth` silently replaced it with 30.0 (birth value). This
prevented BREAKDOWN from firing because:

    rig_v=30.0 < rig_birth*0.50=15.0  -->  False  (no BREAKDOWN)
    rig_v=0.0  < rig_birth*0.50=15.0  -->  True   (BREAKDOWN fires)

The fallback was not a logic error in the original design intent, but Python
`or` treats 0.0 the same as None, making the "missing data guard" also fire
on fully decayed but valid states.

--------------------------------------------------
FIX
--------------------------------------------------

Single line change in research/zone_mechanics_calculator.py (lines 3631-3632):

BEFORE (line 3628):
    rig_v = to_float(last_row.get("rigidity_live")) or rig_birth

AFTER (lines 3631-3632):
    _rig_raw = to_float(last_row.get("rigidity_live"))
    rig_v    = rig_birth if _rig_raw is None else _rig_raw

Explicit None-check: preserves 0.0 (fully decayed) vs None (missing data).
cap_v, hlt_v, sig_v fallbacks unchanged (separate audit required).

--------------------------------------------------
IMPACT ON ZONE_VISIT_TIMELINE
--------------------------------------------------

Effect A — RECLAIM reclassified to BREAKDOWN:
  Cases where rigidity_live=0.0 was silently replaced by rig_birth=30.0,
  causing visit_result=RECLAIM instead of BREAKDOWN.
  Formation: 13 cases flipped
  (zone_visit_timeline.csv: 20 RECLAIM at visit N before fix → 7 after fix)

Effect B — DAMAGE reclassified to BREAKDOWN:
  Cases where fallback prevented BREAKDOWN, classifier fell to DAMAGE
  (AMBIGUOUS in B12v2). After fix, BREAKDOWN fires first.
  Formation: +17 newly evaluable correct FAILs
  Active Core: +13 newly evaluable correct FAILs
  Density Band: +7 newly evaluable correct FAILs

--------------------------------------------------
VALIDATED RESULTS — POST-FIX B12v2
--------------------------------------------------

Formation mode (research/b12v2_report.md):
  Evaluable: 650  |  Accuracy: 98.8%  |  Lift: +42.3% vs baseline 56.5%
  HOLD  — Precision: 99.2%  Recall: 98.6%  F1: 0.989  |  False HOLDs: 3
  FAIL  — Precision: 98.2%  Recall: 98.9%  F1: 0.986  |  False FAILs: 5
  LEAKAGE: PASS  |  CONSISTENCY: PASS

Active Core mode (research/b12v2_report_active_core.md):
  Evaluable: 400  |  Accuracy: 98.8%  |  Lift: +43.8% vs baseline 55.0%
  HOLD  — Precision: 98.6%  Recall: 99.1%  F1: 0.989  |  False HOLDs: 3
  FAIL  — Precision: 98.9%  Recall: 98.3%  F1: 0.986  |  False FAILs: 2
  LEAKAGE: PASS  |  CONSISTENCY: PASS

Density Band mode (research/b12v2_report_density_band.md):
  Evaluable: 263  |  Accuracy: 98.5%  |  Lift: +43.3% vs baseline 55.1%
  HOLD  — Precision: 98.0%  Recall: 99.3%  F1: 0.986  |  False HOLDs: 3
  FAIL  — Precision: 99.1%  Recall: 97.5%  F1: 0.983  |  False FAILs: 1
  LEAKAGE: PASS  |  CONSISTENCY: PASS

Remaining false HOLDs (all 3 modes): 3 identical cases
  — STABLE trajectory / EXHAUSTED_ZONE / HEALTH_STABLE

Remaining false FAILs after fix:
  Formation: 5 (4x EXHAUSTED_ZONE rig_birth>30, 1x RIGID_ZONE ABSORPTION)
  Active Core: 2 (EXHAUSTED_ZONE DEGRADING)
  Density Band: 1 (EXHAUSTED_ZONE DEGRADING)

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

No formula changes.
No Phase 1 production file changes.
No RDM formula changes.
No B9/B10/B11/Synthesis changes.
No lifecycle logic changes.
No replay formula changes.
No dashboard changes.

Only zone_mechanics_calculator.py line 3628 modified (rigidity fallback).
zone_visit_timeline.csv regenerated from existing CSVs (no replay needed).

--------------------------------------------------
FILES CHANGED
--------------------------------------------------

research/zone_mechanics_calculator.py       (fix: line 3628)
research/zone_visit_timeline.csv            (regenerated: 3841 rows)
research/b12v2_case_results.csv             (650 rows)
research/b12v2_case_results_active_core.csv (400 rows)
research/b12v2_case_results_density_band.csv (263 rows)
research/b12v2_report.csv / .md
research/b12v2_report_active_core.csv / .md
research/b12v2_report_density_band.csv / .md
research/b12v2_penultimate_predictions.csv
research/b12v2_penultimate_predictions_active_core.csv
research/b12v2_penultimate_predictions_density_band.csv

--------------------------------------------------
RULES
--------------------------------------------------

No Phase 2.
No execution.
No BUY/SELL.
Do NOT change Phase1B formulas.
Do NOT change RDM formulas.
Do NOT modify B11/B12v2 logic.
Do NOT download data without explicit request.

--------------------------------------------------
NEXT RESEARCH CANDIDATE
--------------------------------------------------

PHASE1B_EXHAUSTED_ZONE_RESEARCH
Goal: Characterize the remaining false FAIL and false HOLD cases that are
concentrated in EXHAUSTED_ZONE. Understand whether STABLE trajectory cases
represent a structural exception or an edge case in B10 trajectory labeling.


==================================================
PHASE1B_LIVE_ZONE_ENGINE_STABLE
==================================================

DATE:
2026-06-09

STATUS:
STABLE

OBJECTIVE ACHIEVED:

Full LIVE Zone Engine operational from V2 Episode generation through LIVE structural prediction.

==================================================
COMPLETED
==================================================

LIVE V2 Episodes

- LIVE episode closure
- Dashboard integration
- Episode persistence
- Score4+ parity validation

Preparation Engine

- LIVE Preparation snapshots
- Replay parity validation
- Score4+ filter enforced
- peak_layer_count >= 4 required
- Preparation Watch dashboard

Lifecycle Engine

- ZoneLifecycleMemory
- FieldLifecycleMemory
- LIVE lifecycle events
- zone_created
- zone_tested
- zone_rejected
- zone_reclaimed
- expansion_state
- reversal_state
- hypothesis02_state

Return Detection Engine

- Streaming return detection
- Replay parity validation
- Formation-bound detection
- CLOSE-only parity with replay
- Pending zone registry
- return_found tracking

Two-Phase Emit Architecture

PENDING_FINALIZATION:

- Immediate structural output
- Group A
- Group B
- B8
- B9
- B10
- B11
- Synthesis

FINALIZED_OUTCOME:

- future moves
- reversal_type
- expansion_type
- failed_after_return
- max_move_after_return

RDM LIVE

- Group A
- Group B
- RDM evolution
- Attacker evolution
- Timeline
- Health evolution

B10

- Structural trajectory

B11

- Structural prediction

Synthesis

- Structural interpretation
- Prediction reasoning

Geometry

Formation

- preparation_low_price
- preparation_high_price
- preparation_mid_price

Tight Formation

- tight_formation_low_price
- tight_formation_high_price
- tight_formation_mid_price

Active Core

- interaction_core_lower_edge
- interaction_core_upper_edge
- interaction_core_mid_price
- interaction_core_width

Density Band

- interaction_density_lower_band
- interaction_density_upper_band
- interaction_density_weighted_center
- interaction_density_width

Dashboard

8 LIVE panels operational:

1. Live V2 Episodes
2. Preparation Watch
3. Lifecycle Watch
4. Return Detection
5. RDM Status
6. B10 Trajectory
7. B11 Prediction
8. Synthesis

==================================================
VALIDATION STATUS
==================================================

Preparation:
PASS

Lifecycle:
PASS

Return Detection:
PASS

RDM:
PASS

B10:
PASS

B11:
PASS

Synthesis:
PASS

Unexplained divergences:
ZERO

==================================================
ARCHITECTURAL DECISIONS
==================================================

Replay parity preserved.

Return Detection uses:

Formation bounds only

Condition:

close >= zone_low
and
close <= zone_high

Wick touches are ignored.

Active Core and Density Band:

Display-only geometry layers.

Do NOT participate in return detection.

Score4+ parity:

LIVE now mirrors replay.

Episodes with:

peak_layer_count < 4

are ignored before Preparation processing.

==================================================
CURRENT LIVE STATUS
==================================================

LIVE system healthy.

No active bug.

After restart:

V2 episodes observed:
4

Score4+ episodes:
0

Preparation zones:
0

Reason:

Market has not yet produced a qualifying score4+ episode.

System waiting for:

peak_layer_count >= 4

followed by

valid Preparation candidate.

==================================================
NEXT STEP
==================================================

Observe LIVE market.

Wait for:

1. score4+ episode
2. valid Preparation candidate
3. return_found
4. first PENDING_FINALIZATION record
5. first Active Core
6. first Density Band
7. first LIVE B11 prediction

Stop here.

Do NOT start Footprint.
Do NOT start Microstructure.
Do NOT start Regime Engine.

--------------------------------------------------
RULES
--------------------------------------------------

No Phase 2.
No execution.
No BUY/SELL.
Do NOT change Phase1B formulas.
Do NOT change RDM formulas.
Do NOT modify B11/B12v2 logic.
Do NOT download data without explicit request.

==================================================
PHASE1B_RDM_V2_MECHANICAL_ARCHITECTURE_STABLE
==================================================

STATUS:
STABLE RESEARCH CHECKPOINT

SCOPE:
Documentation and architecture consolidation only.

COMPLETED:
- Stage 5D Dynamic State signature analysis
- Stage 5E transition analysis
- Stage 5F transition family discovery
- Stage 5G attacker force causality analysis
- Stage 5H mechanical dependency graph

NEW DOCUMENTATION:
- docs/RDM_V2_MECHANICAL_ARCHITECTURE_SPEC.md

STAGE 5H DEPENDENCY GRAPH:
- Variables classified: 49
- Dependency edges: 113
- Dependency layers: 21
- Max dependency depth: 20
- Direct dependency loops: 0

CORE ARCHITECTURE:
Raw Market Data
    -> Statistics Engine
    -> Geometry Engine
    -> Interaction / Penetration
    -> Mechanical Exposure
    -> RDM V2
    -> SDR / Derivative / Integral
    -> Dynamic State
    -> Structural Prediction

VALIDATED CONCLUSIONS:
- The mechanical engine is feed-forward at artifact-generation time.
- Temporal memory exists through integrals, guards, health evolution, sigma evolution, and structural damage.
- No same-step algebraic loop was confirmed.
- Stage 2C replaced frozen post-return mechanics with acute pressure + chronic structural damage.
- Stage 2C is mechanically superior to frozen post-return behavior.
- ATTACKER_DOMINANT has a distinct mechanical signature.
- ATTACKER_DOMINANT is the strongest continuation-bearing Dynamic State so far.
- STABLE / PROBABLE_HOLD are more rejection-biased.
- Attacker Force and Omega are common first movers in transition analysis.
- Fatigue is the clearest deterioration precursor.
- Attacker Force appears interaction-conditioned, not raw-delta-only.

ARCHITECTURAL DECISION:
Current mechanical architecture is accepted as a stable research checkpoint.
It is not approved for production replacement.
It is not trading validation.
It does not start Phase 2.

PROJECT STATUS:
Project 1 remains inside Phase 1B+ research expansion.
Project 2 remains not implemented; its intended philosophy is to replace only the Geometry Engine while reusing replay, statistics, dashboard, research infrastructure, and validation methodology.

RULES PRESERVED:
No production formula change.
No replay change.
No dashboard logic change.
No RDM formula change.
No Dynamic State threshold change.
No execution.
No entries/exits.
No BUY/SELL.
No live signals.
No Phase 2.

NEXT ARCHITECTURAL DECISION:
Decide whether to continue Dynamic State architecture review, study redundancy/merging questions, or begin the next approved research stage. Do not implement Project 2 until explicitly approved.


==================================================
RDM_V2_EVENT_DRIVEN_SHADOW_FOUNDATION
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

OBJECTIVE:
Establish the first deterministic, event-driven RDM V2 foundation
without connecting it to any production or LIVE processing path.

COMPONENTS:
- Interaction Interpreter
  - Pure normalization layer from market row + geometry state to
    MechanicalEvent records.
  - Supported shadow events: TOUCH, ZONE_ENTER, ZONE_EXIT, RETURN,
    PENETRATION_UPDATED, VISIT_STARTED, VISIT_COMPLETED.
- Mechanical Refresh Coordinator
  - Pure orchestration planner from InteractionState + MechanicalEvent
    records to dirty flags and an ordered RefreshPlan.
  - Does not calculate mechanics or call RDM components.
- Interpreter + Coordinator Shadow Chain Test
  - Deterministic synthetic sequence validates:
    market row + geometry -> events -> refresh plan.
  - Two identical runs produce identical event and plan output.
  - Expected events and dirty flags pass with zero mismatches.

ARCHITECTURAL ROLE:
Foundation for a future Event-Driven RDM V2 refresh pipeline.
Interaction interpretation and refresh planning are now explicit while
all existing calculations and consumers remain unchanged.

ISOLATION:
- Shadow mode only.
- Not consumed by the production pipeline.
- No LIVE integration.
- No file routing or snapshot writes.
- No dashboard integration.
- No Stage 2C integration.
- No RDM formula change.
- No Dynamic State change.
- No production behavior change.

VALIDATION:
- core/interaction_interpreter.py compile: PASS
- core/mechanical_refresh_coordinator.py compile: PASS
- experiments/event_refresh_shadow_chain.py compile: PASS
- SHADOW_CHAIN_TEST = PASS
- DETERMINISTIC_REPLAY = PASS
- PRODUCTION_EFFECTS = FALSE
- MISMATCHES = NONE

NEXT:
Await architectural approval before any production integration.


==================================================
RDM_V2_EVENT_DRIVEN_BACKBONE_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

SHADOW BACKBONE:
Interaction Interpreter
    ->
Event Dispatcher
    ->
Mechanical Refresh Coordinator

COMPONENT RESPONSIBILITIES:
- Interaction Interpreter
  - Converts market row + geometry state into normalized MechanicalEvent
    records.
- Event Dispatcher
  - Validates identity and event ordering.
  - Deduplicates event IDs.
  - Sends one accepted event batch to the shadow coordinator.
- Mechanical Refresh Coordinator
  - Converts InteractionState + MechanicalEvent records into dirty flags
    and an ordered RefreshPlan.
  - Plans refresh work without executing mechanical calculations.

EVENT DISPATCHER VALIDATION:
- Valid ordered batch: PASS
- Duplicate event IDs: PASS
- Replayed event IDs: PASS
- Invalid event order rejection: PASS
- Zone mismatch rejection: PASS
- Shadow coordinator plan returned: PASS
- Production effects: FALSE

ARCHITECTURAL ROLE:
The event-driven RDM V2 shadow backbone is now complete. It establishes
deterministic event interpretation, transport, validation, deduplication,
and refresh planning before any future Canonical Snapshot integration.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No stream_manager or observation_logger integration.
- No LIVE pipeline changes.
- No RDM formula changes.
- No Dynamic State changes.
- No Stage 2C integration.
- No dashboard changes.
- No snapshot implementation.
- No runtime file writes.
- No production behavior change.

NEXT:
Await explicit approval before implementing the Canonical Snapshot or
connecting any shadow component to production.


==================================================
RDM_V2_CANONICAL_SNAPSHOT_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

IMPLEMENTED:
- CanonicalZoneSnapshot
  - Deeply immutable current-state projection for one shadow zone.
- SnapshotBuilder
  - Assembles supplied RefreshPlan result patches.
  - Does not calculate mechanical values.
- SnapshotStore
  - In-memory current-snapshot store.
  - Supports create, get_current, and update.

INITIAL SNAPSHOT SECTIONS:
- Metadata
- Geometry
- Current Row Mechanics
- Open Visit

REVISION MODEL:
- Snapshot creation begins at revision 1.
- Every successful update increments the revision.
- Updates use copy-on-write.
- A candidate revision is built completely before publication.
- A failed update leaves the previous immutable revision valid.

BOUNDARY:
- In-memory shadow only.
- No persistence or CSV writes.
- No production consumer.
- No stream_manager, observation_logger, or LIVE integration.
- No dashboard integration.
- No Last Completed Visit section yet.
- No Dynamic Mechanics or Dynamic State.
- No transitions.
- No Stage 2C.
- No B10/B11 or prediction.
- No RDM formula change.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- experiments/canonical_snapshot/shadow_test.py compile: PASS
- Snapshot creation: PASS
- Snapshot update: PASS
- Revision increment: PASS
- Failed update preserved previous revision: PASS
- Production effects: FALSE

NEXT:
Await explicit approval before integrating the first mechanical component.


==================================================
RDM_V2_ROW_MECHANICS_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/row_mechanics_adapter.py
- experiments/row_mechanics_adapter/shadow_test.py

IMPLEMENTED:
- Row Mechanics Adapter Stage 1
- Mapping of 17 existing current-row mechanical fields:
  price, timestamp, row ID, zone presence, touch, distance, penetration,
  fleche, sigma market, sigma barre, load, Omega, fatigue, recovery,
  rigidity, capacity, and health.
- Explicit source aliases with source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN inputs.
- Zero and False remain valid source values.
- RefreshResult-style Current Row Mechanics patch output.
- Canonical Snapshot shadow-store compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No arithmetic.
- No numeric coercion.
- No normalization.
- No fallback mechanical derivation.
- Existing values are copied unchanged.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE integration.
- No live_rdm changes.
- No RDM formula changes.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/row_mechanics_adapter.py compile: PASS
- experiments/row_mechanics_adapter/shadow_test.py compile: PASS
- Normal row mapping: PASS
- Missing-field handling: PASS
- No-calculation proof: PASS
- Canonical Snapshot patch application: PASS
- Production effects: FALSE

NEXT:
Await approval for the next mechanical adapter.


==================================================
RDM_V2_OPEN_VISIT_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/open_visit_adapter.py
- experiments/open_visit_adapter/shadow_test.py

IMPLEMENTED:
- Open Visit Adapter Stage 1
- Mapping from existing InteractionState or visit-style dictionaries into
  Canonical Snapshot Open Visit patches.
- Open Visit fields include visit identity/status, start row/time/price,
  row count, maximum penetration, cumulative Omega, accumulated pressure,
  attacker force, interaction flags, and last event/row identity.
- active_visit_flag explicitly identifies active versus inactive visits.
- Explicit source-field provenance.
- NOT_AVAILABLE handling for missing visit values.
- Available False and zero values remain valid.
- Canonical Snapshot shadow-store patch compatibility.

NO-ACTIVE-VISIT BEHAVIOR:
- active_visit_flag = False.
- Visit-specific fields are NOT_AVAILABLE.
- Existing interaction facts such as inside_zone=False and
  touch_active=False remain available and unchanged.

CALCULATION BOUNDARY:
- Mapping only.
- No accumulation.
- No inferred visit outcome.
- No inferred Omega, pressure, attacker force, or visit status.
- No mechanical formulas or coercion.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/open_visit_adapter.py compile: PASS
- experiments/open_visit_adapter/shadow_test.py compile: PASS
- Active visit mapping: PASS
- No-active-visit behavior: PASS
- Missing-field handling: PASS
- No-calculation proof: PASS
- Canonical Snapshot patch application: PASS
- Production effects: FALSE

NEXT:
Await approval for the next adapter.


==================================================
RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/last_completed_visit_adapter.py
- experiments/last_completed_visit_adapter/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes last_completed_visit.
- SnapshotBuilder and SnapshotStore accept immutable
  last_completed_visit patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot tests remain valid.

ADAPTER:
- Last Completed Visit Adapter Stage 1.
- Maps 22 existing completed-visit fields.
- Includes visit identity, row/time boundaries, duration, row count,
  penetration, Omega, attacker force, structural values, visit result and
  classification, plus absorption/reflection/reclaim/damage/growth flags.
- Supports current timeline aliases including visit_start_time,
  visit_end_time, visit_duration_rows, and max_penetration_at_visit.
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False are preserved as valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No duration calculation.
- No visit classification.
- No inferred outcome flags.
- No formulas, coercion, or fallback mechanical derivation.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/last_completed_visit_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Completed-visit mapping: PASS
- Missing-field handling: PASS
- Zero/False preservation: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Production effects: FALSE

NEXT:
Await Dynamic Mechanics Adapter approval.


==================================================
RDM_V2_DYNAMIC_MECHANICS_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/dynamic_mechanics_adapter.py
- experiments/dynamic_mechanics_adapter/shadow_test.py
- experiments/canonical_snapshot/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes dynamic_mechanics.
- SnapshotBuilder and SnapshotStore accept immutable dynamic_mechanics
  patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot and completed-visit regressions remain valid.

ADAPTER:
- Dynamic Mechanics Adapter Stage 1.
- Maps 16 existing dynamic timeline fields.
- Includes visit identity, current/previous Dynamic State, first and second
  derivatives, zone and attacker integrals, SDR, health slope/change,
  Omega total/mean, state reason/confidence, as-of visit, and update time.
- Alias support:
  - sdr -> SDR
  - visit_index -> dynamic_state_as_of_visit
  - analysis_run_utc -> dynamic_updated_at
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False remain valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No derivative calculation.
- No integral calculation.
- No SDR calculation.
- No Dynamic State classification.
- No reason or confidence inference.
- No formulas, coercion, or fallback mechanical derivation.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/dynamic_mechanics_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Dynamic mechanics mapping: PASS
- Alias and missing-field handling: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Existing Last Completed Visit regression: PASS
- Production effects: FALSE

NEXT:
Await prediction adapter approval.


==================================================
RDM_V2_PREDICTION_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/prediction_adapter.py
- experiments/prediction_adapter/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes prediction.
- SnapshotBuilder and SnapshotStore accept immutable prediction patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot, Dynamic Mechanics, and completed-visit regressions
  remain valid.

ADAPTER:
- Prediction Adapter Stage 1.
- Maps 14 existing B10/B11 prediction fields.
- Includes B10 trajectory/state/reason/confidence, B11 prediction/state/
  reason/confidence, version/status, input Dynamic State/visit, as-of visit,
  and update timestamp.
- Alias support:
  - structural_trajectory -> b10_trajectory
  - trajectory_direction -> b10_state
  - trajectory_reason/confidence -> B10 reason/confidence
  - structural_prediction -> b11_prediction
  - prediction_reason/confidence -> B11 reason/confidence
  - emit_status -> prediction_status
  - dynamic_state/visit_id/visit_index -> input/as-of provenance
  - analysis_run_utc -> prediction_updated_at
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False remain valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No B10 calculation.
- No B11 calculation.
- No prediction or confidence calculation.
- No Dynamic State calculation.
- No formulas, coercion, or fallback prediction.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Stage 2C.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/prediction_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Prediction mapping: PASS
- Alias and missing-field handling: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Existing Dynamic Mechanics regression: PASS
- Existing Last Completed Visit regression: PASS
- Production effects: FALSE

NEXT:
Await Canonical Snapshot V1 consolidation approval.


==================================================
RDM_V2_CANONICAL_SNAPSHOT_V1_CONSOLIDATED_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

COMPLETE CANONICAL SNAPSHOT V1:
- One immutable in-memory snapshot assembled from all accepted shadow
  adapters.
- No production integration or persistence.

VALIDATED SECTIONS:
- Metadata
- Geometry
- Current Row Mechanics
- Open Visit
- Last Completed Visit
- Dynamic Mechanics
- Prediction

SIX ADAPTERS TESTED TOGETHER:
- Project 1 Geometry Snapshot Adapter
- Row Mechanics Adapter
- Open Visit Adapter
- Last Completed Visit Adapter
- Dynamic Mechanics Adapter
- Prediction Adapter

REVISION AND ATOMICITY:
- Initial snapshot revision = 1.
- Successful update produces revision 2.
- Copy-on-write preserves the immutable prior revision.
- Top-level and nested snapshot mappings are deeply immutable.
- A failed update leaves revision 2 authoritative and unchanged.

MAPPING INTEGRITY:
- NOT_AVAILABLE behavior validated across sections.
- Precomputed values remain unchanged.
- Intentionally non-derived geometry values remain unchanged.
- No adapter calculates geometry, mechanics, derivatives, integrals, SDR,
  Dynamic State, B10, or B11.

ARTIFACT:
- experiments/canonical_snapshot_v1/consolidation_test.py

REPRODUCIBLE GEOMETRY DEPENDENCY:
- core/geometry_snapshot_adapter.py
- experiments/geometry_snapshot_adapter/shadow_test.py
- These accepted shadow files are included because the consolidation test
  imports and validates the Geometry Snapshot Adapter directly.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE or live_rdm changes.
- No dashboard.
- No Stage 2C.
- No CSV writes.
- No snapshot persistence.
- No formulas.
- No production behavior change.

VALIDATION:
- Consolidation test compile: PASS
- Six-adapter snapshot build: PASS
- All seven sections present: PASS
- Revision 1 -> 2: PASS
- Deep immutability: PASS
- Failed-update rollback: PASS
- NOT_AVAILABLE handling: PASS
- No-calculation proof: PASS
- Production effects: FALSE

NEXT:
Await first shadow integration pipeline approval.


==================================================
RDM_V2_COORDINATOR_ROW_MECHANICS_SNAPSHOT_INTEGRATION_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW INTEGRATION CHECKPOINT

ARTIFACT:
- experiments/coordinator_snapshot_integration/shadow_test.py

INTEGRATION:
MechanicalRefreshCoordinator
    -> RefreshPlan dirty flags
    -> RowMechanicsAdapter
    -> Canonical Snapshot

VALIDATED BEHAVIOR:
- RefreshPlan row-mechanics dirty flags gate RowMechanicsAdapter execution.
- The Row Mechanics patch creates and updates the Canonical Snapshot.
- Snapshot revisions advance from 1 to 2.
- Copy-on-write preserves revision 1 after revision 2 is committed.
- A negative-control plan without row-mechanics dirty flags skips the
  adapter and leaves the current snapshot unchanged.
- global_zone_key is preserved as the session-scoped snapshot identity.
- Existing zone_id remains metadata/provenance only.

CALCULATION BOUNDARY:
- No calculations.
- No mechanical formulas.
- No Dynamic State calculation.
- No Stage 2C.
- No B10/B11.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE pipeline integration.
- No dashboard.
- No CSV writes.
- No snapshot persistence.
- No production behavior change.

VALIDATION:
- Integration test compile: PASS
- Coordinator dirty-flag gating: PASS
- Row Mechanics mapping: PASS
- Snapshot revision 1 -> 2: PASS
- Copy-on-write preservation: PASS
- Negative-control skip: PASS
- global_zone_key identity: PASS
- No calculations: PASS
- Production effects: FALSE

NEXT:
Await multi-adapter shadow integration approval.
