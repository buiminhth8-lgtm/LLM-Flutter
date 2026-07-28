"""Prompt construction with tokenizer chat-template fallback."""

from __future__ import annotations

from .message import ChatMessage


class PromptBuilder:
    """Build model input text from normalized chat messages."""

    role_tokens = {
        "system": "<|system|>",
        "user": "<|user|>",
        "assistant": "<|assistant|>",
        "tool": "<|tool|>",
    }

    def build_text(
        self,
        *,
        tokenizer,
        messages: list[ChatMessage],
        add_generation_prompt: bool = True,
    ) -> str:
        apply_template = getattr(tokenizer, "apply_chat_template", None)
        if callable(apply_template):
            return apply_template(
                [message.to_dict() for message in messages],
                tokenize=False,
                add_generation_prompt=add_generation_prompt,
            )
        return self._fallback_text(messages, add_generation_prompt=add_generation_prompt)

    def _fallback_text(self, messages: list[ChatMessage], *, add_generation_prompt: bool) -> str:
        parts: list[str] = []
        for message in messages:
            parts.append(self.role_tokens[message.role])
            parts.append(message.content)
        if add_generation_prompt:
            parts.append(self.role_tokens["assistant"])
        return "\n".join(parts).rstrip() + "\n"
