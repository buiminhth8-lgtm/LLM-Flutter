"""Version API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import VERSION_NOT_AVAILABLE, api_error
from llm_studio.version import get_version_payload

router = APIRouter()


@router.get("/v1/version")
async def version_info():
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    try:
        return get_version_payload(get_api_state().config)
    except Exception as exc:
        raise api_error(
            500,
            VERSION_NOT_AVAILABLE,
            "版本信息不可用，请查看后端日志。",
            request_id,
        ) from exc
