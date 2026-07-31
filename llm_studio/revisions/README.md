# Novel Studio Stage 5 Revisions

Stage 5 adds human revision records on top of Stage 4 generation history.

Boundaries:

- Reads `generation_records.model_output` as immutable model original text.
- Stores `original_text`, `edited_text`, backend-generated `diff_json`, edit tags,
  user score, review status, and the `accepted_for_dataset` candidate flag.
- Stores autosaves separately in `revision_autosaves`; autosaves never update
  formal revision text and never enter dataset flows.
- Archives revisions by setting `status=archived`; records are not physically
  deleted by the API.
- Does not create training samples, dataset versions, SFT JSONL, adapter
  evaluations, RAG memory, or model generation calls.

The `accepted_for_dataset` field is only a future Stage 6 candidate marker.
