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
    assert caps["revision_diff"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["revision_autosave"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["finetune_center"].status == CapabilityStatus.NOT_IMPLEMENTED
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
    client = TestClient(app)
    disabled = client.get("/v1/novels/projects")
    assert disabled.status_code == 404
    assert disabled.json()["error"]["code"] == "NOVEL_FEATURE_DISABLED"
    writing = client.get("/v1/writing/generations")
    assert writing.status_code == 404
    assert writing.json()["error"]["code"] == "WRITING_FEATURE_DISABLED"
    revisions = client.get("/v1/revisions")
    assert revisions.status_code == 404
    assert revisions.json()["error"]["code"] == "REVISION_FEATURE_DISABLED"
    datasets = client.get("/v1/datasets")
    assert datasets.status_code == 404
    assert datasets.json()["error"]["code"] == "DATASET_FEATURE_DISABLED"

    response = client.get("/v1/capabilities")
    assert response.status_code == 200
    caps = {item["name"]: item for item in response.json()["capabilities"]}
    assert caps["novel_studio"]["status"] == CapabilityStatus.NOT_IMPLEMENTED.value


def test_novel_scope_does_not_add_stage7_or_training_services():
    from pathlib import Path

    import llm_studio

    root = Path(llm_studio.__file__).parent
    forbidden_files = {
        root / "datasets" / "versions.py",
        root / "datasets" / "recipes.py",
        root / "datasets" / "training.py",
    }
    assert not any(path.exists() for path in forbidden_files)
