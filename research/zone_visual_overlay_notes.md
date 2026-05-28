# RDM Visual Overlay

Research-only visualization layer for Phase 1B+ RDM Market Mechanics.

## Purpose

Display RDM mechanics directly over replay price context:

- Formation range
- Interaction core
- Zone birth
- Retests / touches
- Breach / rupture markers
- Fatigue strip
- Dormant / lifecycle state
- Mechanical death marker

## Rules

- Research only
- Observation only
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

## Implementation

The dashboard uses a dependency-light SVG overlay renderer so it does not require Plotly.
The overlay reads existing historical observation rows and live-style RDM evolution rows.
