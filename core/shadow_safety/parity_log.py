"""Shadow-only parity log writer interface (Phase 0A).

Appends JSON-line records to research/shadow_parity/ ONLY. Any path that would
escape that directory is rejected at construction. No production output is
touched and no production module imports this.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
PARITY_DIR = REPO_ROOT / "research" / "shadow_parity"
DEFAULT_FILENAME = "shadow_parity_log.jsonl"


class ParityLogWriter:
    """Append-only JSONL writer confined to the parity directory."""

    def __init__(
        self,
        filename: str = DEFAULT_FILENAME,
        *,
        base_dir: str | Path | None = None,
    ) -> None:
        base = (Path(base_dir) if base_dir is not None else PARITY_DIR).resolve()
        target = (base / filename).resolve()
        # Containment guard: the resolved target MUST live inside base.
        if target != base and base not in target.parents:
            raise ValueError(
                f"parity log path escapes {base}: {target}"
            )
        self._base = base
        self._path = target
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def base_dir(self) -> Path:
        return self._base

    def write(self, record: Mapping[str, Any]) -> None:
        """Append one JSON line (with a UTC timestamp). Shadow-only."""
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        payload = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            **dict(record),
        }
        line = json.dumps(payload, default=str, sort_keys=True)
        with self._lock:
            self._base.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def write_many(self, records: Iterable[Mapping[str, Any]]) -> int:
        count = 0
        for record in records:
            self.write(record)
            count += 1
        return count


__all__ = [
    "DEFAULT_FILENAME",
    "PARITY_DIR",
    "ParityLogWriter",
]
