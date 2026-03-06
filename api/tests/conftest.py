"""Shared pytest fixtures for the BuildForge API tests."""

import pytest

from app import create_app
from app.config import Config
from app.models import db as _db


class TestConfig(Config):
    """Override config for testing: in-memory SQLite, no debug noise."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"


@pytest.fixture()
def app():
    """Create a fresh Flask app with an empty in-memory database for each test."""
    flask_app = create_app(config_class=TestConfig)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client -- sends HTTP requests without a running server."""
    return app.test_client()


@pytest.fixture()
def sample_app(client):
    """Create and return a sample application for tests that need one."""
    resp = client.post("/api/apps", json={
        "name": "test-app",
        "repo_url": "https://github.com/test/repo",
        "language": "python",
    })
    return resp.get_json()
