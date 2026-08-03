"""Novel Studio Stage 10 Memory / RAG API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import MEMORY_FEATURE_DISABLED, api_error
from llm_studio.features import is_novel_memory_enabled
from llm_studio.memory.errors import MemoryError
from llm_studio.memory.schemas import (
    ChapterSummaryActivateRequest,
    ChapterSummaryCreateRequest,
    ChapterSummaryGenerateRequest,
    MemoryBuildRequest,
    MemoryDocumentCreateRequest,
    MemoryDocumentUpdateRequest,
    MemoryRetrieveRequest,
)

router = APIRouter(prefix="/v1/memory")


def _service(request: Request):
    state = get_api_state()
    if not is_novel_memory_enabled(state.config):
        raise api_error(
            404,
            MEMORY_FEATURE_DISABLED,
            "Novel Memory is disabled. Enable novel_studio and novel_memory.",
            getattr(request.state, "request_id", ""),
        )
    if state.memory_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Memory service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.memory_service


def _raise_memory_error(request: Request, exc: MemoryError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
    ) from exc


@router.get("/documents")
async def list_memory_documents(
    request: Request,
    project_id: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_documents(
                project_id=project_id,
                source_type=source_type,
                source_id=source_id,
                status=status,
                tag=tag,
                limit=limit,
                offset=offset,
            )
        }
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/documents")
async def create_memory_document(request: Request, body: MemoryDocumentCreateRequest):
    try:
        return _service(request).create_document(body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.get("/documents/{document_id}")
async def get_memory_document(request: Request, document_id: str):
    try:
        return _service(request).get_document(document_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.patch("/documents/{document_id}")
async def update_memory_document(
    request: Request,
    document_id: str,
    body: MemoryDocumentUpdateRequest,
):
    try:
        return _service(request).update_document(document_id, body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.delete("/documents/{document_id}")
async def archive_memory_document(request: Request, document_id: str):
    try:
        return _service(request).archive_document(document_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/projects/{project_id}/build-from-novel")
async def build_memory_from_novel(
    request: Request,
    project_id: str,
    body: MemoryBuildRequest,
):
    try:
        return _service(request).build_from_novel(project_id, body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/projects/{project_id}/index/rebuild")
async def rebuild_project_memory_index(request: Request, project_id: str):
    try:
        return _service(request).rebuild_project_index(project_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.get("/projects/{project_id}/index/status")
async def get_project_memory_index_status(request: Request, project_id: str):
    try:
        return _service(request).get_project_index_status(project_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/documents/{document_id}/index/rebuild")
async def rebuild_document_memory_index(request: Request, document_id: str):
    try:
        return _service(request).rebuild_document_index(document_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/retrieve")
async def retrieve_memory(request: Request, body: MemoryRetrieveRequest):
    try:
        return _service(request).retrieve(body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.get("/retrieval-records")
async def list_memory_retrieval_records(
    request: Request,
    project_id: str | None = None,
    chapter_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_retrieval_records(
                project_id=project_id,
                chapter_id=chapter_id,
                limit=limit,
                offset=offset,
            )
        }
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.get("/retrieval-records/{retrieval_id}")
async def get_memory_retrieval_record(request: Request, retrieval_id: str):
    try:
        return _service(request).get_retrieval_record(retrieval_id)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.get("/chapters/{chapter_id}/summaries")
async def list_chapter_summaries(
    request: Request,
    chapter_id: str,
    summary_type: str | None = None,
    limit: int = 50,
):
    try:
        return {
            "data": _service(request).list_chapter_summaries(
                chapter_id,
                summary_type=summary_type,
                limit=limit,
            )
        }
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/chapters/{chapter_id}/summaries")
async def create_chapter_summary(
    request: Request,
    chapter_id: str,
    body: ChapterSummaryCreateRequest,
):
    try:
        return _service(request).create_chapter_summary(chapter_id, body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/chapters/{chapter_id}/summaries/generate")
async def generate_chapter_summary(
    request: Request,
    chapter_id: str,
    body: ChapterSummaryGenerateRequest,
):
    try:
        return await _service(request).generate_chapter_summary(chapter_id, body)
    except MemoryError as exc:
        _raise_memory_error(request, exc)


@router.post("/chapters/{chapter_id}/summaries/{summary_id}/activate")
async def activate_chapter_summary(
    request: Request,
    chapter_id: str,
    summary_id: str,
    body: ChapterSummaryActivateRequest | None = None,
):
    try:
        sync = True if body is None else body.sync_to_chapter
        return _service(request).activate_chapter_summary(
            chapter_id,
            summary_id,
            sync_to_chapter=sync,
        )
    except MemoryError as exc:
        _raise_memory_error(request, exc)

