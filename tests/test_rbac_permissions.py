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
    model_dir = root / "data" / "models" / "transformers" / "tiny-rbac"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(
        json.dumps({"architectures": ["TinyForCausalLM"], "model_type": "tiny"}),
        encoding="utf-8",
    )
    (model_dir / "model.safetensors").write_bytes(b"fake")
    return model_dir


class FakeRunner:
    def __init__(self, path, config):
        self.path = path
        self.loaded = False

    def load(self):
        self.loaded = True

    def unload(self):
        self.loaded = False

    def generate(self, messages, **kwargs):
        return "ok"

    def generate_stream(self, messages, **kwargs):
        yield "ok"


def _setup_users(client):
    import llm_studio.api_server as api_server

    setup = client.post("/v1/setup/initialize", json={"admin_password": "StrongerPassword123"})
    admin_key = setup.json()["api_key"]
    viewer = api_server._admin.create_user("viewer", role="viewer")
    operator = api_server._admin.create_user("operator", role="operator")
    return {
        "admin": {"X-User-ID": "admin", "X-API-Key": admin_key},
        "viewer": {"X-User-ID": "viewer", "X-API-Key": viewer.plain_api_key},
        "operator": {"X-User-ID": "operator", "X-API-Key": operator.plain_api_key},
    }


def test_rbac_roles_gate_api_actions(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    _create_ready_model(tmp_path)
    monkeypatch.setattr(api_server, "create_runner", FakeRunner)
    client = TestClient(get_app(Config(cfg_path)))
    headers = _setup_users(client)

    assert client.get("/v1/runtime").status_code == 401
    assert client.get("/v1/runtime", headers=headers["viewer"]).status_code == 200

    denied = client.post(
        "/v1/chat/completions",
        headers=headers["viewer"],
        json={"model": "auto", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    allowed = client.post(
        "/v1/chat/completions",
        headers=headers["operator"],
        json={"model": "auto", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert allowed.status_code == 200

    model_id = client.get("/v1/models", headers=headers["admin"]).json()["data"][0]["id"]
    delete_denied = client.delete(f"/v1/models/{model_id}?confirm=true", headers=headers["operator"])
    assert delete_denied.status_code == 403

    benchmark = client.post(
        "/v1/benchmarks",
        headers=headers["admin"],
        json={"model_id": model_id, "context_lengths": [16], "measured_runs": 1, "warmup_runs": 0},
    )
    assert benchmark.status_code == 200


def test_legacy_missing_role_migrates_to_admin(tmp_path):
    from llm_studio.admin import AdminManager
    from llm_studio.security import hash_api_key

    key = "sk-legacy"
    db = {
        "admin_password_hash": "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy",
        "users": [{"user_id": "legacy", "api_key_hash": hash_api_key(key), "api_key_masked": "sk...cy"}],
    }
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "api_users.json").write_text(json.dumps(db), encoding="utf-8")

    manager = AdminManager(tmp_path)

    assert manager.get_user("legacy").role == "admin"
