import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'evaluation_api_client.dart';
import 'evaluation_state.dart';
import 'models/evaluation_run_dto.dart';

class EvaluationController extends ChangeNotifier {
  EvaluationController(this._api);

  final EvaluationApiClient _api;
  EvaluationState state = const EvaluationState();

  Future<void> refresh() async {
    await _run(() async {
      final runs = await _api.listRuns(
        projectId: state.selectedProjectId,
        targetType: state.selectedTargetType,
        status: state.selectedStatus,
      );
      state = state.copyWith(runs: runs);
      final current = state.currentRun;
      if (current != null && runs.any((item) => item.runId == current.runId)) {
        await _loadRun(current.runId);
      }
    });
  }

  Future<void> setFilters({
    String? projectId,
    String? targetType,
    String? status,
    bool clearProject = false,
    bool clearTargetType = false,
    bool clearStatus = false,
  }) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      selectedTargetType: targetType,
      selectedStatus: status,
      clearProject: clearProject,
      clearTargetType: clearTargetType,
      clearStatus: clearStatus,
    );
    notifyListeners();
    await refresh();
  }

  Future<String?> createRun(CreateEvaluationRunRequest request) async {
    String? runId;
    await _run(() async {
      final run = await _api.createRun(request);
      runId = run.runId;
      await _afterRunChanged(run, notice: '评估运行已完成。');
    }, running: true);
    return runId;
  }

  Future<String?> createRunForTarget({
    required String targetType,
    required String targetId,
    String? projectId,
    String? chapterId,
    String? name,
  }) {
    return createRun(
      CreateEvaluationRunRequest(
        name: name ?? '评估：$targetType $targetId',
        targetType: targetType,
        targetId: targetId,
        projectId: projectId,
        chapterId: chapterId,
      ),
    );
  }

  Future<String?> runSync(CreateEvaluationRunRequest request) async {
    String? runId;
    await _run(() async {
      final run = await _api.runSync(request);
      runId = run.runId;
      await _afterRunChanged(run, notice: '评估运行已完成。');
    }, running: true);
    return runId;
  }

  Future<void> selectRun(String runId) async {
    await _run(() async {
      await _loadRun(runId);
    });
  }

  Future<void> startCurrentRun() async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.startRun(run.runId);
      await _afterRunChanged(updated, notice: '评估运行已完成。');
    }, running: true);
  }

  Future<void> cancelCurrentRun() async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.cancelRun(run.runId);
      await _afterRunChanged(updated, notice: '评估运行已取消。');
    });
  }

  Future<void> archiveCurrentRun() async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.archiveRun(run.runId);
      await _afterRunChanged(updated, notice: '评估运行已归档。');
    });
  }

  Future<void> updateFindingStatus(String findingId, String status) async {
    await _run(() async {
      await _api.updateFindingStatus(findingId, status);
      final run = state.currentRun;
      if (run != null) {
        await _loadRun(run.runId);
      }
      state = state.copyWith(notice: '发现项状态已更新。');
    }, saving: true);
  }

  Future<void> addManualScore(ManualEvaluationScoreRequest request) async {
    final run = state.currentRun;
    if (run == null) {
      state = state.copyWith(error: '请先选择评估运行。');
      notifyListeners();
      return;
    }
    await _run(() async {
      await _api.addManualScore(run.runId, request);
      await _loadRun(run.runId);
      state = state.copyWith(notice: '人工评分已保存。');
    }, saving: true);
  }

  Future<void> generateReport() async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final report = await _api.generateReport(run.runId);
      await _loadRun(run.runId, selectedReportId: report.reportId);
      state = state.copyWith(notice: '评估报告已生成。');
    }, saving: true);
  }

  Future<void> openReport(String reportId) async {
    await _run(() async {
      state = state.copyWith(currentReport: await _api.getReport(reportId));
    });
  }

  Future<void> _afterRunChanged(EvaluationRunDto run, {String? notice}) async {
    final runs = await _api.listRuns(
      projectId: state.selectedProjectId,
      targetType: state.selectedTargetType,
      status: state.selectedStatus,
    );
    state = state.copyWith(runs: runs, currentRun: run, notice: notice);
    await _loadRun(run.runId);
  }

  Future<void> _loadRun(String runId, {String? selectedReportId}) async {
    final run = await _api.getRun(runId);
    final metrics = run.metrics.isNotEmpty
        ? run.metrics
        : await _api.listMetrics(runId);
    final findings = run.findings.isNotEmpty
        ? run.findings
        : await _api.listFindings(runId);
    final manual = run.manualScores.isNotEmpty
        ? run.manualScores
        : await _api.listManualScores(runId);
    final reports = run.reports.isNotEmpty
        ? run.reports
        : await _api.listReports(runId);
    var selectedReport = selectedReportId == null
        ? (reports.isEmpty ? null : reports.first)
        : null;
    if (selectedReportId != null) {
      for (final report in reports) {
        if (report.reportId == selectedReportId) {
          selectedReport = report;
          break;
        }
      }
    }
    state = state.copyWith(
      currentRun: run,
      metrics: metrics,
      findings: findings,
      manualScores: manual,
      reports: reports,
      currentReport: selectedReport,
      clearReport: selectedReport == null,
      clearError: true,
    );
  }

  Future<void> _run(
    Future<void> Function() action, {
    bool running = false,
    bool saving = false,
  }) async {
    state = state.copyWith(
      loading: true,
      running: running,
      saving: saving,
      clearError: true,
      clearNotice: true,
    );
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false, running: false, saving: false);
    } catch (error) {
      state = state.copyWith(
        loading: false,
        running: false,
        saving: false,
        error: _message(error),
      );
    }
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';
}
