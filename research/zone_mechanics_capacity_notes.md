# Zone Mechanics Capacity Notes

- Run UTC: 2026-06-03T21:57:18+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 148
- ELU_LIMIT: 68
- ELS_LIMIT: 2
- HIGH_LOAD: 15
- WARNING: 43

## Dynamic ELU State Counts
- ELS_SAFE: 129
- SAFE: 19
- ELU_LIMIT: 68
- ELS_LIMIT: 2
- HIGH_LOAD: 15
- WARNING: 43

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 167
- EXPANSION_EXHAUSTION_CONTEXT: 85
- RECOVERY_CONTEXT: 24

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 129
- RECOVERY_PROTECTED: 79
- EXPANSION_PROTECTED: 68

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
