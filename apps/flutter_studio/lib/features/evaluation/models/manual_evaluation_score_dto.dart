class ManualEvaluationScoreDto {
  const ManualEvaluationScoreDto({
    required this.manualScoreId,
    required this.runId,
    required this.targetType,
    required this.targetId,
    this.reviewerId,
    this.overallScore,
    this.dimensions = const {},
    this.notes,
    this.createdAt,
    this.updatedAt,
  });

  final String manualScoreId;
  final String runId;
  final String targetType;
  final String targetId;
  final String? reviewerId;
  final double? overallScore;
  final Map<String, dynamic> dimensions;
  final String? notes;
  final String? createdAt;
  final String? updatedAt;

  factory ManualEvaluationScoreDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    final rawScore = map['overall_score'];
    return ManualEvaluationScoreDto(
      manualScoreId: '${map['manual_score_id'] ?? ''}',
      runId: '${map['run_id'] ?? ''}',
      targetType: '${map['target_type'] ?? ''}',
      targetId: '${map['target_id'] ?? ''}',
      reviewerId: map['reviewer_id']?.toString(),
      overallScore: rawScore is num
          ? rawScore.toDouble()
          : double.tryParse('${rawScore ?? ''}'),
      dimensions: Map<String, dynamic>.from(
        (map['dimensions'] as Map?) ?? const {},
      ),
      notes: map['notes']?.toString(),
      createdAt: map['created_at']?.toString(),
      updatedAt: map['updated_at']?.toString(),
    );
  }
}
