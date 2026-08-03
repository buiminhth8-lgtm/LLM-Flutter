class EvaluationMetricDto {
  const EvaluationMetricDto({
    required this.metricId,
    required this.runId,
    required this.metricName,
    required this.metricValue,
    this.caseId,
    this.evaluatorType,
    this.metricUnit,
    this.metric = const {},
    this.createdAt,
  });

  final String metricId;
  final String runId;
  final String? caseId;
  final String? evaluatorType;
  final String metricName;
  final double? metricValue;
  final String? metricUnit;
  final Map<String, dynamic> metric;
  final String? createdAt;

  factory EvaluationMetricDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    final rawValue = map['metric_value'];
    return EvaluationMetricDto(
      metricId: '${map['metric_id'] ?? ''}',
      runId: '${map['run_id'] ?? ''}',
      caseId: map['case_id']?.toString(),
      evaluatorType: map['evaluator_type']?.toString(),
      metricName: '${map['metric_name'] ?? ''}',
      metricValue: rawValue is num
          ? rawValue.toDouble()
          : double.tryParse('${rawValue ?? ''}'),
      metricUnit: map['metric_unit']?.toString(),
      metric: Map<String, dynamic>.from((map['metric'] as Map?) ?? const {}),
      createdAt: map['created_at']?.toString(),
    );
  }
}
