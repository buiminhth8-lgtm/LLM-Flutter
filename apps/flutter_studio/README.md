# LLM-Studio Flutter Windows 客户端

这是 LLM-Studio 当前第一客户端，面向 Windows Desktop。项目主文档在仓库根目录 `README.md`，包括整体架构、后端启动、Flutter 调试、API 调用、模型管理、安全策略和验证命令。

常用开发命令：

```powershell
.\scripts\test_flutter.ps1
```

也可以直接运行：

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

桌面端在本地后端模式下会检查 `/health`，并按配置启动：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

当前不使用 `llm-studio.exe`、旧 CLI 或 click 启动后端。后端日志可在 Settings 页面查看和复制，复制内容会先脱敏。

功能状态以 `GET /v1/capabilities` 为准。Flutter Windows 已接入非流式聊天、SSE 基础流式聊天、模型加载/卸载、Jobs、Downloads、RAG 查询、Adapter 最小操作、Storage 和 Diagnostics 的基础页面；Benchmark 和部分 Adapter 能力仍按能力表标记为实验性或未实现。

当前 Flutter API 契约重点：

- RAG 查询请求体使用 `question` 字段，默认 `top_k=5`。
- Adapter 加载和激活会传入当前基础模型 ID。
- 删除模型会在二次确认后调用 `confirm=true`，后端默认移入回收站。
- Benchmark 的 Adapter 选择暂不暴露；`benchmark_with_adapter` 在 capabilities 中标记为 `not_implemented`。
- Downloads 页面展示后台 Job 的真实状态；`total_bytes` 未知时不显示百分比，取消操作显示“取消请求已提交”，重试会复用 Hugging Face cache。
- 下载成功后，如果后端扫描识别出 ready 模型，任务会带回 `model_id`，页面可以跳转查看模型。
