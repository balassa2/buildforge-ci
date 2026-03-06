"""Prometheus metrics for the BuildForge API.

Exposes request counts and latency histograms. The /metrics endpoint
is registered as a Flask blueprint in the application factory.
"""

import time

from flask import Blueprint, Response, request
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "buildforge_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "buildforge_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=registry,
)

BUILDS_TRIGGERED = Counter(
    "buildforge_builds_triggered_total",
    "Total builds triggered through the API",
    registry=registry,
)

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


def start_timer():
    """Store request start time."""
    request._prom_start = time.monotonic()  # pylint: disable=protected-access


def record_metrics(response):
    """Record request count and latency after each response."""
    latency = time.monotonic() - getattr(request, "_prom_start", time.monotonic())
    endpoint = request.endpoint or "unknown"

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(latency)

    return response
