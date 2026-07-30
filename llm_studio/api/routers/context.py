"""Novel Studio Stage 3 Context Assembler API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import CONTEXT_FEATURE_DISABLED, api_error
from llm_studio.context.errors import ContextError
from llm_studio.context.schemas import ContextAssemblyRequest, ContextEstimateRequest
from llm_studio.features import is_novel_studio_enabled

router = APIRouter(prefix="/v1/context")


def _service(request: Request):
    state = get_api_state()
    if not is_novel_studio_enabled(state.config):
        raise api_error(
            404,
            CONTEXT_FEATURE_DISABLED,
            "Context Assembler is disabled. Enable features.novel_studio.enabled.",
            getattr(request.state, "request_id", ""),
        )
    if state.context_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Context service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.context_service


def _handle(request: Request, action):
    try:
        return action()
    except ContextError as exc:
        raise api_error(
            exc.status_code,
            exc.code,
            exc.message,
            getattr(request.state, "request_id", ""),
        ) from exc


@router.post("/assemble")
async def assemble_context(request: Request, body: ContextAssemblyRequest):
    return _handle(request, lambda: _service(request).assemble_context(body))


@router.post("/render-preview")
async def render_context_preview(request: Request, body: ContextAssemblyRequest):
    return _handle(request, lambda: _service(request).assemble_and_render(body))


@router.get("/records")
async def list_context_records(
    request: Request,
    project_id: str | None = None,
    chapter_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return {
        "data": _handle(
            request,
            lambda: _service(request).list_context_records(
                project_id=project_id,
                chapter_id=chapter_id,
                limit=limit,
                offset=offset,
            ),
        )
    }


@router.get("/records/{context_id}")
async def get_context_record(request: Request, context_id: str):
    return _handle(
        request,
        lambda: _service(request).get_context_record(context_id),
    )


@router.post("/estimate")
async def estimate_context(request: Request, body: ContextEstimateRequest):
    return _handle(request, lambda: _service(request).estimate(body))
