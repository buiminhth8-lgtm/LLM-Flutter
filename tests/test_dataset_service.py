from __future__ import annotations

import asyncio

import pytest

from llm_studio.datasets import DatasetService
from llm_studio.datasets.errors import (
    DatasetNoApprovedSamplesError,
    DatasetRevisionNotAcceptedError,
    DatasetRevisionNotFoundError,
    DatasetSampleDuplicateError,
)
from llm_studio.revisions import RevisionService
from tests.test_writing_service import _seed


def _dataset_seed(tmp_path, *, accepted=True, approved=True, edited_text="human edited"):
    novels, prompts, _, writing, _, project, chapter, _, request = _seed(tmp_path)
    generation = asyncio.run(writing.generate(request))
    revisions = RevisionService(
        writing.db_path,
        novel_service=novels,
        writing_service=writing,
    )
    revision = revisions.create_from_generation(
        {
            "generation_id": generation["generation_id"],
            "edited_text": edited_text,
            "user_score": 4,
            "accepted_for_dataset": accepted,
        }
    )
    if approved:
        revision = revisions.approve_revision(revision["revision_id"])
    datasets = DatasetService(
        writing.db_path,
        export_root=tmp_path / "data" / "datasets",
        novel_service=novels,
        revision_service=revisions,
        writing_service=writing,
        prompt_service=prompts,
    )
    dataset = datasets.create_dataset({"name": "Stage 6", "project_id": project["id"]})
    return datasets, revisions, dataset, revision, project, chapter


def test_dataset_crud_and_sample_lifecycle(tmp_path):
    datasets, _, dataset, revision, project, _ = _dataset_seed(tmp_path)

    listed = datasets.list_datasets(project_id=project["id"])
    assert listed[0]["dataset_id"] == dataset["dataset_id"]

    patched = datasets.update_dataset(
        dataset["dataset_id"],
        {"description": "draft samples", "status": "reviewing"},
    )
    assert patched["status"] == "reviewing"

    sample = datasets.create_sample_from_revision(
        dataset["dataset_id"],
        revision["revision_id"],
    )
    assert sample["sample_type"] == "sft"
    assert sample["instruction"]
    assert sample["input"]
    assert sample["output"] == "human edited"
    assert sample["status"] == "pending"
    assert datasets.get_dataset(dataset["dataset_id"])["sample_count"] == 1

    with pytest.raises(DatasetSampleDuplicateError):
        datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])

    approved = datasets.approve_sample(sample["sample_id"])
    assert approved["status"] == "approved"
    assert datasets.get_dataset(dataset["dataset_id"])["approved_sample_count"] == 1

    rejected = datasets.reject_sample(sample["sample_id"], reason="bad")
    assert rejected["status"] == "rejected"
    assert "bad" in rejected["review_notes"]
    removed = datasets.remove_sample(sample["sample_id"])
    assert removed["status"] == "archived"

    archived_dataset = datasets.archive_dataset(dataset["dataset_id"])
    assert archived_dataset["status"] == "archived"


def test_revision_acceptance_and_missing_errors(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path, accepted=False)

    with pytest.raises(DatasetRevisionNotAcceptedError):
        datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])

    with pytest.raises(DatasetRevisionNotFoundError):
        datasets.create_sample_from_revision(dataset["dataset_id"], "missing")


def test_bulk_create_and_export_jsonl(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)

    result = datasets.bulk_create_samples_from_revisions(
        dataset["dataset_id"],
        {
            "project_id": revision["project_id"],
            "min_score": 4,
            "tags": [],
            "accepted_for_dataset": True,
            "revision_status": "approved",
            "sample_type": "sft",
            "limit": 10,
        },
    )
    assert result["created_count"] == 1
    sample = result["samples"][0]

    with pytest.raises(DatasetNoApprovedSamplesError):
        datasets.export_dataset(dataset["dataset_id"], {"format": "sft_jsonl"})

    datasets.approve_sample(sample["sample_id"])
    export = datasets.export_dataset(
        dataset["dataset_id"],
        {"format": "sft_jsonl", "file_name": "draft_sft.jsonl"},
    )
    assert export["sample_count"] == 1
    assert export["export_hash"]
    assert export["export_path"].startswith("datasets/")
    assert datasets.list_exports(dataset["dataset_id"])[0]["export_id"] == export["export_id"]
