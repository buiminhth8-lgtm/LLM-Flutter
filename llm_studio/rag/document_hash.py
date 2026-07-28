"""Document hashing helpers."""

from __future__ import annotations

import hashlib
import re


def normalize_content(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def document_hash(content: str) -> str:
    return hashlib.sha256(normalize_content(content).encode("utf-8")).hexdigest()
