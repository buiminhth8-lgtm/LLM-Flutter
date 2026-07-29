# 下载生命周期

LLM Studio 的模型下载通过后台 Job 执行，不依赖 CLI，也不会在测试中真实下载大模型。

## Download Provider

当前下载源通过 `provider` 字段选择：

- `huggingface`：Hugging Face Hub，保留原有下载能力。
- `modelscope`：ModelScope / 魔塔社区，适合国内网络环境；依赖 `modelscope-hub`。

未传 `provider` 时使用配置项 `downloads.default_provider`。国内环境可以配置为：

```yaml
downloads:
  default_provider: "modelscope"
  providers:
    huggingface:
      cache_dir: "./data/cache/huggingface"
    modelscope:
      cache_dir: "./data/cache/modelscope"
      endpoint: "https://modelscope.cn"
```

请求示例：

```json
{
  "provider": "modelscope",
  "repo_id": "modelscope/Llama-3.2-1B",
  "revision": "master",
  "allow_patterns": ["*.safetensors", "*.json"],
  "ignore_patterns": ["*.bin"]
}
```

ModelScope 配置可由环境变量覆盖：

- `MODELSCOPE_API_TOKEN`：ModelScope 访问 Token。
- `MODELSCOPE_ENDPOINT`：ModelScope endpoint。
- `MODELSCOPE_CACHE`：ModelScope 本地缓存目录。

Hugging Face Token 和 ModelScope Token 都不会写入 Job payload、日志或诊断包。

## 任务状态

下载任务可能经历以下状态：

- `pending`：任务已创建，等待执行。
- `resolving`：解析仓库信息或本地缓存状态。当前实现可能以 `pending/running` 加消息表达该阶段。
- `downloading`：正在写入项目下载临时目录。当前实现可能以 `running` 加进度字段表达该阶段。
- `cancel_requested`：取消请求已提交；当前文件传输步骤可能结束后才会停止。
- `cancelled`：任务已取消。
- `succeeded`：下载成功并完成模型扫描注册。
- `failed`：下载、校验或注册失败。
- `interrupted`：服务重启或进程中断后，原运行中任务被标记为中断。

终态任务包括 `succeeded`、`failed`、`cancelled`、`interrupted`。终态任务不能再次取消。

## Progress 字段

下载状态包含以下进度字段：

- `downloaded_bytes`：已观察到的真实下载字节数。
- `total_bytes`：可获取时的总字节数；未知时为 `null`。
- `percent`：仅在 `total_bytes` 已知时计算；未知时为 `null`。
- `speed_bytes_per_second`：基于真实字节增量计算的速度；未知时为 `null`。
- `eta_seconds`：基于真实速度和剩余字节估算；未知时为 `null`。
- `current_file`：当前文件名，必须脱敏，不能包含 Token 或用户敏感路径。
- `completed_files`：已完成文件数。
- `total_files`：可获取时的总文件数；未知时为 `null`。

实现不伪造 `total_bytes` 或 `percent`。当 provider 无法提供真实大小时，客户端应显示不确定进度。

## Cancel 语义

取消是协作式取消：

- `pending/running` 任务可以取消。
- `succeeded/failed/cancelled/interrupted` 任务不能取消，返回 `JOB_CANCEL_NOT_ALLOWED` 或 `DOWNLOAD_CANCEL_NOT_ALLOWED`。
- 取消请求提交后可能先进入 `cancel_requested`，不保证立即停止当前网络传输步骤。

## Retry 语义

- `failed/cancelled/interrupted` 可以 retry。
- `succeeded` 不允许 retry，返回 `DOWNLOAD_RETRY_NOT_ALLOWED`。
- retry 会尽量复用底层缓存。
- 当前不声明严格暂停/断点续传，只复用 Hugging Face 或 ModelScope SDK 的缓存能力。

## local_files_only

`local_files_only=true` 表示只使用本地缓存：

- Hugging Face provider 不访问 Hugging Face 网络 API，不调用远程 repo metadata 或 `model_info`。
- ModelScope provider 不访问 ModelScope 网络 API，不调用远程 repo metadata。
- `snapshot_download` 或等价 SDK 调用会带上 `local_files_only=true`。
- 本地缓存不存在时返回 `DOWNLOAD_LOCAL_FILES_NOT_FOUND` 或 `MODELSCOPE_LOCAL_FILES_NOT_FOUND`。
- `total_bytes` 和 `percent` 可以为 `null`。

## 下载完成后的模型注册

下载成功后会：

1. 校验下载目录。
2. 移动到统一模型仓库。
3. 调用模型扫描。
4. 写回 `model_id`。

如果扫描失败，不会伪装成注册成功；任务会记录 `DOWNLOAD_MODEL_SCAN_FAILED` 或 `registration_status=failed`。

## temp_dir 清理策略

项目下载临时目录格式为：

```text
data/downloads/{job_id}-xxx
```

规则：

- 下载任务会在 Job payload 中记录 `temp_dir` / `download_temp_dir`。
- 成功下载后，临时目录会被移动到最终模型目录。
- 失败或取消后的项目临时目录可能保留，用于排查或后续 cleanup。
- Storage cleanup preview 会以 `download_temp` 分类显示过期下载临时目录。
- cleanup 只能删除项目 `data/downloads` 下的下载临时目录。
- 不删除最终模型目录。
- 不删除全局 Hugging Face cache 或 ModelScope cache。
- 清理失败时返回 `DOWNLOAD_TEMP_CLEANUP_FAILED` 或通用 `STORAGE_CLEANUP_FAILED`。

## Token 安全

- Hugging Face Token 不进入 Job payload。
- ModelScope Token 不进入 Job payload。
- Token 不进入日志。
- Token 不进入诊断包。
- Hugging Face / ModelScope 异常、`Authorization` header、`token=...`、`api_key=...` 会在写入 Job error 或返回 API 前脱敏。
