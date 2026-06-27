# Current Checkpoint

## Active Checkpoint

Checkpoint: PHASE1B_B125_AUTOTRIGGER_STABLE

What this checkpoint adds:
- B12.5 now fires AUTOMATICALLY on every new zone detection
  (score >= 4), wired into core/live_rdm.py inside
  compute_live_rdm_for_case(), immediately after _persist_record().
  Wrapped in try/except: pass so a B12.5 failure never blocks the
  main live pipeline. Runtime confirmed <2s.
- dashboard_live_zones.py filter changed from "last N hours" to
  calendar-day selector: Today / Yesterday / Last 3 days
  (default: Today, Algeria midnight as boundary)
- Auto-refresh tightened: cache TTL 10s, fragment run_every 15s
  (was 30s/60s) — new zones appear on dashboard within 15s with
  zero manual action
- Diagnostic command if auto-trigger silently fails:
    python -c "from research.zone_mechanics_calculator import
    run_zone_visit_timeline_dynamic_live as r1,
    add_dynamic_layers_to_timeline_live as r2; r1(); r2();
    print('Manual B12.5 OK')"

Dashboard architecture (two separate apps, run independently):
  dashboard_app.py            -> full historical archive (default port)
  dashboard_live_zones.py     -> today's active zones only (port 8502)
    Focus: Density Bands as decision zone, Active Core as context,
    Preparation Zone in expander only. Plain-language WHY reasoning
    per card (reuses _classify_dynamic_state rules). Expandable visit
    history with outcome tracking (what_happened_next per visit).

Run commands:
  powercfg /change standby-timeout-ac 0
  python -m engines.stream_manager
  streamlit run dashboard_app.py
  streamlit run dashboard_live_zones.py --server.port 8502

Next steps:
  - Run LIVE continuously for extended period (days) to accumulate
    enough post-return visits for meaningful dynamic_state validation
  - Once sufficient LIVE post-return data exists, compare LIVE vs
    REPLAY dynamic_state distributions
  - Consider B13 (Markov transition engine) once B12.5 is validated
    on LIVE data

---

## Prior Checkpoint: PHASE1B_B125_LIVE_DASHBOARD_STABLE

What this checkpoint added:
- B12.5 wired into LIVE pipeline (run_zone_visit_timeline_dynamic_live,
  add_dynamic_layers_to_timeline_live) — uses fixed REPLAY-calibrated
  thresholds for LIVE/REPLAY comparability
- New file: research/live_zone_visit_timeline_dynamic.csv
- New standalone dashboard: dashboard_live_zones.py (port 8502)
  - Shows only zones active in last N hours (configurable, default 24)
  - One card per zone, focused on Density Bands as the decision zone
    (Active Core shown as context only, Preparation Zone moved to
    expander)
  - Plain-language prediction reasoning per card (reuses
    _classify_dynamic_state rules, does not duplicate logic)
  - Expandable "More Information": full visit history with
    outcome tracking (what_happened_next per visit)
  - Algeria timezone throughout, auto-refresh every 60s + manual button
- Existing dashboard_app.py (research/stream view) UNCHANGED, runs on
  default port, still shows full historical archive

LIVE data status (as of this checkpoint):
- 3 days collected (Jun 17-19) on @aggTrade stream, with gaps
  (stream not yet run continuously)
- 50 unique returning zones, 8 post-return visits, mostly NO_DATA/
  PROBABLE_HOLD (insufficient post-return history yet)

---

## Prior Checkpoint: PHASE1B_B125_DYNAMIC_TIMELINE_STABLE

What this checkpoint added:
- B12.5 Full Post-Return Visit Timeline Engine (3 stages)
- zone_visit_timeline_dynamic.csv: 14,512 rows, 2,980 returning zones
- Dynamic state classification: SDR-led rules, 86.6% accuracy
- Physics confirmed: SDR >= 1 → 99.6% FAIL (deterministic)
- Gold tier: STRONG_HOLD → 100% HOLD (743 cases)
- ATTACKER_DOMINANT → 99.6% FAIL (528 cases)

B12.5 Three stages:
  Stage 1: Extended live_row_window by 500 post-return rows (hard cap)
           zone_live_rdm_evolution: 1.8M → 3.3M rows
  Stage 2: Built zone_visit_timeline_dynamic.csv
           14,512 post-return visits across 2,980 zones
  Stage 3: Added derivative + integral + SDR + dynamic_state
           Calibrated percentile-based thresholds from pre-return data

Dynamic state accuracy (vs B12v2 outcomes, n=2,430):
  STRONG_HOLD       → 100.0% HOLD  (n=743)
  ATTACKER_DOMINANT → 99.6%  FAIL  (n=528)
  STABLE            → 91.6%  HOLD  (n=383)
  PEAK_WARNING      → 100.0% FAIL  (n=40)
  RECOVERING        → 100.0% FAIL  (n=26)
  CRITICAL          → 100.0% FAIL  (n=8)
  DEGRADING         → 88.1%  FAIL  (n=42)
  PROBABLE_HOLD     → 56.5%  FAIL  (n=657) <- needs refinement
  Overall accuracy: 86.6% (was 74.4% before calibration)

Mathematical layers per visit:
  first_derivative  = health(k) - health(k-1)
  second_derivative = first_derivative(k) - first_derivative(k-1)
  slope_short       = regression slope over last 2 visits
  slope_medium      = regression slope over last 3-5 visits
  zone_integral     = I(k-1) * 0.98 + health(k)
  attacker_integral = I(k-1) * 0.98 + attacker_force(k)
  SDR               = attacker_integral / zone_integral

Calibrated thresholds (percentile-based, from pre-return data):
  slope_pos=3.894, slope_neg=-1.248,
  integral_high=410.68, integral_low=76.85, sdr_high=1.079

Prior checkpoints (preserved):
  - PHASE1B_UNIFIED_ARCHIVE_STABLE
  - PHASE1B_STREAMING_REPLAY_STABLE
  - PHASE1B_B12_LIVE_VALIDATION
  - PHASE1B_SYNTHESIS_ENGINE_STABLE

---

---

## Active Checkpoint: PHASE1B_RDM_V2_MECHANICAL_ARCHITECTURE_STABLE

Status: STABLE RESEARCH CHECKPOINT

This checkpoint consolidates the current RDM V2 mechanical architecture after Stage 5H.

Included stages:
- Stage 5D Dynamic State signature analysis
- Stage 5E transition analysis
- Stage 5F transition family discovery
- Stage 5G attacker force causality analysis
- Stage 5H mechanical dependency graph

New spec:
- docs/RDM_V2_MECHANICAL_ARCHITECTURE_SPEC.md

Stage 5H graph summary:
- 49 variables classified
- 113 dependency edges
- 21 dependency layers
- max dependency depth = 20
- direct dependency loops = 0

Core conclusion:
The implemented mechanical engine is feed-forward at artifact-generation time. It has temporal memory through integrals, guards, health evolution, sigma evolution, and structural damage, but no same-step algebraic dependency loop was confirmed.

Important research conclusions:
- Stage 2C acute pressure + chronic structural damage is mechanically superior to frozen post-return behavior.
- ATTACKER_DOMINANT has a distinct mechanical signature and is the strongest continuation-bearing Dynamic State so far.
- STABLE / PROBABLE_HOLD are more rejection-biased.
- Attacker Force and Omega are common first movers.
- Fatigue is the clearest deterioration precursor.
- Attacker Force is interaction-conditioned, not raw-delta-only.

Project state:
- Project 1 remains Phase 1B+ research expansion.
- Project 2 has not begun; when approved, it should replace only the Geometry Engine while reusing replay, statistics, dashboard, research infrastructure, and validation methodology.

Rules:
No Phase 2, no Footprint, no execution, no entries/exits, no BUY/SELL, no live signals, no scoring changes, no RDM formula changes, no Dynamic State threshold changes.


---

## Active Checkpoint: RDM_V2_EVENT_DRIVEN_SHADOW_FOUNDATION

Status: VALIDATED SHADOW CHECKPOINT

Purpose:
Create an explicit event-driven RDM V2 foundation without changing
production behavior.

Components:
- Interaction Interpreter:
  market row + geometry -> deterministic MechanicalEvent records.
- Mechanical Refresh Coordinator:
  InteractionState + events -> dirty flags -> ordered RefreshPlan.
- Shadow Chain Test:
  deterministic end-to-end validation with zero mismatches.

Supported shadow events:
TOUCH, ZONE_ENTER, ZONE_EXIT, RETURN, PENETRATION_UPDATED,
VISIT_STARTED, VISIT_COMPLETED.

Validation:
- Requested modules compile: PASS
- Shadow chain test: PASS
- Deterministic replay: PASS
- Mismatches: NONE
- Production effects: FALSE

Isolation:
Shadow mode only. No production or LIVE consumer, no RDM execution,
no Stage 2C integration, no snapshots, no dashboard changes, and no
formula or Dynamic State changes.

Next:
Await architectural decision before production integration.


---

## Active Checkpoint: RDM_V2_EVENT_DRIVEN_BACKBONE_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Shadow backbone:

```text
Interaction Interpreter
    -> Event Dispatcher
    -> Mechanical Refresh Coordinator
```

Responsibilities:
- Interpreter: market row + geometry -> normalized MechanicalEvent records.
- Dispatcher: identity/order validation, event-ID deduplication, atomic
  shadow batch delivery.
- Coordinator: events -> dirty flags -> ordered RefreshPlan.

Validation:
- Valid ordered dispatch: PASS
- Duplicate/replayed IDs: PASS
- Invalid order rejection: PASS
- Zone mismatch rejection: PASS
- Shadow coordinator plan: PASS
- Production effects: FALSE

Boundary:
All three components are shadow-only. No production consumer, LIVE
integration, RDM execution, Stage 2C, Dynamic State, dashboard, snapshot,
or runtime file writes were added.

Next:
Await Canonical Snapshot implementation approval.
