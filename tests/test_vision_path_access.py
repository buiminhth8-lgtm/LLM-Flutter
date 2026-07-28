import pytest

from llm_studio.config import Config


def _write_config(path, *, enabled: bool, allowed_root):
    allowed_root_text = str(allowed_root).replace("\\", "/")
    path.write_text(
        f"""
auth:
  enabled: true
api:
  allowed_origins: []
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
security:
  local_path_access:
    enabled: {str(enabled).lower()}
    allowed_roots:
      - "{allowed_root_text}"
""",
        encoding="utf-8",
    )


def _setup_users(client):
    import llm_studio.api_server as api_server

    setup = client.post("/v1/setup/initialize", json={"admin_password": "StrongerPassword123"})
    admin_key = setup.json()["api_key"]
    operator = api_server._admin.create_user("operator", role="operator")
    return {
        "admin": {"X-User-ID": "admin", "X-API-Key": admin_key},
        "operator": {"X-User-ID": "operator", "X-API-Key": operator.plain_api_key},
    }


class FakeVisionRunner:
    def analyze_image(self, image_path, **kwargs):
        return f"analyzed:{image_path}"


def _client(monkeypatch, tmp_path, *, enabled: bool, allowed_root):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, enabled=enabled, allowed_root=allowed_root)
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    api_server._runners.clear()
    api_server._vision_runners.clear()
    api_server._runner_model_ids.clear()
    api_server._current_model_id = None
    client = TestClient(get_app(Config(cfg_path)))
    api_server._vision_runners["vision"] = FakeVisionRunner()
    return client, _setup_users(client)


def test_vision_image_path_disabled_by_default(monkeypatch, tmp_path):
    allowed = tmp_path / "uploads"
    allowed.mkdir()
    image = allowed / "image.png"
    image.write_bytes(b"fake")
    client, headers = _client(monkeypatch, tmp_path, enabled=False, allowed_root=allowed)

    response = client.post(
        "/v1/vision/analyze",
        headers=headers["admin"],
        json={"model": "vision", "image_path": str(image)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "VISION_PATH_NOT_ALLOWED"


def test_vision_image_path_requires_admin(monkeypatch, tmp_path):
    allowed = tmp_path / "uploads"
    allowed.mkdir()
    image = allowed / "image.png"
    image.write_bytes(b"fake")
    client, headers = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/vision/analyze",
        headers=headers["operator"],
        json={"model": "vision", "image_path": str(image)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "VISION_PATH_NOT_ALLOWED"


def test_vision_image_path_rejects_outside_allowlist(monkeypatch, tmp_path):
    allowed = tmp_path / "uploads"
    allowed.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"fake")
    client, headers = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/vision/analyze",
        headers=headers["admin"],
        json={"model": "vision", "image_path": str(outside)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "VISION_PATH_NOT_ALLOWED"


def test_vision_allowed_image_path_enters_business_logic(monkeypatch, tmp_path):
    allowed = tmp_path / "uploads"
    allowed.mkdir()
    image = allowed / "image.png"
    image.write_bytes(b"fake")
    client, headers = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/vision/analyze",
        headers=headers["admin"],
        json={"model": "vision", "image_path": str(image)},
    )

    assert response.status_code == 200
    assert response.json()["response"] == f"analyzed:{image.resolve()}"
