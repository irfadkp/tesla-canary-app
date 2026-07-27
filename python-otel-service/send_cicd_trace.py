#!/usr/bin/env python3
"""
Tesla CI/CD Pipeline — OTel Traces
Sends a full pipeline trace to Instana via OTLP/gRPC.
Same pattern as OtelDemoSamples Python app — appears under tesla-backend in Services.

Pipeline shape:
  pipeline-run (root)
  ├── pipeline-init
  ├── build-backend   (parallel)
  ├── build-frontend  (parallel)
  └── otel-finalize
"""

import time, random
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

# ── Config ─────────────────────────────────────────────────────────────────────
ENDPOINT    = "otlp-grpc-orange-saas.instana.io:443"
INSTANA_KEY = "uBp4GXpZQpKrHxMXNcvInQ"
SERVICE     = "tesla-backend"
VERSION     = "1.0.9"
RUN_ID      = f"cicd-{int(time.time())}"

# ── Resource — same service.name as the Python metrics app ────────────────────
resource = Resource.create({
    "service.name":            SERVICE,
    "service.version":         VERSION,
    "deployment.environment":  "dev",
    "service.namespace":       "tesla-shop",
    "cicd.tool":               "github-actions",
    "cicd.pipeline.name":      "tesla-app-cicd",
    "entity.label.attribute":  "tesla-backend cicd pipeline",
})

# ── Tracer ─────────────────────────────────────────────────────────────────────
exporter = OTLPSpanExporter(
    endpoint=ENDPOINT,
    headers=(
        ("x-instana-key", INSTANA_KEY),
        ("x-instana-host", "tesla-cicd-vm"),
    ),
    insecure=False,
)
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("tesla-cicd-tracer", VERSION)

print("=" * 60)
print("  Tesla CI/CD Pipeline — OTel Trace Sender")
print("=" * 60)
print(f"  service.name : {SERVICE}")
print(f"  run_id       : {RUN_ID}")
print(f"  endpoint     : {ENDPOINT}")
print()

def run_stage(name, duration_s, parent_ctx=None, status_code=StatusCode.OK, attrs={}):
    """Run a single pipeline stage as a span."""
    ctx = trace.set_span_in_context(trace.get_current_span()) if parent_ctx is None else parent_ctx
    with tracer.start_as_current_span(
        name,
        context=ctx,
        kind=SpanKind.INTERNAL,
    ) as span:
        span.set_attributes({
            "cicd.stage.name":       name,
            "cicd.pipeline.run.id":  RUN_ID,
            "cicd.image.tag":        VERSION,
            "cicd.repo.ref":         "master",
            "cicd.repo.url":         "https://github.com/irfadkp/tesla-canary-app",
            **attrs,
        })
        print(f"  ▶  {name} ...", end="", flush=True)
        time.sleep(duration_s)
        span.set_status(Status(status_code))
        result = "✓" if status_code == StatusCode.OK else "✗"
        print(f"\r  {result}  {name} ({duration_s:.1f}s)")
    return span

# ── Send pipeline trace ────────────────────────────────────────────────────────
print("Sending pipeline trace to Instana...\n")

with tracer.start_as_current_span("pipeline-run", kind=SpanKind.SERVER) as root:
    root.set_attributes({
        "cicd.pipeline.name":    "tesla-app-cicd",
        "cicd.pipeline.run.id":  RUN_ID,
        "cicd.image.tag":        VERSION,
        "cicd.repo.ref":         "master",
        "cicd.repo.url":         "https://github.com/irfadkp/tesla-canary-app",
        "http.method":           "POST",
        "http.route":            "/cicd/pipeline/run",
        "http.status_code":      200,
    })

    run_stage("pipeline-init",    0.5, attrs={"cicd.stage.name": "pipeline-init"})
    run_stage("build-backend",    1.5, attrs={"cicd.stage.name": "build-backend",  "cicd.component": "backend"})
    run_stage("build-frontend",   1.2, attrs={"cicd.stage.name": "build-frontend", "cicd.component": "frontend"})
    run_stage("otel-finalize",    0.3, attrs={"cicd.stage.name": "otel-finalize"})

    root.set_status(Status(StatusCode.OK))

print()
print("Flushing to Instana...", end="", flush=True)
provider.force_flush(timeout_millis=15000)
provider.shutdown()
print(" done.\n")

print("=" * 60)
print(f"  ✅  Pipeline trace sent!")
print(f"  In Instana → Analytics → Calls")
print(f"    filter: service.name = {SERVICE}")
print(f"    look for span: pipeline-run / build-backend / build-frontend")
print("=" * 60)
