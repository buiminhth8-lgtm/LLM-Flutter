import asyncio

from llm_studio.context import ContextService
from llm_studio.novels import NovelService
from llm_studio.prompts import PromptService
from llm_studio.writing import WritingRuntimeBridge, WritingService


class _NoopAsyncContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeRunner:
    def __init__(self, text: str = "夜色落在旧城。", stream_chunks=("夜色", "落在", "旧城。")):
        self.text = text
        self.stream_chunks = stream_chunks

    def generate(self, prompt, **kwargs):
        return self.text

    def generate_stream(self, prompt, cancellation_token=None, **kwargs):
        yield from self.stream_chunks

    def list_loaded_adapters(self):
        return ()

    def deactivate_adapter(self):
        pass

    def load_adapter(self, adapter, adapter_name=None):
        return adapter_name or adapter.name

    def activate_adapter(self, adapter_name):
        pass


class _FakeAdapter:
    def __init__(self, adapter_id: str):
        self.name = adapter_id


class _FakeAdapterRepository:
    def __init__(self):
        self.adapters = {}

    def register(self, adapter_id: str):
        self.adapters[adapter_id] = _FakeAdapter(adapter_id)

    def get(self, adapter_id: str):
        return self.adapters[adapter_id]


def _bridge(
    text: str = "夜色落在旧城。",
    stream_chunks=("夜色", "落在", "旧城。"),
    adapter_repository=None,
):
    async def _resolve(model_id, owner):
        return model_id, _FakeRunner(text, stream_chunks)

    def _scope(owner):
        return _NoopAsyncContext()

    return WritingRuntimeBridge(
        resolve_runner=_resolve,
        inference_scope=_scope,
        adapter_repository=adapter_repository,
    )


def _seed(tmp_path, text: str = "夜色落在旧城。"):
    db_path = tmp_path / "novels.sqlite"
    novels = NovelService(db_path)
    prompts = PromptService(db_path, novel_service=novels)
    context = ContextService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
    )
    adapters = _FakeAdapterRepository()
    adapters.register("adapter-1")
    bridge = _bridge(text, adapter_repository=adapters)
    writing = WritingService(
        db_path,
        novel_service=novels,
        prompt_service=prompts,
        context_service=context,
        runtime_bridge=bridge,
    )
    project = novels.create_project({"title": "长夜"})
    chapter = novels.create_chapter(
        project["id"],
        {"title": "黑市", "outline": "主角进入黑市。"},
    )
    template = prompts.create_template(
        {
            "name": "章节生成",
            "type": "chapter_generate",
            "scope": "global",
            "instruction_template": "{{project_title}}\n{{chapter_outline}}",
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
        "adapter_id": "adapter-1",
        "mode": "chapter_generate",
        "target_length": {
            "unit": "chars",
            "min": 1,
            "max": 100,
            "strategy": "soft",
        },
        "generation_params": {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 128,
            "repetition_penalty": 1.1,
        },
    }
    return writing, project, chapter, request


def test_writing_service_generates_through_model_gateway(tmp_path):
    writing, project, _, request = _seed(tmp_path)

    result = asyncio.run(writing.generate(request))

    assert result["text"] == "夜色落在旧城。"
    assert result["finish_reason"] == "stop"
    record = writing.get_generation(result["generation_id"])
    assert record["status"] == "succeeded"
    assert record["model_id"] == "model-1"
    assert record["adapter_id"] == "adapter-1"
    assert record["generation_params"]["max_tokens"] == 128
    assert record["latency_ms"] is not None


def test_writing_service_keeps_below_target_warning(tmp_path):
    writing, _, _, request = _seed(tmp_path, text="短")
    request["target_length"] = {
        "unit": "chars",
        "min": 5,
        "max": 100,
        "strategy": "soft",
    }

    result = asyncio.run(writing.generate(request))

    codes = [warning["code"] for warning in result["warnings"]]
    assert "WRITING_OUTPUT_BELOW_TARGET" in codes
    assert result["text"] == "短"


def test_writing_service_streams_through_model_gateway(tmp_path):
    writing, project, _, request = _seed(tmp_path)

    async def _collect():
        return [event async for event in writing.stream_generate(request)]

    events = asyncio.run(_collect())
    deltas = [event["text"] for event in events if event["type"] == "delta"]
    done = next(event for event in events if event["type"] == "done")

    assert "".join(deltas) == "夜色落在旧城。"
    assert done["finish_reason"] == "stop"
    records = writing.list_generations(project_id=project["id"])
    assert records[0]["status"] == "succeeded"
    assert records[0]["model_output"] == "夜色落在旧城。"


def test_writing_service_empty_output_keeps_existing_warning_behavior(tmp_path):
    writing, _, _, request = _seed(tmp_path, text="")

    result = asyncio.run(writing.generate(request))

    codes = [warning["code"] for warning in result["warnings"]]
    assert "WRITING_OUTPUT_BELOW_TARGET" in codes
    record = writing.get_generation(result["generation_id"])
    assert record["status"] == "succeeded"
    assert record["model_output"] == ""
