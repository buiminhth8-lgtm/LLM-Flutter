"""Capability status values exposed to clients and documentation."""

from __future__ import annotations

from enum import StrEnum


class CapabilityStatus(StrEnum):
    AVAILABLE = "available"
    BACKEND_ONLY = "backend_only"
    EXPERIMENTAL = "experimental"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    DISABLED = "disabled"
