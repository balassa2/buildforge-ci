"""CRUD routes for registered applications."""

from flask import Blueprint, jsonify, request

from app.models import App, db

apps_bp = Blueprint("apps", __name__, url_prefix="/api/apps")


@apps_bp.route("", methods=["POST"])
def create_app():
    """Register a new application.

    Expects JSON: {"name": "myapp", "repo_url": "https://...", "language": "python"}
    """
    data = request.get_json()
    if not data or not data.get("name") or not data.get("repo_url"):
        return jsonify({"error": "name and repo_url are required"}), 400

    if App.query.filter_by(name=data["name"]).first():
        return jsonify({"error": f"App '{data['name']}' already exists"}), 409

    app = App(
        name=data["name"],
        repo_url=data["repo_url"],
        language=data.get("language", "python"),
    )
    db.session.add(app)
    db.session.commit()
    return jsonify(app.to_dict()), 201


@apps_bp.route("", methods=["GET"])
def list_apps():
    """List all registered applications."""
    apps = App.query.order_by(App.created_at.desc()).all()
    return jsonify([a.to_dict() for a in apps])


@apps_bp.route("/<int:app_id>", methods=["GET"])
def get_app(app_id):
    """Get a single application by ID."""
    app = db.session.get(App, app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404
    return jsonify(app.to_dict())


@apps_bp.route("/<int:app_id>", methods=["DELETE"])
def delete_app(app_id):
    """Delete an application and all its builds."""
    app = db.session.get(App, app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404
    db.session.delete(app)
    db.session.commit()
    return jsonify({"message": f"App '{app.name}' deleted"}), 200
