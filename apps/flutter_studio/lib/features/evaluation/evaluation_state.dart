import 'models/evaluation_finding_dto.dart';
import 'models/evaluation_metric_dto.dart';
import 'models/evaluation_report_dto.dart';
import 'models/evaluation_run_dto.dart';
import 'models/manual_evaluation_score_dto.dart';

class EvaluationState {
  const EvaluationState({
    this.runs = const [],
    this.currentRun,
    this.metrics = const [],
    this.findings = const [],
    this.manualScores = const [],
    this.reports = const [],
    this.currentReport,
    this.selectedProjectId,
    this.selectedTargetType,
    this.selectedStatus,
    this.loading = false,
    this.running = false,
    this.saving = false,
    this.error,
    this.notice,
  });

  final List<EvaluationRunDto> runs;
  final EvaluationRunDto? currentRun;
  final List<EvaluationMetricDto> metrics;
  final List<EvaluationFindingDto> findings;
  final List<ManualEvaluationScoreDto> manualScores;
  final List<EvaluationReportDto> reports;
  final EvaluationReportDto? currentReport;
  final String? selectedProjectId;
  final String? selectedTargetType;
  final String? selectedStatus;
  final bool loading;
  final bool running;
  final bool saving;
  final String? error;
  final String? notice;

  EvaluationState copyWith({
    List<EvaluationRunDto>? runs,
    EvaluationRunDto? currentRun,
    List<EvaluationMetricDto>? metrics,
    List<EvaluationFindingDto>? findings,
    List<ManualEvaluationScoreDto>? manualScores,
    List<EvaluationReportDto>? reports,
    EvaluationReportDto? currentReport,
    String? selectedProjectId,
    String? selectedTargetType,
    String? selectedStatus,
    bool? loading,
    bool? running,
    bool? saving,
    String? error,
    String? notice,
    bool clearRun = false,
    bool clearReport = false,
    bool clearProject = false,
    bool clearTargetType = false,
    bool clearStatus = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => EvaluationState(
    runs: runs ?? this.runs,
    currentRun: clearRun ? null : currentRun ?? this.currentRun,
    metrics: metrics ?? this.metrics,
    findings: findings ?? this.findings,
    manualScores: manualScores ?? this.manualScores,
    reports: reports ?? this.reports,
    currentReport: clearReport ? null : currentReport ?? this.currentReport,
    selectedProjectId: clearProject
        ? null
        : selectedProjectId ?? this.selectedProjectId,
    selectedTargetType: clearTargetType
        ? null
        : selectedTargetType ?? this.selectedTargetType,
    selectedStatus: clearStatus ? null : selectedStatus ?? this.selectedStatus,
    loading: loading ?? this.loading,
    running: running ?? this.running,
    saving: saving ?? this.saving,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
  );
}
