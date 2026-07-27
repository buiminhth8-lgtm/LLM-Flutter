import numpy as np
import pytest

from llm_studio.document_loader import Document, DocumentLoader
from llm_studio.rag import VectorStore


def test_chinese_sentence_split_prefers_punctuation():
    loader = DocumentLoader(chunk_size=20, chunk_overlap=2)
    chunks = loader._split_text("第一段。第二句！\n\n第二段包含更多中文内容，用来测试切分。")
    assert len(chunks) >= 2
    assert any("第一段" in chunk for chunk in chunks)


def test_vector_store_deduplicates_hashes():
    store = VectorStore("embed", embedding_dim=2)
    docs = [
        Document("same", {"content_hash": "h1"}),
        Document("same", {"content_hash": "h1"}),
    ]
    added = store.add_documents(docs, np.array([[1, 0], [1, 0]], dtype=np.float32))
    assert added == 1


def test_vector_store_dimension_mismatch_rejected():
    store = VectorStore("embed", embedding_dim=2)
    with pytest.raises(ValueError):
        store.add_documents(
            [Document("x", {"content_hash": "h2"})],
            np.array([[1, 2, 3]], dtype=np.float32),
        )
