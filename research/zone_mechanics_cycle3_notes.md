# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-05-27T12:38:05+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 11
- EXHAUSTED_ZONE: 3
- RUPTURE_ZONE: 2
- FATIGUE_ZONE: 10
- RECOVERED_ZONE: 1

## Mechanical Family Counts
- ELASTIC_FAMILY: 11
- EXHAUSTION_FAMILY: 3
- RUPTURE_FAMILY: 2
- FATIGUE_FAMILY: 10
- RECOVERY_FAMILY: 1

## Mechanical Subtype Counts
- RIGID_SUPPORT: 11
- EXPANSION_EXHAUSTION: 3
- FAILED_RETURN_RUPTURE: 2
- RECOVERY_LOSS: 10
- RECLAIM_RECOVERY: 1

## Reference Examples
- CASE_00021: NOT_FOUND
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
