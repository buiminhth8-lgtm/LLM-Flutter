"""Benchmark result persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from llm_studio.models.storage import layout_from_config

from .entities import BenchmarkResult
from .report import render_markdown_report


class BenchmarkRepository:
    def __init__(self, config):
        self.layout = layout_from_config(config)
        self.layout.ensure()
        self.root = self.layout.benchmarks_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, result: BenchmarkResult) -> tuple[Path, Path]:
        json_path = self.root / f"{result.created_at.strftime('%Y%m%dT%H%M%SZ')}-{result.id}.json"
        md_path = json_path.with_suffix(".md")
        tmp_json = json_path.with_suffix(".json.tmp")
        tmp_md = md_path.with_suffix(".md.tmp")
        tmp_json.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_md.write_text(render_markdown_report(result), encoding="utf-8")
        os.replace(tmp_json, json_path)
        os.replace(tmp_md, md_path)
        return json_path, md_path

    def list(self) -> list[dict[str, object]]:
        items = []
        for path in sorted(self.root.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                items.append({"id": data.get("id"), "created_at": data.get("created_at"), "path": str(path)})
            except Exception:
                continue
        return items

    def get(self, result_id: str) -> dict[str, object]:
        for path in self.root.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("id") == result_id:
                return data
        raise FileNotFoundError(result_id)
