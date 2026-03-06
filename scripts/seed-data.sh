#!/usr/bin/env bash
# seed-data.sh -- Populate the API with sample apps and builds for demo.
#
# Usage:  ./scripts/seed-data.sh
#
# Prerequisites: API must be reachable (run deploy.sh first).
#
# What it does:
#   1. Waits for the API to respond
#   2. Creates sample applications
#   3. Triggers sample builds for each app

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
# Try ingress first, fall back to port-forward.
# When accessing via localhost (port-forward), the Host header is needed
# so nginx-ingress routes to the right backend.
API_URL="${BUILDFORGE_API_URL:-http://buildforge.local}"
CURL_EXTRA=()

if [[ "$API_URL" == *"localhost"* || "$API_URL" == *"127.0.0.1"* ]]; then
    CURL_EXTRA=(-H "Host: buildforge.local")
fi

# ── Colors ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*" >&2; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*" >&2; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 1. Wait for API ──────────────────────────────────────────────────
info "Checking API at $API_URL/healthz ..."

MAX_RETRIES=15
RETRY=0
until curl -sf "$API_URL/healthz" &>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
        echo ""
        warn "Could not reach $API_URL/healthz after $MAX_RETRIES attempts."
        warn "Trying port-forward fallback..."

        # Start a background port-forward if ingress isn't reachable
        kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 &>/dev/null &
        PF_PID=$!
        sleep 3

        API_URL="http://localhost:8080"
        if ! curl -sf -H "Host: buildforge.local" "$API_URL/healthz" &>/dev/null; then
            kill "$PF_PID" 2>/dev/null || true
            error "API is not reachable. Make sure deploy.sh has been run."
        fi

        info "Using port-forward fallback on localhost:8080"
        # When using port-forward, we need the Host header
        CURL_EXTRA=(-H "Host: buildforge.local")
        trap 'kill $PF_PID 2>/dev/null || true' EXIT
        break
    fi
    echo -n "."
    sleep 2
done

info "API is healthy!"
echo "" >&2

# ── Helper: POST to API ──────────────────────────────────────────────
api_post() {
    local path="$1" data="$2"
    if [ ${#CURL_EXTRA[@]} -gt 0 ]; then
        curl -sf -X POST \
            -H "Content-Type: application/json" \
            "${CURL_EXTRA[@]}" \
            -d "$data" \
            "$API_URL$path" 2>/dev/null
    else
        curl -sf -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$path" 2>/dev/null
    fi
}

api_get() {
    local path="$1"
    if [ ${#CURL_EXTRA[@]} -gt 0 ]; then
        curl -sf "${CURL_EXTRA[@]}" "$API_URL$path" 2>/dev/null
    else
        curl -sf "$API_URL$path" 2>/dev/null
    fi
}

# ── 2. Create sample applications ────────────────────────────────────
echo -e "${CYAN}── Creating sample applications ──${NC}" >&2

create_app() {
    local name="$1" repo="$2" lang="$3"
    local result
    result=$(api_post "/api/apps" "{\"name\":\"$name\",\"repo_url\":\"$repo\",\"language\":\"$lang\"}")

    if [ -n "$result" ]; then
        local app_id
        app_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "?")
        info "Created app '$name' (id: $app_id)"
        echo "$app_id"
    else
        warn "App '$name' may already exist -- skipping."
        echo ""
    fi
}

APP1_ID=$(create_app "buildforge-api"    "https://github.com/balassa2/buildforge-ci" "python")
APP2_ID=$(create_app "payment-service"   "https://github.com/example/payment-svc"    "python")
APP3_ID=$(create_app "notification-worker" "https://github.com/example/notif-worker"  "python")

echo "" >&2

# ── 3. Trigger sample builds ─────────────────────────────────────────
echo -e "${CYAN}── Triggering sample builds ──${NC}" >&2

trigger_build() {
    local app_id="$1" branch="${2:-main}" commit="${3:-abc1234}"
    if [ -z "$app_id" ]; then
        return
    fi
    local result
    result=$(api_post "/api/builds" "{\"app_id\":$app_id,\"branch\":\"$branch\",\"commit_sha\":\"$commit\"}")

    if [ -n "$result" ]; then
        local build_id
        build_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "?")
        info "Triggered build #$build_id for app_id=$app_id (branch: $branch)"
    else
        warn "Failed to trigger build for app_id=$app_id"
    fi
}

# Two builds for the main app, one each for the others
if [ -n "$APP1_ID" ]; then
    trigger_build "$APP1_ID" "main"    "a1b2c3d"
    trigger_build "$APP1_ID" "feature/auth" "e4f5g6h"
fi
if [ -n "$APP2_ID" ]; then
    trigger_build "$APP2_ID" "main"    "i7j8k9l"
fi
if [ -n "$APP3_ID" ]; then
    trigger_build "$APP3_ID" "develop" "m0n1o2p"
fi

echo "" >&2

# ── 4. Summary ────────────────────────────────────────────────────────
echo -e "${CYAN}── Seed data summary ──${NC}" >&2
echo "" >&2

info "Apps:"
api_get "/api/apps" | python3 -m json.tool >&2 2>/dev/null || warn "Could not fetch apps"

echo "" >&2
info "Builds:"
api_get "/api/builds" | python3 -m json.tool >&2 2>/dev/null || warn "Could not fetch builds"

echo "" >&2
info "Seed data loaded! You can now explore:"
echo "    API apps:    curl $API_URL/api/apps" >&2
echo "    API builds:  curl $API_URL/api/builds" >&2
echo "    CLI:         buildforge app list" >&2
echo "" >&2
