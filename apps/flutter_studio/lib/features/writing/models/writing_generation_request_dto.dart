import 'target_length_dto.dart';

class WritingGenerationRequestDto {
  const WritingGenerationRequestDto({
    required this.projectId,
    required this.templateId,
    required this.modelId,
    this.chapterId,
    this.sceneId,
    this.templateVersionId,
    this.contextId,
    this.adapterId,
    this.mode = 'chapter_generate',
    this.targetLength = const TargetLengthDto(),
    this.userVariables = const {},
    this.temperature = 0.8,
    this.topP = 0.9,
    this.maxTokens = 2048,
    this.repetitionPenalty = 1.1,
    this.stream = true,
    this.stop = const [],
    this.saveToChapter = false,
  });

  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String templateId;
  final String? templateVersionId;
  final String? contextId;
  final String modelId;
  final String? adapterId;
  final String mode;
  final TargetLengthDto targetLength;
  final Map<String, Object?> userVariables;
  final double temperature;
  final double topP;
  final int maxTokens;
  final double repetitionPenalty;
  final bool stream;
  final List<String> stop;
  final bool saveToChapter;

  Map<String, Object?> toMap() => {
    'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    if (sceneId != null && sceneId!.isNotEmpty) 'scene_id': sceneId,
    'template_id': templateId,
    if (templateVersionId != null && templateVersionId!.isNotEmpty)
      'template_version_id': templateVersionId,
    if (contextId != null && contextId!.isNotEmpty) 'context_id': contextId,
    'model_id': modelId,
    if (adapterId != null && adapterId!.isNotEmpty) 'adapter_id': adapterId,
    'mode': mode,
    'target_length': targetLength.toMap(),
    'user_variables': userVariables,
    'generation_params': {
      'temperature': temperature,
      'top_p': topP,
      'max_tokens': maxTokens,
      'repetition_penalty': repetitionPenalty,
      'stream': stream,
      'stop': stop,
    },
    'save_to_chapter': saveToChapter,
  };
}
