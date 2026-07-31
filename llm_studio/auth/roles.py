"""Role and permission definitions for API keys."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class Permission(StrEnum):
    VIEW_RUNTIME = "view_runtime"
    VIEW_MODELS = "view_models"
    CHAT = "chat"
    LOAD_MODEL = "load_model"
    UNLOAD_MODEL = "unload_model"
    MANAGE_MODELS = "manage_models"
    MANAGE_DOWNLOADS = "manage_downloads"
    MANAGE_ADAPTERS = "manage_adapters"
    RUN_BENCHMARK = "run_benchmark"
    MANAGE_RAG = "manage_rag"
    MANAGE_STORAGE = "manage_storage"
    EXPORT_DIAGNOSTICS = "export_diagnostics"
    MANAGE_USERS = "manage_users"
    VIEW_NOVELS = "view_novels"
    MANAGE_NOVELS = "manage_novels"
    DELETE_NOVELS = "delete_novels"
    VIEW_PROMPTS = "view_prompts"
    MANAGE_PROMPTS = "manage_prompts"
    DELETE_PROMPTS = "delete_prompts"
    VIEW_CONTEXT = "view_context"
    MANAGE_CONTEXT = "manage_context"
    VIEW_WRITING = "view_writing"
    MANAGE_WRITING = "manage_writing"
    VIEW_REVISIONS = "view_revisions"
    MANAGE_REVISIONS = "manage_revisions"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset(
        {
            Permission.VIEW_RUNTIME,
            Permission.VIEW_MODELS,
            Permission.VIEW_NOVELS,
            Permission.VIEW_PROMPTS,
            Permission.VIEW_CONTEXT,
            Permission.VIEW_WRITING,
            Permission.VIEW_REVISIONS,
        }
    ),
    Role.OPERATOR: frozenset(
        {
            Permission.VIEW_RUNTIME,
            Permission.VIEW_MODELS,
            Permission.CHAT,
            Permission.LOAD_MODEL,
            Permission.UNLOAD_MODEL,
            Permission.MANAGE_RAG,
            Permission.VIEW_NOVELS,
            Permission.MANAGE_NOVELS,
            Permission.VIEW_PROMPTS,
            Permission.MANAGE_PROMPTS,
            Permission.VIEW_CONTEXT,
            Permission.MANAGE_CONTEXT,
            Permission.VIEW_WRITING,
            Permission.MANAGE_WRITING,
            Permission.VIEW_REVISIONS,
            Permission.MANAGE_REVISIONS,
        }
    ),
    Role.ADMIN: frozenset(Permission),
}


def normalize_role(value: str | None, *, missing_role: Role = Role.ADMIN) -> Role:
    """Normalize stored roles, including pre-RBAC legacy records."""
    if not value:
        return missing_role
    lowered = str(value).lower()
    if lowered == "user":
        return Role.OPERATOR
    try:
        return Role(lowered)
    except ValueError:
        return Role.VIEWER


def has_permission(role: str | Role | None, permission: Permission) -> bool:
    normalized = normalize_role(str(role) if role is not None else None, missing_role=Role.VIEWER)
    return permission in ROLE_PERMISSIONS[normalized]
