from __future__ import annotations

from types import SimpleNamespace

from llm_studio.adapter_evaluation import AdapterEvaluationService
from llm_studio.datasets import DatasetService
from llm_studio.finetune.errors import FineTuneRunNotFoundError
from llm_studio.models.entities import LocalModel, ModelFormat, ModelStatus
from llm_studio.models.exceptions import InvalidModelPathError
from llm_studio.revisions import RevisionService
from llm_studio.writing.entities import RuntimeTextResult
from llm_studio.writing.errors import WritingRuntimeError
from tests.test_writing_service import _seed


class FakeAdapterEvalRuntimeBridge:
    def __init__(self):
        self.calls: list[dict] = []
        self.fail_adapter = False
        self.fail_base = False

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        adapter_id = kwargs.get("adapter_id")
        if adapter_id and self.fail_adapter:
            raise WritingRuntimeError("WRITING_GENERATION_FAILED", "adapter failed")
        if adapter_id is None and self.fail_base:
            raise WritingRuntimeError("WRITING_GENERATION_FAILED", "base failed")
        prefix = "adapter" if adapter_id else "base"
        return RuntimeTextResult(
            f"{prefix} output for {kwargs['prompt'][:20]}",
            finish_reason="stop",
            latency_ms=9,
        )


class FakeModelRepository:
    def __init__(self, tmp_path):
        self.path = tmp_path / "models" / "qwen-local"
        self.path.mkdir(parents=True, exist_ok=True)

    def get(self, model_id: str):
        if model_id != "qwen-local":
            raise InvalidModelPathError(model_id)
        return LocalModel(
            id="qwen-local",
            display_name="qwen-local",
            path=self.path,
            format=ModelFormat.TRANSFORMERS,
            status=ModelStatus.READY,
            architecture="qwen2",
            parameter_count=1_500_000_000,
            quantization=None,
            context_length=4096,
            size_bytes=1,
            files=("config.json",),
        )


class FakeAdapterRepository:
    def __init__(self, *, compatible: bool = True):
        self.compatible = compatible

    def get(self, adapter_id: str):
        if adapter_id != "adapter-1":
            from llm_studio.adapters.exceptions import AdapterNotFoundError

            raise AdapterNotFoundError(adapter_id)
        return SimpleNamespace(
            id="adapter-1",
            name="adapter-1",
            compatible=self.compatible,
            compatibility_errors=("bad",) if not self.compatible else (),
        )


class FakeFineTuneRecords:
    def __init__(self, status: str = "completed"):
        self.status = status

    def get_run(self, run_id: str):
        if run_id != "run-1":
            raise FineTuneRunNotFoundError(run_id)
        return {
            "run_id": "run-1",
            "status": self.status,
            "dataset_version_id": "version-1",
            "base_model_id": "qwen-local",
            "adapter_id": "adapter-1",
        }


class FakeFineTuneService:
    def __init__(self, status: str = "completed"):
        self.records = FakeFineTuneRecords(status)


def adapter_eval_seed(tmp_path, *, finetune_status: str = "completed"):
    novels, prompts, context, writing, _, project, chapter, template, _ = _seed(tmp_path)
    revisions = RevisionService(
        writing.db_path,
        novel_service=novels,
        writing_service=writing,
    )
    datasets = DatasetService(
        writing.db_path,
        export_root=tmp_path / "datasets",
        novel_service=novels,
        revision_service=revisions,
        writing_service=writing,
        prompt_service=prompts,
    )
    runtime = FakeAdapterEvalRuntimeBridge()
    service = AdapterEvaluationService(
        writing.db_path,
        novel_service=novels,
        prompt_service=prompts,
        context_service=context,
        writing_service=writing,
        revision_service=revisions,
        dataset_service=datasets,
        finetune_service=FakeFineTuneService(finetune_status),
        model_repository=FakeModelRepository(tmp_path),
        adapter_repository=FakeAdapterRepository(),
        runtime_bridge=runtime,
    )
    session = service.create_session(
        {
            "name": "Stage 9",
            "project_id": project["id"],
            "finetune_run_id": "run-1",
            "base_model_id": "qwen-local",
            "adapter_id": "adapter-1",
        }
    )
    case_request = {
        "title": "compare market",
        "project_id": project["id"],
        "chapter_id": chapter["id"],
        "template_id": template["id"],
        "mode": "chapter_generate",
        "user_variables": {"current_chapter_goal": "compare"},
        "target_length": {"unit": "chars", "min": 1, "max": 100, "strategy": "soft"},
        "generation_params": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 128},
    }
    case = service.create_case(session["session_id"], case_request)
    return SimpleNamespace(
        service=service,
        runtime=runtime,
        project=project,
        chapter=chapter,
        template=template,
        session=session,
        case=case,
        revisions=revisions,
        datasets=datasets,
    )
