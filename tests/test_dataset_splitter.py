from __future__ import annotations

from llm_studio.datasets.splitter import DatasetSplitter


def _entry(sample_id: str, chapter_id: str):
    return {
        "sample": {
            "sample_id": sample_id,
            "chapter_id": chapter_id,
            "content_hash": sample_id,
        },
        "warnings": [],
    }


def test_group_by_chapter_keeps_chapter_in_one_split():
    entries = [_entry(f"s{i}", f"chapter-{i // 3}") for i in range(15)]
    result = DatasetSplitter().split(
        entries,
        strategy="group_by_chapter",
        val_ratio=0.2,
        seed=42,
    )
    split_by_chapter = {}
    for split_name in ("train", "val"):
        for entry in result[split_name]:
            chapter = entry["sample"]["chapter_id"]
            split_by_chapter.setdefault(chapter, split_name)
            assert split_by_chapter[chapter] == split_name
    assert result["val"]


def test_small_dataset_uses_no_validation_warning():
    result = DatasetSplitter().split([_entry("s1", "c1")])
    assert len(result["train"]) == 1
    assert result["val"] == []
    assert any(warning["code"] == "DATASET_NO_VALIDATION_SPLIT" for warning in result["warnings"])
