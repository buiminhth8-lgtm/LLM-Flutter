"""Evaluation report generation."""

from __future__ import annotations

from collections import Counter
from typing import Any


class EvaluationReportBuilder:
    def build(
        self,
        *,
        run: dict[str, Any],
        cases: list[dict[str, Any]],
        metrics: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        manual_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        finding_counts = {
            "severity": dict(Counter(item["severity"] for item in findings)),
            "category": dict(Counter(item["category"] for item in findings)),
            "status": dict(Counter(item["status"] for item in findings)),
        }
        metric_summary = {
            item["metric_name"]: item.get("metric_value")
            for item in metrics
            if item.get("metric_value") is not None
        }
        auto_findings = [item for item in findings if item.get("category") != "manual"]
        manual_overall = [
            item["overall_score"] for item in manual_scores if item.get("overall_score") is not None
        ]
        return {
            "run_id": run["run_id"],
            "target_type": run["target_type"],
            "target_id": run["target_id"],
            "overall_score": run.get("overall_score"),
            "status": run.get("status"),
            "automatic_evaluation": {
                "case_count": len(cases),
                "metric_summary": metric_summary,
                "finding_count": len(auto_findings),
            },
            "manual_evaluation": {
                "score_count": len(manual_scores),
                "latest_overall_score": manual_overall[0] if manual_overall else None,
            },
            "finding_counts": finding_counts,
            "top_findings": [
                {
                    "severity": item["severity"],
                    "category": item["category"],
                    "title": item["title"],
                    "message": item["message"],
                    "evidence": item.get("evidence") or {},
                    "suggestion": item.get("suggestion"),
                }
                for item in findings[:10]
            ],
            "disclaimer": "自动评估是启发式/辅助结论，不声明一定正确，也不会修改正文。",
        }

    @staticmethod
    def summary(report: dict[str, Any]) -> str:
        score = report.get("overall_score")
        counts = report.get("finding_counts", {}).get("severity", {})
        warnings = int(counts.get("warning") or 0)
        errors = int(counts.get("error") or 0) + int(counts.get("critical") or 0)
        score_text = "暂无总分" if score is None else f"总分 {score:.2f}"
        return f"{score_text}；发现 {warnings} 个 warning，{errors} 个 error/critical。自动评估仅供人工参考。"

