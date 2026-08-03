# Windows 桌面说明

Flutter Windows 客户端可连接远程后端，也可自动启动本地后端。

## 启动顺序

1. 读取设置。
2. 检查本地模式。
3. 启动 `python -m llm_studio.server`。
4. 请求健康检查和能力清单。
5. 显示可用页面。

## 排查

- 页面缺失：刷新能力或检查 feature flag。
- 后端启动失败：检查 Python 路径、项目根目录和依赖。
- 权限失败：检查 API Key。
