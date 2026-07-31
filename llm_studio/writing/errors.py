"""Stable errors for Novel Studio writing generation."""

from __future__ import annotations

from llm_studio.api import errors as api_errors


class WritingError(ValueError):
    code = api_errors.WRITING_GENERATION_FAILED
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class WritingNotFoundError(WritingError):
    status_code = 404

    def __init__(self, kind: str, item_id: str):
        codes = {
            "project": api_errors.WRITING_PROJECT_NOT_FOUND,
            "chapter": api_errors.WRITING_CHAPTER_NOT_FOUND,
            "scene": api_errors.WRITING_SCENE_NOT_FOUND,
            "template": api_errors.WRITING_TEMPLATE_NOT_FOUND,
            "context": api_errors.WRITING_CONTEXT_NOT_FOUND,
            "model": api_errors.WRITING_MODEL_NOT_FOUND,
            "adapter": api_errors.WRITING_ADAPTER_NOT_FOUND,
            "generation": api_errors.WRITING_GENERATION_NOT_FOUND,
        }
        self.code = codes.get(kind, api_errors.WRITING_GENERATION_NOT_FOUND)
        super().__init__(f"Writing {kind} not found: {item_id}")


class WritingInvalidModeError(WritingError):
    code = api_errors.WRITING_INVALID_MODE


class WritingInvalidTargetLengthError(WritingError):
    code = api_errors.WRITING_INVALID_TARGET_LENGTH


class WritingInvalidGenerationParamsError(WritingError):
    code = api_errors.WRITING_INVALID_GENERATION_PARAMS


class WritingContextAssemblyError(WritingError):
    code = api_errors.WRITING_CONTEXT_ASSEMBLY_FAILED


class WritingPromptRenderError(WritingError):
    code = api_errors.WRITING_PROMPT_RENDER_FAILED


class WritingRuntimeError(WritingError):
    status_code = 500

    def __init__(self, code: str, message: str):
        self.code = code
        if code in {
            api_errors.WRITING_MODEL_NOT_FOUND,
            api_errors.WRITING_ADAPTER_NOT_FOUND,
        }:
            self.status_code = 404
        elif code == api_errors.WRITING_MODEL_NOT_LOADED:
            self.status_code = 409
        elif code == api_errors.WRITING_MODEL_NOT_SUPPORTED:
            self.status_code = 400
        super().__init__(message)


class WritingCancelNotSupportedError(WritingError):
    code = api_errors.WRITING_CANCEL_NOT_SUPPORTED
    status_code = 409


class WritingSaveTargetError(WritingError):
    code = api_errors.WRITING_SAVE_TARGET_NOT_ALLOWED


class WritingStreamError(WritingError):
    code = api_errors.WRITING_STREAM_FAILED
    status_code = 500
