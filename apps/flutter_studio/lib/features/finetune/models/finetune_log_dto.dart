class FinetuneLogDto {
  const FinetuneLogDto({
    required this.logId,
    required this.runId,
    required this.level,
    required this.message,
    required this.createdAt,
    this.eventType,
    this.step,
  });

  factory FinetuneLogDto.fromMap(Map<dynamic, dynamic> map) => FinetuneLogDto(
    logId: '${map['log_id'] ?? map['id'] ?? ''}',
    runId: '${map['run_id'] ?? ''}',
    level: '${map['level'] ?? 'info'}',
    message: '${map['message'] ?? ''}',
    eventType: map['event_type'] == null ? null : '${map['event_type']}',
    step: (map['step'] as num?)?.toInt(),
    createdAt: '${map['created_at'] ?? ''}',
  );

  final String logId;
  final String runId;
  final String level;
  final String message;
  final String? eventType;
  final int? step;
  final String createdAt;
}
