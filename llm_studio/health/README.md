# Stage 12 Health Checks

The health module is a read-only productization layer for the Windows desktop
release. It verifies that the server, configuration, managed storage, SQLite
database, capability registry, JobQueue, model repository, and adapter
repository are reachable.

It does not load models, start training, run RAG indexing, mutate novel text, or
perform any long-running task.
