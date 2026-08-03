"""AdapterEvaluationService orchestration for Novel Studio Stage 9."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_studio.adapters.exceptions import AdapterNotFoundError
from llm_studio.api import errors as api_errors
from llm_studio.context.errors import ContextError
from llm_studio.models.exceptions import InvalidModelPathError
from llm_studio.novels.errors import NovelError
from llm_studio.prompts.errors import PromptError
from llm_studio.writing.generation_modes import GENERATION_MODES
from llm_studio.writing.length_control import normalize_target_length
from llm_studio.writing.service import WritingService

from .comparison_runner import AdapterComparisonRunner
from .errors import (
    AdapterEvalAdapterIncompatibleError,
    AdapterEvalAdapterNotFoundError,
    AdapterEvalBaseModelNotFoundError,
    AdapterEvalCaseNotReadyError,
    AdapterEvalChapterNotFoundError,
    AdapterEvalContextFailedError,
    AdapterEvalFineTuneRunNotCompletedError,
    AdapterEvalFineTuneRunNotFoundError,
    AdapterEvalGenerationFailedError,
    AdapterEvalProjectNotFoundError,
    AdapterEvalPromptRenderFailedError,
    AdapterEvalReportFailedError,
    AdapterEvalResultPairIncompleteError,
    AdapterEvalTemplateNotFoundError,
)
from .reports import AdapterEvaluationReportBuilder
from .repository import AdapterEvaluationRepository
from .revision_bridge import AdapterEvaluationRevisionBridge
from .schemas import model_dump_compat
from .scoring import (
    validate_dimensions,
    validate_score,
    validate_winner,
)

SESSION_STATUSES = frozenset(
    {"draft", "ready", "running", "reviewing", "completed", "failed", "archived"}
)
CASE_STATUSES = frozenset({"pending", "ready", "running", "completed", "failed", "archived"})
MAX_SYNC_SESSION_CASES = 20


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise AdapterEvalContextFailedError(f"{field} is required.")
    return text


class AdapterEvaluationService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        prompt_service: Any,
        context_service: Any,
        writing_service: Any,
        revision_service: Any,
        dataset_service: Any,
        finetune_service: Any,
        model_repository: Any,
        adapter_repository: Any,
        runtime_bridge: Any,
        comparison_runner: AdapterComparisonRunner | None = None,
        report_builder: AdapterEvaluationReportBuilder | None = None,
    ):
        self.db_path = Path(db_path)
        self.records = AdapterEvaluationRepository(self.db_path)
        self.novel_service = novel_service
        self.prompt_service = prompt_service
        self.context_service = context_service
        self.writing_service = writing_service
        self.revision_service = revision_service
        self.dataset_service = dataset_service
        self.finetune_service = finetune_service
        self.model_repository = model_repository
        self.adapter_repository = adapter_repository
        self.runner = comparison_runner or AdapterComparisonRunner(runtime_bridge)
        self.report_builder = report_builder or AdapterEvaluationReportBuilder()
        self.revision_bridge = AdapterEvaluationRevisionBridge(
            self.records,
            revision_service,
        )

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        prompt_service: Any,
        context_service: Any,
        writing_service: Any,
        revision_service: Any,
        dataset_service: Any,
        finetune_service: Any,
        model_repository: Any,
        adapter_repository: Any,
        runtime_bridge: Any,
    ) -> AdapterEvaluationService:
        cfg = config.get("adapter_evaluation", {}) if config is not None else {}
        fallback = (
            config.get("finetune", {}).get(
                "db_path",
                config.get("datasets", {}).get(
                    "db_path",
                    config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite"),
                ),
            )
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(
            Path(cfg.get("db_path", fallback)),
            novel_service=novel_service,
            prompt_service=prompt_service,
            context_service=context_service,
            writing_service=writing_service,
            revision_service=revision_service,
            dataset_service=dataset_service,
            finetune_service=finetune_service,
            model_repository=model_repository,
            adapter_repository=adapter_repository,
            runtime_bridge=runtime_bridge,
        )

    def create_session(self, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        data["name"] = _require_text(data.get("name"), "name")
        self._base_model(data["base_model_id"])
        adapter = self._adapter(data["adapter_id"])
        self._adapter_compatible(adapter)
        if data.get("project_id"):
            self._project(data["project_id"])
        if data.get("finetune_run_id"):
            run = self._finetune_run(data["finetune_run_id"])
            if run.get("status") != "completed":
                raise AdapterEvalFineTuneRunNotCompletedError(
                    "Fine-tune run must be completed before evaluation."
                )
        if data.get("dataset_version_id"):
            self._dataset_version(data["dataset_version_id"])
        return self.records.create_session(
            {
                **data,
                "status": "draft",
                "metadata": data.get("metadata") or {},
            }
        )

    def list_sessions(
        self,
        *,
        status: str | None = None,
        project_id: str | None = None,
        adapter_id: str | None = None,
        finetune_run_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if status:
            self._session_status(status)
        return self.records.list_sessions(
            status=status,
            project_id=project_id,
            adapter_id=adapter_id,
            finetune_run_id=finetune_run_id,
            limit=limit,
            offset=offset,
        )

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.records.get_session(session_id)
        cases = self.records.list_cases(session_id, limit=500)
        scores = self.records.list_scores(session_id)
        return {
            **session,
            "cases": [self._case_with_children(case) for case in cases],
            "reports": self.records.list_reports(session_id),
            "stats": self._session_stats(cases, scores),
        }

    def update_session(self, session_id: str, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        changes: dict[str, Any] = {}
        if "name" in data and data["name"] is not None:
            changes["name"] = _require_text(data["name"], "name")
        if "description" in data:
            changes["description"] = data.get("description")
        if "status" in data and data["status"] is not None:
            changes["status"] = self._session_status(data["status"])
        if "metadata" in data and data["metadata"] is not None:
            changes["metadata_json"] = json.dumps(
                data.get("metadata") or {},
                ensure_ascii=False,
                sort_keys=True,
            )
        return self.records.update_session(session_id, changes)

    def archive_session(self, session_id: str) -> dict[str, Any]:
        return self.records.update_session(session_id, {"status": "archived"})

    def create_case(self, session_id: str, request: Any) -> dict[str, Any]:
        session = self.records.get_session(session_id)
        data = model_dump_compat(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = data.get("project_id") or session.get("project_id")
        prepared = self._prepare_case_payload(session, data)
        created = self.records.create_case(
            {
                **data,
                **prepared,
                "session_id": session_id,
                "status": "ready",
            }
        )
        if session["status"] == "draft":
            self.records.update_session(session_id, {"status": "ready"})
        return created

    def prepare_case(self, case_id: str) -> dict[str, Any]:
        case = self.records.get_case(case_id)
        if case.get("prompt_rendered") and case["status"] == "ready":
            return self.get_case(case_id)
        session = self.records.get_session(case["session_id"])
        prepared = self._prepare_case_payload(session, case)
        updated = self.records.update_case(
            case_id,
            {
                **prepared,
                "context_snapshot_json": json.dumps(
                    prepared["context_snapshot"],
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "status": "ready",
            },
        )
        return self._case_with_children(updated)

    async def run_case(self, case_id: str) -> dict[str, Any]:
        case = self.records.get_case(case_id)
        if case["status"] not in {"ready", "completed"}:
            raise AdapterEvalCaseNotReadyError("Evaluation case must be ready before run.")
        session = self.records.get_session(case["session_id"])
        if session["status"] == "archived" or case["status"] == "archived":
            raise AdapterEvalCaseNotReadyError("Archived evaluation records cannot run.")
        self.records.update_case(case_id, {"status": "running"})
        pair = await self.runner.run_pair(case=case, session=session)
        base_result = self.records.upsert_result(
            {
                **pair.base.to_dict(),
                "case_id": case_id,
                "session_id": session["session_id"],
            }
        )
        adapter_result = self.records.upsert_result(
            {
                **pair.adapter.to_dict(),
                "case_id": case_id,
                "session_id": session["session_id"],
            }
        )
        if base_result["status"] == "failed" and adapter_result["status"] == "failed":
            self.records.update_case(case_id, {"status": "failed"})
            raise AdapterEvalGenerationFailedError(
                "Both base and adapter generation failed.",
                details={"base": base_result, "adapter": adapter_result},
            )
        updated = self.records.update_case(case_id, {"status": "completed"})
        if session["status"] in {"draft", "ready"}:
            self.records.update_session(session["session_id"], {"status": "reviewing"})
        return self._case_with_children(updated)

    async def run_session(
        self,
        session_id: str,
        request: Any | None = None,
    ) -> dict[str, Any]:
        data = model_dump_compat(request or {})
        selected = set(data.get("case_ids") or [])
        rerun_completed = bool(data.get("rerun_completed", False))
        session = self.records.update_session(session_id, {"status": "running"})
        cases = self.records.list_cases(session_id, limit=500)
        runnable = [
            case
            for case in cases
            if (not selected or case["case_id"] in selected)
            and (
                case["status"] in {"pending", "ready"}
                or (rerun_completed and case["status"] == "completed")
            )
        ][:MAX_SYNC_SESSION_CASES]
        errors: list[dict[str, Any]] = []
        for case in runnable:
            try:
                if case["status"] == "pending":
                    self.prepare_case(case["case_id"])
                await self.run_case(case["case_id"])
            except Exception as exc:
                errors.append(
                    {
                        "case_id": case["case_id"],
                        "error_code": getattr(exc, "code", api_errors.ADAPTER_EVAL_GENERATION_FAILED),
                        "message": getattr(exc, "message", str(exc)),
                    }
                )
        completed_cases = [
            case
            for case in self.records.list_cases(session_id, limit=500)
            if case["status"] == "completed"
        ]
        next_status = "reviewing" if completed_cases else "failed"
        self.records.update_session(session["session_id"], {"status": next_status})
        detail = self.get_session(session_id)
        detail["run_summary"] = {
            "attempted_count": len(runnable),
            "error_count": len(errors),
            "errors": errors,
            "sync_case_limit": MAX_SYNC_SESSION_CASES,
        }
        return detail

    def get_case(self, case_id: str) -> dict[str, Any]:
        return self._case_with_children(self.records.get_case(case_id))

    def list_cases(
        self,
        session_id: str,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if status:
            self._case_status(status)
        return [
            self._case_with_children(case)
            for case in self.records.list_cases(
                session_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        ]

    def score_case(self, case_id: str, request: Any) -> dict[str, Any]:
        case = self.records.get_case(case_id)
        results = {item["variant"]: item for item in self.records.list_results(case_id=case_id)}
        base = results.get("base")
        adapter = results.get("adapter")
        if not base or not adapter:
            raise AdapterEvalResultPairIncompleteError("Both base and adapter results are required.")
        data = model_dump_compat(request)
        base_score = validate_score(data.get("base_score"), "base_score")
        adapter_score = validate_score(data.get("adapter_score"), "adapter_score")
        winner = validate_winner(data.get("winner"))
        dimensions = validate_dimensions(data.get("dimensions") or {})
        return self.records.upsert_score(
            {
                "case_id": case_id,
                "session_id": case["session_id"],
                "base_result_id": base["result_id"],
                "adapter_result_id": adapter["result_id"],
                "winner": winner,
                "base_score": base_score,
                "adapter_score": adapter_score,
                "dimensions": dimensions,
                "notes": data.get("notes"),
                "reviewer_id": data.get("reviewer_id"),
            }
        )

    def get_score(self, case_id: str) -> dict[str, Any]:
        return self.records.get_score_for_case(case_id)

    def generate_report(self, session_id: str) -> dict[str, Any]:
        session = self.records.get_session(session_id)
        cases = self.records.list_cases(session_id, limit=500)
        scores = self.records.list_scores(session_id)
        try:
            report = self.report_builder.build(session=session, cases=cases, scores=scores)
            return self.records.create_report(
                {
                    "session_id": session_id,
                    "report": report,
                    "summary_text": self.report_builder.summary(report),
                }
            )
        except Exception as exc:
            raise AdapterEvalReportFailedError("Failed to generate adapter evaluation report.") from exc

    def list_reports(
        self,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_reports(session_id, limit=limit, offset=offset)

    def get_report(self, report_id: str) -> dict[str, Any]:
        return self.records.get_report(report_id)

    def create_revision_from_result(self, result_id: str, request: Any) -> dict[str, Any]:
        return self.revision_bridge.create_revision_from_result(result_id, request)

    def _prepare_case_payload(
        self,
        session: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        mode = str(data.get("mode") or "")
        if mode not in GENERATION_MODES:
            raise AdapterEvalContextFailedError(f"Unsupported writing mode: {mode}")
        target = normalize_target_length(data.get("target_length"))
        try:
            params = WritingService._generation_params(
                data.get("generation_params") or {},
                target=target,
            )
        except Exception as exc:
            raise AdapterEvalContextFailedError("Invalid generation parameters.") from exc
        project_id = data.get("project_id") or session.get("project_id")
        if not project_id:
            raise AdapterEvalProjectNotFoundError("project_id is required.")
        project = self._project(project_id)
        chapter = self._chapter(data.get("chapter_id"), project["id"])
        if data.get("scene_id"):
            self._scene(data["scene_id"], chapter)
        variables = dict(data.get("user_variables") or {})
        if chapter:
            variables.setdefault("chapter_draft", chapter.get("draft_content") or "")
            variables.setdefault("current_text", chapter.get("draft_content") or "")
        variables.setdefault(
            "target_length",
            f"{target.minimum}-{target.maximum} "
            f"{'中文字符' if target.unit == 'chars' else 'tokens'}",
        )
        context_tokens = max(512, min(32768 - params["max_tokens"], 12000))
        request = {
            "project_id": project_id,
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": data.get("template_id"),
            "template_version_id": data.get("template_version_id"),
            "mode": mode,
            "target_budget": {
                "max_tokens": min(32768, context_tokens + params["max_tokens"]),
                "reserved_output_tokens": params["max_tokens"],
                "max_context_tokens": context_tokens,
                "max_chars": max(12000, context_tokens * 3),
                "hard_limit": True,
            },
            "user_variables": variables,
            "save_record": True,
        }
        try:
            assembled = self.context_service.assemble_and_render(request)
        except ContextError as exc:
            code = getattr(exc, "code", "")
            if code in {
                api_errors.CONTEXT_PROJECT_NOT_FOUND,
                api_errors.CONTEXT_CHAPTER_NOT_FOUND,
                api_errors.CONTEXT_SCENE_NOT_FOUND,
            }:
                if code == api_errors.CONTEXT_PROJECT_NOT_FOUND:
                    raise AdapterEvalProjectNotFoundError(exc.message) from exc
                raise AdapterEvalChapterNotFoundError(exc.message) from exc
            if code in {
                api_errors.CONTEXT_TEMPLATE_NOT_FOUND,
                api_errors.CONTEXT_TEMPLATE_VERSION_NOT_FOUND,
            }:
                raise AdapterEvalTemplateNotFoundError(exc.message) from exc
            if code == api_errors.CONTEXT_RENDER_FAILED:
                raise AdapterEvalPromptRenderFailedError(exc.message) from exc
            raise AdapterEvalContextFailedError(exc.message) from exc
        except PromptError as exc:
            raise AdapterEvalPromptRenderFailedError(str(exc)) from exc
        context_snapshot = {
            "variables": assembled.get("variables") or {},
            "selected_items": assembled.get("selected_items") or {},
            "warnings": assembled.get("warnings") or [],
            "missing_variables": assembled.get("missing_variables") or [],
            "render_warnings": assembled.get("render_warnings") or [],
            "estimated_tokens": assembled.get("estimated_tokens") or 0,
        }
        return {
            "project_id": project_id,
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": assembled.get("template_id") or data.get("template_id"),
            "template_version_id": assembled.get("template_version_id")
            or data.get("template_version_id"),
            "context_id": assembled.get("context_id"),
            "mode": mode,
            "user_variables": variables,
            "generation_params": params,
            "target_length": target.to_dict(),
            "prompt_rendered": assembled["rendered_prompt"],
            "context_snapshot": context_snapshot,
            "prompt_hash": assembled.get("prompt_hash"),
            "context_hash": assembled.get("context_hash"),
        }

    def _case_with_children(self, case: dict[str, Any]) -> dict[str, Any]:
        return {
            **case,
            "results": self.records.list_results(case_id=case["case_id"]),
            "score": self.records.get_score_for_case(case["case_id"], required=False),
        }

    @staticmethod
    def _session_stats(cases: list[dict[str, Any]], scores: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "case_count": len(cases),
            "completed_case_count": sum(1 for case in cases if case["status"] == "completed"),
            "failed_case_count": sum(1 for case in cases if case["status"] == "failed"),
            "scored_case_count": len(scores),
        }

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise AdapterEvalProjectNotFoundError(f"Project not found: {project_id}") from exc

    def _chapter(
        self,
        chapter_id: str | None,
        project_id: str,
    ) -> dict[str, Any] | None:
        if not chapter_id:
            return None
        try:
            chapter = self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise AdapterEvalChapterNotFoundError(f"Chapter not found: {chapter_id}") from exc
        if chapter.get("project_id") != project_id:
            raise AdapterEvalChapterNotFoundError(f"Chapter not found: {chapter_id}")
        return chapter

    def _scene(self, scene_id: str, chapter: dict[str, Any] | None) -> None:
        if not chapter:
            raise AdapterEvalChapterNotFoundError(f"Scene requires chapter: {scene_id}")
        scenes = self.novel_service.list_scenes(chapter["id"], limit=200)
        if not any(item.get("id") == scene_id for item in scenes):
            raise AdapterEvalChapterNotFoundError(f"Scene not found: {scene_id}")

    def _base_model(self, model_id: str) -> Any:
        try:
            return self.model_repository.get(model_id)
        except InvalidModelPathError as exc:
            raise AdapterEvalBaseModelNotFoundError(f"Base model not found: {model_id}") from exc

    def _adapter(self, adapter_id: str) -> Any:
        try:
            return self.adapter_repository.get(adapter_id)
        except AdapterNotFoundError as exc:
            raise AdapterEvalAdapterNotFoundError(f"Adapter not found: {adapter_id}") from exc

    @staticmethod
    def _adapter_compatible(adapter: Any) -> None:
        compatible = adapter.get("compatible", True) if isinstance(adapter, dict) else getattr(adapter, "compatible", True)
        errors = adapter.get("compatibility_errors", []) if isinstance(adapter, dict) else getattr(adapter, "compatibility_errors", ())
        if not compatible:
            raise AdapterEvalAdapterIncompatibleError("; ".join(str(item) for item in errors))

    def _dataset_version(self, dataset_version_id: str) -> dict[str, Any]:
        try:
            return self.dataset_service.get_version(dataset_version_id)
        except Exception as exc:
            raise AdapterEvalContextFailedError(f"DatasetVersion not found: {dataset_version_id}") from exc

    def _finetune_run(self, run_id: str) -> dict[str, Any]:
        try:
            return self.finetune_service.records.get_run(run_id)
        except Exception as exc:
            raise AdapterEvalFineTuneRunNotFoundError(f"FineTuneRun not found: {run_id}") from exc

    @staticmethod
    def _session_status(status: str) -> str:
        value = str(status)
        if value not in SESSION_STATUSES:
            raise AdapterEvalContextFailedError(f"Unsupported session status: {value}")
        return value

    @staticmethod
    def _case_status(status: str) -> str:
        value = str(status)
        if value not in CASE_STATUSES:
            raise AdapterEvalContextFailedError(f"Unsupported case status: {value}")
        return value
