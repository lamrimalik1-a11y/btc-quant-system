# Zone Mechanics Capacity Notes

- Run UTC: 2026-06-05T21:47:45+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 550
- ELU_LIMIT: 326
- WARNING: 208
- HIGH_LOAD: 129
- ELS_LIMIT: 6

## Dynamic ELU State Counts
- ELS_SAFE: 484
- ELU_LIMIT: 327
- WARNING: 208
- HIGH_LOAD: 129
- SAFE: 66
- ELS_LIMIT: 5

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 748
- EXPANSION_EXHAUSTION_CONTEXT: 380
- RECOVERY_CONTEXT: 91

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 484
- EXPANSION_PROTECTED: 327
- RECOVERY_PROTECTED: 408

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
