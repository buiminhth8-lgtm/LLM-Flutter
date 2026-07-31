from __future__ import annotations

from fastapi.testclient import TestClient

from llm_studio.capabilities import CapabilityStatus, get_capabilities_for_config
from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, versioning: bool = True, recipe: bool = True) -> TestClient:
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
    enabled: true
  dataset_versioning:
    enabled: {str(versioning).lower()}
  training_recipe_recommender:
    enabled: {str(recipe).lower()}
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


def test_dataset_stage7_feature_flags(monkeypatch, tmp_path):
    disabled = _client(tmp_path, monkeypatch, versioning=False)
    response = disabled.get("/v1/datasets/versions/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_FEATURE_DISABLED"

    config = Config(tmp_path / "config.yaml")
    config._data["features"]["dataset_versioning"]["enabled"] = True
    config._data["features"]["training_recipe_recommender"]["enabled"] = True
    caps = {item.name: item for item in get_capabilities_for_config(config)}
    assert caps["dataset_versioning"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_freeze"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_manifest"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_train_val_split"].status == CapabilityStatus.AVAILABLE
    assert caps["training_recipe_recommender"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_center"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["finetune_runs"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["adapter_training"].status == CapabilityStatus.NOT_IMPLEMENTED
