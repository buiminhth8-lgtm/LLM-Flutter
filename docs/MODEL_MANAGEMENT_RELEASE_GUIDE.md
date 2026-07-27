# Model Management And Release Guide

第三阶段新增本地模型仓库、后台任务、LoRA 管理、Benchmark、存储治理和诊断包导出。

## Model Repository

- 扫描 `data/models/transformers`、`data/models/gguf`、`data/models/gptq`、`data/models/awq`。
- 扫描只读取 `config.json`、量化配置、文件名和 GGUF header，不加载权重。
- 扫描阶段不调用 `AutoModel.from_pretrained`，也不启用 `trust_remote_code`。
- 单个模型损坏会记录 `metadata_errors`，不会中断整个列表。

## Downloads

- 下载通过后台 `MODEL_DOWNLOAD` Job 执行。
- Hugging Face Token 只来自环境变量或请求内存对象，不写入 Job payload。
- 下载先进入 `data/downloads`，校验通过后才移动到正式模型目录。
- 取消后重新开始会利用 Hugging Face 缓存自动续传；UI 不伪装成真正暂停。

## LoRA

- Adapter 扫描读取 `adapter_config.json` 和 adapter 权重文件。
- 推理侧使用 PEFT 官方接口 `load_adapter`、`set_adapter`、`disable_adapter`、`delete_adapter`。
- 合并任务会生成新模型目录，不覆盖原始基础模型。

## Benchmark

- Benchmark 逐个模型加载、测试、卸载。
- 指标区分加载时间、TTFT、生成耗时和 Token/s。
- 默认 warmup=1、measured=3、max_new_tokens=128、context=[512, 2048]，不默认跑超长上下文。

## Diagnostics

诊断包包含运行时、版本、pip freeze、脱敏配置、模型摘要和磁盘摘要。不包含模型权重、聊天记录、文档正文、Token、Cookie 或密码。

## Windows Release

当前推荐便携目录版。PyInstaller 和 Inno Setup 文件是可复现脚手架，必须在干净 Windows 用户环境验证后再发布。
