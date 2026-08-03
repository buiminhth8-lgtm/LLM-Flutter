from fastapi.testclient import TestClient

from llm_studio.auth.permissions import required_permission_for_request
from llm_studio.auth.roles import Permission
from llm_studio.capabilities import CapabilityStatus, get_capabilities_for_config
from llm_studio.config import Config


def test_evaluation_feature_flag_disables_api(monkeypatch, tmp_path):
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
    client = TestClient(get_app(Config(cfg_path)))
    response = client.get("/v1/evaluation/runs")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVALUATION_FEATURE_DISABLED"


def test_evaluation_capabilities_and_permissions_enabled():
    config = {
        "features": {
            "novel_studio": {"enabled": True},
            "evaluation_center": {"enabled": True},
        }
    }
    caps = {cap.name: cap for cap in get_capabilities_for_config(config)}
    assert caps["full_evaluation_center"].status == CapabilityStatus.AVAILABLE
    assert caps["novel_evaluation"].status == CapabilityStatus.AVAILABLE
    assert caps["evaluation_local_model_judge"].status == CapabilityStatus.PARTIAL
    assert caps["windows_packaging"].status == CapabilityStatus.AVAILABLE
    assert required_permission_for_request("GET", "/v1/evaluation/runs") == Permission.VIEW_EVALUATION
    assert required_permission_for_request("POST", "/v1/evaluation/run-sync") == Permission.MANAGE_EVALUATION
