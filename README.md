# BuildForge CI

A CI/CD Pipeline Management Platform built with Jenkins, Kubernetes, Python, and Groovy. Designed to demonstrate production-grade infrastructure for application build, test, and deployment workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  buildforge.local (nginx-ingress)                                       │
│  /api/* ──► Flask API    /jenkins/* ──► Jenkins    /grafana/* ──► Grafana│
└────────┬──────────────────────┬──────────────────────────┬──────────────┘
         │                      │                          │
┌────────▼──────────┐  ┌───────▼──────────┐  ┌────────────▼──────────────┐
│ buildforge        │  │ buildforge-ci    │  │ buildforge-monitoring     │
│                   │  │                  │  │                           │
│  Flask API        │  │  Jenkins         │  │  Prometheus ──► Grafana   │
│  (REST + SQLite)  │  │  (JCasC)         │  │                           │
│                   │  │  Dynamic Agents  │  │  Fluent Bit ──► Splunk    │
│  Local Registry   │  │  (Kaniko)        │  │  (DaemonSet)   (HEC)     │
└───────────────────┘  └──────────────────┘  └───────────────────────────┘
```

Three Kubernetes namespaces with clear responsibilities:

- **buildforge** -- Flask REST API and local Docker registry
- **buildforge-ci** -- Jenkins controller with dynamic Kubernetes agents
- **buildforge-monitoring** -- Prometheus, Grafana, Fluent Bit, Splunk

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| CI/CD | Jenkins, Groovy, JCasC | Pipeline orchestration, shared library, config-as-code |
| API | Python, Flask, SQLAlchemy, Gunicorn | REST microservice for app/build management |
| CLI | Python, Click, Rich | Command-line tool for interacting with the API |
| Infrastructure | Kubernetes, Docker, Kind | Container orchestration (local dev with Kind) |
| Image Builds | Kaniko | Daemonless container builds inside Kubernetes |
| Metrics | Prometheus, Grafana | Scraping, dashboards, alerting |
| Logging | Splunk, Fluent Bit | Log aggregation (HEC for events, DaemonSet for stdout) |
| Networking | nginx-ingress | Path-based routing under a single hostname |
| Code Quality | Pylint | Static analysis integrated into pipelines |
| Source Control | Git, GitHub | Version control and shared library hosting |

## Project Structure

```
buildforge-ci/
├── api/                          # Flask REST API
│   ├── app/
│   │   ├── __init__.py           #   Application factory
│   │   ├── config.py             #   Configuration (env vars)
│   │   ├── models.py             #   SQLAlchemy models (App, Build)
│   │   └── routes/
│   │       ├── health.py         #   GET /healthz
│   │       ├── apps.py           #   CRUD /api/apps
│   │       └── builds.py         #   CRUD /api/builds
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .pylintrc
│
├── cli/                          # Click-based CLI tool
│   ├── buildforge_cli/
│   │   ├── main.py               #   Entry point and command groups
│   │   └── commands/
│   │       ├── apps.py           #   buildforge app {create,list,delete}
│   │       └── builds.py         #   buildforge build {trigger,status,logs,list}
│   ├── setup.py                  #   pip install -e .
│   └── requirements.txt
│
├── jenkins/                      # Jenkins configuration
│   ├── config/
│   │   └── jenkins-casc.yaml     #   Configuration as Code (JCasC)
│   ├── pipelines/
│   │   └── Jenkinsfile.app       #   Example pipeline using shared library
│   └── shared-library/
│       ├── vars/
│       │   ├── buildforgePipeline.groovy   # Main pipeline orchestrator
│       │   ├── runLinting.groovy            # Pylint stage
│       │   ├── runTests.groovy              # Pytest stage
│       │   ├── buildImage.groovy            # Kaniko image build
│       │   ├── deployToK8s.groovy           # kubectl rolling update
│       │   └── sendToSplunk.groovy          # Structured HEC events
│       └── src/com/buildforge/
│           └── PipelineConfig.groovy        # Shared config class
│
├── k8s/                          # Kubernetes manifests
│   ├── namespaces.yaml           #   3 namespaces
│   ├── buildforge/               #   API + local registry
│   ├── buildforge-ci/            #   Jenkins (RBAC, JCasC, deployment)
│   ├── buildforge-monitoring/    #   Prometheus, Grafana, Fluent Bit, Splunk
│   └── ingress/                  #   nginx-ingress rules
│
├── scripts/                      # Automation
│   ├── bootstrap.sh              #   Create Kind cluster + install ingress
│   ├── deploy.sh                 #   Build images + apply all manifests
│   └── seed-data.sh              #   Populate sample apps and builds
│
├── docker-compose.yml            # Local dev (no K8s needed)
├── docker-compose/               # Compose-specific configs
├── kind-config.yaml              # Kind cluster with port mappings
└── .gitignore
```

## Quick Start

### Option A: Kubernetes (Kind)

Requires: Docker, [Kind](https://kind.sigs.k8s.io/), kubectl

```bash
# 1. Create cluster, install ingress, create namespaces
./scripts/bootstrap.sh

# 2. Build images, deploy all services
./scripts/deploy.sh

# 3. Seed sample data
./scripts/seed-data.sh
```

Add the hostname to `/etc/hosts`:

```bash
echo '127.0.0.1 buildforge.local' | sudo tee -a /etc/hosts
```

Then access:

| Service | URL |
|---------|-----|
| API | http://buildforge.local/api/apps |
| Health | http://buildforge.local/healthz |
| Jenkins | http://buildforge.local/jenkins/ |
| Grafana | http://buildforge.local/grafana/ |

If the Kind cluster was created without port mappings, use port-forward as a fallback:

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
# Then access via localhost:8080 with -H "Host: buildforge.local"
```

### Option B: Docker Compose

Requires: Docker

```bash
docker compose up -d
```

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:5050 | -- |
| Jenkins | http://localhost:8080 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | -- |
| Registry | http://localhost:5001 | -- |

```bash
docker compose down      # stop
docker compose down -v   # stop and remove volumes
```

### CLI Tool

```bash
cd cli
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# Point to the API
export BUILDFORGE_API_URL=http://localhost:5050  # compose
# or
export BUILDFORGE_API_URL=http://buildforge.local  # k8s with /etc/hosts

buildforge app list
buildforge app create --name my-app --repo https://github.com/org/repo --language python
buildforge build trigger --app-id 1
buildforge build status --build-id 1
buildforge build logs --build-id 1
```

## Components

### Flask REST API

A Python microservice that manages applications and builds. Provides CRUD endpoints for registering apps, triggering builds, and querying build status/logs.

**Key endpoints:**

- `GET /healthz` -- Kubernetes liveness/readiness probe
- `POST /api/apps` -- Register a new application
- `GET /api/apps` -- List all applications
- `POST /api/builds` -- Trigger a build
- `GET /api/builds?app_id=1` -- List builds (with optional filter)
- `GET /api/builds/<id>/logs` -- Retrieve build logs

### Jenkins Shared Library

An opinionated Groovy shared library that standardizes CI/CD pipelines. Application teams consume it with minimal configuration (~10 lines in a Jenkinsfile):

```groovy
@Library('buildforge-shared-library') _

buildforgePipeline {
    appName    = 'my-service'
    repoUrl    = 'https://github.com/org/my-service.git'
    language   = 'python'
}
```

**Pipeline stages:** Checkout, Lint (Pylint), Test (Pytest), Build Image (Kaniko), Deploy (kubectl), Post (Splunk HEC).

### Monitoring

**Metrics (Prometheus + Grafana):**
- Prometheus scrapes the Flask API, Jenkins, and itself on 15s intervals
- Two pre-built Grafana dashboards:
  - **Pipeline Health** -- build success/failure rates, duration percentiles, queue length
  - **Build Metrics & Infrastructure** -- API request rate/latency, pod CPU/memory

**Logging (Fluent Bit + Splunk):**
- Fluent Bit runs as a DaemonSet, tailing container stdout logs and forwarding to Splunk via HEC
- `sendToSplunk.groovy` sends structured build events directly to Splunk HEC for richer querying
- Pre-built saved searches for failed builds, slow builds, and build volume

### Ingress

nginx-ingress provides path-based routing so all services are accessible through a single hostname (`buildforge.local`). Each namespace has its own Ingress resource since K8s Ingress objects must reference services in the same namespace.

## Apple Silicon Notes

- **Kind** runs natively on ARM64 -- no issues
- **Splunk** (`splunk/splunk`) is x86_64-only and will not run on Apple Silicon Kind clusters. The manifests are complete and valid for x86_64 environments. On ARM64, Splunk is skipped during deployment
- **Port 5000** is used by macOS AirPlay Receiver. Docker Compose maps the API to port 5050 instead. Disable AirPlay Receiver in System Settings if you need port 5000
- All other images (Jenkins, Prometheus, Grafana, Fluent Bit, registry, nginx-ingress) have ARM64 variants and work natively

## Namespace Layout

| Namespace | Components | Purpose |
|-----------|-----------|---------|
| `buildforge` | Flask API, local registry | Application services |
| `buildforge-ci` | Jenkins controller, dynamic agents | CI/CD orchestration |
| `buildforge-monitoring` | Prometheus, Grafana, Fluent Bit, Splunk | Observability |
| `ingress-nginx` | nginx-ingress controller | Traffic routing |
