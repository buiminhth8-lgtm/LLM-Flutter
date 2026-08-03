"""Novel Studio Stage 11 Evaluation Center API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import EVALUATION_FEATURE_DISABLED, api_error
from llm_studio.evaluation.errors import EvaluationError
from llm_studio.evaluation.schemas import (
    CreateEvaluationRunRequest,
    ManualEvaluationScoreRequest,
    UpdateFindingRequest,
)
from llm_studio.features import is_evaluation_center_enabled

router = APIRouter(prefix="/v1/evaluation")


def _service(request: Request):
    state = get_api_state()
    if not is_evaluation_center_enabled(state.config):
        raise api_error(
            404,
            EVALUATION_FEATURE_DISABLED,
            "Evaluation Center is disabled. Enable novel_studio and evaluation_center.",
            getattr(request.state, "request_id", ""),
        )
    if state.evaluation_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Evaluation service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.evaluation_service


def _raise_evaluation_error(request: Request, exc: EvaluationError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
    ) from exc


@router.get("/runs")
async def list_evaluation_runs(
    request: Request,
    project_id: str | None = None,
    target_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_runs(
                project_id=project_id,
                target_type=target_type,
                status=status,
                limit=limit,
                offset=offset,
            )
        }
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/runs")
async def create_evaluation_run(request: Request, body: CreateEvaluationRunRequest):
    try:
        return await _service(request).create_run(body)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/run-sync")
async def run_evaluation_sync(request: Request, body: CreateEvaluationRunRequest):
    try:
        return await _service(request).run_sync(body)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/runs/{run_id}")
async def get_evaluation_run(request: Request, run_id: str):
    try:
        return _service(request).get_run(run_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/runs/{run_id}/start")
async def start_evaluation_run(request: Request, run_id: str):
    try:
        return await _service(request).start_run(run_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/runs/{run_id}/cancel")
async def cancel_evaluation_run(request: Request, run_id: str):
    try:
        return _service(request).cancel_run(run_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.delete("/runs/{run_id}")
async def archive_evaluation_run(request: Request, run_id: str):
    try:
        return _service(request).archive_run(run_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/runs/{run_id}/findings")
async def get_evaluation_findings(
    request: Request,
    run_id: str,
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).get_findings(
                run_id,
                category=category,
                severity=severity,
                status=status,
                limit=limit,
                offset=offset,
            )
        }
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.patch("/findings/{finding_id}")
async def update_evaluation_finding(
    request: Request,
    finding_id: str,
    body: UpdateFindingRequest,
):
    try:
        return _service(request).update_finding_status(finding_id, body.status)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/runs/{run_id}/metrics")
async def get_evaluation_metrics(request: Request, run_id: str):
    try:
        return {"data": _service(request).get_metrics(run_id)}
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/runs/{run_id}/manual-score")
async def add_evaluation_manual_score(
    request: Request,
    run_id: str,
    body: ManualEvaluationScoreRequest,
):
    try:
        return _service(request).add_manual_score(run_id, body)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/runs/{run_id}/manual-scores")
async def list_evaluation_manual_scores(request: Request, run_id: str):
    try:
        return {"data": _service(request).list_manual_scores(run_id)}
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.post("/runs/{run_id}/report")
async def generate_evaluation_report(request: Request, run_id: str):
    try:
        return _service(request).generate_report(run_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/runs/{run_id}/reports")
async def list_evaluation_reports(
    request: Request,
    run_id: str,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {"data": _service(request).list_reports(run_id, limit=limit, offset=offset)}
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)


@router.get("/reports/{report_id}")
async def get_evaluation_report(request: Request, report_id: str):
    try:
        return _service(request).get_report(report_id)
    except EvaluationError as exc:
        _raise_evaluation_error(request, exc)
