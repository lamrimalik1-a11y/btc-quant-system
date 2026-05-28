# Zone Mechanics Capacity Notes

- Run UTC: 2026-05-28T11:10:25+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 26
- ELU_LIMIT: 16
- WARNING: 10
- HIGH_LOAD: 1

## Dynamic ELU State Counts
- ELS_SAFE: 25
- ELU_LIMIT: 16
- WARNING: 10
- SAFE: 1
- HIGH_LOAD: 1

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 31
- EXPANSION_EXHAUSTION_CONTEXT: 20
- RECOVERY_CONTEXT: 2

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 25
- EXPANSION_PROTECTED: 16
- RECOVERY_PROTECTED: 12

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.
