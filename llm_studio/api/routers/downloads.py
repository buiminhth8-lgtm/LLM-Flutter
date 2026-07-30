"""Download lifecycle API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import (
    DOWNLOAD_ALREADY_RUNNING,
    DOWNLOAD_CANCEL_NOT_ALLOWED,
    DOWNLOAD_CANCEL_REQUESTED,
    DOWNLOAD_FAILED,
    DOWNLOAD_NOT_FOUND,
    DOWNLOAD_RECORD_DELETE_NOT_ALLOWED,
    DOWNLOAD_RETRY_NOT_ALLOWED,
    api_error,
)
from llm_studio.downloads import DownloadRequest, DownloadTaskState
from llm_studio.downloads.exceptions import (
    DownloadAlreadyRunningError,
    DownloadCancelNotAllowedError,
    DownloadError,
    DownloadRetryNotAllowedError,
)
from llm_studio.jobs import JobType
from llm_studio.jobs.entities import TERMINAL_JOB_STATUSES
from llm_studio.jobs.exceptions import JobNotFoundError

router = APIRouter()


class DownloadModelRequest(BaseModel):
    repo_id: str
    provider: str | None = None
    revision: str | None = None
    allow_patterns: list[str] | None = None
    ignore_patterns: list[str] | None = None
    local_name: str | None = None
    local_files_only: bool = False


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


@router.post("/v1/downloads")
async def create_download(req: DownloadModelRequest):
    state = get_api_state()
    assert state.download_manager is not None
    try:
        job = state.download_manager.create_download(
            DownloadRequest(
                repo_id=req.repo_id,
                provider=req.provider,
                revision=req.revision,
                allow_patterns=tuple(req.allow_patterns) if req.allow_patterns else None,
                ignore_patterns=tuple(req.ignore_patterns) if req.ignore_patterns else None,
                local_name=req.local_name,
                token=None,
                local_files_only=req.local_files_only,
            )
        )
    except DownloadAlreadyRunningError as exc:
        raise api_error(409, DOWNLOAD_ALREADY_RUNNING, str(exc), _request_id()) from exc
    except DownloadError as exc:
        raise api_error(400, getattr(exc, "error_code", DOWNLOAD_FAILED), str(exc), _request_id()) from exc
    return {"job_id": job.id}


@router.get("/v1/downloads")
async def list_downloads():
    state = get_api_state()
    assert state.job_repository is not None
    return {
        "data": [
            DownloadTaskState.from_job(job).to_dict()
            for job in state.job_repository.list(limit=100)
            if job.type == JobType.MODEL_DOWNLOAD.value
        ]
    }


@router.get("/v1/downloads/{job_id}")
async def get_download(job_id: str):
    state = get_api_state()
    assert state.job_repository is not None
    try:
        job = state.job_repository.get(job_id)
    except JobNotFoundError as exc:
        raise api_error(404, DOWNLOAD_NOT_FOUND, "下载任务不存在。", _request_id()) from exc
    return DownloadTaskState.from_job(job).to_dict()


@router.post("/v1/downloads/{job_id}/cancel")
async def cancel_download(job_id: str):
    state = get_api_state()
    assert state.download_manager is not None
    try:
        job = state.download_manager.cancel_job(job_id)
    except JobNotFoundError as exc:
        raise api_error(404, DOWNLOAD_NOT_FOUND, "下载任务不存在。", _request_id()) from exc
    except DownloadCancelNotAllowedError as exc:
        raise api_error(409, DOWNLOAD_CANCEL_NOT_ALLOWED, str(exc), _request_id()) from exc
    data = DownloadTaskState.from_job(job).to_dict()
    data["error_code"] = data["error_code"] or DOWNLOAD_CANCEL_REQUESTED
    data["cancel_semantics"] = "取消请求已提交；当前网络传输步骤可能结束后才会停止，重试会复用 ModelScope 缓存。"
    return data


@router.post("/v1/downloads/{job_id}/retry")
async def retry_download(job_id: str):
    state = get_api_state()
    assert state.download_manager is not None and state.job_repository is not None
    try:
        retried = state.download_manager.retry_interrupted(state.job_repository.get(job_id))
    except JobNotFoundError as exc:
        raise api_error(404, DOWNLOAD_NOT_FOUND, "下载任务不存在。", _request_id()) from exc
    except DownloadRetryNotAllowedError as exc:
        raise api_error(409, DOWNLOAD_RETRY_NOT_ALLOWED, str(exc), _request_id()) from exc
    return {
        "job_id": retried.id,
        "resume_supported": True,
        "message": "Retry reuses the ModelScope cache; strict pause/resume is not claimed.",
    }


@router.delete("/v1/downloads/{job_id}")
async def delete_download_record(job_id: str):
    state = get_api_state()
    assert state.job_repository is not None
    try:
        job = state.job_repository.get(job_id)
    except JobNotFoundError as exc:
        raise api_error(404, DOWNLOAD_NOT_FOUND, "下载记录不存在。", _request_id()) from exc
    if job.type != JobType.MODEL_DOWNLOAD.value:
        raise api_error(404, DOWNLOAD_NOT_FOUND, "下载记录不存在。", _request_id())
    if job.status not in TERMINAL_JOB_STATUSES:
        raise api_error(
            409,
            DOWNLOAD_RECORD_DELETE_NOT_ALLOWED,
            "下载任务仍在运行，不能删除记录；请先取消或等待任务结束。",
            _request_id(),
        )
    state.job_repository.delete(job_id)
    return {"status": "deleted", "job_id": job_id}
