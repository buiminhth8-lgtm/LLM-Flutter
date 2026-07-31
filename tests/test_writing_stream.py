import asyncio

from llm_studio.writing.errors import WritingRuntimeError
from tests.test_writing_service import _seed


async def _collect(service, request):
    return [event async for event in service.stream_generate(request)]


def test_stream_generation_emits_and_persists_deltas(tmp_path):
    _, _, _, writing, runtime, project, _, _, request = _seed(tmp_path)
    events = asyncio.run(_collect(writing, request))

    assert events[0]["type"] == "start"
    assert [item["text"] for item in events if item["type"] == "delta"] == [
        "夜色",
        "落在",
        "旧城。",
    ]
    assert events[-1]["type"] == "done"
    records = writing.list_generations(project_id=project["id"])
    assert records[0]["status"] == "succeeded"
    assert records[0]["model_output"] == "夜色落在旧城。"
    assert len(runtime.stream_calls) == 1


class StopRuntime:
    async def generate_text(self, **kwargs):
        raise AssertionError("not used")

    async def stream_text(self, **kwargs):
        for chunk in ("夜色<EN", "D>不应出现"):
            yield chunk

    def cancel_generation(self, generation_id):
        return True


class PartialFailureRuntime:
    async def generate_text(self, **kwargs):
        raise AssertionError("not used")

    async def stream_text(self, **kwargs):
        yield "已经生成"
        raise WritingRuntimeError("WRITING_STREAM_FAILED", "stream failed")

    def cancel_generation(self, generation_id):
        return True


def test_stream_stop_sequence_can_span_chunks(tmp_path):
    *_, writing, _, project, _, _, request = _seed(tmp_path, StopRuntime())
    request["generation_params"]["stop"] = ["<END>"]

    events = asyncio.run(_collect(writing, request))

    assert "".join(item.get("text", "") for item in events) == "夜色"
    record = writing.list_generations(project_id=project["id"])[0]
    assert record["model_output"] == "夜色"
    assert record["finish_reason"] == "stop"


def test_stream_failure_persists_partial_output(tmp_path):
    *_, writing, _, project, _, _, request = _seed(
        tmp_path,
        PartialFailureRuntime(),
    )

    events = asyncio.run(_collect(writing, request))

    assert events[-1]["type"] == "error"
    record = writing.list_generations(project_id=project["id"])[0]
    assert record["status"] == "failed"
    assert record["model_output"] == "已经生成"
    assert record["output_hash"]
