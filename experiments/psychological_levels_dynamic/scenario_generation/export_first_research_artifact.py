"""Export the first permanent Project 2 research artifact."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_engine import (
    RESEARCH_ANALYSIS_ENGINE_VERSION,
    analyze_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_generator import (
    RESEARCH_ARTIFACT_GENERATOR_VERSION,
    build_research_artifact,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_exporter import (
    DEFAULT_RESEARCH_ARTIFACT_JSON_DIRECTORY,
    write_research_artifact_json,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_renderer import (
    render_research_artifact_json,
    research_artifact_json_render_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_report_generator import (
    RESEARCH_REPORT_GENERATOR_VERSION,
    build_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_first_research_campaign_100_execution import (
    _execute_campaign,
)

REPORT_ID = "PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT"
REPORT_VERSION = "1"
ANALYSIS_ID = "PHASE2E_RESEARCH_ANALYSIS_ENGINE"
ANALYSIS_VERSION = "1"
ARTIFACT_ID = "PHASE2F_RESEARCH_ARTIFACT"
ARTIFACT_VERSION = "1"

EXPECTED_ANALYSIS_FINGERPRINT = (
    "sha256:11eb46f171e7e1ce09dbd818234ec59e268b8901ebbe128993658353359929f1"
)
EXPECTED_ARTIFACT_FINGERPRINT = (
    "sha256:4a401701509dbaeaa2b52c30bd442768b29b11881ec19627ae4c4356ef47c1de"
)
EXPECTED_RENDER_FINGERPRINT = (
    "sha256:c9ccc23f8294b22a1228af054b38b0a1aa29d0e7862eb6cc54c417d7a7c2d2b5"
)
ARTIFACT_DIRECTORY = REPO_ROOT / DEFAULT_RESEARCH_ARTIFACT_JSON_DIRECTORY
ARTIFACT_PATH = ARTIFACT_DIRECTORY / "PHASE2F_RESEARCH_ARTIFACT__1.json"


def build_first_research_artifact_bytes() -> tuple[bytes, str, str, str]:
    campaign_result = _execute_campaign()
    report = build_research_campaign_report(
        campaign_result,
        report_id=REPORT_ID,
        report_version=REPORT_VERSION,
        report_generator_version=RESEARCH_REPORT_GENERATOR_VERSION,
    )
    analysis = analyze_research_campaign_report(
        report,
        analysis_id=ANALYSIS_ID,
        analysis_version=ANALYSIS_VERSION,
        analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
    )
    artifact = build_research_artifact(
        analysis,
        artifact_id=ARTIFACT_ID,
        artifact_version=ARTIFACT_VERSION,
        artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
    )
    rendered_bytes = render_research_artifact_json(artifact)
    render_fingerprint = research_artifact_json_render_fingerprint(rendered_bytes)
    return (
        rendered_bytes,
        analysis.campaign_analysis_fingerprint,
        artifact.artifact_fingerprint,
        render_fingerprint,
    )


def _validate_rendered_bytes(
    rendered_bytes: bytes,
    *,
    analysis_fingerprint: str,
    artifact_fingerprint: str,
    render_fingerprint: str,
) -> None:
    if analysis_fingerprint != EXPECTED_ANALYSIS_FINGERPRINT:
        raise RuntimeError("analysis fingerprint changed; aborting before export")
    if artifact_fingerprint != EXPECTED_ARTIFACT_FINGERPRINT:
        raise RuntimeError("artifact fingerprint changed; aborting before export")
    if render_fingerprint != EXPECTED_RENDER_FINGERPRINT:
        raise RuntimeError("render fingerprint changed; aborting before export")
    if not isinstance(rendered_bytes, bytes):
        raise TypeError("rendered artifact must be bytes")
    if rendered_bytes.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("rendered artifact contains UTF-8 BOM")
    if b"\r" in rendered_bytes:
        raise RuntimeError("rendered artifact contains CR bytes")
    if not rendered_bytes.endswith(b"\n") or rendered_bytes.endswith(b"\n\n"):
        raise RuntimeError("rendered artifact must contain exactly one trailing LF")
    if artifact_fingerprint.encode("ascii") not in rendered_bytes:
        raise RuntimeError("artifact fingerprint missing from rendered bytes")


def export_first_research_artifact() -> dict[str, object]:
    rendered_bytes, analysis_fingerprint, artifact_fingerprint, render_fingerprint = (
        build_first_research_artifact_bytes()
    )
    _validate_rendered_bytes(
        rendered_bytes,
        analysis_fingerprint=analysis_fingerprint,
        artifact_fingerprint=artifact_fingerprint,
        render_fingerprint=render_fingerprint,
    )
    result = write_research_artifact_json(
        rendered_bytes,
        ARTIFACT_DIRECTORY,
        ARTIFACT_ID,
        ARTIFACT_VERSION,
    )
    if result.export_status not in {"CREATED", "ALREADY_EXISTS_IDENTICAL"}:
        raise RuntimeError(f"unexpected export status: {result.export_status}")
    written_bytes = ARTIFACT_PATH.read_bytes()
    if written_bytes != rendered_bytes:
        raise RuntimeError("written artifact bytes do not match rendered bytes")
    if research_artifact_json_render_fingerprint(written_bytes) != EXPECTED_RENDER_FINGERPRINT:
        raise RuntimeError("written artifact render fingerprint mismatch")
    if EXPECTED_ARTIFACT_FINGERPRINT.encode("ascii") not in written_bytes:
        raise RuntimeError("written artifact fingerprint missing")
    return {
        "export_status": result.export_status,
        "artifact_path": str(ARTIFACT_PATH.as_posix()),
        "analysis_fingerprint": analysis_fingerprint,
        "artifact_fingerprint": artifact_fingerprint,
        "render_fingerprint": render_fingerprint,
        "byte_count": len(written_bytes),
    }


def main() -> None:
    summary = export_first_research_artifact()
    for key in (
        "export_status",
        "artifact_path",
        "analysis_fingerprint",
        "artifact_fingerprint",
        "render_fingerprint",
        "byte_count",
    ):
        print(f"{key}: {summary[key]}")
    print("PHASE2F_FIRST_RESEARCH_ARTIFACT_EXPORTED PASS")


if __name__ == "__main__":
    main()
