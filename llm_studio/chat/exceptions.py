"""Chat message and prompt construction exceptions."""


class ChatError(ValueError):
    """Base class for chat input errors."""


class InvalidChatMessageError(ChatError):
    """Raised when a chat message has an invalid role or payload."""
