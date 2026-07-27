#!/usr/bin/env bash
# otel_send_span.sh — send a single OTLP/HTTP span to Instana
#
# Usage:
#   otel_send_span.sh <trace_id> <span_id> <parent_span_id> <span_name> \
#                     <start_ns> <end_ns> <status_code> <status_msg> \
#                     <service_name> <pipeline_run_id> <image_tag> \
#                     <commit_sha> <ref_name> <repo_url>
#
# Arguments:
#   trace_id        32-char hex trace ID
#   span_id         16-char hex span ID
#   parent_span_id  16-char hex parent span ID (empty string = root span)
#   span_name       human-readable stage name (e.g. "build-backend")
#   start_ns        start time in Unix nanoseconds
#   end_ns          end time in Unix nanoseconds
#   status_code     1 = OK, 2 = ERROR
#   status_msg      "success" or "failure"
#   service_name    Instana APM service name (e.g. "tesla-backend")
#   pipeline_run_id GitHub run ID + attempt (e.g. "12345678-1")
#   image_tag       container image tag (e.g. "1.0.9")
#   commit_sha      full git commit SHA
#   ref_name        branch or tag name
#   repo_url        repository URL
#
# Required env vars:
#   INSTANA_AGENT_KEY       Instana backend agent key
#   INSTANA_OTLP_ENDPOINT   (optional, defaults to https://release-instana.instana.rocks)
#   INSTANA_PLUGIN_NAME     (optional, defaults to otel-sensorsdk-cicd)
#   DEPLOYMENT_ENVIRONMENT  (optional, defaults to dev)

set -euo pipefail

TRACE_ID="${1}"
SPAN_ID="${2}"
PARENT_SPAN_ID="${3}"
SPAN_NAME="${4}"
START_NS="${5}"
END_NS="${6}"
STATUS_CODE="${7}"    # 1=OK 2=ERROR
STATUS_MSG="${8}"
SERVICE_NAME="${9}"
PIPELINE_RUN_ID="${10:-}"
IMAGE_TAG="${11:-}"
COMMIT_SHA="${12:-}"
REF_NAME="${13:-}"
REPO_URL="${14:-}"

ENDPOINT="${INSTANA_OTLP_ENDPOINT:-https://otlp-orange-saas.instana.io}"
PLUGIN_NAME="${INSTANA_PLUGIN_NAME:-otel-sensorsdk-cicd}"
ENVIRONMENT="${DEPLOYMENT_ENVIRONMENT:-dev}"

# Build the parentSpanId field only when a parent exists
if [[ -n "$PARENT_SPAN_ID" ]]; then
  PARENT_FIELD="\"parentSpanId\": \"${PARENT_SPAN_ID}\","
else
  PARENT_FIELD=""
fi

# Safely build optional string attributes
attr_str() { echo "{ \"key\": \"$1\", \"value\": { \"stringValue\": \"$2\" } }"; }

ATTRIBUTES=$(cat <<EOF
$(attr_str "cicd.pipeline.name"        "tesla-app-cicd"),
$(attr_str "cicd.pipeline.run.id"      "$PIPELINE_RUN_ID"),
$(attr_str "cicd.pipeline.run.state"   "executing"),
$(attr_str "cicd.pipeline.result"      "$STATUS_MSG"),
$(attr_str "vcs.ref.head.name"         "$REF_NAME"),
$(attr_str "vcs.ref.head.type"         "branch"),
$(attr_str "vcs.repository.url.full"   "$REPO_URL"),
$(attr_str "vcs.repository.name"       "tesla-canary-app"),
$(attr_str "vcs.owner.name"            "irfadkp"),
$(attr_str "vcs.provider.name"         "github"),
$(attr_str "deployment.environment"    "$ENVIRONMENT")
EOF
)

PAYLOAD=$(cat <<EOF
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          $(attr_str "service.name"           "$SERVICE_NAME"),
          $(attr_str "deployment.environment" "$ENVIRONMENT"),
          $(attr_str "cicd.pipeline.name"     "tesla-app-cicd"),
          $(attr_str "service.namespace"      "tesla-shop")
        ]
      },
      "scopeSpans": [
        {
          "scope": { "name": "tesla-cicd-pipeline", "version": "1.0.0" },
          "spans": [
            {
              "traceId": "${TRACE_ID}",
              "spanId":  "${SPAN_ID}",
              ${PARENT_FIELD}
              "name":    "${SPAN_NAME}",
              "kind":    3,
              "startTimeUnixNano": "${START_NS}",
              "endTimeUnixNano":   "${END_NS}",
              "status": {
                "code":    ${STATUS_CODE},
                "message": "${STATUS_MSG}"
              },
              "attributes": [
                ${ATTRIBUTES}
              ]
            }
          ]
        }
      ]
    }
  ]
}
EOF
)

echo "[otel_send_span] Sending span '${SPAN_NAME}' (trace=${TRACE_ID}, span=${SPAN_ID}) to Instana"

# OTLP/HTTP JSON — requires endpoint that accepts application/json
# (otlp-orange-saas.instana.io, NOT the grpc-only endpoint)
HTTP_STATUS=$(curl --silent --output /dev/stderr --write-out "%{http_code}" \
  -X POST "${ENDPOINT}/v1/traces" \
  -H "Content-Type: application/json" \
  -H "x-instana-key: ${INSTANA_AGENT_KEY}" \
  --data "${PAYLOAD}" \
  --max-time 10 \
  --retry 2 \
  --retry-delay 1)

echo "[otel_send_span] HTTP status: ${HTTP_STATUS}"

# Warn on failure but never block the pipeline
if [[ "$HTTP_STATUS" != "200" && "$HTTP_STATUS" != "204" ]]; then
  echo "[otel_send_span] WARNING: non-2xx response ${HTTP_STATUS} — pipeline continues"
fi
