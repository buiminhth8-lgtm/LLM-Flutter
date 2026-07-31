from __future__ import annotations

from llm_studio.datasets.dedupe import DatasetDedupeService


def test_exact_duplicate_is_excluded_and_near_duplicate_warns():
    samples = [
        {
            "sample_id": "sample-1",
            "content_hash": "same",
            "instruction": "写作",
            "input": "黑市",
            "output": "夜色沉入旧城。",
        },
        {
            "sample_id": "sample-2",
            "content_hash": "same",
            "instruction": "写作",
            "input": "黑市",
            "output": "夜色沉入旧城。",
        },
        {
            "sample_id": "sample-3",
            "content_hash": "other",
            "instruction": "写作",
            "input": "黑市",
            "output": "夜色沉入旧城",
        },
    ]
    result = DatasetDedupeService().dedupe(samples, near_duplicate_threshold=0.9)
    assert len(result["kept"]) == 2
    assert len(result["excluded"]) == 1
    assert result["excluded"][0]["warnings"][0]["code"] == "DATASET_EXACT_DUPLICATE"
    assert result["kept"][1]["warnings"][0]["code"] == "DATASET_NEAR_DUPLICATE"
