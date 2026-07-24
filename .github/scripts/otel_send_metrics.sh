#!/usr/bin/env bash
# otel_send_metrics.sh — emit DORA OTel metrics to Instana via OTLP/HTTP
#
# Usage:
#   otel_send_metrics.sh <trace_id> <pipeline_run_id> <service_name> \
#                        <duration_s> <deploy_success> <cfr> \
#                        <image_tag> <ref_name>
#
# Arguments:
#   trace_id          32-char hex trace ID (for correlation)
#   pipeline_run_id   GitHub run ID + attempt
#   service_name      Instana APM service name (e.g. "tesla-backend")
#   duration_s        pipeline total wall-clock duration in seconds (integer)
#   deploy_success    1 = successful deploy, 0 = failed
#   cfr               change failure rate for this run: 0.0 = pass, 1.0 = fail
#   image_tag         container image tag
#   ref_name          branch or tag name
#
# Required env vars:
#   INSTANA_AGENT_KEY
#   INSTANA_OTLP_ENDPOINT  (optional)
#   INSTANA_PLUGIN_NAME    (optional)
#   DEPLOYMENT_ENVIRONMENT (optional)

set -euo pipefail

TRACE_ID="${1}"
PIPELINE_RUN_ID="${2}"
SERVICE_NAME="${3}"
DURATION_S="${4}"
DEPLOY_SUCCESS="${5}"    # 1 or 0
CFR="${6}"               # 0.0 or 1.0
IMAGE_TAG="${7:-}"
REF_NAME="${8:-}"

ENDPOINT="${INSTANA_OTLP_ENDPOINT:-https://release-instana.instana.rocks}"
PLUGIN_NAME="${INSTANA_PLUGIN_NAME:-otel-sensorsdk-cicd}"
ENVIRONMENT="${DEPLOYMENT_ENVIRONMENT:-dev}"
NOW_NS=$(date +%s%N)

attr_str() { echo "{ \"key\": \"$1\", \"value\": { \"stringValue\": \"$2\" } }"; }
attr_int() { echo "{ \"key\": \"$1\", \"value\": { \"intValue\": $2 } }"; }

# Shared resource attributes for all metrics
RESOURCE_ATTRS=$(cat <<EOF
$(attr_str "service.name"           "$SERVICE_NAME"),
$(attr_str "instana.plugin.name"    "$PLUGIN_NAME"),
$(attr_str "deployment.environment" "$ENVIRONMENT"),
$(attr_str "cicd.tool"              "github-actions"),
$(attr_str "cicd.pipeline.name"     "tesla-app-cicd")
EOF
)

# Shared data-point attributes
DP_ATTRS=$(cat <<EOF
$(attr_str "cicd.pipeline.run.id"  "$PIPELINE_RUN_ID"),
$(attr_str "cicd.image.tag"        "$IMAGE_TAG"),
$(attr_str "cicd.repo.ref"         "$REF_NAME"),
$(attr_str "deployment.environment" "$ENVIRONMENT")
EOF
)

# Helper: build a single Gauge data-point
gauge_dp() {
  local val="$1"
  cat <<EOF
{
  "attributes": [ ${DP_ATTRS} ],
  "timeUnixNano": "${NOW_NS}",
  "asDouble": ${val}
}
EOF
}

# Helper: build a single Sum (Counter) data-point
sum_dp() {
  local val="$1"
  cat <<EOF
{
  "attributes": [ ${DP_ATTRS} ],
  "timeUnixNano": "${NOW_NS}",
  "asInt": ${val}
}
EOF
}

PAYLOAD=$(cat <<EOF
{
  "resourceMetrics": [
    {
      "resource": {
        "attributes": [ ${RESOURCE_ATTRS} ]
      },
      "scopeMetrics": [
        {
          "scope": { "name": "tesla-cicd-pipeline", "version": "1.0.0" },
          "metrics": [
            {
              "name":        "cicd.deployment.frequency",
              "description": "Number of deployments (counter, +1 per run)",
              "unit":        "{deployment}",
              "sum": {
                "dataPoints":              [ $(sum_dp "$DEPLOY_SUCCESS") ],
                "aggregationTemporality": 2,
                "isMonotonic":            true
              }
            },
            {
              "name":        "cicd.pipeline.duration.seconds",
              "description": "Full pipeline wall-clock duration",
              "unit":        "s",
              "gauge": {
                "dataPoints": [ $(gauge_dp "$DURATION_S") ]
              }
            },
            {
              "name":        "cicd.change_failure_rate",
              "description": "Change failure rate for this run (0.0=pass, 1.0=fail)",
              "unit":        "1",
              "gauge": {
                "dataPoints": [ $(gauge_dp "$CFR") ]
              }
            }
          ]
        }
      ]
    }
  ]
}
EOF
)

echo "[otel_send_metrics] Sending DORA metrics for run ${PIPELINE_RUN_ID} to Instana"

HTTP_STATUS=$(curl --silent --output /dev/stderr --write-out "%{http_code}" \
  -X POST "${ENDPOINT}/otlp/v1/metrics" \
  -H "Content-Type: application/json" \
  -H "x-instana-key: ${INSTANA_AGENT_KEY}" \
  --data "${PAYLOAD}" \
  --max-time 10 \
  --retry 2 \
  --retry-delay 1)

echo "[otel_send_metrics] HTTP status: ${HTTP_STATUS}"

if [[ "$HTTP_STATUS" != "200" && "$HTTP_STATUS" != "204" ]]; then
  echo "[otel_send_metrics] WARNING: non-2xx response ${HTTP_STATUS} — pipeline continues"
fi
