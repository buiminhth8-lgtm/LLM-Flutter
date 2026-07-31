"""Dataset freeze orchestration for immutable Stage 7 DatasetVersion records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dedupe import DatasetDedupeService
from .errors import (
    DatasetFreezeFailedError,
    DatasetFreezeNoApprovedSamplesError,
    DatasetFreezeNotReadyError,
)
from .formats import safe_export_format, safe_split_strategy
from .manifest import DatasetManifestWriter
from .repository import DatasetRepository
from .splitter import DatasetSplitter
from .token_stats import DatasetTokenStats
from .versioning import build_dataset_version_hash


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


class DatasetFreezeService:
    def __init__(
        self,
        repository: DatasetRepository,
        *,
        export_root: str | Path,
        dedupe_service: DatasetDedupeService | None = None,
        splitter: DatasetSplitter | None = None,
        token_stats: DatasetTokenStats | None = None,
        manifest_writer: DatasetManifestWriter | None = None,
    ):
        self.records = repository
        self.export_root = Path(export_root)
        self.dedupe = dedupe_service or DatasetDedupeService()
        self.splitter = splitter or DatasetSplitter()
        self.token_stats = token_stats or DatasetTokenStats()
        self.manifest_writer = manifest_writer or DatasetManifestWriter(export_root)

    def freeze_dataset(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        dataset_id = data.get("dataset_id")
        if not dataset_id:
            raise DatasetFreezeFailedError("dataset_id is required.")
        dataset = self.records.get_dataset(dataset_id)
        if dataset["status"] not in {"ready", "dirty"}:
            raise DatasetFreezeNotReadyError("Only ready or dirty datasets can be frozen.")
        samples = self.records.list_samples_for_export(dataset_id, approved_only=True)
        if not samples:
            raise DatasetFreezeNoApprovedSamplesError("No approved samples are available for freeze.")
        export_format = safe_export_format(data.get("export_format"))
        split_config = self._split_config(data.get("split") or {})
        dedupe_config = self._dedupe_config(data.get("dedupe") or {})
        self._validate_samples(samples)
        dedupe_result = self.dedupe.dedupe(samples, **dedupe_config)
        split_result = self.splitter.split(dedupe_result["kept"], **split_config)
        train_entries = split_result["train"]
        val_entries = split_result["val"]
        excluded_entries = dedupe_result["excluded"]
        self._assign_stats(train_entries)
        self._assign_stats(val_entries)
        self._assign_stats(excluded_entries)
        train_samples = [entry["sample"] for entry in train_entries]
        val_samples = [entry["sample"] for entry in val_entries]
        train_stats = self.token_stats.summarize(train_samples)
        val_stats = self.token_stats.summarize(val_samples)
        version = self.records.next_dataset_version_number(dataset_id)
        dataset_version_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        version_sample_rows = self._version_sample_rows(
            dataset_version_id,
            train_entries=train_entries,
            val_entries=val_entries,
            excluded_entries=excluded_entries,
        )
        counts = {
            "source_samples": len(samples),
            "train_samples": len(train_entries),
            "val_samples": len(val_entries),
            "duplicates_excluded": int(dedupe_result["rejected_duplicate_count"]),
        }
        stats = {
            "train_chars": train_stats.char_count,
            "val_chars": val_stats.char_count,
            "train_token_estimate": train_stats.token_estimate,
            "val_token_estimate": val_stats.token_estimate,
        }
        warnings = [
            *split_result["warnings"],
            *self._entry_warnings(train_entries),
            *self._entry_warnings(val_entries),
            *self._entry_warnings(excluded_entries),
        ]
        artifact = self.manifest_writer.write_version_artifacts(
            dataset=dataset,
            dataset_version_id=dataset_version_id,
            version=version,
            export_format=export_format,
            split_config=split_config,
            train_samples=train_samples,
            val_samples=val_samples,
            counts=counts,
            stats=stats,
            warnings=warnings,
        )
        content_hash = build_dataset_version_hash(
            train_hash=artifact["train_hash"],
            val_hash=artifact["val_hash"],
            version_samples=version_sample_rows,
            split=split_config,
            export_format=export_format,
        )
        artifact = self.manifest_writer.write_version_artifacts(
            dataset=dataset,
            dataset_version_id=dataset_version_id,
            version=version,
            export_format=export_format,
            split_config=split_config,
            train_samples=train_samples,
            val_samples=val_samples,
            counts=counts,
            stats=stats,
            warnings=warnings,
            content_hash=content_hash,
        )
        version_record = self.records.create_dataset_version(
            {
                "id": dataset_version_id,
                "dataset_id": dataset_id,
                "version": version,
                "name": (data.get("name") or dataset.get("name") or f"Dataset v{version}").strip(),
                "description": data.get("description"),
                "status": "frozen",
                "source_sample_count": len(samples),
                "train_sample_count": len(train_entries),
                "val_sample_count": len(val_entries),
                "rejected_duplicate_count": int(dedupe_result["rejected_duplicate_count"]),
                "warning_count": len(warnings),
                "train_char_count": train_stats.char_count,
                "val_char_count": val_stats.char_count,
                "train_token_estimate": train_stats.token_estimate,
                "val_token_estimate": val_stats.token_estimate,
                "content_hash": content_hash,
                "manifest_path": artifact["manifest_path"],
                "train_path": artifact["train_path"],
                "val_path": artifact["val_path"],
                "metadata": {
                    "split": split_config,
                    "dedupe": dedupe_config,
                    "export_format": export_format,
                    "warnings": warnings,
                    "created_at": created_at,
                },
                "created_by": data.get("created_by"),
                "created_at": created_at,
            }
        )
        self.records.create_dataset_version_samples(dataset_version_id, version_sample_rows)
        self.records.update_dataset(dataset_id, {"status": "frozen"})
        return {
            **version_record,
            "warnings": warnings,
            "manifest": artifact["manifest"],
            "version_samples": self.records.list_dataset_version_samples(
                dataset_version_id,
                limit=1000,
            ),
        }

    @staticmethod
    def _split_config(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "strategy": safe_split_strategy(raw.get("strategy")),
            "val_ratio": float(raw.get("val_ratio", 0.1)),
            "seed": int(raw.get("seed", 42)),
        }

    @staticmethod
    def _dedupe_config(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "exact_hash": bool(raw.get("exact_hash", True)),
            "near_duplicate": bool(raw.get("near_duplicate", True)),
            "near_duplicate_threshold": float(raw.get("near_duplicate_threshold", 0.92)),
        }

    @staticmethod
    def _validate_samples(samples: list[dict[str, Any]]) -> None:
        for sample in samples:
            if not (sample.get("instruction") or "").strip():
                raise DatasetFreezeFailedError("Approved sample has empty instruction.")
            if sample.get("sample_type") == "preference":
                if not (sample.get("chosen") or sample.get("output") or "").strip():
                    raise DatasetFreezeFailedError("Approved preference sample has empty chosen/output.")
            elif not (sample.get("output") or "").strip():
                raise DatasetFreezeFailedError("Approved SFT sample has empty output.")

    def _assign_stats(self, entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            sample = entry["sample"]
            entry["char_count"] = self.token_stats.sample_char_count(sample)
            entry["token_estimate"] = self.token_stats.estimate_sample_tokens(sample)

    @staticmethod
    def _entry_warnings(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        for entry in entries:
            warnings.extend(entry.get("warnings") or [])
        return warnings

    @staticmethod
    def _version_sample_rows(
        dataset_version_id: str,
        *,
        train_entries: list[dict[str, Any]],
        val_entries: list[dict[str, Any]],
        excluded_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for split, entries in (
            ("train", train_entries),
            ("val", val_entries),
            ("excluded", excluded_entries),
        ):
            for index, entry in enumerate(entries):
                sample = entry["sample"]
                rows.append(
                    {
                        "dataset_version_id": dataset_version_id,
                        "sample_id": sample["sample_id"],
                        "split": split,
                        "sample_order": index,
                        "content_hash": entry.get("content_hash") or sample.get("content_hash") or "",
                        "source_hash": sample.get("source_hash"),
                        "char_count": int(entry.get("char_count") or 0),
                        "token_estimate": int(entry.get("token_estimate") or 0),
                        "duplicate_group_id": entry.get("duplicate_group_id"),
                        "warnings": entry.get("warnings") or [],
                    }
                )
        return rows
