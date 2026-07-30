import json

import pytest

from llm_studio.admin import AdminManager
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


def _setup_client(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    client = TestClient(get_app(Config(cfg_path)))
    setup = client.post(
        "/v1/setup/initialize",
        json={"admin_password": "StrongAdminPassword123"},
    )
    assert setup.status_code == 200
    return client, setup.json()["api_key"], api_server


def test_bearer_only_authenticates_and_identifies_user(tmp_path):
    client, admin_key, _api_server = _setup_client(tmp_path)

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {admin_key}"})

    assert response.status_code == 200
    assert response.json()["user"]["user_id"] == "admin"
    assert response.json()["user"]["role"] == "admin"


def test_bearer_only_rejects_invalid_and_disabled_users(tmp_path):
    client, _admin_key, api_server = _setup_client(tmp_path)
    operator = api_server._admin.create_user("operator", role="operator")

    bad = client.get("/v1/auth/me", headers={"Authorization": "Bearer bad"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "AUTH_INVALID_API_KEY"

    api_server._admin.toggle_user("operator")
    disabled = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {operator.plain_api_key}"})
    assert disabled.status_code == 401
    assert disabled.json()["error"]["code"] == "AUTH_USER_DISABLED"


def test_legacy_user_id_api_key_headers_still_work(tmp_path):
    client, admin_key, _api_server = _setup_client(tmp_path)

    response = client.get("/v1/auth/me", headers={"X-User-ID": "admin", "X-API-Key": admin_key})

    assert response.status_code == 200
    assert response.json()["user"]["user_id"] == "admin"


def test_admin_user_list_is_safe_and_regenerate_invalidates_old_key(tmp_path):
    client, admin_key, _api_server = _setup_client(tmp_path)
    headers = {"Authorization": f"Bearer {admin_key}"}

    users = client.get("/v1/auth/users", headers=headers)
    assert users.status_code == 200
    user = users.json()["users"][0]
    assert user["user_id"] == "admin"
    assert "api_key_hash" not in user
    assert "api_key" not in user

    regenerated = client.post("/v1/auth/users/admin/regenerate", headers=headers, json={})
    assert regenerated.status_code == 200
    new_key = regenerated.json()["api_key"]
    assert new_key.startswith("sk-llmstudio-")
    assert regenerated.json()["api_key_masked"]

    assert client.get("/v1/auth/me", headers={"Authorization": f"Bearer {admin_key}"}).status_code == 401
    assert client.get("/v1/auth/me", headers={"Authorization": f"Bearer {new_key}"}).status_code == 200


def test_non_admin_cannot_manage_users(tmp_path):
    client, _admin_key, api_server = _setup_client(tmp_path)
    viewer = api_server._admin.create_user("viewer", role="viewer")

    response = client.get("/v1/auth/users", headers={"Authorization": f"Bearer {viewer.plain_api_key}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_ADMIN_REQUIRED"


def test_full_api_key_is_not_recoverable_after_reload(tmp_path):
    users_dir = tmp_path / "auth"
    manager = AdminManager(users_dir)
    admin = manager.initialize("StrongAdminPassword123")
    assert manager.get_full_key("admin") == admin.plain_api_key

    reloaded = AdminManager(users_dir)

    assert reloaded.get_full_key("admin") is None
    data = json.loads((users_dir / "api_users.json").read_text(encoding="utf-8"))
    assert "api_key" not in data["users"][0]
