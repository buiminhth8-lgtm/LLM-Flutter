"""RevisionService orchestration for Novel Studio Stage 5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llm_studio.novels.errors import NovelError
from llm_studio.writing.errors import WritingError

from .diff import TextDiffService
from .errors import (
    RevisionAutosaveError,
    RevisionDiffFailedError,
    RevisionEditedTextEmptyError,
    RevisionInvalidStatusError,
    RevisionOriginalTextEmptyError,
    RevisionRelatedNotFoundError,
)
from .repository import RevisionRecordRepository
from .scoring import dataset_candidate_warnings, validate_user_score
from .tags import validate_edit_tags

REVISION_STATUSES = frozenset({"draft", "reviewing", "approved", "rejected", "archived"})
REVISION_SOURCES = frozenset(
    {"generation", "chapter_draft", "manual", "adapter_evaluation"}
)


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


def _require_text(value: str | None, *, original: bool) -> str:
    text = (value or "").strip()
    if not text:
        if original:
            raise RevisionOriginalTextEmptyError("original_text is required.")
        raise RevisionEditedTextEmptyError("edited_text is required.")
    return text


class RevisionService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        writing_service: Any,
        diff_service: TextDiffService | None = None,
        autosave_retention: int = 20,
    ):
        self.db_path = Path(db_path)
        self.novel_service = novel_service
        self.writing_service = writing_service
        self.diff_service = diff_service or TextDiffService()
        self.records = RevisionRecordRepository(
            self.db_path,
            autosave_retention=autosave_retention,
        )

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        writing_service: Any,
    ) -> RevisionService:
        cfg = config.get("revisions", {}) if config is not None else {}
        fallback = (
            config.get("writing", {}).get(
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
            autosave_retention=int(cfg.get("autosave_retention", 20)),
        )

    def create_from_generation(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        generation = self._generation(data.get("generation_id") or "")
        original = _require_text(generation.get("model_output"), original=True)
        edited = _require_text(data.get("edited_text") or original, original=False)
        project_id = generation["project_id"]
        self._project(project_id)
        chapter_id = generation.get("chapter_id")
        if chapter_id:
            self._chapter(chapter_id, project_id)
        return self._create(
            {
                **data,
                "generation_id": generation["generation_id"],
                "project_id": project_id,
                "chapter_id": chapter_id,
                "scene_id": generation.get("scene_id"),
                "original_text": original,
                "edited_text": edited,
                "source": "generation",
            }
        )

    def create_from_chapter_draft(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        project_id = data["project_id"]
        self._project(project_id)
        chapter = self._chapter(data["chapter_id"], project_id)
        self._scene(data.get("scene_id"), chapter)
        original = _require_text(
            data.get("original_text") or chapter.get("draft_content"),
            original=True,
        )
        edited = _require_text(data.get("edited_text"), original=False)
        return self._create(
            {
                **data,
                "original_text": original,
                "edited_text": edited,
                "source": "chapter_draft",
            }
        )

    def create_manual(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        project_id = data["project_id"]
        self._project(project_id)
        chapter = self._chapter(data.get("chapter_id"), project_id)
        self._scene(data.get("scene_id"), chapter)
        data["original_text"] = _require_text(data.get("original_text"), original=True)
        data["edited_text"] = _require_text(data.get("edited_text"), original=False)
        return self._create({**data, "source": "manual"})

    def create_from_adapter_evaluation(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        project_id = data["project_id"]
        self._project(project_id)
        chapter = self._chapter(data.get("chapter_id"), project_id)
        self._scene(data.get("scene_id"), chapter)
        data["original_text"] = _require_text(data.get("original_text"), original=True)
        data["edited_text"] = _require_text(data.get("edited_text"), original=False)
        data["accepted_for_dataset"] = False
        return self._create({**data, "source": "adapter_evaluation"})

    def update_revision(self, revision_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        current = self.records.get(revision_id)
        changes: dict[str, Any] = {}
        if "edited_text" in data:
            edited = _require_text(data.get("edited_text"), original=False)
            changes["edited_text"] = edited
            changes["diff"] = self._diff(current["original_text"], edited)
        if "edit_tags" in data:
            changes["edit_tags"] = validate_edit_tags(data.get("edit_tags"))
        if "user_score" in data:
            changes["user_score"] = validate_user_score(data.get("user_score"))
        if "quality_notes" in data:
            changes["quality_notes"] = data.get("quality_notes")
        if "status" in data:
            changes["status"] = self._status(data.get("status"))
        if "accepted_for_dataset" in data:
            changes["accepted_for_dataset"] = bool(data.get("accepted_for_dataset"))
        if "reviewer_id" in data:
            changes["reviewer_id"] = data.get("reviewer_id")
        updated = self.records.update(
            revision_id,
            changes,
            expected_updated_at=data.get("expected_updated_at"),
        )
        return self._with_warnings(updated)

    def autosave_revision(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        try:
            project = self._project(data["project_id"])
            if data.get("chapter_id"):
                self._chapter(data["chapter_id"], project["id"])
            if data.get("revision_id"):
                revision = self.records.get(data["revision_id"])
                if revision["project_id"] != project["id"]:
                    raise RevisionRelatedNotFoundError("project", project["id"])
            draft_text = _require_text(data.get("draft_text"), original=False)
            return self.records.create_autosave({**data, "draft_text": draft_text})
        except RevisionAutosaveError:
            raise
        except Exception as exc:
            if hasattr(exc, "code"):
                raise
            raise RevisionAutosaveError("Failed to save revision autosave.") from exc

    def get_revision(self, revision_id: str) -> dict[str, Any]:
        return self.records.get(revision_id)

    def list_revisions(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        generation_id: str | None = None,
        status: str | None = None,
        user_score: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if status:
            self._status(status)
        if user_score is not None:
            user_score = validate_user_score(user_score)
        return self.records.list(
            project_id=project_id,
            chapter_id=chapter_id,
            generation_id=generation_id,
            status=status,
            user_score=user_score,
            limit=limit,
            offset=offset,
        )

    def approve_revision(self, revision_id: str) -> dict[str, Any]:
        return self.records.update(revision_id, {"status": "approved"})

    def reject_revision(self, revision_id: str, reason: str | None = None) -> dict[str, Any]:
        current = self.records.get(revision_id)
        notes = current.get("quality_notes") or ""
        if reason:
            notes = f"{notes}\nReject reason: {reason}".strip()
        return self.records.update(
            revision_id,
            {"status": "rejected", "quality_notes": notes or current.get("quality_notes")},
        )

    def mark_dataset_candidate(self, revision_id: str, accepted: bool = True) -> dict[str, Any]:
        updated = self.records.update(
            revision_id,
            {"accepted_for_dataset": bool(accepted)},
        )
        return self._with_warnings(updated)

    def archive_revision(self, revision_id: str) -> dict[str, Any]:
        return self.records.update(revision_id, {"status": "archived"})

    def list_autosaves(self, revision_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        self.records.get(revision_id)
        return self.records.list_autosaves(revision_id, limit=limit)

    def _create(self, data: dict[str, Any]) -> dict[str, Any]:
        tags = validate_edit_tags(data.get("edit_tags"))
        score = validate_user_score(data.get("user_score"))
        original = _require_text(data.get("original_text"), original=True)
        edited = _require_text(data.get("edited_text"), original=False)
        source = data.get("source", "manual")
        if source not in REVISION_SOURCES:
            source = "manual"
        record = self.records.create(
            {
                "generation_id": data.get("generation_id"),
                "project_id": data["project_id"],
                "chapter_id": data.get("chapter_id"),
                "scene_id": data.get("scene_id"),
                "original_text": original,
                "edited_text": edited,
                "diff": self._diff(original, edited),
                "edit_tags": tags,
                "user_score": score,
                "quality_notes": data.get("quality_notes"),
                "status": self._status(data.get("status") or "draft"),
                "accepted_for_dataset": bool(data.get("accepted_for_dataset")),
                "reviewer_id": data.get("reviewer_id"),
                "source": source,
            }
        )
        return self._with_warnings(record)

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise RevisionRelatedNotFoundError("project", project_id) from exc

    def _chapter(self, chapter_id: str | None, project_id: str) -> dict[str, Any] | None:
        if not chapter_id:
            return None
        try:
            chapter = self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise RevisionRelatedNotFoundError("chapter", chapter_id) from exc
        if chapter.get("project_id") != project_id:
            raise RevisionRelatedNotFoundError("chapter", chapter_id)
        return chapter

    def _scene(self, scene_id: str | None, chapter: dict[str, Any] | None) -> None:
        if not scene_id:
            return
        if not chapter:
            raise RevisionRelatedNotFoundError("chapter", "")
        scenes = self.novel_service.list_scenes(chapter["id"], limit=200)
        if not any(item.get("id") == scene_id for item in scenes):
            raise RevisionRelatedNotFoundError("chapter", chapter["id"])

    def _generation(self, generation_id: str) -> dict[str, Any]:
        try:
            return self.writing_service.get_generation(generation_id)
        except WritingError as exc:
            raise RevisionRelatedNotFoundError("generation", generation_id) from exc

    def _diff(self, original: str, edited: str) -> dict[str, Any]:
        try:
            return self.diff_service.build_diff(original, edited)
        except Exception as exc:
            raise RevisionDiffFailedError("Failed to build revision diff.") from exc

    @staticmethod
    def _status(status: str | None) -> str:
        value = str(status or "").strip()
        if value not in REVISION_STATUSES:
            raise RevisionInvalidStatusError(f"Unsupported revision status: {value}")
        return value

    @staticmethod
    def _with_warnings(record: dict[str, Any]) -> dict[str, Any]:
        warnings = dataset_candidate_warnings(
            accepted_for_dataset=bool(record.get("accepted_for_dataset")),
            user_score=record.get("user_score"),
        )
        return {**record, "warnings": warnings}
