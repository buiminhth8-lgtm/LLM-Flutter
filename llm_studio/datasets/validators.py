"""Validation rules for Stage 6 Dataset Builder samples."""

from __future__ import annotations

from typing import Any

from .entities import TrainingSampleDraft
from .errors import (
    DatasetRevisionNotAcceptedError,
    DatasetSampleEmptyInstructionError,
    DatasetSampleEmptyOutputError,
    DatasetSampleUnchangedError,
)


def revision_dataset_warnings(revision: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if revision.get("status") != "approved":
        warnings.append(
            {
                "code": "DATASET_REVISION_NOT_APPROVED",
                "message": "Revision is not approved; Stage 6 allows draft sample creation with a warning.",
            }
        )
    return warnings


def validate_revision_for_dataset(revision: dict[str, Any]) -> list[dict[str, Any]]:
    if not bool(revision.get("accepted_for_dataset")):
        raise DatasetRevisionNotAcceptedError(
            "Revision must be marked accepted_for_dataset before creating a training sample."
        )
    return revision_dataset_warnings(revision)


def validate_sample_draft(
    draft: TrainingSampleDraft,
    *,
    revision: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    warnings = list(draft.warnings)
    instruction = draft.instruction.strip()
    if not instruction:
        raise DatasetSampleEmptyInstructionError("Sample instruction is required.")

    if draft.sample_type == "preference":
        if not (draft.chosen or "").strip() or not (draft.rejected or "").strip():
            raise DatasetSampleEmptyOutputError("Preference chosen and rejected are required.")
    else:
        output = draft.output.strip()
        if not output:
            raise DatasetSampleEmptyOutputError("SFT sample output is required.")
        if output == draft.input.strip():
            raise DatasetSampleUnchangedError("SFT output must not be identical to input.")
        if revision is not None and output == str(revision.get("original_text") or "").strip():
            warnings.append(
                {
                    "code": "DATASET_SAMPLE_UNCHANGED_FROM_ORIGINAL",
                    "message": "Sample output is identical to the original model text; manual revision may be insufficient.",
                }
            )
    if draft.quality_score is not None and not (1 <= int(draft.quality_score) <= 5):
        raise DatasetSampleEmptyOutputError("quality_score must be between 1 and 5.")
    return warnings
