"""Revision edit tag definitions and validation."""

from __future__ import annotations

from .errors import RevisionInvalidTagError

EDIT_TAG_LABELS: dict[str, str] = {
    "language_polish": "语言润色",
    "plot_fix": "剧情修正",
    "character_consistency": "人物一致性增强",
    "dialogue_improve": "对白优化",
    "pacing_adjust": "节奏调整",
    "detail_expand": "细节补充",
    "remove_redundancy": "减少废话",
    "style_unify": "文风统一",
    "logic_fix": "逻辑修复",
    "worldbuilding_fix": "世界观修正",
    "emotion_enhance": "情绪增强",
    "scene_atmosphere": "场景氛围增强",
    "continuity_fix": "连贯性修复",
    "other": "其他",
}

VALID_EDIT_TAGS = frozenset(EDIT_TAG_LABELS)


def validate_edit_tags(tags: list[str] | tuple[str, ...] | None) -> list[str]:
    if tags is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        value = str(tag or "").strip()
        if value not in VALID_EDIT_TAGS:
            raise RevisionInvalidTagError(value)
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized
