"""Immutable chat message model shared by API, Flutter UI, and runners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .exceptions import InvalidChatMessageError

ChatRole = Literal["system", "user", "assistant", "tool"]
VALID_ROLES = {"system", "user", "assistant", "tool"}


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise InvalidChatMessageError(f"不支持的消息角色: {self.role}")
        if self.content is None:
            raise InvalidChatMessageError("消息 content 不能为 None。")
        if not isinstance(self.content, str):
            object.__setattr__(self, "content", str(self.content))
        if self.role == "tool" and self.tool_call_id is not None and not isinstance(self.tool_call_id, str):
            raise InvalidChatMessageError("tool_call_id 必须是字符串。")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        if not isinstance(data, dict):
            raise InvalidChatMessageError("消息必须是对象。")
        role = data.get("role", "user")
        return cls(
            role=role,
            content=data.get("content", ""),
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
        )

    def to_dict(self) -> dict[str, str]:
        data = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        return data


def normalize_messages(messages: list[ChatMessage] | list[dict[str, Any]] | str) -> list[ChatMessage]:
    if isinstance(messages, str):
        return [ChatMessage(role="user", content=messages)]
    normalized: list[ChatMessage] = []
    for message in messages:
        if isinstance(message, ChatMessage):
            normalized.append(message)
        else:
            normalized.append(ChatMessage.from_dict(message))
    return normalized
