"""JSONL exporters for Stage 6 Dataset Builder."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_studio.models.storage import ensure_within

from .errors import DatasetExportFailedError, DatasetExportPathInvalidError
from .formats import CHATML_SYSTEM_PROMPT

_SAFE_FILE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_file_name(value: str | None, *, fallback: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = fallback
    name = _SAFE_FILE_RE.sub("-", raw).strip(".-")
    if not name or name in {".", ".."} or ".." in name:
        name = fallback
    if not name.endswith(".jsonl"):
        name += ".jsonl"
    return name


def _metadata_for_sample(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": sample.get("sample_id"),
        "revision_id": sample.get("revision_id"),
        "generation_id": sample.get("generation_id"),
        "project_id": sample.get("project_id"),
        "chapter_id": sample.get("chapter_id"),
        "quality_score": sample.get("quality_score"),
        "status": sample.get("status"),
    }


class DatasetJsonlExporter:
    def __init__(self, export_root: str | Path):
        self.export_root = Path(export_root).resolve()
        self.export_root.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        dataset: dict[str, Any],
        samples: list[dict[str, Any]],
        *,
        export_format: str,
        approved_only: bool = True,
        file_name: str | None = None,
    ) -> dict[str, Any]:
        dataset_id = dataset["dataset_id"]
        dataset_dir = ensure_within(self.export_root / dataset_id, self.export_root)
        exports_dir = ensure_within(dataset_dir / "exports", self.export_root)
        exports_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = ensure_within(dataset_dir / "metadata.json", self.export_root)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        safe_name = _safe_file_name(file_name, fallback=f"export-{timestamp}.jsonl")
        export_path = ensure_within(exports_dir / safe_name, self.export_root)
        try:
            metadata = {
                "dataset_id": dataset_id,
                "name": dataset.get("name"),
                "type": dataset.get("type"),
                "status": dataset.get("status"),
                "sample_count": len(samples),
                "export_format": export_format,
                "approved_only": approved_only,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            with export_path.open("w", encoding="utf-8", newline="\n") as handle:
                for sample in samples:
                    payload = self._payload(sample, export_format)
                    handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
                    handle.write("\n")
            digest = hashlib.sha256(export_path.read_bytes()).hexdigest()
            return {
                "export_path": self._relative_export_path(export_path),
                "export_hash": digest,
                "sample_count": len(samples),
            }
        except Exception as exc:
            if hasattr(exc, "code"):
                raise
            raise DatasetExportFailedError("Failed to export dataset JSONL.") from exc

    def _relative_export_path(self, path: Path) -> str:
        try:
            rel = path.relative_to(self.export_root.parent)
            return rel.as_posix()
        except ValueError as exc:
            raise DatasetExportPathInvalidError("Export path must stay inside data/datasets.") from exc

    @staticmethod
    def _payload(sample: dict[str, Any], export_format: str) -> dict[str, Any]:
        if export_format == "chatml_jsonl":
            return {
                "messages": [
                    {"role": "system", "content": CHATML_SYSTEM_PROMPT},
                    {"role": "user", "content": sample.get("input") or sample.get("instruction") or ""},
                    {"role": "assistant", "content": sample.get("output") or ""},
                ],
                "metadata": _metadata_for_sample(sample),
            }
        if export_format == "preference_jsonl":
            return {
                "prompt": sample.get("input") or sample.get("instruction") or "",
                "chosen": sample.get("chosen") or sample.get("output") or "",
                "rejected": sample.get("rejected") or "",
                "metadata": _metadata_for_sample(sample),
            }
        payload = {
            "instruction": sample.get("instruction") or "",
            "input": sample.get("input") or "",
            "output": sample.get("output") or "",
        }
        if export_format == "sft_jsonl":
            payload["metadata"] = _metadata_for_sample(sample)
        return payload
