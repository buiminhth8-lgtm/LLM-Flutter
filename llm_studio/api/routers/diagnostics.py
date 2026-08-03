"""Diagnostics API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import DIAGNOSTICS_EXPORT_FAILED, api_error
from llm_studio.capabilities import get_capabilities_for_config
from llm_studio.diagnostics import collect_diagnostics, collect_system_summary
from llm_studio.execution import run_blocking_io
from llm_studio.health import build_health_payload

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


@router.get("/v1/diagnostics/health")
async def diagnostics_health():
    return build_health_payload(get_api_state(), full=True)


@router.get("/v1/diagnostics/system")
async def diagnostics_system():
    return collect_system_summary()


@router.get("/v1/diagnostics/capabilities")
async def diagnostics_capabilities():
    config = get_api_state().config
    return {
        "capabilities": [
            capability.to_dict()
            for capability in get_capabilities_for_config(config)
        ]
    }


@router.get("/v1/diagnostics/preview")
async def diagnostics_preview():
    state = get_api_state()
    assert state.config is not None
    payload = await run_blocking_io(collect_diagnostics, state.config)
    return {
        "status": "ok",
        "manifest": list(payload.keys()),
        "system": payload["system"],
        "capabilities_count": len(payload["capabilities"]),
    }
