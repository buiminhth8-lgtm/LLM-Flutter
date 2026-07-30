from fastapi.testclient import TestClient

from llm_studio.config import Config


def _write_config(path, *, enabled: bool):
    path.write_text(
        f"""
auth:
  enabled: false
api:
  allowed_origins: []
features:
  novel_studio:
    enabled: {str(enabled).lower()}
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
novels:
  db_path: ./data/novels/novels.sqlite
""",
        encoding="utf-8",
    )


def _client(tmp_path, monkeypatch, *, enabled: bool):
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, enabled=enabled)
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    return TestClient(get_app(Config(cfg_path)))


def test_novel_api_disabled_by_default(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch, enabled=False)

    response = client.get("/v1/novels/projects")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOVEL_FEATURE_DISABLED"


def test_novel_capabilities_are_stage1_when_enabled(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch, enabled=True)

    response = client.get("/v1/capabilities")
    caps = {item["name"]: item for item in response.json()["capabilities"]}

    assert caps["novel_studio"]["status"] == "partial"
    assert caps["novel_projects"]["status"] == "available"
    assert caps["novel_world_bible"]["status"] == "available"
    assert caps["novel_characters"]["status"] == "available"
    assert caps["novel_chapters"]["status"] == "available"
    assert caps["prompt_studio"]["status"] == "available"
    assert caps["writing_workspace"]["status"] == "not_implemented"
