"""Novel Studio Stage 5 revision API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import REVISION_FEATURE_DISABLED, api_error
from llm_studio.features import is_revision_system_enabled
from llm_studio.revisions.errors import RevisionError
from llm_studio.revisions.schemas import (
    RevisionAutosaveRequest,
    RevisionCreateFromChapterDraftRequest,
    RevisionCreateFromGenerationRequest,
    RevisionDatasetCandidateRequest,
    RevisionManualCreateRequest,
    RevisionRejectRequest,
    RevisionUpdateRequest,
)

router = APIRouter(prefix="/v1/revisions")


def _service(request: Request):
    state = get_api_state()
    if not is_revision_system_enabled(state.config):
        raise api_error(
            404,
            REVISION_FEATURE_DISABLED,
            "Revision system is disabled. Enable Novel Studio and the revision_system feature.",
            getattr(request.state, "request_id", ""),
        )
    if state.revision_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Revision service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.revision_service


def _raise_revision_error(request: Request, exc: RevisionError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
    ) from exc


@router.get("")
async def list_revisions(
    request: Request,
    project_id: str | None = None,
    chapter_id: str | None = None,
    generation_id: str | None = None,
    status: str | None = None,
    user_score: int | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_revisions(
                project_id=project_id,
                chapter_id=chapter_id,
                generation_id=generation_id,
                status=status,
                user_score=user_score,
                limit=limit,
                offset=offset,
            )
        }
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.get("/{revision_id}")
async def get_revision(request: Request, revision_id: str):
    try:
        return _service(request).get_revision(revision_id)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.patch("/{revision_id}")
async def update_revision(
    request: Request,
    revision_id: str,
    body: RevisionUpdateRequest,
):
    try:
        return _service(request).update_revision(revision_id, body)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.delete("/{revision_id}")
async def archive_revision(request: Request, revision_id: str):
    try:
        return _service(request).archive_revision(revision_id)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/from-generation")
async def create_revision_from_generation(
    request: Request,
    body: RevisionCreateFromGenerationRequest,
):
    try:
        return _service(request).create_from_generation(body)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/from-chapter-draft")
async def create_revision_from_chapter_draft(
    request: Request,
    body: RevisionCreateFromChapterDraftRequest,
):
    try:
        return _service(request).create_from_chapter_draft(body)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/manual")
async def create_manual_revision(request: Request, body: RevisionManualCreateRequest):
    try:
        return _service(request).create_manual(body)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/{revision_id}/approve")
async def approve_revision(request: Request, revision_id: str):
    try:
        return _service(request).approve_revision(revision_id)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/{revision_id}/reject")
async def reject_revision(
    request: Request,
    revision_id: str,
    body: RevisionRejectRequest | None = None,
):
    try:
        return _service(request).reject_revision(
            revision_id,
            reason=body.reason if body else None,
        )
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/{revision_id}/dataset-candidate")
async def mark_dataset_candidate(
    request: Request,
    revision_id: str,
    body: RevisionDatasetCandidateRequest,
):
    try:
        return _service(request).mark_dataset_candidate(revision_id, body.accepted)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.post("/autosave")
async def autosave_revision(request: Request, body: RevisionAutosaveRequest):
    try:
        return _service(request).autosave_revision(body)
    except RevisionError as exc:
        _raise_revision_error(request, exc)


@router.get("/{revision_id}/autosaves")
async def list_revision_autosaves(
    request: Request,
    revision_id: str,
    limit: int = 20,
):
    try:
        return {"data": _service(request).list_autosaves(revision_id, limit=limit)}
    except RevisionError as exc:
        _raise_revision_error(request, exc)
