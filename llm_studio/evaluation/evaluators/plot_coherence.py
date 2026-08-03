"""Plot coherence heuristics."""

from __future__ import annotations

import re

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


def _terms(text: str) -> set[str]:
    return {item for item in re.split(r"[^\u4e00-\u9fffA-Za-z0-9_]+", text) if len(item) >= 2}


class PlotCoherenceEvaluator:
    evaluator_type = "plot_coherence"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        chapter = input.references.get("chapter") or {}
        goal = str(input.context.get("current_chapter_goal") or chapter.get("summary") or "")
        outline = str(chapter.get("outline") or chapter.get("summary") or "")
        goal_terms = _terms(goal)
        text_terms = _terms(input.text)
        coverage = len(goal_terms & text_terms) / max(1, len(goal_terms)) if goal_terms else 1.0
        open_threads = [
            item
            for item in input.references.get("plot_threads") or []
            if str(item.get("status") or "open") in {"open", "active", "draft"}
        ]
        thread_conflicts = [
            item.get("title")
            for item in open_threads
            if item.get("title") and item.get("title") in input.text and "解决" in input.text
        ]
        outline_terms = _terms(outline)
        outline_deviation = 0 if not outline_terms or (outline_terms & text_terms) else 1
        score = 5.0 - (1.0 - coverage) * 2.0 - outline_deviation * 0.8 - len(thread_conflicts) * 0.2
        findings: list[EvaluationFindingDraft] = []
        if coverage < 0.35 and goal_terms:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "plot",
                    "章节目标覆盖不足",
                    "正文与 current_chapter_goal / chapter summary 的关键词重合较低。",
                    {"goal": goal, "coverage": round(coverage, 4)},
                    "人工核对章节是否偏离预期目标，必要时调整正文或目标。",
                )
            )
        if outline_deviation:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "plot",
                    "可能偏离章节大纲",
                    "正文与章节 outline/summary 没有明显关键词交集。",
                    {"outline": outline[:300]},
                    "人工确认这是有意转折还是生成偏移。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("plot_coherence_score", round(max(1.0, score), 2), "score"),
                EvaluationMetricDraft("chapter_goal_coverage", round(coverage, 4), "ratio"),
                EvaluationMetricDraft("outline_deviation_count", float(outline_deviation), "count"),
                EvaluationMetricDraft("open_thread_conflict_count", float(len(thread_conflicts)), "count"),
            ],
            findings=findings,
            summary="剧情连贯性启发式评估完成。",
        )

