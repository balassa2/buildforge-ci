"""BuildForge CI API -- Flask application factory."""

from flask import Flask

from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    from app.routes.health import health_bp  # pylint: disable=import-outside-toplevel
    flask_app.register_blueprint(health_bp)

    return flask_app
