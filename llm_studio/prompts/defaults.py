"""Default global Prompt Studio templates.

The default set ships 24 Chinese novel-writing templates split into three
categories:

- ``writing``  : 正文生成类
- ``planning`` : 规划设定类
- ``editing``  : 辅助编辑类

Install / upgrade strategy (idempotent, never overwrites user edits):

1. Every builtin template carries ``metadata.builtin_key``.
2. ``metadata.content_hash`` records the hash of the content that was
   installed (or last upgraded).
3. ``ensure_default_prompt_templates`` matches templates by ``builtin_key``:
   - missing                     -> install a new builtin template
   - active hash != stored hash  -> user modified -> skip
   - stored hash == active hash but differs from the new builtin content
                                  -> pristine old builtin -> upgrade
   - otherwise                   -> skip

Templates without builtin metadata are user templates and are never touched.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .variables import extract_variables

COMMON_VARIABLE_SCHEMA: dict[str, Any] = {
    "project_title": {
        "type": "string",
        "required": True,
        "description": "小说标题",
    },
    "genre": {
        "type": "string",
        "required": False,
        "description": "小说类型，例如玄幻、都市、科幻、悬疑",
    },
    "target_style": {
        "type": "string",
        "required": False,
        "description": "目标文风，例如克制、紧张、热血、细腻、黑暗",
    },
    "target_audience": {
        "type": "string",
        "required": False,
        "description": "目标读者",
    },
    "world_setting": {
        "type": "string",
        "required": False,
        "description": "世界观设定",
    },
    "characters": {
        "type": "string",
        "required": False,
        "description": "主要人物资料",
    },
    "plot_threads": {
        "type": "string",
        "required": False,
        "description": "当前剧情线",
    },
    "timeline": {
        "type": "string",
        "required": False,
        "description": "时间线信息",
    },
    "retrieved_memory": {
        "type": "string",
        "required": False,
        "description": "RAG / Memory 召回的相关记忆",
    },
    "chapter_title": {
        "type": "string",
        "required": False,
        "description": "章节标题",
    },
    "chapter_outline": {
        "type": "string",
        "required": False,
        "description": "章节大纲",
    },
    "previous_chapter_summary": {
        "type": "string",
        "required": False,
        "description": "上一章摘要",
    },
    "current_chapter_goal": {
        "type": "string",
        "required": False,
        "description": "当前章节目标",
    },
    "draft_content": {
        "type": "string",
        "required": False,
        "description": "当前草稿内容",
    },
    "selected_text": {
        "type": "string",
        "required": False,
        "description": "用户选择的待处理文本",
    },
    "target_length": {
        "type": "string",
        "required": False,
        "description": "目标长度，例如 1200-1800 中文字符",
    },
    "pov": {
        "type": "string",
        "required": False,
        "description": "叙事视角",
    },
    "style": {
        "type": "string",
        "required": False,
        "description": "本次生成的具体风格要求",
    },
    "user_instruction": {
        "type": "string",
        "required": False,
        "description": "用户补充指令",
    },
    "forbidden_content": {
        "type": "string",
        "required": False,
        "description": "禁止出现的内容",
    },
}

SCENE_VARIABLES: dict[str, Any] = {
    "scene_title": {
        "type": "string",
        "required": False,
        "description": "场景标题",
    },
    "scene_location": {
        "type": "string",
        "required": False,
        "description": "场景地点",
    },
    "scene_timeline_note": {
        "type": "string",
        "required": False,
        "description": "场景时间线说明",
    },
    "scene_outline": {
        "type": "string",
        "required": False,
        "description": "场景大纲",
    },
}

CHAPTER_SUMMARY_VARIABLE: dict[str, Any] = {
    "chapter_summary": {
        "type": "string",
        "required": False,
        "description": "章节摘要",
    },
}

COMMON_DEFAULT_VALUES: dict[str, Any] = {
    "target_length": "1200-1800 中文字符",
    "pov": "第三人称有限视角",
    "style": "画面感强，节奏清晰，人物行为符合设定",
    "forbidden_content": "不要输出解释，不要总结任务，不要写成大纲，不要出现与设定冲突的内容",
}


def _template(
    *,
    name: str,
    type: str,
    description: str,
    category: str,
    builtin_key: str,
    system_prompt: str,
    role_prompt: str,
    instruction_template: str,
    output_constraints: str,
    negative_prompt: str,
    extra_variables: dict[str, Any] | None = None,
    default_values: dict[str, Any] | None = None,
    recommended: bool = False,
) -> dict[str, Any]:
    """Build one builtin template dict with the shared schema and metadata."""
    variables = {**COMMON_VARIABLE_SCHEMA}
    variables.update(extra_variables or {})
    used = extract_variables(
        system_prompt,
        role_prompt,
        instruction_template,
        output_constraints,
        negative_prompt,
    )
    if "project_title" not in used:
        variables["project_title"] = {
            **variables["project_title"],
            "required": False,
        }
    return {
        "name": name,
        "type": type,
        "description": description,
        "system_prompt": system_prompt,
        "role_prompt": role_prompt,
        "instruction_template": instruction_template,
        "output_constraints": output_constraints,
        "negative_prompt": negative_prompt,
        "variables_schema": variables,
        "default_values": {**COMMON_DEFAULT_VALUES, **(default_values or {})},
        "renderer": "simple_mustache",
        "metadata": {
            "builtin": True,
            "builtin_key": builtin_key,
            "language": "zh-CN",
            "category": category,
            "recommended": recommended,
            "version": 2,
        },
    }


WRITING_SYSTEM = (
    "你是一名专业中文长篇小说作者，擅长根据世界观、人物设定、章节目标和前文信息"
    "创作连载小说正文。你需要保持人物一致性、剧情连续性和文风稳定。"
)
WRITING_ROLE = (
    "你的写作目标不是概述剧情，而是写出可以直接放入小说正文的章节内容。"
    "请关注动作、对话、心理、环境和节奏，不要只做剧情摘要。"
)
PLANNING_SYSTEM = (
    "你是一名资深中文网文策划编辑，擅长小说大纲、人物设定、世界观设定与伏笔设计。"
    "你的输出要具体、可执行，并能直接服务于后续正文创作。"
)
PLANNING_ROLE = "你输出的是创作规划与设定，而不是小说正文。"
EDITING_SYSTEM = (
    "你是一名严谨的小说编辑，擅长章节摘要、前情提要、一致性检查与人工修订建议。"
    "你的分析必须具体、克制，并且忠于原文。"
)
EDITING_ROLE = "你只做编辑与分析工作，不擅自改写全文，除非用户明确要求。"

DEFAULT_PROMPT_TEMPLATES: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # 一、正文生成类（writing）
    # ------------------------------------------------------------------
    _template(
        name="章节正文生成",
        type="chapter_generate",
        description="根据项目资料、章节大纲与目标生成可直接发布的章节正文。",
        category="writing",
        builtin_key="novel.chapter_generate.v2",
        recommended=True,
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "目标读者：{{target_audience}}\n"
            "目标文风：{{target_style}}\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【主要人物】\n{{characters}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【时间线】\n{{timeline}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "【上一章摘要】\n{{previous_chapter_summary}}\n\n"
            "【当前章节】\n"
            "章节标题：{{chapter_title}}\n"
            "章节大纲：{{chapter_outline}}\n"
            "章节目标：{{current_chapter_goal}}\n\n"
            "【本次写作要求】\n"
            "叙事视角：{{pov}}\n"
            "目标长度：{{target_length}}\n"
            "风格要求：{{style}}\n"
            "用户补充要求：{{user_instruction}}\n\n"
            "请根据以上信息创作当前章节正文。"
        ),
        output_constraints=(
            "输出要求：\n"
            "1. 只输出小说正文，不要输出解释。\n"
            "2. 不要写成大纲。\n"
            "3. 不要使用“本章主要讲述”等总结性句子。\n"
            "4. 保持人物行为、语气、动机与人物设定一致。\n"
            "5. 保持世界观规则一致。\n"
            "6. 有明确场景推进，避免空泛抒情。\n"
            "7. 对话、动作、心理、环境描写需要自然融合。\n"
            "8. 如果信息不足，优先保持克制，不要编造重大设定。"
        ),
        negative_prompt=(
            "不要输出分析过程。\n"
            "不要输出写作建议。\n"
            "不要直接复述设定。\n"
            "不要突然引入未铺垫的重要人物或设定。\n"
            "不要让人物做出与性格和目标明显冲突的行为。\n"
            "不要跳过当前章节目标。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节续写",
        type="chapter_continue",
        description="从已有草稿结尾自然续写，不重复已有内容。",
        category="writing",
        builtin_key="novel.chapter_continue.v2",
        recommended=True,
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "目标文风：{{target_style}}\n\n"
            "【世界观与设定】\n{{world_setting}}\n\n"
            "【主要人物】\n{{characters}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "【上一章摘要】\n{{previous_chapter_summary}}\n\n"
            "【当前章节标题】\n{{chapter_title}}\n\n"
            "【当前章节大纲】\n{{chapter_outline}}\n\n"
            "【已有草稿】\n{{draft_content}}\n\n"
            "【续写目标】\n{{current_chapter_goal}}\n\n"
            "【写作要求】\n"
            "叙事视角：{{pov}}\n"
            "续写长度：{{target_length}}\n"
            "风格要求：{{style}}\n"
            "补充要求：{{user_instruction}}\n\n"
            "请从已有草稿的结尾自然续写，不要重复已有内容。"
        ),
        output_constraints=(
            "输出要求：\n"
            "1. 只输出续写部分。\n"
            "2. 不要重复已有草稿。\n"
            "3. 开头必须自然承接已有草稿最后一句。\n"
            "4. 保持人物语气和场景连续。\n"
            "5. 续写必须推动剧情，不要原地描写。\n"
            "6. 不要提前结束整章，除非用户明确要求。"
        ),
        negative_prompt=(
            "不要复述已有草稿。\n"
            "不要输出分析或计划。\n"
            "不要改变已有的人物状态和场景。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节重写",
        type="chapter_rewrite",
        description="按新要求重写章节内容，保留核心剧情。",
        category="writing",
        builtin_key="novel.chapter_rewrite.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "【原文】\n{{selected_text}}\n\n"
            "【小说设定】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "目标文风：{{target_style}}\n"
            "世界观：{{world_setting}}\n"
            "人物：{{characters}}\n\n"
            "【重写目标】\n{{user_instruction}}\n\n"
            "【要求】\n"
            "1. 保留原文核心剧情信息。\n"
            "2. 改善语言表现、节奏、人物动作和情绪层次。\n"
            "3. 如原文存在逻辑不顺，请自然修复。\n"
            "4. 不要改变重大剧情结果，除非用户明确要求。\n"
            "5. 目标长度：{{target_length}}\n\n"
            "请输出重写后的正文。"
        ),
        output_constraints=(
            "只输出重写后的正文。\n"
            "不要解释修改点。\n"
            "不要输出对比。\n"
            "不要输出列表。"
        ),
        negative_prompt=(
            "不要保留原文的啰嗦与重复。\n"
            "不要新增与设定冲突的内容。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节润色",
        type="chapter_polish",
        description="优化语言与画面感，保持原剧情不变。",
        category="writing",
        builtin_key="novel.chapter_polish.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请润色以下小说正文，使语言更自然、更有画面感，并保持原剧情不变。\n\n"
            "【原文】\n{{selected_text}}\n\n"
            "【目标文风】\n{{target_style}}\n\n"
            "【人物设定】\n{{characters}}\n\n"
            "【润色要求】\n{{user_instruction}}\n\n"
            "请输出润色后的正文。"
        ),
        output_constraints=(
            "1. 不改变剧情走向。\n"
            "2. 不改变人物关系。\n"
            "3. 不新增重大设定。\n"
            "4. 可以优化句式、动作、心理、环境描写。\n"
            "5. 删除明显重复和空泛表达。\n"
            "6. 只输出润色后的正文。"
        ),
        negative_prompt=(
            "不要改写剧情结果。\n"
            "不要加入原文没有的设定。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节扩写",
        type="chapter_expand",
        description="扩写小说片段，使场景更完整、冲突更清晰。",
        category="writing",
        builtin_key="novel.chapter_expand.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请扩写以下小说片段，使场景更完整、冲突更清晰、人物反应更具体。\n\n"
            "【原片段】\n{{selected_text}}\n\n"
            "【小说设定】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "世界观：{{world_setting}}\n"
            "人物：{{characters}}\n\n"
            "【扩写方向】\n{{user_instruction}}\n\n"
            "【目标长度】\n{{target_length}}\n\n"
            "请输出扩写后的正文。"
        ),
        output_constraints=(
            "1. 保留原片段核心事件。\n"
            "2. 增加动作、对话、心理、环境细节。\n"
            "3. 不要加入破坏后续剧情的大设定。\n"
            "4. 不要把片段扩成大纲。\n"
            "5. 只输出扩写正文。"
        ),
        negative_prompt=(
            "不要重复原片段。\n"
            "不要堆砌形容词。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节压缩",
        type="custom",
        description="压缩章节正文，保留核心剧情与关键信息，仍保持正文形式。",
        category="writing",
        builtin_key="novel.chapter_compress.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请压缩以下小说正文，保留核心剧情、关键人物动作、重要信息和必要情绪。\n\n"
            "【原文】\n{{selected_text}}\n\n"
            "【压缩目标】\n{{target_length}}\n\n"
            "【保留重点】\n{{user_instruction}}\n\n"
            "请输出压缩后的正文。"
        ),
        output_constraints=(
            "1. 保留核心剧情。\n"
            "2. 保留关键设定。\n"
            "3. 删除重复、空泛、拖慢节奏的内容。\n"
            "4. 不要写成摘要，仍然保持小说正文形式。\n"
            "5. 只输出压缩后的正文。"
        ),
        negative_prompt=(
            "不要输出摘要或大纲。\n"
            "不要删除影响后续剧情的信息。\n"
            "{{forbidden_content}}"
        ),
        default_values={"target_length": "600-800 中文字符"},
    ),
    _template(
        name="场景扩写",
        type="scene_expand",
        description="根据场景大纲扩写成完整小说正文。",
        category="writing",
        builtin_key="novel.scene_expand.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请根据场景大纲扩写成小说正文。\n\n"
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "目标文风：{{target_style}}\n\n"
            "【场景信息】\n"
            "场景标题：{{scene_title}}\n"
            "场景地点：{{scene_location}}\n"
            "场景时间线：{{scene_timeline_note}}\n"
            "场景大纲：{{scene_outline}}\n\n"
            "【人物】\n{{characters}}\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "【场景目标】\n{{current_chapter_goal}}\n\n"
            "【写作要求】\n"
            "叙事视角：{{pov}}\n"
            "目标长度：{{target_length}}\n"
            "补充要求：{{user_instruction}}\n\n"
            "请输出该场景的小说正文。"
        ),
        output_constraints=(
            "1. 只输出该场景的正文。\n"
            "2. 场景要有明确起止与推进。\n"
            "3. 保持人物与世界观一致。\n"
            "4. 不要写成大纲。"
        ),
        negative_prompt=(
            "不要输出场景总结。\n"
            "不要跳过场景关键事件。\n"
            "{{forbidden_content}}"
        ),
        extra_variables=SCENE_VARIABLES,
    ),
    _template(
        name="动作戏生成",
        type="custom",
        description="创作动作戏，动作清晰、空间明确、节奏紧凑。",
        category="writing",
        builtin_key="novel.action_scene.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请创作一段动作戏，要求动作清晰、空间关系明确、节奏紧凑。\n\n"
            "【小说设定】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "世界观：{{world_setting}}\n\n"
            "【人物】\n{{characters}}\n\n"
            "【当前场景】\n{{scene_outline}}\n\n"
            "【动作戏目标】\n{{current_chapter_goal}}\n\n"
            "【限制】\n{{forbidden_content}}\n\n"
            "【要求】\n"
            "1. 写清楚人物位置、动作先后、攻防变化。\n"
            "2. 不要只写招式名称，要写动作结果。\n"
            "3. 动作中穿插心理和环境变化。\n"
            "4. 保持能力体系与世界观一致。\n"
            "5. 目标长度：{{target_length}}\n\n"
            "请输出动作戏正文。"
        ),
        output_constraints=(
            "1. 动作逻辑清晰，攻防有因果。\n"
            "2. 空间位置一致，不出现突然瞬移。\n"
            "3. 人物受伤、消耗与结果要符合能力体系。\n"
            "4. 只输出动作戏正文。"
        ),
        negative_prompt=(
            "不要罗列招式名称。\n"
            "不要凭空增强或削弱人物。\n"
            "{{forbidden_content}}"
        ),
        extra_variables=SCENE_VARIABLES,
    ),
    _template(
        name="情绪戏生成",
        type="custom",
        description="创作情绪戏，表现内心变化与关系张力。",
        category="writing",
        builtin_key="novel.emotional_scene.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请创作一段情绪戏，重点表现人物内心变化、关系张力和未说出口的信息。\n\n"
            "【人物】\n{{characters}}\n\n"
            "【前情】\n{{previous_chapter_summary}}\n\n"
            "【场景】\n{{scene_outline}}\n\n"
            "【情绪目标】\n{{current_chapter_goal}}\n\n"
            "【目标文风】\n{{target_style}}\n\n"
            "【要求】\n"
            "1. 情绪变化要有层次。\n"
            "2. 不要直接喊出人物感受，要通过动作、停顿、对话和细节表现。\n"
            "3. 对话要符合人物性格。\n"
            "4. 避免煽情过度。\n"
            "5. 目标长度：{{target_length}}\n\n"
            "请输出小说正文。"
        ),
        output_constraints=(
            "1. 情绪要有推进过程。\n"
            "2. 人物行为与情绪一致。\n"
            "3. 留白比直白更有效。\n"
            "4. 只输出小说正文。"
        ),
        negative_prompt=(
            "不要直接宣告人物心情。\n"
            "不要过度煽情。\n"
            "不要用排比堆情绪。\n"
            "{{forbidden_content}}"
        ),
        extra_variables=SCENE_VARIABLES,
    ),
    _template(
        name="悬念戏生成",
        type="custom",
        description="创作悬念戏，逐步释放信息并保留钩子。",
        category="writing",
        builtin_key="novel.suspense_scene.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请创作一段悬念戏，逐步释放信息，让读者产生继续阅读的欲望。\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【人物】\n{{characters}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "【场景大纲】\n{{scene_outline}}\n\n"
            "【悬念目标】\n{{current_chapter_goal}}\n\n"
            "【要求】\n"
            "1. 先制造异常，再逐步扩大不安。\n"
            "2. 不要过早揭开谜底。\n"
            "3. 每一段都要推进信息。\n"
            "4. 结尾保留一个明确钩子。\n"
            "5. 目标长度：{{target_length}}\n\n"
            "请输出悬念戏正文。"
        ),
        output_constraints=(
            "1. 信息释放有节奏，不能一次倒完。\n"
            "2. 细节要有误导与双关。\n"
            "3. 结尾必须留下继续阅读的理由。\n"
            "4. 只输出小说正文。"
        ),
        negative_prompt=(
            "不要提前揭底。\n"
            "不要让角色突然全知。\n"
            "{{forbidden_content}}"
        ),
        extra_variables=SCENE_VARIABLES,
    ),
    _template(
        name="对白增强",
        type="dialogue_enhance",
        description="强化人物对白，使声音鲜明、冲突清楚。",
        category="writing",
        builtin_key="novel.dialogue_enhance.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请增强以下小说片段中的对白，使人物声音更鲜明，冲突更清楚。\n\n"
            "【原文】\n{{selected_text}}\n\n"
            "【人物设定】\n{{characters}}\n\n"
            "【场景目标】\n{{current_chapter_goal}}\n\n"
            "【要求】\n"
            "1. 每个人说话方式要符合其性格、身份和目的。\n"
            "2. 对白不能只是解释信息。\n"
            "3. 对白中要有试探、回避、压迫或情绪变化。\n"
            "4. 必要时加入少量动作和停顿。\n"
            "5. 不改变核心剧情结果。\n\n"
            "请输出增强后的正文。"
        ),
        output_constraints=(
            "1. 保留原剧情走向。\n"
            "2. 对白符合人物性格。\n"
            "3. 只输出增强后的正文。"
        ),
        negative_prompt=(
            "不要让所有人物用同一口吻说话。\n"
            "不要用对白直接复述设定。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="冲突升级",
        type="custom",
        description="升级场景冲突，增加压力与代价，保持逻辑自然。",
        category="writing",
        builtin_key="novel.conflict_escalation.v2",
        system_prompt=WRITING_SYSTEM,
        role_prompt=WRITING_ROLE,
        instruction_template=(
            "请将以下场景的冲突升级，让人物目标更对立，压力更强，但不要破坏后续剧情。\n\n"
            "【原文或场景】\n{{selected_text}}\n\n"
            "【人物】\n{{characters}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【当前目标】\n{{current_chapter_goal}}\n\n"
            "【限制】\n{{forbidden_content}}\n\n"
            "【要求】\n"
            "1. 明确冲突双方的目标。\n"
            "2. 增加代价、时间压力或信息差。\n"
            "3. 让人物做出选择，而不是只说情绪。\n"
            "4. 保持逻辑自然。\n"
            "5. 只输出修改后的正文。"
        ),
        output_constraints=(
            "1. 冲突有明确的升级阶梯。\n"
            "2. 代价要可感知。\n"
            "3. 人物选择推动剧情。\n"
            "4. 只输出修改后的正文。"
        ),
        negative_prompt=(
            "不要让人物突然降智。\n"
            "不要无代价地化解冲突。\n"
            "{{forbidden_content}}"
        ),
    ),
    # ------------------------------------------------------------------
    # 二、规划设定类（planning）
    # ------------------------------------------------------------------
    _template(
        name="小说总大纲生成",
        type="outline_generate",
        description="生成小说总大纲：卖点、主线、结构、反转与结局方向。",
        category="planning",
        builtin_key="novel.outline_global.v2",
        recommended=True,
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请为以下小说生成总大纲。\n\n"
            "【小说标题】\n{{project_title}}\n\n"
            "【类型】\n{{genre}}\n\n"
            "【目标读者】\n{{target_audience}}\n\n"
            "【目标风格】\n{{target_style}}\n\n"
            "【核心设定】\n{{world_setting}}\n\n"
            "【主角 / 主要人物】\n{{characters}}\n\n"
            "【用户构想】\n{{user_instruction}}\n\n"
            "请生成：\n"
            "1. 故事核心卖点；\n"
            "2. 主线目标；\n"
            "3. 主要矛盾；\n"
            "4. 三幕式或多卷结构；\n"
            "5. 主要人物成长线；\n"
            "6. 关键反转；\n"
            "7. 结局方向；\n"
            "8. 前 10 章推进建议。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "不要直接写正文。\n"
            "不要空泛，要具体到事件和冲突。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要只给抽象概念。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="分卷大纲生成",
        type="outline_generate",
        description="生成分卷大纲：卷名、矛盾、高潮与结尾钩子。",
        category="planning",
        builtin_key="novel.outline_volume.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请为小说生成分卷大纲。\n\n"
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "目标文风：{{target_style}}\n\n"
            "【总设定】\n{{world_setting}}\n\n"
            "【主要人物】\n{{characters}}\n\n"
            "【当前剧情线】\n{{plot_threads}}\n\n"
            "【用户要求】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 每一卷卷名；\n"
            "2. 每卷核心矛盾；\n"
            "3. 每卷主角目标；\n"
            "4. 每卷关键人物变化；\n"
            "5. 每卷高潮事件；\n"
            "6. 每卷结尾钩子。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "每卷信息要具体到事件。\n"
            "不要直接写正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要遗漏卷与卷之间的承接。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="章节大纲生成",
        type="outline_generate",
        description="根据前情与目标生成章节大纲，含节点、冲突与钩子。",
        category="planning",
        builtin_key="novel.outline_chapter.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请根据以下信息生成章节大纲。\n\n"
            "【小说标题】\n{{project_title}}\n\n"
            "【前情提要】\n{{previous_chapter_summary}}\n\n"
            "【人物】\n{{characters}}\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【当前章节目标】\n{{current_chapter_goal}}\n\n"
            "【要求】\n"
            "1. 给出章节标题建议。\n"
            "2. 按 5～8 个剧情节点列出推进。\n"
            "3. 标明本章冲突。\n"
            "4. 标明本章结尾钩子。\n"
            "5. 标明需要埋下或回收的伏笔。"
        ),
        output_constraints=(
            "输出为 Markdown。\n"
            "不要直接写正文。\n"
            "剧情节点必须具体。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要给出空泛的“推进剧情”式节点。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="人物小传生成",
        type="character_generate",
        description="生成人物小传：身份、欲望、弱点、说话风格与成长线。",
        category="planning",
        builtin_key="novel.character_profile.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请生成小说人物小传。\n\n"
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n"
            "世界观：{{world_setting}}\n\n"
            "【人物要求】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 姓名；\n"
            "2. 身份；\n"
            "3. 外貌特征；\n"
            "4. 性格关键词；\n"
            "5. 核心欲望；\n"
            "6. 恐惧或弱点；\n"
            "7. 说话风格；\n"
            "8. 与主角关系；\n"
            "9. 成长线；\n"
            "10. 可用剧情功能；\n"
            "11. 禁忌写法。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "欲望与弱点必须具体。\n"
            "不要写正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要给出标签式性格。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="人物关系生成",
        type="character_generate",
        description="设计人物关系网：核心关系、利益冲突与隐藏关系。",
        category="planning",
        builtin_key="novel.character_relationships.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请根据已有角色设计人物关系网。\n\n"
            "【人物资料】\n{{characters}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【用户要求】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 核心关系；\n"
            "2. 利益冲突；\n"
            "3. 情感张力；\n"
            "4. 隐藏关系；\n"
            "5. 可发展的关系变化；\n"
            "6. 每组关系适合触发的剧情事件。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "关系必须有剧情用途。\n"
            "不要写正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要让关系停留在标签上。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="世界观设定生成",
        type="world_entry_generate",
        description="生成世界观设定：规则、体系、势力与可推动剧情的矛盾。",
        category="planning",
        builtin_key="novel.worldbuilding.v2",
        recommended=True,
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请生成小说世界观设定。\n\n"
            "【小说标题】\n{{project_title}}\n\n"
            "【类型】\n{{genre}}\n\n"
            "【目标文风】\n{{target_style}}\n\n"
            "【已有设定】\n{{world_setting}}\n\n"
            "【用户构想】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 世界基本规则；\n"
            "2. 力量体系或社会体系；\n"
            "3. 地理与势力；\n"
            "4. 资源与代价；\n"
            "5. 禁忌与风险；\n"
            "6. 普通人的生活状态；\n"
            "7. 可推动剧情的矛盾；\n"
            "8. 容易产生冲突的规则。"
        ),
        output_constraints=(
            "输出为结构化设定。\n"
            "不要写正文。\n"
            "规则要能服务剧情。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要堆砌无代价的设定。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="势力 / 组织设定生成",
        type="world_entry_generate",
        description="设计势力或组织：目标、结构、资源、矛盾与反转可能。",
        category="planning",
        builtin_key="novel.faction_design.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请设计小说中的势力或组织。\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【剧情需要】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 势力名称；\n"
            "2. 表面目标；\n"
            "3. 真实目标；\n"
            "4. 组织结构；\n"
            "5. 关键人物；\n"
            "6. 资源优势；\n"
            "7. 内部矛盾；\n"
            "8. 与主角的关系；\n"
            "9. 可触发的剧情冲突；\n"
            "10. 后续反转可能。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "表面目标与真实目标必须不同。\n"
            "不要写正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要让势力只有名字没有结构。\n"
            "{{forbidden_content}}"
        ),
    ),
    _template(
        name="伏笔设计",
        type="custom",
        description="为当前剧情设计伏笔：出现方式、真实含义与回收建议。",
        category="planning",
        builtin_key="novel.foreshadowing_design.v2",
        system_prompt=PLANNING_SYSTEM,
        role_prompt=PLANNING_ROLE,
        instruction_template=(
            "请为当前剧情设计伏笔。\n\n"
            "【小说信息】\n"
            "标题：{{project_title}}\n"
            "类型：{{genre}}\n\n"
            "【已有剧情线】\n{{plot_threads}}\n\n"
            "【时间线】\n{{timeline}}\n\n"
            "【当前章节目标】\n{{current_chapter_goal}}\n\n"
            "【用户要求】\n{{user_instruction}}\n\n"
            "请输出：\n"
            "1. 伏笔名称；\n"
            "2. 第一次出现方式；\n"
            "3. 表面含义；\n"
            "4. 真实含义；\n"
            "5. 回收章节建议；\n"
            "6. 回收方式；\n"
            "7. 读者误导方向；\n"
            "8. 不能提前暴露的信息。"
        ),
        output_constraints=(
            "输出为结构化 Markdown。\n"
            "伏笔要自然、可回收。\n"
            "不要写正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要让伏笔过于明显或过于生硬。\n"
            "{{forbidden_content}}"
        ),
    ),
    # ------------------------------------------------------------------
    # 三、辅助编辑类（editing）
    # ------------------------------------------------------------------
    _template(
        name="章节摘要生成",
        type="summary_generate",
        description="生成章节摘要：事件、人物变化、伏笔与未解决问题。",
        category="editing",
        builtin_key="novel.summary_chapter.v2",
        recommended=True,
        system_prompt=EDITING_SYSTEM,
        role_prompt=EDITING_ROLE,
        instruction_template=(
            "请为以下小说章节生成摘要。\n\n"
            "【章节正文】\n{{selected_text}}\n\n"
            "请保留：\n"
            "1. 关键事件；\n"
            "2. 人物关系变化；\n"
            "3. 新增设定；\n"
            "4. 伏笔；\n"
            "5. 未解决问题；\n"
            "6. 下一章需要记住的信息。\n\n"
            "请输出：\n"
            "- 简短摘要；\n"
            "- 详细摘要；\n"
            "- 人物变化；\n"
            "- 新增设定；\n"
            "- 伏笔与未解决问题。"
        ),
        output_constraints=(
            "不要评价文本质量。\n"
            "不要扩写。\n"
            "不要加入原文没有的信息。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要加入主观评价。\n"
            "{{forbidden_content}}"
        ),
        default_values={"target_length": "200-400 中文字符"},
    ),
    _template(
        name="前情提要生成",
        type="summary_generate",
        description="生成简洁的前情提要，供续写 Prompt 使用。",
        category="editing",
        builtin_key="novel.recap_previous.v2",
        system_prompt=EDITING_SYSTEM,
        role_prompt=EDITING_ROLE,
        instruction_template=(
            "请根据以下前文信息生成适合放入 Prompt 的前情提要。\n\n"
            "【前文摘要】\n{{previous_chapter_summary}}\n\n"
            "【时间线】\n{{timeline}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "【当前章节目标】\n{{current_chapter_goal}}\n\n"
            "请输出一段简洁、可直接提供给模型续写使用的前情提要。"
        ),
        output_constraints=(
            "1. 控制在 300～600 中文字符。\n"
            "2. 只保留对当前章节有用的信息。\n"
            "3. 不要加入评价。\n"
            "4. 不要写成小说正文。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要复述完整章节。\n"
            "{{forbidden_content}}"
        ),
        default_values={"target_length": "300-600 中文字符"},
    ),
    _template(
        name="一致性检查提示词",
        type="custom",
        description="检查文本与人物、世界观、时间线和剧情线的一致性。",
        category="editing",
        builtin_key="novel.consistency_check.v2",
        system_prompt=EDITING_SYSTEM,
        role_prompt=EDITING_ROLE,
        instruction_template=(
            "请检查以下小说文本是否与设定一致。\n\n"
            "【待检查文本】\n{{selected_text}}\n\n"
            "【人物设定】\n{{characters}}\n\n"
            "【世界观】\n{{world_setting}}\n\n"
            "【剧情线】\n{{plot_threads}}\n\n"
            "【时间线】\n{{timeline}}\n\n"
            "【相关记忆】\n{{retrieved_memory}}\n\n"
            "请检查：\n"
            "1. 人物行为是否一致；\n"
            "2. 人物说话风格是否一致；\n"
            "3. 世界观规则是否冲突；\n"
            "4. 时间线是否冲突；\n"
            "5. 剧情是否偏离目标；\n"
            "6. 是否出现未铺垫的重要设定；\n"
            "7. 是否存在明显重复。"
        ),
        output_constraints=(
            "输出 Markdown：\n"
            "## 总体判断\n"
            "## 问题列表\n"
            "## 证据片段\n"
            "## 修改建议\n\n"
            "不要直接重写全文，除非用户要求。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要无中生有地挑错。\n"
            "{{forbidden_content}}"
        ),
        extra_variables={
            "selected_text": {
                "type": "string",
                "required": True,
                "description": "待检查的小说文本",
            },
        },
    ),
    _template(
        name="人工修订建议",
        type="custom",
        description="作为编辑分析文本，给出具体可执行的人工修订建议。",
        category="editing",
        builtin_key="novel.revision_suggestions.v2",
        system_prompt=EDITING_SYSTEM,
        role_prompt=EDITING_ROLE,
        instruction_template=(
            "请作为小说编辑，对以下文本提出人工修订建议。\n\n"
            "【文本】\n{{selected_text}}\n\n"
            "【目标文风】\n{{target_style}}\n\n"
            "【人物设定】\n{{characters}}\n\n"
            "【章节目标】\n{{current_chapter_goal}}\n\n"
            "请从以下角度分析：\n"
            "1. 语言是否啰嗦；\n"
            "2. 情绪是否到位；\n"
            "3. 人物是否立住；\n"
            "4. 冲突是否清晰；\n"
            "5. 节奏是否拖沓；\n"
            "6. 是否需要增加细节；\n"
            "7. 是否需要删除重复；\n"
            "8. 是否适合作为训练样本。"
        ),
        output_constraints=(
            "输出 Markdown。\n"
            "不要直接改写全文。\n"
            "每条建议必须具体。\n"
            "如果适合作为训练样本，请说明原因。"
        ),
        negative_prompt=(
            "不要输出正文。\n"
            "不要给出“整体不错”式的空泛评价。\n"
            "{{forbidden_content}}"
        ),
    ),
]


_CONTENT_FIELDS = (
    "system_prompt",
    "role_prompt",
    "instruction_template",
    "output_constraints",
    "negative_prompt",
    "variables_schema",
    "default_values",
    "renderer",
)


def builtin_content_hash(template: dict[str, Any]) -> str:
    """Canonical hash of the content fields of a builtin template."""
    payload = {field: template.get(field) for field in _CONTENT_FIELDS}
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ensure_default_prompt_templates(service) -> dict[str, Any]:
    """Install or upgrade builtin templates without touching user edits.

    Returns a summary with installed / skipped / upgraded / user_modified
    counts plus the list of builtin keys.
    """
    summary: dict[str, Any] = {
        "installed_count": 0,
        "skipped_count": 0,
        "upgraded_count": 0,
        "user_modified_count": 0,
        "template_keys": [],
    }
    existing = service.list_templates(scope="global", limit=200)
    by_key: dict[str, dict[str, Any]] = {}
    for item in existing:
        meta = item.get("metadata") or {}
        key = meta.get("builtin_key")
        if isinstance(key, str) and key:
            by_key.setdefault(key, item)

    for template in DEFAULT_PROMPT_TEMPLATES:
        metadata = template["metadata"]
        key = metadata["builtin_key"]
        summary["template_keys"].append(key)
        current = by_key.get(key)

        if current is None:
            service.create_template(
                {
                    **template,
                    "metadata": {
                        **metadata,
                        "content_hash": builtin_content_hash(template),
                    },
                    "scope": "global",
                    "change_note": f"Default template {key}",
                }
            )
            summary["installed_count"] += 1
            continue

        current_meta = current.get("metadata") or {}
        detail = service.get_template(current["id"])
        active = detail.get("active_version")
        if current_meta.get("builtin") is not True or active is None:
            summary["user_modified_count"] += 1
            continue

        stored_hash = current_meta.get("content_hash")
        active_hash = builtin_content_hash(active)
        if not isinstance(stored_hash, str) or stored_hash != active_hash:
            # The active content no longer matches what we installed.
            summary["user_modified_count"] += 1
            continue

        new_hash = builtin_content_hash(template)
        if active_hash == new_hash:
            summary["skipped_count"] += 1
            continue

        # Pristine builtin template with older content -> upgrade in place.
        service.create_version(
            current["id"],
            {
                "system_prompt": template.get("system_prompt"),
                "role_prompt": template.get("role_prompt"),
                "instruction_template": template["instruction_template"],
                "negative_prompt": template.get("negative_prompt"),
                "output_constraints": template.get("output_constraints"),
                "variables_schema": template.get("variables_schema") or {},
                "default_values": template.get("default_values") or {},
                "renderer": template.get("renderer", "simple_mustache"),
                "change_note": f"Upgrade default template to {key}",
            },
        )
        service.update_template_metadata(
            current["id"],
            {
                "metadata": {
                    **metadata,
                    "content_hash": new_hash,
                }
            },
        )
        summary["upgraded_count"] += 1

    return summary
