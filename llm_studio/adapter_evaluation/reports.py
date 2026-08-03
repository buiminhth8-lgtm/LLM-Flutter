"""Lightweight report generation from manual Adapter Evaluation scores."""

from __future__ import annotations

from statistics import mean
from typing import Any

from .scoring import SCORE_DIMENSIONS


class AdapterEvaluationReportBuilder:
    def build(
        self,
        *,
        session: dict[str, Any],
        cases: list[dict[str, Any]],
        scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        completed = [case for case in cases if case.get("status") == "completed"]
        scored = [
            score
            for score in scores
            if score.get("base_score") is not None or score.get("adapter_score") is not None
        ]
        adapter_wins = sum(1 for score in scores if score.get("winner") == "adapter")
        base_wins = sum(1 for score in scores if score.get("winner") == "base")
        ties = sum(1 for score in scores if score.get("winner") == "tie")
        base_values = [int(score["base_score"]) for score in scored if score.get("base_score") is not None]
        adapter_values = [
            int(score["adapter_score"])
            for score in scored
            if score.get("adapter_score") is not None
        ]
        dimension_averages: dict[str, dict[str, float | None]] = {}
        for name in SCORE_DIMENSIONS:
            base_dimension: list[int] = []
            adapter_dimension: list[int] = []
            for score in scores:
                dimension = (score.get("dimensions") or {}).get(name) or {}
                if dimension.get("base") is not None:
                    base_dimension.append(int(dimension["base"]))
                if dimension.get("adapter") is not None:
                    adapter_dimension.append(int(dimension["adapter"]))
            if base_dimension or adapter_dimension:
                dimension_averages[name] = {
                    "base": round(mean(base_dimension), 2) if base_dimension else None,
                    "adapter": round(mean(adapter_dimension), 2) if adapter_dimension else None,
                }
        warnings: list[dict[str, Any]] = []
        scored_count = len(scored)
        if scored_count < max(1, min(3, len(cases))):
            recommendation = "insufficient_scores"
            warnings.append(
                {
                    "code": "ADAPTER_EVAL_INSUFFICIENT_SCORES",
                    "message": "人工评分数量较少，报告只能作为初步参考。",
                }
            )
        elif adapter_values and base_values and mean(adapter_values) <= mean(base_values) - 1:
            recommendation = "adapter_regression"
            warnings.append(
                {
                    "code": "ADAPTER_EVAL_ADAPTER_REGRESSION",
                    "message": "Adapter 平均分明显低于 base，请谨慎使用。",
                }
            )
        elif adapter_wins > base_wins:
            recommendation = "adapter_candidate"
        else:
            recommendation = "needs_more_review"
        return {
            "session_id": session["session_id"],
            "case_count": len(cases),
            "completed_case_count": len(completed),
            "scored_case_count": scored_count,
            "adapter_win_count": adapter_wins,
            "base_win_count": base_wins,
            "tie_count": ties,
            "average_base_score": round(mean(base_values), 2) if base_values else None,
            "average_adapter_score": round(mean(adapter_values), 2) if adapter_values else None,
            "dimension_averages": dimension_averages,
            "recommendation": recommendation,
            "warnings": warnings,
        }

    @staticmethod
    def summary(report: dict[str, Any]) -> str:
        return (
            f"Adapter wins {report['adapter_win_count']} / "
            f"base wins {report['base_win_count']} / ties {report['tie_count']}; "
            f"recommendation={report['recommendation']}."
        )
