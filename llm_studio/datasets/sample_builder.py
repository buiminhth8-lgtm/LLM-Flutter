"""Build training sample drafts from Stage 5 revisions."""

from __future__ import annotations

import hashlib
from typing import Any

from .entities import TrainingSampleDraft
from .formats import DEFAULT_SFT_INSTRUCTION

INPUT_LONG_CHAR_THRESHOLD = 20000


def _hash(parts: list[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _first_instruction_line(prompt_version: dict[str, Any] | None) -> str:
    if not prompt_version:
        return DEFAULT_SFT_INSTRUCTION
    template = str(prompt_version.get("instruction_template") or "").strip()
    if not template:
        return DEFAULT_SFT_INSTRUCTION
    for line in template.splitlines():
        line = line.strip()
        if line and "{{" not in line and "}}" not in line:
            return line[:500]
    return DEFAULT_SFT_INSTRUCTION


def _input_from_generation(generation: dict[str, Any] | None) -> str:
    if not generation:
        return ""
    prompt = str(generation.get("prompt_rendered") or "").strip()
    if prompt:
        return prompt
    context = generation.get("input_context") or {}
    if not isinstance(context, dict) or not context:
        return ""
    lines: list[str] = []
    for key in sorted(context):
        value = context[key]
        if isinstance(value, (dict, list)):
            value = str(value)
        value = str(value or "").strip()
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


class DatasetSampleBuilder:
    def build_sft_from_revision(
        self,
        revision: dict[str, Any],
        *,
        generation: dict[str, Any] | None = None,
        prompt_version: dict[str, Any] | None = None,
    ) -> TrainingSampleDraft:
        instruction = _first_instruction_line(prompt_version)
        sample_input = _input_from_generation(generation)
        output = str(revision.get("edited_text") or "").strip()
        warnings: list[dict[str, Any]] = []
        if len(sample_input) > INPUT_LONG_CHAR_THRESHOLD:
            warnings.append(
                {
                    "code": "DATASET_SAMPLE_INPUT_LONG",
                    "message": "Sample input is long; Stage 6 records a warning instead of truncating.",
                }
            )
        source_hash = _hash(
            [
                str(revision.get("revision_id") or ""),
                str(revision.get("original_hash") or ""),
                str(revision.get("edited_hash") or ""),
            ]
        )
        content_hash = _hash(["sft", instruction, sample_input, output])
        return TrainingSampleDraft(
            sample_type="sft",
            project_id=revision.get("project_id"),
            chapter_id=revision.get("chapter_id"),
            revision_id=revision.get("revision_id"),
            generation_id=revision.get("generation_id"),
            instruction=instruction,
            input=sample_input,
            output=output,
            source_hash=source_hash,
            content_hash=content_hash,
            quality_score=revision.get("user_score"),
            warnings=warnings,
            metadata={
                "source": "revision",
                "revision_status": revision.get("status"),
                "revision_tags": revision.get("edit_tags") or [],
                "revision_score": revision.get("user_score"),
                "accepted_for_dataset": bool(revision.get("accepted_for_dataset")),
            },
        )

    def build_preference_from_revision(
        self,
        revision: dict[str, Any],
        *,
        generation: dict[str, Any] | None = None,
        prompt_version: dict[str, Any] | None = None,
    ) -> TrainingSampleDraft:
        instruction = _first_instruction_line(prompt_version)
        prompt = _input_from_generation(generation)
        chosen = str(revision.get("edited_text") or "").strip()
        rejected = str(revision.get("original_text") or "").strip()
        source_hash = _hash(
            [
                str(revision.get("revision_id") or ""),
                str(revision.get("original_hash") or ""),
                str(revision.get("edited_hash") or ""),
            ]
        )
        content_hash = _hash(["preference", instruction, prompt, chosen, rejected])
        return TrainingSampleDraft(
            sample_type="preference",
            project_id=revision.get("project_id"),
            chapter_id=revision.get("chapter_id"),
            revision_id=revision.get("revision_id"),
            generation_id=revision.get("generation_id"),
            instruction=instruction,
            input=prompt,
            output="",
            chosen=chosen,
            rejected=rejected,
            source_hash=source_hash,
            content_hash=content_hash,
            quality_score=revision.get("user_score"),
            metadata={
                "source": "revision",
                "revision_status": revision.get("status"),
                "revision_tags": revision.get("edit_tags") or [],
                "revision_score": revision.get("user_score"),
                "accepted_for_dataset": bool(revision.get("accepted_for_dataset")),
                "experimental": True,
            },
        )
