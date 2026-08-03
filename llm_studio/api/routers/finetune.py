"""Novel Studio Stage 8 Fine-tune Center API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import FINETUNE_FEATURE_DISABLED, api_error
from llm_studio.features import is_finetune_center_enabled
from llm_studio.finetune.errors import FineTuneError
from llm_studio.finetune.schemas import (
    CreateFineTuneRunRequest,
    FineTunePreflightRequest,
    ResumeFineTuneRunRequest,
)

router = APIRouter(prefix="/v1/finetune")


def _service(request: Request):
    state = get_api_state()
    if not is_finetune_center_enabled(state.config):
        raise api_error(
            404,
            FINETUNE_FEATURE_DISABLED,
            "Fine-tune Center is disabled. Enable Novel Studio and finetune_center.",
            getattr(request.state, "request_id", ""),
        )
    if state.finetune_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Fine-tune service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.finetune_service


def _raise_finetune_error(request: Request, exc: FineTuneError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
        details=exc.details,
    ) from exc


@router.post("/preflight")
async def preflight_finetune(request: Request, body: FineTunePreflightRequest):
    try:
        return _service(request).preflight_public(body)
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.post("/runs")
async def create_finetune_run(request: Request, body: CreateFineTuneRunRequest):
    try:
        return _service(request).create_run(body)
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.get("/runs")
async def list_finetune_runs(
    request: Request,
    status: str | None = None,
    dataset_version_id: str | None = None,
    base_model_id: str | None = None,
    method: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_runs(
                status=status,
                dataset_version_id=dataset_version_id,
                base_model_id=base_model_id,
                method=method,
                limit=limit,
                offset=offset,
            )
        }
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.get("/runs/{run_id}")
async def get_finetune_run(request: Request, run_id: str):
    try:
        return _service(request).get_run(run_id)
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.post("/runs/{run_id}/start")
async def start_finetune_run(request: Request, run_id: str):
    try:
        return _service(request).start_run(run_id)
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.post("/runs/{run_id}/cancel")
async def cancel_finetune_run(request: Request, run_id: str):
    try:
        return _service(request).cancel_run(run_id)
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.post("/runs/{run_id}/resume")
async def resume_finetune_run(
    request: Request,
    run_id: str,
    body: ResumeFineTuneRunRequest | None = None,
):
    try:
        return _service(request).resume_run(
            run_id,
            checkpoint_id=body.checkpoint_id if body else None,
        )
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.get("/runs/{run_id}/metrics")
async def get_finetune_metrics(
    request: Request,
    run_id: str,
    limit: int = 500,
    offset: int = 0,
):
    try:
        return {"data": _service(request).get_metrics(run_id, limit=limit, offset=offset)}
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.get("/runs/{run_id}/logs")
async def get_finetune_logs(
    request: Request,
    run_id: str,
    level: str | None = None,
    since: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).get_logs(
                run_id,
                level=level,
                since=since,
                limit=limit,
                offset=offset,
            )
        }
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)


@router.get("/runs/{run_id}/checkpoints")
async def get_finetune_checkpoints(request: Request, run_id: str):
    try:
        return {"data": _service(request).get_checkpoints(run_id)}
    except FineTuneError as exc:
        _raise_finetune_error(request, exc)
