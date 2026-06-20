# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-06-16T22:03:16+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 1664
- RECOVERED_ZONE: 372
- EXHAUSTED_ZONE: 1296
- FATIGUE_ZONE: 1171
- ELASTIC_ZONE: 356

## Mechanical Family Counts
- ELASTIC_FAMILY: 2020
- RECOVERY_FAMILY: 372
- EXHAUSTION_FAMILY: 1296
- FATIGUE_FAMILY: 1171

## Mechanical Subtype Counts
- RIGID_SUPPORT: 1664
- RECLAIM_RECOVERY: 372
- LATE_FAILURE: 226
- EXPANSION_EXHAUSTION: 1070
- RECOVERY_LOSS: 1171
- STRONG_REACTION: 356

## Reference Examples
- CASE_00021: EXHAUSTION_FAMILY / EXPANSION_EXHAUSTION / EXHAUSTED_ZONE /  / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
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
