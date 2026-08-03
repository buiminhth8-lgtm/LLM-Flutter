"""Base-vs-adapter generation runner for Stage 9."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any

from llm_studio.context.estimators import TokenEstimator
from llm_studio.security.redaction import redact_sensitive_text
from llm_studio.writing.length_control import count_content_chars

from .entities import AdapterPairResult, AdapterVariantResult
from .errors import AdapterEvalGenerationFailedError


class AdapterComparisonRunner:
    """Run a frozen prompt against base and base+adapter via WritingRuntimeBridge."""

    def __init__(self, runtime_bridge: Any):
        self.runtime_bridge = runtime_bridge
        self.estimator = TokenEstimator()

    async def run_pair(
        self,
        *,
        case: dict[str, Any],
        session: dict[str, Any],
    ) -> AdapterPairResult:
        prompt = str(case.get("prompt_rendered") or "")
        if not prompt.strip():
            raise AdapterEvalGenerationFailedError("Evaluation case has no frozen prompt.")
        params = dict(case.get("generation_params") or {})
        base = await self._run_variant(
            variant="base",
            model_id=session["base_model_id"],
            adapter_id=None,
            prompt=prompt,
            generation_params=params,
            case_id=case["case_id"],
        )
        adapter = await self._run_variant(
            variant="adapter",
            model_id=session["base_model_id"],
            adapter_id=session["adapter_id"],
            prompt=prompt,
            generation_params=params,
            case_id=case["case_id"],
        )
        return AdapterPairResult(base=base, adapter=adapter)

    async def _run_variant(
        self,
        *,
        variant: str,
        model_id: str,
        adapter_id: str | None,
        prompt: str,
        generation_params: dict[str, Any],
        case_id: str,
    ) -> AdapterVariantResult:
        started = time.monotonic()
        try:
            result = await self.runtime_bridge.generate_text(
                generation_id=f"adapter-eval-{case_id}-{variant}-{uuid.uuid4().hex[:8]}",
                model_id=model_id,
                adapter_id=adapter_id,
                prompt=prompt,
                generation_params=generation_params,
            )
            output = str(result.text or "").strip()
            return AdapterVariantResult(
                variant=variant,
                model_id=model_id,
                adapter_id=adapter_id,
                output_text=output,
                status="succeeded",
                finish_reason=result.finish_reason or "unknown",
                output_hash=hashlib.sha256(output.encode("utf-8")).hexdigest(),
                output_char_count=count_content_chars(output),
                output_token_estimate=self.estimator.estimate(output),
                latency_ms=result.latency_ms
                if result.latency_ms is not None
                else int((time.monotonic() - started) * 1000),
            )
        except Exception as exc:
            code = getattr(exc, "code", None) or AdapterEvalGenerationFailedError.code
            message = redact_sensitive_text(getattr(exc, "message", str(exc))) or "Generation failed."
            return AdapterVariantResult(
                variant=variant,
                model_id=model_id,
                adapter_id=adapter_id,
                output_text="",
                status="failed",
                finish_reason="error",
                output_hash=hashlib.sha256(b"").hexdigest(),
                output_char_count=0,
                output_token_estimate=0,
                latency_ms=int((time.monotonic() - started) * 1000),
                error_code=str(code),
                error_message=message,
            )
