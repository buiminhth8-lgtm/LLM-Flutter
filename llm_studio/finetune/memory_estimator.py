"""Low-VRAM fine-tuning risk estimator."""

from __future__ import annotations

from dataclasses import dataclass

from llm_studio.runtime.model_load_policy import estimate_model_size_b


@dataclass(frozen=True)
class TrainingMemoryEstimate:
    risk_level: str
    message: str
    estimated_vram_gib: float


def estimate_training_memory(
    *,
    model_path: str,
    method: str,
    max_seq_length: int,
    batch_size: int,
    vram_gib: float = 8.0,
) -> TrainingMemoryEstimate:
    size_b = estimate_model_size_b(model_path) or 3.0
    quant_bits = 4 if method == "qlora" else 16
    param_gib = size_b * 1_000_000_000 * quant_bits / 8 / (1024**3)
    activation_gib = max(0.5, size_b * max_seq_length * batch_size / 4096 * 0.35)
    lora_optimizer_gib = max(0.2, size_b * 0.08)
    total = param_gib + activation_gib + lora_optimizer_gib

    if size_b >= 14:
        return TrainingMemoryEstimate(
            "unsupported",
            "14B 及以上模型默认不支持在 8GB 显存上微调。",
            total,
        )
    if size_b >= 6.5:
        return TrainingMemoryEstimate(
            "high-risk",
            "7B/8B QLoRA 在 8GB 显存上属于高风险，需要明确确认并使用 batch=1。",
            total,
        )
    if total > vram_gib * 0.85:
        return TrainingMemoryEstimate("warning", "预计显存接近上限，建议降低序列长度。", total)
    return TrainingMemoryEstimate("safe", "预计可在 8GB 显存上进行短跑验证。", total)
