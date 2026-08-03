class AdapterEvalScoreDto {
  const AdapterEvalScoreDto({
    required this.scoreId,
    required this.caseId,
    required this.sessionId,
    this.baseResultId,
    this.adapterResultId,
    this.winner,
    this.baseScore,
    this.adapterScore,
    this.dimensions = const {},
    this.notes,
  });

  final String scoreId;
  final String caseId;
  final String sessionId;
  final String? baseResultId;
  final String? adapterResultId;
  final String? winner;
  final int? baseScore;
  final int? adapterScore;
  final Map<String, dynamic> dimensions;
  final String? notes;

  factory AdapterEvalScoreDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return AdapterEvalScoreDto(
      scoreId: '${map['score_id'] ?? ''}',
      caseId: '${map['case_id'] ?? ''}',
      sessionId: '${map['session_id'] ?? ''}',
      baseResultId: map['base_result_id']?.toString(),
      adapterResultId: map['adapter_result_id']?.toString(),
      winner: map['winner']?.toString(),
      baseScore: (map['base_score'] as num?)?.toInt(),
      adapterScore: (map['adapter_score'] as num?)?.toInt(),
      dimensions: Map<String, dynamic>.from(
        (map['dimensions'] as Map?) ?? const {},
      ),
      notes: map['notes']?.toString(),
    );
  }
}

class AdapterEvalScoreRequest {
  const AdapterEvalScoreRequest({
    this.winner,
    this.baseScore,
    this.adapterScore,
    this.dimensions = const {},
    this.notes,
  });

  final String? winner;
  final int? baseScore;
  final int? adapterScore;
  final Map<String, Object?> dimensions;
  final String? notes;

  Map<String, Object?> toMap() => {
    if (winner != null) 'winner': winner,
    if (baseScore != null) 'base_score': baseScore,
    if (adapterScore != null) 'adapter_score': adapterScore,
    'dimensions': dimensions,
    if (notes != null) 'notes': notes,
  };
}
