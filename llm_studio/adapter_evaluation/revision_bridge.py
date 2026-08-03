"""Bridge Adapter Evaluation results into Stage 5 Revision records."""

from __future__ import annotations

from typing import Any

from .errors import (
    AdapterEvalResultPairIncompleteError,
    AdapterEvalRevisionCreateFailedError,
)
from .schemas import model_dump_compat


class AdapterEvaluationRevisionBridge:
    def __init__(self, repository: Any, revision_service: Any):
        self.repository = repository
        self.revision_service = revision_service

    def create_revision_from_result(self, result_id: str, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        selected = self.repository.get_result(result_id)
        case = self.repository.get_case(selected["case_id"])
        results = {
            item["variant"]: item
            for item in self.repository.list_results(case_id=case["case_id"])
        }
        original_source = data.get("source_original") or "base"
        if original_source != "base":
            raise AdapterEvalResultPairIncompleteError(
                "Stage 9 revision bridge currently requires source_original=base."
            )
        base = results.get("base")
        if not base or base.get("status") != "succeeded" or not base.get("output_text"):
            raise AdapterEvalResultPairIncompleteError(
                "Base output is required before creating a Revision from evaluation."
            )
        edited_text = selected.get("output_text") or ""
        if selected.get("status") != "succeeded" or not edited_text.strip():
            raise AdapterEvalResultPairIncompleteError(
                "Selected evaluation result has no successful output."
            )
        try:
            return self.revision_service.create_from_adapter_evaluation(
                {
                    "project_id": data["project_id"],
                    "chapter_id": data.get("chapter_id"),
                    "scene_id": data.get("scene_id"),
                    "original_text": base["output_text"],
                    "edited_text": edited_text,
                    "edit_tags": data.get("edit_tags") or [],
                    "user_score": data.get("user_score"),
                    "quality_notes": data.get("quality_notes"),
                    "reviewer_id": data.get("reviewer_id"),
                    "accepted_for_dataset": False,
                }
            )
        except AdapterEvalResultPairIncompleteError:
            raise
        except Exception as exc:
            raise AdapterEvalRevisionCreateFailedError(
                "Failed to create Revision from adapter evaluation result."
            ) from exc
