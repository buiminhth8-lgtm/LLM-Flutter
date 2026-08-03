# Flutter Windows 客户端

这是 LLM-Studio 的桌面客户端，默认面向 Windows 运行。客户端负责界面、导航、认证信息输入、后端生命周期控制和 SSE 消费；核心业务仍由 Python 后端提供。

## 启动

```powershell
cd apps\flutter_studio
flutter pub get
flutter run -d windows
```

若需要指定项目根目录或 Python：

```powershell
flutter run -d windows `
  --dart-define="LLM_STUDIO_ROOT=<项目根目录>" `
  --dart-define="LLM_STUDIO_PYTHON=<python.exe 路径>"
```

## 页面

- 状态：Runtime、GPU、Capabilities、后台任务。
- 模型：扫描、加载、卸载、选择、移入回收站。
- 聊天：非流式与 SSE 流式聊天。
- 下载：ModelScope 下载、进度、取消、重试、删除记录。
- 存储：磁盘占用、清理预览、执行清理。
- 诊断：脱敏诊断导出与健康检查。
- 小说工作台：项目、提示词、上下文、写作、修订、数据集、微调、评估、记忆。
- 设置：API Base、API Key、本地/远程后端、后端日志、发布说明入口。

## Novel 模块不显示时

1. 检查 `config.yaml`：`features.novel_studio.enabled` 必须为 `true`。
2. 重启后端和 Flutter。
3. 打开设置或诊断页刷新能力。
4. 确认 Flutter 的 API Base 指向当前后端。

## 验证

```powershell
flutter analyze
flutter test
flutter build windows
```
