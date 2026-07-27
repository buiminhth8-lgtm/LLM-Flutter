"""RAG (Retrieval-Augmented Generation) pipeline with a local vector store."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from .config import Config
from .document_loader import Document, DocumentLoader


class EmbeddingModel:
    """Local embedding model using sentence-transformers."""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None

    def load(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self.model_name, device=self.device)

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        if self.model is None:
            self.load()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
        )
        return np.array(embeddings, dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class VectorStore:
    """Simple local vector store using NumPy."""

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
        if int(embeddings.shape[1]) != self.embedding_dim:
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
        if self.embeddings is None:
            self.embeddings = matrix
            self.documents = new_docs
        else:
            self.embeddings = np.vstack([self.embeddings, matrix])
            self.documents.extend(new_docs)
        return len(new_docs)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[Document, float]]:
        """Search for most similar documents using cosine similarity."""
        if self.embeddings is None or not self.documents:
            return []
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        scores = self.embeddings @ query_norm
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.documents[idx], float(scores[idx])) for idx in top_indices]

    def save(self, path: str):
        """Save vector store atomically."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"{target.name}.tmp-", dir=str(target.parent)))
        try:
            if self.embeddings is not None:
                np.save(str(tmp_dir / "embeddings.npy"), self.embeddings)
            else:
                np.save(str(tmp_dir / "embeddings.npy"), np.empty((0, self.embedding_dim or 0), dtype=np.float32))
            docs_data = [{"content": d.content, "metadata": d.metadata} for d in self.documents]
            (tmp_dir / "documents.json").write_text(
                json.dumps(docs_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (tmp_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "embedding_model": self.embedding_model,
                        "embedding_dim": self.embedding_dim,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            if target.exists():
                backup = target.with_name(f"{target.name}.old")
                if backup.exists():
                    shutil.rmtree(backup)
                target.replace(backup)
                tmp_dir.replace(target)
                shutil.rmtree(backup, ignore_errors=True)
            else:
                tmp_dir.replace(target)
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def load(self, path: str):
        """Load vector store from disk and validate model/dimension."""
        root = Path(path)
        emb_path = root / "embeddings.npy"
        doc_path = root / "documents.json"
        meta_path = root / "metadata.json"
        if not (emb_path.exists() and doc_path.exists()):
            return

        metadata = {}
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if metadata.get("embedding_model") and metadata["embedding_model"] != self.embedding_model:
            raise ValueError(
                "当前 embedding 模型与已保存索引不一致，请重建 RAG 索引。"
            )

        embeddings = np.load(str(emb_path))
        if embeddings.ndim != 2:
            raise ValueError("RAG 索引向量文件格式错误，请重建索引。")
        saved_dim = metadata.get("embedding_dim")
        if saved_dim is not None and int(saved_dim) != int(embeddings.shape[1]):
            raise ValueError("RAG 索引向量维度不一致，请重建索引。")

        docs_data = json.loads(doc_path.read_text(encoding="utf-8"))
        self.embeddings = embeddings.astype(np.float32)
        self.embedding_dim = int(embeddings.shape[1]) if embeddings.size else saved_dim
        self.documents = [
            Document(content=item["content"], metadata=item["metadata"])
            for item in docs_data
        ]
        self._hashes = {
            doc.metadata.get("content_hash", "")
            for doc in self.documents
            if doc.metadata.get("content_hash")
        }

    @property
    def count(self) -> int:
        return len(self.documents)

    def clear(self):
        self.embeddings = None
        self.documents = []
        self._hashes = set()


class RAGPipeline:
    """Complete RAG pipeline: load documents, embed, store, and query."""

    def __init__(
        self,
        config: Config,
        embedding_model: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        device: str | None = None,
    ):
        rag_cfg = config.get("rag", {})
        embedding_model = embedding_model or rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5")
        chunk_size = int(chunk_size or rag_cfg.get("chunk_size", 500))
        chunk_overlap = int(chunk_overlap if chunk_overlap is not None else rag_cfg.get("chunk_overlap", 50))
        device = device or rag_cfg.get("device", "cpu")

        self.config = config
        self.doc_loader = DocumentLoader(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding = EmbeddingModel(embedding_model, device=device)
        self.vector_store = VectorStore(embedding_model)
        self.store_dir = config.datasets_dir / "vector_store"

    def ingest_file(self, file_path: str) -> int:
        docs = self.doc_loader.load_file(file_path)
        if not docs:
            return 0
        embeddings = self.embedding.encode([doc.content for doc in docs])
        return self.vector_store.add_documents(docs, embeddings)

    def ingest_directory(self, dir_path: str, recursive: bool = True) -> int:
        docs = self.doc_loader.load_directory(dir_path, recursive=recursive)
        if not docs:
            return 0
        embeddings = self.embedding.encode([doc.content for doc in docs])
        return self.vector_store.add_documents(docs, embeddings)

    def query(self, question: str, top_k: int = 5) -> list[tuple[Document, float]]:
        query_emb = self.embedding.encode_single(question)
        return self.vector_store.search(query_emb, top_k=top_k)

    def build_rag_prompt(
        self,
        question: str,
        top_k: int = 5,
        system_template: str = "",
    ) -> str:
        results = self.query(question, top_k=top_k)
        if not results:
            return question

        context_parts = []
        for idx, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("filename", "unknown")
            page = doc.metadata.get("page")
            page_text = f", page: {page}" if page else ""
            context_parts.append(
                f"[文档片段 {idx}] (来源: {source}{page_text}, 相关度: {score:.2f})\n{doc.content}"
            )
        context_text = "\n\n".join(context_parts)

        if not system_template:
            system_template = self.config.get("rag", {}).get("system_template", "")
        if not system_template:
            system_template = (
                "你是一个智能助手。请根据以下参考资料回答用户的问题。\n"
                "如果参考资料中没有相关信息，请根据你的知识回答并说明。\n\n"
                "参考资料:\n{context}\n\n用户问题: {question}"
            )
        return system_template.format(context=context_text, question=question)

    def save(self):
        self.vector_store.save(str(self.store_dir))

    def load(self) -> bool:
        if (self.store_dir / "embeddings.npy").exists():
            self.vector_store.load(str(self.store_dir))
            return True
        return False

    def clear(self):
        self.vector_store.clear()
        if self.store_dir.exists():
            shutil.rmtree(self.store_dir, ignore_errors=True)

    @property
    def document_count(self) -> int:
        return self.vector_store.count

    def get_ingested_sources(self) -> list[str]:
        sources = {
            doc.metadata.get("source", "unknown")
            for doc in self.vector_store.documents
        }
        return sorted(sources)
