# Flutter Windows 客户端

当前 Flutter 是 LLM-Studio 的第一客户端，目标平台为 Windows Desktop。

## 页面结构

- Status：后端运行状态、GPU Scheduler、能力状态和 Job Center 摘要。
- Models：扫描、筛选、查看详情、加载、卸载、设为聊天模型、移入回收站。
- Chat：非流式/流式聊天、停止生成、重新生成、复制消息、清空历史。
- Downloads：后台下载任务，展示真实进度、速度、ETA、当前文件、取消请求、重试和完成后的模型跳转。
- RAG：最小查询测试入口；本地路径导入默认隐藏并受后端 allowlist 限制。
- Adapters：扫描、加载、激活、停用；无基础模型时禁用操作。
- Benchmark：实验性本机参考测试；不暴露未实现的 Adapter benchmark。
- Storage：分类占用、cleanup preview、cleanup 执行。
- Diagnostics：显示脱敏说明，导出诊断包并复制路径。
- Settings：API Base URL、API Key、本地/远程后端、后端日志、重启/停止后端。

## UI 约定

- 统一使用 `core/ui` 下的 loading、empty、error、status badge、progress bar、section header 和确认弹窗。
- 危险操作必须二次确认。
- API Key、Token、Cookie、Authorization 不进入日志或页面明文展示。
- 后端错误以 `error.code` 映射为中文提示，不展示 Python traceback。

## 调试

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```
