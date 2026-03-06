"""Health check endpoint for Kubernetes liveness/readiness probes."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
def healthz():
    """Return basic health status.

    Kubernetes uses this for liveness and readiness probes to decide
    whether to restart or route traffic to this pod.
    """
    return jsonify({"status": "healthy"}), 200
