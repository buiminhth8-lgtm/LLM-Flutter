"""Embedding model wrapper."""

from __future__ import annotations

import numpy as np


class EmbeddingModel:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None

    def load(self):
        from sentence_transformers import SentenceTransformer

        print(f"[RAG] embedding-device={self.device}")
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
