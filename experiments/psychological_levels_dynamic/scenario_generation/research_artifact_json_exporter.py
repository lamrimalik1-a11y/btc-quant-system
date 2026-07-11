"""Byte-only JSON exporter for Project 2 research artifacts."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_renderer import (
    research_artifact_json_render_fingerprint,
)

RESEARCH_ARTIFACT_JSON_EXPORTER_VERSION = "PHASE2F_RESEARCH_ARTIFACT_JSON_EXPORTER_V1"
DEFAULT_RESEARCH_ARTIFACT_JSON_DIRECTORY = (
    "experiments/psychological_levels_dynamic/scenario_generation/artifacts/json"
)

_COMPONENT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_RESERVED_WINDOWS_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_ALLOWED_STATUSES = frozenset(
    {
        "CREATED",
        "ALREADY_EXISTS_IDENTICAL",
        "CONFLICT_DIFFERENT_CONTENT",
        "VERIFY_FAILED",
    }
)


@dataclass(frozen=True)
class ResearchArtifactJsonExportResult:
    success: bool
    export_status: str
    filename: str
    destination_directory: str
    bytes_written: int
    render_fingerprint: str
    exporter_version: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.export_status not in _ALLOWED_STATUSES:
            raise ValueError("invalid export_status")
        if self.export_status in {"CREATED", "ALREADY_EXISTS_IDENTICAL"} and not self.success:
            raise ValueError("successful statuses require success=True")
        if self.export_status in {"CONFLICT_DIFFERENT_CONTENT", "VERIFY_FAILED"} and self.success:
            raise ValueError("failure statuses require success=False")
        _require_non_empty("filename", self.filename)
        _require_non_empty("destination_directory", self.destination_directory)
        if not isinstance(self.bytes_written, int) or self.bytes_written < 0:
            raise ValueError("bytes_written must be non-negative")
        _require_fingerprint("render_fingerprint", self.render_fingerprint)
        _require_non_empty("exporter_version", self.exporter_version)
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("diagnostics must be tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.diagnostics):
            raise ValueError("diagnostics must contain non-empty strings")
        if tuple(sorted(self.diagnostics)) != self.diagnostics:
            raise ValueError("diagnostics must be sorted canonically")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


def _validate_filename_component(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if value.upper() in _RESERVED_WINDOWS_NAMES:
        raise ValueError(f"{name} is a reserved Windows device name")
    if not _COMPONENT_PATTERN.fullmatch(value):
        raise ValueError(f"{name} contains unsupported filename characters")


def research_artifact_json_filename(artifact_id: str, artifact_version: str) -> str:
    _validate_filename_component("artifact_id", artifact_id)
    _validate_filename_component("artifact_version", artifact_version)
    filename = f"{artifact_id}__{artifact_version}.json"
    if len(filename) > 120:
        raise ValueError("filename exceeds deterministic length limit")
    return filename


def write_research_artifact_json(
    rendered_bytes: bytes,
    destination_directory: object,
    artifact_id: str,
    artifact_version: str,
) -> ResearchArtifactJsonExportResult:
    if not isinstance(rendered_bytes, bytes):
        raise TypeError("rendered_bytes must be bytes")
    filename = research_artifact_json_filename(artifact_id, artifact_version)
    _verify_identity_fragments(rendered_bytes, artifact_id, artifact_version)
    render_fingerprint = research_artifact_json_render_fingerprint(rendered_bytes)

    destination = Path(destination_directory)
    if destination.exists() and not destination.is_dir():
        raise ValueError("destination_directory must be a directory")
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    target = (resolved_destination / filename).resolve()
    _verify_inside_directory(resolved_destination, target)

    if target.is_symlink():
        raise ValueError("target path must not be a symlink")
    if target.exists():
        existing_bytes = target.read_bytes()
        if existing_bytes == rendered_bytes:
            return _result(
                success=True,
                export_status="ALREADY_EXISTS_IDENTICAL",
                filename=filename,
                destination_directory=str(resolved_destination),
                bytes_written=len(rendered_bytes),
                render_fingerprint=render_fingerprint,
                diagnostics=("ALREADY_EXISTS_IDENTICAL",),
            )
        return _result(
            success=False,
            export_status="CONFLICT_DIFFERENT_CONTENT",
            filename=filename,
            destination_directory=str(resolved_destination),
            bytes_written=0,
            render_fingerprint=render_fingerprint,
            diagnostics=("CONFLICT_DIFFERENT_CONTENT",),
        )

    temp_path: str | None = None
    file_descriptor: int | None = None
    try:
        file_descriptor, temp_path = tempfile.mkstemp(
            prefix=f".{filename}.",
            suffix=".tmp",
            dir=str(resolved_destination),
        )
        with os.fdopen(file_descriptor, "wb") as handle:
            file_descriptor = None
            handle.write(rendered_bytes)
            handle.flush()
        temp = Path(temp_path)
        _verify_inside_directory(resolved_destination, temp.resolve())
        temp_bytes = temp.read_bytes()
        if (
            temp_bytes != rendered_bytes
            or research_artifact_json_render_fingerprint(temp_bytes) != render_fingerprint
        ):
            _cleanup_temp(temp_path)
            return _result(
                success=False,
                export_status="VERIFY_FAILED",
                filename=filename,
                destination_directory=str(resolved_destination),
                bytes_written=0,
                render_fingerprint=render_fingerprint,
                diagnostics=("TEMP_VERIFY_FAILED", "VERIFY_FAILED"),
            )
        if target.exists():
            _cleanup_temp(temp_path)
            existing_bytes = target.read_bytes()
            if existing_bytes == rendered_bytes:
                return _result(
                    success=True,
                    export_status="ALREADY_EXISTS_IDENTICAL",
                    filename=filename,
                    destination_directory=str(resolved_destination),
                    bytes_written=len(rendered_bytes),
                    render_fingerprint=render_fingerprint,
                    diagnostics=("ALREADY_EXISTS_IDENTICAL",),
                )
            return _result(
                success=False,
                export_status="CONFLICT_DIFFERENT_CONTENT",
                filename=filename,
                destination_directory=str(resolved_destination),
                bytes_written=0,
                render_fingerprint=render_fingerprint,
                diagnostics=("CONFLICT_DIFFERENT_CONTENT",),
            )
        os.replace(temp_path, target)
        temp_path = None
        target_bytes = target.read_bytes()
        if (
            target_bytes != rendered_bytes
            or research_artifact_json_render_fingerprint(target_bytes) != render_fingerprint
        ):
            return _result(
                success=False,
                export_status="VERIFY_FAILED",
                filename=filename,
                destination_directory=str(resolved_destination),
                bytes_written=0,
                render_fingerprint=render_fingerprint,
                diagnostics=("TARGET_VERIFY_FAILED", "VERIFY_FAILED"),
            )
        return _result(
            success=True,
            export_status="CREATED",
            filename=filename,
            destination_directory=str(resolved_destination),
            bytes_written=len(rendered_bytes),
            render_fingerprint=render_fingerprint,
            diagnostics=("CREATED",),
        )
    finally:
        if file_descriptor is not None:
            try:
                os.close(file_descriptor)
            except OSError:
                pass
        if temp_path is not None:
            _cleanup_temp(temp_path)


def _verify_identity_fragments(rendered_bytes: bytes, artifact_id: str, artifact_version: str) -> None:
    id_fragment = f'"artifact_id":"{artifact_id}"'.encode("ascii")
    version_fragment = f'"artifact_version":"{artifact_version}"'.encode("ascii")
    if id_fragment not in rendered_bytes or version_fragment not in rendered_bytes:
        raise ValueError("rendered_bytes do not match artifact identity")


def _verify_inside_directory(directory: Path, path: Path) -> None:
    try:
        path.relative_to(directory)
    except ValueError as exc:
        raise ValueError("target path must remain inside destination_directory") from exc


def _cleanup_temp(temp_path: str) -> None:
    try:
        Path(temp_path).unlink(missing_ok=True)
    except OSError:
        pass


def _result(
    *,
    success: bool,
    export_status: str,
    filename: str,
    destination_directory: str,
    bytes_written: int,
    render_fingerprint: str,
    diagnostics: tuple[str, ...],
) -> ResearchArtifactJsonExportResult:
    return ResearchArtifactJsonExportResult(
        success=success,
        export_status=export_status,
        filename=filename,
        destination_directory=destination_directory,
        bytes_written=bytes_written,
        render_fingerprint=render_fingerprint,
        exporter_version=RESEARCH_ARTIFACT_JSON_EXPORTER_VERSION,
        diagnostics=tuple(sorted(diagnostics)),
    )
