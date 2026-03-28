---
name: tracemind
description: Implements distributed tracing, structured logging, and observability using OpenTelemetry, Jaeger/Tempo, and SLO-based alerting. Use when asked to add tracing to a service, implement structured logging, set up correlation IDs, configure OpenTelemetry, analyze stack traces, or build SLO alerts.
---

# TraceMind

## Overview

Implements the three pillars of observability — traces, metrics, and logs — using OpenTelemetry as the vendor-neutral instrumentation layer. Backends: Jaeger or Grafana Tempo for traces, Prometheus + Grafana for metrics, and any JSON-structured log aggregator (Loki, Datadog, Elasticsearch). Produces correlation IDs that stitch traces, logs, and metrics together for root-cause analysis.

## Workflow

### 1. OpenTelemetry Setup

OpenTelemetry is the instrumentation standard. Instrument once, export to any backend.

**Python (FastAPI)**:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracing(service_name: str, otlp_endpoint: str):
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
```

**Node.js**: Load `tracing.ts` before all other imports. Use `NodeSDK` with `getNodeAutoInstrumentations()` and `OTLPTraceExporter`. Configure via `OTEL_EXPORTER_OTLP_ENDPOINT` env var.

### 2. Trace Context Propagation

Traces must flow across service boundaries using W3C Trace Context (`traceparent` header):

```
traceparent: 00-{trace-id-32hex}-{parent-span-id-16hex}-{flags}
tracestate: vendor-specific key-value pairs
```

Auto-instrumentation handles this for HTTP clients (httpx, axios, requests). For message queues, inject manually:

```python
# Inject trace context into Kafka message headers
from opentelemetry.propagate import inject

headers = {}
inject(headers)  # adds 'traceparent' and 'tracestate'
producer.send('orders', value=payload, headers=list(headers.items()))

# Extract in consumer
from opentelemetry.propagate import extract
from opentelemetry import trace

ctx = extract(dict(message.headers))
with trace.get_tracer(__name__).start_as_current_span(
    "process-order", context=ctx
) as span:
    ...
```

For async/background workers (Celery, BullMQ): serialize the trace context as a task header and restore it in the worker.

### 3. Structured Logging with Correlation IDs

All logs must be JSON-structured with trace context embedded. Use a structlog processor to inject `trace_id` and `span_id` from the active OTel span into every log entry. Required fields: `event`, `timestamp` (ISO 8601), `service`, `env`, `trace_id`, `span_id`.

**Never log**: passwords, API keys, PII (emails, SSNs) in plaintext. Redact with `***` or hash.

### 4. Custom Spans and Attributes

Name spans `<domain>.<operation>` (`payment.process`, `db.query`, `cache.get`). Set domain attributes on the span, call `span.record_exception(e)` and `span.set_status(StatusCode.ERROR)` in the except block. Follow OTel Semantic Conventions (`db.system`, `http.method`) for standard attributes; use `<service>.<attribute>` for domain-specific ones.

### 5. SLO Definition and Alerting

Define SLOs before configuring alerts. SLI = HTTP 2xx / total requests. SLO = 99.9% over 30-day window. Error budget = 43.8 min/month.

Key Prometheus alert expressions:
- Error rate: `sum(rate(http_requests_total{status!~"5.."}[5m])) / sum(rate(http_requests_total[5m])) < 0.999`
- Latency p99: `histogram_quantile(0.99, ...) > 1.0`

**Error budget burn rate** (Google SRE Workbook): fast burn (1h, 14x) = page; slow burn (6h, 6x) = ticket; very slow (3d, 3x) = sprint review.

### 6. Grafana Dashboard Structure

Use the RED method: Request rate, Error rate, Duration (p50/p95/p99). Include an error budget remaining panel (green > 50%, yellow 10–50%, red < 10%). Link panels directly to Tempo/Jaeger trace queries for the selected time range.

### 7. OTel Collector Configuration

Route telemetry through an OTel Collector (not directly to backends) for flexibility:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: "0.0.0.0:4317" }
      http: { endpoint: "0.0.0.0:4318" }

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  resource:
    attributes:
      - action: insert
        key: deployment.environment
        value: ${ENV}

exporters:
  otlp/tempo:
    endpoint: "tempo:4317"
    tls: { insecure: true }
  prometheus:
    endpoint: "0.0.0.0:8889"
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"

service:
  pipelines:
    traces: { receivers: [otlp], processors: [batch], exporters: [otlp/tempo] }
    metrics: { receivers: [otlp], processors: [batch], exporters: [prometheus] }
    logs: { receivers: [otlp], processors: [batch], exporters: [loki] }
```

## Edge Cases

**Sampling strategy:** At > 1000 req/s, use tail-based sampling: always record traces with errors or high latency, sample 1–5% of healthy fast traces. Configure via OTel Collector `tailsampling` processor. Never use head-based sampling alone.

**Trace context across async boundaries:** `asyncio.gather()`, `ThreadPoolExecutor`, and message queues do not auto-propagate context. Use `contextvars.copy_context()` when spawning threads. For message queues, inject/extract manually (see Section 2).

**Cardinality explosion:** High-cardinality labels (user IDs, full URL paths) cause Prometheus memory exhaustion. Use `http.route` (pattern) not `http.url` (full URL). Audit with `promtool tsdb analyze`.

**Clock skew diagnosis:** Spans with impossible durations (negative or longer than the parent) indicate NTP drift or container clock skew. Check `chronyc tracking` on host nodes and verify container time sync. In Kubernetes, pods inherit host clock — a skewed node affects all pods. Use Jaeger's clock skew adjustment or correct the node NTP source.

**OTel Collector HA:** Run the Collector as a DaemonSet or sidecar for local buffering. Configure the `batch` processor with `sending_queue` and `retry_on_failure` to buffer spans during backend outages. Add a fallback exporter (e.g., write to file) so telemetry is not lost if the primary backend is down.

**PII in span attributes:** Avoid setting user emails, names, or payment data as span attributes — they appear in trace UIs and logs. If unavoidable, use the OTel Collector `transform` processor to redact or hash sensitive attributes before export: `set(attributes["user.email"], "REDACTED") where attributes["user.email"] != nil`.
