class EvaluationReportDto {
  const EvaluationReportDto({
    required this.reportId,
    required this.runId,
    required this.reportType,
    required this.report,
    this.summaryText,
    this.createdAt,
  });

  final String reportId;
  final String runId;
  final String reportType;
  final Map<String, dynamic> report;
  final String? summaryText;
  final String? createdAt;

  factory EvaluationReportDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return EvaluationReportDto(
      reportId: '${map['report_id'] ?? ''}',
      runId: '${map['run_id'] ?? ''}',
      reportType: '${map['report_type'] ?? ''}',
      report: Map<String, dynamic>.from((map['report'] as Map?) ?? const {}),
      summaryText: map['summary_text']?.toString(),
      createdAt: map['created_at']?.toString(),
    );
  }
}
