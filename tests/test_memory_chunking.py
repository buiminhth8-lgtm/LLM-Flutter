from llm_studio.memory.chunking import MemoryChunker
from llm_studio.memory.entities import ChunkOptions, MemoryDocument


def _doc(content):
    return MemoryDocument(
        id="doc-1",
        project_id="p1",
        source_type="chapter",
        source_id="c1",
        title="黑市",
        content=content,
    )


def test_memory_chunking_supports_long_chinese_text():
    text = "第一段黑市。\n\n" + "灵骨交易" * 300
    chunks = MemoryChunker().chunk_document(
        _doc(text),
        ChunkOptions(chunk_chars=120, chunk_overlap_chars=12),
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert all(chunk.chunk_text for chunk in chunks)
    assert all(chunk.content_hash for chunk in chunks)


def test_memory_chunking_skips_empty_text():
    assert MemoryChunker().chunk_document(_doc("  \n ")) == []

