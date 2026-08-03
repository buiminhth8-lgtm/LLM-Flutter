"""MemoryService orchestration for Novel Studio Stage 10."""

from __future__ import annotations

import hashlib
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from llm_studio.api import errors as api_errors
from llm_studio.novels.errors import NovelError
from llm_studio.writing.errors import WritingRuntimeError

from .errors import (
    MemoryModelNotFoundError,
    MemoryModelNotLoadedError,
    MemoryProjectNotFoundError,
    MemorySourceNotFoundError,
    MemorySummaryEmptyError,
    MemorySummaryGenerateFailedError,
)
from .indexing import MemoryIndexService
from .repository import MemoryRepository
from .retrieval import MemoryRetrievalService
from .sources import parse_tags, should_index_status, validate_document_status, validate_source_type
from .summaries import build_summary_prompt, validate_summary_type

_SENSITIVE_KEY_MARKERS = (
    "token",
    "api_key",
    "authorization",
    "password",
    "secret",
    "cookie",
    "file_path",
    "directory_path",
    "model_path",
    "local_path",
)
_WINDOWS_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\)[^\s\"']+")
_POSIX_PATH = re.compile(r"(?<!\w)/(?:home|root|Users|var|tmp)/[^\s\"']+")


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _safe_text(value: Any) -> str:
    text = str(value or "")
    text = _WINDOWS_PATH.sub("<redacted-path>", text)
    return _POSIX_PATH.sub("<redacted-path>", text)


def _safe_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS):
                result[str(key)] = "<redacted>"
            else:
                result[str(key)] = _safe_metadata(item)
        return result
    if isinstance(value, list):
        return [_safe_metadata(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


class MemoryService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        writing_service: Any | None = None,
        adapter_evaluation_service: Any | None = None,
        chunk_chars: int = 1200,
        chunk_overlap_chars: int = 120,
    ):
        self.db_path = Path(db_path)
        self.novel_service = novel_service
        self.writing_service = writing_service
        self.adapter_evaluation_service = adapter_evaluation_service
        self.records = MemoryRepository(self.db_path)
        self.index_service = MemoryIndexService(
            self.records,
            chunk_chars=chunk_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        )
        self.retrieval_service = MemoryRetrievalService(self.records)

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        writing_service: Any | None = None,
        adapter_evaluation_service: Any | None = None,
    ) -> MemoryService:
        cfg = config.get("memory", {}) if config is not None else {}
        fallback = (
            config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite")
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(
            Path(cfg.get("db_path", fallback)),
            novel_service=novel_service,
            writing_service=writing_service,
            adapter_evaluation_service=adapter_evaluation_service,
            chunk_chars=int(cfg.get("chunk_chars", 1200)),
            chunk_overlap_chars=int(cfg.get("chunk_overlap_chars", 120)),
        )

    def list_documents(
        self,
        *,
        project_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if project_id:
            self._project(project_id)
        if source_type:
            validate_source_type(source_type)
        if status:
            validate_document_status(status)
        return self.records.list_documents(
            project_id=project_id,
            source_type=source_type,
            source_id=source_id,
            status=status,
            tag=tag,
            limit=limit,
            offset=offset,
        )

    def create_document(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        self._project(data["project_id"])
        source_type = validate_source_type(data.get("source_type") or "manual_note")
        status = validate_document_status(data.get("status") or "active")
        title = self._require_text(data.get("title"), "title")
        content = self._require_text(data.get("content"), "content")
        source_id = data.get("source_id") or f"manual-{uuid.uuid4()}"
        document = self.records.create_document(
            {
                "project_id": data["project_id"],
                "source_type": source_type,
                "source_id": source_id,
                "title": title,
                "content": _safe_text(content),
                "summary": _safe_text(data.get("summary")) if data.get("summary") else None,
                "tags": parse_tags(data.get("tags")),
                "priority": int(data.get("priority") or 0),
                "status": status,
                "metadata": _safe_metadata(data.get("metadata") or {}),
            }
        )
        if should_index_status(document["status"]):
            self.index_service.rebuild_document(document["document_id"])
        return self.records.get_document(document["document_id"])

    def update_document(self, document_id: str, request: Any) -> dict[str, Any]:
        current = self.records.get_document(document_id)
        data = _model_dump(request)
        changes: dict[str, Any] = {}
        if "title" in data and data["title"] is not None:
            changes["title"] = self._require_text(data["title"], "title")
        if "content" in data and data["content"] is not None:
            changes["content"] = _safe_text(self._require_text(data["content"], "content"))
        if "summary" in data:
            changes["summary"] = _safe_text(data.get("summary")) if data.get("summary") else None
        if "tags" in data and data["tags"] is not None:
            changes["tags"] = parse_tags(data["tags"])
        if "priority" in data and data["priority"] is not None:
            changes["priority"] = int(data["priority"])
        if "status" in data and data["status"] is not None:
            changes["status"] = validate_document_status(data["status"])
        if "metadata" in data and data["metadata"] is not None:
            changes["metadata"] = _safe_metadata(data["metadata"])
        updated = self.records.update_document(document_id, changes)
        if (
            ("content" in changes or "title" in changes or "metadata" in changes)
            and should_index_status(updated["status"])
        ):
            self.index_service.rebuild_document(document_id)
        elif current["status"] != updated["status"] and not should_index_status(updated["status"]):
            self.records.replace_document_chunks(
                document_id,
                [],
                keywords_for_chunk={},
                fts_enabled=self.records.fts_available,
            )
        return self.records.get_document(document_id)

    def get_document(self, document_id: str) -> dict[str, Any]:
        return self.records.get_document(document_id)

    def archive_document(self, document_id: str) -> dict[str, Any]:
        document = self.records.archive_document(document_id)
        self.records.replace_document_chunks(
            document_id,
            [],
            keywords_for_chunk={},
            fts_enabled=self.records.fts_available,
        )
        return document

    def build_from_novel(self, project_id: str, request: Any) -> dict[str, Any]:
        self._project(project_id)
        data = _model_dump(request)
        include = data.get("include") or {}
        if hasattr(include, "model_dump"):
            include = include.model_dump()
        defaults = {
            "chapters": True,
            "scenes": True,
            "characters": True,
            "world_entries": True,
            "plot_threads": True,
            "timeline_events": True,
            "revisions": True,
            "generations": False,
            "adapter_eval_results": False,
        }
        include = {**defaults, **(include or {})}
        created = 0
        updated = 0
        unchanged = 0
        document_ids: list[str] = []
        for payload in self._source_payloads(project_id, include):
            document, was_created, changed = self.records.upsert_source_document(payload)
            document_ids.append(document["document_id"])
            if was_created:
                created += 1
            elif changed:
                updated += 1
            else:
                unchanged += 1
        index_result = None
        if data.get("rebuild_index", True):
            index_result = self.index_service.rebuild_project_index(project_id).to_dict()
        return {
            "project_id": project_id,
            "documents_created": created,
            "documents_updated": updated,
            "documents_unchanged": unchanged,
            "document_ids": document_ids,
            "index": index_result,
        }

    def rebuild_project_index(self, project_id: str) -> dict[str, Any]:
        self._project(project_id)
        return self.index_service.rebuild_project_index(project_id).to_dict()

    def rebuild_document_index(self, document_id: str) -> dict[str, Any]:
        document = self.records.get_document(document_id)
        self._project(document["project_id"])
        return self.index_service.rebuild_document(document_id).to_dict()

    def get_project_index_status(self, project_id: str) -> dict[str, Any]:
        self._project(project_id)
        return self.records.project_index_status(project_id)

    def retrieve(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        self._project(data["project_id"])
        for source_type in (data.get("filters") or {}).get("source_types") or []:
            validate_source_type(source_type)
        return self.retrieval_service.retrieve(data)

    def list_retrieval_records(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if project_id:
            self._project(project_id)
        return self.records.list_retrieval_records(
            project_id=project_id,
            chapter_id=chapter_id,
            limit=limit,
            offset=offset,
        )

    def get_retrieval_record(self, retrieval_id: str) -> dict[str, Any]:
        return self.records.get_retrieval_record(retrieval_id)

    def list_chapter_summaries(
        self,
        chapter_id: str,
        *,
        summary_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        self._chapter(chapter_id)
        return self.records.list_summaries(
            chapter_id=chapter_id,
            summary_type=summary_type,
            limit=limit,
        )

    def create_chapter_summary(self, chapter_id: str, request: Any) -> dict[str, Any]:
        chapter = self._chapter(chapter_id)
        data = _model_dump(request)
        summary_text = self._require_text(data.get("summary_text"), "summary_text")
        source_hash = _hash(chapter.get("final_content") or chapter.get("draft_content") or chapter.get("summary") or "")
        status = "active" if data.get("set_active", True) else "draft"
        summary = self.records.create_summary(
            {
                "project_id": chapter["project_id"],
                "chapter_id": chapter_id,
                "summary_type": validate_summary_type(data.get("summary_type")),
                "summary_text": summary_text,
                "source_text_hash": source_hash,
                "generated_by": "manual",
                "status": status,
            }
        )
        if status == "active":
            summary = self.activate_chapter_summary(chapter_id, summary["summary_id"])
        return summary

    async def generate_chapter_summary(self, chapter_id: str, request: Any) -> dict[str, Any]:
        chapter = self._chapter(chapter_id)
        data = _model_dump(request)
        source_field = str(data.get("source") or "draft_content")
        if source_field not in {"draft_content", "final_content", "summary"}:
            source_field = "draft_content"
        source_text = self._require_text(chapter.get(source_field), source_field)
        max_chars = max(50, min(int(data.get("max_chars") or 500), 5000))
        if self.writing_service is None or getattr(self.writing_service, "runtime_bridge", None) is None:
            raise MemorySummaryGenerateFailedError("WritingRuntimeBridge is not configured.")
        prompt = build_summary_prompt(source_text, max_chars=max_chars)
        try:
            runtime_result = await self.writing_service.runtime_bridge.generate_text(
                generation_id=f"summary-{uuid.uuid4()}",
                model_id=data["model_id"],
                adapter_id=None,
                prompt=prompt,
                generation_params={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": max(64, min(2048, max_chars * 2)),
                    "repetition_penalty": 1.05,
                    "stop": [],
                },
            )
        except WritingRuntimeError as exc:
            if exc.code == api_errors.WRITING_MODEL_NOT_FOUND:
                raise MemoryModelNotFoundError(exc.message) from exc
            if exc.code == api_errors.WRITING_MODEL_NOT_LOADED:
                raise MemoryModelNotLoadedError(exc.message) from exc
            raise MemorySummaryGenerateFailedError(exc.message) from exc
        summary_text = _safe_text(runtime_result.text).strip()
        if not summary_text:
            raise MemorySummaryEmptyError("Generated summary is empty.")
        if len(summary_text) > max_chars:
            summary_text = summary_text[:max_chars]
        status = "active" if data.get("set_active", False) else "draft"
        summary = self.records.create_summary(
            {
                "project_id": chapter["project_id"],
                "chapter_id": chapter_id,
                "summary_type": validate_summary_type(data.get("summary_type")),
                "summary_text": summary_text,
                "source_text_hash": _hash(source_text),
                "generated_by": "model",
                "model_id": data.get("model_id"),
                "prompt_template_id": data.get("prompt_template_id"),
                "status": status,
            }
        )
        if status == "active":
            summary = self.activate_chapter_summary(chapter_id, summary["summary_id"])
        return summary

    def activate_chapter_summary(
        self,
        chapter_id: str,
        summary_id: str,
        *,
        sync_to_chapter: bool = True,
    ) -> dict[str, Any]:
        chapter = self._chapter(chapter_id)
        summary = self.records.activate_summary(chapter_id, summary_id)
        if sync_to_chapter:
            self.novel_service.update_chapter(
                chapter_id,
                {"summary": summary["summary_text"]},
            )
        self.records.upsert_source_document(
            {
                "project_id": chapter["project_id"],
                "source_type": "chapter",
                "source_id": chapter_id,
                "title": f"章节摘要：{chapter.get('title') or chapter_id}",
                "content": summary["summary_text"],
                "summary": summary["summary_text"],
                "tags": ["summary", summary["summary_type"]],
                "priority": 4,
                "status": "active",
                "metadata": {"source_field": "summary", "summary_id": summary_id},
            }
        )
        return summary

    def mark_stale_for_source(self, source_type: str, source_id: str) -> None:
        validate_source_type(source_type)
        self.records.mark_stale_for_source(source_type, source_id)

    def _source_payloads(self, project_id: str, include: dict[str, Any]) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        if include.get("characters", True):
            payloads.extend(self._character_payload(item) for item in self.novel_service.list_characters(project_id, limit=10000) if should_index_status(item.get("status")))
        if include.get("world_entries", True):
            payloads.extend(self._world_payload(item) for item in self.novel_service.list_world_entries(project_id, limit=10000) if should_index_status(item.get("status")))
        if include.get("plot_threads", True):
            payloads.extend(self._plot_payload(item) for item in self.novel_service.list_plot_threads(project_id, limit=10000) if should_index_status(item.get("status")))
        if include.get("timeline_events", True):
            payloads.extend(self._timeline_payload(item) for item in self.novel_service.list_timeline(project_id, limit=10000) if should_index_status(item.get("status")))
        if include.get("chapters", True):
            for chapter in self.novel_service.list_chapters(project_id, limit=10000):
                if not should_index_status(chapter.get("status")):
                    continue
                payloads.extend(self._chapter_payloads(chapter))
        if include.get("scenes", True):
            for chapter in self.novel_service.list_chapters(project_id, limit=10000):
                for scene in self.novel_service.list_scenes(chapter["id"], limit=10000):
                    if should_index_status(scene.get("status")):
                        payloads.append(self._scene_payload(scene))
        if include.get("revisions", True):
            payloads.extend(self._revision_payloads(project_id))
        if include.get("generations", False):
            payloads.extend(self._generation_payloads(project_id))
        if include.get("adapter_eval_results", False):
            payloads.extend(self._adapter_eval_payloads(project_id))
        return [item for item in payloads if item.get("content")]

    def _chapter_payloads(self, chapter: dict[str, Any]) -> list[dict[str, Any]]:
        title = chapter.get("title") or chapter["id"]
        payloads = []
        if (chapter.get("summary") or "").strip():
            payloads.append(
                self._payload(
                    chapter["project_id"],
                    "chapter",
                    chapter["id"],
                    f"章节摘要：{title}",
                    chapter["summary"],
                    priority=4,
                    tags=["summary"],
                    metadata={"source_field": "summary", "chapter_id": chapter["id"]},
                )
            )
        content = (chapter.get("final_content") or "").strip()
        source_field = "final_content"
        priority = 3
        if not content:
            content = (chapter.get("draft_content") or "").strip()
            source_field = "draft_content"
            priority = 1
        if content:
            payloads.append(
                self._payload(
                    chapter["project_id"],
                    "chapter",
                    chapter["id"],
                    f"章节正文：{title}",
                    content,
                    priority=priority,
                    tags=[source_field],
                    metadata={"source_field": source_field, "chapter_id": chapter["id"]},
                )
            )
        return payloads

    def _scene_payload(self, scene: dict[str, Any]) -> dict[str, Any]:
        content = "\n".join(
            part
            for part in (
                f"场景：{scene.get('title') or ''}",
                f"地点：{scene.get('location') or ''}",
                f"大纲：{scene.get('outline') or ''}",
                f"内容：{scene.get('content') or ''}",
                f"时间线备注：{scene.get('timeline_note') or ''}",
            )
            if not part.endswith("：")
        )
        return self._payload(
            scene["project_id"],
            "scene",
            scene["id"],
            scene.get("title") or scene["id"],
            content,
            priority=2,
            metadata={"chapter_id": scene.get("chapter_id"), "scene_id": scene["id"]},
        )

    def _character_payload(self, item: dict[str, Any]) -> dict[str, Any]:
        content = "\n".join(
            part
            for part in (
                f"人物：{item.get('name') or ''}",
                f"别名：{item.get('aliases') or ''}",
                f"角色：{item.get('role') or ''}",
                f"性格：{item.get('personality') or ''}",
                f"背景：{item.get('background') or ''}",
                f"目标：{item.get('goals') or ''}",
                f"关系：{item.get('relationships') or ''}",
                f"说话风格：{item.get('speech_style') or ''}",
                f"外貌：{item.get('appearance') or ''}",
                f"备注：{item.get('notes') or ''}",
            )
            if not part.endswith("：")
        )
        return self._payload(
            item["project_id"],
            "character",
            item["id"],
            item.get("name") or item["id"],
            content,
            priority=6,
            metadata={"source_field": "character_card"},
        )

    def _world_payload(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._payload(
            item["project_id"],
            "world_entry",
            item["id"],
            item.get("title") or item["id"],
            f"{item.get('category') or ''}\n{item.get('content') or ''}".strip(),
            priority=int(item.get("priority") or 0) + 5,
            tags=parse_tags(item.get("tags")),
            metadata={"category": item.get("category")},
        )

    def _plot_payload(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._payload(
            item["project_id"],
            "plot_thread",
            item["id"],
            item.get("title") or item["id"],
            f"{item.get('title') or ''}\n状态：{item.get('status') or ''}\n{item.get('description') or ''}".strip(),
            priority=int(item.get("priority") or 0) + (5 if item.get("status") in {"open", "in_progress"} else 0),
            metadata={"related_character_ids": item.get("related_character_ids")},
        )

    def _timeline_payload(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._payload(
            item["project_id"],
            "timeline_event",
            item["id"],
            item.get("title") or item["id"],
            f"{item.get('title') or ''}\n{item.get('description') or ''}".strip(),
            priority=3,
            metadata={
                "chapter_id": item.get("chapter_id"),
                "scene_id": item.get("scene_id"),
                "event_order": item.get("event_order"),
                "involved_character_ids": item.get("involved_character_ids"),
            },
        )

    def _revision_payloads(self, project_id: str) -> list[dict[str, Any]]:
        rows = self._query_rows(
            """
            SELECT * FROM revision_records
            WHERE project_id = ? AND status != 'archived' AND edited_text != ''
            ORDER BY updated_at DESC
            """,
            (project_id,),
        )
        payloads = []
        for row in rows:
            score = int(row.get("user_score") or 0)
            priority = 4 + max(0, score)
            payloads.append(
                self._payload(
                    project_id,
                    "revision",
                    row["id"],
                    f"修订稿：{row.get('chapter_id') or row['id']}",
                    row.get("edited_text") or "",
                    priority=priority,
                    tags=["revision"],
                    metadata={
                        "chapter_id": row.get("chapter_id"),
                        "generation_id": row.get("generation_id"),
                        "user_score": row.get("user_score"),
                        "status": row.get("status"),
                    },
                )
            )
        return payloads

    def _generation_payloads(self, project_id: str) -> list[dict[str, Any]]:
        rows = self._query_rows(
            """
            SELECT * FROM generation_records
            WHERE project_id = ? AND status = 'succeeded' AND model_output != ''
            ORDER BY created_at DESC
            """,
            (project_id,),
        )
        return [
            self._payload(
                project_id,
                "generation",
                row["id"],
                f"生成记录：{row.get('chapter_id') or row['id']}",
                row.get("model_output") or "",
                priority=1,
                tags=["generation"],
                metadata={"chapter_id": row.get("chapter_id"), "mode": row.get("mode")},
            )
            for row in rows
        ]

    def _adapter_eval_payloads(self, project_id: str) -> list[dict[str, Any]]:
        rows = self._query_rows(
            """
            SELECT r.*, c.project_id, c.chapter_id
            FROM adapter_evaluation_results r
            JOIN adapter_evaluation_cases c ON c.id = r.case_id
            WHERE c.project_id = ? AND r.status = 'succeeded' AND r.output_text != ''
            ORDER BY r.created_at DESC
            """,
            (project_id,),
        )
        return [
            self._payload(
                project_id,
                "adapter_eval_result",
                row["id"],
                f"Adapter评估：{row.get('variant') or row['id']}",
                row.get("output_text") or "",
                priority=1,
                tags=["adapter_eval_result", row.get("variant") or ""],
                metadata={"chapter_id": row.get("chapter_id"), "variant": row.get("variant")},
            )
            for row in rows
        ]

    def _query_rows(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                return [dict(row) for row in conn.execute(sql, params).fetchall()]
        except sqlite3.OperationalError:
            return []

    def _payload(
        self,
        project_id: str,
        source_type: str,
        source_id: str,
        title: str,
        content: str,
        *,
        priority: int = 0,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_source_type(source_type)
        safe_content = _safe_text(content).strip()
        return {
            "project_id": project_id,
            "source_type": source_type,
            "source_id": source_id,
            "title": _safe_text(title).strip() or source_id,
            "content": safe_content,
            "summary": None,
            "tags": [tag for tag in (tags or []) if tag],
            "priority": int(priority or 0),
            "status": "active",
            "content_hash": _hash(safe_content),
            "metadata": _safe_metadata(metadata or {}),
        }

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise MemoryProjectNotFoundError(project_id) from exc

    def _chapter(self, chapter_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise MemorySourceNotFoundError(f"Chapter not found: {chapter_id}") from exc

    @staticmethod
    def _require_text(value: str | None, field: str) -> str:
        text = (value or "").strip()
        if not text:
            raise MemorySummaryEmptyError(f"{field} is required.")
        return text
