"""Stage 9 Adapter Evaluation smoke validation.

This smoke test uses an in-process FastAPI app and explicit fake model,
adapter, fine-tune, and runtime bridges. It does not load a real model, does
not start training, and does not create dataset samples.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from llm_studio.api.deps import get_api_state
from llm_studio.api_server import get_app
from llm_studio.config import Config
from llm_studio.finetune.errors import FineTuneRunNotFoundError
from llm_studio.models.entities import LocalModel, ModelFormat, ModelStatus
from llm_studio.models.exceptions import InvalidModelPathError
from llm_studio.writing.entities import RuntimeTextResult

PROJECT_NAME = "__stage9_adapter_eval_smoke__"


class FakeRuntimeBridge:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def generate_text(self, **kwargs: Any) -> RuntimeTextResult:
        self.calls.append(kwargs)
        variant = "adapter" if kwargs.get("adapter_id") else "base"
        return RuntimeTextResult(
            text=f"{variant} output for {kwargs['prompt'][:24]}",
            finish_reason="stop",
            latency_ms=7,
        )


class FakeModelRepository:
    def __init__(self, root: Path) -> None:
        self.path = root / "data" / "models" / "qwen-local"
        self.path.mkdir(parents=True, exist_ok=True)

    def get(self, model_id: str) -> LocalModel:
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
    def get(self, adapter_id: str) -> SimpleNamespace:
        if adapter_id != "adapter-1":
            from llm_studio.adapters.exceptions import AdapterNotFoundError

            raise AdapterNotFoundError(adapter_id)
        return SimpleNamespace(
            id="adapter-1",
            name="adapter-1",
            compatible=True,
            compatibility_errors=(),
        )


class FakeFineTuneRecords:
    def get_run(self, run_id: str) -> dict[str, Any]:
        if run_id != "run-1":
            raise FineTuneRunNotFoundError(run_id)
        return {
            "run_id": "run-1",
            "status": "completed",
            "dataset_version_id": "version-1",
            "base_model_id": "qwen-local",
            "adapter_id": "adapter-1",
        }


class FakeFineTuneService:
    def __init__(self) -> None:
        self.records = FakeFineTuneRecords()


def _write_config(root: Path) -> Path:
    cfg_path = root / "config.yaml"
    cfg_path.write_text(
        """
auth:
  enabled: false
api:
  allowed_origins: []
features:
  novel_studio:
    enabled: true
  prompt_studio:
    enabled: true
  context_assembler:
    enabled: true
  writing_workspace:
    enabled: true
  revision_system:
    enabled: true
  dataset_builder:
    enabled: true
  finetune_center:
    enabled: true
  adapter_evaluation:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
  adapters_dir: ./data/adapters
novels:
  db_path: ./data/novels/novels.sqlite
prompts:
  db_path: ./data/novels/novels.sqlite
context:
  db_path: ./data/novels/novels.sqlite
writing:
  db_path: ./data/novels/novels.sqlite
revisions:
  db_path: ./data/novels/novels.sqlite
datasets:
  db_path: ./data/novels/novels.sqlite
  export_root: ./data/datasets
finetune:
  db_path: ./data/novels/novels.sqlite
  output_dir: ./data/finetune
adapter_evaluation:
  db_path: ./data/novels/novels.sqlite
""",
        encoding="utf-8",
    )
    return cfg_path


def _ok(response, label: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise RuntimeError(f"{label} failed: {response.status_code} {response.text}")
    return response.json()


def run_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix="stage9_adapter_eval_",
        ignore_cleanup_errors=True,
    ) as tmp:
        root = Path(tmp)
        client = TestClient(get_app(Config(_write_config(root))))
        state = get_api_state()
        runtime = FakeRuntimeBridge()
        service = state.adapter_evaluation_service
        service.model_repository = FakeModelRepository(root)
        service.adapter_repository = FakeAdapterRepository()
        service.finetune_service = FakeFineTuneService()
        service.runner.runtime_bridge = runtime

        caps = _ok(client.get("/v1/capabilities"), "capabilities")["capabilities"]
        cap_map = {item["name"]: item["status"] for item in caps}
        if cap_map.get("adapter_evaluation") != "available":
            raise RuntimeError("adapter_evaluation capability is not available.")

        project = _ok(
            client.post(
                "/v1/novels/projects",
                json={"title": PROJECT_NAME, "description": "Stage 9 smoke"},
            ),
            "create project",
        )
        chapter = _ok(
            client.post(
                f"/v1/novels/projects/{project['id']}/chapters",
                json={
                    "title": "Smoke Chapter",
                    "outline": "主角进入黑市。",
                    "draft_content": "夜雨停在屋檐下。",
                },
            ),
            "create chapter",
        )
        template = _ok(
            client.post(
                "/v1/prompts/templates",
                json={
                    "name": "Stage 9 Smoke Template",
                    "type": "chapter_continue",
                    "scope": "global",
                    "instruction_template": (
                        "{{project_title}}\n{{chapter_outline}}\n"
                        "{{chapter_draft}}\n{{current_chapter_goal}}\n{{style}}"
                    ),
                    "variables_schema": {},
                    "default_values": {},
                },
            ),
            "create template",
        )
        session = _ok(
            client.post(
                "/v1/adapter-evaluations/sessions",
                json={
                    "name": "Stage 9 smoke evaluation",
                    "project_id": project["id"],
                    "finetune_run_id": "run-1",
                    "base_model_id": "qwen-local",
                    "adapter_id": "adapter-1",
                },
            ),
            "create evaluation session",
        )
        case = _ok(
            client.post(
                f"/v1/adapter-evaluations/sessions/{session['session_id']}/cases",
                json={
                    "title": "Smoke comparison case",
                    "project_id": project["id"],
                    "chapter_id": chapter["id"],
                    "template_id": template["id"],
                    "mode": "chapter_continue",
                    "user_variables": {
                        "current_chapter_goal": "继续写主角进入黑市。",
                        "style": "紧张、细节丰富",
                    },
                    "generation_params": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "max_tokens": 128,
                    },
                    "target_length": {
                        "unit": "chars",
                        "min": 1,
                        "max": 300,
                        "strategy": "soft",
                    },
                },
            ),
            "create evaluation case",
        )
        case = _ok(
            client.post(f"/v1/adapter-evaluations/cases/{case['case_id']}/run"),
            "run evaluation case",
        )
        if len(case["results"]) != 2:
            raise RuntimeError("comparison did not persist base and adapter results.")
        base_result = next(item for item in case["results"] if item["variant"] == "base")
        adapter_result = next(
            item for item in case["results"] if item["variant"] == "adapter"
        )
        _ok(
            client.post(
                f"/v1/adapter-evaluations/cases/{case['case_id']}/score",
                json={
                    "winner": "adapter",
                    "base_score": 3,
                    "adapter_score": 5,
                    "dimensions": {"overall": {"base": 3, "adapter": 5}},
                    "notes": "Adapter output is preferred.",
                },
            ),
            "score evaluation case",
        )
        report = _ok(
            client.post(
                f"/v1/adapter-evaluations/sessions/{session['session_id']}/report"
            ),
            "generate report",
        )
        revision = _ok(
            client.post(
                f"/v1/adapter-evaluations/results/{adapter_result['result_id']}/create-revision",
                json={
                    "project_id": project["id"],
                    "chapter_id": chapter["id"],
                    "edit_tags": ["style_unify"],
                    "user_score": 4,
                    "quality_notes": "Stage 9 smoke revision handoff.",
                },
            ),
            "create revision from result",
        )
        return {
            "session_id": session["session_id"],
            "case_id": case["case_id"],
            "base_result_id": base_result["result_id"],
            "adapter_result_id": adapter_result["result_id"],
            "report_id": report["report_id"],
            "recommendation": report["report"]["recommendation"],
            "revision_id": revision["revision_id"],
            "revision_source": revision["source"],
            "runtime_calls": len(runtime.calls),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run_smoke(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
