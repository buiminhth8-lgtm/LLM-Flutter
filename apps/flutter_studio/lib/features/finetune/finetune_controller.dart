import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'finetune_api_client.dart';
import 'finetune_state.dart';
import 'models/finetune_create_run_request_dto.dart';
import 'models/finetune_preflight_dto.dart';

class FinetuneController extends ChangeNotifier {
  FinetuneController(this._api);

  final FinetuneApiClient _api;
  FinetuneState state = const FinetuneState();

  Future<void> refresh() async {
    await _run(() async {
      final runs = await _api.listFinetuneRuns();
      state = state.copyWith(runs: runs);
      final current = state.currentRun;
      if (current != null && runs.any((item) => item.runId == current.runId)) {
        await _loadRun(current.runId);
      }
    });
  }

  Future<FinetunePreflightDto?> preflight(
    FinetunePreflightRequestDto request,
  ) async {
    FinetunePreflightDto? result;
    await _run(() async {
      result = await _api.preflightFinetune(request);
      state = state.copyWith(
        preflight: result,
        notice: result!.ok ? '预检通过。' : '预检存在错误。',
      );
    });
    return result;
  }

  Future<void> createRun(FinetuneCreateRunRequestDto request) async {
    await _run(() async {
      final run = await _api.createFinetuneRun(request);
      state = state.copyWith(
        currentRun: run,
        runs: await _api.listFinetuneRuns(),
        notice: '微调任务已创建。',
      );
      await _loadRun(run.runId);
    });
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
      final updated = await _api.startFinetuneRun(run.runId);
      state = state.copyWith(currentRun: updated);
      await refresh();
    });
  }

  Future<void> cancelCurrentRun() async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.cancelFinetuneRun(run.runId);
      state = state.copyWith(currentRun: updated, notice: '取消请求已提交。');
      await refresh();
    });
  }

  Future<void> resumeCurrentRun({String? checkpointId}) async {
    final run = state.currentRun;
    if (run == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.resumeFinetuneRun(
        run.runId,
        checkpointId: checkpointId,
      );
      state = state.copyWith(currentRun: updated, notice: '恢复请求已入队。');
      await refresh();
    });
  }

  Future<void> _loadRun(String runId) async {
    final run = await _api.getFinetuneRun(runId);
    final metrics = await _api.getFinetuneMetrics(runId);
    final logs = await _api.getFinetuneLogs(runId);
    final checkpoints = await _api.getFinetuneCheckpoints(runId);
    state = state.copyWith(
      currentRun: run,
      metrics: metrics,
      logs: logs,
      checkpoints: checkpoints,
    );
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false);
    } catch (error) {
      state = state.copyWith(loading: false, error: _message(error));
    }
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';
}
