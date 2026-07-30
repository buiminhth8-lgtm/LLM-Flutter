"""Stable Context Assembler errors."""

from __future__ import annotations

from llm_studio.api.errors import (
    CONTEXT_ASSEMBLY_FAILED,
    CONTEXT_BUDGET_EXCEEDED,
    CONTEXT_CHAPTER_NOT_FOUND,
    CONTEXT_INVALID_BUDGET,
    CONTEXT_PROJECT_NOT_FOUND,
    CONTEXT_RENDER_FAILED,
    CONTEXT_SCENE_NOT_FOUND,
    CONTEXT_TEMPLATE_NOT_FOUND,
    CONTEXT_TEMPLATE_VERSION_NOT_FOUND,
    CONTEXT_VARIABLES_INVALID,
)


class ContextError(ValueError):
    code = CONTEXT_ASSEMBLY_FAILED
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ContextNotFoundError(ContextError):
    status_code = 404

    def __init__(self, kind: str, item_id: str):
        codes = {
            "project": CONTEXT_PROJECT_NOT_FOUND,
            "chapter": CONTEXT_CHAPTER_NOT_FOUND,
            "scene": CONTEXT_SCENE_NOT_FOUND,
            "template": CONTEXT_TEMPLATE_NOT_FOUND,
            "template_version": CONTEXT_TEMPLATE_VERSION_NOT_FOUND,
        }
        self.code = codes.get(kind, CONTEXT_ASSEMBLY_FAILED)
        super().__init__(f"Context {kind} not found: {item_id}")


class ContextInvalidBudgetError(ContextError):
    code = CONTEXT_INVALID_BUDGET


class ContextVariablesError(ContextError):
    code = CONTEXT_VARIABLES_INVALID


class ContextBudgetExceededError(ContextError):
    code = CONTEXT_BUDGET_EXCEEDED


class ContextRenderError(ContextError):
    code = CONTEXT_RENDER_FAILED
