# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-06-05T21:47:45+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 428
- ELASTIC_ZONE: 114
- EXHAUSTED_ZONE: 327
- FATIGUE_ZONE: 259
- RECOVERED_ZONE: 91

## Mechanical Family Counts
- ELASTIC_FAMILY: 542
- EXHAUSTION_FAMILY: 327
- FATIGUE_FAMILY: 259
- RECOVERY_FAMILY: 91

## Mechanical Subtype Counts
- RIGID_SUPPORT: 428
- STRONG_REACTION: 114
- EXPANSION_EXHAUSTION: 290
- RECOVERY_LOSS: 259
- RECLAIM_RECOVERY: 91
- LATE_FAILURE: 37

## Reference Examples
- CASE_00021: NOT_FOUND
- CASE_00035: NOT_FOUND
- CASE_00041: ELASTIC_FAMILY / STRONG_REACTION / ELASTIC_ZONE / EXPANSION_THEN_EXHAUSTION / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00036: NOT_FOUND
- CASE_00044: NOT_FOUND

## Interpretation
- Mechanics are classified first by family/subtype/state.
- Case IDs are retained only as reference examples, not as classification anchors.
- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.
- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.
- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.

Research-only note: these classifications are not signals and do not affect scoring.
