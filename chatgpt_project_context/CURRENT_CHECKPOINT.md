# Current Checkpoint

## Active Checkpoint

Checkpoint: PHASE1B_B125_LIVE_DASHBOARD_STABLE

What this checkpoint adds:
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
- Next: run LIVE continuously for extended period to accumulate
  enough post-return visits for meaningful LIVE vs REPLAY comparison

Commands to run both dashboards simultaneously:
  streamlit run dashboard_app.py
  streamlit run dashboard_live_zones.py --server.port 8502

Live stream command:
  python -m engines.stream_manager
  (prevent sleep first: powercfg /change standby-timeout-ac 0)

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
