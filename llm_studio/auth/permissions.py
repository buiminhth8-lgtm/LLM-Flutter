"""Route-to-permission mapping for the FastAPI surface."""

from __future__ import annotations

from .roles import Permission, has_permission


def _is_model_load_path(method: str, path: str) -> bool:
    return method == "POST" and path.startswith("/v1/models/") and path.endswith("/load")


def _is_model_delete_path(method: str, path: str) -> bool:
    return method == "DELETE" and path.startswith("/v1/models/")


def required_permission_for_request(method: str, path: str) -> Permission | None:
    """Return the permission required by a request, or None for authenticated-only."""
    method = method.upper()

    if method == "GET" and path in {
        "/v1/runtime",
        "/v1/gpu/scheduler",
        "/v1/storage",
    }:
        return Permission.VIEW_RUNTIME
    if method == "GET" and (
        path == "/v1/models"
        or path == "/v1/models/current"
        or path.startswith("/v1/jobs")
        or path.startswith("/v1/benchmarks")
        or path == "/v1/rag/status"
    ):
        return Permission.VIEW_MODELS

    if method == "POST" and path == "/v1/chat/completions":
        return Permission.CHAT
    if _is_model_load_path(method, path) or (method == "POST" and path == "/v1/models/load"):
        return Permission.LOAD_MODEL
    if method == "POST" and path == "/v1/models/unload":
        return Permission.UNLOAD_MODEL

    if path.startswith("/v1/rag"):
        return Permission.MANAGE_RAG

    if method == "POST" and path in {"/v1/models/scan", "/v1/models/register"}:
        return Permission.MANAGE_MODELS
    if _is_model_delete_path(method, path):
        return Permission.MANAGE_MODELS

    if path.startswith("/v1/downloads"):
        return Permission.MANAGE_DOWNLOADS if method != "GET" else Permission.VIEW_MODELS
    if path.startswith("/v1/adapters"):
        return Permission.MANAGE_ADAPTERS if method != "GET" else Permission.VIEW_MODELS
    if method == "POST" and path == "/v1/benchmarks":
        return Permission.RUN_BENCHMARK
    if method == "POST" and path == "/v1/storage/cleanup":
        return Permission.MANAGE_STORAGE
    if method == "POST" and path == "/v1/diagnostics/export":
        return Permission.EXPORT_DIAGNOSTICS
    if method == "POST" and path.startswith("/v1/jobs/") and path.endswith("/cancel"):
        return Permission.MANAGE_STORAGE

    if path.startswith("/v1/vision"):
        return Permission.CHAT

    if path.startswith("/v1/"):
        return Permission.MANAGE_USERS
    return None


__all__ = ["Permission", "has_permission", "required_permission_for_request"]
