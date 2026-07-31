"""TrainingRecipe recommendation without starting any training."""

from __future__ import annotations

from typing import Any

from llm_studio.api import errors as api_errors

from .formats import safe_recipe_method
from .recipe_estimators import estimate_train_time_minutes, estimate_vram_gb


class TrainingRecipeRecommender:
    def recommend(
        self,
        dataset_version: dict[str, Any],
        *,
        base_model_id: str | None = None,
        method: str | None = None,
        hardware: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hardware = hardware or {}
        preferences = preferences or {}
        gpu_vram = float(hardware.get("gpu_vram_gb") or 8)
        requested_method = safe_recipe_method(method or ("qlora" if gpu_vram <= 8 else "lora"))
        if gpu_vram <= 8:
            requested_method = "qlora"
        quality = str(preferences.get("quality") or "balanced")
        total_samples = int(dataset_version.get("train_sample_count") or 0) + int(
            dataset_version.get("val_sample_count") or 0
        )
        total_tokens = int(dataset_version.get("train_token_estimate") or 0) + int(
            dataset_version.get("val_token_estimate") or 0
        )
        epochs = 3
        if total_samples < 50:
            epochs = 4
        if total_tokens > 500_000:
            epochs = 2
        if quality == "fast":
            epochs = max(1, epochs - 1)
        elif quality == "quality":
            epochs += 1
        max_seq_length = int(preferences.get("max_seq_length") or 4096)
        max_seq_length = max(512, min(max_seq_length, 8192))
        lora_rank = 16 if requested_method == "qlora" else 8 if gpu_vram < 16 else 16
        config = {
            "epochs": epochs,
            "learning_rate": 0.0002 if requested_method == "qlora" else 0.0001,
            "lora_rank": lora_rank,
            "lora_alpha": lora_rank * 2,
            "lora_dropout": 0.05,
            "batch_size": 1,
            "gradient_accumulation_steps": 8 if gpu_vram <= 8 else 4,
            "max_seq_length": max_seq_length,
            "gradient_checkpointing": True,
            "warmup_ratio": 0.03,
            "save_steps": 200 if total_tokens > 500_000 else 100,
            "eval_steps": 200 if total_tokens > 500_000 else 100,
            "early_stopping_patience": 3,
        }
        warnings: list[dict[str, Any]] = []
        if total_samples < 50:
            warnings.append(
                {
                    "code": api_errors.DATASET_TOO_SMALL_FOR_TRAINING,
                    "message": "样本数量较少，训练容易过拟合；建议仅作为小规模实验。",
                }
            )
        if int(dataset_version.get("val_sample_count") or 0) == 0:
            warnings.append(
                {
                    "code": api_errors.DATASET_NO_VALIDATION_SPLIT,
                    "message": "当前 DatasetVersion 没有 validation split，训练时无法稳定监控泛化。",
                }
            )
        vram = estimate_vram_gb(
            method=requested_method,
            gpu_vram_gb=gpu_vram,
            max_seq_length=max_seq_length,
            lora_rank=lora_rank,
        )
        return {
            "dataset_version_id": dataset_version["dataset_version_id"],
            "base_model_id": base_model_id,
            "method": requested_method,
            "recommended_config": config,
            "user_config": {},
            "recommendation_reason": (
                f"Based on {total_samples} samples, {total_tokens} estimated tokens, "
                f"{gpu_vram:g}GB VRAM, and {quality} preference."
            ),
            "estimated_vram_gb": vram,
            "estimated_train_time_minutes": estimate_train_time_minutes(
                token_estimate=total_tokens,
                epochs=epochs,
                method=requested_method,
                hardware=hardware,
            ),
            "warnings": warnings,
            "status": "draft",
        }
