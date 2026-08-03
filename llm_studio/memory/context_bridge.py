"""Bridge between Stage 10 Memory retrieval and Stage 3 ContextAssembler."""

from __future__ import annotations

from typing import Any

from llm_studio.context.budget import ContextBudgetManager, normalize_budget

from .sources import source_label


class ContextMemoryBridge:
    def __init__(self, memory_service: Any):
        self.memory_service = memory_service

    def enrich(self, context: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        memory = request.get("memory") or {}
        if not memory.get("enabled", False):
            return context
        variables = dict(context.get("variables") or {})
        query_text = str(memory.get("query_text") or "").strip()
        if not query_text:
            query_text = str(
                variables.get("current_chapter_goal")
                or variables.get("user_instruction")
                or variables.get("chapter_outline")
                or ""
            ).strip()
        retrieve_request = {
            "project_id": context["project_id"],
            "chapter_id": context.get("chapter_id"),
            "scene_id": context.get("scene_id"),
            "query_text": query_text,
            "mode": context.get("mode") or request.get("mode") or "chapter_generate",
            "top_k": int(memory.get("top_k") or 12),
            "budget": {
                "max_memory_tokens": int(memory.get("max_memory_tokens") or 1200),
                "max_chunks": int(memory.get("max_chunks") or memory.get("top_k") or 8),
            },
            "filters": {
                "source_types": list(memory.get("source_types") or []),
                "status": memory.get("status") or "active",
            },
            "save_retrieval_record": bool(memory.get("save_retrieval_record", True)),
        }
        result = self.memory_service.retrieve(retrieve_request)
        chunks = list(result.get("chunks") or [])
        warnings = [*context.get("warnings", []), *result.get("warnings", [])]
        selected_items = dict(context.get("selected_items") or {})
        selected_items["memory_chunks"] = [item["chunk_id"] for item in chunks]

        variables = self._with_memory_variables(variables, chunks, result.get("warnings") or [])
        manager = ContextBudgetManager(normalize_budget(context.get("budget") or request.get("target_budget")))
        trimmed: list[str] = []
        while chunks and manager.exceeds(variables):
            removed = chunks.pop()
            trimmed.append(removed["chunk_id"])
            selected_items["memory_chunks"] = [item["chunk_id"] for item in chunks]
            variables = self._with_memory_variables(variables, chunks, result.get("warnings") or [])
        if trimmed:
            warnings.append(
                {
                    "code": "MEMORY_BUDGET_EXCEEDED",
                    "message": "Memory 注入后超出 ContextAssembler 预算，已裁剪低分记忆。",
                    "affected": trimmed,
                }
            )
        estimated_tokens, estimated_chars = manager.measure(variables)
        budget_payload = {
            **(context.get("budget") or {}),
            "estimated_tokens": estimated_tokens,
            "estimated_chars": estimated_chars,
        }
        return {
            **context,
            "variables": variables,
            "selected_items": selected_items,
            "warnings": warnings,
            "estimated_tokens": estimated_tokens,
            "estimated_chars": estimated_chars,
            "budget": budget_payload,
            "retrieval_id": result.get("retrieval_id"),
        }

    def _with_memory_variables(
        self,
        variables: dict[str, Any],
        chunks: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped = {
            "character": [],
            "world_entry": [],
            "plot_thread": [],
            "timeline_event": [],
            "foreshadowing": [],
        }
        for chunk in chunks:
            grouped.setdefault(chunk.get("source_type") or "", []).append(chunk)
        return {
            **variables,
            "retrieved_memory": self.format_retrieved_memory(chunks),
            "retrieved_characters": self.format_retrieved_memory(grouped.get("character") or []),
            "retrieved_world_entries": self.format_retrieved_memory(grouped.get("world_entry") or []),
            "retrieved_plot_threads": self.format_retrieved_memory(grouped.get("plot_thread") or []),
            "retrieved_timeline_events": self.format_retrieved_memory(grouped.get("timeline_event") or []),
            "retrieved_foreshadowing": self.format_retrieved_memory(grouped.get("foreshadowing") or []),
            "memory_warnings": "\n".join(str(item.get("message") or item.get("code") or "") for item in warnings),
        }

    @staticmethod
    def format_retrieved_memory(chunks: list[dict[str, Any]]) -> str:
        if not chunks:
            return ""
        lines = ["【相关记忆】"]
        for index, chunk in enumerate(chunks, 1):
            lines.extend(
                [
                    f"{index}. 来源：{source_label(chunk.get('source_type') or '')} / {chunk.get('title') or ''}",
                    f"内容：{chunk.get('text') or ''}",
                ]
            )
        return "\n\n".join(lines)

