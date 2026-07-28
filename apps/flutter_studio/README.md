# LLM-Studio Flutter Windows 客户端

这是 LLM-Studio 当前第一客户端，面向 Windows desktop。项目主文档已经统一合并到仓库根目录的 `README.md`，包括整体架构、后端启动、Flutter 调试、API 调用、模型管理、安全策略和验证命令。

常用开发命令：

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

桌面端会在本地后端模式下检查 `/health`，并按配置启动：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

当前不使用 `llm-studio.exe`、旧 CLI 或 click 启动后端。后端日志可在 Settings 页面查看和复制，复制内容会先脱敏。
