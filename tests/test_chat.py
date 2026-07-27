from llm_studio.chat import build_model_input, truncate_messages


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
    assert "System: be precise" in text
    assert "Assistant: hi" in text
    assert text.endswith("Assistant:")


def test_truncation_keeps_system_and_recent_turns():
    messages = [{"role": "system", "content": "keep"}]
    messages += [{"role": "user", "content": f"old {idx}"} for idx in range(20)]
    messages.append({"role": "user", "content": "recent"})
    truncated = truncate_messages(FakeTokenizer(), messages, max_context_tokens=8)
    assert truncated[0]["role"] == "system"
    assert truncated[-1]["content"] == "recent"
