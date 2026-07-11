"""Pure canonical JSON renderer for Project 2 research artifacts."""

from __future__ import annotations

import hashlib
import json

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    _canonical,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_contracts import (
    ResearchArtifact,
)

RESEARCH_ARTIFACT_JSON_RENDERER_VERSION = "PHASE2F_RESEARCH_ARTIFACT_JSON_RENDERER_V1"


def render_research_artifact_json(artifact: ResearchArtifact) -> bytes:
    if not isinstance(artifact, ResearchArtifact):
        raise TypeError("artifact must be ResearchArtifact")
    canonical_json = json.dumps(
        _canonical(artifact),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (canonical_json + "\n").encode("utf-8")


def research_artifact_json_render_fingerprint(rendered_bytes: bytes) -> str:
    if not isinstance(rendered_bytes, bytes):
        raise TypeError("rendered_bytes must be bytes")
    return "sha256:" + hashlib.sha256(rendered_bytes).hexdigest()
