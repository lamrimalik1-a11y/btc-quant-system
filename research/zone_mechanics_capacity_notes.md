# Zone Mechanics Capacity Notes

- Run UTC: 2026-05-26T22:10:18+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- CAPACITY_FAILURE: 5
- ELS_LIMIT: 1
- ELU_LIMIT: 4
- WARNING: 1
- SAFE: 1

## Dynamic ELU State Counts
- CAPACITY_FAILURE: 5
- ELU_LIMIT: 6
- SAFE: 1

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 7
- EXPANSION_EXHAUSTION_CONTEXT: 3
- RUPTURE_CONTEXT: 1
- RECOVERY_CONTEXT: 1

## Capacity Calibration State Counts
- ADAPTIVE_NORMAL: 5
- EXPANSION_PROTECTED: 5
- RUPTURE_CONFIRMED: 1
- RECOVERY_PROTECTED: 1

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
