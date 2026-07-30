from fastapi.testclient import TestClient

from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, enabled: bool):
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
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
prompts:
  db_path: ./data/novels/novels.sqlite
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    return TestClient(get_app(Config(cfg_path)))


def test_prompt_api_disabled_with_novel_flag(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch, enabled=False)

    response = client.get("/v1/prompts/templates")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROMPT_FEATURE_DISABLED"


def test_prompt_capabilities_are_stage2_when_enabled(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch, enabled=True)

    caps = {item["name"]: item for item in client.get("/v1/capabilities").json()["capabilities"]}

    assert caps["prompt_studio"]["status"] == "available"
    assert caps["prompt_template_versions"]["status"] == "available"
    assert caps["prompt_render_preview"]["status"] == "available"
    assert caps["context_assembler"]["status"] == "not_implemented"
    assert caps["writing_workspace"]["status"] == "not_implemented"
