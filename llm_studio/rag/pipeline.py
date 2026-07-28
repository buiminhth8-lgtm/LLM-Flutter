"""RAG pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

from llm_studio.config import Config
from llm_studio.document_loader import Document
from llm_studio.models.storage import ensure_within

from .chunker import ChineseTextChunker
from .config import RAGConfig
from .embeddings import EmbeddingModel
from .index import VectorStore


class RAGPipeline:
    def __init__(
        self,
        config: Config,
        embedding_model: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        device: str | None = None,
    ):
        rag_config = RAGConfig.from_app_config(config)
        if embedding_model:
            rag_config = RAGConfig(
                embedding_model=embedding_model,
                device=device or rag_config.device,
                chunk_size=chunk_size or rag_config.chunk_size,
                chunk_overlap=chunk_overlap if chunk_overlap is not None else rag_config.chunk_overlap,
                top_k=rag_config.top_k,
                index_path=rag_config.index_path,
            )
        self.config = config
        self.rag_config = rag_config
        self.doc_loader = ChineseTextChunker(
            chunk_size=rag_config.chunk_size,
            chunk_overlap=rag_config.chunk_overlap,
        )
        self.embedding = EmbeddingModel(rag_config.embedding_model, device=rag_config.device)
        self.vector_store = VectorStore(rag_config.embedding_model)
        self.store_dir = Path(rag_config.index_path)
        if not self.store_dir.is_absolute():
            self.store_dir = config.config_path.parent / self.store_dir
        self.store_dir = self.store_dir.resolve()

    def ingest_file(self, file_path: str) -> int:
        docs = self.doc_loader.load_file(file_path)
        return self._add_docs(docs)

    def ingest_directory(self, dir_path: str, recursive: bool = True) -> int:
        docs = self.doc_loader.load_directory(dir_path, recursive=recursive)
        return self._add_docs(docs)

    def _add_docs(self, docs: list[Document]) -> int:
        if not docs:
            return 0
        embeddings = self.embedding.encode([doc.content for doc in docs])
        return self.vector_store.add_documents(docs, embeddings)

    def query(self, question: str, top_k: int = 5) -> list[tuple[Document, float]]:
        query_emb = self.embedding.encode_single(question)
        return self.vector_store.search(query_emb, top_k=top_k)

    def build_rag_prompt(self, question: str, top_k: int = 5, system_template: str = "") -> str:
        results = self.query(question, top_k=top_k)
        if not results:
            return question
        context_parts = []
        for idx, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("filename", "unknown")
            title = doc.metadata.get("title")
            title_text = f", title: {title}" if title else ""
            context_parts.append(f"[文档片段 {idx}] (来源: {source}{title_text}, 相关度: {score:.2f})\n{doc.content}")
        template = system_template or self.config.get("rag", {}).get("system_template", "")
        if not template:
            template = (
                "你是一个智能助手。请根据以下参考资料回答用户的问题。\n"
                "如果参考资料中没有相关信息，请根据你的知识回答并说明。\n\n"
                "参考资料:\n{context}\n\n用户问题: {question}"
            )
        return template.format(context="\n\n".join(context_parts), question=question)

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
            if self.store_dir == self.store_dir.parent:
                raise ValueError("????????????")
            ensure_within(self.store_dir, self.store_dir.parent)
            shutil.rmtree(self.store_dir)

    @property
    def document_count(self) -> int:
        return self.vector_store.count

    def get_ingested_sources(self) -> list[str]:
        return sorted({doc.metadata.get("source", "unknown") for doc in self.vector_store.documents})
