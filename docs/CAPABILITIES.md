# Capability Status

This document mirrors the backend `GET /v1/capabilities` endpoint. It is intentionally conservative: backend-only, partial, experimental, and not implemented features are not described as fully supported.

| Capability | Status | Frontend | Notes |
|---|---|---:|---|
| chat_non_stream | available | yes | Flutter sends the selected loaded model ID. |
| chat_stream | backend_only | no | SSE exists in the backend; Flutter still uses non-streaming chat. |
| model_scan | available | yes | Uses LocalModelRepository and does not load weights. |
| model_load | available | yes | Uses runtime policy and GPU scheduler. |
| model_unload | available | yes | Backend unloads and releases runtime state. |
| model_download | backend_only | no | Jobs run in backend and successful downloads are scanned into the repository. |
| model_download_cancel | partial | yes | Cancel is cooperative; current transfer may finish first. |
| model_download_resume | partial | no | Retry reuses Hugging Face cache; strict pause/resume is not claimed. |
| rag_query | backend_only | no | Backend endpoints exist. |
| rag_import | backend_only | no | Import runs as a background job. |
| vision_ocr | backend_only | no | Backend endpoints are GPU scheduled. |
| lora_scan | backend_only | no | Adapter scanning exists in backend. |
| lora_load | backend_only | no | Dynamic PEFT-compatible loading exists in backend. |
| lora_activate | backend_only | no | Activate/deactivate exists in backend. |
| lora_unload | backend_only | no | Backend can unload loaded adapters. |
| lora_merge | not_implemented | no | Endpoint creates a failed job; base models are not modified. |
| benchmark | experimental | no | Results are local development references only. |
| storage_cleanup | partial | no | Preview exists; cleanup only removes temporary categories. |
| diagnostics_export | backend_only | no | Redacted export excludes weights, secrets, chat, and document bodies. |
| windows_packaging | experimental | no | Launcher scripts exist; clean VM installer validation is not claimed. |
| flutter_windows | available | yes | Current supported desktop client. |
| flutter_android | not_implemented | no | Planned only. |
| flutter_linux | not_implemented | no | Planned only. |
| flutter_macos | not_implemented | no | Planned only. |
| flutter_web | not_implemented | no | Legacy web UI has been replaced by Flutter Windows. |
