"""
Example: Observability & Metrics

Demonstrates distributed tracing, metrics collection, and alerting.
"""

import time
from uniskill.observability import ObservabilityPipeline, SpanKind


def observability_example():
    """Full observability pipeline demonstration."""
    print("=" * 60)
    print("Observability Pipeline Example")
    print("=" * 60)

    pipeline = ObservabilityPipeline()

    # Simulate a multi-step skill execution
    trace_id = "demo-trace-001"
    pipeline.start_trace(trace_id, {"task": "generate_report", "user": "demo"})

    # Step 1: Security scan
    with pipeline.trace_span(trace_id, "span-scan", SpanKind.SECURITY_SCAN, "security_scan"):
        pipeline._metrics.record_latency("skill_latency_ms", 150)
        time.sleep(0.01)

    # Step 2: Context compression
    with pipeline.trace_span(trace_id, "span-compress", SpanKind.COMPRESSION, "context_compress"):
        pipeline._metrics.record_latency("skill_latency_ms", 200)
        time.sleep(0.01)

    # Step 3: LLM call
    with pipeline.trace_span(trace_id, "span-llm", SpanKind.LLM_CALL, "generate_report_llm"):
        pipeline._metrics.record_latency("skill_latency_ms", 2500)
        pipeline._metrics.increment("llm_calls")
        time.sleep(0.01)

    # Step 4: Tool call
    with pipeline.trace_span(trace_id, "span-tool", SpanKind.TOOL_CALL, "save_report"):
        pipeline._metrics.record_latency("skill_latency_ms", 300)
        time.sleep(0.01)

    # Get trace
    trace = pipeline.get_trace(trace_id)
    print(f"\nTrace: {trace_id}")
    print(f"Spans: {len(trace.spans)}")
    for span in trace.spans:
        print(f"  [{span.kind.value}] {span.name}: {span.duration_ms:.1f}ms ({span.status})")

    # Show metrics
    print(f"\nMetrics:")
    metrics = pipeline.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")

    # Check alerts
    alerts = pipeline.check_alerts()
    if alerts:
        print(f"\nAlerts triggered ({len(alerts)}):")
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['rule']}: {alert['metric']}={alert['value']} (threshold: {alert['threshold']})")
    else:
        print(f"\nNo alerts triggered.")

    # Export OpenTelemetry format
    exported = pipeline.export_traces()
    print(f"\nExported {len(exported)} trace(s) in OpenTelemetry format")


def metrics_example():
    """Standalone metrics collection."""
    print("\n" + "=" * 60)
    print("Metrics Collection Example")
    print("=" * 60)

    pipeline = ObservabilityPipeline()

    # Simulate load
    pipeline._metrics.increment("api_requests", 1000)
    pipeline._metrics.record_latency("api_latency_ms", 45)
    pipeline._metrics.record_latency("api_latency_ms", 55)
    pipeline._metrics.record_latency("api_latency_ms", 40)
    pipeline._metrics.record_latency("api_latency_ms", 120)

    pipeline._metrics.set_gauge("active_connections", 150)
    pipeline._metrics.set_gauge("memory_usage_percent", 65.5)

    # Simulate high latency that triggers alert
    pipeline._metrics.record_latency("skill_latency_ms", 8000)  # Above 5000 threshold

    alerts = pipeline.check_alerts()
    print(f"\nAlerts triggered: {len(alerts)}")
    for alert in alerts:
        print(f"  [{alert['severity'].upper()}] {alert['rule']}")


if __name__ == "__main__":
    observability_example()
    metrics_example()
