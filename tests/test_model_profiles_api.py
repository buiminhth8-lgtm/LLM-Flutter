from tests.test_novel_projects_api import _client


def _create_body(**extra):
    return {
        "name": "Local Qwen Default",
        "provider": "local_runtime",
        "model": "qwen3-8b",
        "description": "本地小说写作默认模型",
        "default_params": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 1400},
        "capabilities": {
            "stream": True,
            "json_output": False,
            "tool_calls": False,
            "vision": False,
            "max_context_tokens": 8192,
            "max_output_tokens": 2048,
        },
        "privacy_policy": {"mode": "offline_only"},
        "connection": {},
        "metadata": {"source": "user"},
        "is_default": True,
        **extra,
    }


def test_model_profiles_list_and_create(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    created = client.post("/v1/model-profiles", json=_create_body())
    assert created.status_code == 200
    profile = created.json()
    assert profile["provider"] == "local_runtime"
    assert profile["model"] == "qwen3-8b"
    assert profile["is_default"] is True

    listed = client.get("/v1/model-profiles")
    assert listed.status_code == 200
    assert any(item["id"] == profile["id"] for item in listed.json()["data"])


def test_model_profiles_get_update_and_set_default(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    created = client.post("/v1/model-profiles", json=_create_body()).json()

    fetched = client.get(f"/v1/model-profiles/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Local Qwen Default"

    patched = client.patch(
        f"/v1/model-profiles/{created['id']}",
        json={"default_params": {"temperature": 0.6}},
    )
    assert patched.status_code == 200
    assert patched.json()["default_params"] == {"temperature": 0.6}

    second = client.post(
        "/v1/model-profiles",
        json=_create_body(name="Second", model="second-model", is_default=False),
    ).json()
    set_default = client.post(f"/v1/model-profiles/{second['id']}/set-default")
    assert set_default.status_code == 200
    assert set_default.json()["is_default"] is True
    assert client.get(f"/v1/model-profiles/{created['id']}").json()["is_default"] is False


def test_model_profiles_default_endpoint(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    client.post("/v1/model-profiles", json=_create_body())

    default = client.get("/v1/model-profiles/default")

    assert default.status_code == 200
    assert default.json()["is_default"] is True
    assert default.json()["provider"] == "local_runtime"


def test_model_profiles_ensure_builtins(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    first = client.post("/v1/model-profiles/defaults/ensure")
    second = client.post("/v1/model-profiles/defaults/ensure")

    assert first.status_code == 200
    assert first.json()["created"] == 2
    assert second.json()["created"] == 0
    assert second.json()["skipped"] == 2

    listed = client.get("/v1/model-profiles").json()["data"]
    names = {item["name"] for item in listed}
    assert names == {"Fake Test Model", "Local Runtime Default"}


def test_model_profiles_delete_archives(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    created = client.post("/v1/model-profiles", json=_create_body()).json()

    deleted = client.delete(f"/v1/model-profiles/{created['id']}")

    assert deleted.status_code == 200
    assert deleted.json()["status"] == "archived"
    listed = client.get("/v1/model-profiles").json()["data"]
    assert created["id"] not in {item["id"] for item in listed}


def test_model_profiles_reserved_provider_rejected(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/v1/model-profiles",
        json=_create_body(name="DeepSeek", provider="deepseek", status="enabled"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MODEL_PROFILE_INVALID_PROVIDER"
