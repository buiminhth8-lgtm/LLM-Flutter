"""Adaptive loading policy for Transformers models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .capabilities import RuntimeCapabilities


@dataclass(frozen=True)
class ModelLoadPolicy:
    device: str
    dtype: str
    quantization: str
    attention_backend: str
    max_memory: dict
    cpu_offload: bool
    trust_remote_code: bool


def estimate_model_size_b(model_path: str) -> float | None:
    name = Path(model_path).name.lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*b", name)
    if match:
        return float(match.group(1))
    text = str(model_path).lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*b", text)
    return float(match.group(1)) if match else None


def _runtime_cfg(config: Any) -> dict:
    return config.get("runtime", {}) if hasattr(config, "get") else {}


def _generation_cfg(config: Any) -> dict:
    return config.get("generation", {}) if hasattr(config, "get") else {}


def _auto_max_cpu_memory(config: Any) -> str:
    value = _runtime_cfg(config).get("max_cpu_memory", "auto")
    if value and str(value).lower() != "auto":
        return str(value)
    try:
        import psutil

        available_gib = max(4, int(psutil.virtual_memory().available / (1024**3)) - 2)
        return f"{available_gib}GiB"
    except Exception:
        return "16GiB"


def choose_model_load_policy(
    model_path: str,
    config: Any,
    capabilities: RuntimeCapabilities,
) -> ModelLoadPolicy:
    runtime = _runtime_cfg(config)
    model_size_b = estimate_model_size_b(model_path)

    configured_device = runtime.get("device", "auto")
    if configured_device == "auto":
        device = "cuda" if capabilities.cuda_available else "cpu"
    else:
        device = str(configured_device)

    configured_dtype = runtime.get("dtype", "auto")
    if configured_dtype == "auto":
        if device == "cuda":
            dtype = "bfloat16" if capabilities.bf16_supported else "float16"
        else:
            dtype = "float32"
    else:
        dtype = str(configured_dtype)

    configured_quant = runtime.get("quantization", "auto")
    if configured_quant == "auto":
        if device == "cuda" and model_size_b is not None and model_size_b >= 6.5:
            quantization = "bnb4" if capabilities.bitsandbytes_4bit_usable else "none"
        else:
            quantization = "none"
    else:
        quantization = str(configured_quant)

    if quantization in {"bnb4", "4bit"} and not capabilities.bitsandbytes_4bit_usable:
        if configured_quant == "auto":
            quantization = "none"
        else:
            detail = capabilities.bitsandbytes_error or "bitsandbytes 4-bit probe failed"
            raise RuntimeError(
                "bitsandbytes 4-bit 不可用，无法按 bnb4 加载模型。"
                f"详情: {detail}"
            )

    if model_size_b is not None and model_size_b >= 14 and quantization == "none":
        raise RuntimeError(
            "14B 及以上模型不能默认全精度加载到 8GB GPU。"
            "请选择 GGUF、bnb4 或显式配置 CPU offload。"
        )

    attention = runtime.get("attention_backend", "auto")
    if attention == "auto":
        attention = "sdpa" if device == "cuda" else "eager"

    max_memory: dict = {"cpu": _auto_max_cpu_memory(config)}
    if device == "cuda":
        max_memory[0] = str(runtime.get("max_gpu_memory", "7GiB"))

    return ModelLoadPolicy(
        device=device,
        dtype=dtype,
        quantization=quantization,
        attention_backend=str(attention),
        max_memory=max_memory,
        cpu_offload=bool(runtime.get("cpu_offload", True)),
        trust_remote_code=bool(runtime.get("trust_remote_code", False)),
    )


def generation_defaults(config: Any) -> dict:
    generation = _generation_cfg(config)
    inference = config.inference if hasattr(config, "inference") else {}
    return {
        "max_new_tokens": generation.get("max_new_tokens", inference.get("max_tokens", 512)),
        "temperature": generation.get("temperature", inference.get("temperature", 0.7)),
        "top_p": generation.get("top_p", inference.get("top_p", 0.9)),
        "top_k": generation.get("top_k", inference.get("top_k", 40)),
        "repetition_penalty": generation.get(
            "repetition_penalty", inference.get("repeat_penalty", 1.05)
        ),
        "do_sample": generation.get("do_sample", True),
        "max_context_tokens": generation.get("max_context_tokens", inference.get("context_length", 4096)),
    }
