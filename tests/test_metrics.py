from datetime import timedelta

import pytest

from src.mcms.core.metrics import MetricsCollector


def test_record_latency() -> None:
    collector = MetricsCollector()
    collector.record_latency("agent-tm-001", "dispatch", 12.0)
    assert collector.samples[0].metric == "latency:dispatch"


def test_record_throughput() -> None:
    collector = MetricsCollector()
    collector.record_throughput("agent-tm-001", "alerts", 100, 10)
    assert collector.samples[0].value == 10.0


def test_record_error() -> None:
    collector = MetricsCollector()
    collector.record_error("agent-tm-001", "timeout")
    assert collector.samples[0].metric == "error:timeout"


def test_record_queue_depth() -> None:
    collector = MetricsCollector()
    collector.record_queue_depth("agent-tm-001", "alerts", 7)
    assert collector.samples[0].value == 7.0


def test_get_p50_percentile() -> None:
    collector = MetricsCollector()
    for value in [10, 20, 30]:
        collector.record_latency("agent-tm-001", "dispatch", value)
    assert (
        collector.get_percentile("agent-tm-001", "latency:dispatch", 50, timedelta(minutes=1))
        == 20.0
    )


def test_get_p95_percentile() -> None:
    collector = MetricsCollector()
    for value in [10, 20, 30, 40]:
        collector.record_latency("agent-tm-001", "dispatch", value)
    assert collector.get_percentile(
        "agent-tm-001", "latency:dispatch", 95, timedelta(minutes=1)
    ) == pytest.approx(38.5)


def test_get_p99_percentile() -> None:
    collector = MetricsCollector()
    for value in [10, 20, 30, 40]:
        collector.record_latency("agent-tm-001", "dispatch", value)
    assert collector.get_percentile(
        "agent-tm-001", "latency:dispatch", 99, timedelta(minutes=1)
    ) == pytest.approx(39.7)


def test_get_rate_over_window() -> None:
    collector = MetricsCollector()
    collector.record_error("agent-tm-001", "timeout")
    collector.record_error("agent-tm-001", "timeout")
    assert collector.get_rate(
        "agent-tm-001", "error:timeout", timedelta(seconds=10)
    ) == pytest.approx(0.2)


def test_get_trend_increasing() -> None:
    collector = MetricsCollector()
    for value in [1, 2, 3]:
        collector.record_queue_depth("agent-tm-001", "alerts", value)
    trend = collector.get_trend("agent-tm-001", "queue_depth:alerts", timedelta(minutes=1))
    assert trend["direction"] == "increasing"
    assert trend["ema"] > 1


def test_detect_anomaly_three_sigma_rule() -> None:
    collector = MetricsCollector()
    for _ in range(10):
        collector.record_latency("agent-tm-001", "dispatch", 10)
    assert (
        collector.detect_anomaly("agent-tm-001", "latency:dispatch", 100, timedelta(minutes=1))
        is True
    )
