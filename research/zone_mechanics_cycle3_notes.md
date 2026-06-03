# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-06-03T21:57:18+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 111
- ELASTIC_ZONE: 36
- RECOVERED_ZONE: 24
- FATIGUE_ZONE: 37
- EXHAUSTED_ZONE: 68

## Mechanical Family Counts
- ELASTIC_FAMILY: 147
- RECOVERY_FAMILY: 24
- FATIGUE_FAMILY: 37
- EXHAUSTION_FAMILY: 68

## Mechanical Subtype Counts
- RIGID_SUPPORT: 111
- STRONG_REACTION: 36
- RECLAIM_RECOVERY: 24
- RECOVERY_LOSS: 37
- EXPANSION_EXHAUSTION: 36
- LATE_FAILURE: 32

## Reference Examples
- CASE_00021: RECOVERY_FAMILY / RECLAIM_RECOVERY / RECOVERED_ZONE /  / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00035: NOT_FOUND
- CASE_00041: NOT_FOUND
- CASE_00036: NOT_FOUND
- CASE_00044: NOT_FOUND

## Interpretation
- Mechanics are classified first by family/subtype/state.
- Case IDs are retained only as reference examples, not as classification anchors.
- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.
- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.
- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.

Research-only note: these classifications are not signals and do not affect scoring.
