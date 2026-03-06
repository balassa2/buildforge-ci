#!/usr/bin/env bash
# bootstrap.sh -- Create the kind cluster and install foundational infra.
#
# Usage:  ./scripts/bootstrap.sh
#
# What it does:
#   1. Checks that required tools are installed (docker, kind, kubectl)
#   2. Creates a kind cluster named "buildforge" with ingress port mappings
#   3. Installs the nginx-ingress controller
#   4. Creates the three project namespaces
#
# Safe to re-run: it will skip cluster creation if the cluster exists.

set -euo pipefail

CLUSTER_NAME="buildforge"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KIND_CONFIG="$PROJECT_ROOT/kind-config.yaml"
INGRESS_MANIFEST="https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"

# ── Colors for output ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 1. Check prerequisites ───────────────────────────────────────────
info "Checking prerequisites..."

for cmd in docker kind kubectl; do
    if ! command -v "$cmd" &>/dev/null; then
        error "'$cmd' is not installed. Please install it first."
    fi
done

if ! docker info &>/dev/null; then
    error "Docker daemon is not running. Please start Docker Desktop."
fi

info "All prerequisites satisfied."

# ── 2. Create kind cluster ───────────────────────────────────────────
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    warn "Kind cluster '$CLUSTER_NAME' already exists -- skipping creation."
    warn "To recreate: kind delete cluster --name $CLUSTER_NAME && re-run this script."
else
    info "Creating kind cluster '$CLUSTER_NAME' with ingress port mappings..."
    kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
    info "Cluster created."
fi

# Make sure kubectl is pointing at the right cluster
kubectl cluster-info --context "kind-${CLUSTER_NAME}" &>/dev/null \
    || error "Cannot reach cluster 'kind-${CLUSTER_NAME}'."

info "kubectl context set to kind-${CLUSTER_NAME}."

# ── 3. Install nginx-ingress controller ──────────────────────────────
if kubectl get namespace ingress-nginx &>/dev/null; then
    warn "ingress-nginx namespace exists -- skipping controller install."
else
    info "Installing nginx-ingress controller (kind variant)..."
    kubectl apply -f "$INGRESS_MANIFEST"

    info "Waiting for ingress controller pod to be ready (up to 120s)..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s
    info "Ingress controller is ready."
fi

# ── 4. Create namespaces ─────────────────────────────────────────────
info "Applying namespaces..."
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"

# ── Done ──────────────────────────────────────────────────────────────
echo ""
info "Bootstrap complete!"
echo ""
echo "  Cluster:    $CLUSTER_NAME"
echo "  Namespaces: buildforge, buildforge-ci, buildforge-monitoring"
echo "  Ingress:    nginx-ingress on localhost:80 / localhost:443"
echo ""
echo "  Next step:  ./scripts/deploy.sh"
echo ""

# Hint about /etc/hosts
if ! grep -q "buildforge.local" /etc/hosts 2>/dev/null; then
    warn "Add this to /etc/hosts for hostname access:"
    echo "    echo '127.0.0.1 buildforge.local' | sudo tee -a /etc/hosts"
    echo ""
fi
