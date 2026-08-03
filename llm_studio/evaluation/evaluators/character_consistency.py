"""Character consistency heuristics."""

from __future__ import annotations

import re

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


class CharacterConsistencyEvaluator:
    evaluator_type = "character_consistency"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        characters = list(input.references.get("characters") or [])
        known = {str(item.get("name") or "") for item in characters if item.get("name")}
        speaker_mentions = set(re.findall(r"([\u4e00-\u9fff]{2,4})(?:说|问|喊|答|道)", input.text))
        unknown = sorted(name for name in speaker_mentions if known and name not in known)
        speech_warnings = []
        for char in characters:
            name = str(char.get("name") or "")
            style = str(char.get("speech_style") or "")
            if name and style and name in input.text:
                style_terms = [term for term in re.split(r"[,，、\s]+", style) if term]
                if style_terms and not any(term in input.text for term in style_terms):
                    speech_warnings.append({"name": name, "speech_style": style})
        relationship_conflicts = 0
        score = 5.0 - min(2.0, len(unknown) * 0.4) - min(1.0, len(speech_warnings) * 0.3)
        findings: list[EvaluationFindingDraft] = []
        if unknown:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "character",
                    "疑似未登记人物发言",
                    "检测到发言者不在当前人物卡列表中，可能是临时角色或遗漏登记。",
                    {"unknown_character_mentions": unknown[:10], "known_characters": sorted(known)},
                    "人工确认这些人物是否需要加入人物卡，或是否只是普通称谓。",
                )
            )
        if speech_warnings:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "character",
                    "人物说话风格可能未体现",
                    "部分出场人物的 speech_style 关键词未在文本中体现。",
                    {"characters": speech_warnings[:10]},
                    "人工核对对白是否符合人物卡，不自动修改人物设定。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("character_consistency_score", round(max(1.0, score), 2), "score"),
                EvaluationMetricDraft("unknown_character_mentions", float(len(unknown)), "count"),
                EvaluationMetricDraft("speech_style_warning_count", float(len(speech_warnings)), "count"),
                EvaluationMetricDraft("relationship_conflict_count", float(relationship_conflicts), "count"),
            ],
            findings=findings,
            summary="人物一致性启发式评估完成。",
        )

