"""DatasetService orchestration for Novel Studio Stage 6."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from llm_studio.novels.errors import NovelError
from llm_studio.revisions.errors import RevisionError
from llm_studio.writing.errors import WritingError

from .entities import TrainingSampleDraft
from .errors import (
    DatasetError,
    DatasetInvalidStatusError,
    DatasetNoApprovedSamplesError,
    DatasetProjectNotFoundError,
    DatasetRevisionNotFoundError,
)
from .exporters import DatasetJsonlExporter
from .formats import (
    safe_dataset_status,
    safe_dataset_type,
    safe_export_format,
    safe_recipe_method,
    safe_recipe_status,
    safe_sample_status,
    safe_sample_type,
    safe_version_sample_split,
)
from .freeze_service import DatasetFreezeService
from .recipe_recommender import TrainingRecipeRecommender
from .repository import DatasetRepository
from .sample_builder import DatasetSampleBuilder
from .validators import validate_revision_for_dataset, validate_sample_draft


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        from .errors import DatasetSampleEmptyInstructionError

        raise DatasetSampleEmptyInstructionError(f"{field} is required.")
    return text


def _content_hash(sample_type: str, data: dict[str, Any]) -> str:
    if sample_type == "preference":
        parts = [
            sample_type,
            str(data.get("instruction") or ""),
            str(data.get("input") or ""),
            str(data.get("chosen") or ""),
            str(data.get("rejected") or ""),
        ]
    else:
        parts = [
            sample_type,
            str(data.get("instruction") or ""),
            str(data.get("input") or ""),
            str(data.get("output") or ""),
        ]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


class DatasetService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        export_root: str | Path,
        novel_service: Any,
        revision_service: Any,
        writing_service: Any | None = None,
        prompt_service: Any | None = None,
        sample_builder: DatasetSampleBuilder | None = None,
        exporter: DatasetJsonlExporter | None = None,
    ):
        self.db_path = Path(db_path)
        self.records = DatasetRepository(self.db_path)
        self.export_root = Path(export_root)
        self.novel_service = novel_service
        self.revision_service = revision_service
        self.writing_service = writing_service
        self.prompt_service = prompt_service
        self.sample_builder = sample_builder or DatasetSampleBuilder()
        self.exporter = exporter or DatasetJsonlExporter(self.export_root)
        self.freeze_service = DatasetFreezeService(self.records, export_root=self.export_root)
        self.recipe_recommender = TrainingRecipeRecommender()

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        revision_service: Any,
        writing_service: Any | None = None,
        prompt_service: Any | None = None,
    ) -> DatasetService:
        cfg = config.get("datasets", {}) if config is not None else {}
        fallback_db = (
            config.get("revisions", {}).get(
                "db_path",
                config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite"),
            )
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        raw_export_root = cfg.get("export_dir", "./data/datasets")
        export_root = Path(raw_export_root)
        if config is not None and not export_root.is_absolute():
            export_root = config.config_path.parent / export_root
        return cls(
            Path(cfg.get("db_path", fallback_db)),
            export_root=export_root,
            novel_service=novel_service,
            revision_service=revision_service,
            writing_service=writing_service,
            prompt_service=prompt_service,
        )

    def create_dataset(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        name = _require_text(data.get("name"), "name")
        dataset_type = safe_dataset_type(data.get("type"))
        project_id = data.get("project_id")
        if project_id:
            self._project(project_id)
        return self.records.create_dataset(
            {
                "name": name,
                "type": dataset_type,
                "description": data.get("description"),
                "project_id": project_id,
                "status": "draft",
                "metadata": data.get("metadata") or {},
                "created_by": data.get("created_by"),
            }
        )

    def list_datasets(
        self,
        *,
        project_id: str | None = None,
        type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if type:
            safe_dataset_type(type)
        if status:
            safe_dataset_status(status)
        return self.records.list_datasets(
            project_id=project_id,
            type=type,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        dataset = self.records.get_dataset(dataset_id)
        return {
            **dataset,
            "samples": self.records.list_samples(dataset_id, limit=100),
            "exports": self.records.list_exports(dataset_id, limit=50),
            "versions": self.records.list_dataset_versions(dataset_id, limit=50),
            "change_marks": self.records.list_change_marks(dataset_id, limit=20),
        }

    def update_dataset(self, dataset_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        changes: dict[str, Any] = {}
        if "name" in data and data["name"] is not None:
            changes["name"] = _require_text(data["name"], "name")
        if "type" in data and data["type"] is not None:
            changes["type"] = safe_dataset_type(data["type"])
        if "description" in data:
            changes["description"] = data.get("description")
        if "project_id" in data:
            if data.get("project_id"):
                self._project(data["project_id"])
            changes["project_id"] = data.get("project_id")
        if "status" in data and data["status"] is not None:
            changes["status"] = safe_dataset_status(data["status"])
        if "metadata" in data and data["metadata"] is not None:
            changes["metadata_json"] = json.dumps(
                data.get("metadata") or {},
                ensure_ascii=False,
                sort_keys=True,
            )
        return self.records.update_dataset(dataset_id, changes)

    def archive_dataset(self, dataset_id: str) -> dict[str, Any]:
        return self.records.update_dataset(dataset_id, {"status": "archived"})

    def mark_ready(self, dataset_id: str) -> dict[str, Any]:
        dataset = self.records.get_dataset(dataset_id)
        if dataset["status"] == "archived":
            raise DatasetInvalidStatusError("archived datasets cannot be marked ready")
        return self.records.update_dataset(dataset_id, {"status": "ready"})

    def mark_dirty(self, dataset_id: str, reason: str = "manual") -> dict[str, Any]:
        dataset = self.records.get_dataset(dataset_id)
        if dataset["status"] == "archived":
            raise DatasetInvalidStatusError("archived datasets cannot be marked dirty")
        self.records.update_dataset(dataset_id, {"status": "dirty"})
        self.records.mark_dataset_changed(
            dataset_id,
            reason=reason,
            changed_entity_type="training_dataset",
            changed_entity_id=dataset_id,
        )
        return self.records.get_dataset(dataset_id)

    def create_sample_from_revision(
        self,
        dataset_id: str,
        revision_id: str,
        sample_type: str = "sft",
    ) -> dict[str, Any]:
        dataset = self.records.get_dataset(dataset_id)
        if dataset["status"] == "archived":
            raise DatasetInvalidStatusError("archived datasets cannot accept new samples")
        sample_type = safe_sample_type(sample_type)
        revision = self._revision(revision_id)
        generation = self._generation(revision.get("generation_id"))
        prompt_version = self._prompt_version(generation)
        revision_warnings = validate_revision_for_dataset(revision)
        draft = self._build_draft(
            sample_type,
            revision=revision,
            generation=generation,
            prompt_version=prompt_version,
        )
        warnings = [*revision_warnings, *validate_sample_draft(draft, revision=revision)]
        return self._store_draft(dataset_id, draft, warnings=warnings)

    def bulk_create_samples_from_revisions(
        self,
        dataset_id: str,
        filters: Any,
    ) -> dict[str, Any]:
        self.records.get_dataset(dataset_id)
        data = _model_dump(filters)
        sample_type = safe_sample_type(data.get("sample_type"))
        limit = max(1, min(int(data.get("limit") or 100), 500))
        revisions = self.revision_service.list_revisions(
            project_id=data.get("project_id"),
            chapter_id=data.get("chapter_id"),
            status=data.get("revision_status"),
            limit=limit,
        )
        tags = set(data.get("tags") or [])
        min_score = data.get("min_score")
        accepted = bool(data.get("accepted_for_dataset", True))
        created: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for revision in revisions:
            if accepted and not revision.get("accepted_for_dataset"):
                continue
            if min_score is not None and int(revision.get("user_score") or 0) < int(min_score):
                continue
            if tags and not tags.issubset(set(revision.get("edit_tags") or [])):
                continue
            try:
                created.append(
                    self.create_sample_from_revision(
                        dataset_id,
                        revision["revision_id"],
                        sample_type=sample_type,
                    )
                )
            except DatasetError as exc:
                errors.append(
                    {
                        "revision_id": revision.get("revision_id"),
                        "error_code": exc.code,
                        "message": exc.message,
                    }
                )
        return {
            "created_count": len(created),
            "error_count": len(errors),
            "samples": created,
            "errors": errors,
        }

    def list_samples(
        self,
        dataset_id: str,
        *,
        status: str | None = None,
        sample_type: str | None = None,
        revision_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if status:
            safe_sample_status(status)
        if sample_type:
            safe_sample_type(sample_type)
        return self.records.list_samples(
            dataset_id,
            status=status,
            sample_type=sample_type,
            revision_id=revision_id,
            limit=limit,
            offset=offset,
        )

    def get_sample(self, sample_id: str) -> dict[str, Any]:
        return self.records.get_sample(sample_id)

    def update_sample(self, sample_id: str, request: Any) -> dict[str, Any]:
        current = self.records.get_sample(sample_id)
        data = _model_dump(request)
        changes: dict[str, Any] = {}
        sample_type = current["sample_type"]
        for field in ("instruction", "input", "output", "chosen", "rejected"):
            if field in data and data[field] is not None:
                changes[field] = data[field]
        if "quality_score" in data:
            changes["quality_score"] = data.get("quality_score")
        if "status" in data and data["status"] is not None:
            changes["status"] = safe_sample_status(data["status"])
        if "review_notes" in data:
            changes["review_notes"] = data.get("review_notes")
        metadata = current.get("metadata") or {}
        if data.get("metadata") is not None:
            metadata.update(data["metadata"])
            changes["metadata_json"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        merged = {**current, **changes}
        draft = TrainingSampleDraft(
            sample_type=sample_type,
            instruction=merged.get("instruction") or "",
            input=merged.get("input") or "",
            output=merged.get("output") or "",
            chosen=merged.get("chosen"),
            rejected=merged.get("rejected"),
            source_hash=merged["source_hash"],
            content_hash=_content_hash(sample_type, merged),
            quality_score=merged.get("quality_score"),
        )
        warnings = validate_sample_draft(draft)
        metadata = {**metadata, "warnings": warnings}
        changes["metadata_json"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        changes["content_hash"] = draft.content_hash
        return self.records.update_sample(sample_id, changes)

    def approve_sample(self, sample_id: str) -> dict[str, Any]:
        return self.records.update_sample(sample_id, {"status": "approved"})

    def reject_sample(self, sample_id: str, reason: str | None = None) -> dict[str, Any]:
        current = self.records.get_sample(sample_id)
        notes = current.get("review_notes") or ""
        if reason:
            notes = f"{notes}\nReject reason: {reason}".strip()
        return self.records.update_sample(
            sample_id,
            {"status": "rejected", "review_notes": notes or current.get("review_notes")},
        )

    def remove_sample(self, sample_id: str) -> dict[str, Any]:
        return self.records.update_sample(sample_id, {"status": "archived"})

    def export_dataset(self, dataset_id: str, request: Any) -> dict[str, Any]:
        dataset = self.records.get_dataset(dataset_id)
        data = _model_dump(request)
        export_format = safe_export_format(data.get("format"))
        approved_only = bool(data.get("approved_only", True))
        samples = self.records.list_samples_for_export(
            dataset_id,
            approved_only=approved_only,
        )
        if approved_only and not samples:
            raise DatasetNoApprovedSamplesError("No approved samples are available for export.")
        if not approved_only and not samples:
            raise DatasetNoApprovedSamplesError("No exportable samples are available.")
        export_result = self.exporter.export(
            dataset,
            samples,
            export_format=export_format,
            approved_only=approved_only,
            file_name=data.get("file_name"),
        )
        return self.records.create_export(
            dataset_id,
            {
                "export_format": export_format,
                "export_path": export_result["export_path"],
                "sample_count": export_result["sample_count"],
                "approved_only": approved_only,
                "export_hash": export_result["export_hash"],
                "status": "created",
            },
        )

    def list_exports(self, dataset_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return self.records.list_exports(dataset_id, limit=limit, offset=offset)

    def get_export(self, export_id: str) -> dict[str, Any]:
        return self.records.get_export(export_id)

    def freeze_dataset(self, dataset_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        data["dataset_id"] = dataset_id
        return self.freeze_service.freeze_dataset(data)

    def list_versions(
        self,
        dataset_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_dataset_versions(dataset_id, limit=limit, offset=offset)

    def get_version(self, dataset_version_id: str) -> dict[str, Any]:
        version = self.records.get_dataset_version(dataset_version_id)
        return {
            **version,
            "samples": self.records.list_dataset_version_samples(dataset_version_id, limit=100),
            "recipes": self.records.list_training_recipes(dataset_version_id, limit=50),
        }

    def get_manifest(self, dataset_version_id: str) -> dict[str, Any]:
        version = self.records.get_dataset_version(dataset_version_id)
        return self.freeze_service.manifest_writer.read_manifest(version["manifest_path"])

    def list_version_samples(
        self,
        dataset_version_id: str,
        *,
        split: str | None = None,
        has_warnings: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if split:
            split = safe_version_sample_split(split)
        return self.records.list_dataset_version_samples(
            dataset_version_id,
            split=split,
            has_warnings=has_warnings,
            limit=limit,
            offset=offset,
        )

    def recommend_recipe(self, dataset_version_id: str, request: Any) -> dict[str, Any]:
        version = self.records.get_dataset_version(dataset_version_id)
        data = _model_dump(request)
        recommendation = self.recipe_recommender.recommend(
            version,
            base_model_id=data.get("base_model_id"),
            method=data.get("method"),
            hardware=data.get("hardware") or {},
            preferences=data.get("preferences") or {},
        )
        return self.records.create_training_recipe(recommendation)

    def list_recipes(
        self,
        dataset_version_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_training_recipes(dataset_version_id, limit=limit, offset=offset)

    def get_recipe(self, recipe_id: str) -> dict[str, Any]:
        return self.records.get_training_recipe(recipe_id)

    def update_recipe(self, recipe_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        changes: dict[str, Any] = {}
        if "base_model_id" in data:
            changes["base_model_id"] = data.get("base_model_id")
        if data.get("method") is not None:
            changes["method"] = safe_recipe_method(data.get("method"))
        if data.get("status") is not None:
            changes["status"] = safe_recipe_status(data.get("status"))
        if data.get("user_config") is not None:
            changes["user_config_json"] = json.dumps(
                data.get("user_config") or {},
                ensure_ascii=False,
                sort_keys=True,
            )
        return self.records.update_training_recipe(recipe_id, changes)

    def confirm_recipe(self, recipe_id: str) -> dict[str, Any]:
        return self.records.confirm_training_recipe(recipe_id)

    def archive_recipe(self, recipe_id: str) -> dict[str, Any]:
        return self.records.update_training_recipe(recipe_id, {"status": "archived"})

    def _build_draft(
        self,
        sample_type: str,
        *,
        revision: dict[str, Any],
        generation: dict[str, Any] | None,
        prompt_version: dict[str, Any] | None,
    ) -> TrainingSampleDraft:
        if sample_type == "preference":
            return self.sample_builder.build_preference_from_revision(
                revision,
                generation=generation,
                prompt_version=prompt_version,
            )
        return self.sample_builder.build_sft_from_revision(
            revision,
            generation=generation,
            prompt_version=prompt_version,
        )

    def _store_draft(
        self,
        dataset_id: str,
        draft: TrainingSampleDraft,
        *,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        metadata = {**draft.metadata, "warnings": warnings}
        return self.records.create_sample(
            dataset_id,
            {
                "project_id": draft.project_id,
                "chapter_id": draft.chapter_id,
                "revision_id": draft.revision_id,
                "generation_id": draft.generation_id,
                "sample_type": draft.sample_type,
                "instruction": draft.instruction,
                "input": draft.input,
                "output": draft.output,
                "chosen": draft.chosen,
                "rejected": draft.rejected,
                "metadata": metadata,
                "source_hash": draft.source_hash,
                "content_hash": draft.content_hash,
                "quality_score": draft.quality_score,
                "status": "pending",
            },
        )

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise DatasetProjectNotFoundError(project_id) from exc

    def _revision(self, revision_id: str) -> dict[str, Any]:
        try:
            return self.revision_service.get_revision(revision_id)
        except RevisionError as exc:
            raise DatasetRevisionNotFoundError(revision_id) from exc

    def _generation(self, generation_id: str | None) -> dict[str, Any] | None:
        if not generation_id or self.writing_service is None:
            return None
        try:
            return self.writing_service.get_generation(generation_id)
        except WritingError:
            return None

    def _prompt_version(self, generation: dict[str, Any] | None) -> dict[str, Any] | None:
        if not generation or self.prompt_service is None:
            return None
        version_id = generation.get("template_version_id")
        if not version_id:
            return None
        try:
            return self.prompt_service.get_version(version_id)
        except Exception:
            return None
