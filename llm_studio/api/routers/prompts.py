"""Prompt Studio stage 2 API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import PROMPT_FEATURE_DISABLED, api_error
from llm_studio.features import is_novel_studio_enabled
from llm_studio.prompts.errors import PromptError
from llm_studio.prompts.schemas import (
    PromptCopyToProjectRequest,
    PromptRenderRequest,
    PromptTemplateCreateRequest,
    PromptTemplateUpdateRequest,
    PromptTemplateVersionCreateRequest,
)

router = APIRouter(prefix="/v1/prompts")


def _service(request: Request):
    state = get_api_state()
    if not is_novel_studio_enabled(state.config):
        raise api_error(
            404,
            PROMPT_FEATURE_DISABLED,
            "Prompt Studio is disabled. Enable features.novel_studio.enabled to use Stage 2 APIs.",
            getattr(request.state, "request_id", ""),
        )
    if state.prompt_service is None:
        raise api_error(500, "INTERNAL_ERROR", "Prompt service is not configured.", getattr(request.state, "request_id", ""))
    return state.prompt_service


def _handle(request: Request, action):
    try:
        return action()
    except PromptError as exc:
        raise api_error(exc.status_code, exc.code, exc.message, getattr(request.state, "request_id", "")) from exc


@router.get("/templates")
async def list_templates(
    request: Request,
    type: str | None = None,
    scope: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return {
        "data": _handle(
            request,
            lambda: _service(request).list_templates(
                type=type,
                scope=scope,
                project_id=project_id,
                limit=limit,
                offset=offset,
            ),
        )
    }


@router.post("/templates")
async def create_template(request: Request, body: PromptTemplateCreateRequest):
    return _handle(request, lambda: _service(request).create_template(body))


@router.get("/templates/{template_id}")
async def get_template(request: Request, template_id: str):
    return _handle(request, lambda: _service(request).get_template(template_id))


@router.patch("/templates/{template_id}")
async def update_template(request: Request, template_id: str, body: PromptTemplateUpdateRequest):
    return _handle(request, lambda: _service(request).update_template_metadata(template_id, body))


@router.delete("/templates/{template_id}")
async def delete_template(request: Request, template_id: str):
    return _handle(request, lambda: _service(request).soft_delete_template(template_id))


@router.get("/templates/{template_id}/versions")
async def list_versions(request: Request, template_id: str):
    return {"data": _handle(request, lambda: _service(request).list_versions(template_id))}


@router.post("/templates/{template_id}/versions")
async def create_version(request: Request, template_id: str, body: PromptTemplateVersionCreateRequest):
    return _handle(request, lambda: _service(request).create_version(template_id, body))


@router.get("/versions/{version_id}")
async def get_version(request: Request, version_id: str):
    return _handle(request, lambda: _service(request).get_version(version_id))


@router.post("/templates/{template_id}/versions/{version_id}/activate")
async def activate_version(request: Request, template_id: str, version_id: str):
    return _handle(request, lambda: _service(request).activate_version(template_id, version_id))


@router.post("/render")
async def render_prompt(request: Request, body: PromptRenderRequest):
    return _handle(request, lambda: _service(request).render(body))


@router.get("/render-records")
async def list_render_records(request: Request, template_id: str | None = None, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_render_records(template_id=template_id, limit=limit, offset=offset))}


@router.get("/render-records/{render_id}")
async def get_render_record(request: Request, render_id: str):
    return _handle(request, lambda: _service(request).get_render_record(render_id))


@router.post("/defaults/ensure")
async def ensure_defaults(request: Request):
    return {"data": _handle(request, lambda: _service(request).ensure_defaults())}


@router.post("/templates/{template_id}/copy-to-project")
async def copy_to_project(request: Request, template_id: str, body: PromptCopyToProjectRequest):
    return _handle(request, lambda: _service(request).copy_to_project(template_id, body))
