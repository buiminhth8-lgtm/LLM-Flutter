# RAG Guide

RAG settings live in `config.yaml`:

```yaml
rag:
  embedding_model: BAAI/bge-small-zh-v1.5
  device: cpu
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
  index_path: ./data/rag
```

On RTX 5060 Laptop 8GB, embeddings default to CPU so the main model keeps GPU memory.

Chunking order:

1. Paragraph boundaries.
2. Chinese and English sentence punctuation.
3. Fixed length fallback with overlap.

The index stores:

- `schema_version`
- `embedding_model`
- `embedding_dimension`
- `created_at`
- document and chunk counts

Loading refuses incompatible model or dimension metadata and asks for rebuild instead of returning incorrect retrieval results.
