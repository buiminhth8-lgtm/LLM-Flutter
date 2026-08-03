"""Health check API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import HEALTH_CHECK_FAILED, api_error
from llm_studio.health import build_health_payload

router = APIRouter()


@router.get("/v1/health")
async def health():
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    try:
        return build_health_payload(get_api_state(), full=False)
    except Exception as exc:
        raise api_error(500, HEALTH_CHECK_FAILED, "健康检查失败。", request_id) from exc


@router.get("/v1/health/full")
async def health_full():
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    try:
        return build_health_payload(get_api_state(), full=True)
    except Exception as exc:
        raise api_error(500, HEALTH_CHECK_FAILED, "完整健康检查失败。", request_id) from exc
