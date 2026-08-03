"""Optional local model assisted judging."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from llm_studio.api import errors as api_errors
from llm_studio.writing.errors import WritingRuntimeError

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult


class LocalModelJudgeEvaluator:
    evaluator_type = "local_model_judge"

    def __init__(self, runtime_bridge: Any, model_id: str):
        self.runtime_bridge = runtime_bridge
        self.model_id = model_id

    async def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        if not self.model_id:
            return self._warning("未配置本地评估模型", "local_model_id is required.")
        prompt = self._prompt(input)
        try:
            result = await self.runtime_bridge.generate_text(
                generation_id=f"eval-judge-{uuid.uuid4().hex[:12]}",
                model_id=self.model_id,
                adapter_id=None,
                prompt=prompt,
                generation_params={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "max_tokens": 768,
                    "repetition_penalty": 1.05,
                    "stop": [],
                },
            )
        except WritingRuntimeError as exc:
            if exc.code in {api_errors.WRITING_MODEL_NOT_FOUND, api_errors.WRITING_MODEL_NOT_LOADED}:
                return self._warning("本地评估模型不可用", exc.message)
            return self._warning("本地模型辅助评估失败", exc.message)
        payload = self._extract_json(result.text)
        if not isinstance(payload, dict):
            return self._warning("本地模型评估 JSON 解析失败", result.text[:500])
        metrics = []
        score = payload.get("overall_score")
        if score is not None:
            try:
                metrics.append(EvaluationMetricDraft("local_model_judge_score", float(score), "score", payload))
            except (TypeError, ValueError):
                pass
        findings = []
        for raw in payload.get("findings") or []:
            if isinstance(raw, dict):
                findings.append(
                    EvaluationFindingDraft(
                        severity=str(raw.get("severity") or "info"),
                        category=str(raw.get("category") or "manual"),
                        title=str(raw.get("title") or "本地模型辅助评估发现"),
                        message=str(raw.get("message") or ""),
                        evidence={"source": "local_model_judge", "raw": raw},
                        suggestion=raw.get("suggestion"),
                    )
                )
        return EvaluationResult(
            metrics=metrics,
            findings=findings,
            summary=str(payload.get("summary") or "本地模型辅助评估完成。"),
        )

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        try:
            value = json.loads(text)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _prompt(input: EvaluationInput) -> str:
        return (
            "你是本地小说质量评估助手。只输出 JSON，不要修改正文。"
            "JSON 字段：overall_score(1-5), summary, findings数组。"
            f"\n目标类型：{input.target_type}\n目标ID：{input.target_id}\n正文：\n{input.text[:6000]}"
        )

    @staticmethod
    def _warning(title: str, message: str) -> EvaluationResult:
        return EvaluationResult(
            metrics=[],
            findings=[
                EvaluationFindingDraft(
                    "warning",
                    "manual",
                    title,
                    message or "Local model judge failed.",
                    {"source": "local_model_judge"},
                    "这只是可选辅助评估失败，不影响其他启发式评估结论。",
                )
            ],
            summary="本地模型辅助评估未完成，已记录 warning。",
        )


class LocalModelJudgeUnavailableEvaluator:
    evaluator_type = "local_model_judge"

    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        return LocalModelJudgeEvaluator._warning(self.title, self.message)
