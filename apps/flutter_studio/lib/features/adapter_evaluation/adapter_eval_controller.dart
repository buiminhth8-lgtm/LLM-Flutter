import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'adapter_eval_api_client.dart';
import 'adapter_eval_state.dart';
import 'models/adapter_eval_create_request_dto.dart';
import 'models/adapter_eval_score_dto.dart';

class AdapterEvalController extends ChangeNotifier {
  AdapterEvalController(this._api);

  final AdapterEvalApiClient _api;
  AdapterEvalState state = const AdapterEvalState();

  Future<void> refresh() async {
    await _run(() async {
      final sessions = await _api.listSessions();
      state = state.copyWith(sessions: sessions);
      final current = state.currentSession;
      if (current != null &&
          sessions.any((item) => item.sessionId == current.sessionId)) {
        await _loadSession(current.sessionId);
      }
    });
  }

  Future<void> createSession(CreateAdapterEvalSessionRequest request) async {
    await _run(() async {
      final session = await _api.createSession(request);
      state = state.copyWith(
        sessions: await _api.listSessions(),
        currentSession: session,
        clearCurrentCase: true,
        notice: '评估会话已创建。',
      );
      await _loadSession(session.sessionId);
    });
  }

  Future<void> selectSession(String sessionId) async {
    await _run(() async {
      await _loadSession(sessionId);
    });
  }

  Future<void> createCase(CreateAdapterEvalCaseRequest request) async {
    final session = state.currentSession;
    if (session == null) {
      return;
    }
    await _run(() async {
      final caseDto = await _api.createCase(session.sessionId, request);
      state = state.copyWith(currentCase: caseDto, notice: '评估用例已准备。');
      await _loadSession(session.sessionId);
    });
  }

  Future<void> selectCase(String caseId) async {
    await _run(() async {
      state = state.copyWith(currentCase: await _api.getCase(caseId));
    });
  }

  Future<void> runCurrentCase() async {
    final caseDto = state.currentCase;
    if (caseDto == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.runCase(caseDto.caseId);
      state = state.copyWith(currentCase: updated, notice: '对比已完成。');
      await _loadSession(updated.sessionId);
    });
  }

  Future<void> runCurrentSession() async {
    final session = state.currentSession;
    if (session == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.runSession(session.sessionId);
      state = state.copyWith(currentSession: updated, notice: '会话运行已完成。');
    });
  }

  Future<void> scoreCurrentCase(AdapterEvalScoreRequest request) async {
    final caseDto = state.currentCase;
    if (caseDto == null) {
      return;
    }
    await _run(() async {
      await _api.scoreCase(caseDto.caseId, request);
      state = state.copyWith(
        currentCase: await _api.getCase(caseDto.caseId),
        notice: '评分已保存。',
      );
    });
  }

  Future<void> generateReport() async {
    final session = state.currentSession;
    if (session == null) {
      return;
    }
    await _run(() async {
      final report = await _api.generateReport(session.sessionId);
      state = state.copyWith(
        reports: [report, ...state.reports],
        notice: '报告已生成。',
      );
      await _loadSession(session.sessionId);
    });
  }

  Future<void> createRevisionFromResult(
    String resultId,
    CreateRevisionFromEvalResultRequest request,
  ) async {
    await _run(() async {
      await _api.createRevisionFromEvalResult(resultId, request);
      state = state.copyWith(notice: '修订候选已创建。');
    });
  }

  Future<void> _loadSession(String sessionId) async {
    final session = await _api.getSession(sessionId);
    final reports = await _api.listReports(sessionId);
    state = state.copyWith(currentSession: session, reports: reports);
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
