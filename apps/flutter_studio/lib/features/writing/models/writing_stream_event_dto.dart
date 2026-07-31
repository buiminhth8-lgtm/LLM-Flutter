class WritingStreamEventDto {
  const WritingStreamEventDto({
    required this.type,
    this.generationId,
    this.text,
    this.finishReason,
    this.errorCode,
    this.message,
    this.outputCharCount,
    this.warnings = const [],
  });

  factory WritingStreamEventDto.fromMap(Map<dynamic, dynamic> map) =>
      WritingStreamEventDto(
        type: '${map['type'] ?? ''}',
        generationId: map['generation_id'] == null
            ? null
            : '${map['generation_id']}',
        text: map['text'] == null ? null : '${map['text']}',
        finishReason: map['finish_reason'] == null
            ? null
            : '${map['finish_reason']}',
        errorCode: map['error_code'] == null ? null : '${map['error_code']}',
        message: map['message'] == null ? null : '${map['message']}',
        outputCharCount: (map['output_char_count'] as num?)?.toInt(),
        warnings: map['warnings'] is List
            ? (map['warnings'] as List)
                  .whereType<Map>()
                  .map(
                    (item) => item.map((key, value) => MapEntry('$key', value)),
                  )
                  .toList(growable: false)
            : const [],
      );

  final String type;
  final String? generationId;
  final String? text;
  final String? finishReason;
  final String? errorCode;
  final String? message;
  final int? outputCharCount;
  final List<Map<String, dynamic>> warnings;
}
