"""SQLAlchemy models for applications and builds."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class App(db.Model):
    """A registered application that can be built through the CI pipeline."""

    __tablename__ = "apps"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    repo_url = db.Column(db.String(512), nullable=False)
    language = db.Column(db.String(64), default="python")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    builds = db.relationship("Build", backref="app", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize to JSON-friendly dict."""
        return {
            "id": self.id,
            "name": self.name,
            "repo_url": self.repo_url,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
        }


class Build(db.Model):
    """A single CI build triggered for an application."""

    __tablename__ = "builds"

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey("apps.id"), nullable=False)
    branch = db.Column(db.String(128), default="main")
    status = db.Column(db.String(32), default="pending")
    commit_sha = db.Column(db.String(40), nullable=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = db.Column(db.DateTime, nullable=True)
    logs = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """Serialize to JSON-friendly dict."""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "app_name": self.app.name if self.app else None,
            "branch": self.branch,
            "status": self.status,
            "commit_sha": self.commit_sha,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
