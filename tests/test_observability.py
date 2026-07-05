"""Tests for observability module."""

import time
import pytest
from uniskill.observability import (
    ObservabilityPipeline,
    MetricsCollector,
    SpanKind,
    AlertRule,
)


class TestMetricsCollector:
    """Test metrics collection."""

    def test_counter(self):
        mc = MetricsCollector()
        mc.increment("requests", 5)
        mc.increment("requests")

        stats = mc.get_stats()
        assert stats["counters"]["requests"] == 6

    def test_latency_recording(self):
        mc = MetricsCollector()
        mc.record_latency("api_call", 100)
        mc.record_latency("api_call", 200)
        mc.record_latency("api_call", 300)

        stats = mc.get_stats()
        assert stats["api_call_avg"] == 200
        assert stats["api_call_min"] == 100
        assert stats["api_call_max"] == 300

    def test_gauge(self):
        mc = MetricsCollector()
        mc.set_gauge("memory_usage", 0.75)
        mc.set_gauge("memory_usage", 0.80)  # Update

        stats = mc.get_stats()
        assert stats["gauges"]["memory_usage"] == 0.80

    def test_event_recording(self):
        mc = MetricsCollector()
        mc.record_event("deployment", {"version": "1.0.0"})

        assert len(mc._events) == 1
        assert mc._events[0]["name"] == "deployment"


class TestObservabilityPipeline:
    """Test observability pipeline."""

    def test_full_trace_lifecycle(self):
        pipeline = ObservabilityPipeline()
        trace_id = "trace-001"

        pipeline.start_trace(trace_id, {"user": "test"})
        span = pipeline.start_span(trace_id, "span-001", SpanKind.SKILL_EXECUTION, "test_skill")

        time.sleep(0.01)
        pipeline.end_span("span-001", "ok")

        trace = pipeline.get_trace(trace_id)
        assert trace is not None
        assert len(trace.spans) == 1
        assert trace.spans[0].duration_ms > 0

    def test_nested_spans(self):
        pipeline = ObservabilityPipeline()
        trace_id = "trace-002"

        pipeline.start_trace(trace_id)
        parent = pipeline.start_span(trace_id, "parent", SpanKind.SKILL_EXECUTION, "parent_skill")
        child = pipeline.start_span(trace_id, "child", SpanKind.TOOL_CALL, "child_tool", parent_id="parent")

        pipeline.end_span("child", "ok")
        pipeline.end_span("parent", "ok")

        trace = pipeline.get_trace(trace_id)
        assert len(trace.spans) == 2

    def test_alert_evaluation(self):
        pipeline = ObservabilityPipeline()
        pipeline._metrics.record_latency("skill_latency_ms", 10000)  # Above 5000 threshold

        alerts = pipeline.check_alerts()
        assert len(alerts) > 0

    def test_no_alerts_when_normal(self):
        pipeline = ObservabilityPipeline()
        pipeline._metrics.record_latency("skill_latency_ms", 100)  # Below threshold

        alerts = pipeline.check_alerts()
        assert len(alerts) == 0

    def test_export_traces(self):
        pipeline = ObservabilityPipeline()
        trace_id = "trace-003"
        pipeline.start_trace(trace_id)
        pipeline.start_span(trace_id, "span-001", SpanKind.SKILL_EXECUTION, "test")
        pipeline.end_span("span-001")

        exported = pipeline.export_traces()
        assert len(exported) == 1
        assert exported[0]["traceId"] == "trace-003"
