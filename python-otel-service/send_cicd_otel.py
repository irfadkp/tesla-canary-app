#!/usr/bin/env python3
"""
Tesla CI/CD — OTel Metrics + Traces sender
Implements OTel semantic conventions for CI/CD and VCS metrics:
  cicd.pipeline.run.duration   (Histogram, s)
  cicd.pipeline.run.active     (UpDownCounter, {run})
  cicd.pipeline.run.errors     (Counter, {error})
  cicd.worker.count            (UpDownCounter, {worker})
  vcs.change.count             (UpDownCounter, {change})
  vcs.ref.count                (UpDownCounter, {ref})
  vcs.ref.revisions_delta      (Gauge, {revision})
  vcs.ref.lines_delta          (Gauge, {line})

Plus a full pipeline trace:
  pipeline-run (root)
  ├── pipeline-init
  ├── build-backend
  ├── build-frontend
  └── otel-finalize

Usage: python3 send_cicd_otel.py [--fail]
  --fail  simulate a failed pipeline run
"""

import time, sys, random
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

# ── Config ─────────────────────────────────────────────────────────────────────
ENDPOINT    = "otlp-grpc-orange-saas.instana.io:443"
INSTANA_KEY = "uBp4GXpZQpKrHxMXNcvInQ"
SERVICE     = "tesla-backend"
VERSION     = "1.0.9"
PIPELINE    = "tesla-app-cicd"
REPO_URL    = "https://github.com/irfadkp/tesla-canary-app"
REPO_NAME   = "tesla-canary-app"
OWNER       = "irfadkp"
BRANCH      = "master"
RUN_ID      = f"{int(time.time())}-1"
SIMULATE_FAIL = "--fail" in sys.argv

HEADERS = (
    ("x-instana-key", INSTANA_KEY),
    ("x-instana-host", "tesla-cicd-vm"),
)

# ── Resource ───────────────────────────────────────────────────────────────────
resource = Resource.create({
    "service.name":            SERVICE,
    "service.version":         VERSION,
    "deployment.environment":  "dev",
    "service.namespace":       "tesla-shop",
    "cicd.pipeline.name":      PIPELINE,
    "entity.label.attribute":  "tesla-backend cicd",
})

# ── Tracer ─────────────────────────────────────────────────────────────────────
span_exporter = OTLPSpanExporter(endpoint=ENDPOINT, headers=HEADERS, insecure=False)
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("tesla-cicd-tracer", VERSION)

# ── Metrics ────────────────────────────────────────────────────────────────────
metric_exporter = OTLPMetricExporter(endpoint=ENDPOINT, headers=HEADERS, insecure=False)
reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000, export_timeout_millis=10000)
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("tesla-cicd-meter", VERSION)

# ── CI/CD Metric instruments (OTel semantic conventions) ──────────────────────
run_duration = meter.create_histogram(
    "cicd.pipeline.run.duration",
    unit="s",
    description="Duration of a pipeline run grouped by pipeline, state and result.",
)
run_active = meter.create_up_down_counter(
    "cicd.pipeline.run.active",
    unit="{run}",
    description="The number of pipeline runs currently active in the system by state.",
)
run_errors = meter.create_counter(
    "cicd.pipeline.run.errors",
    unit="{error}",
    description="The number of errors encountered in pipeline runs.",
)
worker_count = meter.create_up_down_counter(
    "cicd.worker.count",
    unit="{worker}",
    description="The number of workers on the CI/CD system by state.",
)

# ── VCS Metric instruments (OTel semantic conventions) ────────────────────────
vcs_change_count = meter.create_up_down_counter(
    "vcs.change.count",
    unit="{change}",
    description="The number of changes (pull requests) in a repository by state.",
)
vcs_ref_count = meter.create_up_down_counter(
    "vcs.ref.count",
    unit="{ref}",
    description="The number of refs (branches/tags) in a repository.",
)
vcs_revisions_delta = meter.create_gauge(
    "vcs.ref.revisions_delta",
    unit="{revision}",
    description="Commits a ref is ahead/behind the base branch.",
)
vcs_lines_delta = meter.create_gauge(
    "vcs.ref.lines_delta",
    unit="{line}",
    description="Lines added/removed in a ref relative to base.",
)

print("=" * 60)
print("  Tesla CI/CD — OTel Metrics + Traces")
print("=" * 60)
print(f"  pipeline : {PIPELINE}")
print(f"  run_id   : {RUN_ID}")
print(f"  result   : {'FAIL (simulated)' if SIMULATE_FAIL else 'SUCCESS'}")
print(f"  endpoint : {ENDPOINT}")
print()

# ── Record worker available ────────────────────────────────────────────────────
worker_count.add(1, {"cicd.worker.state": "busy"})
worker_count.add(-1, {"cicd.worker.state": "available"})

# ── Record pending → executing ────────────────────────────────────────────────
run_active.add(1, {
    "cicd.pipeline.name":      PIPELINE,
    "cicd.pipeline.run.state": "pending",
})

# ── VCS metrics ───────────────────────────────────────────────────────────────
vcs_change_count.add(3, {
    "vcs.change.state":        "open",
    "vcs.repository.url.full": REPO_URL,
    "vcs.owner.name":          OWNER,
    "vcs.repository.name":     REPO_NAME,
})
vcs_change_count.add(12, {
    "vcs.change.state":        "merged",
    "vcs.repository.url.full": REPO_URL,
    "vcs.owner.name":          OWNER,
    "vcs.repository.name":     REPO_NAME,
})
vcs_ref_count.add(4, {
    "vcs.ref.type":            "branch",
    "vcs.repository.url.full": REPO_URL,
    "vcs.owner.name":          OWNER,
    "vcs.repository.name":     REPO_NAME,
})
vcs_revisions_delta.set(3, {
    "vcs.ref.head.name":       BRANCH,
    "vcs.ref.head.type":       "branch",
    "vcs.ref.base.name":       "main",
    "vcs.ref.base.type":       "branch",
    "vcs.repository.url.full": REPO_URL,
    "vcs.revision_delta.direction": "ahead",
})
vcs_lines_delta.set(42, {
    "vcs.line_change.type":    "added",
    "vcs.ref.head.name":       BRANCH,
    "vcs.ref.head.type":       "branch",
    "vcs.ref.base.name":       "main",
    "vcs.ref.base.type":       "branch",
    "vcs.repository.url.full": REPO_URL,
})
vcs_lines_delta.set(7, {
    "vcs.line_change.type":    "removed",
    "vcs.ref.head.name":       BRANCH,
    "vcs.ref.head.type":       "branch",
    "vcs.ref.base.name":       "main",
    "vcs.ref.base.type":       "branch",
    "vcs.repository.url.full": REPO_URL,
})

# ── Pipeline trace ─────────────────────────────────────────────────────────────
pipeline_start = time.time()

def stage(name, duration, component=None, fail=False):
    attrs = {
        "cicd.pipeline.name":      PIPELINE,
        "cicd.pipeline.run.id":    RUN_ID,
        "cicd.pipeline.run.state": "executing",
        "vcs.ref.head.name":       BRANCH,
        "vcs.ref.head.type":       "branch",
        "vcs.repository.url.full": REPO_URL,
        "vcs.repository.name":     REPO_NAME,
        "vcs.owner.name":          OWNER,
    }
    if component:
        attrs["cicd.component"] = component

    with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
        span.set_attributes(attrs)
        print(f"  ▶ {name} ...", end="", flush=True)
        time.sleep(duration)
        if fail:
            span.set_status(Status(StatusCode.ERROR, "build failure"))
            span.set_attribute("error.type", "failure")
            print(f"\r  ✗ {name} ({duration:.1f}s)  ERROR")
        else:
            span.set_status(Status(StatusCode.OK))
            print(f"\r  ✓ {name} ({duration:.1f}s)")
    return not fail

print("Sending pipeline trace...\n")

with tracer.start_as_current_span("pipeline-run", kind=SpanKind.SERVER) as root:
    root.set_attributes({
        "cicd.pipeline.name":      PIPELINE,
        "cicd.pipeline.run.id":    RUN_ID,
        "cicd.pipeline.run.state": "executing",
        "cicd.pipeline.result":    "failure" if SIMULATE_FAIL else "success",
        "vcs.ref.head.name":       BRANCH,
        "vcs.ref.head.type":       "branch",
        "vcs.repository.url.full": REPO_URL,
        "vcs.repository.name":     REPO_NAME,
        "vcs.owner.name":          OWNER,
    })

    # transition: pending → executing
    run_active.add(-1, {"cicd.pipeline.name": PIPELINE, "cicd.pipeline.run.state": "pending"})
    run_active.add(1,  {"cicd.pipeline.name": PIPELINE, "cicd.pipeline.run.state": "executing"})

    stage("pipeline-init",   0.3)
    ok_be = stage("build-backend",   1.2, component="backend",  fail=SIMULATE_FAIL)
    ok_fe = stage("build-frontend",  1.0, component="frontend")
    stage("otel-finalize",   0.2)

    overall_result = "success" if (ok_be and ok_fe) else "failure"
    root.set_status(Status(StatusCode.ERROR if not ok_be else StatusCode.OK))

pipeline_duration = time.time() - pipeline_start

# ── Record finalizing metrics ──────────────────────────────────────────────────
run_active.add(-1, {"cicd.pipeline.name": PIPELINE, "cicd.pipeline.run.state": "executing"})
run_active.add(1,  {"cicd.pipeline.name": PIPELINE, "cicd.pipeline.run.state": "finalizing"})

run_duration.record(
    pipeline_duration,
    {
        "cicd.pipeline.name":      PIPELINE,
        "cicd.pipeline.run.state": "finalizing",
        "cicd.pipeline.result":    overall_result,
    },
)

if overall_result == "failure":
    run_errors.add(1, {
        "cicd.pipeline.name": PIPELINE,
        "error.type":         "failure",
    })

run_active.add(-1, {"cicd.pipeline.name": PIPELINE, "cicd.pipeline.run.state": "finalizing"})

# worker back to available
worker_count.add(-1, {"cicd.worker.state": "busy"})
worker_count.add(1,  {"cicd.worker.state": "available"})

print(f"\n  duration : {pipeline_duration:.1f}s  result: {overall_result}")
print("\nFlushing metrics + traces to Instana...", end="", flush=True)
meter_provider.force_flush(timeout_millis=15000)
tracer_provider.force_flush(timeout_millis=15000)
tracer_provider.shutdown()
meter_provider.shutdown()
print(" done.\n")

print("=" * 60)
print(f"  ✅  CI/CD OTel sent to Instana!")
print(f"  Traces  → Analytics → Calls → service.name = {SERVICE}")
print(f"  Metrics → cicd.pipeline.run.duration / .active / .errors")
print(f"            vcs.change.count / vcs.ref.count / vcs.ref.revisions_delta")
print("=" * 60)
