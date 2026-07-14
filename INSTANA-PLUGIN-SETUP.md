# Instana Metrics Plugin Integration for Argo Rollouts

## Overview
This document describes the integration of Kash's Instana metrics plugin with Argo Rollouts for automated canary deployment analysis in the Tesla Shop application.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Canary Deployment Flow                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  New Version     │
                    │  Deployed (20%)  │
                    └──────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Argo Rollouts Controller              │
        │   Triggers AnalysisRun                  │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Instana Metrics Plugin (RPC)          │
        │   - Queries Instana API                 │
        │   - Evaluates success conditions        │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Instana Tenant                        │
        │   https://release-instana.instana.rocks │
        │   - Returns error-rate metrics          │
        │   - Returns latency-p90 metrics         │
        └─────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Decision         │
                    │  ✅ Promote       │
                    │  ❌ Rollback      │
                    └──────────────────┘
```

## Components

### 1. Instana Metrics Plugin
- **Repository**: https://github.ibm.com/instana/rollouts-plugin-metric-instana
- **Built Binary**: `/root/rollouts-plugin-metric-instana/dist/rollouts-plugin-metric-instana`
- **SHA256**: `e7bccbcd12fdff62a241e076f67b4f76f60c994cdf4dde7ddbf46cdf8143100e`
- **Served via HTTP**: `http://9.60.231.225:8888/rollouts-plugin-metric-instana`

### 2. Argo Rollouts Configuration
**ConfigMap**: `argo-rollouts-config` (namespace: argo-rollouts)
```yaml
metricProviderPlugins:
  - name: "instana/metrics"
    location: "http://9.60.231.225:8888/rollouts-plugin-metric-instana"
    sha256: "e7bccbcd12fdff62a241e076f67b4f76f60c994cdf4dde7ddbf46cdf8143100e"
```

**API Token Secret**: `instana-api-token` (namespace: argo-rollouts)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: instana-api-token
  namespace: argo-rollouts
type: Opaque
data:
  token: <base64-encoded-token>
```

**Environment Variable**: Controller deployment configured with:
```yaml
env:
  - name: INSTANA_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: instana-api-token
        key: token
```

### 3. AnalysisTemplate
**File**: `gitops/base/backend/analysis-template.yaml`

**Metrics Configured**:
1. **error-rate**
   - Metric: `errors`
   - Aggregation: `MEAN`
   - Success Condition: `result <= 0.05` (5%)
   - Interval: 1 minute
   - Count: 5 measurements
   - Failure Limit: 2 consecutive failures

2. **latency-p90**
   - Metric: `latency`
   - Aggregation: `P90`
   - Success Condition: `result <= 1000` (1000ms)
   - Interval: 1 minute
   - Count: 5 measurements
   - Failure Limit: 2 consecutive failures

**Scoping**:
- Cluster: `in-cluster`
- Namespace: `tesla-shop-dev`
- Tag Filter: `kubernetes.pod.label.rollouts-pod-template-hash`
- Group By: Pod template hash (canary-specific)

### 4. Rollout Configuration
**File**: `gitops/base/backend/rollout.yaml`

**Canary Steps**:
1. Set weight to 20%
2. Pause 30 seconds
3. **Run Analysis** (error-rate + latency-p90)
4. Set weight to 50%
5. Pause 30 seconds
6. **Run Analysis** (error-rate + latency-p90)
7. Promote to 100% (if all analyses pass)

### 5. Error Simulator
**Backend Endpoint**: `/api/simulate-error`
- Controller: `ErrorSimulatorController.java`
- Method: POST
- Parameters: `statusCode`, `message`

**Frontend UI**: Error Simulator tab
- Customizable HTTP status codes (400-504)
- Repeat mode with configurable intervals (1-60s)
- Real-time request log

## Installation Steps

### 1. Build and Serve Plugin
```bash
# Clone repository
git clone https://${GITHUB_IBM_TOKEN}@github.ibm.com/instana/rollouts-plugin-metric-instana.git

# Build plugin
cd rollouts-plugin-metric-instana
go build -o dist/rollouts-plugin-metric-instana main.go

# Calculate SHA256
sha256sum dist/rollouts-plugin-metric-instana

# Serve via HTTP
cd dist
python3 -m http.server 8888 &
```

### 2. Configure Argo Rollouts
```bash
# Create API token secret
kubectl create secret generic instana-api-token \
  -n argo-rollouts \
  --from-literal=token=<YOUR_INSTANA_API_TOKEN>

# Update ConfigMap
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: argo-rollouts-config
  namespace: argo-rollouts
data:
  metricProviderPlugins: |-
    - name: "instana/metrics"
      location: "http://9.60.231.225:8888/rollouts-plugin-metric-instana"
      sha256: "e7bccbcd12fdff62a241e076f67b4f76f60c994cdf4dde7ddbf46cdf8143100e"
EOF

# Configure environment variable
kubectl patch deployment argo-rollouts -n argo-rollouts --type=json -p='[{
  "op": "replace",
  "path": "/spec/template/spec/containers/0/env",
  "value": [{
    "name": "INSTANA_API_TOKEN",
    "valueFrom": {
      "secretKeyRef": {
        "name": "instana-api-token",
        "key": "token"
      }
    }
  }]
}]'

# Restart controller
kubectl rollout restart deployment/argo-rollouts -n argo-rollouts
```

### 3. Deploy AnalysisTemplate and Rollout
```bash
# Commit and push changes
cd /root/tesla-canary-app
git add gitops/base/backend/analysis-template.yaml
git add gitops/base/backend/rollout.yaml
git add gitops/base/kustomization.yaml
git commit -m "Add Instana metrics analysis"
git push

# Sync ArgoCD
argocd app sync tesla-canary-app --grpc-web
```

## Testing

### Test Successful Promotion
1. Deploy new version (update image tag in kustomization.yaml)
2. Watch rollout progress:
   ```bash
   kubectl argo rollouts get rollout tesla-backend -n tesla-shop-dev --watch
   ```
3. Observe analysis runs:
   ```bash
   kubectl get analysisrun -n tesla-shop-dev --watch
   ```
4. If metrics pass (error-rate ≤ 5%, latency-p90 ≤ 1000ms), canary promotes automatically

### Test Automatic Rollback
1. Access Error Simulator: `http://tesla-shop.local/` → "Error Simulator" tab
2. Configure error injection:
   - Status Code: 500
   - Interval: 5 seconds
3. Click "Start Repeating"
4. Watch analysis fail and rollout abort:
   ```bash
   kubectl argo rollouts get rollout tesla-backend -n tesla-shop-dev
   ```
5. Observe automatic rollback to stable version

### Manual Promotion
```bash
# Promote canary to next step
kubectl argo rollouts promote tesla-backend -n tesla-shop-dev

# Abort rollout
kubectl argo rollouts abort tesla-backend -n tesla-shop-dev

# Retry failed rollout
kubectl argo rollouts retry rollout tesla-backend -n tesla-shop-dev
```

## Monitoring

### View Analysis Results
```bash
# List analysis runs
kubectl get analysisrun -n tesla-shop-dev

# View detailed analysis
kubectl get analysisrun <name> -n tesla-shop-dev -o yaml

# Check metrics
kubectl get analysisrun <name> -n tesla-shop-dev -o jsonpath='{.status.metricResults}'
```

### View Rollout Status
```bash
# Current status
kubectl argo rollouts status tesla-backend -n tesla-shop-dev

# Detailed view
kubectl argo rollouts get rollout tesla-backend -n tesla-shop-dev

# Watch progress
kubectl argo rollouts get rollout tesla-backend -n tesla-shop-dev --watch
```

### Instana Dashboard
- URL: https://release-instana.instana.rocks
- Navigate to: Applications → tesla-backend
- View: Error rate, Latency metrics, Call traces

## Troubleshooting

### Plugin Not Loading
**Symptom**: Controller logs show "failed to download plugin"
**Solution**:
1. Verify HTTP server is running: `curl http://9.60.231.225:8888/rollouts-plugin-metric-instana`
2. Check ConfigMap has correct URL and SHA256
3. Restart controller: `kubectl rollout restart deployment/argo-rollouts -n argo-rollouts`

### Authorization Failed
**Symptom**: Analysis shows "Authorization validation failed"
**Solution**:
1. Verify API token is correct: `kubectl get secret instana-api-token -n argo-rollouts -o yaml`
2. Check environment variable: `kubectl get deployment argo-rollouts -n argo-rollouts -o yaml | grep -A 5 INSTANA_API_TOKEN`
3. Ensure token has metrics read permissions in Instana

### Analysis Always Fails
**Symptom**: Metrics show high error rates even with no errors
**Solution**:
1. Verify scoping is correct (cluster name, namespace)
2. Check pod-template-hash label exists on pods
3. Review Instana query in plugin logs
4. Adjust success conditions if needed

### No Metrics Returned
**Symptom**: Analysis shows "no data" or empty results
**Solution**:
1. Verify Instana agent is running and reporting
2. Check application is instrumented correctly
3. Ensure traffic is flowing to canary pods
4. Review time window configuration (default: 300s)

## Configuration Reference

### Instana Plugin Parameters
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `host` | Yes | - | Instana tenant URL |
| `metric` | Yes | - | Metric ID (errors, latency, calls) |
| `aggregation` | No | MEAN | Aggregation type (MEAN, SUM, P90, P95, P99) |
| `granularity` | No | 60 | Seconds between data points |
| `timeWindowMs` | No | 60000 | Look-back window in milliseconds |
| `clusterName` | No | - | Kubernetes cluster name |
| `namespace` | No | - | Kubernetes namespace |
| `groupByTag` | No | kubernetes.pod.label | Tag to group by |
| `groupByTagKey` | No | rollouts-pod-template-hash | Label key for grouping |
| `selectGroup` | No | - | Select specific group by name |
| `apiTokenEnv` | No | INSTANA_API_TOKEN | Environment variable with token |

### Success Condition Syntax
- Comparison operators: `<`, `<=`, `>`, `>=`, `==`, `!=`
- Logical operators: `&&`, `||`
- Examples:
  - `result <= 0.05` (error rate ≤ 5%)
  - `result < 1000` (latency < 1000ms)
  - `result > 0 && result < 100` (between 0 and 100)

## Best Practices

1. **Start Conservative**: Begin with lenient thresholds and tighten over time
2. **Multiple Metrics**: Use both error-rate and latency for comprehensive analysis
3. **Sufficient Measurements**: Use at least 5 measurements for statistical significance
4. **Appropriate Intervals**: 1-minute intervals balance responsiveness and stability
5. **Failure Limits**: Allow 2 consecutive failures to avoid false positives
6. **Proper Scoping**: Always scope by cluster and namespace to avoid cross-contamination
7. **Test Rollbacks**: Regularly test automatic rollback with Error Simulator
8. **Monitor Instana**: Keep Instana dashboard open during deployments

## References

- Argo Rollouts Documentation: https://argo-rollouts.readthedocs.io/
- Instana API Documentation: https://www.ibm.com/docs/en/instana-observability/current
- Plugin Repository: https://github.ibm.com/instana/rollouts-plugin-metric-instana
- Analysis Template Spec: https://argo-rollouts.readthedocs.io/en/stable/features/analysis/

---
*Last Updated: 2026-07-14*
*Author: AI Agent*
