import pytest

from llm_studio.config import Config


def _write_config(path):
    path.write_text(
        """
auth:
  enabled: true
api:
  allowed_origins: []
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )


def test_diagnostics_export_failure_returns_stable_error(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    client = TestClient(get_app(Config(cfg_path)))
    setup = client.post("/v1/setup/initialize", json={"admin_password": "StrongerPassword123"})
    headers = {"X-User-ID": "admin", "X-API-Key": setup.json()["api_key"]}

    def fail_export(config):
        raise RuntimeError("secret traceback")

    monkeypatch.setattr(api_server, "export_diagnostics", fail_export)

    response = client.post("/v1/diagnostics/export", headers=headers)

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "DIAGNOSTICS_EXPORT_FAILED"
    assert "traceback" not in body["error"]["message"].lower()
