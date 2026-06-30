# ChatGPT Project Context

## Active Checkpoint: RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Last Completed Visit Adapter Stage 1 (shadow-only):
- **Extended the existing adapter additively** (committed aefec1c) — existing
  target names/behavior untouched; dependent consolidation test stays green.
- **Maps existing completed-visit fields into the Canonical Snapshot
  "last_completed_visit" section** (projection only, no rebuild, no inference).
- **Adds `max_penetration_ratio` and `defender_state`** (plus `visit_start_price`
  / `visit_end_price`) as new mapped target fields.
- **Supports aliases** (first present/available alias wins, primary names first):
  completed_visit_id, visit_max_penetration, visit_max_penetration_ratio,
  visit_final_omega, visit_attacker_force, visit_defender_state,
  visit_health/rigidity/capacity/fatigue/recovery.
- **NOT_AVAILABLE behavior** for absent / None / empty / NaN (no defaulting),
  recorded in source_fields.
- **No calculations** (no Dynamic State, derivatives, integrals, SDR, Stage 2C,
  B10, B11, dashboard, CSV writes, persistence).
- **Snapshot compatibility** validated.
- **No production behavior changed** (no importer outside shadow tests).

Validation (all pass): py_compile adapter + test OK; extended shadow test PASS;
consolidation test PASS; git diff --check clean.

Next: Dynamic Mechanics Adapter approval.

---

## Active Checkpoint: RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED

Status: ACCEPTED CONTRACT — architecture decision only. NO code implemented,
no production code changed.

Restart / Durability Contract:
- **The append-only ordered row log is the source of truth** (per session_id;
  each row carries global_zone_key and the geometry_version in effect).
- **Persist-before-process:** durably append the row BEFORE InteractionState
  advances from it -> an open visit is always replayable.
- **Rebuild-from-history is the primary recovery mechanism** (restart = replay
  rows through interpret_in_order; rebuild InteractionState + SnapshotStore).
- **The snapshot is a cache / projection only — never the source of truth.**
- **Watermark = InteractionState.previous_row_index** is the single recovery
  anchor (same single source of truth as the Row Ordering Contract).
- **Geometry-in-effect must be pinned** (geometry_version + bounds) or replay
  diverges.
- **Checkpoints are an optimization, not correctness** (carry cumulative
  counters: revision, active_visit_index, completed_visit_count, return_count,
  guard/breach state).

Primary (must persist): ordered row log, session_id, global_zone_key,
geometry-in-effect. Everything else is DERIVED and rebuildable from history.

No production code changed (documentation/design only).

Next: Restart / Durability implementation decision.

---

## Active Checkpoint: RDM_V2_ROW_ORDERING_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Row Ordering Contract in the Interaction Interpreter:
- New **interpret_in_order()** enforces row ordering BEFORE any transition;
  delegates to the existing pure **interpret()** only on accept.
- New **OrderingResult** (status + audit + state + events).
- Statuses: **ORDER_ACCEPTED**, **ROW_DUPLICATE**, **ROW_OUT_OF_ORDER**.
- **InteractionState remains the single ordering watermark** (previous_row_index).
- **No dispatcher watermark. No coordinator watermark.**
- **row_index is authoritative; timestamp is informational only** (equal
  timestamps with increasing row_index remain valid).
- **No events are emitted for duplicate / out-of-order rows** (audit code only);
  unchanged input state returned on rejection.
- **Existing interpret() remains unchanged.**
- No production behavior changed (interaction_interpreter is shadow-only).

Validation (all pass): py_compile of core + both shadow tests OK; existing
interpreter shadow test PASS; new row ordering shadow test PASS (all 6 cases);
full shadow-suite regression (11 tests) PASS; git diff --check clean.

Next: Restart / Durability Contract review.

---

## Active Checkpoint: RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

- Canonical Snapshot identity is now **global_zone_key**.
- zone_id is descriptive metadata only (no longer determines identity).
- SnapshotStore is keyed by global_zone_key (was: bare zone_id).
- Session-scoped identity now matches the Event Dispatcher identity contract.
- Snapshot revision model unchanged; copy-on-write unchanged; sections unchanged.
- Production behavior unchanged (canonical_snapshot is shadow-only; only
  experiment shadow tests import it).

Validation (all pass): py_compile OK; all 8 Canonical Snapshot / adapter shadow
tests PASS; identity-collision shadow test PASS (same zone_id reused across
Session A = BTCUSDT_2026-06-28_230000Z::SNAPSHOT_ZONE_1 and
Session B = BTCUSDT_2026-06-29_230000Z::SNAPSHOT_ZONE_1 -> two independent
snapshots, no collision, no overwrite); git diff --check clean.

Next: Row Ordering Guard architectural review.

---

Current stable checkpoint:

`PHASE1B_LIVE_ZONE_ENGINE_STABLE`

Commit:

`(see below)`

Prior stable checkpoint:

`PHASE1B_RDM_VISUALIZATION_STABLE` — commit `f818d5f`

Status:

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

## Latest Stable Work

### Preparation Watch Fix

- Research coverage expanded from `93` rows to `634` rows.
- Current replay / research coverage: `2026-05-25 -> 2026-06-01`.
- Preparation candidates: `338`.
- Research coverage is now `100%` across the replay episode set.

### RDM Coverage Fix

- RDM coverage increased from `35.48%` to `100%`.
- `634 / 634` Dashboard V2 episodes are mapped.
- The previous `None` / `N/A` coverage issue for mapped RDM fields is resolved.

### Dashboard Improvements

- Show All controls added.
- Row limit controls added.
- Date filters added.
- Sort order controls added.
- Preparation Watch supports multi-day research rows.
- Dashboard V2 Research Mapping panels support multi-day rows across:
  - PREPARATION
  - EXPANSION
  - REVERSAL
  - COMPARISON
  - HYPOTHESIS

### Timezone Support

- Algeria timezone display support added: `UTC+1`.
- UTC display remains available.
- This is display-only.
- Stored timestamps, replay data, research data, and calculations remain unchanged.

### RDM Mapping Fix

- `resistance_live` mapping added.
- Dashboard RDM fields now map to regenerated full research / RDM coverage.

### RDM Price Overlay

New dashboard component:

`RDM Price Overlay - Research Only`

Uses existing fields only:

- Formation Range
- Active Core
- Interaction Density Band
- Birth Price

Display:

- Absolute BTC price axis
- Nested horizontal price bands
- Birth price reference line
- Reference table with exact lower / upper / width values
- Core / Formation ratio
- Density / Formation ratio

No calculations were changed.

## Important RDM Visualization Discovery

Formation Range
!=
Active RDM Zone
!=
Interaction Density

Current interpretation:

- Formation = Context
- Active Core = Operational Zone
- Density = Interaction Heart

Binance comparison observation:

Active Core and Density Band appear to match the real market zone better than the full Formation Range.

This is an observation only. It is not a signal and not a trading rule.

## Episode 622 Validation

Episode:

- `episode_id`: `622`
- `case_id`: `CASE_00622`
- `episode_start_time_utc`: `2026-06-01 08:42:27`
- Algeria time: `2026-06-01 09:42:27`

Birth Price:

`72698.42`

Formation:

- Lower: `72612.24`
- Upper: `72864.36`
- Width: `252.12`

Active Core:

- Lower: `72787.66`
- Upper: `72850.70`
- Width: `63.03`

Density Band:

- Lower: `72823.68`
- Upper: `72832.69`
- Width: `9.00`

Ratios:

- Core / Formation: `0.2500`
- Density / Formation: `0.0357`

## What Did Not Change

- RDM formulas
- Dashboard scoring
- Dashboard V2 scoring
- Replay generation
- Research logic
- Downloads
- Binance pulls
- Live execution
- Signal logic

## RDM V1.6 — Completed Series

### V1.6-A Numerical Foundation

Status: COMPLETED

- 42 new `rdm_v16_*` columns
- Birth / Current / Live / Final metrics for all structural families

### V1.6-B1 through B7.7 — Attacker and Exposure Physics

Status: COMPLETED

Key validated finding:

```
sigma_at_return × zone_penetration_depth ≈ omega_stress_area
r = 0.9935
```

Omega is the primary Deep Structural Exposure variable.

Structural engagement chain:

```
Force → sigma_barre filter → Penetration → Omega → mechanical_family → Growth or Damage
```

sigma_barre is driven by structural memory (reclaim_history, mechanical_memory_score) — NOT by force.

Surface Damage hypothesis (B7.6-E/F): REJECTED. Zero-omega damage is time-based temporal decay.

### Downloader Stability Fix

Status: COMPLETED

- Timeout: 120s -> 150s
- Retries: 10 -> 15
- Extended backoff, jitter, WinError 10060 detection
- Session retry tracking, resume deduplication
- New CLI: `--max-retries`, `--timeout`

## 3-Tier Hybrid Downloader

Status: COMPLETED

Tier 1 (local cache) + Tier 2 (Binance ZIP) + Tier 3 (API fallback).

Priority per UTC day:

1. archives/{SYMBOL}/raw-trades/{date}.csv -> CACHE HIT (zero network)
2. data.binance.vision ZIP (date >= 2 days old) -> ZIP HIT -> save to cache
3. Binance aggTrades API -> API DOWNLOAD -> save to cache

Key: Binance ZIP timestamps are microseconds. Converted to milliseconds (// 1000) inside download_day_from_binance_zip.

Validated: BTCUSDT 2026-05-25 — 542,386 trades, 7.7 MB, 2.7 sec via ZIP.

New CLI: --no-local-cache, --no-zip

Standard command:

python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500

Use --slow-mode only for recent-date API fallback on unstable networks, not for historical downloads.

## Phase 1 Synthesis Engine

Status: COMPLETED

File:    research/synthesis_engine.py (NEW)
Output:  research/zone_synthesis.csv (276 rows, 13 columns)

Phase 1 is now structurally coherent. The Synthesis Engine connects all
Phase 1 layers (Statistical Engine, Dashboard V2, RDM B1-B11) into one
MarketInterpretation per zone case:

    context | structure | engagement | flow | prediction | coherence | interpretation

Architecture (6 components, minimal professional version):
    Taxonomy Register (role + scope per field)
    Bundle Assembler (B10 + B11 + episode context)
    Priority Rules (STRUCTURAL > CURRENT, STRUCTURE > CONTEXT)
    Genuine Conflict Check (binary flag)
    3-Gate Synthesis Check
    4-Level Coherence Label (STRONG / MODERATE / WEAK / INSUFFICIENT)

Example: "TERMINAL zone under opposing flow - failure confirmed."
Example: "STRENGTHENING zone after 3 visits - hold confirmed."

## Current Active Phase

PHASE 1B+ Research Expansion

Current checkpoint: PHASE1B_SYNTHESIS_ENGINE_STABLE

Prior checkpoints:
- PHASE1B_HYBRID_DOWNLOADER_STABLE
- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE

Rules preserved:
- No scoring changes
- No lifecycle changes
- No Dashboard V2 scoring impact
- No RDM formula changes
- No replay formula changes
- No Phase 2 / No execution / No entries / No live signals

Next task: 45-60 day data collection, then B12 prediction validation.

Do not advance to Phase 2.


---

## PHASE1B_LIVE_ZONE_ENGINE_STABLE

DATE: 2026-06-09

STATUS: STABLE

### Objective Achieved

Full LIVE Zone Engine operational from V2 Episode generation through LIVE structural prediction.

### Completed

**LIVE V2 Episodes**
- LIVE episode closure, dashboard integration, episode persistence, score4+ parity validation

**Preparation Engine**
- LIVE Preparation snapshots, replay parity validation
- Score4+ filter enforced: peak_layer_count >= 4 required
- Preparation Watch dashboard panel

**Lifecycle Engine**
- ZoneLifecycleMemory, FieldLifecycleMemory
- LIVE events: zone_created, zone_tested, zone_rejected, zone_reclaimed, expansion_state, reversal_state, hypothesis02_state

**Return Detection Engine**
- Streaming return detection, replay parity validation
- Formation-bound detection, CLOSE-only parity with replay
- Pending zone registry, return_found tracking

**Two-Phase Emit Architecture**

PENDING_FINALIZATION (immediate, at return_found=True):
- Group A, Group B, B8, B9, B10, B11, Synthesis

FINALIZED_OUTCOME (after both 4h windows):
- future moves, reversal_type, expansion_type, failed_after_return, max_move_after_return

**RDM LIVE** — Group A, Group B, RDM evolution, Attacker evolution, Timeline, Health evolution

**B10** — Structural trajectory

**B11** — Structural prediction

**Synthesis** — Structural interpretation, prediction reasoning

**Geometry**

| Layer | Fields |
|---|---|
| Formation | preparation_low/high/mid_price |
| Tight Formation | tight_formation_low/high/mid_price |
| Active Core | interaction_core_lower/upper_edge, mid_price, width |
| Density Band | interaction_density_lower/upper_band, weighted_center, width |

**Dashboard** — 8 LIVE panels: V2 Episodes, Preparation Watch, Lifecycle Watch, Return Detection, RDM Status, B10 Trajectory, B11 Prediction, Synthesis

### Validation Status

Preparation: PASS | Lifecycle: PASS | Return Detection: PASS | RDM: PASS | B10: PASS | B11: PASS | Synthesis: PASS

Unexplained divergences: ZERO

### Architectural Decisions

- Return Detection: Formation bounds only (close >= zone_low and close <= zone_high). Wick touches ignored.
- Active Core and Density Band: display-only geometry. Do NOT participate in return detection.
- Score4+ parity: LIVE mirrors replay. peak_layer_count < 4 blocked before Preparation processing.

### Current Live Status

LIVE system healthy. No active bug.

After restart: 4 V2 episodes observed, 0 score4+ episodes, 0 preparation zones.
Market has not yet produced a qualifying score4+ episode.

System waiting for: peak_layer_count >= 4 followed by valid Preparation candidate.

### Next Step

Observe LIVE market. Wait for:
1. score4+ episode
2. valid Preparation candidate
3. return_found
4. first PENDING_FINALIZATION record
5. first Active Core
6. first Density Band
7. first LIVE B11 prediction

Stop here. Do NOT start Footprint. Do NOT start Microstructure. Do NOT start Regime Engine.

### Rules

- No Phase 2. No execution. No BUY/SELL.
- Do NOT change Phase1B formulas.
- Do NOT change RDM formulas.
- Do NOT modify B11/B12v2 logic.
- Do NOT download data without explicit request.

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
