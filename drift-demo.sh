#!/bin/bash
# Tesla Canary App - Drift Demo Script
# This script simulates configuration drift by changing image tags every 5 minutes
# ArgoCD auto-sync will detect and fix the drift automatically

set -e

KUSTOMIZATION_FILE="/root/tesla-canary-app/gitops/overlays/dev/kustomization.yaml"
REPO_DIR="/root/tesla-canary-app"
DRIFT_INTERVAL=300  # 5 minutes in seconds

# Image versions to cycle through
VERSIONS=("v1.0.14" "v1.0.15" "v1.0.16" "v1.0.17")
CURRENT_INDEX=0

echo "=== Tesla Canary App - Drift Demo Started ==="
echo "This script will create drift every ${DRIFT_INTERVAL} seconds (5 minutes)"
echo "ArgoCD auto-sync will automatically fix the drift"
echo ""

while true; do
    # Get current version
    CURRENT_VERSION="${VERSIONS[$CURRENT_INDEX]}"
    
    # Calculate next version index
    CURRENT_INDEX=$(( (CURRENT_INDEX + 1) % ${#VERSIONS[@]} ))
    NEXT_VERSION="${VERSIONS[$CURRENT_INDEX]}"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creating drift: Changing image tags to ${NEXT_VERSION}"
    
    # Change image tags in kustomization.yaml
    cd "$REPO_DIR"
    sed -i "s/newTag: \".*\"/newTag: \"${NEXT_VERSION}\"/g" "$KUSTOMIZATION_FILE"
    
    # Commit and push changes
    git add gitops/overlays/dev/kustomization.yaml
    git commit -m "Drift Demo: Update image tags to ${NEXT_VERSION} (auto-generated)" || echo "No changes to commit"
    git push origin master 2>&1 | grep -v "Username\|Password" || echo "Push completed"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Drift created! ArgoCD will detect out-of-sync state"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting ${DRIFT_INTERVAL} seconds before next drift..."
    echo ""
    
    sleep "$DRIFT_INTERVAL"
done
