"""Stable Memory / RAG errors for Novel Studio Stage 10."""

from __future__ import annotations

from llm_studio.api import errors as api_errors


class MemoryError(ValueError):
    code = api_errors.MEMORY_RETRIEVE_FAILED
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MemoryFeatureDisabledError(MemoryError):
    code = api_errors.MEMORY_FEATURE_DISABLED
    status_code = 404


class MemoryProjectNotFoundError(MemoryError):
    code = api_errors.MEMORY_PROJECT_NOT_FOUND
    status_code = 404

    def __init__(self, project_id: str):
        super().__init__(f"Memory project not found: {project_id}")


class MemoryDocumentNotFoundError(MemoryError):
    code = api_errors.MEMORY_DOCUMENT_NOT_FOUND
    status_code = 404

    def __init__(self, document_id: str):
        super().__init__(f"Memory document not found: {document_id}")


class MemoryChunkNotFoundError(MemoryError):
    code = api_errors.MEMORY_CHUNK_NOT_FOUND
    status_code = 404

    def __init__(self, chunk_id: str):
        super().__init__(f"Memory chunk not found: {chunk_id}")


class MemorySourceNotFoundError(MemoryError):
    code = api_errors.MEMORY_SOURCE_NOT_FOUND
    status_code = 404


class MemoryInvalidSourceTypeError(MemoryError):
    code = api_errors.MEMORY_INVALID_SOURCE_TYPE

    def __init__(self, source_type: str):
        super().__init__(f"Invalid memory source_type: {source_type}")


class MemoryInvalidStatusError(MemoryError):
    code = api_errors.MEMORY_INVALID_STATUS

    def __init__(self, status: str):
        super().__init__(f"Invalid memory status: {status}")


class MemoryIndexFailedError(MemoryError):
    code = api_errors.MEMORY_INDEX_FAILED
    status_code = 500


class MemoryIndexNotAvailableError(MemoryError):
    code = api_errors.MEMORY_INDEX_NOT_AVAILABLE


class MemoryFtsNotAvailableError(MemoryError):
    code = api_errors.MEMORY_FTS_NOT_AVAILABLE


class MemoryRetrieveFailedError(MemoryError):
    code = api_errors.MEMORY_RETRIEVE_FAILED
    status_code = 500


class MemoryRetrievalRecordNotFoundError(MemoryError):
    code = api_errors.MEMORY_RETRIEVAL_RECORD_NOT_FOUND
    status_code = 404

    def __init__(self, retrieval_id: str):
        super().__init__(f"Memory retrieval record not found: {retrieval_id}")


class MemoryBudgetExceededError(MemoryError):
    code = api_errors.MEMORY_BUDGET_EXCEEDED


class MemorySummaryNotFoundError(MemoryError):
    code = api_errors.MEMORY_SUMMARY_NOT_FOUND
    status_code = 404

    def __init__(self, summary_id: str):
        super().__init__(f"Chapter summary not found: {summary_id}")


class MemorySummaryEmptyError(MemoryError):
    code = api_errors.MEMORY_SUMMARY_EMPTY


class MemorySummaryGenerateFailedError(MemoryError):
    code = api_errors.MEMORY_SUMMARY_GENERATE_FAILED
    status_code = 500


class MemoryModelNotFoundError(MemoryError):
    code = api_errors.MEMORY_MODEL_NOT_FOUND
    status_code = 404


class MemoryModelNotLoadedError(MemoryError):
    code = api_errors.MEMORY_MODEL_NOT_LOADED


class MemoryContextBridgeFailedError(MemoryError):
    code = api_errors.MEMORY_CONTEXT_BRIDGE_FAILED
    status_code = 500

