"""FastAPI authorization dependency helpers."""

from __future__ import annotations

from fastapi import Request

from llm_studio.api.errors import PERMISSION_DENIED, api_error

from .roles import Permission, has_permission


def require_permission(permission: Permission):
    """Return a FastAPI dependency that checks the authenticated user's role."""

    def dependency(request: Request) -> None:
        user = getattr(request.state, "user", None) or {}
        if not has_permission(user.get("role"), permission):
            request_id = getattr(request.state, "request_id", "")
            raise api_error(403, PERMISSION_DENIED, "当前 API Key 没有执行该操作的权限。", request_id)

    return dependency
