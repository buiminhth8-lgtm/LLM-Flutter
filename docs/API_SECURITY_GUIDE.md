# API Security Guide

Security defaults:

- `trust_remote_code: false`
- API host defaults to `127.0.0.1`
- CORS uses explicit `api.allowed_origins`
- `allow_origins=["*"]` with credentials is rejected
- Admin password is stored as Argon2id
- API keys are stored as SHA-256 hashes
- Full API keys are returned only on creation or regeneration

Set the first admin password:

```powershell
$env:LLM_STUDIO_INITIAL_ADMIN_PASSWORD = "use-a-long-random-password"
python -m llm_studio.cli serve
```

Do not log Authorization headers, cookies, passwords, or full API keys. Use `redact_secret()` for diagnostics.
