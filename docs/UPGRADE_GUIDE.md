# Upgrade Guide

1. 停止 Flutter 和本地后端。
2. 运行备份：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/backup_data.ps1
```

3. 拉取或安装新版本。
4. 检查环境：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/check_environment.ps1
```

5. 启动后端并检查：

```powershell
curl http://127.0.0.1:8000/v1/version
curl http://127.0.0.1:8000/v1/health/full
```

Stage 12 不修改冻结的 DatasetVersion，也不会自动训练或自动激活 Adapter。
