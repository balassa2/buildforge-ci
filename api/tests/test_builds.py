"""Tests for the /api/builds CRUD endpoints."""


class TestTriggerBuild:
    """POST /api/builds"""

    def test_trigger_build_success(self, client, sample_app):
        resp = client.post("/api/builds", json={
            "app_id": sample_app["id"],
            "branch": "main",
            "commit_sha": "abc1234",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["app_id"] == sample_app["id"]
        assert data["branch"] == "main"
        assert data["commit_sha"] == "abc1234"
        assert data["status"] == "pending"
        assert data["app_name"] == "test-app"

    def test_trigger_build_default_branch(self, client, sample_app):
        resp = client.post("/api/builds", json={
            "app_id": sample_app["id"],
        })
        assert resp.status_code == 201
        assert resp.get_json()["branch"] == "main"

    def test_trigger_build_missing_app_id(self, client):
        resp = client.post("/api/builds", json={
            "branch": "main",
        })
        assert resp.status_code == 400
        assert "app_id" in resp.get_json()["error"]

    def test_trigger_build_invalid_app_id(self, client):
        resp = client.post("/api/builds", json={
            "app_id": 999,
        })
        assert resp.status_code == 404

    def test_trigger_build_empty_body(self, client):
        resp = client.post("/api/builds", json={})
        assert resp.status_code == 400


class TestListBuilds:
    """GET /api/builds"""

    def test_list_builds_empty(self, client):
        resp = client.get("/api/builds")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_builds_with_data(self, client, sample_app):
        client.post("/api/builds", json={"app_id": sample_app["id"]})
        client.post("/api/builds", json={"app_id": sample_app["id"], "branch": "dev"})

        resp = client.get("/api/builds")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    def test_list_builds_filter_by_app(self, client, sample_app):
        # Create a second app
        resp2 = client.post("/api/apps", json={
            "name": "other-app",
            "repo_url": "https://github.com/other/repo",
        })
        other_id = resp2.get_json()["id"]

        client.post("/api/builds", json={"app_id": sample_app["id"]})
        client.post("/api/builds", json={"app_id": other_id})

        resp = client.get(f"/api/builds?app_id={sample_app['id']}")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["app_id"] == sample_app["id"]


class TestGetBuild:
    """GET /api/builds/<id>"""

    def test_get_build_success(self, client, sample_app):
        create = client.post("/api/builds", json={"app_id": sample_app["id"]})
        build_id = create.get_json()["id"]

        resp = client.get(f"/api/builds/{build_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == build_id

    def test_get_build_not_found(self, client):
        resp = client.get("/api/builds/999")
        assert resp.status_code == 404


class TestGetBuildLogs:
    """GET /api/builds/<id>/logs"""

    def test_get_logs_no_logs_yet(self, client, sample_app):
        create = client.post("/api/builds", json={"app_id": sample_app["id"]})
        build_id = create.get_json()["id"]

        resp = client.get(f"/api/builds/{build_id}/logs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["build_id"] == build_id
        assert "No logs" in data["logs"]

    def test_get_logs_not_found(self, client):
        resp = client.get("/api/builds/999/logs")
        assert resp.status_code == 404


class TestDeleteCascade:
    """Deleting an app should also delete its builds."""

    def test_builds_deleted_with_app(self, client, sample_app):
        client.post("/api/builds", json={"app_id": sample_app["id"]})
        client.post("/api/builds", json={"app_id": sample_app["id"]})

        # Verify builds exist
        builds = client.get(f"/api/builds?app_id={sample_app['id']}")
        assert len(builds.get_json()) == 2

        # Delete the app
        client.delete(f"/api/apps/{sample_app['id']}")

        # Builds should be gone
        all_builds = client.get("/api/builds")
        assert len(all_builds.get_json()) == 0
