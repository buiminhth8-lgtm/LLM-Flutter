from __future__ import annotations

from tests.test_dataset_service import _dataset_seed


def test_dataset_version_detail_lists_immutable_samples(tmp_path):
    datasets, _, dataset, revision, *_ = _dataset_seed(tmp_path)
    sample = datasets.create_sample_from_revision(dataset["dataset_id"], revision["revision_id"])
    datasets.approve_sample(sample["sample_id"])
    datasets.mark_ready(dataset["dataset_id"])
    version = datasets.freeze_dataset(dataset["dataset_id"], {"name": "version"})

    detail = datasets.get_version(version["dataset_version_id"])

    assert detail["dataset_version_id"] == version["dataset_version_id"]
    assert detail["samples"]
    assert detail["samples"][0]["split"] == "train"
    assert datasets.list_versions(dataset["dataset_id"])[0]["version"] == 1
