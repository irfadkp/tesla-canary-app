# Ferrari Canary App - Installation Guide

## Prerequisites

- Kubernetes cluster with kubectl configured
- ArgoCD installed in the cluster
- Instana account with Agent Key and EUM Key

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/irfadkp/ferrari-canary-app.git
cd ferrari-canary-app
```

### 2. Configure Instana Credentials

**Option A: Using Environment Variables**

```bash
export INSTANA_AGENT_KEY="your-agent-key"
export INSTANA_EUM_KEY="your-eum-key"
export INSTANA_AGENT_ENDPOINT="ingress-magenta-saas.instana.rocks"
export INSTANA_EUM_ENDPOINT="eum-magenta-saas.instana.rocks"
```

**Option B: Using .env File (Not Recommended for Production)**

```bash
cp .env.example .env
# Edit .env and add your keys
nano .env
```

**Note:** The `.env` file is in `.gitignore` and will not be committed to Git.

### 3. Run the Installer

```bash
chmod +x install.sh
./install.sh
```

The installer will:
1. Create the `ferrari-shop-dev` namespace
2. Create Kubernetes secrets with Instana credentials
3. Deploy the ArgoCD Application
4. Wait for ArgoCD to sync

### 4. Verify Installation

```bash
# Check ArgoCD application status
kubectl get applications -n argocd-namespace

# Check pods
kubectl get pods -n ferrari-shop-dev

# View ArgoCD application details
argocd app get ferrari-canary-app --grpc-web
```

## Instana Configuration

The installer creates the following secrets in the `ferrari-shop-dev` namespace:

- **backend-ferrari-instana-secret**: Contains agent key and endpoint for backend service
- **frontend-ferrari-instana-secret**: Contains EUM key and endpoint for frontend
- **java-service-ferrari-instana-secret**: Contains agent key and endpoint for Java service

These secrets are referenced by the application deployments and are **never committed to Git**.

## Security Best Practices

1. **Never commit Instana keys to Git**
   - Keys are stored as Kubernetes secrets
   - `.env` file is in `.gitignore`
   - Use environment variables or secret management tools

2. **Rotate keys regularly**
   - Update secrets in Kubernetes when rotating keys
   - Restart affected pods after updating secrets

3. **Use RBAC**
   - Limit access to the namespace containing secrets
   - Use Kubernetes RBAC to control who can read secrets

## Uninstallation

```bash
# Delete ArgoCD application
kubectl delete application ferrari-canary-app -n argocd-namespace

# Delete namespace (this will delete all resources including secrets)
kubectl delete namespace ferrari-shop-dev
```

## Troubleshooting

### Application not syncing

```bash
# Check ArgoCD application status
argocd app get ferrari-canary-app --grpc-web

# Force sync
argocd app sync ferrari-canary-app --grpc-web
```

### Pods not starting

```bash
# Check pod logs
kubectl logs -n ferrari-shop-dev <pod-name>

# Check if secrets exist
kubectl get secrets -n ferrari-shop-dev
```

### Instana not receiving data

1. Verify secrets contain correct keys
2. Check Instana agent is running in the cluster
3. Verify network connectivity to Instana endpoints

## Support

For issues related to:
- **Application deployment**: Check ArgoCD logs and application manifests
- **Instana integration**: Verify secrets and check Instana agent logs
- **Build issues**: Check GitHub Actions workflow logs
