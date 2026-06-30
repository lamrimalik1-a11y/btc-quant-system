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
PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE
==================================================

Date: 2026-06-06
Status: STABLE CHECKPOINT

WHAT HAPPENED:

A silent data corruption bug was discovered and fixed in
research/zone_mechanics_calculator.py inside build_zone_visit_timeline().

The bug caused fully-decayed EXHAUSTED_ZONE states to be misclassified
as RECLAIM or DAMAGE instead of BREAKDOWN, contaminating B12v2 outcome labels.

ROOT CAUSE:

Line 3628 (original):
    rig_v = to_float(last_row.get("rigidity_live")) or rig_birth

Python `or` treats 0.0 as falsy. For EXHAUSTED_ZONE (rig_birth=30.0,
zone_strength_decay>=50, recovery_current=0.0), the live rigidity formula
clamps the zone to exactly rigidity_live=0.0.

When 0.0 was fetched, `to_float()` correctly returned 0.0, but `or rig_birth`
silently replaced it with 30.0. The BREAKDOWN check then saw rig_v=30.0 and
found 30.0 < 15.0 = False, so BREAKDOWN never fired.

Three conditions make EXHAUSTED_ZONE exclusively vulnerable:
  1. rig_birth <= 30 (MEDIUM zone — BREAKDOWN threshold is 15.0)
  2. zone_strength_decay >= 50 (enough decay to reach 0.0)
  3. recovery_current = 0.0 (NO_RECOVERY — no repair to prevent floor)

THE FIX:

Single-line replacement (lines 3631-3632 after edit):

    _rig_raw = to_float(last_row.get("rigidity_live"))
    rig_v    = rig_birth if _rig_raw is None else _rig_raw

Explicit None-check: 0.0 (fully decayed) is preserved. None (missing data)
still falls back to rig_birth. Behavior unchanged for all non-EXHAUSTED cases.

IMPACT ON ZONE_VISIT_TIMELINE:

Effect A (RECLAIM → BREAKDOWN):
  13 visit_N outcomes that were RECLAIM are now correctly BREAKDOWN.
  B12v2 impact: 13 cases that were false FAILs (pred=FAIL, out=HOLD)
  became true positives (pred=FAIL, out=FAIL).

Effect B (DAMAGE → BREAKDOWN):
  Unexpected positive side effect: zones where fallback had given rig_v=30.0
  caused the classifier to fall to DAMAGE (not BREAKDOWN), which B12v2 mapped
  as AMBIGUOUS and excluded. After fix, BREAKDOWN fires first on all these.
  Formation: +17 newly evaluable correct FAILs
  Active Core: +13 newly evaluable correct FAILs
  Density Band: +7 newly evaluable correct FAILs

RESULTS — POST-FIX B12v2 VALIDATED:

  Mode           Evaluable  Accuracy  HOLD F1  FAIL F1  Lift
  Formation          650     98.8%    0.989    0.986   +42.3%
  Active Core        400     98.8%    0.989    0.986   +43.8%
  Density Band       263     98.5%    0.986    0.983   +43.3%

All modes: LEAKAGE PASS, CONSISTENCY PASS, INTEGRITY PASS.

Remaining false HOLDs: 3 identical cases across all modes
  — STABLE trajectory / EXHAUSTED_ZONE / HEALTH_STABLE
  — Same 3 zones — different failure mode (not the fallback bug)

Remaining false FAILs after fix:
  Formation: 5 (4x EXHAUSTED_ZONE rig_birth>30, 1x RIGID_ZONE ABSORPTION)
  Active Core: 2 (EXHAUSTED_ZONE DEGRADING)
  Density Band: 1 (EXHAUSTED_ZONE DEGRADING)

INTERPRETATION:

The fix corrected a classification bug, not a formula. No RDM physics changed.
The B12v2 engine now sees correct structural states: zones that fully decayed
(rigidity=0.0) are correctly labeled BREAKDOWN. The accuracy improvement from
~97.2% to 98.8% (Formation) is entirely attributable to removing misclassified
outcomes from the ground truth — not from improving the prediction model.

ARCHITECTURE PRESERVED:

No formula changes.
No Phase 1 production file changes.
No RDM formula changes.
No B9/B10/B11/Synthesis changes.
No lifecycle logic changes.
No replay formula changes.
No dashboard changes.

CURRENT PROJECT STATUS:

B12v2 is validated at 98.8% prospective accuracy (Formation mode) across a
34-day dataset (Apr 30 – Jun 2, 2026). All three zone modes confirmed.
Physics correlation (sigma x penetration r=0.9953) intact.
Leakage-free architecture confirmed.

Repository: CLEAN. Commit: PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE.

NEXT RESEARCH CANDIDATE:

PHASE1B_EXHAUSTED_ZONE_RESEARCH

Goal: Characterize the remaining error concentration in EXHAUSTED_ZONE.
  - False HOLDs: 3 cases — STABLE trajectory / HEALTH_STABLE / EXHAUSTED_ZONE
    (B10 calls these STABLE even though they eventually breakdown — why?)
  - False FAILs: 4 Formation cases — EXHAUSTED_ZONE with rig_birth > 30
    (BREAKDOWN threshold of rig_birth*0.50 not reached because rig_birth > 30)
  - Question: Is STABLE trajectory in EXHAUSTED_ZONE a systematic B10 error
    or a genuine edge case (zone that was stable until a sudden event)?

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
