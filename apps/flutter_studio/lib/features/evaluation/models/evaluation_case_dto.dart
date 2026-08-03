class EvaluationCaseDto {
  const EvaluationCaseDto({
    required this.caseId,
    required this.runId,
    required this.targetType,
    required this.targetId,
    required this.evaluatorType,
    required this.status,
    this.projectId,
    this.chapterId,
    this.inputSnapshot = const {},
    this.startedAt,
    this.finishedAt,
    this.errorCode,
    this.errorMessage,
    this.createdAt,
    this.updatedAt,
  });

  final String caseId;
  final String runId;
  final String? projectId;
  final String? chapterId;
  final String targetType;
  final String targetId;
  final String evaluatorType;
  final Map<String, dynamic> inputSnapshot;
  final String status;
  final String? startedAt;
  final String? finishedAt;
  final String? errorCode;
  final String? errorMessage;
  final String? createdAt;
  final String? updatedAt;

  factory EvaluationCaseDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return EvaluationCaseDto(
      caseId: '${map['case_id'] ?? ''}',
      runId: '${map['run_id'] ?? ''}',
      projectId: map['project_id']?.toString(),
      chapterId: map['chapter_id']?.toString(),
      targetType: '${map['target_type'] ?? ''}',
      targetId: '${map['target_id'] ?? ''}',
      evaluatorType: '${map['evaluator_type'] ?? ''}',
      inputSnapshot: Map<String, dynamic>.from(
        (map['input_snapshot'] as Map?) ?? const {},
      ),
      status: '${map['status'] ?? ''}',
      startedAt: map['started_at']?.toString(),
      finishedAt: map['finished_at']?.toString(),
      errorCode: map['error_code']?.toString(),
      errorMessage: map['error_message']?.toString(),
      createdAt: map['created_at']?.toString(),
      updatedAt: map['updated_at']?.toString(),
    );
  }
}
