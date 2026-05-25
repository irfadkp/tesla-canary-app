#!/bin/bash
set -e

# Ferrari Canary App - Installer Script
# This script deploys the Ferrari app with Instana monitoring configured via Kubernetes secrets

echo "=== Ferrari Canary App Installer ==="
echo ""

# Configuration
NAMESPACE="ferrari-shop-dev"
ARGOCD_NAMESPACE="argocd-namespace"
APP_NAME="ferrari-canary-app"

# Instana Configuration (set these as environment variables or prompt for input)
INSTANA_AGENT_KEY="${INSTANA_AGENT_KEY:-}"
INSTANA_AGENT_ENDPOINT="${INSTANA_AGENT_ENDPOINT:-ingress-magenta-saas.instana.rocks}"
INSTANA_AGENT_PORT="${INSTANA_AGENT_PORT:-443}"
INSTANA_EUM_KEY="${INSTANA_EUM_KEY:-}"
INSTANA_EUM_ENDPOINT="${INSTANA_EUM_ENDPOINT:-eum-magenta-saas.instana.rocks}"

# Prompt for Instana keys if not set
if [ -z "$INSTANA_AGENT_KEY" ]; then
    read -p "Enter Instana Agent Key: " INSTANA_AGENT_KEY
fi

if [ -z "$INSTANA_EUM_KEY" ]; then
    read -p "Enter Instana EUM (End User Monitoring) Key: " INSTANA_EUM_KEY
fi

echo ""
echo "Step 1: Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "Step 2: Creating Instana secrets..."

# Backend Instana Secret
kubectl create secret generic backend-ferrari-instana-secret \
  --from-literal=INSTANA_AGENT_KEY="$INSTANA_AGENT_KEY" \
  --from-literal=INSTANA_AGENT_ENDPOINT="$INSTANA_AGENT_ENDPOINT" \
  --from-literal=INSTANA_AGENT_PORT="$INSTANA_AGENT_PORT" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Frontend Instana Secret
kubectl create secret generic frontend-ferrari-instana-secret \
  --from-literal=INSTANA_EUM_KEY="$INSTANA_EUM_KEY" \
  --from-literal=INSTANA_EUM_ENDPOINT="$INSTANA_EUM_ENDPOINT" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Java Service Instana Secret
kubectl create secret generic java-service-ferrari-instana-secret \
  --from-literal=INSTANA_AGENT_KEY="$INSTANA_AGENT_KEY" \
  --from-literal=INSTANA_AGENT_ENDPOINT="$INSTANA_AGENT_ENDPOINT" \
  --from-literal=INSTANA_AGENT_PORT="$INSTANA_AGENT_PORT" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "Step 3: Creating ArgoCD namespace..."
kubectl create namespace $ARGOCD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "Step 4: Deploying ArgoCD Application..."
kubectl apply -f gitops/argocd/application.yaml

echo ""
echo "Step 5: Waiting for ArgoCD to sync..."
sleep 5

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Ferrari Canary App has been deployed!"
echo ""
echo "To check the status:"
echo "  kubectl get applications -n $ARGOCD_NAMESPACE"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "To view ArgoCD application:"
echo "  argocd app get $APP_NAME --grpc-web"
echo ""
echo "Instana secrets created:"
echo "  - backend-ferrari-instana-secret"
echo "  - frontend-ferrari-instana-secret"
echo "  - java-service-ferrari-instana-secret"
echo ""
echo "Note: Instana keys are stored as Kubernetes secrets and not committed to Git."
