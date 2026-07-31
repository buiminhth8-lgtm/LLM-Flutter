"""Novel Studio Stage 6 Dataset Builder API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import DATASET_FEATURE_DISABLED, api_error
from llm_studio.datasets.errors import DatasetError
from llm_studio.datasets.schemas import (
    BulkCreateSamplesFromRevisionsRequest,
    CreateDatasetRequest,
    CreateSampleFromRevisionRequest,
    ExportDatasetRequest,
    FreezeDatasetRequest,
    RecommendRecipeRequest,
    RejectSampleRequest,
    UpdateDatasetRequest,
    UpdateRecipeRequest,
    UpdateSampleRequest,
)
from llm_studio.features import (
    is_dataset_builder_enabled,
    is_dataset_versioning_enabled,
    is_training_recipe_recommender_enabled,
)

router = APIRouter(prefix="/v1/datasets")


def _service(
    request: Request,
    *,
    require_versioning: bool = False,
    require_recipe: bool = False,
):
    state = get_api_state()
    if not is_dataset_builder_enabled(state.config):
        raise api_error(
            404,
            DATASET_FEATURE_DISABLED,
            "Dataset Builder is disabled. Enable Novel Studio, Revision, and dataset_builder.",
            getattr(request.state, "request_id", ""),
        )
    if require_versioning and not is_dataset_versioning_enabled(state.config):
        raise api_error(
            404,
            DATASET_FEATURE_DISABLED,
            "Dataset versioning is disabled. Enable dataset_versioning.",
            getattr(request.state, "request_id", ""),
        )
    if require_recipe and not is_training_recipe_recommender_enabled(state.config):
        raise api_error(
            404,
            DATASET_FEATURE_DISABLED,
            "Training recipe recommender is disabled.",
            getattr(request.state, "request_id", ""),
        )
    if state.dataset_service is None:
        raise api_error(
            500,
            "INTERNAL_ERROR",
            "Dataset service is not configured.",
            getattr(request.state, "request_id", ""),
        )
    return state.dataset_service


def _raise_dataset_error(request: Request, exc: DatasetError):
    raise api_error(
        exc.status_code,
        exc.code,
        exc.message,
        getattr(request.state, "request_id", ""),
    ) from exc


@router.get("")
async def list_datasets(
    request: Request,
    project_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_datasets(
                project_id=project_id,
                type=type,
                status=status,
                limit=limit,
                offset=offset,
            )
        }
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("")
async def create_dataset(request: Request, body: CreateDatasetRequest):
    try:
        return _service(request).create_dataset(body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/{dataset_id}")
async def get_dataset(request: Request, dataset_id: str):
    try:
        return _service(request).get_dataset(dataset_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.patch("/{dataset_id}")
async def update_dataset(
    request: Request,
    dataset_id: str,
    body: UpdateDatasetRequest,
):
    try:
        return _service(request).update_dataset(dataset_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.delete("/{dataset_id}")
async def archive_dataset(request: Request, dataset_id: str):
    try:
        return _service(request).archive_dataset(dataset_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/mark-ready")
async def mark_dataset_ready(request: Request, dataset_id: str):
    try:
        return _service(request, require_versioning=True).mark_ready(dataset_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/mark-dirty")
async def mark_dataset_dirty(request: Request, dataset_id: str):
    try:
        return _service(request, require_versioning=True).mark_dirty(dataset_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/freeze")
async def freeze_dataset(
    request: Request,
    dataset_id: str,
    body: FreezeDatasetRequest,
):
    try:
        return _service(request, require_versioning=True).freeze_dataset(dataset_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/{dataset_id}/versions")
async def list_dataset_versions(
    request: Request,
    dataset_id: str,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request, require_versioning=True).list_versions(
                dataset_id,
                limit=limit,
                offset=offset,
            )
        }
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/versions/{dataset_version_id}")
async def get_dataset_version(request: Request, dataset_version_id: str):
    try:
        return _service(request, require_versioning=True).get_version(dataset_version_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/versions/{dataset_version_id}/manifest")
async def get_dataset_manifest(request: Request, dataset_version_id: str):
    try:
        return _service(request, require_versioning=True).get_manifest(dataset_version_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/versions/{dataset_version_id}/samples")
async def list_dataset_version_samples(
    request: Request,
    dataset_version_id: str,
    split: str | None = None,
    has_warnings: bool | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request, require_versioning=True).list_version_samples(
                dataset_version_id,
                split=split,
                has_warnings=has_warnings,
                limit=limit,
                offset=offset,
            )
        }
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/versions/{dataset_version_id}/recommend-recipe")
async def recommend_training_recipe(
    request: Request,
    dataset_version_id: str,
    body: RecommendRecipeRequest,
):
    try:
        return _service(
            request,
            require_versioning=True,
            require_recipe=True,
        ).recommend_recipe(dataset_version_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/versions/{dataset_version_id}/recipes")
async def list_training_recipes(
    request: Request,
    dataset_version_id: str,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(
                request,
                require_versioning=True,
                require_recipe=True,
            ).list_recipes(dataset_version_id, limit=limit, offset=offset)
        }
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/recipes/{recipe_id}")
async def get_training_recipe(request: Request, recipe_id: str):
    try:
        return _service(request, require_recipe=True).get_recipe(recipe_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.patch("/recipes/{recipe_id}")
async def update_training_recipe(
    request: Request,
    recipe_id: str,
    body: UpdateRecipeRequest,
):
    try:
        return _service(request, require_recipe=True).update_recipe(recipe_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/recipes/{recipe_id}/confirm")
async def confirm_training_recipe(request: Request, recipe_id: str):
    try:
        return _service(request, require_recipe=True).confirm_recipe(recipe_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.delete("/recipes/{recipe_id}")
async def archive_training_recipe(request: Request, recipe_id: str):
    try:
        return _service(request, require_recipe=True).archive_recipe(recipe_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/samples/from-revision")
async def create_sample_from_revision(
    request: Request,
    dataset_id: str,
    body: CreateSampleFromRevisionRequest,
):
    try:
        return _service(request).create_sample_from_revision(
            dataset_id,
            body.revision_id,
            sample_type=body.sample_type,
        )
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/samples/bulk-from-revisions")
async def bulk_create_samples_from_revisions(
    request: Request,
    dataset_id: str,
    body: BulkCreateSamplesFromRevisionsRequest,
):
    try:
        return _service(request).bulk_create_samples_from_revisions(dataset_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/{dataset_id}/samples")
async def list_samples(
    request: Request,
    dataset_id: str,
    status: str | None = None,
    sample_type: str | None = None,
    revision_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {
            "data": _service(request).list_samples(
                dataset_id,
                status=status,
                sample_type=sample_type,
                revision_id=revision_id,
                limit=limit,
                offset=offset,
            )
        }
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/samples/{sample_id}")
async def get_sample(request: Request, sample_id: str):
    try:
        return _service(request).get_sample(sample_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.patch("/samples/{sample_id}")
async def update_sample(
    request: Request,
    sample_id: str,
    body: UpdateSampleRequest,
):
    try:
        return _service(request).update_sample(sample_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.delete("/samples/{sample_id}")
async def remove_sample(request: Request, sample_id: str):
    try:
        return _service(request).remove_sample(sample_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/samples/{sample_id}/approve")
async def approve_sample(request: Request, sample_id: str):
    try:
        return _service(request).approve_sample(sample_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/samples/{sample_id}/reject")
async def reject_sample(
    request: Request,
    sample_id: str,
    body: RejectSampleRequest | None = None,
):
    try:
        return _service(request).reject_sample(
            sample_id,
            reason=body.reason if body else None,
        )
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.post("/{dataset_id}/export")
async def export_dataset(
    request: Request,
    dataset_id: str,
    body: ExportDatasetRequest,
):
    try:
        return _service(request).export_dataset(dataset_id, body)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/{dataset_id}/exports")
async def list_exports(
    request: Request,
    dataset_id: str,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return {"data": _service(request).list_exports(dataset_id, limit=limit, offset=offset)}
    except DatasetError as exc:
        _raise_dataset_error(request, exc)


@router.get("/exports/{export_id}")
async def get_export(request: Request, export_id: str):
    try:
        return _service(request).get_export(export_id)
    except DatasetError as exc:
        _raise_dataset_error(request, exc)
