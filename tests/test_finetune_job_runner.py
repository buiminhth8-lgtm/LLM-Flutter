from __future__ import annotations

from llm_studio.finetune import FineTuneService
from llm_studio.jobs import JobQueue, JobRepository
from llm_studio.runtime.gpu_scheduler import GpuTaskScheduler
from tests.finetune_stage8_utils import (
    FakeAdapterRepository,
    FakeModelRepository,
    frozen_dataset_and_recipe,
)
from tests.test_dataset_freeze_service import _add_approved_sample
from tests.test_dataset_service import _dataset_seed


def test_fake_trainer_job_completes_and_registers_adapter(tmp_path):
    datasets, _, version, recipe = frozen_dataset_and_recipe(tmp_path)
    job_repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(job_repo)
    adapter_repo = FakeAdapterRepository(tmp_path)
    service = FineTuneService(
        datasets.db_path,
        output_root=tmp_path / "data" / "finetune",
        dataset_service=datasets,
        model_repository=FakeModelRepository(tmp_path),
        adapter_repository=adapter_repo,
        job_queue=queue,
        gpu_scheduler=GpuTaskScheduler(enabled=False),
        use_fake_trainer=True,
        dependency_checker=lambda method: ([], []),
    )

    run = service.create_run(
        {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "玄幻风格-v1",
            "start_immediately": True,
        }
    )
    queue.shutdown(wait=True)
    completed = service.get_run(run["run_id"])

    assert completed["status"] == "completed"
    assert completed["adapter_id"] == "adapter-1"
    assert completed["last_checkpoint_id"]
    assert completed["best_checkpoint_id"] is None
    assert completed["metrics"]
    assert any(item["metric_type"] == "train" for item in completed["metrics"])
    assert adapter_repo.registered
    assert not completed["cancel_requested"]


def test_fake_trainer_saves_best_checkpoint_when_validation_improves(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    for index in range(12):
        _add_approved_sample(datasets, dataset["dataset_id"], index, chapter_id=f"chapter-{index // 3}")
    datasets.mark_ready(dataset["dataset_id"])
    version = datasets.freeze_dataset(
        dataset["dataset_id"],
        {"name": "with-val", "split": {"strategy": "group_by_chapter", "val_ratio": 0.25}},
    )
    recipe = datasets.recommend_recipe(
        version["dataset_version_id"],
        {"base_model_id": "qwen-local", "hardware": {"gpu_vram_gb": 8}},
    )
    recipe = datasets.confirm_recipe(recipe["recipe_id"])
    job_repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(job_repo)
    service = FineTuneService(
        datasets.db_path,
        output_root=tmp_path / "data" / "finetune",
        dataset_service=datasets,
        model_repository=FakeModelRepository(tmp_path),
        adapter_repository=FakeAdapterRepository(tmp_path),
        job_queue=queue,
        gpu_scheduler=GpuTaskScheduler(enabled=False),
        use_fake_trainer=True,
        dependency_checker=lambda method: ([], []),
    )

    run = service.create_run(
        {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "with-val",
            "start_immediately": True,
        }
    )
    queue.shutdown(wait=True)
    completed = service.get_run(run["run_id"])

    assert completed["best_checkpoint_id"]
    assert completed["best_val_loss"] is not None
    checkpoints = service.get_checkpoints(run["run_id"])
    assert any(item["is_best"] for item in checkpoints)
    assert any(item["is_last"] for item in checkpoints)
