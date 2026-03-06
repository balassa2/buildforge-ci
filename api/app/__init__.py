"""BuildForge CI API -- Flask application factory."""

from flask import Flask

from app.config import Config
from app.models import db


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)

    from app.routes.health import health_bp  # pylint: disable=import-outside-toplevel
    from app.routes.apps import apps_bp  # pylint: disable=import-outside-toplevel
    from app.routes.builds import builds_bp  # pylint: disable=import-outside-toplevel
    from app.metrics import metrics_bp, start_timer, record_metrics  # pylint: disable=import-outside-toplevel

    flask_app.register_blueprint(health_bp)
    flask_app.register_blueprint(apps_bp)
    flask_app.register_blueprint(builds_bp)
    flask_app.register_blueprint(metrics_bp)

    flask_app.before_request(start_timer)
    flask_app.after_request(record_metrics)

    # Create tables on first request in dev; migrations handle this in prod
    with flask_app.app_context():
        db.create_all()

    return flask_app
