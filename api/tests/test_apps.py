"""Tests for the /api/apps CRUD endpoints."""


class TestCreateApp:
    """POST /api/apps"""

    def test_create_app_success(self, client):
        resp = client.post("/api/apps", json={
            "name": "my-app",
            "repo_url": "https://github.com/org/repo",
            "language": "python",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "my-app"
        assert data["repo_url"] == "https://github.com/org/repo"
        assert data["language"] == "python"
        assert "id" in data
        assert "created_at" in data

    def test_create_app_default_language(self, client):
        resp = client.post("/api/apps", json={
            "name": "no-lang",
            "repo_url": "https://github.com/org/repo",
        })
        assert resp.status_code == 201
        assert resp.get_json()["language"] == "python"

    def test_create_app_missing_name(self, client):
        resp = client.post("/api/apps", json={
            "repo_url": "https://github.com/org/repo",
        })
        assert resp.status_code == 400
        assert "name" in resp.get_json()["error"]

    def test_create_app_missing_repo_url(self, client):
        resp = client.post("/api/apps", json={
            "name": "my-app",
        })
        assert resp.status_code == 400

    def test_create_app_empty_body(self, client):
        resp = client.post("/api/apps", json={})
        assert resp.status_code == 400

    def test_create_app_duplicate_name(self, client, sample_app):
        resp = client.post("/api/apps", json={
            "name": "test-app",
            "repo_url": "https://github.com/other/repo",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.get_json()["error"]


class TestListApps:
    """GET /api/apps"""

    def test_list_apps_empty(self, client):
        resp = client.get("/api/apps")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_apps_with_data(self, client, sample_app):
        resp = client.get("/api/apps")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "test-app"


class TestGetApp:
    """GET /api/apps/<id>"""

    def test_get_app_success(self, client, sample_app):
        app_id = sample_app["id"]
        resp = client.get(f"/api/apps/{app_id}")
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "test-app"

    def test_get_app_not_found(self, client):
        resp = client.get("/api/apps/999")
        assert resp.status_code == 404


class TestDeleteApp:
    """DELETE /api/apps/<id>"""

    def test_delete_app_success(self, client, sample_app):
        app_id = sample_app["id"]
        resp = client.delete(f"/api/apps/{app_id}")
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"]

        # Verify it's gone
        resp = client.get(f"/api/apps/{app_id}")
        assert resp.status_code == 404

    def test_delete_app_not_found(self, client):
        resp = client.delete("/api/apps/999")
        assert resp.status_code == 404
