import pytest

from llm_studio.memory.errors import MemoryInvalidSourceTypeError, MemoryInvalidStatusError
from llm_studio.memory.sources import (
    SOURCE_TYPES,
    parse_tags,
    validate_document_status,
    validate_source_type,
)


def test_memory_source_types_include_stage10_sources():
    assert "chapter" in SOURCE_TYPES
    assert "revision" in SOURCE_TYPES
    assert "adapter_eval_result" in SOURCE_TYPES
    assert validate_source_type("world_entry") == "world_entry"


def test_memory_source_validation_rejects_unknown_source():
    with pytest.raises(MemoryInvalidSourceTypeError):
        validate_source_type("vector_db")


def test_memory_status_validation_and_tags():
    assert validate_document_status("stale") == "stale"
    with pytest.raises(MemoryInvalidStatusError):
        validate_document_status("removed")
    assert parse_tags("黑市, 灵骨，伏笔") == ["黑市", "灵骨", "伏笔"]

