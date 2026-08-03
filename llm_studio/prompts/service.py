"""Business service for Prompt Studio templates and preview rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .defaults import ensure_default_prompt_templates
from .errors import (
    PromptInvalidScopeError,
    PromptInvalidTypeError,
    PromptNotFoundError,
    PromptValidationError,
)
from .migrations import initialize_prompt_database
from .renderer import PromptRenderer
from .repository import (
    PromptRenderRecordRepository,
    PromptTemplateRepository,
    PromptTemplateVersionRepository,
)
from .variables import validate_variables_schema

PROMPT_TYPES = {
    "chapter_generate",
    "chapter_continue",
    "chapter_rewrite",
    "chapter_polish",
    "chapter_expand",
    "dialogue_enhance",
    "scene_expand",
    "outline_generate",
    "character_generate",
    "world_entry_generate",
    "summary_generate",
    "custom",
}
PROMPT_SCOPES = {"global", "project"}


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise PromptValidationError(f"{field} is required.")
    return text


class PromptService:
    def __init__(self, db_path: str | Path, *, novel_service: Any | None = None):
        self.db_path = Path(db_path)
        initialize_prompt_database(self.db_path)
        self.templates = PromptTemplateRepository(self.db_path)
        self.versions = PromptTemplateVersionRepository(self.db_path)
        self.records = PromptRenderRecordRepository(self.db_path)
        self.renderer = PromptRenderer()
        self.novel_service = novel_service

    @classmethod
    def from_config(cls, config: Any, *, novel_service: Any | None = None) -> PromptService:
        cfg = config.get("prompts", {}) if config is not None else {}
        fallback = config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite") if config is not None else "./data/novels/novels.sqlite"
        return cls(Path(cfg.get("db_path", fallback)), novel_service=novel_service)

    def list_templates(
        self,
        *,
        type: str | None = None,
        scope: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if type:
            self._validate_type(type)
        if scope:
            self._validate_scope(scope)
        return self.templates.list_templates(type=type, scope=scope, project_id=project_id, limit=limit, offset=offset)

    def create_template(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        self._validate_type(data.get("type"))
        self._validate_scope(data.get("scope", "global"))
        if data.get("scope") == "project":
            self._require_project(data.get("project_id"))
        data["name"] = _require_text(data.get("name"), "name")
        data["instruction_template"] = _require_text(data.get("instruction_template"), "instruction_template")
        data["variables_schema"] = validate_variables_schema(data.get("variables_schema") or {})
        if not isinstance(data.get("default_values") or {}, dict):
            raise PromptValidationError("default_values must be an object.")
        template = self.templates.create_template(data)
        version = self.versions.create_version(template["id"], data)
        return self.templates.activate_version(template["id"], version["id"])

    def get_template(self, template_id: str) -> dict[str, Any]:
        template = self.templates.get_template(template_id)
        if template.get("active_version_id"):
            template["active_version"] = self.versions.get_version(template["active_version_id"])
        return template

    def update_template_metadata(self, template_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "type" in data and data["type"] is not None:
            self._validate_type(data["type"])
        if "scope" in data and data["scope"] is not None:
            self._validate_scope(data["scope"])
        if data.get("scope") == "project":
            self._require_project(data.get("project_id"))
        if "name" in data and data["name"] is not None:
            data["name"] = _require_text(data["name"], "name")
        if "metadata" in data:
            data["metadata_json"] = json.dumps(data.pop("metadata") or {}, ensure_ascii=False)
        return self.templates.update_template_metadata(template_id, data)

    def soft_delete_template(self, template_id: str) -> dict[str, Any]:
        return self.templates.soft_delete_template(template_id)

    def list_versions(self, template_id: str) -> list[dict[str, Any]]:
        self.templates.get_template(template_id)
        return self.versions.list_versions(template_id)

    def create_version(self, template_id: str, request: Any) -> dict[str, Any]:
        self.templates.get_template(template_id)
        data = _model_dump(request)
        data["instruction_template"] = _require_text(data.get("instruction_template"), "instruction_template")
        data["variables_schema"] = validate_variables_schema(data.get("variables_schema") or {})
        if not isinstance(data.get("default_values") or {}, dict):
            raise PromptValidationError("default_values must be an object.")
        version = self.versions.create_version(template_id, data)
        self.templates.activate_version(template_id, version["id"])
        return version

    def get_version(self, version_id: str) -> dict[str, Any]:
        return self.versions.get_version(version_id)

    def activate_version(self, template_id: str, version_id: str) -> dict[str, Any]:
        return self.templates.activate_version(template_id, version_id)

    def render(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        template = self.templates.get_template(data["template_id"])
        version_id = data.get("template_version_id") or template.get("active_version_id")
        if not version_id:
            raise PromptNotFoundError("version", data["template_id"])
        version = self.versions.get_version(version_id)
        if version["template_id"] != template["id"]:
            from .errors import PromptVersionMismatchError

            raise PromptVersionMismatchError("Version does not belong to template.")
        project_context = self._build_project_context(data.get("project_id"), data.get("chapter_id"))
        result = self.renderer.render(version, data.get("variables") or {}, project_context)
        payload = {
            "template_id": result.template_id,
            "template_version_id": result.template_version_id,
            "rendered_prompt": result.rendered_prompt,
            "missing_variables": result.missing_variables,
            "warnings": result.warnings,
            "prompt_hash": result.prompt_hash,
        }
        if data.get("save_record", True):
            record = self.records.save_render_record(
                {
                    **payload,
                    "project_id": data.get("project_id"),
                    "chapter_id": data.get("chapter_id"),
                    "variables": data.get("variables") or {},
                }
            )
            payload["render_id"] = record["id"]
        else:
            payload["render_id"] = None
        return payload

    def list_render_records(self, *, template_id: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return self.records.list_render_records(template_id=template_id, limit=limit, offset=offset)

    def get_render_record(self, render_id: str) -> dict[str, Any]:
        return self.records.get_render_record(render_id)

    def ensure_defaults(self) -> dict[str, Any]:
        return ensure_default_prompt_templates(self)

    def copy_to_project(self, template_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        project_id = _require_text(data.get("project_id"), "project_id")
        self._require_project(project_id)
        template = self.get_template(template_id)
        version = template.get("active_version") or self.versions.latest_for_template(template_id)
        return self.create_template(
            {
                "name": data.get("name") or f"{template['name']} copy",
                "type": template["type"],
                "description": template.get("description"),
                "scope": "project",
                "project_id": project_id,
                "system_prompt": version.get("system_prompt"),
                "role_prompt": version.get("role_prompt"),
                "instruction_template": version["instruction_template"],
                "negative_prompt": version.get("negative_prompt"),
                "output_constraints": version.get("output_constraints"),
                "variables_schema": version.get("variables_schema") or {},
                "default_values": version.get("default_values") or {},
                "renderer": version.get("renderer", "simple_mustache"),
                "change_note": "Copied from global template",
            }
        )

    def _build_project_context(self, project_id: str | None, chapter_id: str | None) -> dict[str, Any]:
        if self.novel_service is None or not project_id:
            return {}
        try:
            project = self.novel_service.get_project(project_id)
        except Exception as exc:
            raise PromptNotFoundError("project", project_id) from exc
        context = {
            "project_title": project.get("title"),
            "genre": project.get("genre"),
            "target_style": project.get("target_style"),
            "target_audience": project.get("target_audience"),
        }
        if chapter_id:
            try:
                chapter = self.novel_service.get_chapter(chapter_id)
            except Exception as exc:
                raise PromptNotFoundError("chapter", chapter_id) from exc
            if chapter.get("project_id") != project_id:
                raise PromptNotFoundError("chapter", chapter_id)
            context.update(
                {
                    "chapter_title": chapter.get("title"),
                    "chapter_outline": chapter.get("outline"),
                    "chapter_summary": chapter.get("summary"),
                }
            )
        characters = self.novel_service.list_characters(project_id, limit=200)
        worlds = self.novel_service.list_world_entries(project_id, limit=200)
        plots = self.novel_service.list_plot_threads(project_id, limit=200)
        timeline = self.novel_service.list_timeline(project_id, limit=200)
        context.update(
            {
                "characters": "\n".join(f"{item.get('name')}: {item.get('role') or ''} {item.get('notes') or ''}".strip() for item in characters),
                "world_setting": "\n".join(f"{item.get('category')} - {item.get('title')}: {item.get('content')}" for item in worlds),
                "plot_threads": "\n".join(f"{item.get('title')}: {item.get('description') or ''}" for item in plots),
                "timeline": "\n".join(f"{item.get('event_order')}. {item.get('title')}: {item.get('description') or ''}" for item in timeline),
            }
        )
        return context

    def _require_project(self, project_id: str | None) -> None:
        if not project_id:
            raise PromptNotFoundError("project", "")
        if self.novel_service is None:
            return
        try:
            self.novel_service.get_project(project_id)
        except Exception as exc:
            raise PromptNotFoundError("project", project_id) from exc

    @staticmethod
    def _validate_type(value: str | None) -> None:
        if value not in PROMPT_TYPES:
            raise PromptInvalidTypeError(f"Unsupported prompt type: {value}")

    @staticmethod
    def _validate_scope(value: str | None) -> None:
        if value not in PROMPT_SCOPES:
            raise PromptInvalidScopeError(f"Unsupported prompt scope: {value}")
