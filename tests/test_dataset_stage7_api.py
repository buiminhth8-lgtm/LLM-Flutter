from __future__ import annotations

import sqlite3

from llm_studio.api.deps import get_api_state
from tests.test_dataset_api import _accepted_revision
from tests.test_novel_projects_api import _client


def test_dataset_stage7_api_freeze_manifest_and_recipe(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, _, _, revision = _accepted_revision(client)
    dataset = client.post(
        "/v1/datasets",
        json={"name": "Stage 7 API", "project_id": project["id"]},
    ).json()
    sample = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": revision["revision_id"]},
    ).json()
    client.post(f"/v1/datasets/samples/{sample['sample_id']}/approve")

    assert client.post(f"/v1/datasets/{dataset['dataset_id']}/mark-ready").json()["status"] == "ready"
    freeze = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/freeze",
        json={
            "name": "Stage 7 frozen v1",
            "split": {"strategy": "group_by_chapter", "val_ratio": 0.1, "seed": 42},
            "dedupe": {"exact_hash": True, "near_duplicate": True},
            "export_format": "sft_jsonl",
        },
    )
    assert freeze.status_code == 200
    version = freeze.json()
    assert version["version"] == 1
    assert version["status"] == "frozen"

    versions = client.get(f"/v1/datasets/{dataset['dataset_id']}/versions").json()["data"]
    assert versions[0]["dataset_version_id"] == version["dataset_version_id"]
    assert client.get(f"/v1/datasets/versions/{version['dataset_version_id']}").json()["samples"]
    manifest = client.get(
        f"/v1/datasets/versions/{version['dataset_version_id']}/manifest"
    ).json()
    assert manifest["dataset_version_id"] == version["dataset_version_id"]
    assert client.get(
        f"/v1/datasets/versions/{version['dataset_version_id']}/samples"
    ).json()["data"]

    recipe = client.post(
        f"/v1/datasets/versions/{version['dataset_version_id']}/recommend-recipe",
        json={
            "base_model_id": "qwen-local",
            "method": "lora",
            "hardware": {"gpu_vram_gb": 8, "cuda_available": True},
            "preferences": {"quality": "balanced", "max_seq_length": 4096},
        },
    ).json()
    assert recipe["method"] == "qlora"
    patched = client.patch(
        f"/v1/datasets/recipes/{recipe['recipe_id']}",
        json={"user_config": {"epochs": 2}},
    ).json()
    assert patched["user_config"]["epochs"] == 2
    confirmed = client.post(f"/v1/datasets/recipes/{recipe['recipe_id']}/confirm").json()
    assert confirmed["status"] == "confirmed"
    assert client.get(
        f"/v1/datasets/versions/{version['dataset_version_id']}/recipes"
    ).json()["data"]

    with sqlite3.connect(get_api_state().dataset_service.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "finetune_runs" in tables


def test_stage7_api_freeze_not_ready_returns_stable_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project, *_ = _accepted_revision(client)
    dataset = client.post(
        "/v1/datasets",
        json={"name": "not ready", "project_id": project["id"]},
    ).json()

    response = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/freeze",
        json={"name": "bad"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATASET_FREEZE_NOT_READY"
