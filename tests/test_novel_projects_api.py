from fastapi.testclient import TestClient

from llm_studio.config import Config


def _client(tmp_path, monkeypatch):
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
auth:
  enabled: false
api:
  allowed_origins: []
features:
  novel_studio:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
novels:
  db_path: ./data/novels/novels.sqlite
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    return TestClient(get_app(Config(cfg_path)))


def test_project_crud_and_soft_delete(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    created = client.post(
        "/v1/novels/projects",
        json={"title": "长夜行", "genre": "fantasy", "description": "stage1"},
    )
    assert created.status_code == 200
    project = created.json()
    assert project["title"] == "长夜行"
    assert project["slug"]

    listed = client.get("/v1/novels/projects")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [project["id"]]

    got = client.get(f"/v1/novels/projects/{project['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == project["id"]

    patched = client.patch(
        f"/v1/novels/projects/{project['id']}",
        json={"target_style": "冷峻克制", "metadata": {"seed": "stage1"}},
    )
    assert patched.status_code == 200
    assert patched.json()["target_style"] == "冷峻克制"
    assert patched.json()["metadata"]["seed"] == "stage1"

    deleted = client.delete(f"/v1/novels/projects/{project['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    assert client.get("/v1/novels/projects").json()["data"] == []


def test_duplicate_project_slug_returns_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    body = {"title": "Project A", "slug": "project-a"}

    assert client.post("/v1/novels/projects", json=body).status_code == 200
    duplicate = client.post("/v1/novels/projects", json=body)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "NOVEL_DUPLICATE_SLUG"
