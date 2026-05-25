# Tesla Canary App - Drift Demo

This is a demonstration application that automatically creates configuration drift every 5 minutes to showcase ArgoCD's auto-sync capabilities.

## What This Demo Does

The `drift-demo.sh` script automatically:
1. **Changes image tags** in `gitops/overlays/dev/kustomization.yaml` every 5 minutes
2. **Commits and pushes** changes to GitHub
3. **Creates drift** - ArgoCD detects the cluster is out-of-sync with Git
4. **Auto-heals** - ArgoCD's auto-sync automatically fixes the drift

## Current Status

- **Application Name**: `tesla-canary-app`
- **Namespace**: `ferrari-shop-dev` (shared with Ferrari app)
- **Repository**: https://github.com/irfadkp/tesla-canary-app
- **ArgoCD URL**: https://localhost:32739/applications/tesla-canary-app

## Drift Demo Control

### Check if Drift Demo is Running
```bash
ps -p $(cat /tmp/tesla-drift-demo.pid) && echo "Running" || echo "Stopped"
```

### View Drift Demo Logs
```bash
tail -f /tmp/tesla-drift-demo.log
```

### Stop Drift Demo
```bash
kill $(cat /tmp/tesla-drift-demo.pid)
```

### Start Drift Demo
```bash
cd /root/tesla-canary-app
nohup ./drift-demo.sh > /tmp/tesla-drift-demo.log 2>&1 &
echo $! > /tmp/tesla-drift-demo.pid
```

## Monitor ArgoCD Sync Status

### Check Application Status
```bash
argocd app get tesla-canary-app --grpc-web
```

### Watch for Out-of-Sync Events
```bash
watch -n 5 'argocd app get tesla-canary-app --grpc-web | grep -E "Sync Status|Health Status"'
```

### View Sync History
```bash
argocd app history tesla-canary-app --grpc-web
```

## Expected Behavior

Every 5 minutes you should see:

1. **Drift Created** (in logs):
   ```
   [2026-05-25 00:26:52] Creating drift: Changing image tags to v1.0.15
   [2026-05-25 00:26:54] Drift created! ArgoCD will detect out-of-sync state
   ```

2. **ArgoCD Detects Drift**:
   - Sync Status changes to `OutOfSync`
   - Health Status remains `Healthy` or `Progressing`

3. **ArgoCD Auto-Heals** (within seconds):
   - Auto-sync triggers automatically
   - Sync Status returns to `Synced`
   - Cluster state matches Git repository

## Image Versions Cycle

The demo cycles through these versions:
- v1.0.14
- v1.0.15
- v1.0.16
- v1.0.17

## Troubleshooting

### Drift Demo Not Running
```bash
cd /root/tesla-canary-app
./drift-demo.sh
```

### ArgoCD Not Auto-Syncing
Check auto-sync is enabled:
```bash
kubectl get application tesla-canary-app -n argocd-namespace -o jsonpath='{.spec.syncPolicy.automated}'
```

Should show: `{"allowEmpty":false,"prune":true,"selfHeal":true}`

### View Recent Git Commits
```bash
cd /root/tesla-canary-app
git log --oneline -10
```

## Clean Up

To stop the demo and remove the application:
```bash
# Stop drift demo
kill $(cat /tmp/tesla-drift-demo.pid)

# Delete ArgoCD application
kubectl delete application tesla-canary-app -n argocd-namespace

# Optional: Delete the namespace (if not shared)
# kubectl delete namespace ferrari-shop-dev
```

## Notes

- The demo uses the same namespace as Ferrari app (`ferrari-shop-dev`)
- All resources have `ferrari-` prefix (inherited from cloned app)
- Only the ArgoCD application name is `tesla-canary-app`
- Drift is created by changing Git, not by manual kubectl changes
- This demonstrates GitOps principles: Git is the source of truth
