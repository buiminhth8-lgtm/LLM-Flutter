# Windows Desktop 运行方式

后端不使用 CLI、click 或 `llm-studio.exe`。推荐服务启动方式：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

Flutter 本地后端模式会检查 `/health`，必要时使用 Python 模块方式启动后端：

```text
python.exe -m llm_studio.server --host 127.0.0.1 --port 8000
```

Settings 页面支持：

- 自动启动本地后端或连接远程后端。
- 配置 Python 路径和后端根目录。
- 手动重启或停止后端。
- 查看和复制脱敏后的后端日志。
- 配置退出应用时是否关闭本地后端。

当前不提供安装器或 exe 打包；旧虚拟环境中残留的 `llm-studio.exe` 不是当前启动入口。
