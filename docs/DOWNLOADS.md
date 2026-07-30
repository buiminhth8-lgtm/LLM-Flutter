# 模型下载生命周期

LLM Studio 当前仅支持 ModelScope / 魔塔社区作为远程模型下载源。Hugging Face 远程下载 provider 已移除；本地模型扫描和加载仍支持 Transformers / safetensors / GGUF 等常见模型格式。

## 配置

```yaml
downloads:
  default_provider: "modelscope"
  providers:
    modelscope:
      cache_dir: "./data/cache/modelscope"
      endpoint: "https://modelscope.cn"
```

环境变量：

- `MODELSCOPE_API_TOKEN`：ModelScope 访问 Token。
- `MODELSCOPE_ENDPOINT`：ModelScope endpoint。
- `MODELSCOPE_CACHE`：ModelScope 本地缓存目录。

Token 不会写入 Job payload、日志或诊断包。

## API 请求

`POST /v1/downloads` 可以省略 `provider`，后端会使用 `modelscope`。

```json
{
  "provider": "modelscope",
  "repo_id": "damo/model",
  "revision": "master",
  "allow_patterns": ["*.safetensors", "*.json"],
  "ignore_patterns": ["*.bin"],
  "local_files_only": false
}
```

兼容行为：

- `provider` 省略：使用 `modelscope`。
- `provider=modelscope`：正常创建下载任务。
- `provider=huggingface` 或其他值：返回 `DOWNLOAD_PROVIDER_NOT_SUPPORTED`。

## 任务状态

下载任务可能经历：

- `pending`
- `running`
- `cancelling`
- `cancelled`
- `succeeded`
- `failed`
- `interrupted`

终态任务包括 `succeeded`、`failed`、`cancelled`、`interrupted`。终态任务不能再次取消。

## Progress 字段

下载状态包含：

- `downloaded_bytes`
- `total_bytes`
- `percent`
- `speed_bytes_per_second`
- `eta_seconds`
- `current_file`
- `completed_files`
- `total_files`

规则：

- `total_bytes` 未知时返回 `null`。
- `percent` 只有 `total_bytes` 已知时计算。
- 不伪造总大小或百分比。
- `current_file` 必须脱敏，不能包含 Token 或用户敏感路径。

## 取消

取消是协作式取消：

- `pending/running` 可以取消。
- 当前网络传输步骤可能结束后才会停止。
- 取消请求提交后会显示 `cancel_requested=true` 或进入 `cancelling`。
- 终态任务取消返回 `JOB_CANCEL_NOT_ALLOWED` 或 `DOWNLOAD_CANCEL_NOT_ALLOWED`。

## 重试和恢复

- `failed/cancelled/interrupted` 可以 retry。
- `succeeded` 不允许 retry，返回 `DOWNLOAD_RETRY_NOT_ALLOWED`。
- retry 会尽量复用 ModelScope cache。
- 当前不声明严格暂停/断点续传，只声明缓存复用。

## local_files_only

`local_files_only=true` 表示只使用 ModelScope 本地缓存，不访问网络：

- 不访问远程 metadata API。
- SDK 调用必须传入 `local_files_only=true`。
- 本地缓存不存在时返回 `DOWNLOAD_LOCAL_FILES_NOT_FOUND` 或 `MODELSCOPE_LOCAL_FILES_NOT_FOUND`。
- `total_bytes` 和 `percent` 可以为 `null`。

## 下载完成后的模型注册

下载成功后后端会：

1. 校验下载目录。
2. 移动到统一模型仓库。
3. 调用 `ModelScanner`。
4. 更新 `LocalModelRepository`。
5. 将 `model_id` 写回下载任务。

如果扫描失败，任务会记录 `DOWNLOAD_MODEL_SCAN_FAILED` 或 `registration_status=failed`，不会伪装成注册成功。

## 删除下载记录

`DELETE /v1/downloads/{job_id}` 只删除下载 Job 记录，不删除模型文件、ModelScope cache 或失败任务留下的项目临时目录。

- 仅终态下载任务记录可删除。
- `pending/running/cancelling` 返回 `DOWNLOAD_RECORD_DELETE_NOT_ALLOWED`。
- 失败或取消后留下的项目临时目录通过 Storage cleanup preview / cleanup 清理。

## temp_dir 清理策略

项目下载临时目录格式：

```text
data/downloads/{job_id}-xxx
```

规则：

- Job payload 记录 `temp_dir` / `download_temp_dir`。
- 成功下载后，临时目录会移动到最终模型目录。
- 失败或取消后的项目临时目录可通过 `download_temp` 类别清理。
- cleanup 只能删除项目 `data/downloads` 下的临时目录。
- cleanup 不删除最终模型目录。
- cleanup 不删除 ModelScope cache。
- 清理失败返回 `DOWNLOAD_TEMP_CLEANUP_FAILED` 或 `STORAGE_CLEANUP_FAILED`。

## Token 安全

- `MODELSCOPE_API_TOKEN` 不进入 Job payload。
- Token 不进入日志。
- Token 不进入诊断包。
- `Authorization` header、`token=...`、`access_token=...`、`api_key=...` 写入日志或错误前必须脱敏。
