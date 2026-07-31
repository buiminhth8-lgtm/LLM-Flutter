# Novel Studio Writing

Stage 4 connects the Stage 3 Context Assembler and Stage 2 PromptRenderer to
the existing local model Runtime. It records model generations and can save a
successful output to a chapter draft or summary.

This module does not implement revisions, diffs, datasets, fine-tuning, RAG,
or evaluation. It never writes `final_content`.

Module responsibilities:

- `service.py`: validates requests, calls Context Assembler and PromptRenderer,
  orchestrates Runtime generation, and persists terminal state.
- `runtime_bridge.py`: reuses the application's runner resolver, inference
  concurrency gate, GPU Scheduler, Adapter manager, and cancellation token.
- `repository.py` / `migrations.py`: own only `generation_records`.
- `generation_modes.py` / `length_control.py`: validate Stage 4 modes and
  Chinese-focused output length behavior.
- `stream.py`: serializes stable SSE events and stop-sequence helpers.

`Save to Draft` is not a Revision. Human edits, diffs, dataset candidates,
training samples, and any `final_content` workflow belong to later stages.
