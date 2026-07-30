"""Default global Prompt Studio templates."""

from __future__ import annotations

from typing import Any

DEFAULT_PROMPT_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "章节生成",
        "type": "chapter_generate",
        "description": "用于根据项目资料和章节大纲生成章节正文的预览模板。",
        "system_prompt": "你是一名专业网络小说作者，擅长长篇连载小说创作。",
        "role_prompt": "你需要保持人物性格、世界观规则和剧情线一致。",
        "instruction_template": (
            "小说标题：\n{{project_title}}\n\n"
            "小说类型：\n{{genre}}\n\n"
            "目标风格：\n{{target_style}}\n\n"
            "世界观设定：\n{{world_setting}}\n\n"
            "主要人物：\n{{characters}}\n\n"
            "当前章节标题：\n{{chapter_title}}\n\n"
            "当前章节大纲：\n{{chapter_outline}}\n\n"
            "当前章节目标：\n{{current_chapter_goal}}\n\n"
            "写作要求：\n"
            "1. 使用 {{pov}}。\n"
            "2. 字数控制在 {{target_length}}。\n"
            "3. 保持人物性格一致。\n"
            "4. 不要跳过关键情节。\n"
            "5. 不要直接总结剧情，要写成正文。\n"
            "6. 避免重复、空泛和流水账。\n\n"
            "请输出当前章节正文。"
        ),
        "negative_prompt": "不要输出解释、提示词分析或创作计划。",
        "output_constraints": "只输出正文，不输出 Markdown 标题。",
        "variables_schema": {
            "project_title": {"type": "string", "required": True, "description": "小说标题"},
            "genre": {"type": "string", "required": False, "description": "小说类型"},
            "target_style": {"type": "string", "required": False, "description": "目标风格"},
            "world_setting": {"type": "string", "required": False, "description": "世界观设定"},
            "characters": {"type": "string", "required": False, "description": "主要人物"},
            "chapter_title": {"type": "string", "required": True, "description": "章节标题"},
            "chapter_outline": {"type": "string", "required": True, "description": "章节大纲"},
            "current_chapter_goal": {"type": "string", "required": False, "description": "当前章节目标"},
            "pov": {"type": "string", "required": False, "description": "叙事视角"},
            "target_length": {"type": "string", "required": False, "description": "目标长度"},
        },
        "default_values": {"pov": "第三人称", "target_length": "1200-1800 中文字符"},
    },
    {
        "name": "章节续写",
        "type": "chapter_continue",
        "description": "基于已有章节草稿和当前目标续写。",
        "instruction_template": "已有内容：\n{{chapter_summary}}\n\n续写目标：\n{{current_chapter_goal}}\n\n请保持风格一致继续正文。",
        "variables_schema": {
            "chapter_summary": {"type": "string", "required": True},
            "current_chapter_goal": {"type": "string", "required": True},
        },
        "default_values": {},
    },
    {
        "name": "章节重写",
        "type": "chapter_rewrite",
        "description": "按新要求重写章节内容。",
        "instruction_template": "章节标题：{{chapter_title}}\n原章节摘要：{{chapter_summary}}\n重写要求：{{user_instruction}}",
        "variables_schema": {"chapter_title": {"type": "string", "required": True}, "user_instruction": {"type": "string", "required": True}},
        "default_values": {},
    },
    {
        "name": "润色",
        "type": "chapter_polish",
        "description": "优化语言表达和节奏。",
        "instruction_template": "请按 {{style}} 风格润色以下章节摘要或片段：\n{{chapter_summary}}",
        "variables_schema": {"chapter_summary": {"type": "string", "required": True}, "style": {"type": "string", "required": False}},
        "default_values": {"style": "清晰、克制、有画面感"},
    },
    {
        "name": "扩写",
        "type": "chapter_expand",
        "description": "扩展章节关键情节。",
        "instruction_template": "章节大纲：{{chapter_outline}}\n扩写重点：{{user_instruction}}\n目标长度：{{target_length}}",
        "variables_schema": {"chapter_outline": {"type": "string", "required": True}, "user_instruction": {"type": "string", "required": False}, "target_length": {"type": "string", "required": False}},
        "default_values": {"target_length": "1200 中文字符"},
    },
    {
        "name": "对白增强",
        "type": "dialogue_enhance",
        "description": "强化人物对白区分度。",
        "instruction_template": "人物：\n{{characters}}\n\n场景：\n{{scene_outline}}\n\n请增强对白，保持人物语气差异。",
        "variables_schema": {"characters": {"type": "string", "required": True}, "scene_outline": {"type": "string", "required": True}},
        "default_values": {},
    },
    {
        "name": "场景扩写",
        "type": "scene_expand",
        "description": "扩展单个场景。",
        "instruction_template": "场景大纲：{{scene_outline}}\n地点：{{world_setting}}\n视角：{{pov}}\n请扩写该场景。",
        "variables_schema": {"scene_outline": {"type": "string", "required": True}, "world_setting": {"type": "string", "required": False}, "pov": {"type": "string", "required": False}},
        "default_values": {"pov": "第三人称"},
    },
    {
        "name": "大纲生成",
        "type": "outline_generate",
        "description": "基于项目设定生成章节大纲。",
        "instruction_template": "小说：{{project_title}}\n世界观：{{world_setting}}\n剧情线：{{plot_threads}}\n请生成下一章大纲。",
        "variables_schema": {"project_title": {"type": "string", "required": True}, "world_setting": {"type": "string", "required": False}, "plot_threads": {"type": "string", "required": False}},
        "default_values": {},
    },
    {
        "name": "人物生成",
        "type": "character_generate",
        "description": "辅助构思人物资料。",
        "instruction_template": "小说类型：{{genre}}\n世界观：{{world_setting}}\n需求：{{user_instruction}}\n请生成人物设定。",
        "variables_schema": {"genre": {"type": "string", "required": False}, "world_setting": {"type": "string", "required": False}, "user_instruction": {"type": "string", "required": True}},
        "default_values": {},
    },
    {
        "name": "世界观生成",
        "type": "world_entry_generate",
        "description": "辅助构思世界观条目。",
        "instruction_template": "小说标题：{{project_title}}\n类别：{{user_instruction}}\n请生成世界观条目。",
        "variables_schema": {"project_title": {"type": "string", "required": True}, "user_instruction": {"type": "string", "required": True}},
        "default_values": {},
    },
]


def ensure_default_prompt_templates(service) -> list[dict[str, Any]]:
    """Create default global templates if absent."""
    created: list[dict[str, Any]] = []
    existing = service.list_templates(scope="global", limit=200)
    existing_keys = {(item["type"], item["name"]) for item in existing}
    for template in DEFAULT_PROMPT_TEMPLATES:
        key = (template["type"], template["name"])
        if key in existing_keys:
            continue
        created.append(service.create_template({**template, "scope": "global", "change_note": "Default template"}))
    return created
