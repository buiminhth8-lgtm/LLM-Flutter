"""Safe local model scanner."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from .entities import LocalModel, ModelFormat, ModelStatus
from .metadata import (
    detect_gguf_metadata,
    detect_transformers_metadata,
    directory_size,
    relative_files,
)
from .storage import ModelStorageLayout


class ModelScanner:
    def __init__(self, layout: ModelStorageLayout, external_paths: list[str] | None = None):
        self.layout = layout
        self.external_paths = external_paths or []

    def scan(self) -> list[LocalModel]:
        candidates: list[Path] = []
        for base in (self.layout.root_dir / "transformers", self.layout.root_dir / "gptq", self.layout.root_dir / "awq"):
            candidates.extend(self._safe_children(base))
        candidates.extend(self._safe_children(self.layout.root_dir / "gguf"))
        if self.layout.allow_external_paths:
            candidates.extend(Path(item) for item in self.external_paths)

        models: list[LocalModel] = []
        for candidate in candidates:
            try:
                model = self._scan_one(candidate)
            except Exception as exc:
                model = self._error_model(candidate, str(exc))
            if model:
                models.append(model)
        return models

    def _safe_children(self, base: Path) -> list[Path]:
        if not base.exists():
            return []
        children: list[Path] = []
        for item in base.iterdir():
            if item.is_symlink() and not self.layout.follow_symlinks:
                continue
            if item.is_dir() or item.suffix.lower() == ".gguf":
                children.append(item)
        return children

    def _scan_one(self, path: Path) -> LocalModel | None:
        path = path.expanduser().resolve()
        if path.is_symlink() and not self.layout.follow_symlinks:
            return None
        if path.is_file() and path.suffix.lower() == ".gguf":
            meta = detect_gguf_metadata(path)
            size = path.stat().st_size
            files = (path.name,)
        elif path.is_dir():
            if not (path / "config.json").exists() and not any(path.glob("*.gguf")):
                return None
            meta = detect_transformers_metadata(path)
            size = directory_size(path)
            files = relative_files(path)
        else:
            return None

        stat = path.stat()
        return LocalModel(
            id=self._model_id(path),
            display_name=path.stem if path.is_file() else path.name,
            path=path,
            format=meta.get("format", ModelFormat.UNKNOWN),
            status=meta.get("status", ModelStatus.UNSUPPORTED),
            architecture=meta.get("architecture"),
            parameter_count=meta.get("parameter_count"),
            quantization=meta.get("quantization"),
            context_length=meta.get("context_length"),
            size_bytes=size,
            files=files,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            metadata_errors=tuple(meta.get("errors", ())),
        )

    def _error_model(self, path: Path, error: str) -> LocalModel:
        resolved = path.expanduser().resolve()
        size = resolved.stat().st_size if resolved.exists() and resolved.is_file() else 0
        return LocalModel(
            id=self._model_id(resolved),
            display_name=resolved.name,
            path=resolved,
            format=ModelFormat.UNKNOWN,
            status=ModelStatus.CORRUPTED,
            architecture=None,
            parameter_count=None,
            quantization=None,
            context_length=None,
            size_bytes=size,
            files=(),
            metadata_errors=(error,),
        )

    def _model_id(self, path: Path) -> str:
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
        safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in path.stem if ch)[:80]
        return f"{safe_name}-{digest}"
