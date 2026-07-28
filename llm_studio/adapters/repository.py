"""Adapter repository."""

from __future__ import annotations

from pathlib import Path

from llm_studio.models.storage import layout_from_config

from .entities import AdapterInfo
from .exceptions import AdapterNotFoundError
from .scanner import AdapterScanner


class AdapterRepository:
    def __init__(self, config):
        self.layout = layout_from_config(config)
        self.layout.ensure()
        self.scanner = AdapterScanner(self.layout.adapters_dir)

    def list(self) -> list[AdapterInfo]:
        return self.scanner.scan()

    def get(self, adapter_id: str) -> AdapterInfo:
        for adapter in self.list():
            if adapter.id == adapter_id or str(adapter.path) == adapter_id:
                return adapter
        raise AdapterNotFoundError(adapter_id)

    def register_path(self, path: str) -> AdapterInfo:
        return self.scanner.scan_one(Path(path))
