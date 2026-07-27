# Low VRAM Fine-tuning Guide

RTX 5060 Laptop 8GB defaults:

```yaml
finetune:
  method: qlora
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 16
  max_seq_length: 1024
  gradient_checkpointing: true
  precision: auto
  target_modules: all-linear
```

Training data uses dynamic padding. Padding, system messages, and user prompts are masked with `-100`; assistant replies are supervised.

Risk levels:

- 1B-3B QLoRA: allowed for short validation.
- 7B/8B QLoRA: high risk on 8GB; use batch size 1 and short runs only.
- 14B+: unsupported by default on 8GB VRAM.

QLoRA dependency failures are not silently converted into full-precision training. Install CUDA optional dependencies first:

```powershell
.\scripts\install_optional_cuda.ps1
```
