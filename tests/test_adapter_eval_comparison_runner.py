from __future__ import annotations

import asyncio

from tests.adapter_eval_stage9_utils import adapter_eval_seed


def test_adapter_eval_runner_uses_same_prompt_and_params(tmp_path):
    seed = adapter_eval_seed(tmp_path)

    detail = asyncio.run(seed.service.run_case(seed.case["case_id"]))

    assert len(seed.runtime.calls) == 2
    base_call, adapter_call = seed.runtime.calls
    assert base_call["prompt"] == adapter_call["prompt"] == seed.case["prompt_rendered"]
    assert base_call["generation_params"] == adapter_call["generation_params"]
    assert base_call["adapter_id"] is None
    assert adapter_call["adapter_id"] == "adapter-1"
    results = {item["variant"]: item for item in detail["results"]}
    assert results["base"]["adapter_id"] is None
    assert results["adapter"]["adapter_id"] == "adapter-1"


def test_adapter_eval_single_side_failure_keeps_other_result(tmp_path):
    seed = adapter_eval_seed(tmp_path)
    seed.runtime.fail_adapter = True

    detail = asyncio.run(seed.service.run_case(seed.case["case_id"]))

    results = {item["variant"]: item for item in detail["results"]}
    assert results["base"]["status"] == "succeeded"
    assert results["adapter"]["status"] == "failed"
    assert results["adapter"]["error_code"]
