from llm_studio.finetune.memory_estimator import estimate_training_memory


def test_7b_on_8gb_high_risk():
    estimate = estimate_training_memory(
        model_path="Qwen2.5-7B-Instruct",
        method="qlora",
        max_seq_length=1024,
        batch_size=1,
    )
    assert estimate.risk_level == "high-risk"


def test_14b_unsupported():
    estimate = estimate_training_memory(
        model_path="Qwen2.5-14B-Instruct",
        method="qlora",
        max_seq_length=1024,
        batch_size=1,
    )
    assert estimate.risk_level == "unsupported"
