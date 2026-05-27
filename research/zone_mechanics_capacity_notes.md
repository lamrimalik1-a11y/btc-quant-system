# Zone Mechanics Capacity Notes

- Run UTC: 2026-05-27T10:48:55+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 12
- ELU_LIMIT: 3
- CAPACITY_FAILURE: 2
- ELS_LIMIT: 1
- WARNING: 7
- HIGH_LOAD: 2

## Dynamic ELU State Counts
- ELS_SAFE: 11
- ELU_LIMIT: 3
- CAPACITY_FAILURE: 2
- ELS_LIMIT: 1
- WARNING: 7
- SAFE: 1
- HIGH_LOAD: 2

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 21
- EXPANSION_EXHAUSTION_CONTEXT: 3
- RUPTURE_CONTEXT: 2
- RECOVERY_CONTEXT: 1

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 11
- EXPANSION_PROTECTED: 3
- RUPTURE_CONFIRMED: 2
- RECOVERY_PROTECTED: 11

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
