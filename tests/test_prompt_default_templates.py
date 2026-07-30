from tests.test_novel_projects_api import _client


def test_default_templates_are_idempotent(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    first = client.post("/v1/prompts/defaults/ensure")
    second = client.post("/v1/prompts/defaults/ensure")

    assert first.status_code == 200
    assert len(first.json()["data"]) >= 10
    assert second.status_code == 200
    assert second.json()["data"] == []


def test_copy_global_template_to_project(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "长夜"}).json()
    template = client.post("/v1/prompts/defaults/ensure").json()["data"][0]

    copied = client.post(
        f"/v1/prompts/templates/{template['id']}/copy-to-project",
        json={"project_id": project["id"], "name": "项目模板"},
    )

    assert copied.status_code == 200
    assert copied.json()["scope"] == "project"
    assert copied.json()["project_id"] == project["id"]


def test_copy_to_missing_project_returns_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    template = client.post("/v1/prompts/defaults/ensure").json()["data"][0]

    response = client.post(
        f"/v1/prompts/templates/{template['id']}/copy-to-project",
        json={"project_id": "missing"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROMPT_PROJECT_NOT_FOUND"
