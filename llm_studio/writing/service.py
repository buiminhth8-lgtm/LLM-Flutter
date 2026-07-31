"""WritingService orchestration for Novel Studio Stage 4."""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from llm_studio.api import errors as api_errors
from llm_studio.context.errors import ContextError
from llm_studio.context.estimators import TokenEstimator
from llm_studio.novels.errors import NovelError
from llm_studio.prompts.errors import PromptError
from llm_studio.security.redaction import redact_sensitive_text

from .entities import WritingGenerationResult
from .errors import (
    WritingCancelNotSupportedError,
    WritingContextAssemblyError,
    WritingError,
    WritingInvalidGenerationParamsError,
    WritingInvalidModeError,
    WritingNotFoundError,
    WritingPromptRenderError,
    WritingRuntimeError,
    WritingSaveTargetError,
)
from .generation_modes import GENERATION_MODES
from .length_control import (
    TargetLength,
    apply_length_control,
    count_content_chars,
    normalize_target_length,
    suggest_max_tokens,
)
from .repository import GenerationRecordRepository
from .stream import split_at_stop

_SENSITIVE_KEY_MARKERS = (
    "token",
    "api_key",
    "authorization",
    "password",
    "secret",
    "cookie",
    "file_path",
    "directory_path",
    "image_path",
    "local_path",
)
_WINDOWS_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\)[^\s\"']+")
_POSIX_PATH = re.compile(r"(?<!\w)/(?:home|root|Users|var|tmp)/[^\s\"']+")


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def _safe_text(value: Any) -> str:
    text = redact_sensitive_text(str(value or "")) or ""
    text = _WINDOWS_PATH.sub("<redacted-path>", text)
    return _POSIX_PATH.sub("<redacted-path>", text)


def _safe_data(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS):
                cleaned[str(key)] = "<redacted>"
            else:
                cleaned[str(key)] = _safe_data(item)
        return cleaned
    if isinstance(value, list):
        return [_safe_data(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


class WritingService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        novel_service: Any,
        prompt_service: Any,
        context_service: Any,
        runtime_bridge: Any,
    ):
        self.db_path = Path(db_path)
        self.records = GenerationRecordRepository(self.db_path)
        self.novel_service = novel_service
        self.prompt_service = prompt_service
        self.context_service = context_service
        self.runtime_bridge = runtime_bridge
        self.estimator = TokenEstimator()

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        novel_service: Any,
        prompt_service: Any,
        context_service: Any,
        runtime_bridge: Any,
    ) -> WritingService:
        cfg = config.get("writing", {}) if config is not None else {}
        fallback = (
            config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite")
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(
            Path(cfg.get("db_path", fallback)),
            novel_service=novel_service,
            prompt_service=prompt_service,
            context_service=context_service,
            runtime_bridge=runtime_bridge,
        )

    async def generate(self, request: Any) -> dict[str, Any]:
        data, target, params, prepared = self._prepare(request)
        record = self._create_record(data, target, params, prepared, status="running")
        generation_id = record["generation_id"]
        try:
            runtime_result = await self.runtime_bridge.generate_text(
                generation_id=generation_id,
                model_id=data["model_id"],
                adapter_id=data.get("adapter_id"),
                prompt=prepared["rendered_prompt"],
                generation_params=params,
            )
            stopped_text, stopped = split_at_stop(
                runtime_result.text,
                params.get("stop") or [],
            )
            text, length_finish, length_warnings = apply_length_control(
                stopped_text,
                target,
                estimator=self.estimator,
            )
            finish_reason = (
                length_finish
                if length_finish == "length"
                else "stop"
                if stopped
                else runtime_result.finish_reason or "unknown"
            )
            updated = self._complete_record(
                generation_id,
                text,
                finish_reason,
                runtime_result.latency_ms,
            )
            warnings = [
                *prepared.get("warnings", []),
                *prepared.get("render_warnings", []),
                *length_warnings,
            ]
            result = self._result(updated, warnings)
            if data.get("save_to_chapter") and data.get("chapter_id"):
                self.save_output_to_chapter(
                    generation_id,
                    target="draft_content",
                    append=False,
                )
            return result.to_dict()
        except WritingError as exc:
            self._fail_record(generation_id, exc.code, exc.message)
            raise
        except Exception as exc:
            error = WritingRuntimeError(
                api_errors.WRITING_GENERATION_FAILED,
                _safe_text(exc) or "本地小说生成失败。",
            )
            self._fail_record(generation_id, error.code, error.message)
            raise error from exc

    async def stream_generate(self, request: Any) -> AsyncIterator[dict[str, Any]]:
        data, target, params, prepared = self._prepare(request)
        record = self._create_record(data, target, params, prepared, status="streaming")
        generation_id = record["generation_id"]
        yield {"type": "start", "generation_id": generation_id}
        chunks: list[str] = []
        pending = ""
        stop_sequences = [item for item in params.get("stop") or [] if item]
        stop_tail = max((len(item) for item in stop_sequences), default=1) - 1
        stopped = False
        last_flush = time.monotonic()
        try:
            async for chunk in self.runtime_bridge.stream_text(
                generation_id=generation_id,
                model_id=data["model_id"],
                adapter_id=data.get("adapter_id"),
                prompt=prepared["rendered_prompt"],
                generation_params=params,
            ):
                if stop_sequences:
                    pending += chunk
                    emitted, stopped = split_at_stop(pending, stop_sequences)
                    if stopped:
                        if emitted:
                            chunks.append(emitted)
                            yield {"type": "delta", "text": emitted}
                        self.runtime_bridge.cancel_generation(generation_id)
                        pending = ""
                        break
                    safe_length = max(0, len(pending) - stop_tail)
                    if safe_length:
                        emitted = pending[:safe_length]
                        pending = pending[safe_length:]
                        chunks.append(emitted)
                        yield {"type": "delta", "text": emitted}
                else:
                    chunks.append(chunk)
                    yield {"type": "delta", "text": chunk}
                if time.monotonic() - last_flush >= 0.5:
                    self.records.update(
                        generation_id,
                        {"model_output": _safe_text("".join(chunks))},
                    )
                    last_flush = time.monotonic()

            if pending and not stopped:
                chunks.append(pending)
                yield {"type": "delta", "text": pending}

            current = self.records.get(generation_id)
            if current["status"] == "cancelled":
                partial = _safe_text("".join(chunks))
                self.records.update(
                    generation_id,
                    {
                        "model_output": partial,
                        "finish_reason": "cancelled",
                        "output_hash": self._hash(partial),
                        "output_char_count": count_content_chars(partial),
                        "output_token_estimate": self.estimator.estimate(partial),
                    },
                )
                yield {
                    "type": "done",
                    "generation_id": generation_id,
                    "finish_reason": "cancelled",
                }
                return

            text, finish_reason, length_warnings = apply_length_control(
                "".join(chunks),
                target,
                estimator=self.estimator,
            )
            updated = self._complete_record(
                generation_id,
                text,
                "stop" if stopped and finish_reason != "length" else finish_reason,
                None,
            )
            if data.get("save_to_chapter") and data.get("chapter_id"):
                self.save_output_to_chapter(
                    generation_id,
                    target="draft_content",
                    append=False,
                )
            yield {
                "type": "done",
                "generation_id": generation_id,
                "finish_reason": updated["finish_reason"],
                "output_char_count": updated["output_char_count"],
                "warnings": [
                    *prepared.get("warnings", []),
                    *prepared.get("render_warnings", []),
                    *length_warnings,
                ],
            }
        except WritingError as exc:
            current = self.records.get(generation_id)
            if current["status"] != "cancelled":
                partial = _safe_text("".join(chunks) + pending)
                if partial:
                    self.records.update(
                        generation_id,
                        {
                            "model_output": partial,
                            "output_hash": self._hash(partial),
                            "output_char_count": count_content_chars(partial),
                            "output_token_estimate": self.estimator.estimate(partial),
                        },
                    )
                self._fail_record(generation_id, exc.code, exc.message)
            yield {
                "type": "error",
                "generation_id": generation_id,
                "error_code": exc.code,
                "message": exc.message,
            }
        except Exception as exc:
            message = _safe_text(exc) or "本地小说流式生成失败。"
            partial = _safe_text("".join(chunks) + pending)
            if partial:
                self.records.update(
                    generation_id,
                    {
                        "model_output": partial,
                        "output_hash": self._hash(partial),
                        "output_char_count": count_content_chars(partial),
                        "output_token_estimate": self.estimator.estimate(partial),
                    },
                )
            self._fail_record(generation_id, api_errors.WRITING_STREAM_FAILED, message)
            yield {
                "type": "error",
                "generation_id": generation_id,
                "error_code": api_errors.WRITING_STREAM_FAILED,
                "message": message,
            }

    def save_output_to_chapter(
        self,
        generation_id: str,
        *,
        target: str = "draft_content",
        append: bool = False,
    ) -> dict[str, Any]:
        if target not in {"draft_content", "summary"}:
            raise WritingSaveTargetError(
                "Stage 4 only allows draft_content or summary as save targets."
            )
        record = self.records.get(generation_id)
        chapter_id = record.get("chapter_id")
        if not chapter_id:
            raise WritingNotFoundError("chapter", "")
        try:
            chapter = self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise WritingNotFoundError("chapter", chapter_id) from exc
        if chapter.get("project_id") != record.get("project_id"):
            raise WritingNotFoundError("chapter", chapter_id)
        output = record.get("model_output") or ""
        if append:
            current = chapter.get(target) or ""
            output = f"{current.rstrip()}\n\n{output.lstrip()}".strip()
        return self.novel_service.update_chapter(chapter_id, {target: output})

    def cancel_generation(self, generation_id: str) -> dict[str, Any]:
        record = self.records.get(generation_id)
        if record["status"] not in {"running", "streaming"}:
            raise WritingCancelNotSupportedError(
                "该生成任务已结束或当前不能取消。"
            )
        if not self.runtime_bridge.cancel_generation(generation_id):
            raise WritingCancelNotSupportedError("当前 Runtime 不支持取消该生成任务。")
        return self.records.update(
            generation_id,
            {"status": "cancelled", "finish_reason": "cancelled"},
        )

    def get_generation(self, generation_id: str) -> dict[str, Any]:
        return self.records.get(generation_id)

    def list_generations(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        mode: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if mode:
            self._validate_mode(mode)
        return self.records.list(
            project_id=project_id,
            chapter_id=chapter_id,
            mode=mode,
            status=status,
            limit=limit,
            offset=offset,
        )

    def _prepare(
        self,
        request: Any,
    ) -> tuple[dict[str, Any], TargetLength, dict[str, Any], dict[str, Any]]:
        data = _model_dump(request)
        self._validate_mode(str(data.get("mode") or ""))
        target = normalize_target_length(data.get("target_length"))
        params = self._generation_params(
            data.get("generation_params") or {},
            target=target,
        )
        user_variables = data.get("user_variables") or {}
        if not isinstance(user_variables, dict):
            raise WritingInvalidGenerationParamsError(
                "user_variables must be an object."
            )
        safe_variables = _safe_data(user_variables)
        project = self._project(data["project_id"])
        chapter = self._chapter(data.get("chapter_id"), project["id"])
        self._scene(data.get("scene_id"), chapter)
        if chapter:
            safe_variables.setdefault("chapter_draft", chapter.get("draft_content") or "")
            safe_variables.setdefault("current_text", chapter.get("draft_content") or "")
        safe_variables.setdefault(
            "target_length",
            f"{target.minimum}-{target.maximum} "
            f"{'中文字符' if target.unit == 'chars' else 'tokens'}",
        )
        data["user_variables"] = safe_variables
        prepared = self._prepare_prompt(data, params)
        prepared["rendered_prompt"] = _safe_text(prepared["rendered_prompt"])
        prepared["variables"] = _safe_data(prepared.get("variables") or {})
        return data, target, params, prepared

    def _prepare_prompt(
        self,
        data: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if data.get("context_id"):
            try:
                context = self.context_service.get_context_record(data["context_id"])
            except ContextError as exc:
                raise WritingNotFoundError("context", data["context_id"]) from exc
            if context.get("project_id") != data["project_id"]:
                raise WritingNotFoundError("context", data["context_id"])
            template_id = data.get("template_id") or context.get("template_id")
            version_id = data.get("template_version_id") or context.get(
                "template_version_id"
            )
            try:
                template = self.prompt_service.get_template(template_id)
                version = self.prompt_service.get_version(
                    version_id or template.get("active_version_id")
                )
                variables = {
                    **(context.get("variables") or {}),
                    **data["user_variables"],
                }
                rendered = self.prompt_service.renderer.render(version, variables, None)
            except PromptError as exc:
                raise WritingPromptRenderError(exc.message) from exc
            return {
                **context,
                "template_id": template["id"],
                "template_version_id": version["id"],
                "variables": variables,
                "rendered_prompt": rendered.rendered_prompt,
                "prompt_hash": rendered.prompt_hash,
                "render_warnings": rendered.warnings,
            }

        context_tokens = max(512, min(32768 - params["max_tokens"], 12000))
        request = {
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": data.get("template_id"),
            "template_version_id": data.get("template_version_id"),
            "mode": data["mode"],
            "target_budget": {
                "max_tokens": min(32768, context_tokens + params["max_tokens"]),
                "reserved_output_tokens": params["max_tokens"],
                "max_context_tokens": context_tokens,
                "max_chars": max(12000, context_tokens * 3),
                "hard_limit": True,
            },
            "user_variables": data["user_variables"],
            "save_record": True,
        }
        try:
            return self.context_service.assemble_and_render(request)
        except ContextError as exc:
            if exc.code in {
                api_errors.CONTEXT_PROJECT_NOT_FOUND,
                api_errors.CONTEXT_CHAPTER_NOT_FOUND,
                api_errors.CONTEXT_SCENE_NOT_FOUND,
            }:
                kind = exc.code.removeprefix("CONTEXT_").removesuffix("_NOT_FOUND").lower()
                raise WritingNotFoundError(kind, data.get(f"{kind}_id") or "") from exc
            if exc.code in {
                api_errors.CONTEXT_TEMPLATE_NOT_FOUND,
                api_errors.CONTEXT_TEMPLATE_VERSION_NOT_FOUND,
            }:
                raise WritingNotFoundError(
                    "template",
                    data.get("template_id") or "",
                ) from exc
            if exc.code == api_errors.CONTEXT_RENDER_FAILED:
                raise WritingPromptRenderError(exc.message) from exc
            raise WritingContextAssemblyError(exc.message) from exc

    def _create_record(
        self,
        data: dict[str, Any],
        target: TargetLength,
        params: dict[str, Any],
        prepared: dict[str, Any],
        *,
        status: str,
    ) -> dict[str, Any]:
        return self.records.create(
            {
                "project_id": data["project_id"],
                "chapter_id": data.get("chapter_id"),
                "scene_id": data.get("scene_id"),
                "template_id": prepared.get("template_id"),
                "template_version_id": prepared.get("template_version_id"),
                "context_id": prepared.get("context_id"),
                "model_id": data["model_id"],
                "adapter_id": data.get("adapter_id"),
                "mode": data["mode"],
                "prompt_rendered": prepared["rendered_prompt"],
                "input_context": {
                    "variables": prepared.get("variables") or {},
                    "selected_items": prepared.get("selected_items") or {},
                    "warnings": prepared.get("warnings") or [],
                },
                "generation_params": params,
                "target_length": target.to_dict(),
                "status": status,
                "prompt_hash": prepared.get("prompt_hash"),
                "context_hash": prepared.get("context_hash"),
                "input_token_estimate": int(prepared.get("estimated_tokens") or 0),
            }
        )

    def _complete_record(
        self,
        generation_id: str,
        text: str,
        finish_reason: str,
        latency_ms: int | None,
    ) -> dict[str, Any]:
        safe_output = _safe_text(text)
        return self.records.update(
            generation_id,
            {
                "model_output": safe_output,
                "status": "succeeded",
                "finish_reason": finish_reason,
                "output_hash": self._hash(safe_output),
                "output_token_estimate": self.estimator.estimate(safe_output),
                "output_char_count": count_content_chars(safe_output),
                "latency_ms": latency_ms,
                "error_code": None,
                "error_message": None,
            },
        )

    def _fail_record(self, generation_id: str, code: str, message: str) -> None:
        self.records.update(
            generation_id,
            {
                "status": "failed",
                "finish_reason": "error",
                "error_code": code,
                "error_message": _safe_text(message),
            },
        )

    def _result(
        self,
        record: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> WritingGenerationResult:
        return WritingGenerationResult(
            generation_id=record["generation_id"],
            project_id=record["project_id"],
            chapter_id=record.get("chapter_id"),
            mode=record["mode"],
            model_id=record["model_id"],
            adapter_id=record.get("adapter_id"),
            text=record["model_output"],
            finish_reason=record.get("finish_reason") or "unknown",
            output_char_count=record["output_char_count"],
            input_token_estimate=record["input_token_estimate"],
            output_token_estimate=record["output_token_estimate"],
            warnings=warnings,
        )

    def _project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.novel_service.get_project(project_id)
        except NovelError as exc:
            raise WritingNotFoundError("project", project_id) from exc

    def _chapter(
        self,
        chapter_id: str | None,
        project_id: str,
    ) -> dict[str, Any] | None:
        if not chapter_id:
            return None
        try:
            chapter = self.novel_service.get_chapter(chapter_id)
        except NovelError as exc:
            raise WritingNotFoundError("chapter", chapter_id) from exc
        if chapter.get("project_id") != project_id:
            raise WritingNotFoundError("chapter", chapter_id)
        return chapter

    def _scene(
        self,
        scene_id: str | None,
        chapter: dict[str, Any] | None,
    ) -> None:
        if not scene_id:
            return
        if not chapter:
            raise WritingNotFoundError("scene", scene_id)
        scenes = self.novel_service.list_scenes(chapter["id"], limit=200)
        if not any(item.get("id") == scene_id for item in scenes):
            raise WritingNotFoundError("scene", scene_id)

    @staticmethod
    def _validate_mode(mode: str) -> None:
        if mode not in GENERATION_MODES:
            raise WritingInvalidModeError(f"Unsupported writing mode: {mode}")

    @staticmethod
    def _generation_params(
        value: Any,
        *,
        target: TargetLength | None = None,
    ) -> dict[str, Any]:
        data = _model_dump(value) if not isinstance(value, dict) else dict(value)
        try:
            max_tokens_value = data.get("max_tokens")
            if max_tokens_value is None:
                max_tokens_value = suggest_max_tokens(target or TargetLength())
            params = {
                "temperature": float(data.get("temperature", 0.8)),
                "top_p": float(data.get("top_p", 0.9)),
                "max_tokens": int(max_tokens_value),
                "repetition_penalty": float(data.get("repetition_penalty", 1.1)),
                "stream": bool(data.get("stream", False)),
                "stop": list(data.get("stop") or []),
            }
        except (TypeError, ValueError) as exc:
            raise WritingInvalidGenerationParamsError(
                "Invalid generation parameter types."
            ) from exc
        if not 0 <= params["temperature"] <= 2:
            raise WritingInvalidGenerationParamsError(
                "temperature must be between 0.0 and 2.0."
            )
        if not 0 <= params["top_p"] <= 1:
            raise WritingInvalidGenerationParamsError(
                "top_p must be between 0.0 and 1.0."
            )
        if not 1 <= params["max_tokens"] <= 32768:
            raise WritingInvalidGenerationParamsError(
                "max_tokens must be between 1 and 32768."
            )
        if not 0.8 <= params["repetition_penalty"] <= 2:
            raise WritingInvalidGenerationParamsError(
                "repetition_penalty must be between 0.8 and 2.0."
            )
        return params

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
