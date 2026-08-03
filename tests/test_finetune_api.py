from __future__ import annotations

from llm_studio.api.deps import get_api_state
from tests.finetune_stage8_utils import FakeModelRepository
from tests.test_dataset_api import _accepted_revision
from tests.test_novel_projects_api import _client


def _frozen_api_dataset(client):
    project, _, _, revision = _accepted_revision(client)
    dataset = client.post(
        "/v1/datasets",
        json={"name": "Stage 8 API", "project_id": project["id"]},
    ).json()
    sample = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
        json={"revision_id": revision["revision_id"]},
    ).json()
    client.post(f"/v1/datasets/samples/{sample['sample_id']}/approve")
    client.post(f"/v1/datasets/{dataset['dataset_id']}/mark-ready")
    version = client.post(
        f"/v1/datasets/{dataset['dataset_id']}/freeze",
        json={"name": "stage8-v1"},
    ).json()
    recipe = client.post(
        f"/v1/datasets/versions/{version['dataset_version_id']}/recommend-recipe",
        json={"base_model_id": "qwen-local", "hardware": {"gpu_vram_gb": 8}},
    ).json()
    recipe = client.post(f"/v1/datasets/recipes/{recipe['recipe_id']}/confirm").json()
    return version, recipe


def _enable_fake_finetune(tmp_path):
    state = get_api_state()
    fake_models = FakeModelRepository(tmp_path)
    state.finetune_service.model_repository = fake_models
    state.finetune_service.preflight_checker.model_repository = fake_models
    state.finetune_service.use_fake_trainer = True
    state.finetune_service.preflight_checker.use_fake_trainer = True
    state.finetune_service.preflight_checker.dependency_checker = lambda method: ([], [])
    return state


def test_finetune_api_preflight_create_run_metrics_and_checkpoints(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    version, recipe = _frozen_api_dataset(client)
    state = _enable_fake_finetune(tmp_path)
    request = {
        "dataset_version_id": version["dataset_version_id"],
        "recipe_id": recipe["recipe_id"],
        "base_model_id": "qwen-local",
        "adapter_name": "玄幻风格-v1",
    }

    preflight = client.post("/v1/finetune/preflight", json=request)
    assert preflight.status_code == 200
    assert preflight.json()["ok"] is True

    created = client.post("/v1/finetune/runs", json={**request, "start_immediately": True})
    assert created.status_code == 200
    run = created.json()
    assert run["job_id"]
    state.job_queue.shutdown(wait=True)

    detail = client.get(f"/v1/finetune/runs/{run['run_id']}").json()
    assert detail["status"] == "completed"
    assert detail["adapter_id"]
    assert client.get("/v1/finetune/runs").json()["data"]
    assert client.get(f"/v1/finetune/runs/{run['run_id']}/metrics").json()["data"]
    assert client.get(f"/v1/finetune/runs/{run['run_id']}/logs").json()["data"]
    assert client.get(f"/v1/finetune/runs/{run['run_id']}/checkpoints").json()["data"]


def test_finetune_api_missing_version_returns_stable_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _enable_fake_finetune(tmp_path)
    response = client.post(
        "/v1/finetune/preflight",
        json={
            "dataset_version_id": "missing",
            "recipe_id": "recipe",
            "base_model_id": "qwen-local",
            "adapter_name": "a",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FINETUNE_DATASET_VERSION_NOT_FOUND"
