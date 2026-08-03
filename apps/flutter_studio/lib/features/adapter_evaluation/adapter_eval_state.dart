import 'models/adapter_eval_case_dto.dart';
import 'models/adapter_eval_report_dto.dart';
import 'models/adapter_eval_session_dto.dart';

class AdapterEvalState {
  const AdapterEvalState({
    this.loading = false,
    this.sessions = const [],
    this.currentSession,
    this.currentCase,
    this.reports = const [],
    this.error,
    this.notice,
  });

  final bool loading;
  final List<AdapterEvalSessionDto> sessions;
  final AdapterEvalSessionDto? currentSession;
  final AdapterEvalCaseDto? currentCase;
  final List<AdapterEvalReportDto> reports;
  final String? error;
  final String? notice;

  AdapterEvalState copyWith({
    bool? loading,
    List<AdapterEvalSessionDto>? sessions,
    AdapterEvalSessionDto? currentSession,
    AdapterEvalCaseDto? currentCase,
    List<AdapterEvalReportDto>? reports,
    String? error,
    String? notice,
    bool clearError = false,
    bool clearNotice = false,
    bool clearCurrentCase = false,
  }) {
    return AdapterEvalState(
      loading: loading ?? this.loading,
      sessions: sessions ?? this.sessions,
      currentSession: currentSession ?? this.currentSession,
      currentCase: clearCurrentCase ? null : currentCase ?? this.currentCase,
      reports: reports ?? this.reports,
      error: clearError ? null : error ?? this.error,
      notice: clearNotice ? null : notice ?? this.notice,
    );
  }
}
