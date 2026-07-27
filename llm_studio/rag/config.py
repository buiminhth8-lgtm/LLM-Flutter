"""RAG configuration model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RAGConfig:
    embedding_model: str
    device: str = "cpu"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 4
    index_path: str = "./data/rag"

    @classmethod
    def from_app_config(cls, config) -> "RAGConfig":
        data = config.get("rag", {})
        return cls(
            embedding_model=data.get("embedding_model", "BAAI/bge-small-zh-v1.5"),
            device=data.get("device", "cpu"),
            chunk_size=int(data.get("chunk_size", 500)),
            chunk_overlap=int(data.get("chunk_overlap", 50)),
            top_k=int(data.get("top_k", 4)),
            index_path=str(data.get("index_path", config.datasets_dir / "vector_store")),
        )
