"""SQLite persistence for Novel Studio Stage 10 Memory / RAG."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    MemoryDocumentNotFoundError,
    MemoryRetrievalRecordNotFoundError,
    MemorySummaryNotFoundError,
)
from .migrations import has_fts5, initialize_memory_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _json(value: Any, fallback: Any) -> str:
    return json.dumps(value if value is not None else fallback, ensure_ascii=False, sort_keys=True)


class MemoryRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_memory_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @property
    def fts_available(self) -> bool:
        return has_fts5(self.db_path) and self._fts_table_exists()

    def _fts_table_exists(self) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'memory_chunks_fts'"
            ).fetchone()
        return row is not None

    def create_document(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "project_id": data["project_id"],
            "source_type": data["source_type"],
            "source_id": data["source_id"],
            "title": data["title"],
            "content": data["content"],
            "summary": data.get("summary"),
            "tags_json": _json(data.get("tags"), []),
            "priority": int(data.get("priority") or 0),
            "status": data.get("status", "active"),
            "content_hash": data.get("content_hash") or _hash(data["content"]),
            "metadata_json": _json(data.get("metadata"), {}),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_documents (
                  id, project_id, source_type, source_id, title, content, summary,
                  tags_json, priority, status, content_hash, metadata_json,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_document(item["id"])

    def upsert_source_document(self, data: dict[str, Any]) -> tuple[dict[str, Any], bool, bool]:
        metadata = data.get("metadata") or {}
        source_field = metadata.get("source_field")
        existing = self.find_source_document(
            data["project_id"],
            data["source_type"],
            data["source_id"],
            title=data.get("title"),
            source_field=source_field,
        )
        new_hash = data.get("content_hash") or _hash(data.get("content") or "")
        if existing is None:
            return self.create_document({**data, "content_hash": new_hash}), True, True
        changed = existing.get("content_hash") != new_hash
        changes = {
            "title": data.get("title"),
            "content": data.get("content"),
            "summary": data.get("summary"),
            "tags": data.get("tags") or [],
            "priority": data.get("priority") or 0,
            "metadata": metadata,
            "status": "active" if changed or existing.get("status") == "stale" else existing.get("status", "active"),
            "content_hash": new_hash,
        }
        updated = self.update_document(existing["document_id"], changes)
        return updated, False, changed

    def find_source_document(
        self,
        project_id: str,
        source_type: str,
        source_id: str,
        *,
        title: str | None = None,
        source_field: str | None = None,
    ) -> dict[str, Any] | None:
        clauses = [
            "project_id = ?",
            "source_type = ?",
            "source_id = ?",
            "status != 'deleted'",
        ]
        params: list[Any] = [project_id, source_type, source_id]
        if title:
            clauses.append("title = ?")
            params.append(title)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM memory_documents WHERE {' AND '.join(clauses)} ORDER BY created_at ASC",
                params,
            ).fetchall()
        for row in rows:
            item = self._document_row(row)
            if source_field is None or (item.get("metadata") or {}).get("source_field") == source_field:
                return item
        return None

    def update_document(self, document_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get_document(document_id)
        allowed = {
            "title",
            "content",
            "summary",
            "tags",
            "priority",
            "status",
            "content_hash",
            "metadata",
        }
        values: dict[str, Any] = {}
        for key, value in changes.items():
            if key not in allowed:
                continue
            if key == "tags":
                values["tags_json"] = _json(value, [])
            elif key == "metadata":
                values["metadata_json"] = _json(value, {})
            else:
                values[key] = value
        if "content" in values and "content_hash" not in values:
            values["content_hash"] = _hash(values["content"])
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE memory_documents SET {assignments} WHERE id = ?",
                [*values.values(), document_id],
            )
        if cursor.rowcount == 0:
            raise MemoryDocumentNotFoundError(document_id)
        return self.get_document(document_id)

    def get_document(self, document_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM memory_documents WHERE id = ? AND status != 'deleted'",
                (document_id,),
            ).fetchone()
        if row is None:
            raise MemoryDocumentNotFoundError(document_id)
        return self._document_row(row)

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
        clauses = ["status != 'deleted'"]
        params: list[Any] = []
        for field, value in (
            ("project_id", project_id),
            ("source_type", source_type),
            ("source_id", source_id),
            ("status", status),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}"
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM memory_documents{where} ORDER BY updated_at DESC, title ASC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        items = [self._document_row(row) for row in rows]
        if tag:
            return [item for item in items if tag in (item.get("tags") or [])]
        return items

    def mark_stale_for_source(self, source_type: str, source_id: str) -> int:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE memory_documents
                SET status = 'stale', updated_at = ?
                WHERE source_type = ? AND source_id = ? AND status = 'active'
                """,
                (_now(), source_type, source_id),
            )
        return int(cursor.rowcount or 0)

    def archive_document(self, document_id: str) -> dict[str, Any]:
        return self.update_document(document_id, {"status": "archived"})

    def replace_document_chunks(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
        *,
        keywords_for_chunk: dict[str, list[str]],
        fts_enabled: bool,
    ) -> int:
        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id, status FROM memory_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
            if existing is None:
                raise MemoryDocumentNotFoundError(document_id)
            old_chunk_ids = [
                row["id"]
                for row in conn.execute(
                    "SELECT id FROM memory_chunks WHERE document_id = ?",
                    (document_id,),
                ).fetchall()
            ]
            if old_chunk_ids:
                placeholders = ", ".join("?" for _ in old_chunk_ids)
                conn.execute(
                    f"DELETE FROM memory_index_entries WHERE chunk_id IN ({placeholders})",
                    old_chunk_ids,
                )
                if fts_enabled and self._fts_table_exists_for_conn(conn):
                    conn.executemany(
                        "DELETE FROM memory_chunks_fts WHERE chunk_id = ?",
                        [(chunk_id,) for chunk_id in old_chunk_ids],
                    )
            conn.execute("DELETE FROM memory_chunks WHERE document_id = ?", (document_id,))
            now = _now()
            inserted = 0
            for raw in chunks:
                chunk_id = raw.get("id") or str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO memory_chunks (
                      id, document_id, project_id, chunk_index, chunk_text,
                      chunk_summary, token_estimate, char_count, content_hash,
                      metadata_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        raw["document_id"],
                        raw["project_id"],
                        int(raw["chunk_index"]),
                        raw["chunk_text"],
                        raw.get("chunk_summary"),
                        int(raw.get("token_estimate") or 0),
                        int(raw.get("char_count") or 0),
                        raw.get("content_hash") or _hash(raw["chunk_text"]),
                        _json(raw.get("metadata"), {}),
                        raw.get("created_at") or now,
                    ),
                )
                keywords = keywords_for_chunk.get(chunk_id) or keywords_for_chunk.get(str(raw["chunk_index"])) or []
                conn.execute(
                    """
                    INSERT INTO memory_index_entries (
                      id, project_id, chunk_id, index_type, keywords_json,
                      embedding_ref, score_boost, metadata_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        raw["project_id"],
                        chunk_id,
                        "keyword",
                        _json(keywords, []),
                        None,
                        1.0,
                        _json(raw.get("metadata"), {}),
                        now,
                    ),
                )
                if fts_enabled and self._fts_table_exists_for_conn(conn):
                    document_title = (raw.get("metadata") or {}).get("title") or ""
                    conn.execute(
                        """
                        INSERT INTO memory_chunks_fts (chunk_id, project_id, title, chunk_text)
                        VALUES (?, ?, ?, ?)
                        """,
                        (chunk_id, raw["project_id"], document_title, raw["chunk_text"]),
                    )
                    conn.execute(
                        """
                        INSERT INTO memory_index_entries (
                          id, project_id, chunk_id, index_type, keywords_json,
                          embedding_ref, score_boost, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            raw["project_id"],
                            chunk_id,
                            "sqlite_fts",
                            _json(keywords, []),
                            None,
                            1.0,
                            _json(raw.get("metadata"), {}),
                            now,
                        ),
                    )
                inserted += 1
            if str(existing["status"]) in {"active", "stale"}:
                conn.execute(
                    "UPDATE memory_documents SET status = 'active', updated_at = ? WHERE id = ?",
                    (now, document_id),
                )
            else:
                conn.execute(
                    "UPDATE memory_documents SET updated_at = ? WHERE id = ?",
                    (now, document_id),
                )
        return inserted

    @staticmethod
    def _fts_table_exists_for_conn(conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'memory_chunks_fts'"
        ).fetchone()
        return row is not None

    def list_chunks(
        self,
        *,
        project_id: str,
        source_types: list[str] | None = None,
        status: str = "active",
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        clauses = ["d.project_id = ?", "d.status = ?"]
        params: list[Any] = [project_id, status]
        if source_types:
            placeholders = ", ".join("?" for _ in source_types)
            clauses.append(f"d.source_type IN ({placeholders})")
            params.extend(source_types)
        params.append(max(1, min(limit, 10000)))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                  c.*, d.id AS doc_id, d.source_type, d.source_id, d.title,
                  d.summary AS document_summary, d.tags_json AS document_tags_json,
                  d.priority AS document_priority, d.status AS document_status,
                  d.content_hash AS document_content_hash,
                  d.metadata_json AS document_metadata_json,
                  d.created_at AS document_created_at,
                  d.updated_at AS document_updated_at
                FROM memory_chunks c
                JOIN memory_documents d ON d.id = c.document_id
                WHERE {' AND '.join(clauses)}
                ORDER BY d.priority DESC, d.updated_at DESC, d.title ASC, c.chunk_index ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._chunk_join_row(row) for row in rows]

    def create_retrieval_record(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "query_text": data["query_text"],
            "mode": data.get("mode", "retrieve"),
            "top_k": int(data.get("top_k") or 0),
            "budget_json": _json(data.get("budget"), {}),
            "retrieved_chunks_json": _json(data.get("retrieved_chunks"), []),
            "selected_chunks_json": _json(data.get("selected_chunks"), []),
            "warnings_json": _json(data.get("warnings"), []),
            "total_token_estimate": int(data.get("total_token_estimate") or 0),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_retrieval_records (
                  id, project_id, chapter_id, scene_id, query_text, mode, top_k,
                  budget_json, retrieved_chunks_json, selected_chunks_json,
                  warnings_json, total_token_estimate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_retrieval_record(item["id"])

    def get_retrieval_record(self, retrieval_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM memory_retrieval_records WHERE id = ?",
                (retrieval_id,),
            ).fetchone()
        if row is None:
            raise MemoryRetrievalRecordNotFoundError(retrieval_id)
        return self._retrieval_row(row)

    def list_retrieval_records(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if chapter_id:
            clauses.append("chapter_id = ?")
            params.append(chapter_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM memory_retrieval_records{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._retrieval_row(row) for row in rows]

    def create_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "project_id": data["project_id"],
            "chapter_id": data["chapter_id"],
            "summary_type": data.get("summary_type", "short"),
            "summary_text": data["summary_text"],
            "source_text_hash": data["source_text_hash"],
            "generated_by": data.get("generated_by", "manual"),
            "model_id": data.get("model_id"),
            "prompt_template_id": data.get("prompt_template_id"),
            "status": data.get("status", "active"),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chapter_summary_versions (
                  id, project_id, chapter_id, summary_type, summary_text,
                  source_text_hash, generated_by, model_id, prompt_template_id,
                  status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_summary(item["id"])

    def get_summary(self, summary_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chapter_summary_versions WHERE id = ?",
                (summary_id,),
            ).fetchone()
        if row is None:
            raise MemorySummaryNotFoundError(summary_id)
        return self._summary_row(row)

    def list_summaries(
        self,
        *,
        chapter_id: str,
        summary_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clauses = ["chapter_id = ?"]
        params: list[Any] = [chapter_id]
        if summary_type:
            clauses.append("summary_type = ?")
            params.append(summary_type)
        params.append(max(1, min(limit, 200)))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM chapter_summary_versions WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._summary_row(row) for row in rows]

    def activate_summary(self, chapter_id: str, summary_id: str) -> dict[str, Any]:
        summary = self.get_summary(summary_id)
        if summary["chapter_id"] != chapter_id:
            raise MemorySummaryNotFoundError(summary_id)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE chapter_summary_versions
                SET status = 'archived'
                WHERE chapter_id = ? AND summary_type = ? AND id != ? AND status = 'active'
                """,
                (chapter_id, summary["summary_type"], summary_id),
            )
            conn.execute(
                "UPDATE chapter_summary_versions SET status = 'active' WHERE id = ?",
                (summary_id,),
            )
        return self.get_summary(summary_id)

    def project_index_status(self, project_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            docs = conn.execute(
                """
                SELECT
                  COUNT(*) AS total,
                  SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                  SUM(CASE WHEN status = 'stale' THEN 1 ELSE 0 END) AS stale,
                  SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) AS archived
                FROM memory_documents
                WHERE project_id = ? AND status != 'deleted'
                """,
                (project_id,),
            ).fetchone()
            chunks = conn.execute(
                "SELECT COUNT(*) AS count FROM memory_chunks WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            indexes = conn.execute(
                "SELECT index_type, COUNT(*) AS count FROM memory_index_entries WHERE project_id = ? GROUP BY index_type",
                (project_id,),
            ).fetchall()
        return {
            "project_id": project_id,
            "documents": {
                "total": int(docs["total"] or 0),
                "active": int(docs["active"] or 0),
                "stale": int(docs["stale"] or 0),
                "archived": int(docs["archived"] or 0),
            },
            "chunks": int(chunks["count"] or 0),
            "index_entries": {row["index_type"]: int(row["count"] or 0) for row in indexes},
            "fts_available": self.fts_available,
        }

    @staticmethod
    def _document_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["document_id"] = data.pop("id")
        data["tags"] = _loads(data.pop("tags_json"), [])
        data["metadata"] = _loads(data.pop("metadata_json"), {})
        return data

    @staticmethod
    def _chunk_join_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        chunk = {
            "chunk_id": data["id"],
            "document_id": data["document_id"],
            "project_id": data["project_id"],
            "chunk_index": data["chunk_index"],
            "chunk_text": data["chunk_text"],
            "chunk_summary": data["chunk_summary"],
            "token_estimate": data["token_estimate"],
            "char_count": data["char_count"],
            "content_hash": data["content_hash"],
            "metadata": _loads(data["metadata_json"], {}),
            "created_at": data["created_at"],
            "source_type": data["source_type"],
            "source_id": data["source_id"],
            "title": data["title"],
            "document": {
                "document_id": data["doc_id"],
                "source_type": data["source_type"],
                "source_id": data["source_id"],
                "title": data["title"],
                "summary": data["document_summary"],
                "tags": _loads(data["document_tags_json"], []),
                "priority": data["document_priority"],
                "status": data["document_status"],
                "content_hash": data["document_content_hash"],
                "metadata": _loads(data["document_metadata_json"], {}),
                "created_at": data["document_created_at"],
                "updated_at": data["document_updated_at"],
            },
        }
        return chunk

    @staticmethod
    def _retrieval_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["retrieval_id"] = data.pop("id")
        data["budget"] = _loads(data.pop("budget_json"), {})
        data["retrieved_chunks"] = _loads(data.pop("retrieved_chunks_json"), [])
        data["selected_chunks"] = _loads(data.pop("selected_chunks_json"), [])
        data["warnings"] = _loads(data.pop("warnings_json"), [])
        return data

    @staticmethod
    def _summary_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["summary_id"] = data.pop("id")
        return data
