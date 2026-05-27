# Zone Mechanics Birth Concept

Mode: Research only

This document defines the Phase 1B+ RDM Market Mechanics zone lifecycle model.
It does not introduce execution, entries, live signals, Phase 2 logic, or Dashboard V2 scoring changes.

## Lifecycle

Birth -> Life -> Memory -> Interaction -> Outcome -> Death

## Birth

Zone birth captures formation volume, delta, velocity, duration, quality, base resistance,
initial sigma barre, initial rigidity, initial capacity, and institutional reinforcement.

Birth states:

- ELASTIC_BIRTH
- RIGID_BIRTH
- INSTITUTIONAL_BIRTH
- PREPARATION_BIRTH
- EXPANSION_BIRTH
- UNKNOWN_BIRTH

## Life Tracking

Life tracking records age, tests, active duration, decay rate, and survival ratio.

## Mechanical Memory

Mechanical memory stores per-zone stress, fleche, fatigue, repair, capacity, sigma, and timeline history.

## Death

Death labels:

- RUPTURE
- FATIGUE
- EXHAUSTION
- RECOVERY_COMPLETE
- TIME_DECAY
- DORMANT_EXPIRED
- UNKNOWN_DEATH

## Safety Rule

Cases may be shown as reference examples, but classification remains mechanics-first:

Variables -> Family -> Subtype -> State
