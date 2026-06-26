# RDM V2 Mechanical Architecture Spec

Status: STABLE RESEARCH CHECKPOINT
Checkpoint: PHASE1B_RDM_V2_MECHANICAL_ARCHITECTURE_STABLE
Scope: documentation and architecture consolidation only

This document summarizes the current stable understanding of the mechanical engine after Stage 5H. It is a research architecture specification, not a production replacement approval, not trading validation, and not an execution design.

## Research Timeline

Stage 1 established the first post-return research frame: zones were observed after return and measured as structural objects rather than as trading signals.

Stage 2 / 2C replaced frozen post-return mechanics with a two-axis model:
- acute pressure
- chronic structural damage

Stage 2C is mechanically superior to frozen post-return behavior because it separates immediate pressure from accumulating structural degradation.

Stage 2D replay validation checked whether the post-return evolution behavior survived replay-style validation.

Stage 3 / 3B introduced gating and recalibration checks around prediction quality and holdout behavior.

Stage 4 added economic/validation gating without changing the mechanical premise.

Stage 5 / 5B / 5C moved validation from direction-blind tests toward directional structural targets. Stage 5C made clear that family-level FAIL/HOLD aggregation could hide state-level information.

Stage 5D analyzed Dynamic States individually and found that individual Dynamic States carry different directional information. ATTACKER_DOMINANT is the strongest continuation-bearing state observed so far.

Stage 5E analyzed Dynamic State transitions descriptively, focusing on what variables moved before transitions and in what sequence.

Stage 5F grouped transitions by mechanical evolution pattern instead of by State A -> State B labels, showing that broad process families exist while strict transition mechanics remain state-specific.

Stage 5G studied what creates Attacker Force. The key finding was that Attacker Force does not appear to originate primarily from raw delta alone; it most often emerges after interaction with geometry, penetration, omega/exposure, attacker integral, and SDR.

Stage 5H documented the mechanical dependency graph and classified variables as PRIMARY, DERIVED, or EMERGENT.

## Core Mechanical Architecture

The current research architecture is:

```text
Raw Market Data
    -> Statistics Engine
    -> Geometry Engine
    -> Interaction / Penetration
    -> Mechanical Exposure
    -> RDM V2
    -> SDR / Derivative / Integral
    -> Dynamic State
    -> Structural Prediction
```

The project does not search for a trading signal at this stage. Each layer answers a scientific question:

- Statistics Engine: what is statistically unusual?
- Geometry Engine: where does interaction occur?
- Mechanical Engine: what is the structural condition of that interaction?
- Dynamic State: how is that condition evolving?
- Structural Prediction: what structural evolution is most likely?

Execution, entries, exits, Footprint, Structure Engine, Entropy Engine, and decision logic remain future layers and are explicitly out of scope.

## Variable Hierarchy

Stage 5H used these research artifacts:

- research/post_return_evo_experiment/stage5h_variable_classification.csv
- research/post_return_evo_experiment/stage5h_dependency_layers.csv
- research/post_return_evo_experiment/stage5h_dependency_graph.csv
- research/post_return_evo_experiment/stage5h_dependency_loops.csv

Summary:

- Variables classified: 49
- Dependency edges: 113
- Dependency layers: 21
- Max dependency depth: 20
- Direct dependency loops: 0

### PRIMARY Variables

PRIMARY variables are direct market, geometry, episode, or lifecycle inputs. Examples:

- Raw Market Rows
- Statistical Fields
- Dashboard V2 Episodes
- Research Case
- Formation Range
- Return/Revisit Context
- Zone Lifecycle Events
- Field Lifecycle Events

### DERIVED Variables

DERIVED variables are formulas or aggregations from primary and earlier derived variables. Examples:

- Penetration / Fleche
- Rigidity
- Capacity
- Health
- Fatigue
- Recovery
- Structural Damage
- Sigma Barre
- Sigma Market
- Stress Utilization
- Omega
- Attacker Force
- Attacker Integral
- Zone Integral
- First Derivative
- Second Derivative
- SDR

### EMERGENT Variables

EMERGENT variables are higher-level mechanical states, trajectories, predictions, or synthesis labels formed by multiple lower layers. Examples:

- ELS / ELU State
- Mechanical Family / State
- Sigma State
- Sigma Failure Risk
- Capacity State
- Dynamic State
- B10 Structural Trajectory
- B11 Structural Prediction
- Synthesis

## Dependency Graph Summary

The current mechanical engine is feed-forward at artifact-generation time.

Important conclusion:

- No same-step algebraic dependency loop was confirmed.
- Temporal memory exists through integrals, live guards, health evolution, sigma evolution, and structural damage.
- These are recurrences over ordered visits/rows, not direct same-step algebraic cycles.

The key graph chain is:

```text
Raw / statistical / geometry context
    -> RDM primitives
    -> row-level live evolution
    -> visit timeline
    -> health and attacker force series
    -> derivatives / integrals / SDR
    -> Dynamic State
    -> B10 trajectory
    -> B11 structural prediction
    -> Synthesis / validation
```

## Validated Mechanical Conclusions

1. The mechanical engine is feed-forward at artifact-generation time.

2. It has temporal memory through:
   - zone and field lifecycle events
   - integrals
   - live guards
   - health evolution
   - sigma evolution
   - structural damage

3. No same-step algebraic loop was confirmed.

4. Stage 2C replaced frozen post-return mechanics with a two-axis model:
   - acute pressure
   - chronic structural damage

5. Stage 2C is mechanically superior to frozen post-return behavior.

6. Stress exposure remains central. Prior exposure work validated that:

```text
sigma_at_return x zone_penetration_depth ~= omega_stress_area
```

Omega remains the central deep structural exposure variable.

## Dynamic State Findings

ATTACKER_DOMINANT has a distinct mechanical signature.

ATTACKER_DOMINANT is the strongest continuation-bearing Dynamic State observed so far.

STABLE and PROBABLE_HOLD are more rejection-biased.

Some hold-side states and warning/recovery states may require future redundancy review, but no state merge is approved yet.

Dynamic State is not a trading signal. It is a descriptive structural state layer.

## Transition Findings

Stage 5E and Stage 5F suggest:

- Attacker Force and Omega are the most common first movers.
- Fatigue is the clearest deterioration precursor.
- Broad transition process classes exist.
- Strict transition mechanics remain specific to the transition path.
- No universal transition rule is accepted yet.

## Attacker Force Findings

Attacker Force does not appear to originate primarily from raw delta alone.

It most often emerges after market interaction with:

- zone geometry
- penetration
- omega / exposure
- attacker integral
- SDR

This means Attacker Force is better understood as an interaction-conditioned structural variable, not a simple order-flow variable.

## Current Limitations

Dynamic State has not yet been fully validated as a trading signal.

Structural Prediction is a research layer, not the final objective.

Trading and execution remain out of scope.

Footprint, Structure Engine, Entropy Engine, execution, entries, exits, and decision logic remain future layers.

Project 2 has not started implementation. Its philosophy remains: replace only the Geometry Engine while reusing replay, statistics, dashboard, research infrastructure, and validation methodology.

## Architectural Decision

The current mechanical architecture is accepted as a stable research checkpoint.

It is NOT approved for production replacement.

It is NOT trading validation.

It is NOT Phase 2.

It is a consolidated research architecture for continuing mechanical validation.

## Rules Preserved

- No Phase 2
- No Footprint
- No execution
- No entries/exits
- No BUY/SELL
- No live signals
- No Dashboard V2 scoring changes
- No replay scoring changes
- No RDM formula changes
- No Dynamic State threshold changes
- Research before optimization
- Negative results remain valid knowledge
