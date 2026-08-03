from __future__ import annotations

from llm_studio.api.deps import get_api_state
from tests.adapter_eval_stage9_utils import (
    FakeAdapterEvalRuntimeBridge,
    FakeAdapterRepository,
    FakeFineTuneService,
    FakeModelRepository,
)
from tests.test_context_api import create_context_fixture
from tests.test_novel_projects_api import _client
from tests.test_prompt_templates_api import _template_body


def _patch_adapter_eval_state(tmp_path):
    state = get_api_state()
    runtime = FakeAdapterEvalRuntimeBridge()
    state.adapter_evaluation_service.model_repository = FakeModelRepository(tmp_path)
    state.adapter_evaluation_service.adapter_repository = FakeAdapterRepository()
    state.adapter_evaluation_service.finetune_service = FakeFineTuneService()
    state.adapter_evaluation_service.runner.runtime_bridge = runtime
    return runtime


def test_adapter_eval_api_full_smoke(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    runtime = _patch_adapter_eval_state(tmp_path)
    fixture = create_context_fixture(client)
    template = client.post("/v1/prompts/templates", json=_template_body()).json()
    project = fixture["project"]
    chapter = fixture["chapter"]

    session = client.post(
        "/v1/adapter-evaluations/sessions",
        json={
            "name": "api compare",
            "project_id": project["id"],
            "finetune_run_id": "run-1",
            "base_model_id": "qwen-local",
            "adapter_id": "adapter-1",
        },
    )
    assert session.status_code == 200
    session_id = session.json()["session_id"]
    case = client.post(
        f"/v1/adapter-evaluations/sessions/{session_id}/cases",
        json={
            "title": "case",
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "mode": "chapter_generate",
            "user_variables": {"current_chapter_goal": "compare"},
            "generation_params": {"max_tokens": 64},
            "target_length": {"unit": "chars", "min": 1, "max": 80},
        },
    )
    assert case.status_code == 200
    case_id = case.json()["case_id"]

    detail = client.post(f"/v1/adapter-evaluations/cases/{case_id}/run")
    assert detail.status_code == 200
    assert len(runtime.calls) == 2
    score = client.post(
        f"/v1/adapter-evaluations/cases/{case_id}/score",
        json={"winner": "adapter", "base_score": 3, "adapter_score": 4},
    )
    assert score.status_code == 200
    report = client.post(f"/v1/adapter-evaluations/sessions/{session_id}/report")
    assert report.status_code == 200
    adapter_result = next(
        item for item in detail.json()["results"] if item["variant"] == "adapter"
    )
    revision = client.post(
        f"/v1/adapter-evaluations/results/{adapter_result['result_id']}/create-revision",
        json={
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "edit_tags": ["style_unify"],
            "user_score": 4,
        },
    )
    assert revision.status_code == 200
    assert revision.json()["source"] == "adapter_evaluation"
    assert client.get("/v1/adapter-evaluations/sessions").json()["data"]
    assert client.get(f"/v1/adapter-evaluations/sessions/{session_id}").json()["cases"]


def test_adapter_eval_api_missing_adapter_stable_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _patch_adapter_eval_state(tmp_path)
    response = client.post(
        "/v1/adapter-evaluations/sessions",
        json={"name": "bad", "base_model_id": "qwen-local", "adapter_id": "missing"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ADAPTER_EVAL_ADAPTER_NOT_FOUND"
