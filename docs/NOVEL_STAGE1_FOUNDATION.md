# Novel Studio Stage 1 Foundation

Stage 1 adds the local Novel Studio foundation library on top of the existing
LLM-Studio backend and Flutter Windows client. It does not connect model
generation, Prompt Studio, WritingService, Revision, Dataset, or FineTune flows.

## Scope

- Novel projects
- Volumes
- Chapters
- Scenes
- Characters
- World bible entries
- Plot threads
- Timeline events
- SQLite repository and service layer
- `/v1/novels/*` API guarded by `features.novel_studio.enabled`
- Flutter Novel Studio project list and basic detail page

## SQLite Tables

- `novel_projects`
- `novel_volumes`
- `novel_chapters`
- `novel_scenes`
- `novel_characters`
- `novel_world_entries`
- `novel_plot_threads`
- `novel_timeline_events`

The database path is configured by:

```yaml
novels:
  db_path: "./data/novels/novels.sqlite"
```

Migrations use `CREATE TABLE IF NOT EXISTS` and do not modify existing
non-`novel_*` tables.

## API Routes

Projects:

- `GET /v1/novels/projects`
- `POST /v1/novels/projects`
- `GET /v1/novels/projects/{project_id}`
- `PATCH /v1/novels/projects/{project_id}`
- `DELETE /v1/novels/projects/{project_id}`

Foundation resources:

- `GET|POST /v1/novels/projects/{project_id}/volumes`
- `PATCH|DELETE /v1/novels/volumes/{volume_id}`
- `GET|POST /v1/novels/projects/{project_id}/chapters`
- `GET|PATCH|DELETE /v1/novels/chapters/{chapter_id}`
- `GET|POST /v1/novels/chapters/{chapter_id}/scenes`
- `PATCH|DELETE /v1/novels/scenes/{scene_id}`
- `GET|POST /v1/novels/projects/{project_id}/characters`
- `PATCH|DELETE /v1/novels/characters/{character_id}`
- `GET|POST /v1/novels/projects/{project_id}/world`
- `PATCH|DELETE /v1/novels/world/{entry_id}`
- `GET|POST /v1/novels/projects/{project_id}/plot-threads`
- `PATCH|DELETE /v1/novels/plot-threads/{thread_id}`
- `GET|POST /v1/novels/projects/{project_id}/timeline`
- `PATCH|DELETE /v1/novels/timeline/{event_id}`

## Permissions

- `viewer`: read-only Novel APIs.
- `operator`: create and update Novel records.
- `admin`: create, update, and soft-delete Novel records.

Stage 1 uses coarse Novel permissions first. More granular project ownership
can be added in a later stage.

## Error Codes

- `NOVEL_FEATURE_DISABLED`
- `NOVEL_PROJECT_NOT_FOUND`
- `NOVEL_VOLUME_NOT_FOUND`
- `NOVEL_CHAPTER_NOT_FOUND`
- `NOVEL_SCENE_NOT_FOUND`
- `NOVEL_CHARACTER_NOT_FOUND`
- `NOVEL_WORLD_ENTRY_NOT_FOUND`
- `NOVEL_PLOT_THREAD_NOT_FOUND`
- `NOVEL_TIMELINE_EVENT_NOT_FOUND`
- `NOVEL_VALIDATION_FAILED`
- `NOVEL_DUPLICATE_SLUG`

## Flutter UI

The Flutter Windows client shows `Novel Studio` only when backend capabilities
report:

```json
{"name": "novel_studio", "status": "partial", "frontend_exposed": true}
```

Implemented UI surfaces:

- Project list
- Create project
- Project overview
- Chapter list and create chapter
- Character list and create character
- World bible list and create entry

Planned UI surfaces:

- Full volume editor
- Full scene editor
- Plot thread editor
- Timeline editor

## Not Included

- Prompt Studio
- PromptRenderer
- WritingService
- AI generation or Runtime/Runner calls
- Revision records
- Dataset Builder
- Dataset version freezing
- FineTune / LoRA / QLoRA workflows

## Stage 2 Prerequisites

Before Stage 2, define the Prompt Studio template schema, variable model,
preview contract, permission rules, and test fixtures. Do not connect prompt
rendering to Runtime until the Writing stage explicitly starts.
