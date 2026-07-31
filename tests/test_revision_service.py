from __future__ import annotations

import asyncio
import sqlite3

import pytest

from llm_studio.revisions import RevisionService
from llm_studio.revisions.errors import (
    RevisionConflictError,
    RevisionEditedTextEmptyError,
    RevisionOriginalTextEmptyError,
    RevisionRelatedNotFoundError,
)
from tests.test_writing_service import _seed


def _revision_seed(tmp_path):
    novels, prompts, context, writing, runtime, project, chapter, template, request = _seed(tmp_path)
    result = asyncio.run(writing.generate(request))
    revisions = RevisionService(
        writing.db_path,
        novel_service=novels,
        writing_service=writing,
    )
    return revisions, novels, writing, project, chapter, result


def test_create_revision_from_generation_and_update_conflict(tmp_path):
    revisions, _, writing, project, chapter, generation = _revision_seed(tmp_path)

    revision = revisions.create_from_generation(
        {
            "generation_id": generation["generation_id"],
            "edited_text": "edited text",
            "edit_tags": ["language_polish", "detail_expand"],
            "user_score": 4,
            "accepted_for_dataset": True,
        }
    )

    assert revision["source"] == "generation"
    assert revision["project_id"] == project["id"]
    assert revision["chapter_id"] == chapter["id"]
    assert revision["generation_id"] == generation["generation_id"]
    assert revision["original_text"] == writing.get_generation(generation["generation_id"])["model_output"]
    assert revision["edited_text"] == "edited text"
    assert revision["diff"]["summary"]["changed_blocks"] >= 1
    assert revision["original_hash"]
    assert revision["edited_hash"]

    updated = revisions.update_revision(
        revision["revision_id"],
        {
            "edited_text": "edited text plus",
            "expected_updated_at": revision["updated_at"],
        },
    )
    assert updated["edited_text"] == "edited text plus"

    with pytest.raises(RevisionConflictError):
        revisions.update_revision(
            revision["revision_id"],
            {
                "edited_text": "stale",
                "expected_updated_at": revision["updated_at"],
            },
        )


def test_generation_missing_and_empty_text_errors(tmp_path):
    revisions, _, writing, *_ = _revision_seed(tmp_path)

    with pytest.raises(RevisionRelatedNotFoundError):
        revisions.create_from_generation({"generation_id": "missing"})

    empty = writing.records.create(
        {
            "project_id": "project",
            "model_id": "model",
            "mode": "chapter_generate",
            "prompt_rendered": "prompt",
            "status": "succeeded",
            "model_output": "",
        }
    )
    with pytest.raises(RevisionOriginalTextEmptyError):
        revisions.create_from_generation({"generation_id": empty["generation_id"]})


def test_create_revision_from_chapter_draft_and_manual(tmp_path):
    revisions, novels, _, project, chapter, _ = _revision_seed(tmp_path)

    draft = revisions.create_from_chapter_draft(
        {
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "edited_text": "draft edited",
            "user_score": 3,
            "accepted_for_dataset": True,
        }
    )
    assert draft["source"] == "chapter_draft"
    assert draft["warnings"][0]["code"] == "REVISION_LOW_SCORE_DATASET_CANDIDATE"

    manual = revisions.create_manual(
        {
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "original_text": "manual original",
            "edited_text": "manual edited",
        }
    )
    assert manual["source"] == "manual"

    with pytest.raises(RevisionEditedTextEmptyError):
        revisions.create_manual(
            {
                "project_id": project["id"],
                "original_text": "manual original",
                "edited_text": " ",
            }
        )
    assert novels.get_chapter(chapter["id"]).get("final_content") in {None, ""}


def test_revision_review_status_archive_and_dataset_boundary(tmp_path):
    revisions, _, _, project, _, generation = _revision_seed(tmp_path)
    revision = revisions.create_from_generation({"generation_id": generation["generation_id"]})

    approved = revisions.approve_revision(revision["revision_id"])
    assert approved["status"] == "approved"
    assert revisions.mark_dataset_candidate(revision["revision_id"], True)["accepted_for_dataset"] is True
    rejected = revisions.reject_revision(revision["revision_id"], reason="not enough detail")
    assert rejected["status"] == "rejected"
    archived = revisions.archive_revision(revision["revision_id"])
    assert archived["status"] == "archived"

    with sqlite3.connect(revisions.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "training_samples" not in tables
    assert revisions.list_revisions(project_id=project["id"])[0]["status"] == "archived"
