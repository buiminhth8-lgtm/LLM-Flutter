from fastapi.testclient import TestClient

from llm_studio.config import Config


def _stage12_client(tmp_path, monkeypatch):
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
  evaluation_center:
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


def test_version_api_reports_stage12_without_secrets(monkeypatch, tmp_path):
    client = _stage12_client(tmp_path, monkeypatch)

    response = client.get("/v1/version")

    assert response.status_code == 200
    body = response.json()
    assert body["app_name"] == "LLM Studio"
    assert body["novel_studio_stage"] == 12
    caps = {item["name"]: item for item in body["capabilities"]}
    assert caps["novel_studio_product_ui"]["status"] == "available"
    assert caps["health_checks"]["status"] == "available"
    assert "api_key" not in str(body).lower()
