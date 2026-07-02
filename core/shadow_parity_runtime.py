"""Best-effort parity logging wrapper for the passive shadow runtime."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from core.canonical_snapshot import SNAPSHOT_SECTIONS
from core.passive_shadow_runtime import PassiveShadowRuntimeHandler
from core.shadow_parity_logger import (
    ShadowParityLogger,
    compare_reference_values,
)


class ParityLoggingShadowHandler:
    """Run the shadow runtime, then append a non-authoritative parity record."""

    def __init__(
        self,
        *,
        runtime: PassiveShadowRuntimeHandler | None = None,
        logger: ShadowParityLogger | None = None,
        counters_provider: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self.runtime = runtime or PassiveShadowRuntimeHandler()
        self.logger = logger or ShadowParityLogger()
        self._counters_provider = counters_provider

    @property
    def store(self):
        return self.runtime.store

    def set_counters_provider(
        self,
        provider: Callable[[], Mapping[str, Any]] | None,
    ) -> None:
        self._counters_provider = provider

    def __call__(self, payload: Any) -> None:
        started = time.perf_counter()
        data = _payload_dict(payload)
        global_key = str(data.get("global_zone_key", ""))
        before = self.store.get_current(global_key) if global_key else None

        try:
            self.runtime(payload)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:
            current = self.store.get_current(global_key) if global_key else None
            self._write(
                data,
                before,
                current,
                started,
                event_status="FAILED",
                error=exc,
            )
            raise

        current = self.store.get_current(global_key) if global_key else None
        self._write(
            data,
            before,
            current,
            started,
            event_status="PROCESSED",
            error=None,
        )

    def _write(
        self,
        data: Mapping[str, Any],
        before: Any,
        current: Any,
        started: float,
        *,
        event_status: str,
        error: BaseException | None,
    ) -> None:
        shadow_values = current.to_dict() if current is not None else {}
        references = _reference_values(data)
        row_id = _last_row_id(data)
        sections = _changed_sections(before, current)
        counters = _safe_counters(self._counters_provider)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload_id": data.get("payload_id", ""),
            "session_id": data.get("session_id", ""),
            "global_zone_key": data.get("global_zone_key", ""),
            "row_id": row_id,
            "row_index": row_id,
            "event_status": event_status,
            "refresh_plan_id": (
                current.source_plan_id if current is not None else ""
            ),
            "snapshot_revision": (
                current.revision if current is not None else None
            ),
            "sections_updated": sections,
            "production_reference_values": references,
            "shadow_snapshot_values": shadow_values,
            "mismatch_flags": compare_reference_values(
                references,
                shadow_values,
            ),
            "processing_latency_ms": (
                (time.perf_counter() - started) * 1000.0
            ),
            "queue_worker_counters": counters,
            "error_status": (
                "OK" if error is None else type(error).__name__
            ),
            "error_message": "" if error is None else str(error),
            "shadow_only": True,
            "production_effects": False,
        }
        # Shadow parity is observational. Writer failure is intentionally
        # ignored and can never change runtime or worker success.
        self.logger.write(record)


def _payload_dict(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    to_dict = getattr(payload, "to_dict", None)
    try:
        value = to_dict() if callable(to_dict) else {}
    except Exception:
        return {}
    return value if isinstance(value, Mapping) else {}


def _reference_values(data: Mapping[str, Any]) -> dict[str, Any]:
    explicit = data.get("production_reference_values")
    if isinstance(explicit, Mapping):
        return dict(explicit)
    result_row = data.get("result_row")
    return dict(result_row) if isinstance(result_row, Mapping) else {}


def _last_row_id(data: Mapping[str, Any]) -> Any:
    rows = data.get("rows")
    if not isinstance(rows, (list, tuple)) or not rows:
        return None
    row = rows[-1]
    if not isinstance(row, Mapping):
        return None
    return row.get("row_index", row.get("row_id"))


def _changed_sections(before: Any, current: Any) -> list[str]:
    if current is None:
        return []
    if before is None:
        return [
            section
            for section in SNAPSHOT_SECTIONS
            if bool(getattr(current, section))
        ]
    return [
        section
        for section in SNAPSHOT_SECTIONS
        if dict(getattr(before, section)) != dict(getattr(current, section))
    ]


def _safe_counters(
    provider: Callable[[], Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if provider is None:
        return {}
    try:
        value = provider()
        return dict(value) if isinstance(value, Mapping) else {}
    except Exception:
        return {}


__all__ = ["ParityLoggingShadowHandler"]
