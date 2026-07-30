class ChatTurn {
  const ChatTurn({required this.role, required this.content});

  factory ChatTurn.user(String content) =>
      ChatTurn(role: 'user', content: content);

  factory ChatTurn.assistant(String content) =>
      ChatTurn(role: 'assistant', content: content);

  final String role;
  final String content;

  ChatTurn copyWith({String? role, String? content}) {
    return ChatTurn(role: role ?? this.role, content: content ?? this.content);
  }
}

class CurrentModelState {
  const CurrentModelState({
    required this.loaded,
    this.modelId,
    this.displayName,
    this.adapterId,
  });

  factory CurrentModelState.fromMap(Map<String, dynamic>? map) {
    if (map == null || map['loaded'] != true) {
      return const CurrentModelState(loaded: false);
    }
    return CurrentModelState(
      loaded: true,
      modelId: '${map['model_id'] ?? ''}',
      displayName: '${map['display_name'] ?? map['model_id'] ?? ''}',
      adapterId: map['adapter_id'] == null ? null : '${map['adapter_id']}',
    );
  }

  final bool loaded;
  final String? modelId;
  final String? displayName;
  final String? adapterId;
}

class DownloadTaskDto {
  const DownloadTaskDto({
    required this.jobId,
    required this.provider,
    required this.repoId,
    required this.status,
    this.revision,
    this.downloadedBytes,
    this.totalBytes,
    this.percent,
    this.completedFiles,
    this.totalFiles,
    this.currentFile,
    this.speedBytesPerSecond,
    this.etaSeconds,
    this.canCancel = false,
    this.canRetry = false,
    this.canDelete = false,
    this.resumeSupported = false,
    this.cancelRequested = false,
    this.message,
    this.errorCode,
    this.errorMessage,
    this.modelId,
  });

  factory DownloadTaskDto.fromMap(Map<dynamic, dynamic> map) {
    int? asInt(Object? value) =>
        value is num ? value.toInt() : int.tryParse('$value');
    double? asDouble(Object? value) =>
        value is num ? value.toDouble() : double.tryParse('$value');
    String? asString(Object? value) => value == null ? null : '$value';

    final status = '${map['status'] ?? 'unknown'}';
    final isRunningStatus = {
      'pending',
      'running',
      'resolving',
      'downloading',
    }.contains(status);
    final isRetryableStatus = {
      'failed',
      'cancelled',
      'interrupted',
    }.contains(status);
    final isTerminalStatus = {
      'succeeded',
      'failed',
      'cancelled',
      'interrupted',
    }.contains(status);

    return DownloadTaskDto(
      jobId: '${map['job_id'] ?? map['id'] ?? ''}',
      provider:
          '${map['provider'] ?? map['payload']?['provider'] ?? 'modelscope'}',
      repoId: '${map['repo_id'] ?? map['payload']?['repo_id'] ?? ''}',
      revision: asString(map['revision'] ?? map['payload']?['revision']),
      status: status,
      downloadedBytes: asInt(map['downloaded_bytes']),
      totalBytes: asInt(map['total_bytes']),
      percent: asDouble(map['percent']),
      completedFiles: asInt(map['completed_files']),
      totalFiles: asInt(map['total_files']),
      currentFile: asString(map['current_file']),
      speedBytesPerSecond: asDouble(map['speed_bytes_per_second']),
      etaSeconds: asDouble(map['eta_seconds']),
      canCancel:
          map['can_cancel'] == true ||
          (map['can_cancel'] == null && isRunningStatus),
      canRetry:
          map['can_retry'] == true ||
          (map['can_retry'] == null && isRetryableStatus),
      canDelete:
          map['can_delete'] == true ||
          (map['can_delete'] == null && isTerminalStatus),
      resumeSupported: map['resume_supported'] == true,
      cancelRequested: map['cancel_requested'] == true,
      message: asString(map['message']),
      errorCode: asString(map['error_code']),
      errorMessage: asString(map['error_message']),
      modelId: asString(map['model_id']),
    );
  }

  final String jobId;
  final String provider;
  final String repoId;
  final String status;
  final String? revision;
  final int? downloadedBytes;
  final int? totalBytes;
  final double? percent;
  final int? completedFiles;
  final int? totalFiles;
  final String? currentFile;
  final double? speedBytesPerSecond;
  final double? etaSeconds;
  final bool canCancel;
  final bool canRetry;
  final bool canDelete;
  final bool resumeSupported;
  final bool cancelRequested;
  final String? message;
  final String? errorCode;
  final String? errorMessage;
  final String? modelId;

  bool get isRunning =>
      status == 'pending' ||
      status == 'running' ||
      status == 'resolving' ||
      status == 'downloading' ||
      status == 'cancelling';
  bool get isSucceeded => status == 'succeeded';
  bool get isFailed => status == 'failed';
  bool get isCancelled => status == 'cancelled';
  bool get isInterrupted => status == 'interrupted';
  bool get isTerminal =>
      isSucceeded || isFailed || isCancelled || isInterrupted;
}

class AuthUserDto {
  const AuthUserDto({
    required this.userId,
    required this.role,
    required this.enabled,
    this.apiKeyMasked,
    this.note,
    this.createdAt,
    this.updatedAt,
  });

  factory AuthUserDto.fromMap(Map<dynamic, dynamic> map) {
    return AuthUserDto(
      userId: '${map['user_id'] ?? ''}',
      role: '${map['role'] ?? ''}',
      enabled: map['enabled'] != false,
      apiKeyMasked: map['api_key_masked'] == null
          ? null
          : '${map['api_key_masked']}',
      note: map['note'] == null ? null : '${map['note']}',
      createdAt: map['created_at'] is num
          ? (map['created_at'] as num).toDouble()
          : null,
      updatedAt: map['updated_at'] is num
          ? (map['updated_at'] as num).toDouble()
          : null,
    );
  }

  final String userId;
  final String role;
  final bool enabled;
  final String? apiKeyMasked;
  final String? note;
  final double? createdAt;
  final double? updatedAt;

  bool get isAdmin => role == 'admin';
}

class RegeneratedApiKeyDto {
  const RegeneratedApiKeyDto({
    required this.userId,
    required this.apiKey,
    required this.apiKeyMasked,
  });

  factory RegeneratedApiKeyDto.fromMap(Map<dynamic, dynamic> map) {
    return RegeneratedApiKeyDto(
      userId: '${map['user_id'] ?? ''}',
      apiKey: '${map['api_key'] ?? ''}',
      apiKeyMasked: '${map['api_key_masked'] ?? ''}',
    );
  }

  final String userId;
  final String apiKey;
  final String apiKeyMasked;
}
