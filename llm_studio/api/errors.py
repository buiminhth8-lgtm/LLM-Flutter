"""API error helpers with stable error codes."""

from __future__ import annotations

from fastapi import HTTPException


MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
MODEL_LOADING = "MODEL_LOADING"
QUEUE_FULL = "QUEUE_FULL"
GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
GENERATION_CANCELLED = "GENERATION_CANCELLED"
CUDA_OUT_OF_MEMORY = "CUDA_OUT_OF_MEMORY"
INVALID_MESSAGES = "INVALID_MESSAGES"
RAG_INDEX_INVALID = "RAG_INDEX_INVALID"
DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
UNAUTHORIZED = "UNAUTHORIZED"


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
