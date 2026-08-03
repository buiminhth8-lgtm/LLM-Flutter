"""EvaluationService orchestration for Stage 11."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_studio.adapter_evaluation.errors import AdapterEvaluationError
from llm_studio.api import errors as api_errors
from llm_studio.jobs import JobType
from llm_studio.memory.errors import MemoryError
from llm_studio.novels.errors import NovelError
from llm_studio.revisions.errors import RevisionError
from llm_studio.writing.errors import WritingError

from .entities import EVALUATOR_TYPES, RUN_STATUSES, TARGET_TYPES, EvaluationTarget
from .errors import (
    EvaluationCancelNotSupportedError,
    EvaluationInvalidEvaluatorError,
    EvaluationInvalidTargetTypeError,
    EvaluationReportFailedError,
    EvaluationRunFailedError,
    EvaluationTargetNotFoundError,
    EvaluationTextEmptyError,
)
from .evaluators import HEURISTIC_EVALUATORS, LocalModelJudgeEvaluator
from .evaluators.base import EvaluationInput, EvaluationResult
from .evaluators.local_model_judge import LocalModelJudgeUnavailableEvaluator
from .findings import safe_category, safe_severity, validate_finding_status
from .job_runner import run_evaluation_job
from .reports import EvaluationReportBuilder
from .repository import EvaluationRepository
from .schemas import model_dump_compat
from .scoring import aggregate_overall_score, validate_dimensions, validate_manual_score

DEFAULT_EVALUATORS = (
    "repetition",
    "style_consistency",
    "character_consistency",
    "world_consistency",
    "plot_coherence",
    "pacing",
    "memory_usage",
    "foreshadowing",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_text(value: str | None, field: str = "text") -> str:
    text = (value or "").strip()
    if not text:
        raise EvaluationTextEmptyError(f"{field} is empty.")
    return text


class EvaluationService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        writing_service: Any | None = None,
        revision_service: Any | None = None,
        memory_service: Any | None = None,
        adapter_evaluation_service: Any | None = None,
        model_repository: Any | None = None,
        runtime_bridge: Any | None = None,
        job_queue: Any | None = None,
        report_builder: EvaluationReportBuilder | None = None,
    ):
        self.db_path = Path(db_path)
        self.records = EvaluationRepository(self.db_path)
        self.novel_service = novel_service
        self.writing_service = writing_service
        self.revision_service = revision_service
        self.memory_service = memory_service
        self.adapter_evaluation_service = adapter_evaluation_service
        self.model_repository = model_repository
        self.runtime_bridge = runtime_bridge
        self.job_queue = job_queue
        self.report_builder = report_builder or EvaluationReportBuilder()

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        writing_service: Any | None = None,
        revision_service: Any | None = None,
        memory_service: Any | None = None,
        adapter_evaluation_service: Any | None = None,
        model_repository: Any | None = None,
        runtime_bridge: Any | None = None,
        job_queue: Any | None = None,
    ) -> EvaluationService:
        cfg = config.get("evaluation", {}) if config is not None else {}
        fallback = (
            config.get("memory", {}).get(
                "db_path",
                config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite"),
            )
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(
            Path(cfg.get("db_path", fallback)),
            novel_service=novel_service,
            writing_service=writing_service,
            revision_service=revision_service,
            memory_service=memory_service,
            adapter_evaluation_service=adapter_evaluation_service,
            model_repository=model_repository,
            runtime_bridge=runtime_bridge,
            job_queue=job_queue,
        )

    async def create_run(self, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        name = _require_text(data.get("name"), "name")
        target = self._resolve_target(data)
        evaluator_config = data.get("evaluator_config") or {}
        evaluators = self._enabled_evaluators(evaluator_config)
        run = self.records.create_run(
            {
                "name": name,
                "description": data.get("description"),
                **self._target_ids(target),
                "target_type": target.target_type,
                "target_id": target.target_id,
                "evaluator_config": {**evaluator_config, "enabled_evaluators": evaluators},
                "created_by": data.get("created_by"),
            }
        )
        for evaluator_type in evaluators:
            self.records.create_case(
                {
                    "run_id": run["run_id"],
                    "project_id": target.project_id,
                    "chapter_id": target.chapter_id,
                    "target_type": target.target_type,
                    "target_id": target.target_id,
                    "evaluator_type": evaluator_type,
                    "input_snapshot": {
                        "target": target.snapshot,
                        "context": data.get("context") or {},
                        "text_hash_hint": len(target.text),
                    },
                }
            )
        if data.get("run_async", False):
            if self.job_queue is None:
                raise EvaluationRunFailedError("JobQueue is not configured for async evaluation.")
            job = self.job_queue.submit(
                JobType.EVALUATION.value,
                {
                    "run_id": run["run_id"],
                    "target_type": target.target_type,
                    "target_id": target.target_id,
                },
                run_evaluation_job(self, run["run_id"]),
            )
            return self.records.update_run(run["run_id"], {"status": "queued", "job_id": job.id})
        return await self.start_run(run["run_id"])

    async def run_sync(self, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        data["run_async"] = False
        return await self.create_run(data)

    async def start_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        if run["status"] == "archived":
            raise EvaluationRunFailedError("Archived evaluation run cannot start.")
        target = self._resolve_target(run)
        self.records.clear_case_outputs(run_id)
        run = self.records.update_run(
            run_id,
            {
                "status": "running",
                "started_at": _now(),
                "error_code": None,
                "error_message": None,
            },
        )
        summaries: list[str] = []
        try:
            for case in self.records.list_cases(run_id):
                self.records.update_case(case["case_id"], {"status": "running"})
                evaluator = self._evaluator(case["evaluator_type"], run["evaluator_config"])
                evaluation_input = EvaluationInput(
                    target_type=target.target_type,
                    target_id=target.target_id,
                    project_id=target.project_id,
                    chapter_id=target.chapter_id,
                    text=target.text,
                    context=case.get("input_snapshot", {}).get("context") or {},
                    references=target.references,
                )
                result = evaluator.evaluate(evaluation_input)
                if inspect.isawaitable(result):
                    result = await result
                assert isinstance(result, EvaluationResult)
                self._save_result(run_id, case["case_id"], result)
                if result.summary:
                    summaries.append(result.summary)
                self.records.update_case(case["case_id"], {"status": "completed"})
            metrics = self.records.list_metrics(run_id)
            overall = aggregate_overall_score(metrics)
            return self.records.update_run(
                run_id,
                {
                    "status": "completed",
                    "overall_score": overall,
                    "summary_text": self._summary(overall, summaries),
                    "finished_at": _now(),
                },
            )
        except Exception as exc:
            code = getattr(exc, "code", api_errors.EVALUATION_RUN_FAILED)
            message = getattr(exc, "message", str(exc))
            self.records.update_run(
                run_id,
                {
                    "status": "failed",
                    "error_code": code,
                    "error_message": message,
                    "finished_at": _now(),
                },
            )
            if isinstance(exc, EvaluationRunFailedError):
                raise
            raise EvaluationRunFailedError(message) from exc

    def cancel_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        if run["status"] in {"completed", "failed", "cancelled", "archived"}:
            raise EvaluationCancelNotSupportedError("Terminal evaluation run cannot be cancelled.")
        if run.get("job_id") and self.job_queue is not None:
            try:
                self.job_queue.cancel(run["job_id"])
            except Exception:
                pass
        return self.records.update_run(run_id, {"status": "cancelled", "finished_at": _now()})

    def archive_run(self, run_id: str) -> dict[str, Any]:
        return self.records.update_run(run_id, {"status": "archived"})

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        return {
            **run,
            "cases": self.records.list_cases(run_id),
            "metrics": self.records.list_metrics(run_id),
            "findings": self.records.list_findings(run_id),
            "manual_scores": self.records.list_manual_scores(run_id),
            "reports": self.records.list_reports(run_id),
        }

    def list_runs(
        self,
        *,
        project_id: str | None = None,
        target_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if target_type:
            self._target_type(target_type)
        if status:
            self._run_status(status)
        return self.records.list_runs(
            project_id=project_id,
            target_type=target_type,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_metrics(self, run_id: str) -> list[dict[str, Any]]:
        return self.records.list_metrics(run_id)

    def get_findings(
        self,
        run_id: str,
        *,
        category: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_findings(
            run_id,
            category=category,
            severity=severity,
            status=status,
            limit=limit,
            offset=offset,
        )

    def update_finding_status(self, finding_id: str, status: str) -> dict[str, Any]:
        return self.records.update_finding_status(finding_id, validate_finding_status(status))

    def add_manual_score(self, run_id: str, request: Any) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        data = model_dump_compat(request)
        overall = validate_manual_score(data.get("overall_score"))
        dimensions = validate_dimensions(data.get("dimensions") or {})
        score = self.records.add_manual_score(
            {
                "run_id": run_id,
                "target_type": run["target_type"],
                "target_id": run["target_id"],
                "reviewer_id": data.get("reviewer_id"),
                "overall_score": overall,
                "dimensions": dimensions,
                "notes": data.get("notes"),
            }
        )
        if overall is not None:
            self.records.add_metric(
                {
                    "run_id": run_id,
                    "metric_name": "manual_overall_score",
                    "metric_value": float(overall),
                    "metric_unit": "score",
                    "metric": {"source": "manual", "dimensions": dimensions},
                }
            )
        if data.get("notes"):
            self.records.add_finding(
                {
                    "run_id": run_id,
                    "severity": "info",
                    "category": "manual",
                    "title": "人工评估备注",
                    "message": data["notes"],
                    "evidence": {"reviewer_id": data.get("reviewer_id")},
                    "suggestion": None,
                }
            )
        metrics = self.records.list_metrics(run_id)
        self.records.update_run(run_id, {"overall_score": aggregate_overall_score(metrics)})
        return score

    def list_manual_scores(self, run_id: str) -> list[dict[str, Any]]:
        return self.records.list_manual_scores(run_id)

    def generate_report(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        try:
            cases = self.records.list_cases(run_id)
            metrics = self.records.list_metrics(run_id)
            findings = self.records.list_findings(run_id)
            manual = self.records.list_manual_scores(run_id)
            report = self.report_builder.build(
                run=run,
                cases=cases,
                metrics=metrics,
                findings=findings,
                manual_scores=manual,
            )
            return self.records.create_report(
                {
                    "run_id": run_id,
                    "report_type": self._report_type(run["target_type"]),
                    "report": report,
                    "summary_text": self.report_builder.summary(report),
                }
            )
        except EvaluationReportFailedError:
            raise
        except Exception as exc:
            raise EvaluationReportFailedError("Failed to generate evaluation report.") from exc

    def list_reports(self, run_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return self.records.list_reports(run_id, limit=limit, offset=offset)

    def get_report(self, report_id: str) -> dict[str, Any]:
        return self.records.get_report(report_id)

    def _save_result(self, run_id: str, case_id: str, result: EvaluationResult) -> None:
        for metric in result.metrics:
            self.records.add_metric(
                {
                    "run_id": run_id,
                    "case_id": case_id,
                    "metric_name": metric.metric_name,
                    "metric_value": metric.metric_value,
                    "metric_unit": metric.metric_unit,
                    "metric": metric.metric,
                }
            )
        for finding in result.findings:
            self.records.add_finding(
                {
                    "run_id": run_id,
                    "case_id": case_id,
                    "severity": safe_severity(finding.severity),
                    "category": safe_category(finding.category),
                    "title": finding.title,
                    "message": finding.message,
                    "evidence": finding.evidence,
                    "suggestion": finding.suggestion,
                }
            )

    def _enabled_evaluators(self, config: dict[str, Any]) -> list[str]:
        requested = list(config.get("enabled_evaluators") or DEFAULT_EVALUATORS)
        if config.get("use_local_model_judge") and "local_model_judge" not in requested:
            requested.append("local_model_judge")
        clean: list[str] = []
        for value in requested:
            evaluator = str(value)
            if evaluator not in EVALUATOR_TYPES or evaluator == "manual_score":
                raise EvaluationInvalidEvaluatorError(f"Invalid evaluator: {evaluator}")
            if evaluator not in clean:
                clean.append(evaluator)
        if not clean:
            raise EvaluationInvalidEvaluatorError("At least one evaluator is required.")
        return clean

    def _evaluator(self, evaluator_type: str, config: dict[str, Any]):
        if evaluator_type == "local_model_judge":
            model_id = config.get("local_model_id")
            if model_id and self.model_repository is not None:
                try:
                    self.model_repository.get(model_id)
                except Exception:
                    return LocalModelJudgeUnavailableEvaluator(
                        "本地评估模型不存在",
                        f"Local model not found: {model_id}",
                    )
            if self.runtime_bridge is None:
                return LocalModelJudgeUnavailableEvaluator(
                    "本地评估 Runtime 未配置",
                    "Runtime bridge is not configured.",
                )
            return LocalModelJudgeEvaluator(self.runtime_bridge, model_id or "")
        cls = HEURISTIC_EVALUATORS.get(evaluator_type)
        if cls is None:
            raise EvaluationInvalidEvaluatorError(f"Invalid evaluator: {evaluator_type}")
        return cls()

    def _resolve_target(self, data: dict[str, Any]) -> EvaluationTarget:
        target_type = self._target_type(str(data.get("target_type") or ""))
        target_id = str(data.get("target_id") or "")
        if not target_id:
            raise EvaluationTargetNotFoundError("target_id is required.")
        try:
            if target_type == "chapter":
                chapter = self.novel_service.get_chapter(target_id)
                text = _require_text(chapter.get("final_content") or chapter.get("draft_content"), "chapter text")
                refs = self._references(chapter["project_id"], chapter.get("id"))
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=chapter["project_id"],
                    chapter_id=chapter["id"],
                    snapshot=chapter,
                    references=refs,
                )
            if target_type == "project":
                project = self.novel_service.get_project(target_id)
                chapters = self.novel_service.list_chapters(project["id"], limit=500)
                text = "\n\n".join(
                    item.get("final_content") or item.get("draft_content") or item.get("summary") or ""
                    for item in chapters
                )
                text = _require_text(text, "project text")
                refs = self._references(project["id"], None)
                refs["chapters"] = chapters
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=project["id"],
                    snapshot=project,
                    references=refs,
                )
            if target_type == "generation":
                generation = self._generation(target_id)
                text = _require_text(generation.get("model_output"), "generation output")
                refs = self._references(generation.get("project_id"), generation.get("chapter_id"))
                refs["generation"] = generation
                if generation.get("input_context"):
                    refs["input_context"] = generation["input_context"]
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=generation.get("project_id"),
                    chapter_id=generation.get("chapter_id"),
                    generation_id=generation["generation_id"],
                    snapshot=generation,
                    references=refs,
                )
            if target_type == "revision":
                revision = self._revision(target_id)
                text = _require_text(revision.get("edited_text"), "revision text")
                refs = self._references(revision.get("project_id"), revision.get("chapter_id"))
                refs["revision"] = revision
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=revision.get("project_id"),
                    chapter_id=revision.get("chapter_id"),
                    generation_id=revision.get("generation_id"),
                    revision_id=revision["revision_id"],
                    snapshot=revision,
                    references=refs,
                )
            if target_type == "memory_retrieval":
                retrieval = self._memory_retrieval(target_id)
                chunks = retrieval.get("selected_chunks") or retrieval.get("retrieved_chunks") or []
                text = _require_text(
                    "\n".join(
                        str(item.get("text") or item.get("chunk_text") or item.get("title") or "")
                        for item in chunks
                    )
                    or retrieval.get("query_text"),
                    "memory retrieval text",
                )
                refs = self._references(retrieval.get("project_id"), retrieval.get("chapter_id"))
                refs["memory_retrieval"] = retrieval
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=retrieval.get("project_id"),
                    chapter_id=retrieval.get("chapter_id"),
                    memory_retrieval_id=retrieval["retrieval_id"],
                    snapshot=retrieval,
                    references=refs,
                )
            if target_type == "adapter_eval_session":
                session = self._adapter_session(target_id)
                cases = session.get("cases") or []
                outputs: list[str] = []
                for case in cases:
                    for result in case.get("results") or []:
                        outputs.append(str(result.get("output_text") or ""))
                text = _require_text("\n\n".join(outputs), "adapter evaluation output")
                refs = self._references(session.get("project_id"), None)
                refs["adapter_eval_session"] = session
                refs["adapter_scores"] = [case.get("score") for case in cases if case.get("score")]
                return EvaluationTarget(
                    target_type,
                    target_id,
                    text,
                    project_id=session.get("project_id"),
                    adapter_eval_session_id=session["session_id"],
                    snapshot=session,
                    references=refs,
                )
        except EvaluationTextEmptyError:
            raise
        except (NovelError, WritingError, RevisionError, MemoryError, AdapterEvaluationError) as exc:
            raise EvaluationTargetNotFoundError(f"Evaluation target not found: {target_id}") from exc
        raise EvaluationInvalidTargetTypeError(f"Invalid target_type: {target_type}")

    def _references(self, project_id: str | None, chapter_id: str | None) -> dict[str, Any]:
        refs: dict[str, Any] = {}
        if not project_id:
            return refs
        try:
            refs["project"] = self.novel_service.get_project(project_id)
            refs["characters"] = self.novel_service.list_characters(project_id, limit=500)
            refs["world_entries"] = self.novel_service.list_world_entries(project_id, limit=500)
            refs["plot_threads"] = self.novel_service.list_plot_threads(project_id, limit=500)
            refs["timeline_events"] = self.novel_service.list_timeline(project_id, limit=500)
            if chapter_id:
                refs["chapter"] = self.novel_service.get_chapter(chapter_id)
                refs["scenes"] = self.novel_service.list_scenes(chapter_id, limit=500)
        except NovelError:
            pass
        if self.memory_service is not None:
            try:
                refs["memory_documents"] = self.memory_service.list_documents(
                    project_id=project_id,
                    limit=500,
                )
            except Exception:
                refs["memory_documents"] = []
        return refs

    def _generation(self, generation_id: str) -> dict[str, Any]:
        if self.writing_service is None:
            raise EvaluationTargetNotFoundError("Writing service is not configured.")
        return self.writing_service.get_generation(generation_id)

    def _revision(self, revision_id: str) -> dict[str, Any]:
        if self.revision_service is None:
            raise EvaluationTargetNotFoundError("Revision service is not configured.")
        return self.revision_service.get_revision(revision_id)

    def _memory_retrieval(self, retrieval_id: str) -> dict[str, Any]:
        if self.memory_service is None:
            raise EvaluationTargetNotFoundError("Memory service is not configured.")
        return self.memory_service.get_retrieval_record(retrieval_id)

    def _adapter_session(self, session_id: str) -> dict[str, Any]:
        if self.adapter_evaluation_service is None:
            raise EvaluationTargetNotFoundError("Adapter Evaluation service is not configured.")
        return self.adapter_evaluation_service.get_session(session_id)

    @staticmethod
    def _target_ids(target: EvaluationTarget) -> dict[str, Any]:
        return {
            "project_id": target.project_id,
            "chapter_id": target.chapter_id,
            "generation_id": target.generation_id,
            "revision_id": target.revision_id,
            "adapter_eval_session_id": target.adapter_eval_session_id,
            "memory_retrieval_id": target.memory_retrieval_id,
        }

    @staticmethod
    def _target_type(target_type: str) -> str:
        if target_type not in TARGET_TYPES:
            raise EvaluationInvalidTargetTypeError(f"Invalid target_type: {target_type}")
        return target_type

    @staticmethod
    def _run_status(status: str) -> str:
        if status not in RUN_STATUSES:
            raise EvaluationInvalidEvaluatorError(f"Invalid run status: {status}")
        return status

    @staticmethod
    def _summary(overall: float | None, summaries: list[str]) -> str:
        score = "暂无总分" if overall is None else f"总分 {overall:.2f}"
        return f"{score}；已执行 {len(summaries)} 个评估器。自动评估仅供人工参考。"

    @staticmethod
    def _report_type(target_type: str) -> str:
        return {
            "chapter": "chapter",
            "project": "project",
            "adapter_eval_session": "adapter",
            "memory_retrieval": "memory",
        }.get(target_type, "summary")
