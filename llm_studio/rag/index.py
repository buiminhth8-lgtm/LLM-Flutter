"""Local NumPy vector index with metadata validation."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from llm_studio.document_loader import Document


SCHEMA_VERSION = 2


class RAGIndexInvalidError(ValueError):
    """Raised when a persisted RAG index is incompatible or corrupt."""


class VectorStore:
    def __init__(self, embedding_model: str, embedding_dim: int | None = None):
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.embeddings: Optional[np.ndarray] = None
        self.documents: list[Document] = []
        self._hashes: set[str] = set()

    def add_documents(self, documents: list[Document], embeddings: np.ndarray) -> int:
        if embeddings.ndim != 2:
            raise ValueError("embeddings must be a 2D matrix")
        if self.embedding_dim is None:
            self.embedding_dim = int(embeddings.shape[1])
        if int(embeddings.shape[1]) != int(self.embedding_dim):
            raise ValueError("向量维度不一致，请重建索引。")

        new_docs: list[Document] = []
        new_embeddings: list[np.ndarray] = []
        for doc, emb in zip(documents, embeddings, strict=False):
            content_hash = doc.metadata.get("content_hash")
            if content_hash and content_hash in self._hashes:
                continue
            if content_hash:
                self._hashes.add(content_hash)
            new_docs.append(doc)
            new_embeddings.append(emb)

        if not new_docs:
            return 0
        matrix = np.vstack(new_embeddings).astype(np.float32)
        self.embeddings = matrix if self.embeddings is None else np.vstack([self.embeddings, matrix])
        self.documents.extend(new_docs)
        return len(new_docs)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[Document, float]]:
        if self.embeddings is None or not self.documents:
            return []
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        scores = self.embeddings @ query_norm
        return [(self.documents[idx], float(scores[idx])) for idx in np.argsort(scores)[::-1][:top_k]]

    def save(self, path: str):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"{target.name}.tmp-", dir=str(target.parent)))
        try:
            embeddings = self.embeddings
            if embeddings is None:
                embeddings = np.empty((0, self.embedding_dim or 0), dtype=np.float32)
            np.save(str(tmp_dir / "embeddings.npy"), embeddings)
            documents = [{"content": doc.content, "metadata": doc.metadata} for doc in self.documents]
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "embedding_model": self.embedding_model,
                "embedding_dimension": int(embeddings.shape[1]) if embeddings.ndim == 2 else 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "documents": len({doc.metadata.get("source") for doc in self.documents}),
                "chunks": len(self.documents),
            }
            (tmp_dir / "documents.json").write_text(json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (tmp_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._validate_directory(tmp_dir)
            backup = target.with_name(f"{target.name}.bak")
            if backup.exists():
                shutil.rmtree(backup)
            if target.exists():
                target.replace(backup)
            tmp_dir.replace(target)
            shutil.rmtree(backup, ignore_errors=True)
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def load(self, path: str):
        root = Path(path)
        if not (root / "embeddings.npy").exists():
            return
        self._validate_directory(root)
        metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        embeddings = np.load(str(root / "embeddings.npy"))
        if metadata["embedding_model"] != self.embedding_model:
            raise RAGIndexInvalidError("当前 embedding 模型与索引不一致，请重建索引。")
        if int(metadata["embedding_dimension"]) != int(embeddings.shape[1]):
            raise RAGIndexInvalidError("索引向量维度不一致，请重建索引。")
        docs_data = json.loads((root / "documents.json").read_text(encoding="utf-8"))
        self.embedding_dim = int(embeddings.shape[1])
        self.embeddings = embeddings.astype(np.float32)
        self.documents = [Document(content=item["content"], metadata=item["metadata"]) for item in docs_data]
        self._hashes = {doc.metadata.get("content_hash", "") for doc in self.documents if doc.metadata.get("content_hash")}

    def clear(self):
        self.embeddings = None
        self.documents = []
        self._hashes = set()

    @property
    def count(self) -> int:
        return len(self.documents)

    def _validate_directory(self, root: Path) -> None:
        try:
            metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
            if int(metadata.get("schema_version", 0)) != SCHEMA_VERSION:
                raise RAGIndexInvalidError("RAG 索引 schema_version 不受支持，请重建索引。")
            np.load(str(root / "embeddings.npy"))
            json.loads((root / "documents.json").read_text(encoding="utf-8"))
        except RAGIndexInvalidError:
            raise
        except Exception as exc:
            raise RAGIndexInvalidError(f"RAG 索引损坏，请重建索引: {exc}") from exc
