"""World consistency heuristics."""

from __future__ import annotations

import re

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


class WorldConsistencyEvaluator:
    evaluator_type = "world_consistency"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        entries = list(input.references.get("world_entries") or [])
        conflicts = []
        for entry in entries:
            content = str(entry.get("content") or "")
            title = str(entry.get("title") or "")
            for match in re.finditer(r"(?:禁止|不能|无法|不允许)([\u4e00-\u9fffA-Za-z0-9_]{1,12})", content):
                term = match.group(1)
                if term and term in input.text and not re.search(rf"(?:禁止|不能|无法|不允许){re.escape(term)}", input.text):
                    conflicts.append({"title": title, "rule": match.group(0), "term": term})
        known_titles = {str(item.get("title") or "") for item in entries if item.get("title")}
        locations = set(re.findall(r"([\u4e00-\u9fff]{2,8})(?:城|宫|山|河|市|镇|院|宗)", input.text))
        unknown_locations = sorted(
            loc for loc in locations if known_titles and not any(loc in title for title in known_titles)
        )
        timeline_conflicts = 0
        score = 5.0 - min(2.0, len(conflicts) * 0.7) - min(1.0, len(unknown_locations) * 0.2)
        findings: list[EvaluationFindingDraft] = []
        if conflicts:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "world",
                    "疑似违反世界观规则",
                    "文本出现了与 world_entries 中限制性规则相冲突的表达。",
                    {"conflicts": conflicts[:10]},
                    "人工核对设定；本评估不会自动修改世界观或正文。",
                )
            )
        if unknown_locations:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "world",
                    "疑似未登记地点或组织",
                    "检测到可能的新地点/势力名称，建议核对是否需要加入世界观条目。",
                    {"unknown_locations": unknown_locations[:10]},
                    "如果是重要设定，建议人工补充世界观资料。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("world_consistency_score", round(max(1.0, score), 2), "score"),
                EvaluationMetricDraft("world_conflict_count", float(len(conflicts)), "count"),
                EvaluationMetricDraft("unknown_location_count", float(len(unknown_locations)), "count"),
                EvaluationMetricDraft("timeline_conflict_count", float(timeline_conflicts), "count"),
            ],
            findings=findings,
            summary="世界观一致性启发式评估完成。",
        )

