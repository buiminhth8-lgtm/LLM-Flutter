"""Model profile API router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import api_error
from llm_studio.model_gateway import (
    MODEL_PROFILE_DISABLED,
    MODEL_PROFILE_NOT_FOUND,
    ModelGatewayError,
)
from llm_studio.model_gateway.profiles import ModelProfileCreate

router = APIRouter(prefix="/v1/model-profiles")


class ModelProfileCreateRequest(BaseModel):
    name: str
    provider: str
    model: str | None = None
    description: str | None = None
    default_params: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    privacy_policy: dict[str, Any] = Field(default_factory=dict)
    connection: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False
    status: str = "enabled"


class ModelProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    model: str | None = None
    status: str | None = None
    default_params: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    privacy_policy: dict[str, Any] | None = None
    connection: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_default: bool | None = None


def _service(request: Request):
    state = get_api_state()
    if state.model_profile_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Model profile service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.model_profile_service


def _handle(request: Request, action):
    try:
        return action()
    except ModelGatewayError as exc:
        raise api_error(
            _status_for(exc.code),
            exc.code,
            exc.message,
            getattr(request.state, "request_id", ""),
            exc.details,
        ) from exc


def _status_for(code: str) -> int:
    if code == MODEL_PROFILE_NOT_FOUND:
        return 404
    if code == MODEL_PROFILE_DISABLED:
        return 409
    return 400


@router.get("")
async def list_profiles(
    request: Request,
    provider: str | None = None,
    status: str | None = None,
):
    return {
        "data": [
            profile.to_dict()
            for profile in _handle(
                request,
                lambda: _service(request).list_profiles(
                    provider=provider,
                    status=status,
                ),
            )
        ]
    }


@router.post("")
async def create_profile(request: Request, body: ModelProfileCreateRequest):
    create = ModelProfileCreate(
        name=body.name,
        provider=body.provider,
        model=body.model,
        description=body.description,
        default_params=body.default_params,
        capabilities=body.capabilities,
        privacy_policy=body.privacy_policy,
        connection=body.connection,
        metadata=body.metadata,
        is_default=body.is_default,
        status=body.status,
    )
    return _handle(request, lambda: _service(request).create_profile(create).to_dict())


@router.get("/default")
async def get_default(request: Request):
    profile = _service(request).get_default_profile()
    return _handle(request, lambda: profile.to_dict() if profile is not None else None)


@router.post("/defaults/ensure")
async def ensure_defaults(request: Request):
    return _handle(request, lambda: _service(request).ensure_builtin_profiles())


@router.get("/{profile_id}")
async def get_profile(request: Request, profile_id: str):
    return _handle(request, lambda: _service(request).get_profile(profile_id).to_dict())


@router.patch("/{profile_id}")
async def update_profile(
    request: Request,
    profile_id: str,
    body: ModelProfileUpdateRequest,
):
    changes = body.model_dump(exclude_unset=True)
    return _handle(
        request,
        lambda: _service(request).update_profile(profile_id, changes).to_dict(),
    )


@router.delete("/{profile_id}")
async def delete_profile(request: Request, profile_id: str):
    return _handle(request, lambda: _service(request).archive_profile(profile_id).to_dict())


@router.post("/{profile_id}/set-default")
async def set_default(request: Request, profile_id: str):
    return _handle(
        request,
        lambda: _service(request).set_default_profile(profile_id).to_dict(),
    )
