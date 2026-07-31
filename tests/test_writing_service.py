from __future__ import annotations

import asyncio

import pytest

from llm_studio.context import ContextService
from llm_studio.novels import NovelService
from llm_studio.prompts import PromptService
from llm_studio.writing import WritingService
from llm_studio.writing.entities import RuntimeTextResult
from llm_studio.writing.errors import WritingRuntimeError


class FakeRuntimeBridge:
    def __init__(self, text: str = "夜色落在旧城。"):
        self.text = text
        self.generate_calls = []
        self.stream_calls = []
        self.cancelled = set()
        self.error: WritingRuntimeError | None = None

    async def generate_text(self, **kwargs):
        self.generate_calls.append(kwargs)
        if self.error:
            raise self.error
        return RuntimeTextResult(self.text, latency_ms=12)

    async def stream_text(self, **kwargs):
        self.stream_calls.append(kwargs)
        if self.error:
            raise self.error
        for chunk in ("夜色", "落在", "旧城。"):
            yield chunk

    def cancel_generation(self, generation_id):
        self.cancelled.add(generation_id)
        return True


def _services(tmp_path, runtime=None):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    prompts = PromptService(db_path, novel_service=novels)
    context = ContextService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
    )
    runtime = runtime or FakeRuntimeBridge()
    writing = WritingService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
        context_service=context,
        runtime_bridge=runtime,
    )
    return novels, prompts, context, writing, runtime


def _seed(tmp_path, runtime=None):
    novels, prompts, context, writing, runtime = _services(tmp_path, runtime)
    project = novels.create_project({"title": "长夜"})
    chapter = novels.create_chapter(
        project["id"],
        {"title": "黑市", "outline": "主角进入黑市。", "draft_content": "旧稿"},
    )
    template = prompts.create_template(
        {
            "name": "章节生成",
            "type": "chapter_generate",
            "scope": "global",
            "instruction_template": (
                "{{project_title}}\n{{chapter_outline}}\n"
                "{{current_chapter_goal}}\n{{target_length}}"
            ),
            "variables_schema": {
                "project_title": {"type": "string", "required": True},
                "chapter_outline": {"type": "string", "required": True},
            },
            "default_values": {},
        }
    )
    request = {
        "project_id": project["id"],
        "chapter_id": chapter["id"],
        "template_id": template["id"],
        "model_id": "model-1",
        "mode": "chapter_generate",
        "target_length": {
            "unit": "chars",
            "min": 1,
            "max": 100,
            "strategy": "soft",
        },
        "user_variables": {"current_chapter_goal": "发现交易"},
        "generation_params": {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 128,
            "repetition_penalty": 1.1,
        },
    }
    return novels, prompts, context, writing, runtime, project, chapter, template, request


def test_writing_service_calls_context_prompt_and_runtime(tmp_path, monkeypatch):
    (
        _,
        prompts,
        context,
        writing,
        runtime,
        _,
        _,
        _,
        request,
    ) = _seed(tmp_path)
    calls = {"context": 0, "render": 0}
    original_context = context.assemble_and_render
    original_render = prompts.renderer.render

    def tracked_context(value):
        calls["context"] += 1
        return original_context(value)

    def tracked_render(*args, **kwargs):
        calls["render"] += 1
        return original_render(*args, **kwargs)

    monkeypatch.setattr(context, "assemble_and_render", tracked_context)
    monkeypatch.setattr(prompts.renderer, "render", tracked_render)
    result = asyncio.run(writing.generate(request))

    assert calls == {"context": 1, "render": 1}
    assert len(runtime.generate_calls) == 1
    assert result["text"] == "夜色落在旧城。"
    record = writing.get_generation(result["generation_id"])
    assert record["status"] == "succeeded"
    assert record["output_hash"]
    assert "api_key" not in record["input_context"]


def test_runtime_failure_marks_generation_failed(tmp_path):
    runtime = FakeRuntimeBridge()
    runtime.error = WritingRuntimeError(
        "WRITING_GENERATION_FAILED",
        "token=secret-value failed",
    )
    *_, writing, runtime, project, chapter, template, request = _seed(
        tmp_path, runtime
    )
    with pytest.raises(WritingRuntimeError):
        asyncio.run(writing.generate(request))

    records = writing.list_generations(project_id=project["id"])
    assert records[0]["status"] == "failed"
    assert "secret-value" not in records[0]["error_message"]


def test_default_max_tokens_is_suggested_from_target_length(tmp_path):
    *_, writing, runtime, _, _, _, request = _seed(tmp_path)
    request["generation_params"].pop("max_tokens")
    request["target_length"]["max"] = 100

    asyncio.run(writing.generate(request))

    assert runtime.generate_calls[0]["generation_params"]["max_tokens"] == 120


def test_non_stream_generation_applies_stop_sequences(tmp_path):
    runtime = FakeRuntimeBridge("夜色沉入旧城。<END>不应保存")
    *_, writing, _, _, _, _, request = _seed(tmp_path, runtime)
    request["generation_params"]["stop"] = ["<END>"]

    result = asyncio.run(writing.generate(request))

    assert result["text"] == "夜色沉入旧城。"
    assert "<END>" not in writing.get_generation(result["generation_id"])["model_output"]
