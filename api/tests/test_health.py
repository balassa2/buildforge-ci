"""Tests for health check and metrics endpoints."""


def test_healthz_returns_200(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


def test_healthz_json_content_type(client):
    resp = client.get("/healthz")
    assert resp.content_type == "application/json"


def test_metrics_returns_prometheus_format(client):
    # Hit a route first so there's data to report
    client.get("/healthz")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "buildforge_http_requests_total" in body
    assert "buildforge_http_request_duration_seconds" in body


def test_metrics_content_type(client):
    resp = client.get("/metrics")
    assert "text/plain" in resp.content_type or "text/openmetrics" in resp.content_type


def test_unknown_route_returns_404(client):
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
