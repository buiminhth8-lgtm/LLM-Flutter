"""API error helpers with stable error codes."""

from __future__ import annotations

from fastapi import HTTPException

MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
MODEL_LOADING = "MODEL_LOADING"
QUEUE_FULL = "QUEUE_FULL"
GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
GENERATION_CANCELLED = "GENERATION_CANCELLED"
CUDA_OUT_OF_MEMORY = "CUDA_OUT_OF_MEMORY"
INVALID_MESSAGES = "INVALID_MESSAGES"
RAG_INDEX_INVALID = "RAG_INDEX_INVALID"
DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
UNAUTHORIZED = "UNAUTHORIZED"
AUTH_REQUIRED = "AUTH_REQUIRED"
PERMISSION_DENIED = "PERMISSION_DENIED"
UPLOAD_FILENAME_INVALID = "UPLOAD_FILENAME_INVALID"
UPLOAD_EXTENSION_NOT_ALLOWED = "UPLOAD_EXTENSION_NOT_ALLOWED"
UPLOAD_FILE_TOO_LARGE = "UPLOAD_FILE_TOO_LARGE"
UPLOAD_SAVE_FAILED = "UPLOAD_SAVE_FAILED"
UPLOAD_TYPE_NOT_SUPPORTED = "UPLOAD_TYPE_NOT_SUPPORTED"
ASYNC_TASK_FAILED = "ASYNC_TASK_FAILED"
GPU_BUSY = "GPU_BUSY"
GPU_TASK_TIMEOUT = "GPU_TASK_TIMEOUT"
MODEL_LOAD_BUSY = "MODEL_LOAD_BUSY"
BENCHMARK_OOM = "BENCHMARK_OOM"


def error_payload(code: str, message: str, request_id: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }


def api_error(status_code: int, code: str, message: str, request_id: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=error_payload(code, message, request_id),
    )
