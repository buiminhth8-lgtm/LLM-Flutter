"""Novel Studio Stage 9 Adapter Evaluation API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.adapter_evaluation.errors import AdapterEvaluationError
from llm_studio.adapter_evaluation.schemas import (
    AdapterEvalCreateCaseRequest,
    AdapterEvalCreateRevisionRequest,
    AdapterEvalCreateSessionRequest,
    AdapterEvalRunSessionRequest,
    AdapterEvalScoreRequest,
    AdapterEvalUpdateSessionRequest,
)
from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import ADAPTER_EVAL_FEATURE_DISABLED, api_error
from llm_studio.features import is_adapter_evaluation_enabled

router = APIRouter(prefix="/v1/adapter-evaluations")


def _service(request: Request):
    state = get_api_state()
    if not is_adapter_evaluation_enabled(state.config):
        raise api_error(
            404,
            ADAPTER_EVAL_FEATURE_DISABLED,
            "Adapter Evaluation is disabled. Enable Novel Studio and adapter_evaluation.",
            getattr(request.state, "request_id", ""),
        )
    if state.adapter_evaluation_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Adapter Evaluation service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.adapter_evaluation_service


def _raise_adapter_eval_error(request: Request, exc: AdapterEvaluationError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
        details=exc.details,
    ) from exc


@router.get("/sessions")
async def list_adapter_eval_sessions(
    request: Request,
    status: str | None = None,
    project_id: str | None = None,
    adapter_id: str | None = None,
    finetune_run_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_sessions(
                status=status,
                project_id=project_id,
                adapter_id=adapter_id,
                finetune_run_id=finetune_run_id,
                limit=limit,
                offset=offset,
            )
        }
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/sessions")
async def create_adapter_eval_session(
    request: Request,
    body: AdapterEvalCreateSessionRequest,
):
    try:
        return _service(request).create_session(body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/sessions/{session_id}")
async def get_adapter_eval_session(request: Request, session_id: str):
    try:
        return _service(request).get_session(session_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.patch("/sessions/{session_id}")
async def update_adapter_eval_session(
    request: Request,
    session_id: str,
    body: AdapterEvalUpdateSessionRequest,
):
    try:
        return _service(request).update_session(session_id, body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.delete("/sessions/{session_id}")
async def archive_adapter_eval_session(request: Request, session_id: str):
    try:
        return _service(request).archive_session(session_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/sessions/{session_id}/cases")
async def list_adapter_eval_cases(
    request: Request,
    session_id: str,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_cases(
                session_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        }
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/sessions/{session_id}/cases")
async def create_adapter_eval_case(
    request: Request,
    session_id: str,
    body: AdapterEvalCreateCaseRequest,
):
    try:
        return _service(request).create_case(session_id, body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/sessions/{session_id}/run")
async def run_adapter_eval_session(
    request: Request,
    session_id: str,
    body: AdapterEvalRunSessionRequest | None = None,
):
    try:
        return await _service(request).run_session(session_id, body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/cases/{case_id}")
async def get_adapter_eval_case(request: Request, case_id: str):
    try:
        return _service(request).get_case(case_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/cases/{case_id}/prepare")
async def prepare_adapter_eval_case(request: Request, case_id: str):
    try:
        return _service(request).prepare_case(case_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/cases/{case_id}/run")
async def run_adapter_eval_case(request: Request, case_id: str):
    try:
        return await _service(request).run_case(case_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/cases/{case_id}/score")
async def score_adapter_eval_case(
    request: Request,
    case_id: str,
    body: AdapterEvalScoreRequest,
):
    try:
        return _service(request).score_case(case_id, body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/cases/{case_id}/score")
async def get_adapter_eval_score(request: Request, case_id: str):
    try:
        return _service(request).get_score(case_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/sessions/{session_id}/report")
async def generate_adapter_eval_report(request: Request, session_id: str):
    try:
        return _service(request).generate_report(session_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/sessions/{session_id}/reports")
async def list_adapter_eval_reports(
    request: Request,
    session_id: str,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {"data": _service(request).list_reports(session_id, limit=limit, offset=offset)}
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.get("/reports/{report_id}")
async def get_adapter_eval_report(request: Request, report_id: str):
    try:
        return _service(request).get_report(report_id)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)


@router.post("/results/{result_id}/create-revision")
async def create_revision_from_adapter_eval_result(
    request: Request,
    result_id: str,
    body: AdapterEvalCreateRevisionRequest,
):
    try:
        return _service(request).create_revision_from_result(result_id, body)
    except AdapterEvaluationError as exc:
        _raise_adapter_eval_error(request, exc)
