"""Internal entities for Novel Studio Memory / RAG."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryDocument:
    id: str
    project_id: str
    source_type: str
    source_id: str
    title: str
    content: str
    summary: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: int = 0
    status: str = "active"
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> MemoryDocument:
        return cls(
            id=str(data.get("document_id") or data.get("id") or ""),
            project_id=str(data.get("project_id") or ""),
            source_type=str(data.get("source_type") or ""),
            source_id=str(data.get("source_id") or ""),
            title=str(data.get("title") or ""),
            content=str(data.get("content") or ""),
            summary=data.get("summary"),
            tags=list(data.get("tags") or []),
            priority=int(data.get("priority") or 0),
            status=str(data.get("status") or "active"),
            content_hash=str(data.get("content_hash") or ""),
            metadata=dict(data.get("metadata") or {}),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
        )


@dataclass(frozen=True)
class ChunkOptions:
    chunk_chars: int = 1200
    chunk_overlap_chars: int = 120


@dataclass(frozen=True)
class MemoryChunk:
    id: str | None
    document_id: str
    project_id: str
    chunk_index: int
    chunk_text: str
    chunk_summary: str | None = None
    token_estimate: int = 0
    char_count: int = 0
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_insert_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "project_id": self.project_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "chunk_summary": self.chunk_summary,
            "token_estimate": self.token_estimate,
            "char_count": self.char_count,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class MemoryIndexResult:
    project_id: str | None
    document_id: str | None = None
    documents_indexed: int = 0
    chunks_indexed: int = 0
    index_type: str = "keyword"
    fts_available: bool = False
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "document_id": self.document_id,
            "documents_indexed": self.documents_indexed,
            "chunks_indexed": self.chunks_indexed,
            "index_type": self.index_type,
            "fts_available": self.fts_available,
            "warnings": self.warnings,
        }

