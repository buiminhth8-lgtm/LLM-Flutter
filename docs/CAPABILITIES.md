# 能力状态

真实能力以运行时接口为准：

```powershell
curl http://127.0.0.1:8000/v1/capabilities
```

下载生命周期说明见 [docs/DOWNLOADS.md](DOWNLOADS.md)。

关键状态：

- `chat_non_stream`：available，Flutter 已接入。
- `chat_stream`：available，Flutter 已接入基础 SSE 和停止生成。
- `model_scan` / `model_load` / `model_unload`：available。
- `model_download`：available，后台 Job。
- `model_download_progress`：partial；只有真实 `total_bytes` 已知时显示百分比。
- `model_download_cancel`：partial；取消是协作式请求。
- `model_download_retry`：available；重试复用 Hugging Face cache。
- `model_download_auto_register`：available；下载成功后扫描并写回 `model_id`。
- `rag_query`：partial，Flutter 有最小查询入口。
- `rag_import`：backend only。
- `lora_scan` / `lora_load` / `lora_activate`：partial。
- `lora_merge`：not implemented，不在 Flutter 默认展示。
- `benchmark`：experimental，仅供本机开发参考。
- `benchmark_with_adapter`：not implemented，Flutter 不展示 Adapter 选择。
- `diagnostics_export`：partial，导出内容脱敏。
- `flutter_windows`：available。
- Android、Linux、macOS、Web：not implemented。
