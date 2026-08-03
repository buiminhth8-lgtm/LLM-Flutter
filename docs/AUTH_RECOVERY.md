# 认证恢复

## 场景

- 忘记 admin 密码。
- API Key 丢失。
- Flutter 认证信息被清空。

## 原则

- API Key 明文只显示一次。
- 远程 UI 不提供 admin 密码重置。
- 本机恢复必须在后端所在机器执行。

## 常用流程

1. 打开 Flutter 设置页，确认 API Base。
2. 如果只是 Key 丢失，用已认证 admin 重新生成。
3. 如果 admin 无法登录，在后端机器运行恢复脚本：

```powershell
python tools/reset_auth.py --reset-admin
```

4. 重启后端。
5. 在 Flutter 设置页填入新的用户和 API Key。

## 安全边界

诊断包、日志和生成记录不应包含 API Key、Authorization、Cookie 或密码。
