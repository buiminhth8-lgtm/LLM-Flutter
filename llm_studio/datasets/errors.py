"""Stable errors for Novel Studio Dataset Builder."""

from __future__ import annotations

from llm_studio.api import errors as api_errors


class DatasetError(ValueError):
    code = api_errors.DATASET_NOT_FOUND
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DatasetNotFoundError(DatasetError):
    code = api_errors.DATASET_NOT_FOUND
    status_code = 404

    def __init__(self, dataset_id: str):
        super().__init__(f"Dataset not found: {dataset_id}")


class DatasetSampleNotFoundError(DatasetError):
    code = api_errors.DATASET_SAMPLE_NOT_FOUND
    status_code = 404

    def __init__(self, sample_id: str):
        super().__init__(f"Training sample not found: {sample_id}")


class DatasetExportNotFoundError(DatasetError):
    code = api_errors.DATASET_EXPORT_NOT_FOUND
    status_code = 404

    def __init__(self, export_id: str):
        super().__init__(f"Dataset export not found: {export_id}")


class DatasetProjectNotFoundError(DatasetError):
    code = api_errors.DATASET_PROJECT_NOT_FOUND
    status_code = 404

    def __init__(self, project_id: str):
        super().__init__(f"Dataset project not found: {project_id}")


class DatasetRevisionNotFoundError(DatasetError):
    code = api_errors.DATASET_REVISION_NOT_FOUND
    status_code = 404

    def __init__(self, revision_id: str):
        super().__init__(f"Dataset revision not found: {revision_id}")


class DatasetRevisionNotAcceptedError(DatasetError):
    code = api_errors.DATASET_REVISION_NOT_ACCEPTED
    status_code = 400


class DatasetRevisionNotApprovedWarning(DatasetError):
    code = api_errors.DATASET_REVISION_NOT_APPROVED
    status_code = 400


class DatasetInvalidTypeError(DatasetError):
    code = api_errors.DATASET_INVALID_TYPE

    def __init__(self, value: str):
        super().__init__(f"Unsupported dataset type: {value}")


class DatasetInvalidStatusError(DatasetError):
    code = api_errors.DATASET_INVALID_STATUS

    def __init__(self, value: str):
        super().__init__(f"Unsupported dataset status: {value}")


class DatasetInvalidSampleTypeError(DatasetError):
    code = api_errors.DATASET_INVALID_SAMPLE_TYPE

    def __init__(self, value: str):
        super().__init__(f"Unsupported training sample type: {value}")


class DatasetInvalidExportFormatError(DatasetError):
    code = api_errors.DATASET_INVALID_EXPORT_FORMAT

    def __init__(self, value: str):
        super().__init__(f"Unsupported dataset export format: {value}")


class DatasetSampleEmptyInstructionError(DatasetError):
    code = api_errors.DATASET_SAMPLE_EMPTY_INSTRUCTION


class DatasetSampleEmptyOutputError(DatasetError):
    code = api_errors.DATASET_SAMPLE_EMPTY_OUTPUT


class DatasetSampleDuplicateError(DatasetError):
    code = api_errors.DATASET_SAMPLE_DUPLICATE
    status_code = 409


class DatasetSampleUnchangedError(DatasetError):
    code = api_errors.DATASET_SAMPLE_UNCHANGED_FROM_ORIGINAL


class DatasetNoApprovedSamplesError(DatasetError):
    code = api_errors.DATASET_NO_APPROVED_SAMPLES


class DatasetExportFailedError(DatasetError):
    code = api_errors.DATASET_EXPORT_FAILED
    status_code = 500


class DatasetExportPathInvalidError(DatasetError):
    code = api_errors.DATASET_EXPORT_PATH_INVALID


class DatasetVersionNotImplementedError(DatasetError):
    code = api_errors.DATASET_VERSION_NOT_IMPLEMENTED
    status_code = 501

    def __init__(self):
        super().__init__("DatasetVersion and frozen datasets are planned for Stage 7.")
