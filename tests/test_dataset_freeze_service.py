from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from llm_studio.datasets.errors import (
    DatasetFreezeNoApprovedSamplesError,
    DatasetFreezeNotReadyError,
)
from tests.test_dataset_service import _dataset_seed


def _hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _add_approved_sample(datasets, dataset_id: str, index: int, *, chapter_id: str = "chapter-extra"):
    output = f"人工修订正文 {index}"
    return datasets.records.create_sample(
        dataset_id,
        {
            "project_id": "project-extra",
            "chapter_id": chapter_id,
            "revision_id": f"revision-extra-{index}",
            "generation_id": f"generation-extra-{index}",
            "sample_type": "sft",
            "instruction": "根据设定写一段小说。",
            "input": f"章节目标 {index}",
            "output": output,
            "metadata": {},
            "source_hash": _hash("source", str(index)),
            "content_hash": _hash("sft", "根据设定写一段小说。", f"章节目标 {index}", output),
            "quality_score": 4,
            "status": "approved",
        },
    )


def test_ready_dataset_can_freeze_and_write_manifest(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    for index in range(12):
        _add_approved_sample(
            datasets,
            dataset["dataset_id"],
            index,
            chapter_id=f"chapter-{index // 3}",
        )
    datasets.mark_ready(dataset["dataset_id"])

    version = datasets.freeze_dataset(
        dataset["dataset_id"],
        {
            "name": "Stage 7 v1",
            "split": {"strategy": "group_by_chapter", "val_ratio": 0.2, "seed": 7},
            "dedupe": {"exact_hash": True, "near_duplicate": False},
            "export_format": "sft_jsonl",
        },
    )

    assert version["version"] == 1
    assert version["status"] == "frozen"
    assert version["train_sample_count"] > 0
    assert version["val_sample_count"] > 0
    assert ":\\" not in version["manifest_path"]
    manifest = datasets.get_manifest(version["dataset_version_id"])
    assert manifest["dataset_version_id"] == version["dataset_version_id"]
    assert manifest["hashes"]["content_hash"] == version["content_hash"]
    train_file = tmp_path / "data" / version["train_path"]
    assert train_file.exists()
    assert json.loads(train_file.read_text(encoding="utf-8").splitlines()[0])["output"]


def test_freeze_requires_ready_or_dirty_and_approved_samples(tmp_path):
    datasets, _, dataset, *_ = _dataset_seed(tmp_path)
    with pytest.raises(DatasetFreezeNotReadyError):
        datasets.freeze_dataset(dataset["dataset_id"], {"name": "bad"})
    datasets.mark_ready(dataset["dataset_id"])
    with pytest.raises(DatasetFreezeNoApprovedSamplesError):
        datasets.freeze_dataset(dataset["dataset_id"], {"name": "empty"})


def test_dirty_dataset_can_freeze_again_without_modifying_old_version(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    sample = datasets.approve_sample(sample["sample_id"])
    datasets.mark_ready(dataset["dataset_id"])
    first = datasets.freeze_dataset(dataset["dataset_id"], {"name": "v1"})

    updated = datasets.update_sample(
        sample["sample_id"],
        {"output": "人工修订正文 changed"},
    )
    assert updated["status"] == "approved"
    assert datasets.records.get_dataset(dataset["dataset_id"])["status"] == "dirty"
    second = datasets.freeze_dataset(dataset["dataset_id"], {"name": "v2"})

    assert second["version"] == 2
    assert datasets.records.get_dataset_version(first["dataset_version_id"])["content_hash"] == first["content_hash"]
    assert second["content_hash"] != first["content_hash"]


def test_confirm_recipe_does_not_create_finetune_runs(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    datasets.mark_ready(dataset["dataset_id"])
    version = datasets.freeze_dataset(dataset["dataset_id"], {"name": "v1"})
    recipe = datasets.recommend_recipe(
        version["dataset_version_id"],
        {"base_model_id": "qwen-local", "hardware": {"gpu_vram_gb": 8}},
    )
    confirmed = datasets.confirm_recipe(recipe["recipe_id"])
    assert confirmed["status"] == "confirmed"
    with sqlite3.connect(datasets.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "finetune_runs" not in tables
