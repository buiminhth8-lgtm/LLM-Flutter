"""RAG chunking wrapper."""

from __future__ import annotations

from llm_studio.document_loader import DocumentLoader


class ChineseTextChunker(DocumentLoader):
    """DocumentLoader already implements title/paragraph/sentence fallback splitting."""
