from tests.test_revision_service import _revision_seed


def test_revision_autosave_does_not_change_revision_text(tmp_path):
    revisions, _, _, project, chapter, generation = _revision_seed(tmp_path)
    revision = revisions.create_from_generation(
        {
            "generation_id": generation["generation_id"],
            "edited_text": "formal edited",
        }
    )

    autosave = revisions.autosave_revision(
        {
            "revision_id": revision["revision_id"],
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "generation_id": generation["generation_id"],
            "draft_text": "typing draft",
            "base_text_hash": revision["edited_hash"],
            "client_revision": 3,
        }
    )

    assert autosave["draft_text"] == "typing draft"
    assert autosave["client_revision"] == 3
    assert revisions.get_revision(revision["revision_id"])["edited_text"] == "formal edited"
    assert len(revisions.list_autosaves(revision["revision_id"])) == 1
