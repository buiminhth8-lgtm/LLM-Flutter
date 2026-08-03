"""Repetition heuristics."""

from __future__ import annotations

import re
from collections import Counter

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"[。！？!?；;\n]+", text) if item.strip()]


def _paragraphs(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"\n{2,}", text) if item.strip()]


class RepetitionEvaluator:
    evaluator_type = "repetition"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        sentences = _sentences(input.text)
        paragraphs = _paragraphs(input.text)
        sentence_counts = Counter(sentences)
        paragraph_counts = Counter(paragraphs)
        duplicate_sentences = {k: v for k, v in sentence_counts.items() if v > 1}
        duplicate_paragraphs = {k: v for k, v in paragraph_counts.items() if v > 1}
        repeated_sentence_total = sum(v - 1 for v in duplicate_sentences.values())
        repetition_ratio = repeated_sentence_total / max(1, len(sentences))
        distinct_ratio = len(sentence_counts) / max(1, len(sentences))
        phrase_counts = Counter(
            input.text[i : i + 4]
            for i in range(max(0, len(input.text) - 3))
            if input.text[i : i + 4].strip()
        )
        top_phrases = [
            {"phrase": phrase, "count": count}
            for phrase, count in phrase_counts.most_common(10)
            if count >= 4 and not phrase.isspace()
        ][:5]
        score = max(1.0, min(5.0, 5.0 - repetition_ratio * 8.0 - len(top_phrases) * 0.2))
        metrics = [
            EvaluationMetricDraft("repetition_ratio", round(repetition_ratio, 4), "ratio"),
            EvaluationMetricDraft("distinct_sentence_ratio", round(distinct_ratio, 4), "ratio"),
            EvaluationMetricDraft("duplicate_sentence_count", float(len(duplicate_sentences)), "count"),
            EvaluationMetricDraft("duplicate_paragraph_count", float(len(duplicate_paragraphs)), "count"),
            EvaluationMetricDraft(
                "top_repeated_phrases",
                float(len(top_phrases)),
                "count",
                {"phrases": top_phrases},
            ),
            EvaluationMetricDraft("repetition_score", round(score, 2), "score"),
        ]
        findings: list[EvaluationFindingDraft] = []
        if duplicate_sentences:
            sample = [
                {"text": text[:120], "count": count}
                for text, count in list(duplicate_sentences.items())[:5]
            ]
            findings.append(
                EvaluationFindingDraft(
                    severity="warning" if repetition_ratio < 0.25 else "error",
                    category="repetition",
                    title="同一句式或句子重复出现",
                    message="文本中存在重复句子，建议人工判断是否需要压缩或替换表达。",
                    evidence={"duplicates": sample},
                    suggestion="检查重复片段是否承担节奏功能；若不是，请改写或删减。",
                )
            )
        if top_phrases:
            findings.append(
                EvaluationFindingDraft(
                    severity="info",
                    category="repetition",
                    title="存在高频重复短语",
                    message="检测到多个高频 4 字短语，可能造成语言机械感。",
                    evidence={"phrases": top_phrases},
                    suggestion="优先检查动作描写和口头禅是否过度重复。",
                )
            )
        return EvaluationResult(metrics=metrics, findings=findings, summary="重复率启发式评估完成。")

