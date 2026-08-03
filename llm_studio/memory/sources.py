"""Memory source type definitions and source-to-document helpers."""

from __future__ import annotations

import json
from typing import Any

from .errors import MemoryInvalidSourceTypeError, MemoryInvalidStatusError

SOURCE_TYPES: dict[str, str] = {
    "chapter": "章节",
    "scene": "场景",
    "character": "人物",
    "world_entry": "世界观",
    "plot_thread": "剧情线",
    "timeline_event": "时间线",
    "revision": "人工修订",
    "generation": "生成记录",
    "adapter_eval_result": "Adapter 评估结果",
    "manual_note": "手动记忆",
    "foreshadowing": "伏笔",
}

DOCUMENT_STATUSES = {"active", "stale", "archived", "deleted"}

SOURCE_PRIORITY_WEIGHTS: dict[str, float] = {
    "character": 1.3,
    "world_entry": 1.2,
    "plot_thread": 1.25,
    "timeline_event": 1.1,
    "chapter": 1.0,
    "revision": 1.15,
    "generation": 0.8,
    "adapter_eval_result": 0.9,
    "manual_note": 1.4,
    "scene": 1.1,
    "foreshadowing": 1.35,
}


def validate_source_type(source_type: str) -> str:
    value = str(source_type or "").strip()
    if value not in SOURCE_TYPES:
        raise MemoryInvalidSourceTypeError(value)
    return value


def validate_document_status(status: str) -> str:
    value = str(status or "").strip() or "active"
    if value not in DOCUMENT_STATUSES:
        raise MemoryInvalidStatusError(value)
    return value


def parse_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            decoded = None
        if isinstance(decoded, list):
            return [str(item).strip() for item in decoded if str(item).strip()]
        return [item.strip() for item in text.replace("，", ",").split(",") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def source_label(source_type: str) -> str:
    return SOURCE_TYPES.get(source_type, source_type)


def source_weight(source_type: str) -> float:
    return SOURCE_PRIORITY_WEIGHTS.get(source_type, 1.0)


def should_index_status(status: str | None) -> bool:
    return (status or "active") not in {"archived", "deleted"}

