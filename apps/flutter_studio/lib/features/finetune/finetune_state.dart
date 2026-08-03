import 'models/finetune_checkpoint_dto.dart';
import 'models/finetune_log_dto.dart';
import 'models/finetune_metric_dto.dart';
import 'models/finetune_preflight_dto.dart';
import 'models/finetune_run_dto.dart';

class FinetuneState {
  const FinetuneState({
    this.runs = const [],
    this.currentRun,
    this.preflight,
    this.metrics = const [],
    this.logs = const [],
    this.checkpoints = const [],
    this.loading = false,
    this.error,
    this.notice,
  });

  final List<FinetuneRunDto> runs;
  final FinetuneRunDto? currentRun;
  final FinetunePreflightDto? preflight;
  final List<FinetuneMetricDto> metrics;
  final List<FinetuneLogDto> logs;
  final List<FinetuneCheckpointDto> checkpoints;
  final bool loading;
  final String? error;
  final String? notice;

  FinetuneState copyWith({
    List<FinetuneRunDto>? runs,
    FinetuneRunDto? currentRun,
    FinetunePreflightDto? preflight,
    List<FinetuneMetricDto>? metrics,
    List<FinetuneLogDto>? logs,
    List<FinetuneCheckpointDto>? checkpoints,
    bool? loading,
    String? error,
    String? notice,
    bool clearRun = false,
    bool clearPreflight = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => FinetuneState(
    runs: runs ?? this.runs,
    currentRun: clearRun ? null : currentRun ?? this.currentRun,
    preflight: clearPreflight ? null : preflight ?? this.preflight,
    metrics: metrics ?? this.metrics,
    logs: logs ?? this.logs,
    checkpoints: checkpoints ?? this.checkpoints,
    loading: loading ?? this.loading,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
  );
}
