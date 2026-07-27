from llm_studio.finetuner import tokenize_messages_for_assistant_loss


class FakeTokenizer:
    pad_token_id = 0
    eos_token = "</s>"
    pad_token = "</s>"

    def __call__(self, text, truncation=False, max_length=None, add_special_tokens=False, **kwargs):
        ids = [ord(ch) % 255 + 1 for ch in text]
        if truncation and max_length:
            ids = ids[:max_length]
        return {"input_ids": ids}


def test_assistant_only_loss_masks_user_prompt():
    tokenizer = FakeTokenizer()
    row = tokenize_messages_for_assistant_loss(
        tokenizer,
        [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ],
        512,
    )
    assert -100 in row["labels"]
    first_supervised = next(i for i, value in enumerate(row["labels"]) if value != -100)
    assert first_supervised > 0
    assert row["labels"][first_supervised:] == row["input_ids"][first_supervised:]
