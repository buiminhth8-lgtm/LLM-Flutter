"""Configuration management for LLM Studio."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "models_dir": "./models",
    "finetune_output_dir": "./finetuned_models",
    "datasets_dir": "./datasets",
    "inference": {
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "context_length": 4096,
    },
    "runtime": {
        "backend": "auto",
        "device": "auto",
        "dtype": "auto",
        "quantization": "auto",
        "attention_backend": "auto",
        "max_gpu_memory": "7GiB",
        "max_cpu_memory": "auto",
        "cpu_offload": True,
        "offload_folder": "./cache/offload",
        "trust_remote_code": False,
        "inference_concurrency": 1,
        "queue_limit": 8,
        "request_timeout_seconds": 300,
        "gpu_scheduler": {
            "enabled": True,
            "max_heavy_tasks": 1,
            "queue_timeout_seconds": 30,
        },
    },
    "generation": {
        "max_new_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repetition_penalty": 1.05,
        "do_sample": True,
        "max_context_tokens": 4096,
    },
    "llama_cpp": {
        "n_ctx": 4096,
        "n_gpu_layers": -1,
        "n_batch": 256,
        "n_ubatch": 128,
        "n_threads": 0,
        "flash_attn": True,
        "offload_kqv": True,
    },
    "rag": {
        "device": "cpu",
        "embedding_model": "BAAI/bge-small-zh-v1.5",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "top_k": 5,
        "index_path": "./data/rag",
    },
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
        "allowed_origins": [
            "http://127.0.0.1:5000",
            "http://localhost:5000",
            "http://127.0.0.1:8080",
            "http://localhost:8080",
        ],
    },
    "auth": {"enabled": True},
    "finetune": {
        "method": "qlora",
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": "all-linear",
        "learning_rate": 2e-4,
        "num_epochs": 3,
        "per_device_train_batch_size": 1,
        "batch_size": 1,
        "gradient_accumulation_steps": 16,
        "warmup_ratio": 0.03,
        "max_seq_length": 1024,
        "gradient_checkpointing": True,
        "precision": "auto",
        "save_steps": 100,
        "logging_steps": 5,
    },
    "model_registry": [],
    "vision_model_registry": [],
    "models": {
        "root_dir": "./data/models",
        "temp_dir": "./data/downloads",
        "metadata_cache": "./data/model_index.json",
        "adapters_dir": "./data/adapters",
        "allow_external_paths": True,
        "follow_symlinks": False,
        "minimum_free_space_gb": 10,
    },
    "huggingface": {
        "cache_dir": "./data/huggingface",
        "use_global_cache": False,
    },
    "storage": {
        "trash_dir": "./data/trash/models",
        "benchmarks_dir": "./data/benchmarks",
        "jobs_dir": "./data/jobs",
        "diagnostics_dir": "./data/diagnostics",
        "cleanup": {
            "enabled": True,
            "incomplete_download_days": 7,
            "benchmark_retention_days": 90,
            "trash_retention_days": 30,
            "logs_retention_days": 30,
        },
    },
    "uploads": {
        "temp_dir": "./data/uploads",
        "max_document_size_mb": 50,
        "max_image_size_mb": 20,
        "allowed_document_extensions": [".txt", ".md", ".pdf", ".docx"],
        "allowed_image_extensions": [".png", ".jpg", ".jpeg", ".webp"],
    },
    "execution": {
        "blocking_io_workers": 4,
        "cpu_workers": 2,
    },
}


def _deep_merge(defaults: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_default_config_path() -> Path:
    env_path = os.environ.get("LLM_STUDIO_CONFIG")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent.parent / "config.yaml"


def get_platform_info() -> dict:
    """Get current platform information."""
    import psutil

    gpu_info = "N/A"
    gpu_memory = 0
    cuda_available = False
    mps_available = False

    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_info = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_mem / (1024**3)
        mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except Exception:
        pass

    ram = psutil.virtual_memory()

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "ram_total_gb": round(ram.total / (1024 ** 3), 1),
        "ram_available_gb": round(ram.available / (1024 ** 3), 1),
        "cuda_available": cuda_available,
        "mps_available": mps_available,
        "gpu": gpu_info,
        "gpu_memory_gb": round(gpu_memory, 1),
    }


def get_device() -> str:
    """Get the best available compute device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        return "cpu"
    return "cpu"


class Config:
    """Application configuration loaded from YAML."""

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = get_default_config_path()
        self.config_path = Path(config_path)
        self._data = {}
        self.load()

    def load(self):
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                if not isinstance(loaded, dict):
                    raise ValueError("配置文件必须是 YAML 对象。")
                self._data = _deep_merge(DEFAULT_CONFIG, loaded)
        else:
            self._data = dict(DEFAULT_CONFIG)
        self._validate()
        self._resolve_paths()

    def _validate(self):
        runtime = self._data.get("runtime", {})
        if runtime.get("trust_remote_code") is True:
            # Explicitly allowed, but keep default false and warn through caller-visible config.
            pass
        quant = runtime.get("quantization", "auto")
        if quant not in {"auto", "none", "bnb4", "4bit", "bnb8", "8bit", "gguf"}:
            raise ValueError(f"runtime.quantization 无效: {quant}")
        if int(self._data.get("rag", {}).get("chunk_overlap", 0)) < 0:
            raise ValueError("rag.chunk_overlap 不能为负数。")
        if int(self._data.get("models", {}).get("minimum_free_space_gb", 0)) < 0:
            raise ValueError("models.minimum_free_space_gb 不能为负数。")

    def _resolve_paths(self):
        base = self.config_path.parent
        is_template_config = "configs" in {part.lower() for part in self.config_path.parts}
        if is_template_config:
            while base.name.lower() in {"configs", "presets"}:
                base = base.parent
        for key in ("models_dir", "finetune_output_dir", "datasets_dir"):
            val = self._data.get(key, f"./{key.replace('_dir', '')}")
            p = Path(val)
            if not p.is_absolute():
                p = base / p
            if not is_template_config:
                p.mkdir(parents=True, exist_ok=True)
            self._data[key] = str(p.resolve())
        for section, keys in {
            "models": ("root_dir", "temp_dir", "metadata_cache", "adapters_dir"),
            "huggingface": ("cache_dir",),
            "storage": ("trash_dir", "benchmarks_dir", "jobs_dir", "diagnostics_dir"),
            "uploads": ("temp_dir",),
        }.items():
            cfg = self._data.get(section, {})
            for key in keys:
                if key not in cfg:
                    continue
                p = Path(cfg[key])
                if not p.is_absolute():
                    p = base / p
                if not is_template_config:
                    if key in {
                        "root_dir",
                        "temp_dir",
                        "adapters_dir",
                        "cache_dir",
                        "trash_dir",
                        "benchmarks_dir",
                        "jobs_dir",
                        "diagnostics_dir",
                    }:
                        p.mkdir(parents=True, exist_ok=True)
                    else:
                        p.parent.mkdir(parents=True, exist_ok=True)
                cfg[key] = str(p.resolve())

    @property
    def models_dir(self) -> Path:
        models_cfg = self._data.get("models", {})
        return Path(models_cfg.get("root_dir") or self._data["models_dir"])

    @property
    def finetune_output_dir(self) -> Path:
        return Path(self._data["finetune_output_dir"])

    @property
    def datasets_dir(self) -> Path:
        return Path(self._data["datasets_dir"])

    @property
    def inference(self) -> dict:
        return self._data.get("inference", {})

    @property
    def runtime(self) -> dict:
        return self._data.get("runtime", {})

    @property
    def generation(self) -> dict:
        return self._data.get("generation", {})

    @property
    def finetune(self) -> dict:
        return self._data.get("finetune", {})

    @property
    def model_registry(self) -> list:
        return self._data.get("model_registry", [])

    def get(self, key, default=None):
        return self._data.get(key, default)
