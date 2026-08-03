"""Checkpoint directory and metadata management for Stage 8 fine-tune runs."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from llm_studio.models.storage import ensure_within

from .errors import FineTuneOutputPathInvalidError


class FineTuneCheckpointManager:
    def __init__(self, output_root: str | Path):
        self.output_root = Path(output_root).resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        if not run_id or any(part in run_id for part in ("..", "/", "\\")):
            raise FineTuneOutputPathInvalidError("Invalid run id for output path.")
        return ensure_within(self.output_root / "runs" / run_id, self.output_root)

    def ensure_run_layout(self, run_id: str) -> dict[str, Path]:
        run_dir = self.run_dir(run_id)
        paths = {
            "run_dir": run_dir,
            "checkpoints": run_dir / "checkpoints",
            "last": run_dir / "checkpoints" / "last",
            "best": run_dir / "checkpoints" / "best",
            "periodic": run_dir / "checkpoints" / "periodic",
            "adapter": run_dir / "adapter",
        }
        for path in paths.values():
            ensure_within(path, run_dir).mkdir(parents=True, exist_ok=True)
        return paths

    def record_checkpoint(
        self,
        run_id: str,
        *,
        checkpoint_type: str,
        step: int,
        source_path: str | Path | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        layout = self.ensure_run_layout(run_id)
        checkpoint_type = checkpoint_type if checkpoint_type in {"last", "best", "periodic", "manual"} else "periodic"
        target = ensure_within(
            layout[checkpoint_type] / f"step-{int(step)}",
            layout["run_dir"],
        )
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        if source_path:
            source = Path(source_path).expanduser().resolve()
            if source.exists() and source.is_dir():
                for item in source.iterdir():
                    dst = target / item.name
                    if item.is_dir():
                        shutil.copytree(item, dst)
                    else:
                        shutil.copy2(item, dst)
            elif source.exists():
                shutil.copy2(source, target / source.name)
        else:
            (target / "checkpoint.json").write_text(
                f'{{"step":{int(step)},"checkpoint_type":"{checkpoint_type}"}}',
                encoding="utf-8",
            )
        return {
            "checkpoint_type": checkpoint_type,
            "step": int(step),
            "epoch": (metrics or {}).get("epoch"),
            "train_loss": (metrics or {}).get("train_loss"),
            "val_loss": (metrics or {}).get("val_loss"),
            "checkpoint_path": self.relative_path(target),
            "checkpoint_hash": self.path_hash(target),
            "size_bytes": self.size_bytes(target),
        }

    def relative_path(self, path: str | Path) -> str:
        target = Path(path).expanduser().resolve()
        ensure_within(target, self.output_root)
        try:
            return target.relative_to(self.output_root.parent).as_posix()
        except ValueError as exc:
            raise FineTuneOutputPathInvalidError("Fine-tune output must stay under data/finetune.") from exc

    @staticmethod
    def path_hash(path: str | Path) -> str:
        target = Path(path)
        digest = hashlib.sha256()
        if target.is_file():
            digest.update(target.read_bytes())
            return digest.hexdigest()
        for item in sorted(target.rglob("*")):
            if item.is_file():
                digest.update(item.relative_to(target).as_posix().encode("utf-8"))
                digest.update(item.read_bytes())
        return digest.hexdigest()

    @staticmethod
    def size_bytes(path: str | Path) -> int:
        target = Path(path)
        if target.is_file():
            return target.stat().st_size
        return sum(item.stat().st_size for item in target.rglob("*") if item.is_file())
