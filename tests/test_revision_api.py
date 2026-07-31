from llm_studio.api.deps import get_api_state
from tests.test_novel_projects_api import _client
from tests.test_writing_api import _seed_api
from tests.test_writing_service import FakeRuntimeBridge


def _generation(client):
    get_api_state().writing_service.runtime_bridge = FakeRuntimeBridge("model original")
    project, chapter, template = _seed_api(client)
    response = client.post(
        "/v1/writing/generate",
        json={
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "model_id": "fake-model",
            "mode": "chapter_generate",
            "target_length": {
                "unit": "chars",
                "min": 1,
                "max": 100,
                "strategy": "soft",
            },
            "generation_params": {"max_tokens": 64},
        },
    )
    return project, chapter, response.json()


def test_revision_api_crud_review_candidate_and_autosave(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, chapter, generation = _generation(client)

    created = client.post(
        "/v1/revisions/from-generation",
        json={
            "generation_id": generation["generation_id"],
            "edited_text": "human edited",
            "edit_tags": ["language_polish"],
            "user_score": 4,
            "accepted_for_dataset": True,
        },
    )
    assert created.status_code == 200
    revision = created.json()
    assert revision["original_text"] == "model original"
    assert revision["diff"]["summary"]["changed_blocks"] >= 1

    listed = client.get(f"/v1/revisions?project_id={project['id']}")
    assert listed.status_code == 200
    assert listed.json()["data"][0]["revision_id"] == revision["revision_id"]
    assert client.get(f"/v1/revisions/{revision['revision_id']}").status_code == 200

    stale = client.patch(
        f"/v1/revisions/{revision['revision_id']}",
        json={"edited_text": "stale", "expected_updated_at": "old"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "REVISION_CONFLICT"

    updated = client.patch(
        f"/v1/revisions/{revision['revision_id']}",
        json={
            "edited_text": "better human edited",
            "expected_updated_at": revision["updated_at"],
        },
    )
    assert updated.status_code == 200

    autosave = client.post(
        "/v1/revisions/autosave",
        json={
            "revision_id": revision["revision_id"],
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "generation_id": generation["generation_id"],
            "draft_text": "typing draft",
            "client_revision": 2,
        },
    )
    assert autosave.status_code == 200
    assert (
        client.get(f"/v1/revisions/{revision['revision_id']}/autosaves")
        .json()["data"][0]["draft_text"]
        == "typing draft"
    )

    assert client.post(f"/v1/revisions/{revision['revision_id']}/approve").json()["status"] == "approved"
    assert (
        client.post(
            f"/v1/revisions/{revision['revision_id']}/dataset-candidate",
            json={"accepted": False},
        ).json()["accepted_for_dataset"]
        is False
    )
    assert client.post(
        f"/v1/revisions/{revision['revision_id']}/reject",
        json={"reason": "needs work"},
    ).json()["status"] == "rejected"
    assert client.delete(f"/v1/revisions/{revision['revision_id']}").json()["status"] == "archived"


def test_revision_api_validation_errors(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _, _, generation = _generation(client)

    invalid_tag = client.post(
        "/v1/revisions/from-generation",
        json={"generation_id": generation["generation_id"], "edit_tags": ["bad"]},
    )
    assert invalid_tag.status_code == 400
    assert invalid_tag.json()["error"]["code"] == "REVISION_INVALID_TAG"

    missing = client.post(
        "/v1/revisions/from-generation",
        json={"generation_id": "missing"},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "REVISION_GENERATION_NOT_FOUND"
