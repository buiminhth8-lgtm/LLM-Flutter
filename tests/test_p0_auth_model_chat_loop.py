import json

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


def _create_ready_model(root):
    model_dir = root / "data" / "models" / "transformers" / "tiny-3b"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(
        json.dumps(
            {
                "architectures": ["TinyForCausalLM"],
                "model_type": "tiny",
                "max_position_embeddings": 1024,
            }
        ),
        encoding="utf-8",
    )
    (model_dir / "model.safetensors").write_bytes(b"fake")
    return model_dir


class FakeRunner:
    def __init__(self, path, config):
        self.path = path
        self.config = config
        self.loaded = False
        self.unloaded = False

    def load(self):
        self.loaded = True

    def unload(self):
        self.unloaded = True

    def generate(self, messages, **kwargs):
        assert self.loaded
        assert messages[-1].content == "hello"
        return f"ok:{self.path}"

    def generate_stream(self, messages, **kwargs):
        yield "ok"


def test_first_run_setup_initializes_and_authenticates(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    client = TestClient(get_app(Config(cfg_path)))

    status = client.get("/v1/setup/status")
    assert status.status_code == 200
    assert status.json()["requires_setup"] is True

    assert client.get("/v1/runtime").status_code == 401

    weak = client.post("/v1/setup/initialize", json={"admin_password": "admin"})
    assert weak.status_code == 400

    initialized = client.post(
        "/v1/setup/initialize",
        json={"admin_password": "StrongerPassword123", "display_name": "Admin"},
    )
    assert initialized.status_code == 200
    api_key = initialized.json()["api_key"]
    assert api_key.startswith("sk-llmstudio-")

    again = client.post(
        "/v1/setup/initialize",
        json={"admin_password": "AnotherStrongPassword123"},
    )
    assert again.status_code == 409

    headers = {"X-User-ID": "admin", "Authorization": f"Bearer {api_key}"}
    assert client.get("/v1/runtime", headers=headers).status_code == 200
    assert client.get("/v1/runtime", headers={"X-User-ID": "admin", "X-API-Key": "bad"}).status_code == 401


def test_chat_uses_unified_model_repository(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    _create_ready_model(tmp_path)
    monkeypatch.setattr(api_server, "create_runner", FakeRunner)

    client = TestClient(get_app(Config(cfg_path)))
    setup = client.post(
        "/v1/setup/initialize",
        json={"admin_password": "StrongerPassword123"},
    )
    headers = {"X-User-ID": "admin", "X-API-Key": setup.json()["api_key"]}

    models = client.get("/v1/models", headers=headers).json()["data"]
    model_id = models[0]["id"]
    assert models[0]["status"] == "ready"

    loaded = client.post(f"/v1/models/{model_id}/load", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["model_id"] == model_id

    current = client.get("/v1/models/current", headers=headers)
    assert current.json()["loaded"] is True
    assert current.json()["model_id"] == model_id

    chat = client.post(
        "/v1/chat/completions",
        headers=headers,
        json={
            "model": model_id,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert chat.status_code == 200
    assert chat.json()["model"] == model_id
    assert "ok:" in chat.json()["choices"][0]["message"]["content"]


def test_auto_without_repository_model_returns_model_not_found(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    client = TestClient(get_app(Config(cfg_path)))
    setup = client.post(
        "/v1/setup/initialize",
        json={"admin_password": "StrongerPassword123"},
    )
    headers = {"X-User-ID": "admin", "X-API-Key": setup.json()["api_key"]}

    response = client.post(
        "/v1/chat/completions",
        headers=headers,
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"
