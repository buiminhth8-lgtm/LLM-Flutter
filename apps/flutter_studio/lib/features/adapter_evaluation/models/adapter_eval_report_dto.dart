class AdapterEvalReportDto {
  const AdapterEvalReportDto({
    required this.reportId,
    required this.sessionId,
    required this.report,
    this.summaryText,
  });

  final String reportId;
  final String sessionId;
  final Map<String, dynamic> report;
  final String? summaryText;

  int get adapterWinCount =>
      (report['adapter_win_count'] as num?)?.toInt() ?? 0;
  int get baseWinCount => (report['base_win_count'] as num?)?.toInt() ?? 0;
  num? get averageBaseScore => report['average_base_score'] as num?;
  num? get averageAdapterScore => report['average_adapter_score'] as num?;
  String get recommendation => '${report['recommendation'] ?? ''}';

  factory AdapterEvalReportDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return AdapterEvalReportDto(
      reportId: '${map['report_id'] ?? ''}',
      sessionId: '${map['session_id'] ?? ''}',
      report: Map<String, dynamic>.from((map['report'] as Map?) ?? const {}),
      summaryText: map['summary_text']?.toString(),
    );
  }
}
