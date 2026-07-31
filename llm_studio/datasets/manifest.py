"""DatasetVersion artifact and manifest writer."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_studio.models.storage import ensure_within

from .errors import DatasetExportPathInvalidError, DatasetManifestInvalidError
from .exporters import DatasetJsonlExporter


class DatasetManifestWriter:
    def __init__(self, export_root: str | Path):
        self.export_root = Path(export_root).resolve()
        self.export_root.mkdir(parents=True, exist_ok=True)

    def write_version_artifacts(
        self,
        *,
        dataset: dict[str, Any],
        dataset_version_id: str,
        version: int,
        export_format: str,
        split_config: dict[str, Any],
        train_samples: list[dict[str, Any]],
        val_samples: list[dict[str, Any]],
        counts: dict[str, int],
        stats: dict[str, int],
        warnings: list[dict[str, Any]],
        content_hash: str | None = None,
    ) -> dict[str, Any]:
        dataset_id = dataset["dataset_id"]
        version_dir = ensure_within(
            self.export_root / dataset_id / "versions" / f"v{version}",
            self.export_root,
        )
        version_dir.mkdir(parents=True, exist_ok=True)
        train_path = ensure_within(version_dir / "train.jsonl", self.export_root)
        val_path = ensure_within(version_dir / "val.jsonl", self.export_root)
        manifest_path = ensure_within(version_dir / "manifest.json", self.export_root)
        self._write_jsonl(train_path, train_samples, export_format)
        if val_samples:
            self._write_jsonl(val_path, val_samples, export_format)
            val_hash = hashlib.sha256(val_path.read_bytes()).hexdigest()
            relative_val = self._relative_artifact_path(val_path)
        else:
            val_hash = ""
            relative_val = None
        train_hash = hashlib.sha256(train_path.read_bytes()).hexdigest()
        manifest_content_hash = content_hash or hashlib.sha256(
            f"{train_hash}\n{val_hash}".encode()
        ).hexdigest()
        manifest = {
            "dataset_version_id": dataset_version_id,
            "dataset_id": dataset_id,
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "format": export_format,
            "split": split_config,
            "counts": counts,
            "stats": stats,
            "hashes": {
                "content_hash": manifest_content_hash,
                "train_hash": train_hash,
                "val_hash": val_hash,
            },
            "warnings": warnings,
        }
        self._assert_manifest_safe(manifest)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "manifest": manifest,
            "manifest_path": self._relative_artifact_path(manifest_path),
            "train_path": self._relative_artifact_path(train_path),
            "val_path": relative_val,
            "train_hash": train_hash,
            "val_hash": val_hash,
            "content_hash": manifest_content_hash,
        }

    def read_manifest(self, path: str) -> dict[str, Any]:
        target = ensure_within(self.export_root.parent / path, self.export_root.parent)
        if not target.exists():
            from .errors import DatasetManifestNotFoundError

            raise DatasetManifestNotFoundError("Dataset manifest not found.")
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DatasetManifestInvalidError("Dataset manifest is not valid JSON.") from exc
        self._assert_manifest_safe(data)
        return data

    def _write_jsonl(self, path: Path, samples: list[dict[str, Any]], export_format: str) -> None:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for sample in samples:
                payload = DatasetJsonlExporter._payload(sample, export_format)
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
                handle.write("\n")

    def _relative_artifact_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.export_root.parent).as_posix()
        except ValueError as exc:
            raise DatasetExportPathInvalidError("Dataset artifact path must stay inside data/datasets.") from exc

    @staticmethod
    def _assert_manifest_safe(manifest: dict[str, Any]) -> None:
        text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        if "api_key" in text.lower() or ":\\" in text or "/Users/" in text or "/home/" in text:
            raise DatasetManifestInvalidError("Manifest contains sensitive or absolute-path data.")
