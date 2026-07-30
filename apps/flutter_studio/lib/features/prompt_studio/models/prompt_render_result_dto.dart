class PromptRenderResultDto {
  const PromptRenderResultDto({
    required this.templateId,
    required this.templateVersionId,
    required this.renderedPrompt,
    required this.missingVariables,
    required this.warnings,
    required this.promptHash,
    this.renderId,
  });

  factory PromptRenderResultDto.fromMap(Map<dynamic, dynamic> map) {
    List<String> asStringList(Object? value) {
      if (value is List) {
        return value.map((item) => '$item').toList();
      }
      return const [];
    }

    String? asString(Object? value) => value == null ? null : '$value';
    return PromptRenderResultDto(
      templateId: '${map['template_id'] ?? ''}',
      templateVersionId: '${map['template_version_id'] ?? ''}',
      renderedPrompt: '${map['rendered_prompt'] ?? ''}',
      missingVariables: asStringList(map['missing_variables']),
      warnings: asStringList(map['warnings']),
      promptHash: '${map['prompt_hash'] ?? ''}',
      renderId: asString(map['render_id']),
    );
  }

  final String templateId;
  final String templateVersionId;
  final String renderedPrompt;
  final List<String> missingVariables;
  final List<String> warnings;
  final String promptHash;
  final String? renderId;
}
