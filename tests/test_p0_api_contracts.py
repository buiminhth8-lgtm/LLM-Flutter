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
    model_dir = root / "data" / "models" / "transformers" / "tiny-contract"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(
        json.dumps({"architectures": ["TinyForCausalLM"], "model_type": "tiny"}),
        encoding="utf-8",
    )
    (model_dir / "model.safetensors").write_bytes(b"fake")
    return model_dir


def _create_adapter(root, *, complete=True):
    adapter_dir = root / "data" / "adapters" / ("complete-adapter" if complete else "broken-adapter")
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "adapter_config.json").write_text(
        json.dumps(
            {
                "base_model_name_or_path": "tiny-contract",
                "peft_type": "LORA",
                "task_type": "CAUSAL_LM",
                "r": 8,
                "lora_alpha": 16,
                "target_modules": ["q_proj", "v_proj"],
            }
        ),
        encoding="utf-8",
    )
    if complete:
        (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake")
    return adapter_dir


def _setup_users(client):
    import llm_studio.api_server as api_server

    setup = client.post("/v1/setup/initialize", json={"admin_password": "StrongerPassword123"})
    admin_key = setup.json()["api_key"]
    operator = api_server._admin.create_user("operator", role="operator")
    return {
        "admin": {"X-User-ID": "admin", "X-API-Key": admin_key},
        "operator": {"X-User-ID": "operator", "X-API-Key": operator.plain_api_key},
    }


class FakeRunner:
    def __init__(self, path, config):
        self.path = path
        self.loaded = False
        self.loaded_adapter_names = []

    def load(self):
        self.loaded = True

    def unload(self):
        self.loaded = False

    def load_adapter(self, adapter, adapter_name=None):
        if not adapter.compatible:
            from llm_studio.adapters.exceptions import AdapterCompatibilityError

            raise AdapterCompatibilityError("; ".join(adapter.compatibility_errors))
        name = adapter_name or adapter.name
        self.loaded_adapter_names.append(name)
        return name

    def activate_adapter(self, adapter_name):
        self.active_adapter = adapter_name

    def deactivate_adapter(self):
        self.active_adapter = None

    def unload_adapter(self, adapter_name):
        if adapter_name in self.loaded_adapter_names:
            self.loaded_adapter_names.remove(adapter_name)

    def list_loaded_adapters(self):
        return tuple(self.loaded_adapter_names)


class FakeDocument:
    content = "fake context"
    metadata = {"filename": "fake.txt"}


class FakeRagPipeline:
    document_count = 1

    def __init__(self):
        self.last_question = None
        self.last_top_k = None

    def query(self, question, top_k=5):
        self.last_question = question
        self.last_top_k = top_k
        return [(FakeDocument(), 0.9)]

    def build_rag_prompt(self, question, top_k=5):
        return f"{question}:{top_k}"


class FakeAdapterRepository:
    def __init__(self, adapter):
        self.adapter = adapter

    def list(self):
        return [self.adapter]

    def get(self, adapter_id):
        if adapter_id == self.adapter.id:
            return self.adapter
        from llm_studio.adapters.exceptions import AdapterNotFoundError

        raise AdapterNotFoundError(adapter_id)


def _adapter_info(tmp_path, *, compatible=True):
    from llm_studio.adapters import AdapterInfo

    return AdapterInfo(
        id="adapter-contract",
        name="complete-adapter" if compatible else "broken-adapter",
        path=tmp_path / "data" / "adapters" / "adapter-contract",
        base_model_name_or_path="tiny-contract",
        peft_type="LORA",
        task_type="CAUSAL_LM",
        rank=8,
        alpha=16,
        target_modules=("q_proj", "v_proj"),
        size_bytes=1,
        compatible=compatible,
        compatibility_errors=() if compatible else ("missing adapter weights",),
    )


def _client(monkeypatch, tmp_path, *, adapter_complete: bool | None = None):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)
    _create_ready_model(tmp_path)
    if adapter_complete is not None:
        _create_adapter(tmp_path, complete=adapter_complete)
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))

    import llm_studio.api_server as api_server
    from llm_studio.adapters import AdapterRepository
    from llm_studio.api_server import get_app
    from llm_studio.models import LocalModelRepository

    cfg = Config(cfg_path)
    api_server._runners.clear()
    api_server._runner_model_ids.clear()
    api_server._current_model_id = None
    monkeypatch.setattr(api_server, "create_runner", FakeRunner)
    client = TestClient(get_app(cfg))
    api_server._model_repository = LocalModelRepository(cfg)
    api_server._adapter_repository = AdapterRepository(cfg)
    headers = _setup_users(client)
    return client, headers, api_server


def test_rag_query_accepts_question_and_legacy_query(monkeypatch, tmp_path):
    client, headers, api_server = _client(monkeypatch, tmp_path)
    fake_rag = FakeRagPipeline()
    api_server._rag_pipeline = fake_rag

    response = client.post("/v1/rag/query", headers=headers["operator"], json={"question": "hello", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["question"] == "hello"
    assert fake_rag.last_question == "hello"
    assert fake_rag.last_top_k == 3

    legacy = client.post("/v1/rag/query", headers=headers["operator"], json={"query": "legacy"})
    assert legacy.status_code == 200
    assert legacy.json()["question"] == "legacy"

    invalid = client.post("/v1/rag/query", headers=headers["operator"], json={"question": ""})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "RAG_QUERY_INVALID"


def test_adapter_action_requires_model_context_and_accepts_model_body(monkeypatch, tmp_path):
    client, headers, _api_server = _client(monkeypatch, tmp_path)
    adapter = _adapter_info(tmp_path, compatible=True)
    _api_server._adapter_repository = FakeAdapterRepository(adapter)
    adapter_id = adapter.id

    missing_model = client.post(f"/v1/adapters/{adapter_id}/load", headers=headers["operator"])
    assert missing_model.status_code == 400
    assert missing_model.json()["error"]["code"] == "ADAPTER_MODEL_REQUIRED"

    model_id = client.get("/v1/models", headers=headers["admin"]).json()["data"][0]["id"]
    loaded = client.post(f"/v1/adapters/{adapter_id}/load", headers=headers["operator"], json={"model": model_id})
    assert loaded.status_code == 200
    assert loaded.json()["adapter_name"] == "complete-adapter"


def test_incompatible_adapter_returns_stable_error(monkeypatch, tmp_path):
    client, headers, _api_server = _client(monkeypatch, tmp_path)
    adapter = _adapter_info(tmp_path, compatible=False)
    _api_server._adapter_repository = FakeAdapterRepository(adapter)
    adapter_id = adapter.id
    model_id = client.get("/v1/models", headers=headers["admin"]).json()["data"][0]["id"]

    response = client.post(f"/v1/adapters/{adapter_id}/load", headers=headers["operator"], json={"model": model_id})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "ADAPTER_INCOMPATIBLE"


def test_delete_model_requires_confirm_and_returns_stable_success(monkeypatch, tmp_path):
    client, headers, _api_server = _client(monkeypatch, tmp_path)
    model_id = client.get("/v1/models", headers=headers["admin"]).json()["data"][0]["id"]

    missing_confirm = client.delete(f"/v1/models/{model_id}", headers=headers["admin"])
    assert missing_confirm.status_code == 409
    assert missing_confirm.json()["error"]["code"] == "MODEL_DELETE_CONFIRM_REQUIRED"

    false_confirm = client.delete(f"/v1/models/{model_id}?confirm=false", headers=headers["admin"])
    assert false_confirm.status_code == 409
    assert false_confirm.json()["error"]["code"] == "MODEL_DELETE_CONFIRM_REQUIRED"

    deleted = client.delete(f"/v1/models/{model_id}?confirm=true", headers=headers["admin"])
    assert deleted.status_code == 200
    assert deleted.json()["model_id"] == model_id
    assert deleted.json()["trashed"] is True
