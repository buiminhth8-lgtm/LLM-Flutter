# 备份与恢复

## 备份范围

- `data/`
- `config.yaml`
- 必要的本地数据库文件

模型权重通常体积较大，可按需单独备份。

## 备份

```powershell
.\scripts\windows\backup_data.ps1
```

## 恢复

```powershell
.\scripts\windows\restore_data.ps1 -BackupPath <backup.zip>
```

## 注意

恢复前建议停止后端与 Flutter，避免数据库正在写入。
