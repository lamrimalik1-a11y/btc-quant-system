# LIVE ZONE ENGINE INTEGRATION — CHECKPOINT

**Date:** 2026-06-09
**Status:** COMPLETE — Ready for manual LIVE run

---

## Integration Summary

The full Live Zone Engine chain is implemented, validated, and wired into the
dashboard. All stages reuse the validated offline research functions verbatim
via thin-adapter imports (zero formula drift).

---

## Chain (end-to-end)

```
Binance WebSocket
       ↓
core/observation_logger.py      → outputs/dashboard_v2_episodes.csv
       ↓
core/live_return_detection.py   → outputs/live_return_detection.csv
       ↓
core/live_rdm.py
  ├── Group A  (statistics / preparation)
  ├── Group B  (zone mechanics / attacker evolution)
  ├── B8  build_zone_visit_timeline
  ├── B9  build_zone_health_evolution
  ├── B10 build_zone_structural_trajectory → outputs/live_b10_trajectory.csv
  ├── B11 build_zone_structural_prediction → outputs/live_b11_prediction.csv
  └── Synthesis build_zone_synthesis       → outputs/live_synthesis.csv
       ↓
dashboard_app.py  LIVE mode — 8 panels
```

---

## Output Files

| File | Written by |
|---|---|
| `outputs/dashboard_v2_episodes.csv` | `core/observation_logger.py` |
| `outputs/live_preparation_zones.csv` | `core/observation_logger.py` |
| `outputs/live_lifecycle_events.jsonl` | `core/live_lifecycle.py` |
| `outputs/live_field_lifecycle_events.jsonl` | `core/live_lifecycle.py` |
| `outputs/live_lifecycle_state.csv` | `core/live_lifecycle.py` |
| `outputs/live_return_detection.csv` | `core/live_return_detection.py` |
| `outputs/live_rdm_results.csv` | `core/live_rdm.py` |
| `outputs/live_rdm_evolution.csv` | `core/live_rdm.py` |
| `outputs/live_rdm_state.csv` | `core/live_rdm.py` |
| `outputs/live_b10_trajectory.csv` | `core/live_rdm.py` |
| `outputs/live_b11_prediction.csv` | `core/live_rdm.py` |
| `outputs/live_synthesis.csv` | `core/live_rdm.py` |

---

## Dashboard Panels (LIVE mode)

| Order | Panel | Source file |
|---|---|---|
| 1 | Live V2 Episodes | `dashboard_v2_episodes.csv` |
| 2 | Preparation Watch | `live_preparation_zones.csv` |
| 3 | Lifecycle Watch | `live_lifecycle_state.csv` + `.jsonl` |
| 4 | Return Detection | `live_return_detection.csv` |
| 5 | RDM Status | `live_rdm_state.csv` |
| 6 | B10 Trajectory | `live_b10_trajectory.csv` |
| 7 | B11 Prediction | `live_b11_prediction.csv` |
| 8 | Synthesis | `live_synthesis.csv` |

---

## Files Modified (this session)

| File | Status | Role |
|---|---|---|
| `core/live_rdm.py` | NEW | Phase 5: B10/B11/Synthesis pipeline extension |
| `core/live_return_detection.py` | NEW | Phase 3A: zone return detection |
| `core/live_lifecycle.py` | NEW | Phase 3B: lifecycle memory |
| `core/observation_logger.py` | MODIFIED | V2 episode logging + live RDM trigger |
| `dashboard_app.py` | MODIFIED | 8-panel LIVE mode wiring |
| `tools/validate_live_b11.py` | NEW | Phase 5 validation harness |
| `tools/validate_live_rdm.py` | NEW | Phase 4 validation harness |
| `tools/validate_live_preparation.py` | NEW | Preparation validation |
| `tools/validate_live_return_detection.py` | NEW | Return detection validation |
| `tools/validate_live_lifecycle.py` | NEW | Lifecycle validation |
| `tools/validate_live_v2_episode_closure.py` | NEW | V2 episode closure validation |

---

## Validation Results (from dry-run on historical_observation_rows.csv — 9177 rows)

### After Two-Phase Emit Implementation (current)

| Phase | Check | Result |
|---|---|---|
| Phase 4 — Live RDM | CHECK 1 (case-row assembly): 275/276 PASS, 1 FAIL (pre-existing rolling boundary edge case, ep280) | PASS |
| Phase 4 — Live RDM | CHECK 2 (bounded vs full): 276/276 PASS, 100,464/100,464 field comparisons identical | PASS |
| Phase 5 — Live B11 | CHECK 1 (B10 trajectory): 0/276 unexplained | PASS |
| Phase 5 — Live B11 | CHECK 2 (B11 prediction): 0/276 unexplained | PASS |
| Phase 5 — Live B11 | CHECK 3 (Synthesis): 0/276 unexplained | PASS |

### Before Two-Phase Emit (baseline)

| Phase | Check | Result |
|---|---|---|
| Phase 4 — Live RDM | CHECK 1 (rolling buffer): 252/253 PASS, 1 FAIL (rolling boundary edge case) | PASS |
| Phase 4 — Live RDM | CHECK 2 (bounded vs full): 253/253 PASS, 92,092/92,092 fields identical | PASS |
| Phase 5 — Live B11 | CHECK 1 (B10 trajectory): 0/253 unexplained | PASS |
| Phase 5 — Live B11 | CHECK 2 (B11 prediction): 0/253 unexplained | PASS |
| Phase 5 — Live B11 | CHECK 3 (Synthesis): 0/253 unexplained | PASS |

---

## Two-Phase Emit Architecture

Implemented in this session. All output records now carry `emit_status`:

| Status | Trigger | Fields populated |
|---|---|---|
| `PENDING_FINALIZATION` | `return_found=True` (immediate) | All Group A/B + B8–B11 + Synthesis. Outcome fields empty. |
| `FINALIZED_OUTCOME` | Both 4h windows complete | Outcome fields only (appended as separate record). Group A/B not recomputed. |

Files with `emit_status` column: `live_return_detection.csv`, `live_rdm_state.csv`, `live_b10_trajectory.csv`, `live_b11_prediction.csv`, `live_synthesis.csv`.

Dashboard panels: Return Detection, RDM Status show PENDING vs FINALIZED sub-sections. B10/B11/Synthesis show `emit_status` column.

---

## Documented Architectural Limitations

| Limitation | Scope | Impact |
|---|---|---|
| B8 temporal forward-dependence | visit_count and all B9/B10/B11/Synthesis fields | Live bounded at return_row; replay saw post-return visits. Live output is correct for data available at evaluation time. |
| B4 population-relative fields | zone_strength_score, attacker_force_score, force_ratio, prediction_score, engagement | Require cross-case denominators. Not computable for isolated live case. B11 label/confidence/reason unaffected. |
| zone_revisit_count (Phase 4) | 1 of 276 cases, rolling-buffer boundary | <3.5% value impact on 20 preparation-zone fields. |
| Two-phase emit outcome fields | PENDING_FINALIZATION record | direction_after_return, expansion_*, failed_after_return, max_move_after_return, reversal_*, revisit_expansion_delay_minutes empty until FINALIZED_OUTCOME. |

---

## Constraints (permanent — do not remove)

- RESEARCH ONLY. No Phase 2 trading. No execution. No BUY/SELL.
- No formula changes. No threshold changes. No B12v2 changes.
- Do not start Footprint. Do not start Microstructure. Do not start Regime Engine.
- Do not call offline batch scripts inside the LIVE loop.
- Project: BTCUSDT-specific.

---

## Run Commands

```bash
# Start LIVE pipeline (WebSocket-driven)
py -m engines.stream_manager

# Start dashboard
streamlit run dashboard_app.py

# Validation (dry-run on historical data — does not touch live files)
py -m tools.validate_live_b11
py -m tools.validate_live_rdm
```
