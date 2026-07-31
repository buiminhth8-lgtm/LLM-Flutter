"""Route-to-permission mapping for the FastAPI surface."""

from __future__ import annotations

from .roles import Permission, has_permission


def _is_model_load_path(method: str, path: str) -> bool:
    return method == "POST" and path.startswith("/v1/models/") and path.endswith("/load")


def _is_model_delete_path(method: str, path: str) -> bool:
    return method == "DELETE" and path.startswith("/v1/models/")


def normalize_permission_path(path: str) -> str:
    """Normalize compatibility API paths before permission lookup."""
    if path.startswith("/api/v1/"):
        return "/v1/" + path[len("/api/v1/") :]
    if path == "/api/v1":
        return "/v1"
    return path


def required_permission_for_request(method: str, path: str) -> Permission | None:
    """Return the permission required by a request, or None for authenticated-only."""
    method = method.upper()
    path = normalize_permission_path(path)

    if method == "GET" and path in {
        "/v1/runtime",
        "/v1/gpu/scheduler",
        "/v1/capabilities",
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
        if method == "GET":
            return Permission.VIEW_MODELS
        if path == "/v1/adapters/scan" or path == "/v1/adapters/register" or path.endswith("/merge"):
            return Permission.MANAGE_ADAPTERS
        if path.endswith(("/load", "/activate", "/deactivate", "/unload")):
            return Permission.LOAD_MODEL
        return Permission.MANAGE_ADAPTERS
    if method == "POST" and path == "/v1/benchmarks":
        return Permission.RUN_BENCHMARK
    if method == "DELETE" and path.startswith("/v1/benchmarks/"):
        return Permission.RUN_BENCHMARK
    if method == "POST" and path in {"/v1/storage/cleanup", "/v1/storage/cleanup/preview"}:
        return Permission.MANAGE_STORAGE
    if method == "POST" and path == "/v1/diagnostics/export":
        return Permission.EXPORT_DIAGNOSTICS
    if method == "POST" and path.startswith("/v1/jobs/") and path.endswith("/cancel"):
        return Permission.MANAGE_STORAGE

    if path == "/v1/auth/me" or path.startswith("/v1/auth/users"):
        return None

    if path.startswith("/v1/novels"):
        if method == "GET":
            return Permission.VIEW_NOVELS
        if method == "DELETE":
            return Permission.DELETE_NOVELS
        return Permission.MANAGE_NOVELS

    if path.startswith("/v1/prompts"):
        if method == "GET":
            return Permission.VIEW_PROMPTS
        if path == "/v1/prompts/render" and method == "POST":
            return Permission.VIEW_PROMPTS
        if method == "DELETE":
            return Permission.DELETE_PROMPTS
        return Permission.MANAGE_PROMPTS

    if path.startswith("/v1/context"):
        if method in {"GET", "POST"}:
            return Permission.VIEW_CONTEXT
        return Permission.MANAGE_CONTEXT

    if path.startswith("/v1/writing"):
        if method == "GET":
            return Permission.VIEW_WRITING
        return Permission.MANAGE_WRITING

    if path.startswith("/v1/revisions"):
        if method == "GET":
            return Permission.VIEW_REVISIONS
        return Permission.MANAGE_REVISIONS

    if path.startswith("/v1/vision"):
        return Permission.CHAT

    if path.startswith("/v1/"):
        return Permission.MANAGE_USERS
    return None


__all__ = ["Permission", "has_permission", "normalize_permission_path", "required_permission_for_request"]
