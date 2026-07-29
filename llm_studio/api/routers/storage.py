"""Storage API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import STORAGE_CLEANUP_FAILED, api_error
from llm_studio.execution import run_blocking_io
from llm_studio.storage import CacheManager, collect_disk_usage

router = APIRouter()


class StorageCleanupRequest(BaseModel):
    categories: list[str] | None = None


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


@router.get("/v1/storage")
async def storage_status():
    state = get_api_state()
    assert state.config is not None
    request_id = _request_id()
    try:
        items = await run_blocking_io(collect_disk_usage, state.config)
    except Exception as exc:
        raise api_error(500, STORAGE_CLEANUP_FAILED, "磁盘空间统计失败。", request_id) from exc
    return {"data": [item.to_dict() for item in items]}


@router.post("/v1/storage/cleanup/preview")
async def cleanup_storage_preview(req: StorageCleanupRequest | None = None):
    state = get_api_state()
    assert state.config is not None
    request_id = _request_id()
    manager = CacheManager(state.config)
    categories = set(req.categories) if req and req.categories else None
    try:
        items = await run_blocking_io(manager.preview_cleanup, categories)
    except Exception as exc:
        raise api_error(500, STORAGE_CLEANUP_FAILED, "清理预览生成失败。", request_id) from exc
    return {
        "items": [item.to_dict() for item in items],
        "total_size_bytes": sum(item.size_bytes for item in items),
    }


@router.post("/v1/storage/cleanup")
async def cleanup_storage(req: StorageCleanupRequest | None = None):
    state = get_api_state()
    assert state.config is not None
    request_id = _request_id()
    manager = CacheManager(state.config)
    categories = set(req.categories) if req and req.categories else None
    try:
        items = await run_blocking_io(manager.preview_cleanup, categories)
        return await run_blocking_io(manager.cleanup_preview_items, items)
    except Exception as exc:
        raise api_error(500, STORAGE_CLEANUP_FAILED, "存储清理失败。", request_id) from exc
