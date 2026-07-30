import 'context_budget_dto.dart';

class ContextAssemblyRequestDto {
  const ContextAssemblyRequestDto({
    required this.projectId,
    this.chapterId,
    this.sceneId,
    this.templateId,
    this.templateVersionId,
    this.mode = 'chapter_generate',
    this.targetBudget = const ContextBudgetDto(),
    this.userVariables = const {},
    this.include = const {
      'characters': true,
      'world_entries': true,
      'plot_threads': true,
      'timeline': true,
      'previous_chapter_summary': true,
      'chapter_outline': true,
      'scene_outline': true,
    },
    this.saveRecord = true,
  });

  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String? templateId;
  final String? templateVersionId;
  final String mode;
  final ContextBudgetDto targetBudget;
  final Map<String, Object?> userVariables;
  final Map<String, bool> include;
  final bool saveRecord;

  Map<String, Object?> toMap() => {
    'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    if (sceneId != null && sceneId!.isNotEmpty) 'scene_id': sceneId,
    if (templateId != null && templateId!.isNotEmpty) 'template_id': templateId,
    if (templateVersionId != null && templateVersionId!.isNotEmpty)
      'template_version_id': templateVersionId,
    'mode': mode,
    'target_budget': targetBudget.toMap(),
    'user_variables': userVariables,
    'include': include,
    'save_record': saveRecord,
  };
}
