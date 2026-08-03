"""Business orchestration for Context Assembler Stage 3."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from llm_studio.novels.errors import NovelError
from llm_studio.prompts.errors import PromptError

from .assembler import ContextAssembler
from .budget import ContextBudgetManager, normalize_budget
from .errors import (
    ContextNotFoundError,
    ContextRenderError,
    ContextVariablesError,
)
from .estimators import TokenEstimator
from .migrations import initialize_context_database
from .repository import ContextAssemblyRepository
from .selectors import SceneSelector


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


class ContextService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        prompt_service: Any,
        memory_service: Any | None = None,
    ):
        self.db_path = Path(db_path)
        initialize_context_database(self.db_path)
        self.records = ContextAssemblyRepository(self.db_path)
        self.novel_service = novel_service
        self.prompt_service = prompt_service
        self.memory_service = memory_service
        self.assembler = ContextAssembler()
        self.estimator = TokenEstimator()
        self.scene_selector = SceneSelector()

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        prompt_service: Any,
    ) -> ContextService:
        cfg = config.get("context", {}) if config is not None else {}
        fallback = (
            config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite")
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(
            Path(cfg.get("db_path", fallback)),
            novel_service=novel_service,
            prompt_service=prompt_service,
        )

    def assemble_context(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if not isinstance(data.get("user_variables") or {}, dict):
            raise ContextVariablesError("user_variables must be an object.")
        project = self._project(data["project_id"])
        chapter = self._chapter(data.get("chapter_id"), project["id"])
        scenes = (
            self.novel_service.list_scenes(chapter["id"], limit=200)
            if chapter
            else []
        )
        scene = self._scene(data.get("scene_id"), chapter, scenes)
        chapters = self.novel_service.list_chapters(project["id"], limit=200)
        result = self.assembler.assemble(
            project=project,
            chapter=chapter,
            scene=scene,
            chapters=chapters,
            characters=self.novel_service.list_characters(project["id"], limit=200),
            world_entries=self.novel_service.list_world_entries(project["id"], limit=200),
            plot_threads=self.novel_service.list_plot_threads(project["id"], limit=200),
            timeline_events=self.novel_service.list_timeline(project["id"], limit=200),
            request=data,
        )
        if data.get("template_id"):
            template, version = self._template(
                data["template_id"],
                data.get("template_version_id"),
            )
            result = replace(
                result,
                template_id=template["id"],
                template_version_id=version["id"],
            )
        payload = result.to_dict()
        if (data.get("memory") or {}).get("enabled", False):
            if self.memory_service is None:
                payload["warnings"] = [
                    *payload.get("warnings", []),
                    {
                        "code": "MEMORY_FEATURE_DISABLED",
                        "message": "Memory service is not configured; context uses Stage 3 behavior.",
                    },
                ]
            else:
                from llm_studio.memory.context_bridge import ContextMemoryBridge

                payload = ContextMemoryBridge(self.memory_service).enrich(payload, data)
        if data.get("save_record", True):
            record = self.records.save(payload)
            payload["context_id"] = record["context_id"]
        return payload

    def assemble_and_render(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        template_id = data.get("template_id")
        if not template_id:
            raise ContextNotFoundError("template", "")
        template, version = self._template(
            template_id,
            data.get("template_version_id"),
        )
        assembled = self.assemble_context({**data, "template_version_id": version["id"]})
        try:
            rendered = self.prompt_service.renderer.render(
                version,
                assembled["variables"],
                None,
            )
        except PromptError as exc:
            raise ContextRenderError(exc.message) from exc
        return {
            **assembled,
            "template_id": template["id"],
            "template_version_id": version["id"],
            "rendered_prompt": rendered.rendered_prompt,
            "missing_variables": rendered.missing_variables,
            "render_warnings": rendered.warnings,
            "prompt_hash": rendered.prompt_hash,
        }

    def estimate(self, request: Any) -> dict[str, int]:
        data = _model_dump(request)
        text = str(data.get("text") or "")
        variables = data.get("variables") or {}
        if not isinstance(variables, dict):
            raise ContextVariablesError("variables must be an object.")
        if variables:
            manager = ContextBudgetManager(normalize_budget(None), self.estimator)
            tokens, chars = manager.measure(variables)
            if text:
                tokens += self.estimator.estimate(text)
                chars += len(text)
        else:
            tokens, chars = self.estimator.estimate(text), len(text)
        return {"estimated_tokens": tokens, "estimated_chars": chars}

    def get_context_record(self, context_id: str) -> dict[str, Any]:
        return self.records.get(context_id)

    def list_context_records(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list(
            project_id=project_id,
            chapter_id=chapter_id,
            limit=limit,
            offset=offset,
        )

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise ContextNotFoundError("project", project_id) from exc

    def _chapter(
        self,
        chapter_id: str | None,
        project_id: str,
    ) -> dict[str, Any] | None:
        if not chapter_id:
            return None
        try:
            chapter = self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise ContextNotFoundError("chapter", chapter_id) from exc
        if chapter.get("project_id") != project_id:
            raise ContextNotFoundError("chapter", chapter_id)
        return chapter

    def _scene(
        self,
        scene_id: str | None,
        chapter: dict[str, Any] | None,
        scenes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not scene_id:
            return None
        if not chapter:
            raise ContextNotFoundError("scene", scene_id)
        scene = self.scene_selector.select(scenes, scene_id)
        if scene is None:
            raise ContextNotFoundError("scene", scene_id)
        return scene

    def _template(
        self,
        template_id: str,
        version_id: str | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            template = self.prompt_service.get_template(template_id)
        except PromptError as exc:
            raise ContextNotFoundError("template", template_id) from exc
        resolved_id = version_id or template.get("active_version_id")
        if not resolved_id:
            raise ContextNotFoundError("template_version", template_id)
        try:
            version = self.prompt_service.get_version(resolved_id)
        except PromptError as exc:
            raise ContextNotFoundError("template_version", resolved_id) from exc
        if version.get("template_id") != template_id:
            raise ContextNotFoundError("template_version", resolved_id)
        return template, version
