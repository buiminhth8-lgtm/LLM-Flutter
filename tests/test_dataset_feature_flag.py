from __future__ import annotations

from fastapi.testclient import TestClient

from llm_studio.auth.permissions import required_permission_for_request
from llm_studio.auth.roles import Permission
from llm_studio.capabilities import CapabilityStatus, get_capabilities_for_config
from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, enabled: bool = True) -> TestClient:
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
    enabled: true
  revision_system:
    enabled: true
  dataset_builder:
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
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))
    return TestClient(get_app(Config(cfg_path)))


def test_dataset_feature_flag_and_capabilities(monkeypatch, tmp_path):
    disabled = _client(tmp_path, monkeypatch, enabled=False)
    response = disabled.get("/v1/datasets")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_FEATURE_DISABLED"

    config = Config(tmp_path / "config.yaml")
    config._data["features"]["dataset_builder"]["enabled"] = True
    caps = {item.name: item for item in get_capabilities_for_config(config)}
    assert caps["dataset_builder"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_sft_export"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_preference_samples"].status == CapabilityStatus.PARTIAL
    assert caps["dataset_versioning"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_freeze"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_manifest"].status == CapabilityStatus.AVAILABLE
    assert caps["training_recipe_recommender"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_center"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_runs"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_training"].status == CapabilityStatus.PARTIAL


def test_dataset_permissions():
    assert (
        required_permission_for_request("GET", "/v1/datasets")
        == Permission.VIEW_DATASETS
    )
    assert (
        required_permission_for_request("POST", "/v1/datasets")
        == Permission.MANAGE_DATASETS
    )
