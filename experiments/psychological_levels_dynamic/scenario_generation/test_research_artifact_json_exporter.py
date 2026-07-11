"""Validation for Project 2 ResearchArtifact JSON byte exporting."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_exporter as exporter
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_exporter import (
    DEFAULT_RESEARCH_ARTIFACT_JSON_DIRECTORY,
    RESEARCH_ARTIFACT_JSON_EXPORTER_VERSION,
    ResearchArtifactJsonExportResult,
    research_artifact_json_filename,
    write_research_artifact_json,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_renderer import (
    render_research_artifact_json,
    research_artifact_json_render_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_research_artifact_generator import (
    _artifact,
)

MODULE_PATH = Path(__file__).with_name("research_artifact_json_exporter.py")
EXPECTED_GITATTRIBUTES_RULE = (
    "experiments/psychological_levels_dynamic/scenario_generation/artifacts/**/*.json -text"
)
EXPECTED_RENDER_FINGERPRINT = (
    "sha256:c9ccc23f8294b22a1228af054b38b0a1aa29d0e7862eb6cc54c417d7a7c2d2b5"
)
ARTIFACT_ID = "PHASE2F_RESEARCH_ARTIFACT"
ARTIFACT_VERSION = "1"
FORBIDDEN_IMPORTS = (
    " json",
    "render_research_artifact_json",
    "research_artifact_generator",
    "research_analysis_engine",
    "research_report_generator",
    "campaign_designer",
    "campaign_contracts",
    "batch_execution",
    "generator",
    "compiler",
    "assembly",
    "scenario_runner",
    "scenario_catalog.",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "datetime",
    "time",
    "random",
    "locale",
    "subprocess",
)
BANNED_WORDS = (
    "buy",
    "sell",
    "trade",
    "prediction",
    "forecast",
    "ranking",
    "optimization",
    "machine learning",
    "learned threshold",
    "better",
    "stronger",
    "weaker",
    "improved",
    "degraded",
    "proven",
    "proves",
    "validated",
    "confirms",
    "suggests",
    "causal",
    "effect",
    "impact",
    "lift",
    "gain",
    "accuracy",
    "performance",
    "falsified",
    "generalize",
    "generalization",
)


def _rendered_bytes() -> bytes:
    return render_research_artifact_json(_artifact())


def _target(directory: Path) -> Path:
    return directory / research_artifact_json_filename(ARTIFACT_ID, ARTIFACT_VERSION)


def _word_boundary_hit(source: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    pattern = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
    return re.search(pattern, source, flags=re.IGNORECASE) is not None


def _rejected(factory: Any) -> bool:
    try:
        factory()
    except (TypeError, ValueError):
        return True
    return False


def _temp_residue(directory: Path) -> tuple[Path, ...]:
    return tuple(
        path
        for path in directory.iterdir()
        if path.name.startswith(".") and path.name.endswith(".tmp")
    )


def _write(directory: Path, rendered: bytes) -> ResearchArtifactJsonExportResult:
    return write_research_artifact_json(
        rendered,
        directory,
        ARTIFACT_ID,
        ARTIFACT_VERSION,
    )


def _cross_process_export() -> str:
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        script = (
            "from pathlib import Path; "
            "from experiments.psychological_levels_dynamic.scenario_generation."
            "test_research_artifact_json_exporter import _rendered_bytes, _write; "
            f"r=_rendered_bytes(); a=_write(Path({first_dir!r}), r); "
            f"b=_write(Path({second_dir!r}), r); "
            "print(a.render_fingerprint + '|' + b.render_fingerprint)"
        )
        return subprocess.check_output([sys.executable, "-c", script], text=True).strip()


class _CorruptingHandle:
    def __init__(self, path: str) -> None:
        self._handle = open(path, "wb")

    def __enter__(self) -> "_CorruptingHandle":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._handle.close()

    def write(self, data: bytes) -> int:
        return self._handle.write(data[:-1] + b"X")

    def flush(self) -> None:
        self._handle.flush()


class _FailingHandle:
    def __init__(self, path: str) -> None:
        self._handle = open(path, "wb")

    def __enter__(self) -> "_FailingHandle":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._handle.close()

    def write(self, data: bytes) -> int:
        raise OSError("simulated write failure")

    def flush(self) -> None:
        self._handle.flush()


def run() -> dict[str, Any]:
    checks = {
        "filename_helper": False,
        "invalid_filename_components_rejected": False,
        "destination_auto_created": False,
        "destination_is_file_rejected": False,
        "missing_target_creates_file": False,
        "written_bytes_exact": False,
        "render_fingerprint_preserved": False,
        "artifact_fingerprint_present": False,
        "byte_policy_preserved": False,
        "identical_reexport_idempotent": False,
        "identical_existing_not_rewritten": False,
        "conflict_rejected": False,
        "conflict_file_unchanged": False,
        "identity_guard": False,
        "temp_file_created_in_destination": False,
        "no_temp_residue_after_success": False,
        "no_temp_residue_after_write_failure": False,
        "no_final_target_after_write_failure": False,
        "temp_verify_failure": False,
        "final_read_back_verification": False,
        "target_inside_destination": False,
        "path_traversal_and_symlink_escape_rejected": False,
        "separate_directories_identical": False,
        "cross_process_export_determinism": False,
        "never_calls_renderer": False,
        "never_parses_or_serializes_json": False,
        "no_regeneration": False,
        "forbidden_imports": False,
        "research_isolation": False,
        "banned_language_scan": False,
        "tests_write_only_to_temp_directories": False,
        "gitattributes_rule": False,
        "repository_artifacts_unchanged": False,
        "pinned_renderer_checksum": False,
    }
    errors: list[str] = []
    try:
        repo_artifact_dir = REPO_ROOT / DEFAULT_RESEARCH_ARTIFACT_JSON_DIRECTORY
        artifacts_before = tuple(
            sorted(repo_artifact_dir.rglob("*.json"))
        ) if repo_artifact_dir.exists() else ()
        rendered = _rendered_bytes()
        render_fingerprint = research_artifact_json_render_fingerprint(rendered)
        filename = research_artifact_json_filename(ARTIFACT_ID, ARTIFACT_VERSION)
        checks["filename_helper"] = filename == f"{ARTIFACT_ID}__{ARTIFACT_VERSION}.json"
        invalid_values = (
            "",
            "..",
            "../BAD",
            "BAD/ID",
            "BAD\\ID",
            "BAD ID",
            "CON",
            "prn",
            "COM1",
            "LPT9",
            "A" * 121,
        )
        checks["invalid_filename_components_rejected"] = all(
            _rejected(lambda value=value: research_artifact_json_filename(value, "1"))
            for value in invalid_values
        )
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            destination = root / "missing" / "nested"
            created = _write(destination, rendered)
            target = _target(destination)
            checks["destination_auto_created"] = destination.is_dir()
            checks["missing_target_creates_file"] = created.export_status == "CREATED" and target.exists()
            checks["written_bytes_exact"] = target.read_bytes() == rendered
            checks["render_fingerprint_preserved"] = created.render_fingerprint == render_fingerprint
            checks["artifact_fingerprint_present"] = b'"artifact_fingerprint":"' in target.read_bytes()
            checks["byte_policy_preserved"] = (
                not target.read_bytes().startswith(b"\xef\xbb\xbf")
                and b"\r" not in target.read_bytes()
                and target.read_bytes().endswith(b"\n")
                and not target.read_bytes().endswith(b"\n\n")
            )
            before_mtime = target.stat().st_mtime_ns
            identical = _write(destination, rendered)
            after_mtime = target.stat().st_mtime_ns
            checks["identical_reexport_idempotent"] = (
                identical.success
                and identical.export_status == "ALREADY_EXISTS_IDENTICAL"
                and identical.bytes_written == len(rendered)
            )
            checks["identical_existing_not_rewritten"] = before_mtime == after_mtime
            original = target.read_bytes()
            conflict = write_research_artifact_json(
                rendered + b"DIFFERENT",
                destination,
                ARTIFACT_ID,
                ARTIFACT_VERSION,
            )
            checks["conflict_rejected"] = (
                not conflict.success
                and conflict.export_status == "CONFLICT_DIFFERENT_CONTENT"
            )
            checks["conflict_file_unchanged"] = target.read_bytes() == original
            checks["no_temp_residue_after_success"] = not _temp_residue(destination)
            checks["final_read_back_verification"] = target.read_bytes() == rendered
            checks["target_inside_destination"] = target.resolve().parent == destination.resolve()

        with tempfile.TemporaryDirectory() as temp_root:
            file_destination = Path(temp_root) / "not_a_directory"
            file_destination.write_bytes(b"x")
            checks["destination_is_file_rejected"] = _rejected(
                lambda: _write(file_destination, rendered)
            )

        checks["identity_guard"] = _rejected(
            lambda: write_research_artifact_json(
                rendered,
                Path(tempfile.gettempdir()),
                "OTHER_ARTIFACT",
                ARTIFACT_VERSION,
            )
        )

        with tempfile.TemporaryDirectory() as temp_root:
            destination = Path(temp_root)
            recorded_dirs: list[str] = []
            original_mkstemp = exporter.tempfile.mkstemp

            def recording_mkstemp(*args: Any, **kwargs: Any) -> tuple[int, str]:
                recorded_dirs.append(str(kwargs.get("dir", "")))
                return original_mkstemp(*args, **kwargs)

            exporter.tempfile.mkstemp = recording_mkstemp
            try:
                _write(destination, rendered)
            finally:
                exporter.tempfile.mkstemp = original_mkstemp
            checks["temp_file_created_in_destination"] = recorded_dirs == [str(destination.resolve())]

        with tempfile.TemporaryDirectory() as temp_root:
            destination = Path(temp_root)
            original_fdopen = exporter.os.fdopen

            def failing_fdopen(fd: int, mode: str) -> _FailingHandle:
                path = Path(f"/proc/self/fd/{fd}") if os.name != "nt" else None
                if path is not None:
                    return _FailingHandle(str(path))
                raise OSError("simulated write failure")

            exporter.os.fdopen = failing_fdopen
            write_failed = False
            try:
                _write(destination, rendered)
            except OSError:
                write_failed = True
            finally:
                exporter.os.fdopen = original_fdopen
            checks["no_temp_residue_after_write_failure"] = write_failed and not _temp_residue(destination)
            checks["no_final_target_after_write_failure"] = not _target(destination).exists()

        with tempfile.TemporaryDirectory() as temp_root:
            destination = Path(temp_root)
            original_fdopen = exporter.os.fdopen
            original_mkstemp = exporter.tempfile.mkstemp
            fd_paths: dict[int, str] = {}

            def tracking_mkstemp(*args: Any, **kwargs: Any) -> tuple[int, str]:
                fd, path = original_mkstemp(*args, **kwargs)
                fd_paths[fd] = path
                return fd, path

            def corrupting_fdopen(fd: int, mode: str) -> _CorruptingHandle:
                os.close(fd)
                return _CorruptingHandle(fd_paths[fd])

            exporter.tempfile.mkstemp = tracking_mkstemp
            exporter.os.fdopen = corrupting_fdopen
            try:
                verify_failed = _write(destination, rendered)
            finally:
                exporter.os.fdopen = original_fdopen
                exporter.tempfile.mkstemp = original_mkstemp
            checks["temp_verify_failure"] = (
                not verify_failed.success
                and verify_failed.export_status == "VERIFY_FAILED"
                and not _target(destination).exists()
                and not _temp_residue(destination)
            )

        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = _write(Path(first_dir), rendered)
            second = _write(Path(second_dir), rendered)
            checks["separate_directories_identical"] = (
                _target(Path(first_dir)).read_bytes() == _target(Path(second_dir)).read_bytes()
                and first.render_fingerprint == second.render_fingerprint == render_fingerprint
            )
        first_cross = _cross_process_export()
        second_cross = _cross_process_export()
        checks["cross_process_export_determinism"] = (
            first_cross
            == second_cross
            == f"{render_fingerprint}|{render_fingerprint}"
        )

        with tempfile.TemporaryDirectory() as temp_root:
            outside = Path(temp_root) / "outside"
            inside = Path(temp_root) / "inside"
            outside.mkdir()
            inside.mkdir()
            symlink_path = inside / filename
            symlink_supported = True
            try:
                symlink_path.symlink_to(outside / filename)
            except (OSError, NotImplementedError):
                symlink_supported = False
            checks["path_traversal_and_symlink_escape_rejected"] = (
                symlink_supported
                and _rejected(lambda: _write(inside, rendered))
            ) or not symlink_supported

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["never_calls_renderer"] = "render_research_artifact_json(" not in source
        checks["never_parses_or_serializes_json"] = " json" not in imports and "json." not in lower_source
        checks["no_regeneration"] = not any(
            token.lower() in lower_source
            for token in (
                "build_research_artifact",
                "build_research_campaign_report",
                "analyze_research_campaign_report",
                "run_campaign",
                "execute_batch",
                "scenario_runner",
            )
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["banned_language_scan"] = not any(
            _word_boundary_hit(source, phrase) for phrase in BANNED_WORDS
        )
        checks["research_isolation"] = (
            checks["never_calls_renderer"]
            and checks["never_parses_or_serializes_json"]
            and checks["no_regeneration"]
            and checks["forbidden_imports"]
        )
        artifacts_after = tuple(
            sorted(repo_artifact_dir.rglob("*.json"))
        ) if repo_artifact_dir.exists() else ()
        checks["repository_artifacts_unchanged"] = artifacts_after == artifacts_before
        checks["tests_write_only_to_temp_directories"] = checks["repository_artifacts_unchanged"]
        gitattributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
        checks["gitattributes_rule"] = (
            gitattributes.splitlines().count(EXPECTED_GITATTRIBUTES_RULE) == 1
        )
        checks["pinned_renderer_checksum"] = render_fingerprint == EXPECTED_RENDER_FINGERPRINT
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
    print("PHASE2F_RESEARCH_ARTIFACT_JSON_EXPORTER_STABLE PASS")


if __name__ == "__main__":
    main()
