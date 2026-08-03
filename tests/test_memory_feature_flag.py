from fastapi.testclient import TestClient

from llm_studio.auth.permissions import required_permission_for_request
from llm_studio.auth.roles import Permission
from llm_studio.capabilities.registry import get_capabilities_for_config
from llm_studio.capabilities.status import CapabilityStatus
from llm_studio.config import Config


def _client(tmp_path, monkeypatch, *, novel_memory_enabled: bool):
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
  novel_memory:
    enabled: {str(novel_memory_enabled).lower()}
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
    return TestClient(get_app(Config(cfg_path))), Config(cfg_path)


def test_memory_feature_flag_and_capabilities(monkeypatch, tmp_path):
    disabled, _ = _client(tmp_path, monkeypatch, novel_memory_enabled=False)
    response = disabled.get("/v1/memory/documents")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEMORY_FEATURE_DISABLED"

    _, config = _client(tmp_path, monkeypatch, novel_memory_enabled=True)
    caps = {item.name: item for item in get_capabilities_for_config(config)}
    assert caps["novel_rag_memory"].status == CapabilityStatus.AVAILABLE
    assert caps["memory_documents"].status == CapabilityStatus.AVAILABLE
    assert caps["memory_keyword_retrieval"].status == CapabilityStatus.AVAILABLE
    assert caps["memory_embedding_retrieval"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["full_evaluation_center"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_evaluation"].status == CapabilityStatus.NOT_IMPLEMENTED


def test_memory_permissions():
    assert required_permission_for_request("GET", "/v1/memory/documents") == Permission.VIEW_MEMORY
    assert required_permission_for_request("POST", "/v1/memory/retrieve") == Permission.VIEW_MEMORY
    assert required_permission_for_request("POST", "/v1/memory/documents") == Permission.MANAGE_MEMORY

