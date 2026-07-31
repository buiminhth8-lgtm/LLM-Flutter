"""Novel Studio Stage 4 writing API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import WRITING_FEATURE_DISABLED, api_error
from llm_studio.features import is_novel_studio_enabled
from llm_studio.writing.errors import WritingError
from llm_studio.writing.schemas import (
    SaveGenerationRequest,
    WritingGenerationRequest,
)
from llm_studio.writing.stream import writing_sse_event

router = APIRouter(prefix="/v1/writing")


def _service(request: Request):
    state = get_api_state()
    if not is_novel_studio_enabled(state.config):
        raise api_error(
            404,
            WRITING_FEATURE_DISABLED,
            "Writing Workspace is disabled. Enable features.novel_studio.enabled.",
            getattr(request.state, "request_id", ""),
        )
    if state.writing_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Writing service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.writing_service


def _raise_writing_error(request: Request, exc: WritingError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
    ) from exc


@router.post("/generate")
async def generate_writing(request: Request, body: WritingGenerationRequest):
    try:
        return await _service(request).generate(body)
    except WritingError as exc:
        _raise_writing_error(request, exc)


@router.post("/stream")
async def stream_writing(request: Request, body: WritingGenerationRequest):
    service = _service(request)

    async def event_stream():
        generation_id: str | None = None
        try:
            async for event in service.stream_generate(body):
                generation_id = event.get("generation_id") or generation_id
                if await request.is_disconnected():
                    if generation_id:
                        try:
                            service.cancel_generation(generation_id)
                        except WritingError:
                            pass
                    return
                yield writing_sse_event(event)
        except WritingError as exc:
            yield writing_sse_event(
                {
                    "type": "error",
                    "generation_id": generation_id,
                    "error_code": exc.code,
                    "message": exc.message,
                }
            )
        finally:
            yield writing_sse_event({"type": "end"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/generations")
async def list_generations(
    request: Request,
    project_id: str | None = None,
    chapter_id: str | None = None,
    mode: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_generations(
                project_id=project_id,
                chapter_id=chapter_id,
                mode=mode,
                status=status,
                limit=limit,
                offset=offset,
            )
        }
    except WritingError as exc:
        _raise_writing_error(request, exc)


@router.get("/generations/{generation_id}")
async def get_generation(request: Request, generation_id: str):
    try:
        return _service(request).get_generation(generation_id)
    except WritingError as exc:
        _raise_writing_error(request, exc)


@router.post("/generations/{generation_id}/save-to-chapter")
async def save_generation_to_chapter(
    request: Request,
    generation_id: str,
    body: SaveGenerationRequest,
):
    try:
        chapter = _service(request).save_output_to_chapter(
            generation_id,
            target=body.target,
            append=body.append,
        )
        return {"status": "saved", "chapter": chapter}
    except WritingError as exc:
        _raise_writing_error(request, exc)


@router.post("/generations/{generation_id}/cancel")
async def cancel_generation(request: Request, generation_id: str):
    try:
        return _service(request).cancel_generation(generation_id)
    except WritingError as exc:
        _raise_writing_error(request, exc)
