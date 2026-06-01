# Zone Mechanics Cycle 3 Notes

- Run UTC: 2026-06-01T15:12:02+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Mechanical State Counts
- RIGID_ZONE: 281
- RECOVERED_ZONE: 45
- FATIGUE_ZONE: 171
- EXHAUSTED_ZONE: 61
- ELASTIC_ZONE: 75
- PENDING_REVIEW: 1

## Mechanical Family Counts
- ELASTIC_FAMILY: 356
- RECOVERY_FAMILY: 45
- FATIGUE_FAMILY: 171
- EXHAUSTION_FAMILY: 61
- PENDING_REVIEW: 1

## Mechanical Subtype Counts
- RIGID_SUPPORT: 281
- RECLAIM_RECOVERY: 45
- RECOVERY_LOSS: 171
- LATE_FAILURE: 24
- STRONG_REACTION: 75
- PENDING_REVIEW: 1
- EXPANSION_EXHAUSTION: 37

## Reference Examples
- CASE_00021: FATIGUE_FAMILY / RECOVERY_LOSS / FATIGUE_ZONE /  / fatigue=CRITICAL_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00035: ELASTIC_FAMILY / RIGID_SUPPORT / RIGID_ZONE / TRUE_FAILED_RETURN / fatigue=LOW_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00041: RECOVERY_FAMILY / RECLAIM_RECOVERY / RECOVERED_ZONE / EXPANSION_THEN_EXHAUSTION / fatigue=LOW_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00036: ELASTIC_FAMILY / RIGID_SUPPORT / RIGID_ZONE / SUCCESSFUL_RETURN / fatigue=LOW_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE
- CASE_00044: PENDING_REVIEW / PENDING_REVIEW / PENDING_REVIEW / PENDING_SUCCESSFUL_RETURN_REVIEW / fatigue=HIGH_FATIGUE / ELS-ELU=ELU_RUPTURE_RESEARCH_ZONE

## Interpretation
- Mechanics are classified first by family/subtype/state.
- Case IDs are retained only as reference examples, not as classification anchors.
- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.
- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.
- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.

Research-only note: these classifications are not signals and do not affect scoring.
