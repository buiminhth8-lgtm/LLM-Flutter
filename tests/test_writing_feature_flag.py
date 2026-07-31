from fastapi.testclient import TestClient

from llm_studio.auth.permissions import required_permission_for_request
from llm_studio.auth.roles import Permission
from llm_studio.capabilities.registry import get_capabilities_for_config
from llm_studio.config import Config


def test_writing_feature_flag_and_capabilities(monkeypatch, tmp_path):
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
novels:
  db_path: ./data/novels/novels.sqlite
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    config = Config(cfg_path)
    client = TestClient(get_app(config))

    response = client.get("/v1/writing/generations")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WRITING_FEATURE_DISABLED"

    disabled = {
        item.name: item for item in get_capabilities_for_config(config)
    }
    assert disabled["writing_workspace"].status.value == "not_implemented"

    config._data["features"]["novel_studio"]["enabled"] = True
    enabled = {
        item.name: item for item in get_capabilities_for_config(config)
    }
    assert enabled["writing_workspace"].status.value == "available"
    assert enabled["writing_stream"].status.value == "available"
    assert enabled["revision_system"].status.value == "available"
    assert enabled["dataset_builder"].status.value == "available"
    assert enabled["dataset_sft_export"].status.value == "available"
    assert enabled["dataset_versioning"].status.value == "not_implemented"


def test_writing_rbac_permissions():
    assert (
        required_permission_for_request("GET", "/v1/writing/generations")
        == Permission.VIEW_WRITING
    )
    assert (
        required_permission_for_request("POST", "/v1/writing/generate")
        == Permission.MANAGE_WRITING
    )
