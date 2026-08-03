"""Fine-tune preflight checks for Stage 8."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path
from typing import Any

from llm_studio.datasets.errors import DatasetRecipeNotFoundError, DatasetVersionNotFoundError
from llm_studio.models.entities import ModelFormat, ModelStatus
from llm_studio.models.exceptions import InvalidModelPathError
from llm_studio.models.storage import ensure_within

from . import errors as err

ADAPTER_NAME_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def default_dependency_checker(method: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    required = ["torch", "transformers", "peft", "datasets"]
    if method == "qlora":
        required.append("bitsandbytes")
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        errors.append(
            {
                "code": err.FineTuneDependencyMissingError.code,
                "message": f"缺少训练依赖: {', '.join(missing)}。请安装 CUDA/finetune 依赖后再使用真实训练。",
            }
        )
        return errors, warnings
    try:
        import torch

        if not torch.cuda.is_available():
            errors.append(
                {
                    "code": err.FineTuneGpuNotAvailableError.code,
                    "message": "未检测到可用 CUDA GPU；真实 LoRA/QLoRA 训练不会在 API 线程内降级伪造。",
                }
            )
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(
            {
                "code": err.FineTuneDependencyMissingError.code,
                "message": f"训练依赖检查失败: {type(exc).__name__}",
            }
        )
    return errors, warnings


class FineTunePreflight:
    def __init__(
        self,
        *,
        dataset_service: Any,
        model_repository: Any,
        adapter_repository: Any | None,
        output_root: str | Path,
        default_config: dict[str, Any] | None = None,
        use_fake_trainer: bool = False,
        dependency_checker=default_dependency_checker,
    ):
        self.dataset_service = dataset_service
        self.model_repository = model_repository
        self.adapter_repository = adapter_repository
        self.output_root = Path(output_root).resolve()
        self.default_config = default_config or {}
        self.use_fake_trainer = use_fake_trainer
        self.dependency_checker = dependency_checker

    def run(self, request: Any, *, raise_on_error: bool = False) -> dict[str, Any]:
        data = self._model_dump(request)
        dataset_version_id = str(data.get("dataset_version_id") or "").strip()
        recipe_id = str(data.get("recipe_id") or "").strip()
        base_model_id = str(data.get("base_model_id") or "").strip()
        adapter_name = str(data.get("adapter_name") or "").strip()
        version = self._dataset_version(dataset_version_id)
        if version["status"] != "frozen":
            raise err.FineTuneDatasetVersionNotFrozenError("DatasetVersion must be frozen before training.")
        recipe = self._recipe(recipe_id)
        if recipe["status"] != "confirmed":
            raise err.FineTuneRecipeNotConfirmedError("TrainingRecipe must be confirmed before training.")
        if recipe["dataset_version_id"] != dataset_version_id:
            raise err.FineTuneRecipeDatasetMismatchError("TrainingRecipe belongs to a different DatasetVersion.")
        self._validate_adapter_name(adapter_name)
        self._assert_adapter_name_available(adapter_name)
        model = self._model(base_model_id)
        self._assert_model_trainable(model)
        manifest = self._manifest(version)
        dataset_paths = self._dataset_paths(version)
        resolved_config = self._resolved_config(recipe, data, model=model, dataset_paths=dataset_paths)
        errors, warnings = self._config_warnings(version, resolved_config, dataset_paths)
        if not self.use_fake_trainer:
            dep_errors, dep_warnings = self.dependency_checker(resolved_config["method"])
            errors.extend(dep_errors)
            warnings.extend(dep_warnings)
        try:
            self.output_root.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(self.output_root).free
            min_bytes = int(float(self.default_config.get("minimum_free_space_gb") or 0) * (1024**3))
            if min_bytes and free < min_bytes:
                errors.append(
                    {
                        "code": err.FineTuneInsufficientVramError.code,
                        "message": "训练输出目录所在磁盘空间不足。",
                    }
                )
        except OSError as exc:
            errors.append(
                {
                    "code": err.FineTuneOutputPathInvalidError.code,
                    "message": f"训练输出目录不可写: {type(exc).__name__}",
                }
            )
        result = {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "resolved_config": self._public_config(resolved_config),
            "dataset_version": version,
            "training_recipe": recipe,
            "dataset_manifest": manifest,
            "_dataset_paths": dataset_paths,
            "_model_path": str(model.path),
        }
        if raise_on_error and errors:
            first = errors[0]
            raise err.FineTunePreflightFailedError(
                first.get("message") or "Fine-tune preflight failed.",
                details={"errors": errors, "warnings": warnings},
            )
        return result

    def _dataset_version(self, dataset_version_id: str) -> dict[str, Any]:
        try:
            return self.dataset_service.records.get_dataset_version(dataset_version_id)
        except DatasetVersionNotFoundError as exc:
            raise err.FineTuneDatasetVersionNotFoundError(dataset_version_id) from exc

    def _recipe(self, recipe_id: str) -> dict[str, Any]:
        try:
            return self.dataset_service.records.get_training_recipe(recipe_id)
        except DatasetRecipeNotFoundError as exc:
            raise err.FineTuneRecipeNotFoundError(recipe_id) from exc

    def _model(self, base_model_id: str):
        try:
            return self.model_repository.get(base_model_id)
        except (InvalidModelPathError, Exception) as exc:
            if isinstance(exc, err.FineTuneError):
                raise
            raise err.FineTuneBaseModelNotFoundError(base_model_id) from exc

    @staticmethod
    def _assert_model_trainable(model: Any) -> None:
        status = getattr(model, "status", None)
        status_value = getattr(status, "value", status)
        if status_value and status_value != ModelStatus.READY.value:
            raise err.FineTuneBaseModelNotSupportedError("Base model is not ready for training.")
        fmt = getattr(model, "format", None)
        fmt_value = getattr(fmt, "value", fmt)
        if fmt_value and fmt_value != ModelFormat.TRANSFORMERS.value:
            raise err.FineTuneBaseModelNotSupportedError("Stage 8 training requires a Transformers-format base model.")

    @staticmethod
    def _validate_adapter_name(adapter_name: str) -> None:
        if not adapter_name or len(adapter_name) > 80:
            raise err.FineTuneAdapterNameInvalidError("adapter_name must be 1-80 characters.")
        if adapter_name in {".", ".."} or ".." in adapter_name or ADAPTER_NAME_FORBIDDEN.search(adapter_name):
            raise err.FineTuneAdapterNameInvalidError("adapter_name cannot contain path separators or unsafe characters.")

    def _assert_adapter_name_available(self, adapter_name: str) -> None:
        if self.adapter_repository is None:
            return
        try:
            for adapter in self.adapter_repository.list():
                if adapter.name == adapter_name:
                    raise err.FineTuneAdapterNameConflictError(
                        f"Adapter name already exists: {adapter_name}"
                    )
        except err.FineTuneAdapterNameConflictError:
            raise
        except Exception:
            return

    def _manifest(self, version: dict[str, Any]) -> dict[str, Any]:
        try:
            manifest = self.dataset_service.get_manifest(version["dataset_version_id"])
        except Exception as exc:
            raise err.FineTuneDatasetManifestNotFoundError("Dataset manifest not found.") from exc
        if manifest.get("dataset_version_id") != version["dataset_version_id"]:
            raise err.FineTuneDatasetManifestInvalidError("Dataset manifest version mismatch.")
        if (manifest.get("hashes") or {}).get("content_hash") != version.get("content_hash"):
            raise err.FineTuneDatasetManifestInvalidError("Dataset manifest content_hash mismatch.")
        text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        if "api_key" in text.lower() or ":\\" in text or "/Users/" in text or "/home/" in text:
            raise err.FineTuneDatasetManifestInvalidError("Dataset manifest contains unsafe path or secret data.")
        return manifest

    def _dataset_paths(self, version: dict[str, Any]) -> dict[str, str | None]:
        root = Path(self.dataset_service.export_root).resolve().parent
        train = ensure_within(root / version["train_path"], root)
        if not train.exists():
            raise err.FineTuneTrainFileNotFoundError("train.jsonl was not found for DatasetVersion.")
        val_path = version.get("val_path")
        val = ensure_within(root / val_path, root) if val_path else None
        if val is not None and not val.exists():
            raise err.FineTuneDatasetManifestInvalidError("val.jsonl is referenced but missing.")
        return {"train": str(train), "val": str(val) if val else None}

    def _resolved_config(
        self,
        recipe: dict[str, Any],
        request: dict[str, Any],
        *,
        model: Any,
        dataset_paths: dict[str, str | None],
    ) -> dict[str, Any]:
        method = str(recipe.get("method") or "qlora")
        if method not in {"lora", "qlora"}:
            raise err.FineTuneInvalidMethodError(method)
        raw = {
            **self.default_config,
            **(recipe.get("recommended_config") or {}),
            **(recipe.get("user_config") or {}),
        }
        if "epochs" in raw and "num_epochs" not in raw:
            raw["num_epochs"] = raw["epochs"]
        if "lora_rank" in raw and "lora_r" not in raw:
            raw["lora_r"] = raw["lora_rank"]
        return {
            **raw,
            "method": method,
            "dataset_version_id": recipe["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": request["base_model_id"],
            "adapter_name": request["adapter_name"],
            "model_path": str(model.path),
            "train_path": dataset_paths["train"],
            "val_path": dataset_paths.get("val"),
        }

    @staticmethod
    def _config_warnings(
        version: dict[str, Any],
        config: dict[str, Any],
        dataset_paths: dict[str, str | None],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []
        if int(version.get("train_sample_count") or 0) <= 0:
            errors.append(
                {
                    "code": err.FineTuneInvalidConfigError.code,
                    "message": "DatasetVersion must contain at least one train sample.",
                }
            )
        method = str(config.get("method") or "")
        if method not in {"lora", "qlora"}:
            errors.append({"code": err.FineTuneInvalidMethodError.code, "message": "method must be lora or qlora."})
        for key in ("max_seq_length", "batch_size", "gradient_accumulation_steps"):
            value = int(config.get(key) or 0)
            if value <= 0:
                errors.append(
                    {
                        "code": err.FineTuneInvalidConfigError.code,
                        "message": f"{key} must be a positive integer.",
                    }
                )
        if float(config.get("learning_rate") or 0) <= 0:
            errors.append(
                {
                    "code": err.FineTuneInvalidConfigError.code,
                    "message": "learning_rate must be positive.",
                }
            )
        if not dataset_paths.get("val"):
            config["early_stopping_patience"] = None
            warnings.append(
                {
                    "code": "FINETUNE_NO_VALIDATION_SPLIT",
                    "message": "该 DatasetVersion 没有验证集，将禁用 early stopping。",
                }
            )
        return errors, warnings

    @staticmethod
    def _public_config(config: dict[str, Any]) -> dict[str, Any]:
        blocked = {"model_path", "train_path", "val_path", "adapter_output_dir", "run_dir", "resume_from_checkpoint_path"}
        return {key: value for key, value in config.items() if key not in blocked and "api_key" not in key.lower()}

    @staticmethod
    def _model_dump(value: Any) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            return value.model_dump(exclude_unset=True)
        if hasattr(value, "dict"):
            return value.dict(exclude_unset=True)
        return dict(value)
