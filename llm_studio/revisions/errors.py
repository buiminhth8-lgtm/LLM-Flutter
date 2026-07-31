"""Stable errors for Novel Studio revisions."""

from __future__ import annotations

from llm_studio.api import errors as api_errors


class RevisionError(ValueError):
    code = api_errors.REVISION_NOT_FOUND
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class RevisionNotFoundError(RevisionError):
    code = api_errors.REVISION_NOT_FOUND
    status_code = 404

    def __init__(self, revision_id: str):
        super().__init__(f"Revision not found: {revision_id}")


class RevisionRelatedNotFoundError(RevisionError):
    status_code = 404

    def __init__(self, kind: str, item_id: str):
        codes = {
            "project": api_errors.REVISION_PROJECT_NOT_FOUND,
            "chapter": api_errors.REVISION_CHAPTER_NOT_FOUND,
            "generation": api_errors.REVISION_GENERATION_NOT_FOUND,
        }
        self.code = codes.get(kind, api_errors.REVISION_NOT_FOUND)
        super().__init__(f"Revision {kind} not found: {item_id}")


class RevisionOriginalTextEmptyError(RevisionError):
    code = api_errors.REVISION_ORIGINAL_TEXT_EMPTY


class RevisionEditedTextEmptyError(RevisionError):
    code = api_errors.REVISION_EDITED_TEXT_EMPTY


class RevisionInvalidTagError(RevisionError):
    code = api_errors.REVISION_INVALID_TAG

    def __init__(self, tag: str):
        super().__init__(f"Unknown revision edit tag: {tag}")


class RevisionInvalidScoreError(RevisionError):
    code = api_errors.REVISION_INVALID_SCORE


class RevisionInvalidStatusError(RevisionError):
    code = api_errors.REVISION_INVALID_STATUS


class RevisionDiffFailedError(RevisionError):
    code = api_errors.REVISION_DIFF_FAILED
    status_code = 500


class RevisionConflictError(RevisionError):
    code = api_errors.REVISION_CONFLICT
    status_code = 409


class RevisionAutosaveError(RevisionError):
    code = api_errors.REVISION_AUTOSAVE_FAILED
    status_code = 500
