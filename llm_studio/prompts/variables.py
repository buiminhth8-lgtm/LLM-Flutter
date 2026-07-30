"""Prompt variable extraction and validation."""

from __future__ import annotations

import re
from typing import Any

from .errors import PromptValidationError

VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")
ALLOWED_VARIABLE_TYPES = {"string", "number", "boolean", "list", "object"}


def extract_variables(*texts: str | None) -> set[str]:
    found: set[str] = set()
    for text in texts:
        if text:
            found.update(VARIABLE_PATTERN.findall(text))
    return found


def validate_variables_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise PromptValidationError("variables_schema must be an object.")
    for name, spec in schema.items():
        if not isinstance(name, str) or not VARIABLE_PATTERN.fullmatch("{{" + name + "}}"):
            raise PromptValidationError(f"Invalid variable name: {name}")
        if not isinstance(spec, dict):
            raise PromptValidationError(f"Variable spec must be an object: {name}")
        var_type = spec.get("type", "string")
        if var_type not in ALLOWED_VARIABLE_TYPES:
            raise PromptValidationError(f"Invalid variable type for {name}: {var_type}")
        required = spec.get("required", False)
        if not isinstance(required, bool):
            raise PromptValidationError(f"Variable required flag must be boolean: {name}")
    return schema


def stringify_variable(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        return "\n".join(stringify_variable(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {stringify_variable(val)}" for key, val in value.items())
    return str(value)
