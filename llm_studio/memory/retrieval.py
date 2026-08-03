"""Memory retrieval execution and trace persistence."""

from __future__ import annotations

from typing import Any

from .errors import MemoryRetrieveFailedError
from .ranking import MemoryRanker
from .sources import validate_source_type


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


class MemoryRetrievalService:
    def __init__(self, repository: Any, *, ranker: MemoryRanker | None = None):
        self.repository = repository
        self.ranker = ranker or MemoryRanker()

    def retrieve(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        try:
            project_id = data["project_id"]
            query_text = str(data.get("query_text") or "").strip()
            top_k = max(1, min(int(data.get("top_k") or 12), 50))
            budget = data.get("budget") or {}
            max_tokens = max(1, int(budget.get("max_memory_tokens") or 1200))
            max_chunks = max(1, min(int(budget.get("max_chunks") or top_k), top_k))
            filters = data.get("filters") or {}
            source_types = filters.get("source_types") or []
            source_types = [validate_source_type(item) for item in source_types]
            status = str(filters.get("status") or "active")
            warnings: list[dict[str, Any]] = []
            if not self.repository.fts_available:
                warnings.append(
                    {
                        "code": "MEMORY_FTS_NOT_AVAILABLE",
                        "message": "SQLite FTS5 不可用，已回退到 keyword retrieval。",
                    }
                )
            chunks = self.repository.list_chunks(
                project_id=project_id,
                source_types=source_types or None,
                status=status,
                limit=10000,
            )
            ranked = self.ranker.rank(
                chunks,
                query_text=query_text,
                chapter_id=data.get("chapter_id"),
                scene_id=data.get("scene_id"),
            )
            retrieved = [self._payload(item.chunk, item.score, item.explain) for item in ranked[:top_k]]
            selected: list[dict[str, Any]] = []
            total_tokens = 0
            for item in retrieved:
                estimate = int(item.get("token_estimate") or 0)
                if len(selected) >= max_chunks:
                    continue
                if total_tokens + estimate > max_tokens:
                    continue
                selected.append(item)
                total_tokens += estimate
            if len(selected) < len(retrieved):
                warnings.append(
                    {
                        "code": "MEMORY_BUDGET_EXCEEDED",
                        "message": "Memory 检索结果已按 max_memory_tokens / max_chunks 裁剪。",
                    }
                )
            selected_ids = [item["chunk_id"] for item in selected]
            record = None
            if data.get("save_retrieval_record", True):
                record = self.repository.create_retrieval_record(
                    {
                        "project_id": project_id,
                        "chapter_id": data.get("chapter_id"),
                        "scene_id": data.get("scene_id"),
                        "query_text": query_text,
                        "mode": data.get("mode", "retrieve"),
                        "top_k": top_k,
                        "budget": {"max_memory_tokens": max_tokens, "max_chunks": max_chunks},
                        "retrieved_chunks": retrieved,
                        "selected_chunks": selected_ids,
                        "warnings": warnings,
                        "total_token_estimate": total_tokens,
                    }
                )
            return {
                "retrieval_id": record["retrieval_id"] if record else None,
                "project_id": project_id,
                "chapter_id": data.get("chapter_id"),
                "scene_id": data.get("scene_id"),
                "query_text": query_text,
                "mode": data.get("mode", "retrieve"),
                "chunks": selected,
                "retrieved_chunks": retrieved,
                "selected_chunks": selected_ids,
                "total_token_estimate": total_tokens,
                "warnings": warnings,
            }
        except Exception as exc:
            if exc.__class__.__name__.startswith("Memory"):
                raise
            raise MemoryRetrieveFailedError(str(exc) or "Memory retrieval failed.") from exc

    @staticmethod
    def _payload(chunk: dict[str, Any], score: float, explain: dict[str, Any]) -> dict[str, Any]:
        document = chunk.get("document") or {}
        return {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "source_type": document.get("source_type") or chunk.get("source_type"),
            "source_id": document.get("source_id") or chunk.get("source_id"),
            "title": document.get("title") or chunk.get("title") or "",
            "text": chunk.get("chunk_text") or "",
            "score": score,
            "token_estimate": int(chunk.get("token_estimate") or 0),
            "char_count": int(chunk.get("char_count") or 0),
            "metadata": chunk.get("metadata") or {},
            "explain": explain,
        }

