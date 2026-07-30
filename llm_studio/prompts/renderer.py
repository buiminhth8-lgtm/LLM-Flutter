"""Prompt renderer for Stage 2 preview-only workflows."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from .entities import PromptRenderResult, PromptTemplateVersion
from .errors import PromptRenderTooLongError
from .variables import (
    VARIABLE_PATTERN,
    extract_variables,
    stringify_variable,
    validate_variables_schema,
)

MAX_RENDERED_PROMPT_LENGTH = 200_000


class PromptRenderer:
    """Render simple ``{{variable}}`` prompt templates without executing code."""

    def render(
        self,
        template_version: PromptTemplateVersion | dict[str, Any],
        variables: dict[str, Any],
        project_context: dict[str, Any] | None = None,
    ) -> PromptRenderResult:
        version = asdict(template_version) if isinstance(template_version, PromptTemplateVersion) else dict(template_version)
        schema = validate_variables_schema(version.get("variables_schema") or {})
        defaults = version.get("default_values") or {}
        merged = {**defaults, **(project_context or {}), **(variables or {})}
        parts = [
            version.get("system_prompt"),
            version.get("role_prompt"),
            version.get("instruction_template") or "",
            version.get("output_constraints"),
            version.get("negative_prompt"),
        ]
        required = {name for name, spec in schema.items() if bool(spec.get("required"))}
        used = extract_variables(*parts)
        missing = sorted(name for name in required if merged.get(name) in (None, ""))
        warnings = sorted(f"{name} is not declared in variables_schema." for name in used if name not in schema)

        def replace(match) -> str:
            name = match.group(1)
            value = merged.get(name)
            if value in (None, ""):
                if name in required:
                    return ""
                warnings.append(f"{name} is empty.")
                return ""
            return stringify_variable(value)

        rendered_parts = [VARIABLE_PATTERN.sub(replace, part).strip() for part in parts if part]
        rendered = "\n\n".join(part for part in rendered_parts if part)
        if len(rendered) > MAX_RENDERED_PROMPT_LENGTH:
            raise PromptRenderTooLongError("Rendered prompt exceeds 200000 characters.")
        prompt_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        return PromptRenderResult(
            template_id=version["template_id"],
            template_version_id=version["id"],
            rendered_prompt=rendered,
            missing_variables=missing,
            warnings=sorted(set(warnings)),
            prompt_hash=prompt_hash,
        )
