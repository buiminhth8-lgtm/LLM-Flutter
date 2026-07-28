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
storage:
  diagnostics_dir: ./data/diagnostics
uploads:
  temp_dir: ./data/uploads
""",
        encoding="utf-8",
    )


def _headers(client):
    setup = client.post("/v1/setup/initialize", json={"admin_password": "StrongerPassword123"})
    return {"X-User-ID": "admin", "X-API-Key": setup.json()["api_key"]}


def test_capabilities_endpoint_and_storage_preview(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    client = TestClient(get_app(Config(cfg_path)))
    headers = _headers(client)

    caps = client.get("/v1/capabilities", headers=headers)
    assert caps.status_code == 200
    data = {item["name"]: item for item in caps.json()["capabilities"]}
    assert data["lora_merge"]["status"] == "not_implemented"

    upload = tmp_path / "data" / "uploads" / "tmp.txt"
    upload.parent.mkdir(parents=True, exist_ok=True)
    upload.write_text("temp", encoding="utf-8")
    preview = client.post("/v1/storage/cleanup/preview", headers=headers, json={"categories": ["uploads_temp"]})
    assert preview.status_code == 200
    assert preview.json()["total_size_bytes"] >= 4
