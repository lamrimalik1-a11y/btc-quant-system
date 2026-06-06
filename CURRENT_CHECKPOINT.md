==================================================
CURRENT CHECKPOINT
==================================================

Checkpoint: PHASE1B_FORMATION_MODEL
Date:       2026-06-06
Previous:   PHASE1B_MARCH_APRIL_MAY_GENERALIZATION_STABLE (2026-06-05)

==================================================
ACTIVE PHASE
==================================================

PHASE 1B — OBSERVATION RESEARCH MODE
STATUS: STABLE

RESEARCH ONLY. NOT A TRADING SYSTEM.
No Phase 2. No execution. No BUY/SELL. No entries/exits.

==================================================
FORMATION MODEL TERMINOLOGY
==================================================

Formation (replaces Preparation Zone — parent structure)
    Density Band (derived from Formation — high-concentration operational region)
        Active Core (derived from Density Band — highest precision, innermost)

Internal code: still uses preparation_zone. Code renaming not authorized.
Reference: research/terminology_formation_zones.md

==================================================
THREE-PERIOD B12v2 RESULTS
==================================================

TRAINING (Apr30-Jun02):   355 cases  98.3% acc  +35.2pp lift  FAIL 95.6%  PASS
MARCH 2026 (Mar01-Mar31): 633 cases  96.7% acc  +36.7pp lift  FAIL 93.3%  PASS
APRIL 2026 (Apr01-Apr30): 387 cases  95.1% acc  +32.6pp lift  FAIL 89.4%  BORDERLINE FAIL

REGIME GENERALIZATION: STRONGLY VALIDATED (2/3 PASS, April borderline -0.6pp)

Physics (sigma x penetration vs omega):
  Training r=0.9978 / March r=0.9953 / April r=0.9966 — CONFIRMED all periods

==================================================
PRESERVED FILES
==================================================

research/train_*                  (training period backups)
research/apr2026_b12v2_*         (April B12v2 outputs)
research/apr2026_generalization_audit.md
research/mar2026_b12v2_*         (March B12v2 outputs)
research/mar2026_generalization_audit.md

==================================================
KEY CONSTRAINTS
==================================================

Do NOT change Phase1B formulas.
Do NOT change RDM formulas.
Do NOT modify B11/B12v2 logic.
Do NOT download data without explicit request.
Do NOT start Phase 2.

==================================================
NEXT RESEARCH STEPS
==================================================

1. Investigate STABLE trajectory in EXHAUSTED_ZONE (false HOLD pattern, 2 periods)
2. Track TERMINAL recovery rate (3-10% across periods, training may be outlier)
3. Consider widening FAIL Precision threshold to 87-88%
4. Extend to January or February 2026 for fourth-period validation
5. Calibrate B11 thresholds from three-period precision/recall data
