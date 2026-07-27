"""Safe metadata readers for local model files.

The helpers in this module only inspect static files. They never import model
code, call ``from_pretrained``, or read complete weight tensors.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from .entities import ModelFormat, ModelStatus

WEIGHT_PATTERNS = (
    "model.safetensors",
    "model-*.safetensors",
    "pytorch_model.bin",
    "pytorch_model-*.bin",
    "*.gguf",
)


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        return None, f"{path.name}: {exc}"
    if not isinstance(data, dict):
        return None, f"{path.name}: JSON 顶层必须是对象"
    return data, None


def directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def relative_files(path: Path, *, limit: int = 500) -> tuple[str, ...]:
    files: list[str] = []
    for item in path.rglob("*"):
        if len(files) >= limit:
            files.append("...")
            break
        try:
            if item.is_file():
                files.append(item.relative_to(path).as_posix())
        except OSError:
            continue
    return tuple(sorted(files))


def has_any_weight(path: Path) -> bool:
    if path.is_file() and path.suffix.lower() == ".gguf":
        return True
    for pattern in WEIGHT_PATTERNS:
        if any(path.glob(pattern)):
            return True
    return False


def infer_quantization(config: dict[str, Any] | None, quant_config: dict[str, Any] | None, path: Path) -> str | None:
    for data in (quant_config, (config or {}).get("quantization_config")):
        if isinstance(data, dict):
            method = data.get("quant_method") or data.get("bits") or data.get("w_bit")
            if method:
                return str(method)
    name = path.name.lower()
    for marker in ("q2", "q3", "q4", "q5", "q6", "q8", "4bit", "8bit", "gptq", "awq"):
        if marker in name:
            return marker
    return None


def detect_transformers_metadata(path: Path) -> dict[str, object]:
    errors: list[str] = []
    config, err = read_json(path / "config.json")
    if err:
        errors.append(err)
    quant_config = None
    for filename in ("quantize_config.json", "quant_config.json"):
        if (path / filename).exists():
            quant_config, quant_err = read_json(path / filename)
            if quant_err:
                errors.append(quant_err)
            break

    architecture = None
    context_length = None
    if config:
        architectures = config.get("architectures")
        if isinstance(architectures, list) and architectures:
            architecture = str(architectures[0])
        else:
            architecture = str(config.get("model_type")) if config.get("model_type") else None
        for key in ("max_position_embeddings", "max_sequence_length", "seq_length", "n_ctx"):
            if config.get(key):
                context_length = int(config[key])
                break

    fmt = ModelFormat.TRANSFORMERS
    if (path / "quantize_config.json").exists():
        fmt = ModelFormat.GPTQ
    if (path / "quant_config.json").exists() or any("awq" in f.name.lower() for f in path.glob("*")):
        fmt = ModelFormat.AWQ

    status = ModelStatus.READY if (config and has_any_weight(path)) else ModelStatus.INCOMPLETE
    if errors and not config:
        status = ModelStatus.CORRUPTED

    return {
        "format": fmt,
        "status": status,
        "architecture": architecture,
        "parameter_count": estimate_parameter_count_from_name(path.name),
        "quantization": infer_quantization(config, quant_config, path),
        "context_length": context_length,
        "errors": tuple(errors),
    }


def detect_gguf_metadata(path: Path) -> dict[str, object]:
    errors: list[str] = []
    architecture = None
    quantization = infer_quantization(None, None, path)
    context_length = None
    parameter_count = estimate_parameter_count_from_name(path.name)
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if len(header) < 16 or header[:4] != b"GGUF":
            errors.append("GGUF header 不完整或 magic 不匹配")
            status = ModelStatus.CORRUPTED
        else:
            _version, tensor_count, kv_count = struct.unpack("<IQQ", header[4:24])
            status = ModelStatus.READY
            if tensor_count <= 0:
                errors.append("GGUF tensor_count 为 0")
            if kv_count <= 0:
                errors.append("GGUF 元数据为空，已保留基础文件信息")
    except Exception as exc:
        errors.append(f"GGUF header 读取失败: {exc}")
        status = ModelStatus.CORRUPTED

    return {
        "format": ModelFormat.GGUF,
        "status": status,
        "architecture": architecture,
        "parameter_count": parameter_count,
        "quantization": quantization,
        "context_length": context_length,
        "errors": tuple(errors),
    }


def estimate_parameter_count_from_name(name: str) -> int | None:
    import re

    lowered = name.lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*b", lowered)
    if match:
        return int(float(match.group(1)) * 1_000_000_000)
    match = re.search(r"(\d+(?:\.\d+)?)\s*m", lowered)
    if match:
        return int(float(match.group(1)) * 1_000_000)
    return None
