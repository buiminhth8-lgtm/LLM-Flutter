"""Pacing heuristics."""

from __future__ import annotations

import re

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult

ACTION_TERMS = ("走", "冲", "退", "抓", "拔", "推", "砍", "躲", "追", "停", "转身", "抬手")
DESCRIPTION_TERMS = ("仿佛", "像", "颜色", "气味", "声音", "阴影", "光", "风", "夜色", "沉默")


class PacingEvaluator:
    evaluator_type = "pacing"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        text = input.text.strip()
        paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
        dialogue_chars = sum(len(match.group(0)) for match in re.finditer(r"[“\"].+?[”\"]", text))
        dialogue_ratio = dialogue_chars / max(1, len(text))
        action_hits = sum(text.count(term) for term in ACTION_TERMS)
        description_hits = sum(text.count(term) for term in DESCRIPTION_TERMS)
        total_hits = max(1, action_hits + description_hits)
        action_ratio = action_hits / total_hits
        description_ratio = description_hits / total_hits if total_hits else 0.0
        long_paragraphs = [part for part in paragraphs if len(part) >= 280]
        low_progress = action_ratio < 0.18 and len(text) >= 500
        score = 5.0
        if long_paragraphs:
            score -= min(1.5, len(long_paragraphs) * 0.3)
        if low_progress:
            score -= 1.0
        if dialogue_ratio > 0.75 or dialogue_ratio < 0.03:
            score -= 0.4
        findings: list[EvaluationFindingDraft] = []
        if long_paragraphs:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "pacing",
                    "存在较长段落",
                    "长段落可能降低阅读节奏，建议人工判断是否需要拆分。",
                    {"long_paragraph_count": len(long_paragraphs), "samples": [p[:120] for p in long_paragraphs[:3]]},
                    "拆分说明性段落，或加入行动/对白调节节奏。",
                )
            )
        if low_progress:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "pacing",
                    "剧情推进信号偏弱",
                    "动作推进词占比较低，文本可能偏说明或静态描写。",
                    {"action_ratio": round(action_ratio, 4), "description_ratio": round(description_ratio, 4)},
                    "人工核对本章是否需要更多行动、冲突或目标推进。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("pacing_score", round(max(1.0, score), 2), "score"),
                EvaluationMetricDraft("dialogue_ratio", round(dialogue_ratio, 4), "ratio"),
                EvaluationMetricDraft("description_ratio", round(description_ratio, 4), "ratio"),
                EvaluationMetricDraft("action_ratio", round(action_ratio, 4), "ratio"),
                EvaluationMetricDraft("long_paragraph_count", float(len(long_paragraphs)), "count"),
                EvaluationMetricDraft("low_progress_warning", 1.0 if low_progress else 0.0, "bool"),
            ],
            findings=findings,
            summary="节奏启发式评估完成。",
        )

