import 'finetune_checkpoint_dto.dart';
import 'finetune_log_dto.dart';
import 'finetune_metric_dto.dart';

class FinetuneRunDto {
  const FinetuneRunDto({
    required this.runId,
    required this.datasetVersionId,
    required this.recipeId,
    required this.baseModelId,
    required this.method,
    required this.adapterName,
    required this.status,
    required this.configSnapshot,
    required this.datasetManifestSnapshot,
    required this.currentStep,
    required this.totalSteps,
    required this.createdAt,
    required this.updatedAt,
    this.jobId,
    this.adapterId,
    this.currentEpoch,
    this.trainLoss,
    this.valLoss,
    this.bestValLoss,
    this.bestStep,
    this.bestCheckpointId,
    this.lastCheckpointId,
    this.outputAdapterPath,
    this.metricsPath,
    this.logPath,
    this.errorCode,
    this.errorMessage,
    this.cancelRequested = false,
    this.resumeFromCheckpointId,
    this.startedAt,
    this.finishedAt,
    this.metrics = const [],
    this.logs = const [],
    this.checkpoints = const [],
  });

  factory FinetuneRunDto.fromMap(Map<dynamic, dynamic> map) => FinetuneRunDto(
    runId: '${map['run_id'] ?? map['id'] ?? ''}',
    jobId: _string(map['job_id']),
    datasetVersionId: '${map['dataset_version_id'] ?? ''}',
    recipeId: '${map['recipe_id'] ?? ''}',
    baseModelId: '${map['base_model_id'] ?? ''}',
    method: '${map['method'] ?? 'qlora'}',
    adapterName: '${map['adapter_name'] ?? ''}',
    adapterId: _string(map['adapter_id']),
    status: '${map['status'] ?? 'created'}',
    configSnapshot: _map(map['config_snapshot']),
    datasetManifestSnapshot: _map(map['dataset_manifest_snapshot']),
    currentStep: (map['current_step'] as num?)?.toInt() ?? 0,
    totalSteps: (map['total_steps'] as num?)?.toInt() ?? 0,
    currentEpoch: (map['current_epoch'] as num?)?.toDouble(),
    trainLoss: (map['train_loss'] as num?)?.toDouble(),
    valLoss: (map['val_loss'] as num?)?.toDouble(),
    bestValLoss: (map['best_val_loss'] as num?)?.toDouble(),
    bestStep: (map['best_step'] as num?)?.toInt(),
    bestCheckpointId: _string(map['best_checkpoint_id']),
    lastCheckpointId: _string(map['last_checkpoint_id']),
    outputAdapterPath: _string(map['output_adapter_path']),
    metricsPath: _string(map['metrics_path']),
    logPath: _string(map['log_path']),
    errorCode: _string(map['error_code']),
    errorMessage: _string(map['error_message']),
    cancelRequested: map['cancel_requested'] == true,
    resumeFromCheckpointId: _string(map['resume_from_checkpoint_id']),
    startedAt: _string(map['started_at']),
    finishedAt: _string(map['finished_at']),
    createdAt: '${map['created_at'] ?? ''}',
    updatedAt: '${map['updated_at'] ?? ''}',
    metrics: _mapList(map['metrics'])
        .map(FinetuneMetricDto.fromMap)
        .toList(growable: false),
    logs: _mapList(map['logs'])
        .map(FinetuneLogDto.fromMap)
        .toList(growable: false),
    checkpoints: _mapList(map['checkpoints'])
        .map(FinetuneCheckpointDto.fromMap)
        .toList(growable: false),
  );

  final String runId;
  final String? jobId;
  final String datasetVersionId;
  final String recipeId;
  final String baseModelId;
  final String method;
  final String adapterName;
  final String? adapterId;
  final String status;
  final Map<String, dynamic> configSnapshot;
  final Map<String, dynamic> datasetManifestSnapshot;
  final int currentStep;
  final int totalSteps;
  final double? currentEpoch;
  final double? trainLoss;
  final double? valLoss;
  final double? bestValLoss;
  final int? bestStep;
  final String? bestCheckpointId;
  final String? lastCheckpointId;
  final String? outputAdapterPath;
  final String? metricsPath;
  final String? logPath;
  final String? errorCode;
  final String? errorMessage;
  final bool cancelRequested;
  final String? resumeFromCheckpointId;
  final String? startedAt;
  final String? finishedAt;
  final String createdAt;
  final String updatedAt;
  final List<FinetuneMetricDto> metrics;
  final List<FinetuneLogDto> logs;
  final List<FinetuneCheckpointDto> checkpoints;
}

String? _string(Object? value) => value == null ? null : '$value';

Map<String, dynamic> _map(Object? value) {
  if (value is! Map) {
    return const {};
  }
  return value.map((key, value) => MapEntry('$key', value));
}

List<Map<String, dynamic>> _mapList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value
      .whereType<Map>()
      .map((item) => item.map((key, value) => MapEntry('$key', value)))
      .toList(growable: false);
}
