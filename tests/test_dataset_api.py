from __future__ import annotations

from llm_studio.api.deps import get_api_state
from tests.test_novel_projects_api import _client
from tests.test_revision_api import _generation


def _accepted_revision(client):
    project, chapter, generation = _generation(client)
    revision = client.post(
        "/v1/revisions/from-generation",
        json={
            "generation_id": generation["generation_id"],
            "edited_text": "human dataset text",
            "user_score": 4,
            "accepted_for_dataset": True,
        },
    ).json()
    revision = client.post(f"/v1/revisions/{revision['revision_id']}/approve").json()
    return project, chapter, generation, revision


def test_dataset_api_crud_samples_export(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, _, _, revision = _accepted_revision(client)

    created = client.post(
        "/v1/datasets",
        json={"name": "Stage 6 API", "project_id": project["id"]},
    )
    assert created.status_code == 200
    dataset = created.json()

    assert client.get("/v1/datasets").json()["data"][0]["dataset_id"] == dataset["dataset_id"]
    patched = client.patch(
        f"/v1/datasets/{dataset['dataset_id']}",
        json={"status": "reviewing"},
    )
    assert patched.json()["status"] == "reviewing"

    sample_response = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": revision["revision_id"], "sample_type": "sft"},
    )
    assert sample_response.status_code == 200
    sample = sample_response.json()
    assert sample["output"] == "human dataset text"

    duplicate = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": revision["revision_id"], "sample_type": "sft"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DATASET_SAMPLE_DUPLICATE"

    assert (
        client.get(f"/v1/datasets/{dataset['dataset_id']}/samples")
        .json()["data"][0]["sample_id"]
        == sample["sample_id"]
    )
    updated = client.patch(
        f"/v1/datasets/samples/{sample['sample_id']}",
        json={"instruction": "新的指令", "output": "更好的正文"},
    )
    assert updated.json()["instruction"] == "新的指令"
    approved = client.post(f"/v1/datasets/samples/{sample['sample_id']}/approve")
    assert approved.json()["status"] == "approved"

    export = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/export",
        json={"format": "sft_jsonl", "file_name": "draft_sft.jsonl"},
    )
    assert export.status_code == 200
    assert export.json()["sample_count"] == 1
    assert ":\\" not in export.json()["export_path"]
    assert client.get(f"/v1/datasets/{dataset['dataset_id']}/exports").json()["data"]

    rejected = client.post(
        f"/v1/datasets/samples/{sample['sample_id']}/reject",
        json={"reason": "bad"},
    )
    assert rejected.json()["status"] == "rejected"
    assert client.delete(f"/v1/datasets/samples/{sample['sample_id']}").json()["status"] == "archived"
    assert client.delete(f"/v1/datasets/{dataset['dataset_id']}").json()["status"] == "archived"


def test_dataset_api_revision_not_accepted_and_missing(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, _, _, revision = _accepted_revision(client)
    revision = client.post(
        f"/v1/revisions/{revision['revision_id']}/dataset-candidate",
        json={"accepted": False},
    ).json()
    dataset = client.post(
        "/v1/datasets",
        json={"name": "Stage 6 API", "project_id": project["id"]},
    ).json()

    not_accepted = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": revision["revision_id"]},
    )
    assert not_accepted.status_code == 400
    assert not_accepted.json()["error"]["code"] == "DATASET_REVISION_NOT_ACCEPTED"

    missing = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": "missing"},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "DATASET_REVISION_NOT_FOUND"


def test_dataset_api_export_requires_approved_samples(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, *_ = _accepted_revision(client)
    dataset = client.post(
        "/v1/datasets",
        json={"name": "empty", "project_id": project["id"]},
    ).json()
    response = client.post(f"/v1/datasets/{dataset['dataset_id']}/export", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATASET_NO_APPROVED_SAMPLES"


def test_dataset_api_bulk_from_revisions(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, _, _, revision = _accepted_revision(client)
    dataset = client.post(
        "/v1/datasets",
        json={"name": "bulk", "project_id": project["id"]},
    ).json()

    result = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/bulk-from-revisions",
        json={
            "project_id": project["id"],
            "min_score": 4,
            "accepted_for_dataset": True,
            "revision_status": "approved",
            "sample_type": "sft",
        },
    )
    assert result.status_code == 200
    assert result.json()["created_count"] == 1
    assert result.json()["samples"][0]["revision_id"] == revision["revision_id"]

    # Keep the API state dependency reachable for route integration.
    assert get_api_state().dataset_service is not None
