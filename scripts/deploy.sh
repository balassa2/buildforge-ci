#!/usr/bin/env bash
# deploy.sh -- Build images, load into kind, and apply all K8s manifests.
#
# Usage:  ./scripts/deploy.sh
#
# Prerequisites: Run ./scripts/bootstrap.sh first.
#
# What it does:
#   1. Builds the Flask API Docker image
#   2. Loads the image into the kind cluster
#   3. Applies K8s manifests in dependency order
#   4. Waits for deployments to roll out
#   5. Prints a status summary

set -euo pipefail

CLUSTER_NAME="buildforge"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()  { echo -e "\n${CYAN}── $* ──${NC}"; }

# Verify cluster is running
if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    error "Kind cluster '$CLUSTER_NAME' not found. Run ./scripts/bootstrap.sh first."
fi

# ── 1. Build Docker images ───────────────────────────────────────────
step "Building Docker images"

info "Building buildforge-api:dev ..."
docker build -t buildforge-api:dev "$PROJECT_ROOT/api"

# ── 2. Load images into kind ─────────────────────────────────────────
step "Loading images into kind cluster"

info "Loading buildforge-api:dev ..."
kind load docker-image buildforge-api:dev --name "$CLUSTER_NAME"

# ── 3. Apply K8s manifests ───────────────────────────────────────────
step "Applying Kubernetes manifests"

# Namespaces first (idempotent, also applied by bootstrap.sh)
info "Namespaces..."
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"

# buildforge namespace: local registry + API
info "Local registry..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge/local-registry/"

info "BuildForge API..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge/api/"

# buildforge-ci namespace: Jenkins RBAC + config + deployment + services
info "Jenkins RBAC..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-ci/jenkins/rbac.yaml"

info "Jenkins config + deployment + service..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-ci/jenkins/"

# buildforge-monitoring namespace: Prometheus, Grafana, Fluent Bit, Splunk
info "Prometheus..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/prometheus/"

info "Grafana..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/grafana/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/grafana/dashboards-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/grafana/deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/grafana/service.yaml"

info "Fluent Bit..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/fluent-bit/"

# Splunk -- may fail on Apple Silicon (x86_64-only image)
info "Splunk (may not run on Apple Silicon)..."
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/splunk/pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/splunk/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/splunk/service.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/buildforge-monitoring/splunk/deployment.yaml" || \
    warn "Splunk deployment may not work on Apple Silicon (x86_64-only image)."

# Ingress rules
info "Ingress rules..."
kubectl apply -f "$PROJECT_ROOT/k8s/ingress/ingress-rules.yaml"

# ── 4. Wait for deployments ──────────────────────────────────────────
step "Waiting for deployments to become ready"

wait_deploy() {
    local ns="$1" name="$2" timeout="${3:-120s}"
    info "Waiting for $ns/$name (timeout: $timeout)..."
    if ! kubectl rollout status deployment/"$name" -n "$ns" --timeout="$timeout" 2>/dev/null; then
        warn "$ns/$name did not become ready within $timeout -- check with: kubectl describe deployment/$name -n $ns"
    fi
}

wait_deploy buildforge        buildforge-api      90s
wait_deploy buildforge        local-registry      60s
wait_deploy buildforge-ci     jenkins             180s
wait_deploy buildforge-monitoring prometheus       60s
wait_deploy buildforge-monitoring grafana          60s
# Splunk may not start on ARM64 -- don't block on it
wait_deploy buildforge-monitoring splunk           30s

# ── 5. Status summary ────────────────────────────────────────────────
step "Deployment status"

echo ""
kubectl get deployments -A -l app.kubernetes.io/part-of=buildforge-ci 2>/dev/null || true
echo ""
kubectl get pods -A -l app.kubernetes.io/part-of=buildforge-ci 2>/dev/null || true
echo ""

# Also show pods without the label (Jenkins, Splunk, etc.)
info "All pods across buildforge namespaces:"
echo ""
for ns in buildforge buildforge-ci buildforge-monitoring; do
    echo "  ── $ns ──"
    kubectl get pods -n "$ns" --no-headers 2>/dev/null | sed 's/^/    /'
    echo ""
done

info "Deploy complete!"
echo ""
echo "  Access services via ingress (if /etc/hosts is configured):"
echo "    API:      http://buildforge.local/api/apps"
echo "    Healthz:  http://buildforge.local/healthz"
echo "    Jenkins:  http://buildforge.local/jenkins/"
echo "    Grafana:  http://buildforge.local/grafana/"
echo "    Splunk:   http://buildforge.local/splunk/"
echo ""
echo "  Or use port-forward as fallback:"
echo "    kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80"
echo "    Then visit http://localhost:8080/api/apps (with -H 'Host: buildforge.local')"
echo ""
echo "  Next step:  ./scripts/seed-data.sh"
echo ""
