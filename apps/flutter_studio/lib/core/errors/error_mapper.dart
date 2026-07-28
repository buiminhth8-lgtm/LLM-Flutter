import '../api/api_exception.dart';

String mapApiErrorMessage(String code, String fallback) {
  return switch (code) {
    'AUTH_REQUIRED' || 'UNAUTHORIZED' => '认证已失效，请重新填写 API Key。',
    'PERMISSION_DENIED' => '当前 API Key 权限不足。',
    'UPLOAD_FILE_TOO_LARGE' => '上传文件过大。',
    'GPU_BUSY' => 'GPU 正在执行其他任务，请稍后重试。',
    'DOWNLOAD_FAILED' => '下载失败，请查看任务详情。',
    'DOWNLOAD_DISK_FULL' => '磁盘空间不足，无法继续下载。',
    'MODEL_NOT_FOUND' => '没有可用模型，请先扫描、下载或注册模型。',
    'MODEL_LOAD_BUSY' => '模型正在加载或 GPU 忙，请稍后重试。',
    'MODEL_DELETE_CONFIRM_REQUIRED' => '删除模型需要先确认移入回收站。',
    'MODEL_DELETE_FAILED' => '模型删除失败，请查看后端日志。',
    'ADAPTER_MODEL_REQUIRED' => '请先加载或选择基础模型。',
    'ADAPTER_INCOMPATIBLE' => 'Adapter 与当前基础模型不兼容。',
    'ADAPTER_NOT_FOUND' => '未找到指定 Adapter。',
    'PEFT_NOT_AVAILABLE' => '当前模型或环境不支持 PEFT Adapter 操作。',
    'RAG_QUERY_INVALID' => 'RAG 查询问题不能为空。',
    'BENCHMARK_OOM' => 'Benchmark 显存不足，请降低上下文或输出长度。',
    _ => fallback,
  };
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
