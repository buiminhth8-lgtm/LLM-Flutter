from __future__ import annotations

import asyncio
import sqlite3

from tests.adapter_eval_stage9_utils import adapter_eval_seed


def test_adapter_eval_result_can_create_revision_without_training_samples(tmp_path):
    seed = adapter_eval_seed(tmp_path)
    detail = asyncio.run(seed.service.run_case(seed.case["case_id"]))
    adapter_result = next(item for item in detail["results"] if item["variant"] == "adapter")

    revision = seed.service.create_revision_from_result(
        adapter_result["result_id"],
        {
            "project_id": seed.project["id"],
            "chapter_id": seed.chapter["id"],
            "edit_tags": ["style_unify"],
            "user_score": 4,
            "quality_notes": "adapter better",
        },
    )

    assert revision["source"] == "adapter_evaluation"
    assert revision["accepted_for_dataset"] is False
    assert revision["edited_text"] == adapter_result["output_text"]
    with sqlite3.connect(seed.service.db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM training_samples").fetchone()[0]
    assert count == 0
