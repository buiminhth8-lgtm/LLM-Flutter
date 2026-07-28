# Windows Installer Strategy

安装器建议使用 Inno Setup，但本阶段不自动构建安装包。

要求：

- 默认安装到用户选择目录。
- 用户数据放在 `%LOCALAPPDATA%\LLM-Studio` 或用户选择的数据目录。
- 卸载默认保留模型、LoRA、RAG 索引和配置。
- 不自动安装 NVIDIA 驱动。
- 不自动修改系统 CUDA。
- 安装前检测磁盘空间。
