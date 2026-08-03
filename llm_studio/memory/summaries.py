"""Chapter summary prompt helpers for Memory Stage 10."""

from __future__ import annotations

SUMMARY_TYPES = {
    "short",
    "detailed",
    "timeline",
    "character_changes",
    "foreshadowing",
}

GENERATED_BY = {"manual", "model", "imported"}


def validate_summary_type(summary_type: str | None) -> str:
    value = str(summary_type or "short").strip() or "short"
    if value not in SUMMARY_TYPES:
        return "short"
    return value


def build_summary_prompt(source_text: str, *, max_chars: int = 500) -> str:
    return (
        "请将以下小说章节内容压缩为摘要，保留：\n"
        "1. 关键事件；\n"
        "2. 人物关系变化；\n"
        "3. 新增设定；\n"
        "4. 伏笔；\n"
        "5. 下一章需要记住的信息。\n\n"
        "要求：\n"
        "- 不评价文本质量；\n"
        "- 不扩写；\n"
        "- 不加入原文没有的信息；\n"
        f"- 控制在 {max_chars} 中文字符以内。\n\n"
        "章节内容：\n"
        f"{source_text}"
    )

