from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from llm_studio.finetune import FineTuneService
from llm_studio.models.entities import LocalModel, ModelFormat, ModelStatus
from llm_studio.runtime.gpu_scheduler import GpuTaskScheduler
from tests.test_dataset_service import _dataset_seed


class FakeModelRepository:
    def __init__(self, root: Path):
        self.path = root / "models" / "qwen-local"
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "config.json").write_text('{"model_type":"qwen2"}', encoding="utf-8")
        (self.path / "model.safetensors").write_bytes(b"model")

    def get(self, model_id: str):
        if model_id != "qwen-local":
            from llm_studio.models.exceptions import InvalidModelPathError

            raise InvalidModelPathError(model_id)
        return LocalModel(
            id="qwen-local",
            display_name="qwen-local",
            path=self.path,
            format=ModelFormat.TRANSFORMERS,
            status=ModelStatus.READY,
            architecture="qwen2",
            parameter_count=1_500_000_000,
            quantization=None,
            context_length=4096,
            size_bytes=1,
            files=("config.json", "model.safetensors"),
        )


class FakeAdapterRepository:
    def __init__(self, root: Path):
        self.layout = SimpleNamespace(adapters_dir=root / "adapters")
        self.layout.adapters_dir.mkdir(parents=True, exist_ok=True)
        self.registered: list[Path] = []

    def list(self):
        return []

    def register_path(self, path: str):
        target = Path(path)
        self.registered.append(target)
        return SimpleNamespace(
            id=f"adapter-{len(self.registered)}",
            to_dict=lambda: {
                "id": f"adapter-{len(self.registered)}",
                "name": target.name,
                "path": str(target),
                "compatible": True,
                "compatibility_errors": [],
            },
        )


def frozen_dataset_and_recipe(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    datasets.mark_ready(dataset["dataset_id"])
    version = datasets.freeze_dataset(dataset["dataset_id"], {"name": "v1"})
    recipe = datasets.recommend_recipe(
        version["dataset_version_id"],
        {"base_model_id": "qwen-local", "hardware": {"gpu_vram_gb": 8}},
    )
    recipe = datasets.confirm_recipe(recipe["recipe_id"])
    return datasets, dataset, version, recipe


def fake_finetune_service(tmp_path, *, use_fake_trainer: bool = True):
    datasets, dataset, version, recipe = frozen_dataset_and_recipe(tmp_path)
    adapter_repo = FakeAdapterRepository(tmp_path)
    service = FineTuneService(
        datasets.db_path,
        output_root=tmp_path / "data" / "finetune",
        dataset_service=datasets,
        model_repository=FakeModelRepository(tmp_path),
        adapter_repository=adapter_repo,
        job_queue=SimpleNamespace(
            submit=lambda *args, **kwargs: SimpleNamespace(id="job-disabled"),
            cancel=lambda job_id: None,
        ),
        gpu_scheduler=GpuTaskScheduler(enabled=False),
        default_config={"use_fake_trainer": use_fake_trainer},
        use_fake_trainer=use_fake_trainer,
        dependency_checker=lambda method: ([], []),
    )
    return service, datasets, dataset, version, recipe, adapter_repo
