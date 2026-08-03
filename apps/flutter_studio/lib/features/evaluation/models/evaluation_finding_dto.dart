class EvaluationFindingDto {
  const EvaluationFindingDto({
    required this.findingId,
    required this.runId,
    required this.severity,
    required this.category,
    required this.title,
    required this.message,
    required this.status,
    this.caseId,
    this.evaluatorType,
    this.evidence = const {},
    this.suggestion,
    this.createdAt,
    this.updatedAt,
  });

  final String findingId;
  final String runId;
  final String? caseId;
  final String? evaluatorType;
  final String severity;
  final String category;
  final String title;
  final String message;
  final Map<String, dynamic> evidence;
  final String? suggestion;
  final String status;
  final String? createdAt;
  final String? updatedAt;

  factory EvaluationFindingDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return EvaluationFindingDto(
      findingId: '${map['finding_id'] ?? ''}',
      runId: '${map['run_id'] ?? ''}',
      caseId: map['case_id']?.toString(),
      evaluatorType: map['evaluator_type']?.toString(),
      severity: '${map['severity'] ?? 'info'}',
      category: '${map['category'] ?? 'manual'}',
      title: '${map['title'] ?? ''}',
      message: '${map['message'] ?? ''}',
      evidence: Map<String, dynamic>.from(
        (map['evidence'] as Map?) ?? const {},
      ),
      suggestion: map['suggestion']?.toString(),
      status: '${map['status'] ?? 'open'}',
      createdAt: map['created_at']?.toString(),
      updatedAt: map['updated_at']?.toString(),
    );
  }
}
