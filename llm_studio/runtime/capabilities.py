"""Runtime capability probes for local inference backends."""

from __future__ import annotations

import importlib.util
import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeCapabilities:
    python_version: str
    torch_version: str | None
    cuda_available: bool
    cuda_runtime: str | None
    gpu_name: str | None
    compute_capability: tuple[int, int] | None
    total_vram_bytes: int | None
    bf16_supported: bool
    bitsandbytes_installed: bool
    bitsandbytes_4bit_usable: bool
    llama_cpp_installed: bool
    llama_cpp_cuda_enabled: bool
    gptqmodel_installed: bool
    bitsandbytes_error: str | None = None
    llama_cpp_error: str | None = None


def _module_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def probe_bitsandbytes_4bit() -> tuple[bool, str | None]:
    """Run a minimal CUDA 4-bit probe without executing during module import."""
    if not _module_installed("bitsandbytes"):
        return False, "bitsandbytes is not installed"
    try:
        import torch

        if not torch.cuda.is_available():
            return False, "CUDA is unavailable"

        from bitsandbytes.nn import Linear4bit

        layer = Linear4bit(4, 4, bias=False, compute_dtype=torch.float16, quant_type="nf4").cuda()
        layer.load_state_dict({"weight": torch.randn(4, 4, device="cuda", dtype=torch.float16)})
        _ = layer(torch.randn(1, 4, device="cuda", dtype=torch.float16))
        torch.cuda.synchronize()
        return True, None
    except Exception as exc:
        return False, str(exc)


def detect_llama_cpp_cuda() -> tuple[bool, str]:
    """Detect whether llama-cpp-python appears to be built with CUDA support."""
    if not _module_installed("llama_cpp"):
        return False, "llama-cpp-python is not installed"
    try:
        import llama_cpp

        info_func = getattr(llama_cpp, "llama_print_system_info", None)
        if info_func is None:
            return False, "llama_print_system_info is unavailable"
        info = info_func()
        if isinstance(info, bytes):
            info = info.decode("utf-8", errors="replace")
        text = str(info).lower()
        cuda_markers = ("cuda = 1", "cublas = 1", "ggml_cuda", "cuda")
        enabled = any(marker in text for marker in cuda_markers)
        return enabled, str(info)
    except Exception as exc:
        return False, str(exc)


def detect_runtime_capabilities(run_bnb_probe: bool = True) -> RuntimeCapabilities:
    torch_version = None
    cuda_available = False
    cuda_runtime = None
    gpu_name = None
    compute_capability = None
    total_vram_bytes = None
    bf16_supported = False

    try:
        import torch

        torch_version = torch.__version__
        cuda_runtime = torch.version.cuda
        cuda_available = bool(torch.cuda.is_available())
        if cuda_available:
            idx = 0
            gpu_name = torch.cuda.get_device_name(idx)
            props = torch.cuda.get_device_properties(idx)
            total_vram_bytes = int(props.total_memory)
            compute_capability = tuple(torch.cuda.get_device_capability(idx))
            try:
                bf16_supported = bool(torch.cuda.is_bf16_supported())
            except Exception:
                bf16_supported = bool(compute_capability and compute_capability >= (8, 0))
    except Exception:
        pass

    bnb_installed = _module_installed("bitsandbytes")
    bnb_usable = False
    bnb_error = None
    if run_bnb_probe and bnb_installed:
        bnb_usable, bnb_error = probe_bitsandbytes_4bit()
    elif not bnb_installed:
        bnb_error = "bitsandbytes is not installed"

    llama_installed = _module_installed("llama_cpp")
    llama_cuda, llama_error = detect_llama_cpp_cuda() if llama_installed else (False, "llama-cpp-python is not installed")

    return RuntimeCapabilities(
        python_version=platform.python_version(),
        torch_version=torch_version,
        cuda_available=cuda_available,
        cuda_runtime=cuda_runtime,
        gpu_name=gpu_name,
        compute_capability=compute_capability,
        total_vram_bytes=total_vram_bytes,
        bf16_supported=bf16_supported,
        bitsandbytes_installed=bnb_installed,
        bitsandbytes_4bit_usable=bnb_usable,
        llama_cpp_installed=llama_installed,
        llama_cpp_cuda_enabled=llama_cuda,
        gptqmodel_installed=_module_installed("gptqmodel"),
        bitsandbytes_error=bnb_error,
        llama_cpp_error=llama_error,
    )
