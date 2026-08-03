# Novel Studio Stage 10: RAG / Memory

Stage 10 adds long-form novel Memory / RAG on top of Stages 1-9. It stores
novel facts as backend-managed memory documents, chunks them deterministically,
builds local keyword / optional SQLite FTS indexes, records retrieval traces,
and can inject budgeted `retrieved_memory` into Stage 3 `ContextAssembler`.

## Scope

- Build memory from chapters, scenes, characters, world entries, plot threads,
  timeline events, revisions, and optionally generations / adapter evaluation
  results.
- Create manual memory notes.
- Rebuild a project or document index.
- Preview retrieval results with scores and explain fields.
- Persist retrieval records for prompt-debugging.
- Maintain chapter summary versions, manually or through the existing
  `WritingRuntimeBridge`.
- Extend Writing Workspace with Memory controls.

## Memory / RAG and ContextAssembler

Flutter does not run retrieval locally. It sends a `memory` object to
`/v1/context/render-preview` or `/v1/writing/*`. When `memory.enabled=false`,
Stage 3 behavior is unchanged. When enabled, the backend retrieves memory,
formats it as variables such as `retrieved_memory`, and trims lower-scored
chunks if the ContextAssembler budget is exceeded.

## Tables

### memory_documents

Stores source-level memory assets:

- `source_type`: `chapter`, `scene`, `character`, `world_entry`,
  `plot_thread`, `timeline_event`, `revision`, `generation`,
  `adapter_eval_result`, `manual_note`, `foreshadowing`.
- `source_id`: source record id.
- `content_hash`: sha256 used to detect changed source content.
- `status`: `active`, `stale`, `archived`, `deleted`.

### memory_chunks

Stores backend-generated chunks for each document. `chunk_index` starts at 0,
empty text is skipped, and metadata retains title/source fields.

### memory_index_entries

Stores keyword index entries and optional `sqlite_fts` entries. The
`embedding_stub` path is reserved; Stage 10 does not require cloud embeddings or
an external vector database.

### memory_retrieval_records

Stores query text, mode, top-k, budget, retrieved chunks, selected chunks,
warnings, and total token estimate. These traces explain why a prompt saw
specific memory.

### chapter_summary_versions

Stores immutable summary versions per chapter and summary type. Activating a
summary can sync it to `novel_chapters.summary`; old versions are retained.

## Source rules

- `revision_records.edited_text` has higher priority than
  `generation_records.model_output`.
- `final_content` has higher priority than `draft_content`.
- `generation_records` and `adapter_evaluation_results` are excluded by default
  from build-from-novel.
- `archived` / `deleted` sources are skipped by default.
- Manual notes have high user priority.

## Chunking

The default chunk size is 1200 non-whitespace characters with 120 characters of
overlap. Characters, world entries, plot threads, timeline events, scenes, and
manual notes usually become one chunk unless they exceed the configured size.
Long chapter text is split by paragraphs and then by character count.

## Indexing

`MemoryIndexService` rebuilds all active/stale documents in a project or a
single document. Rebuilds are idempotent: old chunks and index entries for the
document are replaced. SQLite FTS5 is detected at runtime. If unavailable, the
system returns warnings and continues with keyword retrieval.

## Retrieval and ranking

Retrieval ranks backend chunks with:

- keyword match score;
- source type boost;
- user priority boost;
- chapter / scene direct relation boost;
- stable tie-breaking by priority, updated_at, title, and chunk index.

The selected chunk list respects `max_memory_tokens` and `max_chunks`.

## Context Memory Bridge

Enabled requests add these variables:

- `retrieved_memory`
- `retrieved_characters`
- `retrieved_world_entries`
- `retrieved_plot_threads`
- `retrieved_timeline_events`
- `retrieved_foreshadowing`
- `memory_warnings`

`context_assembly_records.retrieval_id` stores the associated retrieval trace.

## Chapter summary rules

Manual summaries are stored as `generated_by=manual`. Model summaries reuse the
existing `WritingRuntimeBridge`; tests use fake runtime and never load a real
model. Generated summaries default to draft unless `set_active=true`.

## API summary

- `GET/POST/PATCH/DELETE /v1/memory/documents`
- `POST /v1/memory/projects/{project_id}/build-from-novel`
- `POST /v1/memory/projects/{project_id}/index/rebuild`
- `GET /v1/memory/projects/{project_id}/index/status`
- `POST /v1/memory/documents/{document_id}/index/rebuild`
- `POST /v1/memory/retrieve`
- `GET /v1/memory/retrieval-records`
- `GET /v1/memory/retrieval-records/{retrieval_id}`
- `GET/POST /v1/memory/chapters/{chapter_id}/summaries`
- `POST /v1/memory/chapters/{chapter_id}/summaries/generate`
- `POST /v1/memory/chapters/{chapter_id}/summaries/{summary_id}/activate`

## Flutter

Stage 10 adds:

- Memory Center page for project filters, documents, build, rebuild, manual
  notes, index status, retrieval preview, and summaries.
- Retrieval Preview page/widget showing chunks, source, score, selected chunks,
  warnings, and copied-friendly retrieved memory text.
- Chapter Summary page/widget for manual creation, model generation, and
  activation.
- Writing Workspace Memory controls: enable switch, top-k, max memory tokens,
  source type chips, and Show Retrieved Memory.

## Not included

- Full automatic Evaluation Center.
- Automatic literary quality, style, character consistency, or plot coherence
  scoring.
- LoRA / QLoRA training.
- DPO / RLHF.
- External vector database dependency such as Milvus, Chroma, FAISS, or
  Pinecone.
- Cloud embedding requirement.

## Stage 11 prerequisites

Stage 11 can build on retrieval traces and memory previews to add a separate
Evaluation Center, but must keep automatic scoring distinct from Stage 10
memory retrieval.

