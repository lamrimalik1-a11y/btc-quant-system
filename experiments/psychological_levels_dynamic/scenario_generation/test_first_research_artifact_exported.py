"""Read-only regression for the first permanent Project 2 research artifact."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.export_first_research_artifact import (
    ARTIFACT_PATH,
    EXPECTED_ANALYSIS_FINGERPRINT,
    EXPECTED_ARTIFACT_FINGERPRINT,
    EXPECTED_RENDER_FINGERPRINT,
    build_first_research_artifact_bytes,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_renderer import (
    research_artifact_json_render_fingerprint,
)

EXPECTED_FILENAME = "PHASE2F_RESEARCH_ARTIFACT__1.json"
EXPECTED_GITATTRIBUTES_RULE = (
    "experiments/psychological_levels_dynamic/scenario_generation/artifacts/**/*.json -text"
)


def _word_boundary_hit(source: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    pattern = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
    return re.search(pattern, source, flags=re.IGNORECASE) is not None


def run() -> dict[str, Any]:
    checks = {
        "artifact_exists": False,
        "regenerated_bytes_match": False,
        "render_checksum": False,
        "embedded_artifact_fingerprint": False,
        "analysis_fingerprint": False,
        "no_bom": False,
        "no_cr_bytes": False,
        "single_trailing_lf": False,
        "strict_utf8_ascii_safe": False,
        "single_json_artifact": False,
        "filename_exact": False,
        "gitattributes_rule": False,
        "git_attribute_text_unset": False,
        "test_is_read_only": False,
    }
    errors: list[str] = []
    try:
        rendered_bytes, analysis_fingerprint, artifact_fingerprint, render_fingerprint = (
            build_first_research_artifact_bytes()
        )
        artifact_bytes = ARTIFACT_PATH.read_bytes()
        parsed = json.loads(artifact_bytes.decode("utf-8", errors="strict"))
        checks["artifact_exists"] = ARTIFACT_PATH.exists()
        checks["regenerated_bytes_match"] = artifact_bytes == rendered_bytes
        checks["render_checksum"] = (
            research_artifact_json_render_fingerprint(artifact_bytes)
            == render_fingerprint
            == EXPECTED_RENDER_FINGERPRINT
        )
        checks["embedded_artifact_fingerprint"] = (
            parsed["artifact_fingerprint"]
            == artifact_fingerprint
            == EXPECTED_ARTIFACT_FINGERPRINT
        )
        checks["analysis_fingerprint"] = analysis_fingerprint == EXPECTED_ANALYSIS_FINGERPRINT
        checks["no_bom"] = not artifact_bytes.startswith(b"\xef\xbb\xbf")
        checks["no_cr_bytes"] = b"\r" not in artifact_bytes
        checks["single_trailing_lf"] = artifact_bytes.endswith(b"\n") and not artifact_bytes.endswith(b"\n\n")
        decoded = artifact_bytes.decode("utf-8", errors="strict")
        checks["strict_utf8_ascii_safe"] = decoded.isascii()
        artifact_files = tuple(sorted(ARTIFACT_PATH.parent.glob("*.json")))
        checks["single_json_artifact"] = artifact_files == (ARTIFACT_PATH,)
        checks["filename_exact"] = ARTIFACT_PATH.name == EXPECTED_FILENAME
        gitattributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
        checks["gitattributes_rule"] = (
            gitattributes.splitlines().count(EXPECTED_GITATTRIBUTES_RULE) == 1
        )
        attr_output = subprocess.check_output(
            ["git", "check-attr", "text", "--", str(ARTIFACT_PATH.relative_to(REPO_ROOT))],
            text=True,
            cwd=REPO_ROOT,
        ).strip()
        checks["git_attribute_text_unset"] = attr_output.endswith("text: unset")
        source = Path(__file__).read_text(encoding="utf-8")
        forbidden_tokens = (
            "write_" + "research_artifact_json(",
            "export_" + "first_research_artifact(",
            "." + "write_bytes(",
            "." + "write_text(",
            "." + "mkdir(",
            "temp" + "file",
        )
        checks["test_is_read_only"] = not any(
            _word_boundary_hit(source, token) for token in forbidden_tokens
        )
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "checks": checks,
        "errors": errors,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"errors: {report['errors']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2F_FIRST_RESEARCH_ARTIFACT_EXPORTED PASS")


if __name__ == "__main__":
    main()
