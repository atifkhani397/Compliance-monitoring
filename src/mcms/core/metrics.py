"""In-memory metrics collection for MACMS observability."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from math import sqrt
from typing import Any

from src.mcms.core.exceptions import MetricsError


@dataclass(frozen=True)
class MetricSample:
    """One timestamped metric observation."""

    agent_id: str
    metric: str
    value: float
    timestamp: datetime
    context: Mapping[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collect and query bounded in-memory operational metrics."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self._samples: list[MetricSample] = []
        self.retention = timedelta(
            seconds=max(1, int(self.config.get("retention_seconds", 365 * 86400)))
        )

    @property
    def samples(self) -> list[MetricSample]:
        return list(self._samples)

    def _record(
        self, agent_id: str, metric: str, value: float, context: Mapping[str, Any] | None = None
    ) -> None:
        if not agent_id or not metric:
            raise MetricsError("agent_id and metric are required")
        if not isinstance(value, (int, float)) or not value >= 0:
            raise MetricsError("metric value must be a non-negative number")
        now = datetime.now(UTC)
        self._samples.append(MetricSample(agent_id, metric, float(value), now, dict(context or {})))
        cutoff = now - self.retention
        self._samples = [sample for sample in self._samples if sample.timestamp >= cutoff]

    def record_latency(self, agent_id: str, operation: str, latency_ms: float) -> None:
        self._record(agent_id, f"latency:{operation}", latency_ms)

    def record_throughput(
        self, agent_id: str, operation: str, count: int, window_seconds: int
    ) -> None:
        if count < 0 or window_seconds <= 0:
            raise MetricsError("count must be non-negative and window_seconds must be positive")
        self._record(
            agent_id,
            f"throughput:{operation}",
            count / window_seconds,
            {"count": count, "window_seconds": window_seconds},
        )

    def record_error(self, agent_id: str, error_type: str) -> None:
        self._record(agent_id, f"error:{error_type}", 1.0)

    def record_queue_depth(self, agent_id: str, queue_name: str, depth: int) -> None:
        if depth < 0:
            raise MetricsError("queue depth cannot be negative")
        self._record(agent_id, f"queue_depth:{queue_name}", float(depth))

    def _matching(self, agent_id: str, metric: str, window: timedelta) -> list[MetricSample]:
        if window.total_seconds() <= 0:
            raise MetricsError("metric window must be positive")
        cutoff = datetime.now(UTC) - window
        return [
            sample
            for sample in self._samples
            if sample.agent_id == agent_id
            and (sample.metric == metric or sample.metric.startswith(f"{metric}:"))
            and sample.timestamp >= cutoff
        ]

    def get_percentile(
        self, agent_id: str, metric: str, percentile: float, window: timedelta
    ) -> float:
        if not 0 <= percentile <= 100:
            raise MetricsError("percentile must be between 0 and 100")
        values = sorted(sample.value for sample in self._matching(agent_id, metric, window))
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]
        position = (len(values) - 1) * percentile / 100
        lower = int(position)
        upper = min(lower + 1, len(values) - 1)
        fraction = position - lower
        return values[lower] + (values[upper] - values[lower]) * fraction

    def get_rate(self, agent_id: str, metric: str, window: timedelta) -> float:
        """Return observations per second for counter-like metrics."""
        samples = self._matching(agent_id, metric, window)
        seconds = window.total_seconds()
        return sum(sample.value for sample in samples) / seconds

    def get_trend(self, agent_id: str, metric: str, window: timedelta) -> dict[str, Any]:
        samples = sorted(
            self._matching(agent_id, metric, window), key=lambda sample: sample.timestamp
        )
        if not samples:
            return {"slope": 0.0, "direction": "stable", "anomaly": False, "ema": 0.0}
        alpha = float(self.config.get("ema_alpha", 0.3))
        if not 0 < alpha <= 1:
            alpha = 0.3
        ema = samples[0].value
        for sample in samples[1:]:
            ema = alpha * sample.value + (1 - alpha) * ema
        elapsed = max((samples[-1].timestamp - samples[0].timestamp).total_seconds(), 1e-9)
        slope = (samples[-1].value - samples[0].value) / elapsed
        tolerance = float(self.config.get("trend_stability_tolerance", 1e-9))
        direction = (
            "increasing" if slope > tolerance else "decreasing" if slope < -tolerance else "stable"
        )
        return {
            "slope": slope,
            "direction": direction,
            "anomaly": self.detect_anomaly(agent_id, metric, samples[-1].value, window),
            "ema": ema,
        }

    def detect_anomaly(
        self, agent_id: str, metric: str, current_value: float, window: timedelta
    ) -> bool:
        """Apply a three-sigma statistical process-control rule."""
        values = [sample.value for sample in self._matching(agent_id, metric, window)]
        if len(values) < 2:
            return False
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        deviation = sqrt(variance)
        if deviation == 0:
            return current_value != mean
        return abs(current_value - mean) > 3 * deviation
