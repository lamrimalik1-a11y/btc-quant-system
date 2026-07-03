"""Daily observation session identity and boundary metadata.

Stage 1 is intentionally passive: it creates the current-session directory
and manifest only. It does not reroute writers, archive files, reset memory,
or participate in stream processing.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ALGERIA_TIMEZONE_NAME = "Africa/Algiers"
ALGERIA_TIMEZONE = ZoneInfo(ALGERIA_TIMEZONE_NAME)
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
SESSION_IDENTITY_FIELDNAMES = [
    "session_id",
    "market_date",
    "session_episode_id",
    "global_episode_key",
    "global_case_id",
]


def _as_utc(timestamp: Any = None) -> datetime:
    if timestamp is None:
        return datetime.now(timezone.utc)
    if not isinstance(timestamp, datetime):
        if isinstance(timestamp, (int, float)):
            value = float(timestamp)
            if abs(value) >= 1_000_000_000_000:
                value /= 1000.0
            return datetime.fromtimestamp(value, tz=timezone.utc)
        text = str(timestamp).strip()
        if not text:
            return datetime.now(timezone.utc)
        try:
            numeric = float(text)
        except ValueError:
            normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
            timestamp = datetime.fromisoformat(normalized)
        else:
            if abs(numeric) >= 1_000_000_000_000:
                numeric /= 1000.0
            return datetime.fromtimestamp(numeric, tz=timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _isoformat(timestamp: datetime) -> str:
    return timestamp.isoformat(timespec="seconds")


@dataclass(frozen=True)
class DailySessionManifest:
    symbol: str
    session_id: str
    market_date: str
    timezone: str
    local_start: str
    local_end: str
    utc_start: str
    utc_end: str
    status: str
    created_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DailySessionController:
    """Passive Stage 1 controller for daily session identity metadata."""

    def __init__(
        self,
        symbol: str = DEFAULT_SYMBOL,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        self.symbol = normalized_symbol
        self.output_dir = Path(output_dir)
        self.live_dir = self.output_dir / "live"
        self.current_dir = self.live_dir / "current"
        self.current_session_file = self.live_dir / "current_session.json"

    def build_manifest(
        self,
        timestamp_utc: datetime | None = None,
        status: str = "ACTIVE",
    ) -> DailySessionManifest:
        created_at_utc = _as_utc(timestamp_utc)
        local_timestamp = created_at_utc.astimezone(ALGERIA_TIMEZONE)
        market_date = local_timestamp.date()

        local_start = datetime.combine(
            market_date,
            time.min,
            tzinfo=ALGERIA_TIMEZONE,
        )
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc)
        utc_end = local_end.astimezone(timezone.utc)

        session_id = (
            f"{self.symbol}_{market_date.isoformat()}_"
            f"{utc_start.strftime('%H%M%SZ')}"
        )

        return DailySessionManifest(
            symbol=self.symbol,
            session_id=session_id,
            market_date=market_date.isoformat(),
            timezone=ALGERIA_TIMEZONE_NAME,
            local_start=_isoformat(local_start),
            local_end=_isoformat(local_end),
            utc_start=_isoformat(utc_start),
            utc_end=_isoformat(utc_end),
            status=str(status),
            created_at_utc=_isoformat(created_at_utc),
        )

    def write_current_session(
        self,
        manifest: DailySessionManifest,
    ) -> Path:
        self.current_dir.mkdir(parents=True, exist_ok=True)
        temporary_file = self.current_session_file.with_suffix(".json.tmp")
        temporary_file.write_text(
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_file.replace(self.current_session_file)
        return self.current_session_file

    def initialize(
        self,
        timestamp_utc: datetime | None = None,
        status: str = "ACTIVE",
    ) -> DailySessionManifest:
        manifest = self.build_manifest(timestamp_utc, status)
        self.write_current_session(manifest)
        return manifest

    def load_current_session(self) -> DailySessionManifest | None:
        if not self.current_session_file.exists():
            return None
        try:
            payload = json.loads(
                self.current_session_file.read_text(encoding="utf-8")
            )
            return DailySessionManifest(**payload)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None


def get_current_session_manifest(
    symbol: str = DEFAULT_SYMBOL,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    timestamp_utc: Any = None,
) -> DailySessionManifest:
    """Return the manifest covering timestamp_utc, rebuilding stale state."""
    controller = DailySessionController(symbol=symbol, output_dir=output_dir)
    current_utc = _as_utc(timestamp_utc)
    expected = controller.build_manifest(current_utc)
    manifest = controller.load_current_session()
    if not _manifest_is_current(manifest, expected, current_utc):
        manifest = controller.initialize(current_utc)
    return manifest


def build_session_identity(
    episode_id: Any,
    case_id: Any = None,
    manifest: DailySessionManifest | None = None,
    timestamp_utc: Any = None,
) -> dict[str, str]:
    """Return additive session keys without replacing legacy identifiers."""
    active_manifest = manifest or get_current_session_manifest(
        timestamp_utc=timestamp_utc
    )
    try:
        episode_number = int(float(episode_id))
        session_episode_id = f"E{episode_number:06d}"
    except (TypeError, ValueError):
        normalized_episode_id = str(episode_id or "").strip()
        session_episode_id = (
            normalized_episode_id
            if normalized_episode_id.startswith("E")
            else f"E{normalized_episode_id}"
        )

    normalized_case_id = str(case_id or "").strip()
    return {
        "session_id": active_manifest.session_id,
        "market_date": active_manifest.market_date,
        "session_episode_id": session_episode_id,
        "global_episode_key": (
            f"{active_manifest.session_id}:{session_episode_id}"
        ),
        "global_case_id": (
            f"{active_manifest.session_id}:{normalized_case_id}"
            if normalized_case_id
            else ""
        ),
    }


def inherit_session_identity(source: Any) -> dict[str, str]:
    """Copy an existing identity without creating or rotating a session."""
    getter = (
        source.get
        if hasattr(source, "get")
        else lambda key, default="": default
    )
    return {
        field: str(getter(field, "") or "")
        for field in SESSION_IDENTITY_FIELDNAMES
    }


def _manifest_is_current(
    manifest: DailySessionManifest | None,
    expected: DailySessionManifest,
    current_utc: datetime,
) -> bool:
    if manifest is None:
        return False
    if (
        manifest.symbol != expected.symbol
        or manifest.session_id != expected.session_id
        or manifest.market_date != expected.market_date
        or manifest.timezone != expected.timezone
        or str(manifest.status).upper() != "ACTIVE"
    ):
        return False
    try:
        start = _as_utc(manifest.utc_start)
        end = _as_utc(manifest.utc_end)
    except (TypeError, ValueError, OverflowError):
        return False
    return start <= current_utc < end

def ensure_identity_csv_schema(
    path: str | Path,
    requested_fieldnames: list[str] | tuple[str, ...],
    *,
    encoding: str = "utf-8",
) -> list[str]:
    """Atomically preserve existing columns while adding identity fields."""
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    requested = list(dict.fromkeys(str(name) for name in requested_fieldnames))
    current: list[str] = []
    rows: list[dict[str, Any]] = []
    if csv_path.exists():
        with csv_path.open(mode="r", newline="", encoding=encoding) as handle:
            reader = csv.DictReader(handle)
            current = list(reader.fieldnames or [])
            rows = list(reader)
    merged = [*current, *(name for name in requested if name not in current)]
    if current == merged and csv_path.exists():
        return merged
    if not merged:
        merged = requested

    temporary = csv_path.with_name(
        f".{csv_path.name}.identity-schema.tmp"
    )
    try:
        with temporary.open(
            mode="w", newline="", encoding=encoding
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=merged)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in merged})
        temporary.replace(csv_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return merged

def main() -> None:
    controller = DailySessionController()
    manifest = controller.initialize()
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    print(f"CURRENT_SESSION_FILE = {controller.current_session_file}")
    print(f"CURRENT_SESSION_DIR = {controller.current_dir}")


if __name__ == "__main__":
    main()
