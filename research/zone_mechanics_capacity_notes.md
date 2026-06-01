# Zone Mechanics Capacity Notes

- Run UTC: 2026-06-01T15:12:02+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 424
- WARNING: 129
- ELU_LIMIT: 61
- HIGH_LOAD: 20

## Dynamic ELU State Counts
- ELS_SAFE: 297
- WARNING: 129
- ELU_LIMIT: 61
- SAFE: 127
- HIGH_LOAD: 20

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 509
- EXPANSION_EXHAUSTION_CONTEXT: 80
- RECOVERY_CONTEXT: 45

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 297
- RECOVERY_PROTECTED: 276
- EXPANSION_PROTECTED: 61

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
