# 开发与验证

## 后端

```powershell
python -m compileall llm_studio
python -m pytest
python -m llm_studio.server --help
```

可选：

```powershell
python -m ruff check llm_studio tests
python -m pip check
```

## Flutter

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
```

Flutter 测试使用 fake API client，不应真实启动后端、下载模型或占用 GPU。

## 人工验收

1. 启动 Flutter Windows。
2. 确认后端自动检查和本地启动状态。
3. Models 扫描并加载 ready 模型。
4. Chat 发送消息，测试流式和停止生成。
5. Downloads 创建小任务，验证 unknown total、取消请求、重试和模型跳转。
6. Jobs 查看运行/失败任务。
7. RAG 查询错误能显示中文提示。
8. Adapters 无基础模型时禁用加载。
9. Benchmark 显示实验性提示。
10. Storage 先 preview 后 cleanup。
11. Diagnostics 导出脱敏诊断包。
12. Settings 清除 API Key、复制日志、重启后端。
