# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-05-26T22:10:18+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 7
- ELASTIC_ZONE: 1
- RUPTURE_ZONE: 1
- RECOVERED_ZONE: 1
- EXHAUSTED_ZONE: 2

## Mechanical Family Counts
- ELASTIC_FAMILY: 8
- RUPTURE_FAMILY: 1
- RECOVERY_FAMILY: 1
- EXHAUSTION_FAMILY: 2

## Mechanical Subtype Counts
- RIGID_SUPPORT: 7
- STRONG_REACTION: 1
- FAILED_RETURN_RUPTURE: 1
- RECLAIM_RECOVERY: 1
- EXPANSION_EXHAUSTION: 2

## Reference Examples
- CASE_00021: ELASTIC_FAMILY / RIGID_SUPPORT / RIGID_ZONE /  / fatigue=LOW_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00035: RUPTURE_FAMILY / FAILED_RETURN_RUPTURE / RUPTURE_ZONE / TRUE_FAILED_RETURN / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00041: EXHAUSTION_FAMILY / EXPANSION_EXHAUSTION / EXHAUSTED_ZONE / EXPANSION_THEN_EXHAUSTION / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00036: RECOVERY_FAMILY / RECLAIM_RECOVERY / RECOVERED_ZONE / SUCCESSFUL_RETURN / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELS_DEFORMATION_RESEARCH_ZONE
- CASE_00044: NOT_FOUND

## Interpretation
- Mechanics are classified first by family/subtype/state.
- Case IDs are retained only as reference examples, not as classification anchors.
- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.
- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.
- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.

Research-only note: these classifications are not signals and do not affect scoring.
