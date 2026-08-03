from __future__ import annotations

from fastapi.testclient import TestClient

from llm_studio.api_server import get_app
from llm_studio.capabilities.registry import get_capabilities_for_config
from llm_studio.capabilities.status import CapabilityStatus
from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, enabled: bool):
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
  finetune_center:
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


def test_finetune_feature_flag_and_capabilities(monkeypatch, tmp_path):
    disabled = _client(tmp_path, monkeypatch, enabled=False)
    response = disabled.get("/v1/finetune/runs")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FINETUNE_FEATURE_DISABLED"

    config = Config(tmp_path / "config.yaml")
    config._data["features"]["finetune_center"]["enabled"] = True
    caps = {item.name: item for item in get_capabilities_for_config(config)}
    assert caps["finetune_center"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_preflight"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_runs"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_metrics"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_checkpoints"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_training"].status == CapabilityStatus.PARTIAL
    assert caps["adapter_registration_after_training"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_evaluation"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_evaluation"].status == CapabilityStatus.NOT_IMPLEMENTED
