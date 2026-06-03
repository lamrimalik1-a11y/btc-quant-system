"""
Phase 1 Synthesis Engine — Minimal Professional Version

Connects RDM B1–B11 structural outputs with statistical episode context
into a single coherent MarketInterpretation per zone case.

Architecture:
    Bundle A  — Statistical context (approximated from episode peak data)
    Bundle B  — Structural state (from B10 zone_structural_trajectory)
    Bundle C  — Engagement + Prediction (from B11 zone_structural_prediction)

Output: research/zone_synthesis.csv  — 13 columns, one row per case_id

Research only. No scoring, lifecycle, replay, or dashboard changes.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any


# ==============================================================================
# 1. LAYER TAXONOMY REGISTER
#    role:  OBSERVATION | CONTEXT | STRUCTURE | ENGAGEMENT | PREDICTION | HISTORICAL
#    scope: STRUCTURAL (multi-visit zone evidence) | CURRENT (bar/session level)
# ==============================================================================

TAXONOMY: dict[str, dict[str, str]] = {
    # Structural state fields — multi-visit zone evidence
    "structural_trajectory":  {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "health_state":            {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "health_slope":            {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "health_total_change":     {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "health_last_visit":       {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "sigma_barre_zone":        {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    "omega_stress_area":       {"role": "STRUCTURE",    "scope": "STRUCTURAL"},
    # Engagement fields — visit interaction evidence
    "visit_count":             {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "omega_total":             {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "omega_max":               {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "omega_mean":              {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "damage_visit_count":      {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "growth_visit_count":      {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "breakdown_visit_count":   {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "absorption_visit_count":  {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "final_visit_result":      {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "dominant_visit_result":   {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "attacker_force_total":    {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "attacker_force_max":      {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "force_ratio":             {"role": "ENGAGEMENT",   "scope": "CURRENT"},
    "zone_strength_score":     {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    "zone_penetration_depth":  {"role": "ENGAGEMENT",   "scope": "STRUCTURAL"},
    # Prediction fields
    "structural_prediction":   {"role": "PREDICTION",   "scope": "STRUCTURAL"},
    "prediction_confidence":   {"role": "PREDICTION",   "scope": "STRUCTURAL"},
    "prediction_score":        {"role": "PREDICTION",   "scope": "STRUCTURAL"},
    "trajectory_score":        {"role": "PREDICTION",   "scope": "STRUCTURAL"},
    "trajectory_direction":    {"role": "PREDICTION",   "scope": "STRUCTURAL"},
    # Statistical context (episode-level approximation)
    "peak_state":              {"role": "CONTEXT",      "scope": "CURRENT"},
    "peak_layer_count":        {"role": "CONTEXT",      "scope": "CURRENT"},
    "peak_max_severity":       {"role": "CONTEXT",      "scope": "CURRENT"},
    "peak_primary_context":    {"role": "CONTEXT",      "scope": "CURRENT"},
    # Historical context
    "attacker_force_score":    {"role": "CONTEXT",      "scope": "CURRENT"},
    "sigma_at_return":         {"role": "CONTEXT",      "scope": "STRUCTURAL"},
}

# Structural direction map — maps field values to POSITIVE / NEUTRAL / NEGATIVE
TRAJECTORY_DIRECTION: dict[str, str] = {
    "STRENGTHENING":        "POSITIVE",
    "STABLE":               "POSITIVE",
    "RECOVERY":             "POSITIVE",
    "UNKNOWN":              "NEUTRAL",
    "TRANSITIONAL":         "NEUTRAL",
    "DEGRADING":            "NEGATIVE",
    "ACCELERATING_FAILURE": "NEGATIVE",
    "TERMINAL":             "NEGATIVE",
}
PREDICTION_DIRECTION: dict[str, str] = {
    "HOLD":          "POSITIVE",
    "UNCERTAIN":     "NEUTRAL",
    "NO_PREDICTION": "NEUTRAL",
    "FAIL":          "NEGATIVE",
}


# ==============================================================================
# 2. BUNDLE ASSEMBLER
# ==============================================================================

def assemble_bundles(
    results_df:    pd.DataFrame,
    trajectory_df: pd.DataFrame,
    prediction_df: pd.DataFrame,
    episodes_df:   pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    """
    Assemble the three input bundles for each case_id.

    Returns dict: case_id → flat dict of labeled field values.
    Missing values default to "" or 0.
    """
    # Index sources
    traj_idx = trajectory_df.set_index("case_id").to_dict("index") if (
        "case_id" in trajectory_df.columns
    ) else {}
    pred_idx = prediction_df.set_index("case_id").to_dict("index") if (
        "case_id" in prediction_df.columns
    ) else {}

    # Link case_id → episode_id for Bundle A
    ep_id_map: dict[str, str] = {}
    if "case_id" in results_df.columns and "episode_id" in results_df.columns:
        ep_id_map = dict(
            zip(results_df["case_id"].astype(str),
                results_df["episode_id"].astype(str))
        )
    ep_idx = episodes_df.set_index("episode_id").to_dict("index") if (
        "episode_id" in episodes_df.columns
    ) else {}

    assembled: dict[str, dict[str, Any]] = {}

    for case_id in results_df["case_id"].astype(str).unique():
        tr = traj_idx.get(case_id, {})
        pr = pred_idx.get(case_id, {})
        episode_id_str = str(ep_id_map.get(case_id, ""))
        ep = ep_idx.get(episode_id_str, ep_idx.get(int(episode_id_str) if episode_id_str.isdigit() else -1, {}))

        inputs: dict[str, Any] = {}

        # Bundle B — from trajectory
        for field in ["structural_trajectory", "health_state", "health_slope",
                       "health_total_change", "health_last_visit",
                       "damage_visit_count", "growth_visit_count",
                       "breakdown_visit_count", "absorption_visit_count",
                       "visit_count", "omega_total", "omega_max",
                       "attacker_force_total", "attacker_force_max",
                       "final_visit_result", "dominant_visit_result",
                       "trajectory_confidence", "trajectory_score",
                       "trajectory_direction"]:
            val = tr.get(field, pr.get(field, ""))
            inputs[field] = val if val == val and val != "nan" else ""  # NaN guard

        # Bundle C — from prediction (adds more fields)
        for field in ["structural_prediction", "prediction_confidence",
                       "prediction_score", "sigma_barre_zone", "sigma_at_return",
                       "omega_stress_area", "zone_penetration_depth",
                       "zone_strength_score", "attacker_force_score",
                       "force_ratio"]:
            val = pr.get(field, "")
            inputs[field] = val if val == val and val != "nan" else ""

        # Bundle A — from episodes (statistical context approximation)
        for field in ["peak_state", "peak_layer_count",
                       "peak_max_severity", "peak_primary_context"]:
            val = ep.get(field, "")
            inputs[field] = val if val == val and val != "nan" else ""

        assembled[case_id] = inputs

    return assembled


# ==============================================================================
# 3. PRIORITY RULES
# ==============================================================================

_SCOPE_WEIGHT = {"STRUCTURAL": 2, "CURRENT": 1}
_ROLE_WEIGHT  = {"PREDICTION": 5, "STRUCTURE": 4, "ENGAGEMENT": 3,
                 "CONTEXT": 2, "OBSERVATION": 1, "HISTORICAL": 0}


def scope_authority(scope_a: str, scope_b: str) -> str:
    """Return the scope with higher authority."""
    return scope_a if _SCOPE_WEIGHT.get(scope_a, 0) >= _SCOPE_WEIGHT.get(scope_b, 0) else scope_b


def role_authority(role_a: str, role_b: str) -> str:
    """Return the role with higher interpretive authority."""
    return role_a if _ROLE_WEIGHT.get(role_a, 0) >= _ROLE_WEIGHT.get(role_b, 0) else role_b


def structural_direction(field_name: str, field_value: str) -> str:
    """Return POSITIVE / NEUTRAL / NEGATIVE for a field value."""
    if field_name == "structural_trajectory":
        return TRAJECTORY_DIRECTION.get(str(field_value), "NEUTRAL")
    if field_name == "structural_prediction":
        return PREDICTION_DIRECTION.get(str(field_value), "NEUTRAL")
    if field_name == "trajectory_direction":
        v = str(field_value).upper()
        if v in ("POSITIVE",): return "POSITIVE"
        if v in ("NEGATIVE",): return "NEGATIVE"
        return "NEUTRAL"
    return "NEUTRAL"


# ==============================================================================
# 4. GENUINE CONFLICT CHECK
# ==============================================================================

def check_genuine_conflict(inputs: dict[str, Any]) -> tuple[bool, str]:
    """
    Check whether any two STRUCTURAL-scope, STRUCTURE-role fields point
    in opposite structural directions.

    Returns (genuine_conflict: bool, conflict_note: str).
    """
    candidates = {
        field: structural_direction(field, inputs.get(field, ""))
        for field in ["structural_trajectory", "structural_prediction"]
        if field in inputs
    }

    directions = [d for d in candidates.values() if d != "NEUTRAL"]

    if "POSITIVE" in directions and "NEGATIVE" in directions:
        traj = inputs.get("structural_trajectory", "")
        pred = inputs.get("structural_prediction", "")
        return True, f"trajectory={traj} contradicts prediction={pred}"

    return False, ""


# ==============================================================================
# 5. THREE-GATE SYNTHESIS CHECK
# ==============================================================================

def synthesis_gate(inputs: dict[str, Any]) -> tuple[bool, str]:
    """
    Check three gate conditions. Returns (passed: bool, failure_message: str).

    Gate 1: structural_trajectory is not UNKNOWN/empty
    Gate 2: visit_count >= 1
    Gate 3: NOT (both confidences LOW)
    """
    traj = str(inputs.get("structural_trajectory", "")).strip()
    if not traj or traj in ("", "UNKNOWN", "nan"):
        return False, "No active zone with structural classification available."

    try:
        vc = int(float(inputs.get("visit_count", 0) or 0))
    except (ValueError, TypeError):
        vc = 0
    if vc < 1:
        return False, "Zone identified but no visit data available."

    tc = str(inputs.get("trajectory_confidence", "LOW")).strip()
    pc = str(inputs.get("prediction_confidence", "LOW")).strip()
    if tc == "LOW" and pc == "LOW":
        return False, "Single-visit zone — insufficient evidence for structural prediction."

    return True, ""


# ==============================================================================
# 6. FOUR-LEVEL COHERENCE LABEL
# ==============================================================================

def compute_coherence_label(
    inputs: dict[str, Any],
    genuine_conflict: bool,
) -> str:
    """
    Return STRONG / MODERATE / WEAK / INSUFFICIENT based on structural evidence quality.
    """
    if genuine_conflict:
        return "INSUFFICIENT"

    traj_dir = structural_direction("structural_trajectory",
                                    inputs.get("structural_trajectory", ""))
    pred_dir = structural_direction("structural_prediction",
                                    inputs.get("structural_prediction", ""))

    tc = str(inputs.get("trajectory_confidence", "LOW")).strip()
    pc = str(inputs.get("prediction_confidence", "LOW")).strip()

    try:
        vc = int(float(inputs.get("visit_count", 0) or 0))
    except (ValueError, TypeError):
        vc = 0

    # Both non-neutral and same direction
    aligned = (traj_dir != "NEUTRAL" and pred_dir != "NEUTRAL"
               and traj_dir == pred_dir)

    if aligned and tc == "HIGH" and vc >= 3:
        return "STRONG"

    if aligned and (tc in ("HIGH", "MEDIUM") or vc >= 2):
        return "MODERATE"

    if traj_dir == "NEUTRAL" or pred_dir == "NEUTRAL":
        return "MODERATE"   # uncertain but not conflicted

    # Directions are opposite or confidence low
    return "WEAK"


# ==============================================================================
# 7. FIELD COMPRESSORS (simple threshold lookups)
# ==============================================================================

def _omega_class(omega_max: Any) -> str:
    try:
        v = float(omega_max or 0)
    except (ValueError, TypeError):
        return "unknown omega"
    if v > 20_000:  return "extreme omega"
    if v > 5_000:   return "high omega"
    if v > 1_000:   return "moderate omega"
    return "low omega"


def _force_balance(force_ratio: Any) -> str:
    try:
        v = float(force_ratio or 0)
    except (ValueError, TypeError):
        return "unknown balance"
    if v < 0.4:  return "zone dominant"
    if v < 0.8:  return "contested"
    return "attacker dominant"


def _regime_label(peak_state: str) -> str:
    mapping = {
        "EXTREME_LAYER_CONFLUENCE": "extreme",
        "STRONG_LAYER_CONFLUENCE":  "strong",
        "MODERATE_LAYER_CONFLUENCE": "moderate",
        "NO_CONFLUENCE":            "quiet",
        "UNSTABLE_STATISTICAL_CONTEXT": "unstable",
    }
    return mapping.get(str(peak_state).strip(), "normal")


def _confluence_label(peak_layer_count: Any) -> str:
    try:
        n = int(float(peak_layer_count or 0))
    except (ValueError, TypeError):
        n = 0
    if n >= 5:  return f"{n}-signal (extreme)"
    if n >= 3:  return f"{n}-signal (strong)"
    if n >= 2:  return f"{n}-signal"
    return "low confluence"


def _flow_direction(inputs: dict[str, Any]) -> str:
    """Derive flow direction from trajectory_direction and peak context."""
    traj_dir = str(inputs.get("trajectory_direction", "")).strip().upper()
    peak_ctx  = str(inputs.get("peak_primary_context", "")).strip().upper()

    # Use peak_primary_context if it has directional information
    if "BUYER" in peak_ctx:   return "buyer pressure"
    if "SELLER" in peak_ctx:  return "seller pressure"
    if "BUY" in peak_ctx:     return "buyer pressure"
    if "SELL" in peak_ctx:    return "seller pressure"

    # Fall back to trajectory direction
    if traj_dir == "POSITIVE":  return "supporting flow"
    if traj_dir == "NEGATIVE":  return "opposing flow"
    return "neutral flow"


def compress_context(inputs: dict[str, Any]) -> str:
    regime     = _regime_label(inputs.get("peak_state", ""))
    confluence = _confluence_label(inputs.get("peak_layer_count", 0))
    flow       = _flow_direction(inputs)
    return f"{regime} regime / {confluence} / {flow}"


def compress_structure(inputs: dict[str, Any]) -> str:
    traj   = str(inputs.get("structural_trajectory", "UNKNOWN")).strip()
    tc     = str(inputs.get("trajectory_confidence", "LOW")).strip().lower()
    health = str(inputs.get("health_state", "UNKNOWN")).strip()
    return f"{traj} ({tc}) — {health}"


def compress_engagement(inputs: dict[str, Any]) -> str:
    try:
        vc = int(float(inputs.get("visit_count", 0) or 0))
    except (ValueError, TypeError):
        vc = 0
    omega   = _omega_class(inputs.get("omega_max", 0))
    balance = _force_balance(inputs.get("force_ratio", 0))
    visits  = "1 visit" if vc == 1 else f"{vc} visits"
    return f"{visits} / {omega} / {balance}"


def compress_flow(inputs: dict[str, Any]) -> str:
    direction  = _flow_direction(inputs)
    peak_sev   = str(inputs.get("peak_max_severity", "")).strip().upper()
    if "EXTREME" in peak_sev: intensity = "extreme intensity"
    elif "HIGH"  in peak_sev: intensity = "high intensity"
    elif "MEDIUM" in peak_sev or "MODERATE" in peak_sev: intensity = "moderate intensity"
    else:                      intensity = "low intensity"
    return f"{direction} / {intensity}"


def compress_prediction(
    inputs: dict[str, Any],
    genuine_conflict: bool,
) -> str:
    pred = str(inputs.get("structural_prediction", "NO_PREDICTION")).strip()
    pc   = str(inputs.get("prediction_confidence", "LOW")).strip().lower()
    tag  = " [conflict]" if genuine_conflict else ""
    return f"{pred} ({pc}){tag}"


def compress_coherence(
    coherence_label: str,
    conflict_note: str,
) -> str:
    if conflict_note:
        return f"{coherence_label} [{conflict_note}]"
    return coherence_label


# ==============================================================================
# 8. TEMPLATE ENGINE (3 templates + catch-all)
# ==============================================================================

def _trajectory_word(traj: str) -> str:
    """Short readable form of structural_trajectory value."""
    mapping = {
        "STRENGTHENING":        "STRENGTHENING",
        "STABLE":               "STABLE",
        "RECOVERY":             "RECOVERING",
        "DEGRADING":            "DEGRADING",
        "ACCELERATING_FAILURE": "ACCELERATING FAILURE",
        "TERMINAL":             "TERMINAL",
        "TRANSITIONAL":        "TRANSITIONAL",
        "UNKNOWN":              "UNKNOWN",
    }
    return mapping.get(str(traj).strip(), str(traj).strip())


def _confidence_qualifier(coherence_label: str) -> str:
    return {
        "STRONG":       "confirmed",
        "MODERATE":     "expected",
        "WEAK":         "possible",
        "INSUFFICIENT": "uncertain",
    }.get(coherence_label, "")


def _engagement_note(inputs: dict[str, Any]) -> str:
    try:
        vc = int(float(inputs.get("visit_count", 0) or 0))
    except (ValueError, TypeError):
        vc = 0
    bc = int(float(inputs.get("breakdown_visit_count", 0) or 0))
    if bc > 0:
        return f"surviving {bc} breakdown attempt(s)"
    if vc >= 3:
        return f"after {vc} visits"
    balance = _force_balance(inputs.get("force_ratio", 0))
    return f"with {balance}"


def generate_interpretation(
    inputs: dict[str, Any],
    coherence_label: str,
    gate_failure_message: str,
) -> str:
    """
    Generate a deterministic interpretation sentence from structural evidence.
    Maximum 80 characters. Ends with a full stop.
    """
    if gate_failure_message:
        s = gate_failure_message
        return (s[:77] + "...") if len(s) > 80 else s

    traj  = str(inputs.get("structural_trajectory", "UNKNOWN")).strip()
    pred  = str(inputs.get("structural_prediction", "NO_PREDICTION")).strip()
    flow  = _flow_direction(inputs)
    qual  = _confidence_qualifier(coherence_label)
    tw    = _trajectory_word(traj)

    # Template 1 — FAIL prediction (TERMINAL or ACCELERATING_FAILURE)
    if pred == "FAIL":
        s = f"{tw} zone under {flow} — failure {qual}."
        return (s[:77] + "...") if len(s) > 80 else s

    # Template 2 — HOLD prediction
    if pred == "HOLD":
        note = _engagement_note(inputs)
        s = f"{tw} zone {note} — hold {qual}."
        return (s[:77] + "...") if len(s) > 80 else s

    # Template 3 — UNCERTAIN or NO_PREDICTION
    if pred in ("UNCERTAIN", "NO_PREDICTION"):
        if coherence_label == "INSUFFICIENT":
            note = "insufficient evidence for structural prediction"
        elif coherence_label == "WEAK":
            note = "conflicting signals, low confidence"
        else:
            note = "trajectory developing, await further visits"
        s = f"{tw} zone — {note}."
        return (s[:77] + "...") if len(s) > 80 else s

    # Template 4 — Catch-all
    s = f"{tw} zone — {pred} ({coherence_label.lower()})."
    return (s[:77] + "...") if len(s) > 80 else s


# ==============================================================================
# 9. MAIN FUNCTION — build_zone_synthesis
# ==============================================================================

def build_zone_synthesis(
    results_df:    pd.DataFrame,
    trajectory_df: pd.DataFrame,
    prediction_df: pd.DataFrame,
    episodes_df:   pd.DataFrame,
    run_utc:       str,
) -> pd.DataFrame:
    """
    Phase 1 Synthesis Engine entry point.

    Reads B10 (trajectory), B11 (prediction), and episode statistical context.
    Produces one MarketInterpretation per zone case.

    Output columns (13):
        analysis_run_utc, case_id, episode_id, zone_id, zone_mechanical_state,
        context, structure, engagement, flow, prediction, coherence,
        interpretation, research_only

    Research only. No scoring, lifecycle, replay, or dashboard changes.
    """
    if results_df.empty or trajectory_df.empty or prediction_df.empty:
        return pd.DataFrame()

    # Assemble inputs
    labeled = assemble_bundles(results_df, trajectory_df, prediction_df, episodes_df)

    # Build case metadata lookup
    meta_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}

    rows: list[dict] = []

    for case_id, inputs in labeled.items():
        m = meta_idx.get(case_id, {})

        # Step A: genuine conflict check
        genuine_conflict, conflict_note = check_genuine_conflict(inputs)
        if genuine_conflict:
            inputs["prediction_confidence"] = "LOW"

        # Step B: synthesis gate
        gate_passed, gate_failure_message = synthesis_gate(inputs)

        # Step C: coherence label
        if not gate_passed:
            coherence_label = "INSUFFICIENT"
        else:
            coherence_label = compute_coherence_label(inputs, genuine_conflict)

        # Step D: field compressors
        if gate_passed:
            ctx_str  = compress_context(inputs)
            str_str  = compress_structure(inputs)
            eng_str  = compress_engagement(inputs)
            flow_str = compress_flow(inputs)
            pred_str = compress_prediction(inputs, genuine_conflict)
            coh_str  = compress_coherence(coherence_label, conflict_note)
        else:
            ctx_str  = "Insufficient data"
            str_str  = str(inputs.get("structural_trajectory", "UNKNOWN"))
            eng_str  = "No visit data"
            flow_str = "Unknown"
            pred_str = "NO_PREDICTION (low)"
            coh_str  = "INSUFFICIENT"

        # Step E: interpretation sentence
        interp = generate_interpretation(inputs, coherence_label, gate_failure_message)

        rows.append({
            "analysis_run_utc":    run_utc,
            "case_id":             case_id,
            "episode_id":          m.get("episode_id", ""),
            "zone_id":             m.get("zone_id", ""),
            "zone_mechanical_state": m.get("zone_mechanical_state",
                                          inputs.get("zone_mechanical_state", "")),
            "context":             ctx_str,
            "structure":           str_str,
            "engagement":          eng_str,
            "flow":                flow_str,
            "prediction":          pred_str,
            "coherence":           coh_str,
            "interpretation":      interp,
            "research_only":       True,
        })

    return pd.DataFrame(rows)
