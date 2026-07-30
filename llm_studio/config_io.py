"""Configuration import/export with secret redaction."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

EXPORT_KEYS = {"runtime", "generation", "rag", "finetune", "models", "storage", "downloads", "api"}
SECRET_KEYS = {"password", "api_key", "token", "cookie", "secret", "authorization"}


def redact_config(data: dict[str, Any]) -> dict[str, Any]:
    def redact(value):
        if isinstance(value, dict):
            return {
                key: "<redacted>" if any(secret in key.lower() for secret in SECRET_KEYS) else redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    return {key: redact(data[key]) for key in EXPORT_KEYS if key in data}


def export_runtime_config(config, output_path: str | Path) -> Path:
    output = Path(output_path)
    payload = {"schema_version": 1, "config": redact_config(config._data)}
    output.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return output


def preview_import_config(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if data.get("schema_version") != 1:
        raise ValueError("配置导入 schema_version 不受支持。")
    imported = data.get("config")
    if not isinstance(imported, dict):
        raise ValueError("配置导入文件缺少 config 对象。")
    return imported


def import_runtime_config(config, path: str | Path, *, confirm: bool = False) -> Path:
    if not confirm:
        raise ValueError("导入配置需要用户确认。")
    preview_import_config(path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = config.config_path.with_suffix(f".{stamp}.bak.yaml")
    shutil.copy2(config.config_path, backup)
    shutil.copy2(path, config.config_path)
    return backup
