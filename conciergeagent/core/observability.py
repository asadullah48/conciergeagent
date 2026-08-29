"""Structured logging and in-process metrics.

Exposes Prometheus text-format metrics without pulling in a client library:
the platform tracks a handful of counters and one latency histogram, which is
well under the threshold where a dependency earns its place.
"""
from __future__ import annotations

import json
import logging
import sys
import threading
import time
from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

LATENCY_BUCKETS_MS: tuple[float, ...] = (1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 1000.0)

_RESERVED_LOG_FIELDS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "asctime",
    "message",
}


class JsonLogFormatter(logging.Formatter):
    """Render records as single-line JSON so log shippers can parse them."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_FIELDS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Install a single stdout handler on the root logger (idempotent)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonLogFormatter()
        if json_logs
        else logging.Formatter("%(asctime)s %(levelname)-8s %(name)s :: %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


class MetricsRegistry:
    """Thread-safe counters and a fixed-bucket latency histogram."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)
        self._hist_buckets: dict[float, int] = dict.fromkeys(LATENCY_BUCKETS_MS, 0)
        self._hist_count = 0
        self._hist_sum = 0.0

    def increment(
        self, name: str, labels: Mapping[str, str] | None = None, amount: int = 1
    ) -> None:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._counters[key] += amount

    def observe_latency_ms(self, value_ms: float) -> None:
        with self._lock:
            self._hist_count += 1
            self._hist_sum += value_ms
            for bucket in LATENCY_BUCKETS_MS:
                if value_ms <= bucket:
                    self._hist_buckets[bucket] += 1

    def reset(self) -> None:
        """Clear all series. Intended for test isolation."""
        with self._lock:
            self._counters.clear()
            self._hist_buckets = dict.fromkeys(LATENCY_BUCKETS_MS, 0)
            self._hist_count = 0
            self._hist_sum = 0.0

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": {
                    (name if not labels else f"{name}{dict(labels)}"): value
                    for (name, labels), value in self._counters.items()
                },
                "latency_count": self._hist_count,
                "latency_sum_ms": round(self._hist_sum, 2),
            }

    def render_prometheus(self) -> str:
        """Serialise the registry in Prometheus text exposition format."""
        with self._lock:
            counters = dict(self._counters)
            buckets = dict(self._hist_buckets)
            count, total = self._hist_count, self._hist_sum

        lines: list[str] = []
        by_name: dict[str, list] = defaultdict(list)
        for (name, labels), value in counters.items():
            by_name[name].append((labels, value))

        for name in sorted(by_name):
            lines.append(f"# HELP {name} ConciergeAgent counter.")
            lines.append(f"# TYPE {name} counter")
            for labels, value in sorted(by_name[name]):
                rendered = (
                    "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}" if labels else ""
                )
                lines.append(f"{name}{rendered} {value}")

        lines.append("# HELP concierge_interaction_latency_ms Interaction latency in milliseconds.")
        lines.append("# TYPE concierge_interaction_latency_ms histogram")
        cumulative = 0
        for bucket in LATENCY_BUCKETS_MS:
            cumulative = buckets[bucket]
            lines.append(f'concierge_interaction_latency_ms_bucket{{le="{bucket}"}} {cumulative}')
        lines.append(f'concierge_interaction_latency_ms_bucket{{le="+Inf"}} {count}')
        lines.append(f"concierge_interaction_latency_ms_sum {round(total, 2)}")
        lines.append(f"concierge_interaction_latency_ms_count {count}")
        return "\n".join(lines) + "\n"


METRICS = MetricsRegistry()


@contextmanager
def track_latency() -> Iterator[None]:
    """Record wall-clock duration of the wrapped block into the histogram."""
    started = time.perf_counter()
    try:
        yield
    finally:
        METRICS.observe_latency_ms((time.perf_counter() - started) * 1000.0)
