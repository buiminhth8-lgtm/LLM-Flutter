from llm_studio.capabilities import CapabilityStatus, get_capabilities
from llm_studio.config import Config


def test_capability_registry_has_truthful_statuses():
    caps = {cap.name: cap for cap in get_capabilities()}

    assert caps["chat_non_stream"].status == CapabilityStatus.AVAILABLE
    assert caps["chat_stream"].status != CapabilityStatus.BACKEND_ONLY
    assert caps["chat_stream"].frontend_exposed is True
    assert caps["lora_merge"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["benchmark"].status == CapabilityStatus.EXPERIMENTAL
    assert caps["benchmark_with_adapter"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["benchmark_with_adapter"].frontend_exposed is False
    assert caps["model_download"].status == CapabilityStatus.AVAILABLE
    assert caps["model_download"].frontend_exposed is True
    assert caps["model_download_progress"].status == CapabilityStatus.PARTIAL
    assert caps["model_download_progress"].frontend_exposed is True
    assert caps["model_download_retry"].status == CapabilityStatus.AVAILABLE
    assert caps["model_download_auto_register"].status == CapabilityStatus.AVAILABLE
    assert caps["lora_scan"].frontend_exposed is True
    assert caps["flutter_windows"].status == CapabilityStatus.AVAILABLE
    assert caps["flutter_android"].status == CapabilityStatus.NOT_IMPLEMENTED


def test_capabilities_are_serializable():
    data = [cap.to_dict() for cap in get_capabilities()]

    assert all("name" in item and "status" in item for item in data)
    assert all(item["status"] != "available" for item in data if item["name"].endswith("_android"))


def test_capabilities_endpoint_exposes_streaming_chat(monkeypatch, tmp_path):
    import pytest

    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
auth:
  enabled: false
api:
  allowed_origins: []
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))

    from llm_studio.api_server import get_app

    client = TestClient(get_app(Config(cfg_path)))
    response = client.get("/v1/capabilities")

    assert response.status_code == 200
    caps = {item["name"]: item for item in response.json()["capabilities"]}
    assert caps["chat_stream"]["status"] != CapabilityStatus.BACKEND_ONLY.value
    assert caps["chat_stream"]["frontend_exposed"] is True
    assert caps["benchmark_with_adapter"]["status"] == CapabilityStatus.NOT_IMPLEMENTED.value
    assert caps["benchmark_with_adapter"]["frontend_exposed"] is False
