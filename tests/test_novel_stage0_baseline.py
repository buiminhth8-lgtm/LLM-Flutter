from llm_studio.capabilities import CapabilityStatus, get_capabilities
from llm_studio.features import is_novel_studio_enabled


class TinyConfig:
    def __init__(self, data=None):
        self._data = data or {}

    def get(self, key, default=None):
        return self._data.get(key, default)


def test_novel_feature_flag_defaults_to_disabled():
    assert is_novel_studio_enabled(TinyConfig()) is False
    assert is_novel_studio_enabled(TinyConfig({"features": {"novel_studio": {"enabled": False}}})) is False
    assert is_novel_studio_enabled(TinyConfig({"features": {"novel_studio": {"enabled": True}}})) is True
    assert is_novel_studio_enabled(TinyConfig({"features": "bad"})) is False


def test_novel_capabilities_are_placeholders():
    caps = {cap.name: cap for cap in get_capabilities()}

    assert caps["novel_studio"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_projects"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["prompt_studio"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["writing_workspace"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["revision_system"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["dataset_builder"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["finetune_center"].status == CapabilityStatus.PARTIAL
    assert caps["novel_rag_memory"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_evaluation"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["novel_studio"].frontend_exposed is False


def test_novel_stage0_default_feature_flag_keeps_business_api_disabled(monkeypatch, tmp_path):
    import pytest

    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio.api_server import get_app
    from llm_studio.config import Config

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
    app = get_app(Config(cfg_path))
    paths = {path for route in app.routes if (path := getattr(route, "path", None))}
    assert not any(path.startswith("/v1/writing") for path in paths)
    assert not any(path.startswith("/v1/revisions") for path in paths)
    assert not any(path.startswith("/v1/datasets") for path in paths)

    client = TestClient(app)
    disabled = client.get("/v1/novels/projects")
    assert disabled.status_code == 404
    assert disabled.json()["error"]["code"] == "NOVEL_FEATURE_DISABLED"

    response = client.get("/v1/capabilities")
    assert response.status_code == 200
    caps = {item["name"]: item for item in response.json()["capabilities"]}
    assert caps["novel_studio"]["status"] == CapabilityStatus.NOT_IMPLEMENTED.value


def test_novel_scope_does_not_add_later_stage_services():
    from pathlib import Path

    import llm_studio

    root = Path(llm_studio.__file__).parent
    forbidden_files = {
        root / "revisions" / "repository.py",
        root / "revisions" / "service.py",
        root / "datasets" / "builder.py",
        root / "datasets" / "repository.py",
    }
    assert not any(path.exists() for path in forbidden_files)
