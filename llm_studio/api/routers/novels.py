"""Novel Studio stage 1 API router."""

from __future__ import annotations

from fastapi import APIRouter, Request

from llm_studio.api.deps import get_api_state
from llm_studio.api.errors import NOVEL_FEATURE_DISABLED, api_error
from llm_studio.features import is_novel_studio_enabled
from llm_studio.novels.errors import NovelError
from llm_studio.novels.schemas import (
    ChapterCreateRequest,
    ChapterUpdateRequest,
    CharacterCreateRequest,
    CharacterUpdateRequest,
    PlotThreadCreateRequest,
    PlotThreadUpdateRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    SceneCreateRequest,
    SceneUpdateRequest,
    TimelineEventCreateRequest,
    TimelineEventUpdateRequest,
    VolumeCreateRequest,
    VolumeUpdateRequest,
    WorldEntryCreateRequest,
    WorldEntryUpdateRequest,
)

router = APIRouter(prefix="/v1/novels")


def _service(request: Request):
    state = get_api_state()
    if not is_novel_studio_enabled(state.config):
        raise api_error(
            404,
            NOVEL_FEATURE_DISABLED,
            "Novel Studio is disabled. Enable features.novel_studio.enabled to use Stage 1 APIs.",
            getattr(request.state, "request_id", ""),
        )
    if state.novel_service is None:
        raise api_error(500, "INTERNAL_ERROR", "Novel service is not configured.", getattr(request.state, "request_id", ""))
    return state.novel_service


def _handle(request: Request, action):
    try:
        return action()
    except NovelError as exc:
        raise api_error(exc.status_code, exc.code, exc.message, getattr(request.state, "request_id", "")) from exc


@router.get("/projects")
async def list_projects(request: Request, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_projects(limit=limit, offset=offset))}


@router.post("/projects")
async def create_project(request: Request, body: ProjectCreateRequest):
    return _handle(request, lambda: _service(request).create_project(body))


@router.get("/projects/{project_id}")
async def get_project(request: Request, project_id: str):
    return _handle(request, lambda: _service(request).get_project(project_id))


@router.patch("/projects/{project_id}")
async def update_project(request: Request, project_id: str, body: ProjectUpdateRequest):
    return _handle(request, lambda: _service(request).update_project(project_id, body))


@router.delete("/projects/{project_id}")
async def delete_project(request: Request, project_id: str):
    return _handle(request, lambda: _service(request).delete_project(project_id))


@router.get("/projects/{project_id}/volumes")
async def list_volumes(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_volumes(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/volumes")
async def create_volume(request: Request, project_id: str, body: VolumeCreateRequest):
    return _handle(request, lambda: _service(request).create_volume(project_id, body))


@router.patch("/volumes/{volume_id}")
async def update_volume(request: Request, volume_id: str, body: VolumeUpdateRequest):
    return _handle(request, lambda: _service(request).update_volume(volume_id, body))


@router.delete("/volumes/{volume_id}")
async def delete_volume(request: Request, volume_id: str):
    return _handle(request, lambda: _service(request).delete_volume(volume_id))


@router.get("/projects/{project_id}/chapters")
async def list_chapters(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_chapters(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/chapters")
async def create_chapter(request: Request, project_id: str, body: ChapterCreateRequest):
    return _handle(request, lambda: _service(request).create_chapter(project_id, body))


@router.get("/chapters/{chapter_id}")
async def get_chapter(request: Request, chapter_id: str):
    return _handle(request, lambda: _service(request).get_chapter(chapter_id))


@router.patch("/chapters/{chapter_id}")
async def update_chapter(request: Request, chapter_id: str, body: ChapterUpdateRequest):
    return _handle(request, lambda: _service(request).update_chapter(chapter_id, body))


@router.delete("/chapters/{chapter_id}")
async def delete_chapter(request: Request, chapter_id: str):
    return _handle(request, lambda: _service(request).delete_chapter(chapter_id))


@router.get("/chapters/{chapter_id}/scenes")
async def list_scenes(request: Request, chapter_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_scenes(chapter_id, limit=limit, offset=offset))}


@router.post("/chapters/{chapter_id}/scenes")
async def create_scene(request: Request, chapter_id: str, body: SceneCreateRequest):
    return _handle(request, lambda: _service(request).create_scene(chapter_id, body))


@router.patch("/scenes/{scene_id}")
async def update_scene(request: Request, scene_id: str, body: SceneUpdateRequest):
    return _handle(request, lambda: _service(request).update_scene(scene_id, body))


@router.delete("/scenes/{scene_id}")
async def delete_scene(request: Request, scene_id: str):
    return _handle(request, lambda: _service(request).delete_scene(scene_id))


@router.get("/projects/{project_id}/characters")
async def list_characters(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_characters(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/characters")
async def create_character(request: Request, project_id: str, body: CharacterCreateRequest):
    return _handle(request, lambda: _service(request).create_character(project_id, body))


@router.patch("/characters/{character_id}")
async def update_character(request: Request, character_id: str, body: CharacterUpdateRequest):
    return _handle(request, lambda: _service(request).update_character(character_id, body))


@router.delete("/characters/{character_id}")
async def delete_character(request: Request, character_id: str):
    return _handle(request, lambda: _service(request).delete_character(character_id))


@router.get("/projects/{project_id}/world")
async def list_world_entries(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_world_entries(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/world")
async def create_world_entry(request: Request, project_id: str, body: WorldEntryCreateRequest):
    return _handle(request, lambda: _service(request).create_world_entry(project_id, body))


@router.patch("/world/{entry_id}")
async def update_world_entry(request: Request, entry_id: str, body: WorldEntryUpdateRequest):
    return _handle(request, lambda: _service(request).update_world_entry(entry_id, body))


@router.delete("/world/{entry_id}")
async def delete_world_entry(request: Request, entry_id: str):
    return _handle(request, lambda: _service(request).delete_world_entry(entry_id))


@router.get("/projects/{project_id}/plot-threads")
async def list_plot_threads(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_plot_threads(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/plot-threads")
async def create_plot_thread(request: Request, project_id: str, body: PlotThreadCreateRequest):
    return _handle(request, lambda: _service(request).create_plot_thread(project_id, body))


@router.patch("/plot-threads/{thread_id}")
async def update_plot_thread(request: Request, thread_id: str, body: PlotThreadUpdateRequest):
    return _handle(request, lambda: _service(request).update_plot_thread(thread_id, body))


@router.delete("/plot-threads/{thread_id}")
async def delete_plot_thread(request: Request, thread_id: str):
    return _handle(request, lambda: _service(request).delete_plot_thread(thread_id))


@router.get("/projects/{project_id}/timeline")
async def list_timeline(request: Request, project_id: str, limit: int = 50, offset: int = 0):
    return {"data": _handle(request, lambda: _service(request).list_timeline(project_id, limit=limit, offset=offset))}


@router.post("/projects/{project_id}/timeline")
async def create_timeline_event(request: Request, project_id: str, body: TimelineEventCreateRequest):
    return _handle(request, lambda: _service(request).create_timeline_event(project_id, body))


@router.patch("/timeline/{event_id}")
async def update_timeline_event(request: Request, event_id: str, body: TimelineEventUpdateRequest):
    return _handle(request, lambda: _service(request).update_timeline_event(event_id, body))


@router.delete("/timeline/{event_id}")
async def delete_timeline_event(request: Request, event_id: str):
    return _handle(request, lambda: _service(request).delete_timeline_event(event_id))
