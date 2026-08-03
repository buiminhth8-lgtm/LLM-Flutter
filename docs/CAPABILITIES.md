# 能力状态

真实能力以运行时接口为准：

```powershell
curl http://127.0.0.1:8000/v1/capabilities
```

## Stage 12 productization capabilities

- `version_api`: available; `/v1/version` exposes local app/build/stage metadata without secrets.
- `health_checks`: available; `/v1/health` and `/v1/health/full` run read-only local checks.
- `diagnostics_export`: available; diagnostics packages are backend-redacted and exclude model weights, checkpoints, document bodies, API keys, cookies, and Authorization headers.
- `backup_restore`: available; scripts back up local data while excluding model/download/checkpoint weight files.
- `windows_packaging`: available; Windows launch, diagnostics, backup, restore, and release packaging scripts exist.
- `windows_desktop_release`: available; Flutter Windows is the supported release target.
- `novel_studio_product_ui`: available when `features.novel_studio.enabled=true`.

下载生命周期说明见 [docs/DOWNLOADS.md](DOWNLOADS.md)。

## 当前摘要

- `chat_non_stream`：available；Flutter 已接入。
- `chat_stream`：available；Flutter 已接入 SSE 流式输出和停止生成。
- `model_scan` / `model_load` / `model_unload`：available。
- `model_download`：available；下载作为后台 Job 运行。
- `model_download_modelscope`：partial；ModelScope / 魔塔社区是唯一远程下载源，部分进度字段可能未知。
- `model_download_huggingface`：not implemented；Hugging Face 远程下载 provider 已移除，本地 Transformers/HF 格式模型仍可扫描和加载。
- `model_download_progress`：partial；只有真实 `total_bytes` 已知时显示百分比。
- `model_download_cancel`：partial；取消是协作式请求。
- `model_download_retry`：available；重试复用 ModelScope cache。
- `model_download_resume`：partial；不声明严格暂停/断点续传。
- `model_download_auto_register`：available；下载成功后扫描并写回 `model_id`。
- `rag_query`：partial；Flutter 有最小查询入口。
- `rag_import`：backend only。
- `vision_ocr`：backend only。
- `lora_scan` / `lora_load` / `lora_activate`：partial。
- `lora_merge`：not implemented；不在 Flutter 默认展示。
- `benchmark`：experimental；仅供本机开发参考。
- `benchmark_with_adapter`：not implemented；Flutter 不展示 Adapter 选择。
- `storage_cleanup`：partial；preview 优先，只删允许目录。
- `diagnostics_export`：partial；导出内容脱敏。
- `flutter_windows`：available。
- Android / Linux / macOS / Web：not implemented。
