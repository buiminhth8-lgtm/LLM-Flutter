"""Deterministic Chinese-friendly memory chunking."""

from __future__ import annotations

import hashlib
import re

from llm_studio.context.estimators import TokenEstimator

from .entities import ChunkOptions, MemoryChunk, MemoryDocument


class MemoryChunker:
    def __init__(self, estimator: TokenEstimator | None = None):
        self.estimator = estimator or TokenEstimator()

    def chunk_document(
        self,
        document: MemoryDocument,
        options: ChunkOptions | None = None,
    ) -> list[MemoryChunk]:
        opts = options or ChunkOptions()
        text = (document.content or "").strip()
        if not text:
            return []
        if document.source_type in {
            "character",
            "world_entry",
            "plot_thread",
            "timeline_event",
            "manual_note",
            "foreshadowing",
            "scene",
        } and self._char_count(text) <= opts.chunk_chars:
            parts = [text]
        else:
            parts = self._split_long_text(
                text,
                chunk_chars=max(200, int(opts.chunk_chars or 1200)),
                overlap_chars=max(0, min(int(opts.chunk_overlap_chars or 0), int(opts.chunk_chars or 1200) // 2)),
            )
        chunks: list[MemoryChunk] = []
        for index, part in enumerate(parts):
            chunk_text = part.strip()
            if not chunk_text:
                continue
            metadata = {
                **document.metadata,
                "title": document.title,
                "source_type": document.source_type,
                "source_id": document.source_id,
                "document_status": document.status,
            }
            chunks.append(
                MemoryChunk(
                    id=None,
                    document_id=document.id,
                    project_id=document.project_id,
                    chunk_index=index,
                    chunk_text=chunk_text,
                    chunk_summary=document.summary,
                    token_estimate=self.estimator.estimate(chunk_text),
                    char_count=self._char_count(chunk_text),
                    content_hash=self._hash(chunk_text),
                    metadata=metadata,
                )
            )
        return chunks

    def _split_long_text(
        self,
        text: str,
        *,
        chunk_chars: int,
        overlap_chars: int,
    ) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
        if not paragraphs:
            paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
        if not paragraphs:
            paragraphs = [text]

        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if self._char_count(paragraph) > chunk_chars:
                if current.strip():
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split_by_chars(paragraph, chunk_chars, overlap_chars))
                continue
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if self._char_count(candidate) <= chunk_chars:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                overlap = self._tail_non_space(current, overlap_chars)
                current = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _split_by_chars(self, text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
        compact_positions = [idx for idx, char in enumerate(text) if not char.isspace()]
        if len(compact_positions) <= chunk_chars:
            return [text]
        chunks: list[str] = []
        start_count = 0
        while start_count < len(compact_positions):
            end_count = min(len(compact_positions), start_count + chunk_chars)
            start_index = compact_positions[start_count]
            end_index = compact_positions[end_count - 1] + 1
            chunks.append(text[start_index:end_index].strip())
            if end_count >= len(compact_positions):
                break
            start_count = max(end_count - overlap_chars, start_count + 1)
        return chunks

    @staticmethod
    def _tail_non_space(text: str, chars: int) -> str:
        if chars <= 0:
            return ""
        compact = [char for char in text if not char.isspace()]
        if len(compact) <= chars:
            return text.strip()
        target = "".join(compact[-chars:])
        pos = text.rfind(target[: min(8, len(target))])
        return text[pos:].strip() if pos >= 0 else target

    @staticmethod
    def _char_count(text: str) -> int:
        return sum(1 for char in (text or "").strip() if not char.isspace())

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

