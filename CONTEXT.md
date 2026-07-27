# CONTEXT.md — Tesla Canary App: OTel CI/CD Monitoring Initiative
> **Hand-off context for the next chat session.**
> Read this entire file before taking any action.

---

## 1. Initiative Overview

We are building **CI/CD Pipeline Monitoring with Instana**.
The concept: GitHub Actions pipelines emit OTel signals (traces + metrics) that Instana
ingests, correlates to APM service entities, and surfaces in a new **CI/CD Pipeline tab**
on the service detail page.

Full spec lives at:
- `/root/cicd_pipeline_monitoring_instana/AGENTS.md` — agent operating rules, signal contract
- `/root/cicd_pipeline_monitoring_instana/PROJECT.md` — full concept, architecture, UI spec
- Also pushed to IBM GHE: `https://github.ibm.com/IRFAD-K-P/cicd-obsevability-instana-context-centre`

---

## 2. This Repo — Tesla Canary App

| Property | Value |
|---|---|
| Repo | `https://github.com/irfadkp/tesla-canary-app` |
| Local path | `/root/tesla-canary-app` |
| ArgoCD app | `tesla-canary-app` |
| Namespace | `tesla-shop-dev` |
| Strategy | Canary (Argo Rollouts + Instana metrics analysis) |
| Instana service names | `tesla-backend`, `tesla-frontend` |

---

## 3. What Is Already Done ✅

### Step 1 — Initiative docs
- `/root/cicd_pipeline_monitoring_instana/AGENTS.md` ✅
- `/root/cicd_pipeline_monitoring_instana/PROJECT.md` ✅
- `/root/cicd_pipeline_monitoring_instana/demo/README.md` ✅
- All pushed to IBM GHE context repo ✅

### Step 2 — Tesla GitHub Actions pipeline instrumented ✅
Files added/modified:

| File | What it does |
|---|---|
| `.github/workflows/ci-cd.yaml` | 4-job pipeline: `pipeline-init` → `build-backend` + `build-frontend` (parallel) → `otel-finalize` |
| `.github/scripts/otel_send_span.sh` | Sends one OTLP/HTTP span to Instana |
| `.github/scripts/otel_send_metrics.sh` | Sends DORA metrics (deployment.frequency, pipeline.duration, change_failure_rate) |

Last successful pipeline run: **30252306527** — all OTel steps returned HTTP 200.

### Step 3 — Instana OTel Collector installed in cluster ✅
```
helm install instana-otel-collector \
  --repo https://instana.github.io/instana-otel-collector instana-otel-collector-chart \
  --namespace instana-otel-collector \
  --set clusterName=in-cluster \
  --set instanaEndpoint=otlp-grpc-orange-saas.instana.io:443 \
  --set instanaKey=uBp4GXpZQpKrHxMXNcvInQ
```

Pods running:
```
instana-otel-collector-daemonset-agent-2gbf2   1/1 Running
instana-otel-collector-statefulset-0           1/1 Running
```

Service ClusterIP: `10.43.10.105`
- Port 4318 (OTLP/HTTP) ✅ accepting spans
- Port 4317 (OTLP/gRPC) ❌ not reachable from host network

Exporter config (from helm chart configmap):
```yaml
exporters:
  otlp/instana:
    endpoint: otlp-grpc-orange-saas.instana.io:443
    headers:
      x-instana-key: uBp4GXpZQpKrHxMXNcvInQ
    tls:
      insecure: false
      insecure_skip_verify: true
```

---

## 4. Instana Credentials & Endpoints

| Item | Value |
|---|---|
| **OTLP ingest endpoint (direct HTTP+JSON)** | `https://otlp-orange-saas.instana.io` |
| **OTLP ingest endpoint (gRPC via collector)** | `otlp-grpc-orange-saas.instana.io:443` |
| **Agent key** | `uBp4GXpZQpKrHxMXNcvInQ` (in `.env` and GitHub Actions secret `INSTANA_AGENT_KEY`) |
| **Instana REST API base** | `https://ibmdevsandbox-instanaibm.instana.io` |
| **REST API token** | `Wh9UU3gASkS_wVCHDmHVEQ` (from `kubectl get secret instana-credentials -n ford-shop-dev`) |
| **Instana UI** | `https://ibmdevsandbox-instanaibm.instana.io` |
| **otelCount (last seen)** | 1,228 OTel entities |
| **otelCollectorCount** | 43 (our collector is registered) |

---

## 5. OTel Signal Contract

Every span sent by the pipeline carries these attributes:

**Resource attributes (on every span):**
```
service.name           = "tesla-backend-001"  (test) / "tesla-backend" / "tesla-frontend" (prod)
instana.plugin.name    = "otel-sensorsdk-cicd"
deployment.environment = "dev"
cicd.tool              = "github-actions"
cicd.pipeline.name     = "tesla-app-cicd"
cluster.name           = "in-cluster"
```

**Span attributes:**
```
http.method            = "POST"
http.url               = "/cicd/pipeline/build"
http.status_code       = 200
cicd.pipeline.run.id   = "<github-run-id>-<attempt>"
cicd.stage.name        = "build-backend" | "build-frontend" | "checkout" | "pipeline-run"
cicd.image.tag         = "1.0.9"
cicd.commit.sha        = "<sha>"
cicd.repo.ref          = "master"
cicd.repo.url          = "https://github.com/irfadkp/tesla-canary-app"
```

---

## 6. How to Query Instana REST API

### Confirmed working (fast, from this machine):
```bash
INSTANA_API_TOKEN="Wh9UU3gASkS_wVCHDmHVEQ"
BASE="https://ibmdevsandbox-instanaibm.instana.io"

# Check OTel entity count
curl -s "${BASE}/api/infrastructure-monitoring/monitoring-state" \
  -H "authorization: apiToken ${INSTANA_API_TOKEN}"
```

### Analytics query (POST — use from your laptop, times out from this machine):
```bash
NOW_MS=$(date +%s%3N)
curl -X POST "${BASE}/api/application-monitoring/analyze/call-groups" \
  -H "Content-Type: application/json" \
  -H "authorization: apiToken ${INSTANA_API_TOKEN}" \
  --data '{
    "tagFilterExpression": {
      "type": "TAG_FILTER",
      "name": "otel_resource.service.name",
      "operator": "EQUALS",
      "entity": "DESTINATION",
      "value": "tesla-backend-001"
    },
    "metrics": [
      {"metric": "calls",   "aggregation": "SUM"},
      {"metric": "errors",  "aggregation": "MEAN"},
      {"metric": "latency", "aggregation": "MEAN"}
    ],
    "includeInternal": false,
    "includeSynthetic": false,
    "timeFrame": {"windowSize": 3600000},
    "group": {
      "groupbyTag": "endpoint.name",
      "groupbyTagEntity": "DESTINATION"
    }
  }'
```

### Known issue: POST analytics API times out from this machine
- `GET` endpoints (monitoring-state) work fine — HTTP 200 in ~0.5s
- `POST` to `analyze/call-groups`, `analyze/traces` hang and time out
- **Workaround**: run from your laptop or use Instana UI directly

---

## 7. How to Send a Test OTel Span

### Via Instana OTel Collector (gRPC → Instana backend):
```bash
COLLECTOR_IP=$(kubectl get svc instana-otel-collector-statefulset \
  -n instana-otel-collector -o jsonpath='{.spec.clusterIP}')
# COLLECTOR_IP = 10.43.10.105

TRACE_ID=$(openssl rand -hex 16)
SPAN_ID=$(openssl rand -hex 8)
START_NS=$(date +%s%N); sleep 1; END_NS=$(date +%s%N)

curl -s -w "HTTP %{http_code}\n" \
  -X POST "http://${COLLECTOR_IP}:4318/v1/traces" \
  -H "Content-Type: application/json" \
  --data '{
    "resourceSpans": [{
      "resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "tesla-backend-001"}}
      ]},
      "scopeSpans": [{"spans": [{
        "traceId": "'$TRACE_ID'",
        "spanId":  "'$SPAN_ID'",
        "name":    "/cicd/pipeline/build",
        "kind":    2,
        "startTimeUnixNano": "'$START_NS'",
        "endTimeUnixNano":   "'$END_NS'",
        "status": {"code": 1, "message": "success"}
      }]}]
    }]
  }'
```

### Via direct OTLP/HTTP (bypasses collector):
```bash
export INSTANA_AGENT_KEY="uBp4GXpZQpKrHxMXNcvInQ"
export INSTANA_OTLP_ENDPOINT="https://otlp-orange-saas.instana.io"

bash .github/scripts/otel_send_span.sh \
  "$(openssl rand -hex 16)" "$(openssl rand -hex 8)" "" "test-span" \
  "$(date +%s%N)" "$(date +%s%N)" "1" "success" "tesla-backend-001" \
  "test-run-001" "1.0.9" "abc123" "master" \
  "https://github.com/irfadkp/tesla-canary-app"
```

---

## 8. Remaining Steps (TODO for Next Chat)

### Step 3 — Forge backend plugin `otel-sensorsdk-cicd` (HUMAN)
> **Owner: Human engineer**
The Forge plugin that maps OTel spans with `instana.plugin.name=otel-sensorsdk-cicd`
to a new `CICD_PIPELINE` entity type and correlates it to the `SERVICE` entity via
`service.name` matching. Design spec in `PROJECT.md §Forge Backend Plugin`.

### Step 4 — Verify OTel data is visible in Instana UI (NEXT AGENT TASK)
- [ ] Open `https://ibmdevsandbox-instanaibm.instana.io` → Analytics → Traces
- [ ] Filter: `otel_resource.service.name = "tesla-backend-001"`
- [ ] Confirm span structure matches: `service`, `destination`, `spans[].data.resource`
- [ ] Confirm the test spans sent via collector appear under correct service

### Step 5 — Update GitHub Actions to send via collector (NEXT AGENT TASK)
Current state: GitHub Actions sends directly to `otlp-orange-saas.instana.io` (HTTP+JSON).
Better path: send to the in-cluster collector via the collector's ClusterIP.
**Problem**: GitHub Actions runners are external — can't reach in-cluster ClusterIP.
**Options**:
- (a) Keep direct HTTP+JSON to `otlp-orange-saas.instana.io` ← current, working
- (b) Deploy a NodePort/LoadBalancer for the collector so runners can reach it
- (c) Add a deploy step that sends spans from inside the cluster post-deploy

### Step 6 — Build CI/CD Pipeline tab in Instana frontend (AGENT TASK)
Full UI spec in `PROJECT.md §7 UI Specification`. Seven panels:
1. Combined View (landing)
2. Overall Deployment Health
3. DORA Metrics Panel
4. Timeline View
5. Pipeline View (Gantt)
6. Deployment List
7. Deployment Detail View (with Metrics, Logs, Traces, Changes, Impact Analysis)

### Step 7 — Forge plugin DESIGN.md (AGENT TASK)
Write `/root/cicd_pipeline_monitoring_instana/forge-plugin/DESIGN.md` for the human
engineer implementing Step 3. Model after `otel-sensorsdk-dcgm` pattern.

---

## 9. Key File Locations

```
/root/
├── tesla-canary-app/                          ← THIS REPO
│   ├── CONTEXT.md                             ← this file
│   ├── .env                                   ← INSTANA_AGENT_KEY=uBp4GXpZQpKrHxMXNcvInQ
│   ├── .github/
│   │   ├── workflows/ci-cd.yaml               ← instrumented pipeline (4 jobs)
│   │   └── scripts/
│   │       ├── otel_send_span.sh              ← OTLP/HTTP span sender
│   │       └── otel_send_metrics.sh           ← DORA metrics sender
│   └── gitops/
│       ├── base/backend/rollout.yaml          ← INSTANA_SERVICE_NAME=tesla-backend
│       └── base/frontend/deployment.yaml      ← service label: tesla-frontend
│
└── cicd_pipeline_monitoring_instana/          ← INITIATIVE CONTEXT
    ├── AGENTS.md                              ← signal contract, agent rules
    ├── PROJECT.md                             ← full spec + UI wireframes
    └── demo/README.md                         ← demo walkthrough
```

---

## 10. Quick Validation Commands

```bash
# Check collector is running
kubectl get pods -n instana-otel-collector

# Check Instana OTel entity count
curl -s "https://ibmdevsandbox-instanaibm.instana.io/api/infrastructure-monitoring/monitoring-state" \
  -H "authorization: apiToken Wh9UU3gASkS_wVCHDmHVEQ" | python3 -m json.tool

# Send test span via collector
COLLECTOR_IP=10.43.10.105
TRACE_ID=$(openssl rand -hex 16); SPAN_ID=$(openssl rand -hex 8)
START_NS=$(date +%s%N); sleep 1; END_NS=$(date +%s%N)
curl -s -w "HTTP %{http_code}\n" \
  -X POST "http://${COLLECTOR_IP}:4318/v1/traces" \
  -H "Content-Type: application/json" \
  --data "{\"resourceSpans\":[{\"resource\":{\"attributes\":[{\"key\":\"service.name\",\"value\":{\"stringValue\":\"tesla-backend-001\"}}]},\"scopeSpans\":[{\"spans\":[{\"traceId\":\"${TRACE_ID}\",\"spanId\":\"${SPAN_ID}\",\"name\":\"/cicd/pipeline/build\",\"kind\":2,\"startTimeUnixNano\":\"${START_NS}\",\"endTimeUnixNano\":\"${END_NS}\",\"status\":{\"code\":1,\"message\":\"success\"}}]}]}]}"

# Check latest pipeline run
cd /root/tesla-canary-app && gh run list --limit 3

# Check ArgoCD Tesla app
argocd app get tesla-canary-app --grpc-web
```

---

*Last updated: 2025-07-27*
*Context maintained by: AI Agent (Bob)*
*Continue in new chat — read this file first.*
