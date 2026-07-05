"""
Observability Pipeline - Distributed tracing, metrics, and alerting.

Enterprise-grade monitoring for AI Agent skill execution:
- Distributed tracing across skill pipelines
- Real-time performance metrics
- Drift detection and anomaly alerts
- Golden dataset quality monitoring
- OpenTelemetry compatible
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class SpanKind(Enum):
    """Span kind for distributed tracing."""
    SKILL_EXECUTION = "skill_execution"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    COMPRESSION = "compression"
    SECURITY_SCAN = "security_scan"
    DEPLOYMENT = "deployment"
    API_REQUEST = "api_request"


@dataclass
class Span:
    """A single span in a distributed trace."""

    span_id: str
    trace_id: str
    parent_id: Optional[str]
    kind: SpanKind
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_event(self, name: str, attributes: dict[str, Any] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0


@dataclass
class Trace:
    """A complete distributed trace."""

    trace_id: str
    spans: list[Span] = field(default_factory=list)
    root_span: Optional[Span] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span) -> None:
        self.spans.append(span)

    def get_duration_ms(self) -> float:
        if self.root_span and self.root_span.end_time:
            return self.root_span.duration_ms
        return sum(s.duration_ms for s in self.spans)


class MetricsCollector:
    """Real-time metrics collection for skill execution."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._histograms: dict[str, list[float]] = {}
        self._gauges: dict[str, float] = {}
        self._events: list[dict[str, Any]] = []

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def record_latency(self, name: str, duration_ms: float) -> None:
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(duration_ms)

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def record_event(self, name: str, attributes: dict[str, Any] = None) -> None:
        self._events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })

    def get_stats(self) -> dict[str, Any]:
        stats = {"counters": dict(self._counters), "gauges": dict(self._gauges)}

        for name, values in self._histograms.items():
            if values:
                sorted_vals = sorted(values)
                stats[f"{name}_avg"] = sum(values) / len(values)
                stats[f"{name}_p50"] = sorted_vals[len(sorted_vals) // 2]
                stats[f"{name}_p95"] = sorted_vals[int(len(sorted_vals) * 0.95)]
                stats[f"{name}_p99"] = sorted_vals[int(len(sorted_vals) * 0.99)]
                stats[f"{name}_min"] = min(values)
                stats[f"{name}_max"] = max(values)

        return stats

    def reset(self) -> None:
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()
        self._events.clear()


class AlertRule:
    """An alerting rule for observability."""

    def __init__(self, name: str, metric: str, condition: str, threshold: float, severity: str = "warning"):
        self.name = name
        self.metric = metric
        self.condition = condition
        self.threshold = threshold
        self.severity = severity

    def evaluate(self, value: float) -> bool:
        if self.condition == "gt":
            return value > self.threshold
        elif self.condition == "lt":
            return value < self.threshold
        elif self.condition == "gte":
            return value >= self.threshold
        elif self.condition == "lte":
            return value <= self.threshold
        return False


class ObservabilityPipeline:
    """End-to-end observability pipeline for UniSkill.

    Integrates:
    - Distributed tracing with span hierarchy
    - Real-time metrics collection
    - Alerting with configurable rules
    - Quality regression detection
    - OpenTelemetry export compatibility
    """

    def __init__(self, sample_rate: float = 1.0):
        self._traces: dict[str, Trace] = {}
        self._metrics = MetricsCollector()
        self._alert_rules: list[AlertRule] = []
        self._sample_rate = sample_rate
        self._active_spans: dict[str, Span] = {}

        # Built-in alert rules
        self.add_alert_rule(AlertRule("high_latency", "skill_latency_ms", "gt", 5000, "warning"))
        self.add_alert_rule(AlertRule("critical_latency", "skill_latency_ms", "gt", 30000, "critical"))
        self.add_alert_rule(AlertRule("high_error_rate", "error_rate", "gt", 0.05, "critical"))
        self.add_alert_rule(AlertRule("token_budget_exceeded", "token_usage_ratio", "gt", 0.9, "warning"))

    def add_alert_rule(self, rule: AlertRule) -> None:
        self._alert_rules.append(rule)

    def start_trace(self, trace_id: str, metadata: dict = None) -> Trace:
        trace = Trace(trace_id=trace_id, metadata=metadata or {})
        self._traces[trace_id] = trace
        return trace

    def start_span(
        self, trace_id: str, span_id: str, kind: SpanKind, name: str, parent_id: Optional[str] = None
    ) -> Span:
        span = Span(span_id=span_id, trace_id=trace_id, parent_id=parent_id, kind=kind, name=name)
        self._active_spans[span_id] = span

        trace = self._traces.get(trace_id)
        if trace:
            trace.add_span(span)
            if parent_id is None:
                trace.root_span = span

        return span

    def end_span(self, span_id: str, status: str = "ok") -> Optional[Span]:
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(status)
            self._metrics.record_latency(f"{span.kind.value}_latency_ms", span.duration_ms)
            self._metrics.increment(f"{span.kind.value}_count")
            if status != "ok":
                self._metrics.increment(f"{span.kind.value}_errors")
        return span

    @contextmanager
    def trace_span(self, trace_id: str, span_id: str, kind: SpanKind, name: str):
        """Context manager for automatic span lifecycle."""
        span = self.start_span(trace_id, span_id, kind, name)
        try:
            yield span
            self.end_span(span_id, "ok")
        except Exception as e:
            self.end_span(span_id, "error")
            span.add_event("exception", {"error": str(e)})
            raise

    def check_alerts(self) -> list[dict[str, Any]]:
        """Evaluate all alert rules against current metrics."""
        stats = self._metrics.get_stats()
        triggered = []

        for rule in self._alert_rules:
            value = stats.get(rule.metric)
            if value is not None and rule.evaluate(value):
                triggered.append({
                    "rule": rule.name,
                    "severity": rule.severity,
                    "metric": rule.metric,
                    "value": value,
                    "threshold": rule.threshold,
                    "condition": rule.condition,
                })
                logger.warning("alert_triggered", rule=rule.name, value=value)

        return triggered

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        return self._traces.get(trace_id)

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics.get_stats()

    def export_traces(self) -> list[dict[str, Any]]:
        """Export traces in OpenTelemetry-compatible format."""
        return [
            {
                "traceId": t.trace_id,
                "spans": [
                    {
                        "spanId": s.span_id,
                        "parentSpanId": s.parent_id,
                        "name": s.name,
                        "kind": s.kind.value,
                        "startTime": s.start_time,
                        "endTime": s.end_time,
                        "status": s.status,
                        "attributes": s.attributes,
                    }
                    for s in t.spans
                ],
            }
            for t in self._traces.values()
        ]

    def quality_regression_check(self, historical_stats: dict[str, Any], current_stats: dict[str, Any], threshold: float = 0.1) -> list[str]:
        """Detect quality regression by comparing with historical metrics."""
        regressions = []
        for key in ["avg_latency_ms", "error_rate", "pass_rate"]:
            hist_val = historical_stats.get(key)
            curr_val = current_stats.get(key)
            if hist_val and curr_val:
                change = (curr_val - hist_val) / max(hist_val, 0.001)
                if abs(change) > threshold:
                    direction = "increase" if change > 0 else "decrease"
                    regressions.append(f"{key}: {change*100:.1f}% {direction}")
        return regressions
