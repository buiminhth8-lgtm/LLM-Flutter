import pytest

from llm_studio.chat import ChatHistoryWindow, ChatMessage, InvalidChatMessageError, PromptBuilder, build_model_input, truncate_messages


class FakeTokenizer:
    def __call__(self, text, add_special_tokens=False, **kwargs):
        return {"input_ids": text.split()}


def test_fallback_template_preserves_system_and_history():
    messages = [
        {"role": "system", "content": "be precise"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "again"},
    ]
    text = build_model_input(FakeTokenizer(), messages)
    assert "<|system|>\nbe precise" in text
    assert "<|assistant|>\nhi" in text
    assert text.rstrip().endswith("<|assistant|>")


def test_truncation_keeps_system_and_recent_turns():
    messages = [{"role": "system", "content": "keep"}]
    messages += [{"role": "user", "content": f"old {idx}"} for idx in range(20)]
    messages.append({"role": "user", "content": "recent"})
    truncated = truncate_messages(FakeTokenizer(), messages, max_context_tokens=8)
    assert truncated[0].role == "system"
    assert truncated[-1].content == "recent"


def test_invalid_role_rejected():
    with pytest.raises(InvalidChatMessageError):
        ChatMessage.from_dict({"role": "bad", "content": ""})


def test_prompt_builder_uses_chat_template():
    class TemplateTokenizer(FakeTokenizer):
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return "|".join(message["role"] for message in messages) + "|assistant"

    text = PromptBuilder().build_text(
        tokenizer=TemplateTokenizer(),
        messages=[ChatMessage("system", ""), ChatMessage("tool", "ok", tool_call_id="1")],
    )
    assert text == "system|tool|assistant"


def test_history_window_reserves_generation_tokens():
    messages = [ChatMessage("system", "keep")]
    messages += [ChatMessage("user", f"old {idx}") for idx in range(8)]
    result = ChatHistoryWindow().fit_messages(
        tokenizer=FakeTokenizer(),
        messages=messages,
        max_context_tokens=10,
        reserved_generation_tokens=4,
    )
    assert result[0].role == "system"
    assert len(result) < len(messages)
