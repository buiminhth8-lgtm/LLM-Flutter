from llm_studio.api.deps import get_api_state
from tests.test_novel_projects_api import _client


def test_memory_api_documents_build_retrieve_summary_and_index(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Stage 10"}).json()
    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "黑市", "draft_content": "主角发现黑市。"},
    ).json()
    client.post(
        f"/v1/novels/projects/{project['id']}/world-entries",
        json={"category": "地点", "title": "黑市", "content": "黑市位于旧城地下。", "priority": 10},
    )

    manual = client.post(
        "/v1/memory/documents",
        json={
            "project_id": project["id"],
            "source_type": "manual_note",
            "title": "父亲死因",
            "content": "父亲死因与黑市有关。",
            "tags": ["伏笔"],
        },
    )
    assert manual.status_code == 200
    document_id = manual.json()["document_id"]

    build = client.post(
        f"/v1/memory/projects/{project['id']}/build-from-novel",
        json={"include": {"world_entries": True}, "rebuild_index": True},
    )
    assert build.status_code == 200
    assert build.json()["documents_created"] >= 1
    assert client.post(f"/v1/memory/projects/{project['id']}/index/rebuild").status_code == 200
    assert client.get(f"/v1/memory/projects/{project['id']}/index/status").json()["chunks"] >= 1

    retrieved = client.post(
        "/v1/memory/retrieve",
        json={
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "query_text": "黑市",
            "top_k": 3,
            "budget": {"max_memory_tokens": 200, "max_chunks": 2},
        },
    )
    assert retrieved.status_code == 200
    retrieval_id = retrieved.json()["retrieval_id"]
    assert client.get(f"/v1/memory/retrieval-records/{retrieval_id}").status_code == 200
    assert client.get(f"/v1/memory/retrieval-records?project_id={project['id']}").json()["data"]

    summary = client.post(
        f"/v1/memory/chapters/{chapter['id']}/summaries",
        json={"summary_text": "主角发现黑市。", "set_active": True},
    )
    assert summary.status_code == 200
    assert client.get(f"/v1/memory/chapters/{chapter['id']}/summaries").json()["data"]
    assert client.post(
        f"/v1/memory/chapters/{chapter['id']}/summaries/{summary.json()['summary_id']}/activate",
        json={"sync_to_chapter": True},
    ).status_code == 200

    archived = client.delete(f"/v1/memory/documents/{document_id}")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    listed = client.get(f"/v1/memory/documents?project_id={project['id']}&status=archived").json()
    assert any(item["document_id"] == document_id for item in listed["data"])

    state = get_api_state()
    assert state.memory_service is not None


def test_memory_api_validation_errors(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Stage 10"}).json()
    response = client.post(
        "/v1/memory/documents",
        json={
            "project_id": project["id"],
            "source_type": "bad",
            "title": "x",
            "content": "y",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MEMORY_INVALID_SOURCE_TYPE"
