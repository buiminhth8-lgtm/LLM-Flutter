class WritingGenerationRecordDto {
  const WritingGenerationRecordDto({
    required this.generationId,
    required this.projectId,
    required this.modelId,
    required this.mode,
    required this.promptRendered,
    required this.modelOutput,
    required this.status,
    required this.outputCharCount,
    required this.inputTokenEstimate,
    required this.outputTokenEstimate,
    required this.createdAt,
    required this.updatedAt,
    this.chapterId,
    this.sceneId,
    this.templateId,
    this.templateVersionId,
    this.contextId,
    this.adapterId,
    this.finishReason,
    this.errorCode,
    this.errorMessage,
    this.inputContext = const {},
    this.generationParams = const {},
    this.targetLength = const {},
  });

  factory WritingGenerationRecordDto.fromMap(Map<dynamic, dynamic> map) =>
      WritingGenerationRecordDto(
        generationId: '${map['generation_id'] ?? map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: _string(map['chapter_id']),
        sceneId: _string(map['scene_id']),
        templateId: _string(map['template_id']),
        templateVersionId: _string(map['template_version_id']),
        contextId: _string(map['context_id']),
        modelId: '${map['model_id'] ?? ''}',
        adapterId: _string(map['adapter_id']),
        mode: '${map['mode'] ?? ''}',
        promptRendered: '${map['prompt_rendered'] ?? ''}',
        inputContext: _map(map['input_context']),
        modelOutput: '${map['model_output'] ?? ''}',
        generationParams: _map(map['generation_params']),
        targetLength: _map(map['target_length']),
        status: '${map['status'] ?? 'created'}',
        finishReason: _string(map['finish_reason']),
        outputCharCount: (map['output_char_count'] as num?)?.toInt() ?? 0,
        inputTokenEstimate: (map['input_token_estimate'] as num?)?.toInt() ?? 0,
        outputTokenEstimate:
            (map['output_token_estimate'] as num?)?.toInt() ?? 0,
        errorCode: _string(map['error_code']),
        errorMessage: _string(map['error_message']),
        createdAt: '${map['created_at'] ?? ''}',
        updatedAt: '${map['updated_at'] ?? ''}',
      );

  final String generationId;
  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String? templateId;
  final String? templateVersionId;
  final String? contextId;
  final String modelId;
  final String? adapterId;
  final String mode;
  final String promptRendered;
  final Map<String, dynamic> inputContext;
  final String modelOutput;
  final Map<String, dynamic> generationParams;
  final Map<String, dynamic> targetLength;
  final String status;
  final String? finishReason;
  final int outputCharCount;
  final int inputTokenEstimate;
  final int outputTokenEstimate;
  final String? errorCode;
  final String? errorMessage;
  final String createdAt;
  final String updatedAt;
}

String? _string(Object? value) => value == null ? null : '$value';

Map<String, dynamic> _map(Object? value) {
  if (value is! Map) {
    return const {};
  }
  return value.map((key, value) => MapEntry('$key', value));
}
