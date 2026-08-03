import asyncio

from llm_studio.context import ContextService
from llm_studio.memory import MemoryService
from llm_studio.novels import NovelService
from llm_studio.prompts import PromptService
from llm_studio.writing import WritingService
from tests.test_writing_service import FakeRuntimeBridge


def _services(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    prompts = PromptService(db_path, novel_service=novels)
    context = ContextService(db_path, novel_service=novels, prompt_service=prompts)
    runtime = FakeRuntimeBridge("主角发现黑市与父亲死因有关。")
    writing = WritingService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
        context_service=context,
        runtime_bridge=runtime,
    )
    memory = MemoryService(db_path, novel_service=novels, writing_service=writing)
    return novels, memory


def test_manual_summary_can_activate_and_sync_to_chapter(tmp_path):
    novels, memory = _services(tmp_path)
    project = novels.create_project({"title": "长夜"})
    chapter = novels.create_chapter(
        project["id"],
        {"title": "黑市", "draft_content": "主角进入旧城。"},
    )

    summary = memory.create_chapter_summary(
        chapter["id"],
        {"summary_type": "short", "summary_text": "主角进入旧城。", "set_active": True},
    )

    assert summary["status"] == "active"
    assert novels.get_chapter(chapter["id"])["summary"] == "主角进入旧城。"
    assert memory.list_chapter_summaries(chapter["id"])[0]["summary_id"] == summary["summary_id"]


def test_model_summary_uses_fake_writing_runtime_bridge(tmp_path):
    novels, memory = _services(tmp_path)
    project = novels.create_project({"title": "长夜"})
    chapter = novels.create_chapter(
        project["id"],
        {"title": "黑市", "draft_content": "主角进入旧城并发现黑市。"},
    )

    summary = asyncio.run(
        memory.generate_chapter_summary(
            chapter["id"],
            {"summary_type": "short", "model_id": "fake-model", "source": "draft_content"},
        )
    )

    assert summary["generated_by"] == "model"
    assert "黑市" in summary["summary_text"]

