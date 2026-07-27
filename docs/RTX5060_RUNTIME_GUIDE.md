# RTX 5060 Laptop 8GB Runtime Guide

Recommended environment:

- Windows 11 x64
- Python 3.12 x64
- CUDA PyTorch installed with `scripts/install_windows_cuda.ps1`
- `trust_remote_code: false`

Run diagnostics:

```powershell
python -m llm_studio.runtime.diagnostics
python -m llm_studio.cli doctor
```

Default runtime policy:

- 1B-3B Transformers models: BF16 when supported, otherwise FP16.
- 7B/8B models: prefer 4-bit if bitsandbytes probe passes, otherwise BF16/FP16 with offload or GGUF.
- 14B and larger: not loaded as full GPU models by default on 8GB VRAM.
- `attention_backend: sdpa` on CUDA unless a model requires fallback.
- `max_gpu_memory: 7GiB` reserves roughly 1GiB for runtime headroom.

Concurrency:

- GPU inference concurrency defaults to `1`.
- Queue limit defaults to `8`.
- Queue full returns `QUEUE_FULL`.

Manual validation should record model name, dtype, quantization, attention backend, peak VRAM, first token latency, and tokens/sec. Do not report GPU validation as passed unless it was run on the target machine.
