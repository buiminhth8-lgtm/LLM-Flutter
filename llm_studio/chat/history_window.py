"""Context-window fitting for multi-turn chat history."""

from __future__ import annotations

from dataclasses import replace

from .message import ChatMessage
from .prompt_builder import PromptBuilder


class ChatHistoryWindow:
    """Trim chat history while preserving system prompt and recent turns."""

    def __init__(self, prompt_builder: PromptBuilder | None = None):
        self.prompt_builder = prompt_builder or PromptBuilder()

    def fit_messages(
        self,
        *,
        tokenizer,
        messages: list[ChatMessage],
        max_context_tokens: int,
        reserved_generation_tokens: int,
    ) -> list[ChatMessage]:
        if not messages:
            return []
        budget = max(1, max_context_tokens - max(0, reserved_generation_tokens))
        original_tokens = self._count(tokenizer, messages)
        if original_tokens <= budget:
            return list(messages)

        first_system = next((message for message in messages if message.role == "system"), None)
        non_system = [message for message in messages if message is not first_system]
        kept: list[ChatMessage] = []

        for turn in reversed(self._turns(non_system)):
            candidate = ([first_system] if first_system else []) + turn + kept
            if self._count(tokenizer, candidate) <= budget:
                kept = turn + kept
                continue
            if not kept and turn:
                kept = [self._truncate_tail(tokenizer, turn[-1], budget)]
            break

        result = ([first_system] if first_system else []) + kept
        result_tokens = self._count(tokenizer, result)
        print(
            "[Chat] step=history-trim "
            f"originalMessages={len(messages)} resultMessages={len(result)} "
            f"originalTokens={original_tokens} resultTokens={result_tokens} "
            f"reservedTokens={reserved_generation_tokens}"
        )
        return result

    def _turns(self, messages: list[ChatMessage]) -> list[list[ChatMessage]]:
        turns: list[list[ChatMessage]] = []
        current: list[ChatMessage] = []
        for message in messages:
            if message.role == "user" and current:
                turns.append(current)
                current = [message]
            else:
                current.append(message)
        if current:
            turns.append(current)
        return turns

    def _truncate_tail(self, tokenizer, message: ChatMessage, budget: int) -> ChatMessage:
        if message.role != "user":
            return message
        token_ids = tokenizer(message.content, add_special_tokens=False).get("input_ids", [])
        if len(token_ids) <= budget:
            return message
        tail_ids = token_ids[-budget:]
        decode = getattr(tokenizer, "decode", None)
        if callable(decode):
            content = decode(tail_ids, skip_special_tokens=True)
        else:
            content = message.content[-budget:]
        return replace(message, content=content)

    def _count(self, tokenizer, messages: list[ChatMessage]) -> int:
        text = self.prompt_builder.build_text(
            tokenizer=tokenizer,
            messages=messages,
            add_generation_prompt=True,
        )
        return len(tokenizer(text, add_special_tokens=False).get("input_ids", []))
