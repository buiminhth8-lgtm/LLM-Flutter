# LLM-Studio Flutter Windows 客户端

这是当前项目的 Windows 桌面客户端。后端通过纯 Python 服务启动：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

当前不使用 `llm-studio.exe`、旧 CLI 或 click 启动后端。Settings 页面可选择本地后端自动启动或连接远程后端。

## 常用命令

从仓库根目录运行：

```powershell
.\scripts\test_flutter.ps1
.\scripts\flutter_build_windows.ps1
```

或直接进入 Flutter 项目：

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
flutter run -d windows
```

## 当前页面

- Status：运行时状态、GPU Scheduler、Capabilities、任务摘要。
- Models：扫描、加载、卸载、选择模型；删除模型会二次确认并移入回收站。
- Chat：非流式和 SSE 流式聊天，支持停止生成；未加载模型时禁用输入。
- Downloads：后台下载任务，仅支持 ModelScope / 魔塔社区远程下载源，显示真实进度、速度、ETA、取消、重试、删除记录和完成后查看模型。
- Jobs：任务列表、状态、错误码、取消和详情。
- RAG：查询测试和基础状态展示；本地路径访问默认受限。
- Adapters：扫描、加载、激活、停用 Adapter；无基础模型时禁用相关操作。
- Benchmark：实验性本机开发参考，不作为权威性能数据。
- Storage：磁盘占用、cleanup preview 和 cleanup。
- Diagnostics：导出脱敏诊断包。
- Settings：API Base URL、API Key、本地/远程后端、后端日志和退出行为。

## API 契约重点

- 下载默认发送 `provider=modelscope`。
- RAG 查询请求体使用 `question` 字段，默认 `top_k=5`。
- Adapter 操作传入当前基础模型 ID，不使用 `model=auto`。
- 删除模型在确认后调用 `confirm=true`。
- 功能展示以 `GET /v1/capabilities` 为准。
- 后端日志显示和复制前会脱敏，不应包含 API Key、Authorization、Cookie 或 Token。
- Flutter 客户端启动信息、API 错误和未捕获异常会输出到 Flutter debug console；输出前会脱敏 API Key、Authorization、Cookie、password 和 token。

Windows 真实运行验收见 [docs/WINDOWS_ACCEPTANCE.md](../../docs/WINDOWS_ACCEPTANCE.md)。
