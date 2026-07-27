"""Chat message formatting shared by API, Web UI, CLI, and runners."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


Message = dict[str, str]


def normalize_messages(messages: Sequence[Message] | str) -> list[Message]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]

    normalized: list[Message] = []
    for item in messages:
        role = str(item.get("role", "user")).strip() or "user"
        content = str(item.get("content", ""))
        if role not in {"system", "user", "assistant", "tool"}:
            role = "user"
        normalized.append({"role": role, "content": content})
    return normalized


def fallback_chat_template(messages: Sequence[Message], add_generation_prompt: bool = True) -> str:
    lines: list[str] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            lines.append(f"System: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
        else:
            lines.append(f"User: {content}")
    if add_generation_prompt:
        lines.append("Assistant:")
    return "\n".join(lines)


def build_model_input(
    tokenizer: Any,
    messages: Sequence[Message] | str,
    *,
    add_generation_prompt: bool = True,
) -> str:
    normalized = normalize_messages(messages)
    apply_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_template):
        try:
            return apply_template(
                normalized,
                tokenize=False,
                add_generation_prompt=add_generation_prompt,
            )
        except Exception as exc:
            raise RuntimeError(f"模型 chat template 格式化失败: {exc}") from exc
    return fallback_chat_template(normalized, add_generation_prompt=add_generation_prompt)


def truncate_messages(
    tokenizer: Any,
    messages: Sequence[Message],
    *,
    max_context_tokens: int,
) -> list[Message]:
    normalized = normalize_messages(messages)
    if max_context_tokens <= 0 or tokenizer is None:
        return normalized

    def token_count(candidate: list[Message]) -> int:
        text = build_model_input(tokenizer, candidate, add_generation_prompt=True)
        encoded = tokenizer(text, add_special_tokens=False)
        return len(encoded.get("input_ids", []))

    if token_count(normalized) <= max_context_tokens:
        return normalized

    system_messages = [m for m in normalized if m["role"] == "system"]
    rest = [m for m in normalized if m["role"] != "system"]
    kept: list[Message] = []
    for msg in reversed(rest):
        candidate = system_messages + [msg] + kept
        if token_count(candidate) > max_context_tokens and kept:
            break
        kept.insert(0, msg)
    return system_messages + kept
