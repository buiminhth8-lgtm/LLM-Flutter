"""ContextAssembler selection formatting, priority, and truncation pipeline."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .budget import ContextBudgetManager, normalize_budget
from .entities import ContextAssemblyResult
from .selectors import (
    CharacterSelector,
    PlotThreadSelector,
    PreviousChapterSelector,
    TimelineSelector,
    WorldEntrySelector,
    parse_id_list,
)


class ContextAssembler:
    def __init__(self):
        self.characters = CharacterSelector()
        self.world_entries = WorldEntrySelector()
        self.plot_threads = PlotThreadSelector()
        self.timeline = TimelineSelector()
        self.previous_chapter = PreviousChapterSelector()

    def assemble(
        self,
        *,
        project: dict[str, Any],
        chapter: dict[str, Any] | None,
        scene: dict[str, Any] | None,
        chapters: list[dict[str, Any]],
        characters: list[dict[str, Any]],
        world_entries: list[dict[str, Any]],
        plot_threads: list[dict[str, Any]],
        timeline_events: list[dict[str, Any]],
        request: dict[str, Any],
    ) -> ContextAssemblyResult:
        include = request.get("include") or {}
        budget = normalize_budget(request.get("target_budget"))
        manager = ContextBudgetManager(budget)
        warnings: list[dict[str, Any]] = []

        related_ids: set[str] = set()
        for item in plot_threads:
            related_ids.update(parse_id_list(item.get("related_character_ids")))
        selected_characters = (
            self.characters.select(
                characters,
                pov_character_id=scene.get("pov_character_id") if scene else None,
                related_character_ids=related_ids,
            )
            if include.get("characters", True)
            else []
        )
        selected_world = (
            self.world_entries.select(
                world_entries,
                scene_location=scene.get("location") if scene else None,
            )
            if include.get("world_entries", True)
            else []
        )
        selected_plots = (
            self.plot_threads.select(
                plot_threads,
                selected_character_ids={str(item.get("id")) for item in selected_characters},
            )
            if include.get("plot_threads", True)
            else []
        )
        chapter_indexes = {
            str(item.get("id")): int(item.get("chapter_index") or 0)
            for item in chapters
        }
        selected_timeline = (
            self.timeline.select(
                timeline_events,
                current_chapter_id=chapter.get("id") if chapter else None,
                current_scene_id=scene.get("id") if scene else None,
                current_chapter_index=int(chapter.get("chapter_index") or 0) if chapter else None,
                chapter_indexes=chapter_indexes,
            )
            if include.get("timeline", True)
            else []
        )
        previous, previous_summary, previous_warnings = self.previous_chapter.select(
            chapters,
            chapter,
        )
        if not include.get("previous_chapter_summary", True):
            previous = None
            previous_summary = ""
            previous_warnings = []
        warnings.extend(previous_warnings)

        variables: dict[str, Any] = {
            "project_title": project.get("title") or "",
            "genre": project.get("genre") or "",
            "description": project.get("description") or "",
            "target_style": project.get("target_style") or "",
            "target_audience": project.get("target_audience") or "",
            "chapter_title": (chapter.get("title") or "") if chapter else "",
            "chapter_outline": (
                chapter.get("outline") or ""
                if chapter and include.get("chapter_outline", True)
                else ""
            ),
            "chapter_summary": (chapter.get("summary") or "") if chapter else "",
            "chapter_status": (chapter.get("status") or "") if chapter else "",
            "previous_chapter_summary": previous_summary,
            "previous_chapter_title": (
                (previous.get("title") or "") if previous else ""
            ),
            "scene_title": (scene.get("title") or "") if scene else "",
            "scene_outline": (
                scene.get("outline") or ""
                if scene and include.get("scene_outline", True)
                else ""
            ),
            "scene_location": (scene.get("location") or "") if scene else "",
            "scene_timeline_note": (
                (scene.get("timeline_note") or "") if scene else ""
            ),
            "scene_pov_character": self._character_name(
                selected_characters,
                scene.get("pov_character_id") if scene else None,
            ),
            "characters": self._format_characters(selected_characters),
            "main_characters": self._format_characters(
                [
                    item
                    for item in selected_characters
                    if str(item.get("role") or "").lower()
                    in {"protagonist", "main", "主角", "主要人物"}
                ]
            ),
            "pov_character": self._format_characters(
                [
                    item
                    for item in selected_characters
                    if scene and item.get("id") == scene.get("pov_character_id")
                ]
            ),
            "world_setting": self._format_world(selected_world),
            "plot_threads": self._format_plots(selected_plots),
            "timeline": self._format_timeline(selected_timeline, chapter_indexes),
            "current_chapter_goal": "",
            "target_length": "",
            "style": project.get("target_style") or "",
            "pov": "",
            "user_instruction": "",
            "forbidden_content": "",
        }
        user_variables = request.get("user_variables") or {}
        variables.update(user_variables)
        protected = set(user_variables)

        selected_items = {
            "characters": (
                []
                if "characters" in protected
                else [str(item.get("id")) for item in selected_characters]
            ),
            "world_entries": (
                []
                if "world_setting" in protected
                else [str(item.get("id")) for item in selected_world]
            ),
            "plot_threads": (
                []
                if "plot_threads" in protected
                else [str(item.get("id")) for item in selected_plots]
            ),
            "timeline_events": (
                []
                if "timeline" in protected
                else [str(item.get("id")) for item in selected_timeline]
            ),
            "chapters": (
                []
                if "previous_chapter_summary" in protected or previous is None
                else [str(previous.get("id"))]
            ),
            "scenes": [str(scene.get("id"))] if scene else [],
        }

        truncated: list[str] = []
        while (
            selected_world
            and "world_setting" not in protected
            and manager.exceeds(variables)
        ):
            selected_world.pop()
            variables["world_setting"] = self._format_world(selected_world)
            selected_items["world_entries"] = [str(item.get("id")) for item in selected_world]
            if "world_entries" not in truncated:
                truncated.append("world_entries")
        while (
            selected_timeline
            and "timeline" not in protected
            and manager.exceeds(variables)
        ):
            selected_timeline.pop(0)
            variables["timeline"] = self._format_timeline(selected_timeline, chapter_indexes)
            selected_items["timeline_events"] = [str(item.get("id")) for item in selected_timeline]
            if "timeline" not in truncated:
                truncated.append("timeline")
        while (
            selected_plots
            and "plot_threads" not in protected
            and manager.exceeds(variables)
        ):
            selected_plots.pop()
            variables["plot_threads"] = self._format_plots(selected_plots)
            selected_items["plot_threads"] = [str(item.get("id")) for item in selected_plots]
            if "plot_threads" not in truncated:
                truncated.append("plot_threads")
        if (
            manager.exceeds(variables)
            and "previous_chapter_summary" not in protected
            and variables.get("previous_chapter_summary")
        ):
            variables["previous_chapter_summary"] = ""
            variables["previous_chapter_title"] = ""
            selected_items["chapters"] = []
            truncated.append("previous_chapter_summary")
        if (
            manager.exceeds(variables)
            and "characters" not in protected
            and selected_characters
        ):
            variables["characters"] = self._format_characters(selected_characters, compact=True)
            variables["main_characters"] = self._format_characters(
                [
                    item
                    for item in selected_characters
                    if str(item.get("role") or "").lower()
                    in {"protagonist", "main", "主角", "主要人物"}
                ],
                compact=True,
            )
            truncated.append("character_details")
        if (
            budget.hard_limit
            and manager.exceeds(variables)
            and "chapter_outline" not in protected
            and variables.get("chapter_outline")
        ):
            variables["chapter_outline"] = self._truncate_to_fit(
                variables,
                "chapter_outline",
                manager,
            )
            truncated.append("chapter_outline")
        if truncated:
            warnings.append(
                {
                    "code": "CONTEXT_TRUNCATED",
                    "message": "上下文超出预算，已按优先级裁剪低优先级资料。",
                    "affected": truncated,
                }
            )
        estimated_tokens, estimated_chars = manager.measure(variables)
        if manager.exceeds(variables):
            warnings.append(
                {
                    "code": "CONTEXT_BUDGET_EXCEEDED",
                    "message": "受保护的用户变量或核心章节资料仍超出上下文预算。",
                    "affected": sorted(protected or {"chapter_outline"}),
                }
            )
        budget_payload = {
            **budget.to_dict(),
            "effective_context_tokens": budget.effective_context_tokens,
            "estimated_tokens": estimated_tokens,
            "estimated_chars": estimated_chars,
        }
        context_hash = hashlib.sha256(
            json.dumps(
                {
                    "project_id": project["id"],
                    "chapter_id": chapter.get("id") if chapter else None,
                    "scene_id": scene.get("id") if scene else None,
                    "mode": request.get("mode") or "chapter_generate",
                    "variables": variables,
                    "selected_items": selected_items,
                    "budget": budget_payload,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        return ContextAssemblyResult(
            project_id=str(project["id"]),
            chapter_id=str(chapter["id"]) if chapter else None,
            scene_id=str(scene["id"]) if scene else None,
            template_id=request.get("template_id"),
            template_version_id=request.get("template_version_id"),
            mode=request.get("mode") or "chapter_generate",
            variables=variables,
            selected_items=selected_items,
            budget=budget_payload,
            warnings=warnings,
            estimated_tokens=estimated_tokens,
            estimated_chars=estimated_chars,
            context_hash=context_hash,
        )

    @staticmethod
    def _character_name(items: list[dict[str, Any]], character_id: str | None) -> str:
        if not character_id:
            return ""
        item = next((item for item in items if item.get("id") == character_id), None)
        return str(item.get("name") or "") if item else ""

    @staticmethod
    def _format_characters(items: list[dict[str, Any]], *, compact: bool = False) -> str:
        if not items:
            return ""
        lines = ["【人物】"]
        for index, item in enumerate(items, 1):
            lines.extend(
                [
                    f"{index}. {item.get('name') or ''}",
                    f"- 角色：{item.get('role') or ''}",
                    f"- 性格：{item.get('personality') or ''}",
                    f"- 目标：{item.get('goals') or ''}",
                    f"- 说话风格：{item.get('speech_style') or ''}",
                    f"- 关系：{item.get('relationships') or ''}",
                ]
            )
            if not compact:
                if item.get("background"):
                    lines.append(f"- 背景：{item['background']}")
                if item.get("notes"):
                    lines.append(f"- 备注：{item['notes']}")
        return "\n".join(line for line in lines if not line.endswith("："))

    @staticmethod
    def _format_world(items: list[dict[str, Any]]) -> str:
        if not items:
            return ""
        lines = ["【世界观】"]
        for index, item in enumerate(items, 1):
            lines.extend(
                [
                    f"{index}. {item.get('title') or ''}",
                    f"- 类型：{item.get('category') or ''}",
                    f"- 设定：{item.get('content') or ''}",
                    f"- 优先级：{int(item.get('priority') or 0)}",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _format_plots(items: list[dict[str, Any]]) -> str:
        if not items:
            return ""
        lines = ["【剧情线】"]
        for index, item in enumerate(items, 1):
            lines.extend(
                [
                    f"{index}. {item.get('title') or ''}",
                    f"- 状态：{item.get('status') or ''}",
                    f"- 描述：{item.get('description') or ''}",
                ]
            )
        return "\n".join(line for line in lines if not line.endswith("："))

    @staticmethod
    def _format_timeline(
        items: list[dict[str, Any]],
        chapter_indexes: dict[str, int],
    ) -> str:
        if not items:
            return ""
        lines = ["【时间线】"]
        for index, item in enumerate(items, 1):
            chapter_index = chapter_indexes.get(str(item.get("chapter_id") or ""))
            prefix = f"第 {chapter_index} 章" if chapter_index else f"事件 {item.get('event_order') or index}"
            description = f"：{item.get('description')}" if item.get("description") else ""
            lines.append(f"{index}. {prefix}：{item.get('title') or ''}{description}")
        return "\n".join(lines)

    @staticmethod
    def _truncate_to_fit(
        variables: dict[str, Any],
        field: str,
        manager: ContextBudgetManager,
    ) -> str:
        value = str(variables.get(field) or "")
        low, high = 0, len(value)
        best = ""
        while low <= high:
            middle = (low + high) // 2
            candidate = value[:middle]
            variables[field] = candidate
            if manager.exceeds(variables):
                high = middle - 1
            else:
                best = candidate
                low = middle + 1
        variables[field] = best
        return best
