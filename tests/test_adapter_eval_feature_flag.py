from __future__ import annotations

from fastapi.testclient import TestClient

from llm_studio.api_server import get_app
from llm_studio.capabilities.registry import get_capabilities_for_config
from llm_studio.capabilities.status import CapabilityStatus
from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, adapter_eval_enabled: bool):
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
  adapter_evaluation:
    enabled: {str(adapter_eval_enabled).lower()}
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


def test_adapter_eval_feature_flag_and_capabilities(monkeypatch, tmp_path):
    disabled = _client(tmp_path, monkeypatch, adapter_eval_enabled=False)
    response = disabled.get("/v1/adapter-evaluations/sessions")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ADAPTER_EVAL_FEATURE_DISABLED"

    config = Config(tmp_path / "config.yaml")
    config._data["features"]["adapter_evaluation"]["enabled"] = True
    caps = {item.name: item for item in get_capabilities_for_config(config)}
    assert caps["adapter_evaluation"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_base_compare"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_manual_scoring"].status == CapabilityStatus.AVAILABLE
    assert caps["adapter_evaluation_report"].status == CapabilityStatus.AVAILABLE
    assert caps["full_evaluation_center"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_rag_memory"].status == CapabilityStatus.AVAILABLE
    assert caps["novel_evaluation"].status == CapabilityStatus.NOT_IMPLEMENTED
