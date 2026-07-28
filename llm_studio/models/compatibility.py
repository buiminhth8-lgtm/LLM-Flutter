"""Pre-load model compatibility estimates."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import LocalModel, ModelFormat


@dataclass(frozen=True)
class ModelCompatibilityReport:
    supported: bool
    recommended_backend: str | None
    recommended_dtype: str | None
    recommended_quantization: str | None
    estimated_weight_memory_bytes: int | None
    estimated_runtime_memory_bytes: int | None
    risk_level: str
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]


def estimate_weight_memory(parameter_count: int | None, quantization: str | None, dtype: str = "bf16") -> int | None:
    if parameter_count is None:
        return None
    q = (quantization or "").lower()
    if any(marker in q for marker in ("q4", "4", "bnb4", "gptq", "awq")):
        bytes_per_param = 0.62
    elif any(marker in q for marker in ("q8", "8", "bnb8")):
        bytes_per_param = 1.05
    elif dtype in {"bf16", "fp16", "float16", "bfloat16"}:
        bytes_per_param = 2.0
    else:
        bytes_per_param = 4.0
    return int(parameter_count * bytes_per_param)


def estimate_runtime_memory(
    parameter_count: int | None,
    quantization: str | None,
    context_length: int | None,
    *,
    batch_size: int = 1,
) -> int | None:
    weight = estimate_weight_memory(parameter_count, quantization)
    if weight is None:
        return None
    params_b = parameter_count / 1_000_000_000 if parameter_count else 3
    ctx = context_length or 4096
    kv_cache = int(params_b * 180_000_000 * (ctx / 4096) * batch_size)
    cuda_reserved = 1_000_000_000
    temp = int(weight * 0.10)
    return weight + kv_cache + temp + cuda_reserved


def assess_model_compatibility(
    model: LocalModel,
    *,
    total_vram_bytes: int = 8 * 1024**3,
    max_context_tokens: int | None = None,
) -> ModelCompatibilityReport:
    warnings: list[str] = ["估算值，仅供加载前参考。"]
    blockers: list[str] = []
    params = model.parameter_count
    params_b = params / 1_000_000_000 if params else None
    context = max_context_tokens or model.context_length or 4096
    quant = model.quantization

    backend = "transformers"
    if model.format == ModelFormat.GGUF:
        backend = "llama_cpp"
    elif model.format in {ModelFormat.GPTQ, ModelFormat.AWQ}:
        backend = model.format.value

    dtype = "bfloat16"
    recommended_quant = quant or "none"
    risk = "warning"
    supported = True

    runtime_memory = estimate_runtime_memory(params, quant, context)
    weight_memory = estimate_weight_memory(params, quant)

    if params_b is None:
        warnings.append("无法识别参数量，建议手动确认显存需求。")
        risk = "warning"
    elif params_b <= 3:
        risk = "safe"
        recommended_quant = quant or "none"
        dtype = "bfloat16"
    elif params_b <= 8:
        if quant and any(marker in quant.lower() for marker in ("q4", "4", "gptq", "awq")):
            risk = "warning"
            recommended_quant = quant
            warnings.append("7B/8B 4bit 通常可尝试，但需为 KV Cache 和运行时保留显存。")
        else:
            risk = "high-risk"
            recommended_quant = "bnb4" if model.format != ModelFormat.GGUF else "gguf-q4"
            warnings.append("7B/8B BF16/FP16 不能完整放入 8GB 显存，建议 4bit、GGUF 或 CPU offload。")
    elif params_b <= 14:
        risk = "high-risk"
        recommended_quant = "gguf-q4"
        warnings.append("14B 4bit 在 8GB 上高风险，通常需要大量 CPU offload。")
    else:
        risk = "unsupported"
        supported = False
        blockers.append("32B 及以上模型默认不推荐在 RTX 5060 Laptop 8GB 上本地运行。")

    if runtime_memory and runtime_memory > total_vram_bytes:
        warnings.append("估算运行时显存超过本机显存上限，需要 offload 或更低量化。")
        if risk == "safe":
            risk = "warning"

    return ModelCompatibilityReport(
        supported=supported,
        recommended_backend=backend,
        recommended_dtype=dtype,
        recommended_quantization=recommended_quant,
        estimated_weight_memory_bytes=weight_memory,
        estimated_runtime_memory_bytes=runtime_memory,
        risk_level=risk,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )
