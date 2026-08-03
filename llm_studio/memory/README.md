# llm_studio.memory

Novel Studio Stage 10 adds long-form novel Memory / RAG on top of Stages 1-9.

The package stores Memory documents, chunks, keyword/SQLite FTS index entries,
retrieval traces, and chapter summary versions. Retrieval is performed in the
backend and may be injected into Stage 3 `ContextAssembler` variables through
the Context Memory Bridge.

Boundaries:

- No full automatic Evaluation Center.
- No automatic style, character consistency, or plot coherence scoring.
- No LoRA / QLoRA training is launched here.
- No DPO / RLHF implementation.
- No external vector database is required.
- Embedding retrieval is a reserved interface; keyword and optional SQLite FTS
  are the Stage 10 default.

