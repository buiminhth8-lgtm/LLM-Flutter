"""Style consistency heuristics."""

from __future__ import annotations

import re

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult
from .repetition import _sentences


class StyleConsistencyEvaluator:
    evaluator_type = "style_consistency"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        sentences = _sentences(input.text)
        chars = sum(len(item) for item in sentences)
        avg_sentence = chars / max(1, len(sentences))
        dialogue_chars = sum(len(match.group(0)) for match in re.finditer(r"[“\"].+?[”\"]", input.text))
        dialogue_ratio = dialogue_chars / max(1, len(input.text.strip()))
        description_ratio = max(0.0, 1.0 - dialogue_ratio)
        pov_shift_count = self._pov_shifts(input.text)
        target_style = str((input.references.get("project") or {}).get("target_style") or "")
        style_terms = [term for term in re.split(r"[,，、\s]+", target_style) if term]
        missing_terms = [term for term in style_terms if term not in input.text]
        score = 5.0
        if avg_sentence > 80 or avg_sentence < 8:
            score -= 0.7
        if pov_shift_count:
            score -= min(1.5, pov_shift_count * 0.3)
        if style_terms:
            score -= min(1.5, len(missing_terms) / max(1, len(style_terms)) * 1.5)
        score = round(max(1.0, score), 2)
        findings: list[EvaluationFindingDraft] = []
        if pov_shift_count:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "style",
                    "叙述视角可能发生跳变",
                    "文本中第一/第三人称信号频繁切换，建议人工核对 POV 是否稳定。",
                    {"pov_shift_count": pov_shift_count},
                    "核对章节 POV 设定，避免无意切换叙述视角。",
                )
            )
        if missing_terms and style_terms:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "style",
                    "目标文风关键词覆盖不足",
                    "部分 project.target_style 关键词未在文本中体现。",
                    {"missing_terms": missing_terms[:10], "target_style": target_style},
                    "人工判断是否需要补强文风，而不是机械塞入关键词。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("style_score", score, "score"),
                EvaluationMetricDraft("avg_sentence_length", round(avg_sentence, 2), "chars"),
                EvaluationMetricDraft("dialogue_ratio", round(dialogue_ratio, 4), "ratio"),
                EvaluationMetricDraft("description_ratio", round(description_ratio, 4), "ratio"),
                EvaluationMetricDraft("pov_shift_count", float(pov_shift_count), "count"),
            ],
            findings=findings,
            summary="文风一致性启发式评估完成。",
        )

    @staticmethod
    def _pov_shifts(text: str) -> int:
        first = len(re.findall(r"(?<![你他她])我", text))
        third = len(re.findall(r"[他她它]们?|主角", text))
        return 1 if first >= 3 and third >= 3 else 0

