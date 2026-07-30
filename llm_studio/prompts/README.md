# Prompt Studio Stage 2

This module stores prompt templates, immutable template versions, variable
schemas, preview render records, and default global templates.

Stage 2 deliberately does not call Runtime or Runner, generate novel text,
create WritingService, create Revision/Dataset/FineTune workflows, or connect
to RAG/Memory. Rendering is limited to safe `{{variable}}` substitution for
preview and later-stage orchestration.
