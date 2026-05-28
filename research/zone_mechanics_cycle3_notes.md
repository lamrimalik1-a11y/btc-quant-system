# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-05-28T14:58:29+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 11
- ELASTIC_ZONE: 5
- FATIGUE_ZONE: 4
- EXHAUSTED_ZONE: 4
- RECOVERED_ZONE: 3

## Mechanical Family Counts
- ELASTIC_FAMILY: 16
- FATIGUE_FAMILY: 4
- EXHAUSTION_FAMILY: 4
- RECOVERY_FAMILY: 3

## Mechanical Subtype Counts
- RIGID_SUPPORT: 11
- STRONG_REACTION: 5
- RECOVERY_LOSS: 4
- EXPANSION_EXHAUSTION: 4
- RECLAIM_RECOVERY: 3

## Reference Examples
- CASE_00021: NOT_FOUND
- CASE_00035: NOT_FOUND
- CASE_00041: NOT_FOUND
- CASE_00036: FATIGUE_FAMILY / RECOVERY_LOSS / FATIGUE_ZONE / SUCCESSFUL_RETURN / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00044: NOT_FOUND

## Interpretation
- Mechanics are classified first by family/subtype/state.
- Case IDs are retained only as reference examples, not as classification anchors.
- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.
- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.
- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.

Research-only note: these classifications are not signals and do not affect scoring.
