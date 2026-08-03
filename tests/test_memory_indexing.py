from llm_studio.memory import MemoryService
from llm_studio.novels import NovelService


def test_memory_indexing_is_idempotent_and_marks_stale(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    memory = MemoryService(db_path, novel_service=novels)
    project = novels.create_project({"title": "长夜"})
    character = novels.create_character(
        project["id"],
        {"name": "林烬", "background": "来自旧城，追查灵骨交易。"},
    )

    first = memory.build_from_novel(project["id"], {"include": {"characters": True}, "rebuild_index": True})
    second = memory.build_from_novel(project["id"], {"include": {"characters": True}, "rebuild_index": True})

    assert first["documents_created"] == 1
    assert second["documents_created"] == 0
    assert second["documents_unchanged"] >= 1
    status = memory.get_project_index_status(project["id"])
    assert status["documents"]["active"] == 1
    assert status["chunks"] == 1

    memory.index_service.mark_stale_for_source("character", character["id"])
    assert memory.list_documents(project_id=project["id"], status="stale")[0]["source_id"] == character["id"]

