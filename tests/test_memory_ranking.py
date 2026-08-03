from llm_studio.memory.ranking import MemoryRanker


def test_memory_ranking_uses_keywords_priority_and_source_type():
    chunks = [
        {
            "chunk_id": "low",
            "chunk_index": 0,
            "chunk_text": "普通街道",
            "token_estimate": 10,
            "metadata": {},
            "document": {
                "source_type": "generation",
                "title": "生成",
                "priority": 0,
                "updated_at": "2026-01-01",
            },
        },
        {
            "chunk_id": "high",
            "chunk_index": 0,
            "chunk_text": "黑市里存在灵骨交易",
            "token_estimate": 10,
            "metadata": {},
            "document": {
                "source_type": "world_entry",
                "title": "黑市",
                "priority": 10,
                "updated_at": "2026-01-02",
            },
        },
    ]

    ranked = MemoryRanker().rank(chunks, query_text="黑市 灵骨", chapter_id=None, scene_id=None)

    assert ranked[0].chunk["chunk_id"] == "high"
    assert ranked[0].explain["keyword_hits"] > 0

