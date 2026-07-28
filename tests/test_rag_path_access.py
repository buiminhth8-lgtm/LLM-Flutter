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


class FakeRagPipeline:
    def __init__(self):
        self.document_count = 0
        self.ingested_files: list[str] = []
        self.ingested_directories: list[str] = []

    def load(self):
        return None

    def ingest_file(self, path):
        self.ingested_files.append(str(path))
        self.document_count += 1
        return 1

    def ingest_directory(self, path, recursive=True):
        self.ingested_directories.append(str(path))
        self.document_count += 1
        return 1

    def save(self):
        return None


def _client(monkeypatch, tmp_path, *, enabled: bool, allowed_root):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, enabled=enabled, allowed_root=allowed_root)
    monkeypatch.setenv("LLM_STUDIO_CONFIG", str(cfg_path))

    import llm_studio.api_server as api_server
    from llm_studio.api_server import get_app

    api_server._runners.clear()
    api_server._runner_model_ids.clear()
    api_server._current_model_id = None
    client = TestClient(get_app(Config(cfg_path)))
    fake_rag = FakeRagPipeline()
    api_server._rag_pipeline = fake_rag
    return client, _setup_users(client), fake_rag


def test_rag_file_path_disabled_by_default(monkeypatch, tmp_path):
    allowed = tmp_path / "imports"
    allowed.mkdir()
    document = allowed / "note.txt"
    document.write_text("hello", encoding="utf-8")
    client, headers, _rag = _client(monkeypatch, tmp_path, enabled=False, allowed_root=allowed)

    response = client.post(
        "/v1/rag/ingest?sync=true",
        headers=headers["admin"],
        json={"file_path": str(document)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "RAG_PATH_NOT_ALLOWED"


def test_rag_directory_path_disabled_by_default(monkeypatch, tmp_path):
    allowed = tmp_path / "imports"
    allowed.mkdir()
    client, headers, _rag = _client(monkeypatch, tmp_path, enabled=False, allowed_root=allowed)

    response = client.post(
        "/v1/rag/ingest?sync=true",
        headers=headers["admin"],
        json={"directory_path": str(allowed)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "RAG_PATH_NOT_ALLOWED"


def test_rag_local_path_requires_admin(monkeypatch, tmp_path):
    allowed = tmp_path / "imports"
    allowed.mkdir()
    document = allowed / "note.txt"
    document.write_text("hello", encoding="utf-8")
    client, headers, _rag = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/rag/ingest?sync=true",
        headers=headers["operator"],
        json={"file_path": str(document)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "RAG_PATH_NOT_ALLOWED"


def test_rag_local_path_rejects_outside_allowlist(monkeypatch, tmp_path):
    allowed = tmp_path / "imports"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    client, headers, _rag = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/rag/ingest?sync=true",
        headers=headers["admin"],
        json={"file_path": str(outside)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "RAG_PATH_NOT_ALLOWED"


def test_rag_allowed_local_path_enters_business_logic(monkeypatch, tmp_path):
    allowed = tmp_path / "imports"
    allowed.mkdir()
    document = allowed / "note.txt"
    document.write_text("hello", encoding="utf-8")
    client, headers, rag = _client(monkeypatch, tmp_path, enabled=True, allowed_root=allowed)

    response = client.post(
        "/v1/rag/ingest?sync=true",
        headers=headers["admin"],
        json={"file_path": str(document)},
    )

    assert response.status_code == 200
    assert response.json()["chunks_added"] == 1
    assert rag.ingested_files == [str(document.resolve())]
