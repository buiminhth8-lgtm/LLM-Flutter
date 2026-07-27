"""Local model repository with atomic metadata cache updates."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .compatibility import assess_model_compatibility
from .entities import LocalModel
from .exceptions import InvalidModelPathError, ModelDeleteError
from .scanner import ModelScanner
from .storage import ModelStorageLayout, ensure_within, layout_from_config


class LocalModelRepository:
    def __init__(self, config, layout: ModelStorageLayout | None = None):
        self.config = config
        self.layout = layout or layout_from_config(config)
        self.layout.ensure()

    def scan(self) -> list[LocalModel]:
        external = [entry.get("path") for entry in self._load_external_registry() if entry.get("path")]
        models = ModelScanner(self.layout, external_paths=external).scan()
        self.save_index(models)
        return models

    def list_models(self, *, refresh: bool = False) -> list[LocalModel]:
        if refresh or not self.layout.metadata_cache.exists():
            return self.scan()
        try:
            data = json.loads(self.layout.metadata_cache.read_text(encoding="utf-8"))
            return [LocalModel.from_dict(item) for item in data.get("models", [])]
        except Exception:
            return self.scan()

    def save_index(self, models: list[LocalModel]) -> None:
        payload = {
            "schema_version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "models": [model.to_dict() for model in models],
        }
        self.layout.metadata_cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.layout.metadata_cache.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.layout.metadata_cache)

    def compatibility(self, model_id: str):
        model = self.get(model_id)
        return assess_model_compatibility(model)

    def get(self, model_id: str) -> LocalModel:
        for model in self.list_models():
            if model.id == model_id or str(model.path) == model_id:
                return model
        raise InvalidModelPathError(f"模型不存在: {model_id}")

    def move_to_trash(self, model_id: str, *, confirm: bool = False) -> Path:
        if not confirm:
            raise ModelDeleteError("删除模型需要二次确认，默认只进入回收站。")
        model = self.get(model_id)
        managed_path = ensure_within(model.path, self.layout.root_dir)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = self.layout.trash_dir / f"{stamp}-{managed_path.name}"
        if target.exists():
            raise ModelDeleteError(f"回收站目标已存在: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(managed_path), str(target))
        self.scan()
        return target

    def register_external(self, path: str) -> LocalModel:
        if not self.layout.allow_external_paths:
            raise InvalidModelPathError("当前配置不允许注册外部模型路径。")
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise InvalidModelPathError(f"外部模型路径不存在: {resolved}")
        if resolved.is_symlink() and not self.layout.follow_symlinks:
            raise InvalidModelPathError("默认不跟随符号链接，请在配置中显式启用 follow_symlinks。")

        entries = self._load_external_registry()
        if not any(Path(str(item.get("path"))).expanduser().resolve() == resolved for item in entries):
            entries.append(
                {
                    "path": str(resolved),
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._save_external_registry(entries)

        scanner = ModelScanner(self.layout, external_paths=[str(resolved)])
        models = scanner.scan()
        if not models:
            raise InvalidModelPathError(f"路径不是可识别模型: {resolved}")
        self.scan()
        return models[0]

    def unregister_external(self, model_id: str) -> bool:
        model = self.get(model_id)
        try:
            ensure_within(model.path, self.layout.root_dir)
        except InvalidModelPathError:
            entries = self._load_external_registry()
            kept = [
                item
                for item in entries
                if Path(str(item.get("path"))).expanduser().resolve() != model.path
            ]
            self._save_external_registry(kept)
            self.scan()
            return True
        raise ModelDeleteError("受管理模型不能只取消注册；请使用 move_to_trash。")

    def _external_registry_path(self) -> Path:
        return self.layout.metadata_cache.parent / "external_models.json"

    def _load_external_registry(self) -> list[dict[str, str]]:
        configured = [
            {"path": entry.get("path")}
            for entry in self.config.get("external_models", [])
            if entry.get("path")
        ]
        registry = self._external_registry_path()
        if not registry.exists():
            return configured
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            stored = data.get("models", [])
            if isinstance(stored, list):
                configured.extend(item for item in stored if isinstance(item, dict) and item.get("path"))
        except Exception:
            pass
        deduped: dict[str, dict[str, str]] = {}
        for item in configured:
            try:
                key = str(Path(str(item["path"])).expanduser().resolve())
            except Exception:
                continue
            deduped[key] = {"path": key, **{k: str(v) for k, v in item.items() if v is not None}}
        return list(deduped.values())

    def _save_external_registry(self, entries: list[dict[str, str]]) -> None:
        path = self._external_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"schema_version": 1, "models": entries}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, path)


__all__ = ["LocalModelRepository"]
