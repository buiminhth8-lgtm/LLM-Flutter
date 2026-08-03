from llm_studio.memory import MemoryService
from llm_studio.novels import NovelService


def test_memory_keyword_retrieval_saves_record_and_honors_budget(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    memory = MemoryService(db_path, novel_service=novels)
    project = novels.create_project({"title": "长夜"})
    novels.create_world_entry(
        project["id"],
        {
            "category": "location",
            "title": "黑市",
            "content": "黑市位于旧城地下，灵骨交易由三方势力控制。",
            "priority": 10,
        },
    )
    memory.build_from_novel(project["id"], {"include": {"world_entries": True}, "rebuild_index": True})

    result = memory.retrieve(
        {
            "project_id": project["id"],
            "query_text": "主角进入黑市发现灵骨交易",
            "top_k": 5,
            "budget": {"max_memory_tokens": 100, "max_chunks": 1},
            "filters": {"source_types": ["world_entry"], "status": "active"},
        }
    )

    assert result["retrieval_id"]
    assert len(result["chunks"]) == 1
    assert result["chunks"][0]["source_type"] == "world_entry"
    assert "黑市" in result["chunks"][0]["text"]
    record = memory.get_retrieval_record(result["retrieval_id"])
    assert record["selected_chunks"] == [result["chunks"][0]["chunk_id"]]


def test_memory_retrieval_fallback_warning_when_fts_unavailable(tmp_path, monkeypatch):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    memory = MemoryService(db_path, novel_service=novels)
    project = novels.create_project({"title": "长夜"})
    document = memory.create_document(
        {
            "project_id": project["id"],
            "title": "手记",
            "content": "父亲死因与黑市有关。",
            "source_type": "manual_note",
        }
    )
    assert document["document_id"]
    monkeypatch.setattr(memory.records.__class__, "fts_available", property(lambda self: False))

    result = memory.retrieve({"project_id": project["id"], "query_text": "黑市", "top_k": 1})

    assert any(warning["code"] == "MEMORY_FTS_NOT_AVAILABLE" for warning in result["warnings"])

