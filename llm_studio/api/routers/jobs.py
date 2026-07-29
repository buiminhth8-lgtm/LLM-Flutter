"""Job API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import JOB_CANCEL_NOT_ALLOWED, JOB_NOT_FOUND, api_error
from llm_studio.jobs.exceptions import JobCancelNotAllowedError, JobNotFoundError

router = APIRouter()


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


@router.get("/v1/jobs")
async def list_jobs(limit: int = 50, offset: int = 0):
    state = get_api_state()
    assert state.job_repository is not None
    return {"data": [job.to_public_dict() for job in state.job_repository.list(limit=limit, offset=offset)]}


@router.get("/v1/jobs/{job_id}")
async def get_job(job_id: str):
    state = get_api_state()
    assert state.job_repository is not None
    try:
        return state.job_repository.get(job_id).to_public_dict()
    except JobNotFoundError as exc:
        raise api_error(404, JOB_NOT_FOUND, "任务不存在。", _request_id()) from exc


@router.post("/v1/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    state = get_api_state()
    assert state.job_queue is not None
    try:
        return state.job_queue.cancel(job_id).to_public_dict()
    except JobNotFoundError as exc:
        raise api_error(404, JOB_NOT_FOUND, "任务不存在。", _request_id()) from exc
    except JobCancelNotAllowedError as exc:
        raise api_error(409, JOB_CANCEL_NOT_ALLOWED, str(exc), _request_id()) from exc
