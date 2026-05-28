"""Small research-only performance profiler.

This module records timing and memory diagnostics for replay/research scripts.
It does not change calculations, scoring, replay behavior, or RDM logic.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import tracemalloc
from typing import Any, Dict, Iterable, List


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "outputs"
PROFILE_JSON_FILE = OUTPUT_DIR / "performance_profile.json"
PROFILE_REPORT_FILE = OUTPUT_DIR / "performance_profile_report.md"


class PerfProfiler:
    def __init__(self, script_name: str) -> None:
        self.script_name = script_name
        self.started_at = time.perf_counter()
        self.run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.steps: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    @contextmanager
    def step(self, name: str, **metadata: Any):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record(name, time.perf_counter() - start, **metadata)

    def record(self, name: str, duration_seconds: float, **metadata: Any) -> None:
        step = {
            "name": name,
            "duration_seconds": round(float(duration_seconds), 6),
        }
        if metadata:
            step["metadata"] = sanitize_json(metadata)
        self.steps.append(step)
        print(f"[PERF] {name}: {duration_seconds:.3f}s")

    def add_metric(self, name: str, value: Any) -> None:
        self.metrics[name] = sanitize_json(value)

    def finish(self, csv_files: Iterable[Path] | None = None) -> Dict[str, Any]:
        total_runtime = time.perf_counter() - self.started_at
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        csv_stats = file_size_stats(csv_files or [])
        step_totals = aggregate_steps(self.steps)
        slowest_step = max(step_totals.items(), key=lambda item: item[1], default=("", 0.0))
        bottleneck = classify_bottleneck(step_totals, peak_memory)

        run = {
            "script": self.script_name,
            "run_utc": self.run_utc,
            "total_runtime_seconds": round(total_runtime, 6),
            "slowest_step": {
                "name": slowest_step[0],
                "duration_seconds": round(slowest_step[1], 6),
            },
            "bottleneck_likely": bottleneck,
            "steps": self.steps,
            "step_totals": {
                name: round(duration, 6)
                for name, duration in sorted(
                    step_totals.items(), key=lambda item: item[1], reverse=True
                )
            },
            "metrics": self.metrics,
            "csv_file_sizes": csv_stats,
            "memory": {
                "current_python_heap_mb": round(current_memory / 1024 / 1024, 3),
                "peak_python_heap_mb": round(peak_memory / 1024 / 1024, 3),
            },
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        profile = load_profile()
        profile["updated_utc"] = self.run_utc
        profile.setdefault("runs", {})[self.script_name] = run
        PROFILE_JSON_FILE.write_text(
            json.dumps(profile, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        PROFILE_REPORT_FILE.write_text(build_markdown_report(profile), encoding="utf-8")
        print(f"[PERF] report_json: {relative_path(PROFILE_JSON_FILE)}")
        print(f"[PERF] report_md: {relative_path(PROFILE_REPORT_FILE)}")
        return run


def load_profile() -> Dict[str, Any]:
    if not PROFILE_JSON_FILE.exists():
        return {"runs": {}}
    try:
        return json.loads(PROFILE_JSON_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"runs": {}}


def aggregate_steps(steps: List[Dict[str, Any]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for step in steps:
        name = str(step.get("name") or "unknown")
        totals[name] = totals.get(name, 0.0) + float(step.get("duration_seconds") or 0.0)
    return totals


def classify_bottleneck(step_totals: Dict[str, float], peak_memory: int) -> str:
    groups = {
        "DOWNLOAD": ["download", "http_wait"],
        "CPU_PROCESSING": ["row_build", "observation", "analysis", "episode_analysis"],
        "PANDAS": ["dataframe", "pandas", "merge"],
        "CSV_WRITE": ["write", "csv"],
        "RDM_CALCULATOR": ["rdm", "mechanics", "density", "live_evolution", "interaction_core"],
    }
    scores: Dict[str, float] = {key: 0.0 for key in groups}
    for name, duration in step_totals.items():
        lowered = name.lower()
        for group, patterns in groups.items():
            if any(pattern in lowered for pattern in patterns):
                scores[group] += duration
    if peak_memory / 1024 / 1024 > 1500:
        scores["RAM_LIMIT"] = max(scores.values(), default=0.0) + 1.0
    if not scores:
        return "UNKNOWN"
    winner = max(scores.items(), key=lambda item: item[1])
    return winner[0] if winner[1] > 0 else "UNKNOWN"


def file_size_stats(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    stats = []
    for path in paths:
        resolved = Path(path)
        if not resolved.exists():
            continue
        size_bytes = resolved.stat().st_size
        stats.append(
            {
                "path": relative_path(resolved),
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / 1024 / 1024, 3),
            }
        )
    return stats


def build_markdown_report(profile: Dict[str, Any]) -> str:
    lines = [
        "# Performance Profile Report",
        "",
        f"Updated UTC: {profile.get('updated_utc', '')}",
        "",
    ]
    runs = profile.get("runs", {})
    for script_name, run in runs.items():
        lines.extend(
            [
                f"## {script_name}",
                "",
                f"- Total runtime: {run.get('total_runtime_seconds', 0)}s",
                "- Slowest function / step: "
                f"{run.get('slowest_step', {}).get('name', '')} "
                f"({run.get('slowest_step', {}).get('duration_seconds', 0)}s)",
                f"- Bottleneck likely: {run.get('bottleneck_likely', 'UNKNOWN')}",
                "- Peak Python heap: "
                f"{run.get('memory', {}).get('peak_python_heap_mb', 0)} MB",
                "",
                "### Top Bottlenecks",
                "",
            ]
        )
        for name, duration in list((run.get("step_totals") or {}).items())[:10]:
            lines.append(f"- {name}: {duration}s")
        lines.extend(["", "### Metrics", ""])
        for name, value in (run.get("metrics") or {}).items():
            lines.append(f"- {name}: {value}")
        lines.extend(["", "### CSV File Sizes", ""])
        for item in run.get("csv_file_sizes") or []:
            lines.append(f"- {item['path']}: {item['size_mb']} MB")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_json(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def relative_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT_DIR))
    except ValueError:
        return str(path)
