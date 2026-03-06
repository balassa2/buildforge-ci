"""Application configuration."""

import os


class Config:
    """Base configuration loaded from environment variables with safe defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JENKINS_URL = os.environ.get("JENKINS_URL", "http://jenkins.buildforge-ci:8080")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # SQLite for dev, swap to PostgreSQL via env var in production
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///buildforge.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
