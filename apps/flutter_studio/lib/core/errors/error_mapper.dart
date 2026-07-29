import '../api/api_exception.dart';

String mapApiErrorMessage(String code, String fallback) {
  final message = switch (code) {
    'AUTH_REQUIRED' || 'UNAUTHORIZED' => '请先配置有效的 API Key。',
    'PERMISSION_DENIED' => '当前 API Key 没有执行该操作的权限。',
    'UPLOAD_FILE_TOO_LARGE' => '上传文件超过大小限制。',
    'GPU_BUSY' => 'GPU 正在执行其他任务，请稍后重试。',
    'DOWNLOAD_NOT_FOUND' => '下载任务不存在。',
    'DOWNLOAD_ALREADY_RUNNING' => '同一模型仓库已有下载任务正在运行。',
    'DOWNLOAD_AUTH_REQUIRED' => 'Hugging Face 仓库需要授权，请配置有效 Token。',
    'DOWNLOAD_REPO_NOT_FOUND' => '未找到 Hugging Face 仓库。',
    'DOWNLOAD_REVISION_NOT_FOUND' => '未找到指定 Hugging Face revision。',
    'DOWNLOAD_DISK_FULL' => '磁盘空间不足，无法继续下载。',
    'DOWNLOAD_NETWORK_ERROR' => '下载网络错误，请稍后重试。',
    'DOWNLOAD_CANCEL_REQUESTED' => '取消请求已提交，当前文件传输可能稍后停止。',
    'DOWNLOAD_CANCELLED' => '下载已取消。',
    'DOWNLOAD_RETRY_NOT_ALLOWED' => '当前下载状态不允许重试。',
    'DOWNLOAD_FAILED' => '下载失败，请查看任务详情。',
    'DOWNLOAD_VALIDATION_FAILED' => '下载结果校验失败。',
    'DOWNLOAD_MODEL_SCAN_FAILED' => '下载完成，但模型扫描注册失败。',
    'DOWNLOAD_MODEL_UNSUPPORTED' => '下载完成，但模型格式暂不支持。',
    'MODEL_NOT_FOUND' => '未找到指定模型，请先扫描、下载或注册模型。',
    'MODEL_LOAD_BUSY' => '模型正在加载或 GPU 正忙，请稍后重试。',
    'MODEL_LOAD_FAILED' => '模型加载失败，请查看后端日志。',
    'MODEL_UNLOAD_FAILED' => '模型卸载失败，请查看后端日志。',
    'MODEL_DELETE_CONFIRM_REQUIRED' => '删除模型需要二次确认。',
    'MODEL_DELETE_FAILED' => '模型删除失败，请查看后端日志。',
    'ADAPTER_MODEL_REQUIRED' => '请先选择或加载基础模型。',
    'ADAPTER_INCOMPATIBLE' => 'Adapter 与当前基础模型不兼容。',
    'ADAPTER_NOT_FOUND' => '未找到指定 Adapter。',
    'ADAPTER_OPERATION_FAILED' => 'Adapter 操作失败，请查看后端日志。',
    'PEFT_NOT_AVAILABLE' => '当前模型或环境不支持 PEFT Adapter 操作。',
    'RAG_QUERY_INVALID' => 'RAG 查询问题不能为空。',
    'RAG_PATH_NOT_ALLOWED' => '当前 API Key 无权读取该本地路径，或路径不在允许目录内。',
    'VISION_PATH_NOT_ALLOWED' => '当前 API Key 无权读取该图片路径，或路径不在允许目录内。',
    'DIAGNOSTICS_EXPORT_FAILED' => '诊断包导出失败，请查看后端日志。',
    'STORAGE_CLEANUP_FAILED' => '存储清理失败，请查看后端日志。',
    'INTERNAL_ERROR' => '操作失败，请查看后端日志。',
    'BENCHMARK_OOM' => 'Benchmark 显存不足，请降低上下文或输出长度。',
    _ => fallback,
  };
  return message.trim().isEmpty ? '操作失败，请查看后端日志。' : message;
}

StudioApiException exceptionForApiError({
  required int statusCode,
  required String code,
  required String message,
}) {
  final mapped = mapApiErrorMessage(code, message);
  if (statusCode == 401 || code == 'AUTH_REQUIRED' || code == 'UNAUTHORIZED') {
    return AuthRequiredException(mapped, code: code, statusCode: statusCode);
  }
  if (statusCode == 403 || code == 'PERMISSION_DENIED') {
    return PermissionDeniedException(mapped, code: code, statusCode: statusCode);
  }
  return StudioApiException(mapped, code: code, statusCode: statusCode);
}

