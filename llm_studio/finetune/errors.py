"""Stable errors for Novel Studio Stage 8 Fine-tune Center."""

from __future__ import annotations


class FineTuneError(RuntimeError):
    code = "FINETUNE_PREFLIGHT_FAILED"
    status_code = 400

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FineTuneFeatureDisabledError(FineTuneError):
    code = "FINETUNE_FEATURE_DISABLED"
    status_code = 404


class FineTuneRunNotFoundError(FineTuneError):
    code = "FINETUNE_RUN_NOT_FOUND"
    status_code = 404


class FineTuneDatasetVersionNotFoundError(FineTuneError):
    code = "FINETUNE_DATASET_VERSION_NOT_FOUND"
    status_code = 404


class FineTuneDatasetVersionNotFrozenError(FineTuneError):
    code = "FINETUNE_DATASET_VERSION_NOT_FROZEN"


class FineTuneDatasetManifestNotFoundError(FineTuneError):
    code = "FINETUNE_DATASET_MANIFEST_NOT_FOUND"
    status_code = 404


class FineTuneDatasetManifestInvalidError(FineTuneError):
    code = "FINETUNE_DATASET_MANIFEST_INVALID"


class FineTuneTrainFileNotFoundError(FineTuneError):
    code = "FINETUNE_TRAIN_FILE_NOT_FOUND"
    status_code = 404


class FineTuneRecipeNotFoundError(FineTuneError):
    code = "FINETUNE_RECIPE_NOT_FOUND"
    status_code = 404


class FineTuneRecipeNotConfirmedError(FineTuneError):
    code = "FINETUNE_RECIPE_NOT_CONFIRMED"


class FineTuneRecipeDatasetMismatchError(FineTuneError):
    code = "FINETUNE_RECIPE_DATASET_MISMATCH"


class FineTuneBaseModelNotFoundError(FineTuneError):
    code = "FINETUNE_BASE_MODEL_NOT_FOUND"
    status_code = 404


class FineTuneBaseModelNotSupportedError(FineTuneError):
    code = "FINETUNE_BASE_MODEL_NOT_SUPPORTED"


class FineTuneAdapterNameInvalidError(FineTuneError):
    code = "FINETUNE_ADAPTER_NAME_INVALID"


class FineTuneAdapterNameConflictError(FineTuneError):
    code = "FINETUNE_ADAPTER_NAME_CONFLICT"
    status_code = 409


class FineTuneInvalidMethodError(FineTuneError):
    code = "FINETUNE_INVALID_METHOD"


class FineTuneInvalidConfigError(FineTuneError):
    code = "FINETUNE_INVALID_CONFIG"


class FineTuneDependencyMissingError(FineTuneError):
    code = "FINETUNE_DEPENDENCY_MISSING"


class FineTuneGpuNotAvailableError(FineTuneError):
    code = "FINETUNE_GPU_NOT_AVAILABLE"
    status_code = 409


class FineTuneInsufficientVramError(FineTuneError):
    code = "FINETUNE_INSUFFICIENT_VRAM"
    status_code = 409


class FineTuneOutputPathInvalidError(FineTuneError):
    code = "FINETUNE_OUTPUT_PATH_INVALID"


class FineTunePreflightFailedError(FineTuneError):
    code = "FINETUNE_PREFLIGHT_FAILED"


class FineTuneJobCreateFailedError(FineTuneError):
    code = "FINETUNE_JOB_CREATE_FAILED"
    status_code = 500


class FineTuneTrainingFailedError(FineTuneError):
    code = "FINETUNE_TRAINING_FAILED"
    status_code = 500


class FineTuneCancelNotSupportedError(FineTuneError):
    code = "FINETUNE_CANCEL_NOT_SUPPORTED"
    status_code = 409


class FineTuneCheckpointNotFoundError(FineTuneError):
    code = "FINETUNE_CHECKPOINT_NOT_FOUND"
    status_code = 404


class FineTuneResumeFailedError(FineTuneError):
    code = "FINETUNE_RESUME_FAILED"


class FineTuneAdapterExportFailedError(FineTuneError):
    code = "FINETUNE_ADAPTER_EXPORT_FAILED"
    status_code = 500


class FineTuneAdapterRegisterFailedError(FineTuneError):
    code = "FINETUNE_ADAPTER_REGISTER_FAILED"
    status_code = 500


class FineTunePermissionDeniedError(FineTuneError):
    code = "FINETUNE_PERMISSION_DENIED"
    status_code = 403
