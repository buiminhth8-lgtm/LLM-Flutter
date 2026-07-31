class WritingGenerationResultDto {
  const WritingGenerationResultDto({
    required this.generationId,
    required this.projectId,
    required this.mode,
    required this.modelId,
    required this.text,
    required this.finishReason,
    required this.outputCharCount,
    required this.inputTokenEstimate,
    required this.outputTokenEstimate,
    this.chapterId,
    this.adapterId,
    this.warnings = const [],
  });

  factory WritingGenerationResultDto.fromMap(Map<dynamic, dynamic> map) =>
      WritingGenerationResultDto(
        generationId: '${map['generation_id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: map['chapter_id'] == null ? null : '${map['chapter_id']}',
        mode: '${map['mode'] ?? ''}',
        modelId: '${map['model_id'] ?? ''}',
        adapterId: map['adapter_id'] == null ? null : '${map['adapter_id']}',
        text: '${map['text'] ?? ''}',
        finishReason: '${map['finish_reason'] ?? 'unknown'}',
        outputCharCount: (map['output_char_count'] as num?)?.toInt() ?? 0,
        inputTokenEstimate: (map['input_token_estimate'] as num?)?.toInt() ?? 0,
        outputTokenEstimate:
            (map['output_token_estimate'] as num?)?.toInt() ?? 0,
        warnings: _mapList(map['warnings']),
      );

  final String generationId;
  final String projectId;
  final String? chapterId;
  final String mode;
  final String modelId;
  final String? adapterId;
  final String text;
  final String finishReason;
  final int outputCharCount;
  final int inputTokenEstimate;
  final int outputTokenEstimate;
  final List<Map<String, dynamic>> warnings;
}

List<Map<String, dynamic>> _mapList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value
      .whereType<Map>()
      .map((item) => item.map((key, value) => MapEntry('$key', value)))
      .toList(growable: false);
}
