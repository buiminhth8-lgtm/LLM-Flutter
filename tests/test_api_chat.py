import json

import pytest

from llm_studio.api_server import get_app
from llm_studio.config import Config
from llm_studio.runtime.concurrency import QueueFullError


class FakeRunner:
    def __init__(self, *args, **kwargs):
        self.messages = None
        self.loaded = False

    def load(self):
        self.loaded = True

    def unload(self):
        self.loaded = False

    def generate(self, messages, **kwargs):
        self.messages = messages
        return "ok"

    def generate_stream(self, messages, **kwargs):
        self.messages = messages
        yield "o"
        yield "k"


def _write_config(path):
    path.write_text(
        """
auth:
  enabled: false
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )


def _create_ready_model(root):
    model_dir = root / "data" / "models" / "transformers" / "tiny-chat"
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


def test_api_rejects_empty_messages(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={"model": "auto", "messages": []})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGES"


def test_api_rejects_invalid_role(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "auto", "messages": [{"role": "bad", "content": "x"}]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGES"


def test_api_preserves_multi_turn_messages(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    _create_ready_model(tmp_path)
    runner = FakeRunner()

    def create_fake_runner(*args, **kwargs):
        return runner

    monkeypatch.setattr(api_server, "create_runner", create_fake_runner)
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    models = client.get("/v1/models").json()["data"]
    model_id = models[0]["id"]
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": model_id,
            "messages": [
                {"role": "system", "content": "s"},
                {"role": "user", "content": "u1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "u2"},
            ],
        },
    )
    assert response.status_code == 200
    assert [message.role for message in runner.messages] == ["system", "user", "assistant", "user"]


def test_queue_full_error_type():
    assert str(QueueFullError("full")) == "full"


def test_legacy_admin_html_page_is_not_exposed(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    app = get_app(Config(cfg_path))
    client = TestClient(app)

    response = client.get("/admin")

    assert response.status_code == 404
