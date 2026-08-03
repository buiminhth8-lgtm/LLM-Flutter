from __future__ import annotations

from tests.finetune_stage8_utils import fake_finetune_service


def _request(version, recipe, *, start_immediately=False):
    return {
        "dataset_version_id": version["dataset_version_id"],
        "recipe_id": recipe["recipe_id"],
        "base_model_id": "qwen-local",
        "adapter_name": "玄幻风格-v1",
        "start_immediately": start_immediately,
    }


def test_create_run_persists_snapshots_without_starting_training(tmp_path):
    service, _, _, version, recipe, _ = fake_finetune_service(tmp_path)
    run = service.create_run(_request(version, recipe, start_immediately=False))

    assert run["status"] == "created"
    assert run["dataset_version_id"] == version["dataset_version_id"]
    assert run["recipe_id"] == recipe["recipe_id"]
    assert run["config_snapshot"]["method"] == "qlora"
    assert run["dataset_manifest_snapshot"]["dataset_version_id"] == version["dataset_version_id"]
    assert ":\\" not in (run["metrics_path"] or "")
    assert "metrics" in run
    assert service.list_runs()[0]["run_id"] == run["run_id"]


def test_start_and_cancel_run_update_lifecycle_fields(tmp_path):
    service, _, _, version, recipe, _ = fake_finetune_service(tmp_path)
    run = service.create_run(_request(version, recipe, start_immediately=False))
    queued = service.start_run(run["run_id"])

    assert queued["status"] == "queued"
    assert queued["job_id"] == "job-disabled"
    cancelled = service.cancel_run(run["run_id"])
    assert cancelled["cancel_requested"] is True


def test_get_metrics_logs_checkpoints_empty_for_new_run(tmp_path):
    service, _, _, version, recipe, _ = fake_finetune_service(tmp_path)
    run = service.create_run(_request(version, recipe, start_immediately=False))

    assert service.get_metrics(run["run_id"]) == []
    assert service.get_logs(run["run_id"]) == []
    assert service.get_checkpoints(run["run_id"]) == []
