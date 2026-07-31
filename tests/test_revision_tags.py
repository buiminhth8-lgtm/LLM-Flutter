import pytest

from llm_studio.revisions.errors import RevisionInvalidTagError
from llm_studio.revisions.tags import EDIT_TAG_LABELS, validate_edit_tags


def test_revision_tags_validate_and_dedupe():
    assert "language_polish" in EDIT_TAG_LABELS
    assert validate_edit_tags(["language_polish", "detail_expand", "language_polish"]) == [
        "language_polish",
        "detail_expand",
    ]


def test_revision_unknown_tag_is_rejected():
    with pytest.raises(RevisionInvalidTagError):
        validate_edit_tags(["unknown"])
