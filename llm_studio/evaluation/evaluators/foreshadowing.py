"""Foreshadowing tracking heuristics."""

from __future__ import annotations

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


class ForeshadowingEvaluator:
    evaluator_type = "foreshadowing"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        items = []
        for entry in input.references.get("world_entries") or []:
            if str(entry.get("category") or "").lower() == "foreshadowing":
                items.append({"source": "world_entry", "title": entry.get("title"), "content": entry.get("content")})
        for thread in input.references.get("plot_threads") or []:
            title = str(thread.get("title") or "")
            desc = str(thread.get("description") or "")
            if "伏笔" in title or "伏笔" in desc or "线索" in title or "线索" in desc:
                items.append({"source": "plot_thread", "title": title, "content": desc})
        for event in input.references.get("timeline_events") or []:
            title = str(event.get("title") or "")
            desc = str(event.get("description") or "")
            if "伏笔" in title or "线索" in title or "伏笔" in desc:
                items.append({"source": "timeline_event", "title": title, "content": desc})
        for doc in input.references.get("memory_documents") or []:
            if str(doc.get("source_type") or "") == "foreshadowing":
                items.append({"source": "memory_document", "title": doc.get("title"), "content": doc.get("content")})
        unresolved = [
            item for item in items if item.get("title") and str(item["title"]) not in input.text
        ]
        score = 5.0 - min(2.0, len(unresolved) * 0.25)
        findings: list[EvaluationFindingDraft] = []
        if unresolved:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "foreshadowing",
                    "登记伏笔未在目标文本中出现",
                    "部分已登记伏笔没有在本目标文本中出现；这可能是正常的长线铺垫。",
                    {"unresolved": unresolved[:10]},
                    "人工判断本章节是否应该回收或推进这些伏笔。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("foreshadowing_score", round(max(1.0, score), 2), "score"),
                EvaluationMetricDraft("foreshadowing_registered_count", float(len(items)), "count"),
                EvaluationMetricDraft("foreshadowing_unresolved_count", float(len(unresolved)), "count"),
            ],
            findings=findings,
            summary="伏笔追踪启发式评估完成。",
        )

