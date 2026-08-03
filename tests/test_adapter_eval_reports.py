from __future__ import annotations

import asyncio

from tests.adapter_eval_stage9_utils import adapter_eval_seed


def test_adapter_eval_report_counts_scores_and_recommendation(tmp_path):
    seed = adapter_eval_seed(tmp_path)
    detail = asyncio.run(seed.service.run_case(seed.case["case_id"]))
    seed.service.score_case(
        detail["case_id"],
        {
            "winner": "adapter",
            "base_score": 3,
            "adapter_score": 5,
            "dimensions": {"style": {"base": 3, "adapter": 5}},
            "notes": "adapter better",
        },
    )

    report = seed.service.generate_report(seed.session["session_id"])

    body = report["report"]
    assert body["adapter_win_count"] == 1
    assert body["base_win_count"] == 0
    assert body["average_base_score"] == 3
    assert body["average_adapter_score"] == 5
    assert body["recommendation"] == "adapter_candidate"


def test_adapter_eval_report_insufficient_scores(tmp_path):
    seed = adapter_eval_seed(tmp_path)

    report = seed.service.generate_report(seed.session["session_id"])

    assert report["report"]["recommendation"] == "insufficient_scores"
