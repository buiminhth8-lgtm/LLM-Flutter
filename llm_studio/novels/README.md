# llm_studio.novels

Novel Studio Stage 1 foundation module.

This package contains:

- SQLite migrations for `novel_*` tables.
- Repository classes for project, volume, chapter, scene, character, world
  entry, plot thread, and timeline CRUD.
- A service layer for validation, slug generation, parent-child consistency,
  word count updates, and soft deletes.
- API schemas used by `llm_studio/api/routers/novels.py`.

This package does not contain:

- Prompt Studio.
- PromptRenderer.
- WritingService.
- Revision or Dataset logic.
- Runtime / Runner calls.
- FineTune / LoRA / QLoRA workflows.
