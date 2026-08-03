class CreateAdapterEvalSessionRequest {
  const CreateAdapterEvalSessionRequest({
    required this.name,
    required this.baseModelId,
    required this.adapterId,
    this.description,
    this.projectId,
    this.finetuneRunId,
    this.datasetVersionId,
  });

  final String name;
  final String? description;
  final String? projectId;
  final String? finetuneRunId;
  final String? datasetVersionId;
  final String baseModelId;
  final String adapterId;

  Map<String, Object?> toMap() => {
    'name': name,
    if (description != null && description!.isNotEmpty)
      'description': description,
    if (projectId != null && projectId!.isNotEmpty) 'project_id': projectId,
    if (finetuneRunId != null && finetuneRunId!.isNotEmpty)
      'finetune_run_id': finetuneRunId,
    if (datasetVersionId != null && datasetVersionId!.isNotEmpty)
      'dataset_version_id': datasetVersionId,
    'base_model_id': baseModelId,
    'adapter_id': adapterId,
  };
}

class CreateAdapterEvalCaseRequest {
  const CreateAdapterEvalCaseRequest({
    required this.title,
    required this.templateId,
    required this.mode,
    this.projectId,
    this.chapterId,
    this.sceneId,
    this.templateVersionId,
    this.userVariables = const {},
    this.generationParams = const {},
    this.targetLength = const {},
  });

  final String title;
  final String? projectId;
  final String? chapterId;
  final String? sceneId;
  final String templateId;
  final String? templateVersionId;
  final String mode;
  final Map<String, Object?> userVariables;
  final Map<String, Object?> generationParams;
  final Map<String, Object?> targetLength;

  Map<String, Object?> toMap() => {
    'title': title,
    if (projectId != null && projectId!.isNotEmpty) 'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    if (sceneId != null && sceneId!.isNotEmpty) 'scene_id': sceneId,
    'template_id': templateId,
    if (templateVersionId != null && templateVersionId!.isNotEmpty)
      'template_version_id': templateVersionId,
    'mode': mode,
    'user_variables': userVariables,
    'generation_params': generationParams,
    'target_length': targetLength,
  };
}

class CreateRevisionFromEvalResultRequest {
  const CreateRevisionFromEvalResultRequest({
    required this.projectId,
    this.chapterId,
    this.sourceOriginal = 'base',
    this.editTags = const [],
    this.userScore,
    this.qualityNotes,
  });

  final String projectId;
  final String? chapterId;
  final String sourceOriginal;
  final List<String> editTags;
  final int? userScore;
  final String? qualityNotes;

  Map<String, Object?> toMap() => {
    'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    'source_original': sourceOriginal,
    'edit_tags': editTags,
    if (userScore != null) 'user_score': userScore,
    if (qualityNotes != null && qualityNotes!.isNotEmpty)
      'quality_notes': qualityNotes,
  };
}
