import json
import os
from pathlib import Path

import pytest

from llm_studio.models import ModelFormat, ModelStatus
from llm_studio.models.compatibility import assess_model_compatibility
from llm_studio.models.entities import LocalModel
from llm_studio.models.exceptions import InvalidModelPathError
from llm_studio.models.repository import LocalModelRepository
from llm_studio.models.scanner import ModelScanner
from llm_studio.models.storage import ModelStorageLayout, sanitize_local_name


def layout(tmp_path: Path) -> ModelStorageLayout:
    item = ModelStorageLayout(
        root_dir=tmp_path / "models",
        temp_dir=tmp_path / "downloads",
        metadata_cache=tmp_path / "model_index.json",
        trash_dir=tmp_path / "trash",
        adapters_dir=tmp_path / "adapters",
        benchmarks_dir=tmp_path / "benchmarks",
        jobs_dir=tmp_path / "jobs",
        diagnostics_dir=tmp_path / "diagnostics",
    )
    item.ensure()
    return item


def write_transformers_model(path: Path, *, weights: bool = True, params: str = "3B") -> None:
    path.mkdir(parents=True)
    (path / "config.json").write_text(
        json.dumps(
            {
                "architectures": ["QwenForCausalLM"],
                "model_type": "qwen2",
                "max_position_embeddings": 4096,
            }
        ),
        encoding="utf-8",
    )
    if weights:
        (path / f"model-{params}.safetensors").write_bytes(b"tiny")


def test_scan_transformers_complete_and_incomplete(tmp_path):
    store = layout(tmp_path)
    write_transformers_model(store.root_dir / "transformers" / "demo-3B", weights=True)
    write_transformers_model(store.root_dir / "transformers" / "broken-3B", weights=False)

    models = {model.display_name: model for model in ModelScanner(store).scan()}

    assert models["demo-3B"].format == ModelFormat.TRANSFORMERS
    assert models["demo-3B"].status == ModelStatus.READY
    assert models["broken-3B"].status == ModelStatus.INCOMPLETE


def test_scan_gguf_and_corrupt_config_isolated(tmp_path):
    store = layout(tmp_path)
    gguf = store.root_dir / "gguf" / "tiny-q4.gguf"
    gguf.write_bytes(b"GGUF" + (3).to_bytes(4, "little") + (1).to_bytes(8, "little") + (1).to_bytes(8, "little"))
    bad = store.root_dir / "transformers" / "bad-json-7B"
    bad.mkdir(parents=True)
    (bad / "config.json").write_text("{bad", encoding="utf-8")
    (bad / "model.safetensors").write_bytes(b"x")

    models = ModelScanner(store).scan()

    assert any(model.format == ModelFormat.GGUF for model in models)
    assert any(model.status == ModelStatus.CORRUPTED for model in models)


def test_symlink_not_followed_by_default(tmp_path):
    store = layout(tmp_path)
    target = tmp_path / "external-3B"
    write_transformers_model(target)
    link = store.root_dir / "transformers" / "link-3B"
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink not available")

    assert not ModelScanner(store).scan()


def test_compatibility_rtx5060_levels(tmp_path):
    base = dict(
        id="m",
        display_name="m",
        path=tmp_path,
        format=ModelFormat.TRANSFORMERS,
        status=ModelStatus.READY,
        architecture=None,
        context_length=4096,
        size_bytes=1,
        files=(),
    )

    report_3b = assess_model_compatibility(LocalModel(**base, parameter_count=3_000_000_000, quantization=None))
    report_7b = assess_model_compatibility(LocalModel(**base, parameter_count=7_000_000_000, quantization=None))
    report_7b_q4 = assess_model_compatibility(LocalModel(**base, parameter_count=7_000_000_000, quantization="q4_k_m"))
    report_14b = assess_model_compatibility(LocalModel(**base, parameter_count=14_000_000_000, quantization="q4"))
    report_32b = assess_model_compatibility(LocalModel(**base, parameter_count=32_000_000_000, quantization="q4"))

    assert report_3b.risk_level in {"safe", "warning"}
    assert report_7b.risk_level == "high-risk"
    assert report_7b_q4.risk_level == "warning"
    assert report_14b.risk_level == "high-risk"
    assert report_32b.risk_level == "unsupported"


def test_windows_local_name_rejects_reserved_and_traversal():
    with pytest.raises(InvalidModelPathError):
        sanitize_local_name("..")
    with pytest.raises(InvalidModelPathError):
        sanitize_local_name("CON")
    assert sanitize_local_name("Qwen/Qwen2.5") == "Qwen-Qwen2.5"


def test_register_external_model_persists_registry(tmp_path):
    store = layout(tmp_path)
    external = tmp_path / "external-3B"
    write_transformers_model(external)

    class Config:
        config_path = tmp_path / "config.yaml"

        def get(self, key, default=None):
            data = {
                "models": {
                    "root_dir": str(store.root_dir),
                    "temp_dir": str(store.temp_dir),
                    "metadata_cache": str(store.metadata_cache),
                    "adapters_dir": str(store.adapters_dir),
                    "allow_external_paths": True,
                    "follow_symlinks": False,
                    "minimum_free_space_gb": 0,
                },
                "storage": {
                    "trash_dir": str(store.trash_dir),
                    "benchmarks_dir": str(store.benchmarks_dir),
                    "jobs_dir": str(store.jobs_dir),
                    "diagnostics_dir": str(store.diagnostics_dir),
                },
                "external_models": [],
            }
            return data.get(key, default)

    repo = LocalModelRepository(Config(), store)
    model = repo.register_external(str(external))

    assert model.display_name == "external-3B"
    assert (store.metadata_cache.parent / "external_models.json").exists()
