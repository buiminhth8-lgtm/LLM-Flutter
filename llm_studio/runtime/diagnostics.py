"""CLI diagnostics for the local runtime environment."""

from __future__ import annotations

from .capabilities import detect_runtime_capabilities
from .device_info import bytes_to_gib
from ..config import Config


def main() -> int:
    caps = detect_runtime_capabilities()
    print(f"Python: {caps.python_version}")
    print(f"PyTorch: {caps.torch_version or 'not installed'}")
    print(f"CUDA runtime: {caps.cuda_runtime or 'N/A'}")
    print(f"CUDA available: {caps.cuda_available}")
    print(f"GPU: {caps.gpu_name or 'N/A'}")
    print(f"Compute capability: {caps.compute_capability or 'N/A'}")
    print(f"VRAM: {bytes_to_gib(caps.total_vram_bytes)}")
    print(f"BF16: {caps.bf16_supported}")
    print(
        "bitsandbytes: "
        f"{'installed' if caps.bitsandbytes_installed else 'not installed'}, "
        f"{'usable' if caps.bitsandbytes_4bit_usable else 'not usable'}"
    )
    if caps.bitsandbytes_error:
        print(f"bitsandbytes detail: {caps.bitsandbytes_error}")
    print(
        "llama.cpp CUDA: "
        f"{'yes' if caps.llama_cpp_cuda_enabled else 'no'}"
    )
    if caps.llama_cpp_error:
        print(f"llama.cpp detail: {caps.llama_cpp_error}")
    print(f"GPTQModel: {'yes' if caps.gptqmodel_installed else 'no'}")
    try:
        config = Config()
        print(f"Max context: {config.generation.get('max_context_tokens', 'N/A')}")
        print(f"Inference concurrency: {config.runtime.get('inference_concurrency', 1)}")
        print(f"Queue size: {config.runtime.get('queue_limit', 8)}")
        print(f"RAG embedding device: {config.get('rag', {}).get('device', 'cpu')}")
        print(f"trust_remote_code: {config.runtime.get('trust_remote_code', False)}")
        print("Chat template availability: model-specific (checked during load)")
        print("Fine-tune support: run doctor for risk checks")
        print("Security: admin password Argon2id, API keys SHA-256")
    except Exception as exc:
        print(f"Config diagnostics: failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
