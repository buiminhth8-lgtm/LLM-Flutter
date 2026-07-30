# Context Assembler

This module implements Novel Studio Stage 3.

It selects Stage 1 novel records, applies deterministic priority and budget
rules, and produces variables compatible with the Stage 2 `PromptRenderer`.
It does not call Runtime or Runner, generate prose, use RAG/vector search, save
revisions, or build datasets.
