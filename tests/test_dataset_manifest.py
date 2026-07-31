from __future__ import annotations

from tests.test_dataset_service import _dataset_seed


def test_manifest_json_is_read_from_relative_safe_path(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    datasets.mark_ready(dataset["dataset_id"])
    version = datasets.freeze_dataset(dataset["dataset_id"], {"name": "manifest"})

    manifest = datasets.get_manifest(version["dataset_version_id"])

    assert manifest["dataset_id"] == dataset["dataset_id"]
    assert manifest["format"] == "sft_jsonl"
    assert "hashes" in manifest
    assert "api_key" not in str(manifest).lower()
    assert ":\\" not in version["manifest_path"]
