import 'context_budget_dto.dart';
import 'context_warning_dto.dart';

class ContextAssemblyResultDto {
  const ContextAssemblyResultDto({
    required this.projectId,
    required this.mode,
    required this.variables,
    required this.selectedItems,
    required this.budget,
    required this.warnings,
    required this.contextHash,
    required this.estimatedTokens,
    required this.estimatedChars,
    this.contextId,
    this.chapterId,
    this.sceneId,
    this.templateId,
    this.templateVersionId,
  });

  factory ContextAssemblyResultDto.fromMap(Map<dynamic, dynamic> map) {
    Map<String, dynamic> asMap(Object? value) => value is Map
        ? value.map((key, item) => MapEntry('$key', item))
        : <String, dynamic>{};
    final selected = asMap(map['selected_items']).map(
      (key, value) => MapEntry(
        key,
        (value as List?)?.map((item) => '$item').toList(growable: false) ??
            const <String>[],
      ),
    );
    return ContextAssemblyResultDto(
      contextId: _stringOrNull(map['context_id']),
      projectId: '${map['project_id'] ?? ''}',
      chapterId: _stringOrNull(map['chapter_id']),
      sceneId: _stringOrNull(map['scene_id']),
      templateId: _stringOrNull(map['template_id']),
      templateVersionId: _stringOrNull(map['template_version_id']),
      mode: '${map['mode'] ?? 'chapter_generate'}',
      variables: asMap(map['variables']),
      selectedItems: selected,
      budget: ContextBudgetDto.fromMap(asMap(map['budget'])),
      warnings:
          (map['warnings'] as List?)
              ?.whereType<Map>()
              .map(ContextWarningDto.fromMap)
              .toList(growable: false) ??
          const [],
      contextHash: '${map['context_hash'] ?? ''}',
      estimatedTokens: _asInt(map['estimated_tokens']),
      estimatedChars: _asInt(map['estimated_chars']),
    );
  }

  final String? contextId;
  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String? templateId;
  final String? templateVersionId;
  final String mode;
  final Map<String, dynamic> variables;
  final Map<String, List<String>> selectedItems;
  final ContextBudgetDto budget;
  final List<ContextWarningDto> warnings;
  final String contextHash;
  final int estimatedTokens;
  final int estimatedChars;

  static String? _stringOrNull(Object? value) =>
      value == null ? null : '$value';

  static int _asInt(Object? value) => value is num ? value.toInt() : 0;
}
