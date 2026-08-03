"""Memory index build and rebuild orchestration."""

from __future__ import annotations

from typing import Any

from .chunking import MemoryChunker
from .entities import ChunkOptions, MemoryDocument, MemoryIndexResult
from .errors import MemoryIndexFailedError
from .ranking import extract_terms


class MemoryIndexService:
    def __init__(
        self,
        repository: Any,
        *,
        chunker: MemoryChunker | None = None,
        chunk_chars: int = 1200,
        chunk_overlap_chars: int = 120,
    ):
        self.repository = repository
        self.chunker = chunker or MemoryChunker()
        self.options = ChunkOptions(
            chunk_chars=max(200, int(chunk_chars or 1200)),
            chunk_overlap_chars=max(0, int(chunk_overlap_chars or 120)),
        )

    @classmethod
    def from_config(cls, repository: Any, config: Any | None = None) -> MemoryIndexService:
        cfg = config.get("memory", {}) if config is not None else {}
        return cls(
            repository,
            chunk_chars=int(cfg.get("chunk_chars", 1200)),
            chunk_overlap_chars=int(cfg.get("chunk_overlap_chars", 120)),
        )

    def rebuild_project_index(self, project_id: str) -> MemoryIndexResult:
        documents = self.repository.list_documents(
            project_id=project_id,
            status="active",
            limit=10000,
        )
        stale = self.repository.list_documents(
            project_id=project_id,
            status="stale",
            limit=10000,
        )
        warnings: list[dict[str, Any]] = []
        chunks_indexed = 0
        indexed = 0
        for document in [*documents, *stale]:
            result = self.rebuild_document(document["document_id"])
            chunks_indexed += result.chunks_indexed
            indexed += result.documents_indexed
            warnings.extend(result.warnings)
        return MemoryIndexResult(
            project_id=project_id,
            documents_indexed=indexed,
            chunks_indexed=chunks_indexed,
            index_type="sqlite_fts" if self.repository.fts_available else "keyword",
            fts_available=self.repository.fts_available,
            warnings=warnings,
        )

    def rebuild_document(self, document_id: str) -> MemoryIndexResult:
        try:
            document = self.repository.get_document(document_id)
            entity = MemoryDocument.from_mapping(document)
            chunks = self.chunker.chunk_document(entity, self.options)
            chunk_dicts = [chunk.to_insert_dict() for chunk in chunks]
            keywords_for_chunk = {
                str(item["chunk_index"]): extract_terms(
                    f"{document.get('title') or ''}\n{item.get('chunk_text') or ''}"
                )
                for item in chunk_dicts
            }
            inserted = self.repository.replace_document_chunks(
                document_id,
                chunk_dicts,
                keywords_for_chunk=keywords_for_chunk,
                fts_enabled=self.repository.fts_available,
            )
            warnings = []
            if not self.repository.fts_available:
                warnings.append(
                    {
                        "code": "MEMORY_FTS_NOT_AVAILABLE",
                        "message": "SQLite FTS5 不可用，已回退到 keyword 索引。",
                    }
                )
            return MemoryIndexResult(
                project_id=document["project_id"],
                document_id=document_id,
                documents_indexed=1,
                chunks_indexed=inserted,
                index_type="sqlite_fts" if self.repository.fts_available else "keyword",
                fts_available=self.repository.fts_available,
                warnings=warnings,
            )
        except Exception as exc:
            if exc.__class__.__name__.endswith("NotFoundError"):
                raise
            raise MemoryIndexFailedError(str(exc) or "Memory index rebuild failed.") from exc

    def mark_stale_for_source(self, source_type: str, source_id: str) -> None:
        self.repository.mark_stale_for_source(source_type, source_id)
