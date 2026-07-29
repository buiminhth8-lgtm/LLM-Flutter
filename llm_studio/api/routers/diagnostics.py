"""Diagnostics API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import DIAGNOSTICS_EXPORT_FAILED, api_error
from llm_studio.execution import run_blocking_io

router = APIRouter()


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


@router.post("/v1/diagnostics/export")
async def diagnostics_export():
    state = get_api_state()
    assert state.config is not None
    assert state.diagnostics_exporter is not None
    request_id = _request_id()
    try:
        path = await run_blocking_io(state.diagnostics_exporter, state.config)
    except Exception as exc:
        raise api_error(500, DIAGNOSTICS_EXPORT_FAILED, "诊断包导出失败。", request_id) from exc
    return {"status": "ok", "path": str(path)}
