from __future__ import annotations

import pytest

from llm_studio.adapter_evaluation import AdapterEvaluationService
from llm_studio.adapter_evaluation.errors import (
    AdapterEvalAdapterNotFoundError,
    AdapterEvalBaseModelNotFoundError,
    AdapterEvalFineTuneRunNotCompletedError,
)
from tests.adapter_eval_stage9_utils import (
    FakeAdapterRepository,
    FakeFineTuneService,
    FakeModelRepository,
    adapter_eval_seed,
)


def test_adapter_eval_create_session_and_case_freezes_prompt(tmp_path):
    seed = adapter_eval_seed(tmp_path)

    session = seed.service.get_session(seed.session["session_id"])
    case = seed.service.get_case(seed.case["case_id"])

    assert session["session_id"] == seed.session["session_id"]
    assert case["status"] == "ready"
    assert case["prompt_rendered"]
    assert case["prompt_hash"]
    assert case["context_snapshot"]["variables"]


def test_adapter_eval_create_session_missing_related_errors(tmp_path):
    seed = adapter_eval_seed(tmp_path)
    with pytest.raises(AdapterEvalBaseModelNotFoundError):
        seed.service.create_session(
            {"name": "bad", "base_model_id": "missing", "adapter_id": "adapter-1"}
        )
    with pytest.raises(AdapterEvalAdapterNotFoundError):
        seed.service.create_session(
            {"name": "bad", "base_model_id": "qwen-local", "adapter_id": "missing"}
        )

    service = AdapterEvaluationService(
        seed.service.db_path,
        novel_service=seed.service.novel_service,
        prompt_service=seed.service.prompt_service,
        context_service=seed.service.context_service,
        writing_service=seed.service.writing_service,
        revision_service=seed.service.revision_service,
        dataset_service=seed.service.dataset_service,
        finetune_service=FakeFineTuneService("failed"),
        model_repository=FakeModelRepository(tmp_path),
        adapter_repository=FakeAdapterRepository(),
        runtime_bridge=seed.runtime,
    )
    with pytest.raises(AdapterEvalFineTuneRunNotCompletedError):
        service.create_session(
            {
                "name": "bad",
                "base_model_id": "qwen-local",
                "adapter_id": "adapter-1",
                "finetune_run_id": "run-1",
            }
        )
