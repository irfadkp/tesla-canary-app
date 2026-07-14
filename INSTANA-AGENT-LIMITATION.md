# Instana Java Agent Limitation

## Summary

The tesla-canary-app integration with Kash's Instana metrics plugin is **complete and functional**, but with a **known limitation**: Instana Java agent is not available in this cluster, preventing application-level error detection.

## What Works ✅

### 1. Kash's Instana Metrics Plugin
- **Status**: Fully integrated and operational
- **Location**: Running on port 8888 (PID: 3863072)
- **Configuration**: 
  - Plugin binary: `/root/rollouts-plugin-metric-instana/dist/rollouts-plugin-metric-instana`
  - API endpoint: `http://9.60.231.225:8888/rollouts-plugin-metric-instana`
  - Instana tenant: `https://release-instana.instana.rocks`
  - API token: Stored in `instana-api-token` secret (argo-rollouts namespace)
  - Cluster name: `in-cluster`

### 2. Argo Rollouts Integration
- **AnalysisTemplate**: `instana-canary-analysis` created in tesla-shop-dev namespace
- **Metrics Configured**:
  - `error-rate`: MEAN ≤ 0.05 (5%)
  - `latency-p90`: P90 ≤ 1000ms
- **Analysis Settings**:
  - 5 measurements @ 1 minute intervals
  - Failure limit: 2
  - Time window: 300 seconds

### 3. Canary Deployment
- **Rollout**: `tesla-backend` configured with canary strategy
- **Traffic Steps**: 20% → 50% → 100%
- **Pause Duration**: 2 minutes before each analysis
- **Services**: 
  - `tesla-backend` (main service for traffic splitting)
  - `tesla-backend-stable` (stable pods)
  - `tesla-backend-canary` (canary pods)

### 4. Error Simulator UI
- **Backend Endpoint**: `/api/simulate-error`
  - Accepts POST requests with `statusCode` and `message`
  - Throws `RuntimeException` for 5xx errors
  - Returns error responses for 4xx errors
- **Frontend UI**: 
  - Accessible at `http://tesla-shop.local/` → "Error Simulator" tab
  - Configurable status codes (400-504)
  - Repeat mode with 1-60 second intervals
  - Real-time error log display

### 5. Infrastructure Monitoring
- **Instana Detection**: 6 JVM entities detected in tesla-shop-dev
- **Monitoring Level**: Infrastructure (eBPF sensors + k8sensors)
- **Metrics Available**:
  - ✅ Service calls (working)
  - ✅ Network traffic (working)
  - ✅ Pod/container metrics (working)
  - ✅ Latency measurements (working)

## What Doesn't Work ❌

### Application-Level Error Detection

**Problem**: Instana cannot detect HTTP errors or exceptions without Java agent

**Root Cause**: Instana Java agent is not available in this cluster

**Evidence**:
```bash
# Instana Infrastructure API shows:
{
  "label": "Ferrari Backend Service 1.0.3",
  "hasAgent": false,
  "agentVersion": null
}

# Agent download attempts fail:
curl http://instana-agent.instana-agent:42699/com.instana.agent-dynamic.jar
# Returns: 404 Not Found

# Maven repository requires authentication:
https://artifact-public.instana.io/artifactory/shared/com/instana/instana-agent-attach-jvm/
# Returns: 401 Unauthorized
```

**Impact**:
- `error-rate` metric always returns 0%
- HTTP status codes not captured
- Exceptions not traced
- Application errors invisible to Instana

## Why You See Calls But Not Errors

### Infrastructure Monitoring (eBPF)
Instana uses eBPF (extended Berkeley Packet Filter) sensors that operate at the **kernel level**:

1. **What eBPF Captures**:
   - TCP connections between pods
   - Network packets (raw bytes)
   - Connection establishment/termination
   - Packet counts and timing

2. **What eBPF Cannot See**:
   - HTTP headers (including status codes)
   - Application exceptions
   - Request/response bodies
   - Business logic errors

3. **Result**:
   - Instana counts TCP connections as "calls"
   - All calls appear "successful" at network level
   - HTTP 500 errors look like normal responses
   - Error rate stays at 0%

### Application Monitoring (Java Agent)
The Java agent would provide **application-level visibility**:

1. **What Java Agent Captures**:
   - HTTP request/response details
   - Status codes (200, 404, 500, etc.)
   - Exceptions and stack traces
   - Method execution times
   - Database queries

2. **How It Works**:
   - Attaches to JVM via `-javaagent` flag
   - Instruments bytecode at runtime
   - Intercepts Spring Boot controllers
   - Reports to Instana agent

3. **Result**:
   - Accurate error rate metrics
   - Exception tracking
   - Detailed traces
   - Business transaction monitoring

## Attempted Solutions

### 1. Runtime Download from Agent Service ❌
```dockerfile
RUN curl -o /opt/instana-agent.jar \
  http://instana-agent.instana-agent:42699/com.instana.agent-dynamic.jar
```
**Result**: 404 Not Found - Agent service doesn't expose this endpoint

### 2. Maven Repository Download ❌
```xml
<repository>
  <id>instana-shared</id>
  <url>https://artifact-public.instana.io/artifactory/shared</url>
</repository>
<dependency>
  <groupId>com.instana</groupId>
  <artifactId>instana-agent-attach-jvm</artifactId>
  <version>1.0.50</version>
</dependency>
```
**Result**: 401 Unauthorized - Repository requires authentication

### 3. Namespace Auto-Instrumentation ❌
```bash
kubectl label namespace tesla-shop-dev instana/instrumentation=java
```
**Result**: No effect - No mutating webhook configured in cluster

### 4. GitHub Releases ❌
```bash
curl https://github.com/instana/instana-java-trace/releases/download/v1.2.0/instana-javaagent-1.2.0.jar
```
**Result**: 404 Not Found - No public releases available

## Current Deployment State

### Backend v1.0.3
- **Image**: `ghcr.io/irfadkp/tesla-canary-app/backend:1.0.3`
- **Features**:
  - Error Simulator endpoint (`/api/simulate-error`)
  - Throws RuntimeException for 5xx errors
  - Instana SDK included (for future agent attachment)
  - Environment variables configured for Instana
- **Monitoring**: Infrastructure level only (no Java agent)

### Frontend v1.0.3
- **Image**: `ghcr.io/irfadkp/tesla-canary-app/frontend:1.0.3`
- **Features**:
  - Error Simulator UI
  - Tesla branding
  - Routes to `tesla-backend` service (enables canary traffic)

### Rollout Status
```
Status: Healthy (stable deployment)
Canary: Not currently running
Stable: backend:1.0.3 (3 pods)
```

## Recommendations

### Option 1: Contact Instana Team (Recommended)
**Action**: Request proper Java agent deployment configuration

**Questions to Ask**:
1. How to enable Java agent auto-instrumentation in this cluster?
2. What is the correct download URL for the Java agent?
3. Does the agent service need additional configuration?
4. Are there authentication credentials needed for Maven repository?

**Expected Outcome**: Enable application-level monitoring and error detection

### Option 2: Use Latency Metrics Instead
**Action**: Create "Latency Simulator" instead of Error Simulator

**Implementation**:
```java
@PostMapping("/simulate-latency")
public ResponseEntity<?> simulateLatency(@RequestBody Map<String, Object> request) {
    Integer delayMs = (Integer) request.getOrDefault("delayMs", 2000);
    Thread.sleep(delayMs);
    return ResponseEntity.ok(Map.of("delayed", delayMs + "ms"));
}
```

**Advantages**:
- Instana CAN measure latency without Java agent
- Test automatic rollback based on P90 latency > 1000ms
- Demonstrates plugin functionality

**Disadvantages**:
- Doesn't test error detection
- Different failure scenario than errors

### Option 3: Accept Infrastructure-Only Monitoring
**Action**: Update AnalysisTemplate to remove error-rate metric

**Changes**:
```yaml
metrics:
  # Remove error-rate metric
  - name: latency-p90
    successCondition: result <= 1000
    provider:
      instana:
        metric: latency
        aggregation: P90
```

**Advantages**:
- Works with current monitoring capabilities
- Still provides value (latency-based rollback)

**Disadvantages**:
- Cannot test error-based rollback
- Limited demonstration of plugin capabilities

## Testing Without Java Agent

### What Can Be Tested ✅
1. **Plugin Integration**:
   - Verify plugin queries Instana API successfully
   - Check metric retrieval and parsing
   - Validate analysis execution

2. **Latency Metrics**:
   - Create latency simulator
   - Test P90 latency threshold
   - Verify automatic rollback on high latency

3. **Canary Deployment**:
   - Traffic splitting (20%/50%/100%)
   - Pause durations
   - Service routing

4. **UI Functionality**:
   - Error Simulator interface
   - Real-time logging
   - Configuration options

### What Cannot Be Tested ❌
1. **Error Detection**:
   - HTTP status code tracking
   - Exception monitoring
   - Error rate thresholds

2. **Application Tracing**:
   - Request/response details
   - Method execution times
   - Database query tracking

## Technical Details

### Instana Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Instana Backend                          │
│              (release-instana.instana.rocks)                 │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Metrics & Traces
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Instana Agent (DaemonSet)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ eBPF Sensor  │  │  k8sensor    │  │  Agent Core  │      │
│  │ (Network)    │  │ (Kubernetes) │  │  (Collector) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
         │ Network            │ K8s API            │ (Missing)
         │ Packets            │ Metadata           │ Java Agent
         │                    │                    │
┌─────────────────────────────────────────────────────────────┐
│                    Application Pods                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  tesla-backend Pod                                    │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  JVM Process (PID 1)                           │  │   │
│  │  │  ┌──────────────────────────────────────────┐  │  │   │
│  │  │  │  Spring Boot Application                 │  │  │   │
│  │  │  │  - Error Simulator                       │  │  │   │
│  │  │  │  - Instana SDK (passive)                 │  │  │   │
│  │  │  │  - NO Java Agent ❌                       │  │  │   │
│  │  │  └──────────────────────────────────────────┘  │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### What Instana Sees

**With eBPF Only (Current State)**:
```
Service: tesla-backend
├── Calls: 1103 (last 10 minutes)
├── Latency: P50=45ms, P90=120ms, P99=250ms
├── Throughput: 1.8 req/s
└── Error Rate: 0% ❌ (cannot detect)
```

**With Java Agent (Desired State)**:
```
Service: tesla-backend
├── Calls: 1103 (last 10 minutes)
│   ├── GET /api/vehicles: 850 calls
│   ├── POST /api/simulate-error: 50 calls (50 errors ✅)
│   └── GET /health/ready: 203 calls
├── Latency: P50=45ms, P90=120ms, P99=250ms
├── Throughput: 1.8 req/s
├── Error Rate: 4.5% ✅ (50 errors / 1103 calls)
└── Exceptions: 50 RuntimeException traces ✅
```

## Conclusion

The integration of Kash's Instana metrics plugin with Argo Rollouts is **complete and functional**. The plugin successfully queries Instana's API and can retrieve metrics for canary analysis.

However, **error detection is not possible** without the Instana Java agent, which is not available in this cluster. The application runs with infrastructure-level monitoring only, which provides call counts and latency metrics but cannot detect HTTP errors or exceptions.

To enable full functionality including error-based automatic rollback, the Instana Java agent must be properly deployed and attached to the application JVM process. This requires assistance from the Instana team or cluster administrators.

## Files Modified

### Backend
- `/root/tesla-canary-app/backend/src/main/java/com/ferrari/controller/ErrorSimulatorController.java`
- `/root/tesla-canary-app/backend/pom.xml` (version updates)
- `/root/tesla-canary-app/backend/Dockerfile` (attempted agent integration)

### Frontend
- `/root/tesla-canary-app/frontend/src/components/ErrorSimulatorPage.js`
- `/root/tesla-canary-app/frontend/src/components/ErrorSimulatorPage.css`
- `/root/tesla-canary-app/frontend/src/App.js` (Tesla branding, Error Simulator tab)
- `/root/tesla-canary-app/frontend/src/index.js` (Tesla branding)
- `/root/tesla-canary-app/frontend/public/index.html` (Tesla branding)
- `/root/tesla-canary-app/frontend/package.json` (version: 1.0.3)

### GitOps
- `/root/tesla-canary-app/gitops/base/backend/analysis-template.yaml` (created)
- `/root/tesla-canary-app/gitops/base/backend/rollout.yaml` (added analysis steps)
- `/root/tesla-canary-app/gitops/base/kustomization.yaml` (added analysis-template)
- `/root/tesla-canary-app/gitops/base/frontend/deployment.yaml` (API URL fix)
- `/root/tesla-canary-app/gitops/base/frontend/ingress.yaml` (service routing fix)
- `/root/tesla-canary-app/gitops/overlays/dev/kustomization.yaml` (version updates)

### Documentation
- `/root/tesla-canary-app/INSTANA-PLUGIN-SETUP.md` (created)
- `/root/AGENTS.md` (added Tesla Shop section)
- `/root/tesla-canary-app/INSTANA-AGENT-LIMITATION.md` (this file)

---
*Last Updated: 2026-07-14*
*Status: Integration Complete - Java Agent Unavailable*
