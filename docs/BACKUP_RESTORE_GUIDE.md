# Backup and Restore Guide

## Backup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/backup_data.ps1
```

或：

```powershell
python scripts/backup_data.py --data-dir ./data
```

备份包含本地数据目录中的 SQLite、JSON、YAML、日志和生成的轻量元数据，默认排除：

- `data/models`
- `data/downloads`
- `checkpoints`
- `diagnostics`
- `.bin`、`.safetensors`、`.gguf`、`.pt`、`.pth`、`.onnx`、`.ckpt`

## Restore

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/restore_data.ps1 -Backup path\to\backup.zip -Confirm
```

恢复会覆盖同名文件，因此必须显式传入 `-Confirm`。
