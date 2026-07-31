from fastapi.testclient import TestClient

from llm_studio.auth.permissions import required_permission_for_request
from llm_studio.auth.roles import Permission
from llm_studio.capabilities import get_capabilities_for_config
from llm_studio.config import Config


def test_context_api_is_disabled_with_novel_feature(monkeypatch, tmp_path):
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
    enabled: false
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    client = TestClient(get_app(Config(cfg_path)))

    response = client.post(
        "/v1/context/assemble",
        json={"project_id": "missing"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONTEXT_FEATURE_DISABLED"
    caps = {
        item["name"]: item
        for item in client.get("/v1/capabilities").json()["capabilities"]
    }
    assert caps["context_assembler"]["status"] == "not_implemented"


def test_context_capabilities_are_available_when_novel_feature_is_enabled():
    caps = {
        item.name: item
        for item in get_capabilities_for_config(
            {"features": {"novel_studio": {"enabled": True}}}
        )
    }
    assert caps["context_assembler"].status.value == "available"
    assert caps["context_budget"].status.value == "available"
    assert caps["context_render_preview"].frontend_exposed is True
    assert caps["writing_workspace"].status.value == "available"
    assert caps["revision_system"].status.value == "not_implemented"


def test_context_routes_reuse_read_only_context_permission():
    assert (
        required_permission_for_request("POST", "/v1/context/assemble")
        == Permission.VIEW_CONTEXT
    )
    assert (
        required_permission_for_request("POST", "/v1/context/render-preview")
        == Permission.VIEW_CONTEXT
    )
    assert (
        required_permission_for_request("GET", "/v1/context/records")
        == Permission.VIEW_CONTEXT
    )
