"""Shadow-only, path-confined JSONL parity logging (Phase 0E-3)."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


DEFAULT_PARITY_ROOT = (
    Path(__file__).resolve().parents[1] / "research" / "shadow_parity"
)
DEFAULT_PARITY_FILENAME = "parity.jsonl"


class ShadowParityLogger:
    """Best-effort JSONL writer confined to one shadow research directory."""

    def __init__(
        self,
        *,
        root: str | Path = DEFAULT_PARITY_ROOT,
        filename: str = DEFAULT_PARITY_FILENAME,
    ) -> None:
        self._root = Path(root).resolve()
        if (
            self._root.name != "shadow_parity"
            or self._root.parent.name != "research"
        ):
            raise ValueError(
                "parity root must be confined to research/shadow_parity"
            )
        if Path(filename).name != filename or not filename.endswith(".jsonl"):
            raise ValueError("parity filename must be a local .jsonl name")
        self._path = (self._root / filename).resolve()
        if self._path.parent != self._root:
            raise ValueError("parity log path escapes configured root")
        self._lock = threading.Lock()
        self._written = 0
        self._failed = 0

    @property
    def path(self) -> Path:
        return self._path

    @property
    def root(self) -> Path:
        return self._root

    def write(self, record: Mapping[str, Any]) -> bool:
        """Append one record. Never raise or affect shadow runtime success."""
        try:
            payload = json.dumps(
                _json_safe(deepcopy(dict(record))),
                sort_keys=True,
                separators=(",", ":"),
            )
            with self._lock:
                self._root.mkdir(parents=True, exist_ok=True)
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(payload + "\n")
                self._written += 1
            return True
        except BaseException:
            with self._lock:
                self._failed += 1
            return False

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "written": self._written,
                "failed": self._failed,
                "path": str(self._path),
            }


def compare_reference_values(
    reference: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, bool]:
    """Compare only reference keys that have an exact snapshot leaf match."""
    leaves: dict[str, Any] = {}
    _collect_leaves(snapshot, leaves)
    return {
        str(key): (key not in leaves or leaves[key] != value)
        for key, value in reference.items()
    }


def _collect_leaves(value: Any, leaves: dict[str, Any]) -> None:
    if not isinstance(value, Mapping):
        return
    for key, item in value.items():
        if isinstance(item, Mapping):
            _collect_leaves(item, leaves)
        elif key not in leaves:
            leaves[str(key)] = item


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


__all__ = [
    "DEFAULT_PARITY_FILENAME",
    "DEFAULT_PARITY_ROOT",
    "ShadowParityLogger",
    "compare_reference_values",
]


