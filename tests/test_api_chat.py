import pytest

from llm_studio.api_server import get_app
from llm_studio.config import Config
from llm_studio.runtime.concurrency import QueueFullError


class FakeRunner:
    def __init__(self):
        self.messages = None

    def generate(self, messages, **kwargs):
        self.messages = messages
        return "ok"

    def generate_stream(self, messages, **kwargs):
        self.messages = messages
        yield "o"
        yield "k"


def test_api_rejects_empty_messages(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("auth:\n  enabled: false\n", encoding="utf-8")
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={"model": "auto", "messages": []})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGES"


def test_api_rejects_invalid_role(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("auth:\n  enabled: false\n", encoding="utf-8")
    api_server._runners["auto"] = FakeRunner()
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "auto", "messages": [{"role": "bad", "content": "x"}]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGES"
    api_server._runners.clear()


def test_api_preserves_multi_turn_messages(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("auth:\n  enabled: false\n", encoding="utf-8")
    runner = FakeRunner()
    api_server._runners["auto"] = runner
    app = get_app(Config(cfg_path))
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "auto",
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
    api_server._runners.clear()


def test_queue_full_error_type():
    assert str(QueueFullError("full")) == "full"
