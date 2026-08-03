import asyncio

from llm_studio.context import ContextService
from llm_studio.memory import MemoryService
from llm_studio.novels import NovelService
from llm_studio.prompts import PromptService
from llm_studio.writing import WritingService
from tests.test_writing_service import FakeRuntimeBridge


def _seed(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    prompts = PromptService(db_path, novel_service=novels)
    context = ContextService(db_path, novel_service=novels, prompt_service=prompts)
    memory = MemoryService(db_path, novel_service=novels)
    context.memory_service = memory
    writing = WritingService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
        context_service=context,
        runtime_bridge=FakeRuntimeBridge("正文"),
    )
    project = novels.create_project({"title": "长夜"})
    chapter = novels.create_chapter(project["id"], {"title": "黑市", "outline": "进入黑市"})
    template = prompts.create_template(
        {
            "name": "With Memory",
            "type": "chapter_generate",
            "scope": "global",
            "instruction_template": "{{project_title}}\n{{chapter_outline}}\n{{retrieved_memory}}",
            "variables_schema": {},
            "default_values": {},
        }
    )
    novels.create_world_entry(
        project["id"],
        {"category": "地点", "title": "黑市", "content": "黑市受三方势力控制。", "priority": 10},
    )
    memory.build_from_novel(project["id"], {"include": {"world_entries": True}, "rebuild_index": True})
    return novels, prompts, context, writing, memory, project, chapter, template


def test_context_memory_disabled_keeps_stage3_shape(tmp_path):
    *_, context, _writing, _memory, project, chapter, template = _seed(tmp_path)
    result = context.assemble_context(
        {
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "memory": {"enabled": False},
        }
    )

    assert result["variables"].get("retrieved_memory") is None
    assert result["retrieval_id"] is None


def test_context_memory_enabled_injects_retrieved_memory_and_records_id(tmp_path):
    *_, context, _writing, _memory, project, chapter, template = _seed(tmp_path)
    result = context.assemble_and_render(
        {
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "user_variables": {"current_chapter_goal": "进入黑市"},
            "memory": {
                "enabled": True,
                "query_text": "黑市",
                "top_k": 3,
                "max_memory_tokens": 200,
                "source_types": ["world_entry"],
                "save_retrieval_record": True,
            },
        }
    )

    assert result["retrieval_id"]
    assert "黑市受三方势力控制" in result["variables"]["retrieved_memory"]
    assert "黑市受三方势力控制" in result["rendered_prompt"]
    record = context.get_context_record(result["context_id"])
    assert record["retrieval_id"] == result["retrieval_id"]


def test_writing_service_passes_memory_config_to_context(tmp_path):
    *_, context, writing, _memory, project, chapter, template = _seed(tmp_path)
    result = asyncio.run(
        writing.generate(
            {
                "project_id": project["id"],
                "chapter_id": chapter["id"],
                "template_id": template["id"],
                "model_id": "fake-model",
                "mode": "chapter_generate",
                "target_length": {"unit": "chars", "min": 1, "max": 100, "strategy": "soft"},
                "generation_params": {"max_tokens": 64},
                "memory": {"enabled": True, "query_text": "黑市", "source_types": ["world_entry"]},
            }
        )
    )
    generation = writing.get_generation(result["generation_id"])
    assert generation["input_context"]["retrieval_id"]

