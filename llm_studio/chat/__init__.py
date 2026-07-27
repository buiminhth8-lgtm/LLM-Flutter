"""Shared chat message and prompt utilities."""

from __future__ import annotations

from typing import Any

from .exceptions import ChatError, InvalidChatMessageError
from .history_window import ChatHistoryWindow
from .message import ChatMessage, ChatRole, normalize_messages
from .prompt_builder import PromptBuilder


Message = ChatMessage


def build_model_input(
    tokenizer: Any,
    messages,
    *,
    add_generation_prompt: bool = True,
) -> str:
    normalized = normalize_messages(messages)
    return PromptBuilder().build_text(
        tokenizer=tokenizer,
        messages=normalized,
        add_generation_prompt=add_generation_prompt,
    )


def truncate_messages(
    tokenizer: Any,
    messages,
    *,
    max_context_tokens: int,
) -> list[ChatMessage]:
    return ChatHistoryWindow().fit_messages(
        tokenizer=tokenizer,
        messages=normalize_messages(messages),
        max_context_tokens=max_context_tokens,
        reserved_generation_tokens=0,
    )


__all__ = [
    "ChatError",
    "InvalidChatMessageError",
    "ChatHistoryWindow",
    "ChatMessage",
    "ChatRole",
    "Message",
    "PromptBuilder",
    "build_model_input",
    "normalize_messages",
    "truncate_messages",
]
