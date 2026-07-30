"""Prompt Studio error types."""

from __future__ import annotations

from llm_studio.api.errors import (
    PROMPT_CHAPTER_NOT_FOUND,
    PROMPT_DEFAULT_TEMPLATE_FAILED,
    PROMPT_INVALID_SCOPE,
    PROMPT_INVALID_TYPE,
    PROMPT_INVALID_VARIABLE_SCHEMA,
    PROMPT_MISSING_REQUIRED_VARIABLES,
    PROMPT_PROJECT_NOT_FOUND,
    PROMPT_RENDER_TOO_LONG,
    PROMPT_TEMPLATE_NOT_FOUND,
    PROMPT_TEMPLATE_VERSION_NOT_FOUND,
    PROMPT_VERSION_MISMATCH,
)


class PromptError(ValueError):
    code = "PROMPT_ERROR"
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class PromptNotFoundError(PromptError):
    status_code = 404

    def __init__(self, kind: str, item_id: str):
        codes = {
            "template": PROMPT_TEMPLATE_NOT_FOUND,
            "version": PROMPT_TEMPLATE_VERSION_NOT_FOUND,
            "project": PROMPT_PROJECT_NOT_FOUND,
            "chapter": PROMPT_CHAPTER_NOT_FOUND,
        }
        self.code = codes.get(kind, "PROMPT_NOT_FOUND")
        super().__init__(f"Prompt {kind} not found: {item_id}")


class PromptValidationError(PromptError):
    code = PROMPT_INVALID_VARIABLE_SCHEMA


class PromptInvalidTypeError(PromptError):
    code = PROMPT_INVALID_TYPE


class PromptInvalidScopeError(PromptError):
    code = PROMPT_INVALID_SCOPE


class PromptRenderTooLongError(PromptError):
    code = PROMPT_RENDER_TOO_LONG


class PromptVersionMismatchError(PromptError):
    code = PROMPT_VERSION_MISMATCH


class PromptMissingVariablesError(PromptError):
    code = PROMPT_MISSING_REQUIRED_VARIABLES


class PromptDefaultTemplateError(PromptError):
    code = PROMPT_DEFAULT_TEMPLATE_FAILED
