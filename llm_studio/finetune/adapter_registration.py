"""Adapter registration after successful Stage 8 training."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_studio.models.storage import ensure_within

from .errors import FineTuneAdapterExportFailedError, FineTuneAdapterRegisterFailedError


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff]+", "-", value.strip()).strip("-")
    return slug[:40] or "adapter"


class FineTuneAdapterRegistration:
    def __init__(self, adapter_repository: Any, *, checkpoint_manager: Any):
        self.adapter_repository = adapter_repository
        self.checkpoints = checkpoint_manager

    def register(
        self,
        *,
        run: dict[str, Any],
        adapter_path: str | Path,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        source = Path(adapter_path).expanduser().resolve()
        if not (source / "adapter_config.json").exists():
            raise FineTuneAdapterExportFailedError("adapter_config.json was not produced.")
        if not (source / "adapter_model.safetensors").exists() and not (source / "adapter_model.bin").exists():
            raise FineTuneAdapterExportFailedError("adapter_model.safetensors was not produced.")
        run_dir = self.checkpoints.run_dir(run["run_id"])
        ensure_within(source, run_dir)
        metadata = {
            "source": "novel_studio_finetune",
            "run_id": run["run_id"],
            "dataset_version_id": run["dataset_version_id"],
            "recipe_id": run["recipe_id"],
            "base_model_id": run["base_model_id"],
            "method": run["method"],
            "adapter_name": run["adapter_name"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (source / "training_config.json").write_text(
            json.dumps(run.get("config_snapshot") or {}, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (source / "metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (source / "dataset_snapshot.json").write_text(
            json.dumps(
                run.get("dataset_manifest_snapshot") or {},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (source / "novel_finetune_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        target = self._target_dir(run)
        if target.exists():
            raise FineTuneAdapterRegisterFailedError("Adapter target already exists; refusing to overwrite.")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        try:
            adapter = self.adapter_repository.register_path(str(target))
        except Exception as exc:
            raise FineTuneAdapterRegisterFailedError("Adapter registration failed.") from exc
        return {
            "adapter_id": adapter.id,
            "adapter": adapter.to_dict(),
            "output_adapter_path": self.checkpoints.relative_path(source),
            "registered_adapter_path": self._relative_adapter_path(target),
            "auto_activated": False,
        }

    def _target_dir(self, run: dict[str, Any]) -> Path:
        adapters_dir = Path(self.adapter_repository.layout.adapters_dir).resolve()
        adapters_dir.mkdir(parents=True, exist_ok=True)
        name = f"novel-{_safe_slug(run['adapter_name'])}-{run['run_id'][:12]}"
        return ensure_within(adapters_dir / name, adapters_dir)

    def _relative_adapter_path(self, target: Path) -> str:
        adapters_dir = Path(self.adapter_repository.layout.adapters_dir).resolve()
        ensure_within(target, adapters_dir)
        try:
            return target.relative_to(adapters_dir.parent).as_posix()
        except ValueError:
            return target.name
