"""Routes for triggering and querying CI builds."""

from flask import Blueprint, jsonify, request

from app.models import App, Build, db

builds_bp = Blueprint("builds", __name__, url_prefix="/api/builds")


@builds_bp.route("", methods=["POST"])
def trigger_build():
    """Trigger a new build for an application.

    Expects JSON: {"app_id": 1, "branch": "main", "commit_sha": "abc123"}
    In a later step, this will also call Jenkins to start the actual pipeline.
    """
    data = request.get_json()
    if not data or not data.get("app_id"):
        return jsonify({"error": "app_id is required"}), 400

    app = db.session.get(App, data["app_id"])
    if not app:
        return jsonify({"error": "App not found"}), 404

    build = Build(
        app_id=app.id,
        branch=data.get("branch", "main"),
        commit_sha=data.get("commit_sha"),
        status="pending",
    )
    db.session.add(build)
    db.session.commit()
    return jsonify(build.to_dict()), 201


@builds_bp.route("", methods=["GET"])
def list_builds():
    """List builds, optionally filtered by app_id."""
    app_id = request.args.get("app_id", type=int)
    query = Build.query.order_by(Build.started_at.desc())
    if app_id:
        query = query.filter_by(app_id=app_id)
    builds = query.all()
    return jsonify([b.to_dict() for b in builds])


@builds_bp.route("/<int:build_id>", methods=["GET"])
def get_build(build_id):
    """Get a single build by ID."""
    build = db.session.get(Build, build_id)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify(build.to_dict())


@builds_bp.route("/<int:build_id>/logs", methods=["GET"])
def get_build_logs(build_id):
    """Get the logs for a build."""
    build = db.session.get(Build, build_id)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify({"build_id": build.id, "logs": build.logs or "No logs available yet."})
