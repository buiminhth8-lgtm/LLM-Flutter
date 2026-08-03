# Windows Release Guide

## 1. 环境检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/check_environment.ps1
```

该脚本检查 Python、Flutter、数据目录写入和可选的 `/v1/health`。它不访问云端、不加载模型、不启动训练。

## 2. 启动后端

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/start_backend.ps1
```

默认监听 `127.0.0.1:8000`，日志写入 `data/logs`。

## 3. 启动 Flutter Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/start_flutter_desktop.ps1
```

## 4. 构建发布包

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package_windows.ps1
```

如已提前构建 Flutter，可使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package_windows.ps1 -SkipBuild
```

发布包不会包含模型权重、下载缓存、API Key 或诊断包。

## 5. 验收 API

```powershell
curl http://127.0.0.1:8000/v1/version
curl http://127.0.0.1:8000/v1/health
curl http://127.0.0.1:8000/v1/capabilities
```

`/v1/capabilities` 应包含 `novel_studio_product_ui=available`、`health_checks=available`、`windows_desktop_release=available`。
