# 认证恢复说明

本文说明 LLM Studio 在忘记 API Key、user_id 或 admin 密码时的安全恢复方式。

## 基本原则

- API Key 不能找回，只能重新生成。
- 新 API Key 只显示一次，关闭弹窗或终端后无法再次读取完整 Key。
- 远程 API 不提供未认证的 admin 密码重置能力。
- admin 密码明文不会写入 `api_users.json`、日志、诊断包或 Job payload。
- API Key、Authorization、Cookie、Token 不应写入日志或诊断包。

## API Key 丢失

如果仍有可用的 admin API Key：

1. 打开 Flutter Settings。
2. 在 Auth recovery 区域加载用户列表。
3. 对目标用户执行 Regenerate API Key。
4. 立即复制并保存新 Key。

重新生成后，旧 API Key 立即失效。

后端 API：

```http
GET /v1/auth/users
POST /v1/auth/users/{user_id}/regenerate
```

这些接口必须使用已认证 admin API Key 调用。

## user_id 丢失

如果 API Key 仍在但忘记 user_id：

1. Flutter Settings 中可以留空 User ID。
2. 客户端会发送：

```http
Authorization: Bearer <api_key>
```

后端会根据 API Key hash 自动匹配启用用户，并返回识别到的 `user_id`。

如果已用 admin 登录，也可以在 Settings 的用户列表中查看所有 `user_id`。

## admin 密码丢失

admin 密码丢失不能通过远程 UI 或远程 API 重置。必须登录后端所在机器并运行本机工具：

```powershell
python tools/reset_auth.py --reset-admin-password
```

如需同时重置 admin 密码和 admin API Key：

```powershell
python tools/reset_auth.py --reset-admin
```

工具会在修改前自动备份 `api_users.json`：

```text
api_users.json.bak-YYYYMMDD-HHMMSS
```

## admin 密码和 API Key 都丢失

如果 admin 密码和 API Key 都丢失，不能远程恢复。请在本机重新初始化：

1. 停止后端。
2. 备份当前用户文件。
3. 重命名 `api_users.json`。
4. 重启后端。
5. 重新执行首次初始化。

PowerShell 示例：

```powershell
Copy-Item .\data\auth\api_users.json .\data\auth\api_users.json.bak
Rename-Item .\data\auth\api_users.json api_users.json.lost
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

然后打开 Flutter，按首次初始化流程设置新的 admin 密码和 API Key。

## reset_auth.py 命令

```powershell
python tools/reset_auth.py --list-users
python tools/reset_auth.py --regenerate-key admin
python tools/reset_auth.py --reset-admin-password
python tools/reset_auth.py --reset-admin
python tools/reset_auth.py --create-admin-if-missing
```

可选指定用户文件：

```powershell
python tools/reset_auth.py --users-file .\data\auth\api_users.json --list-users
```

输出不会包含旧 API Key、密码 hash 或完整旧密钥。
