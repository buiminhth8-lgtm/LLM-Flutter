class PromptTemplateVersionDto {
  const PromptTemplateVersionDto({
    required this.id,
    required this.templateId,
    required this.version,
    required this.instructionTemplate,
    required this.variablesSchema,
    required this.defaultValues,
    required this.renderer,
    required this.createdAt,
    this.systemPrompt,
    this.rolePrompt,
    this.negativePrompt,
    this.outputConstraints,
    this.changeNote,
  });

  factory PromptTemplateVersionDto.fromMap(Map<dynamic, dynamic> map) {
    String? asString(Object? value) => value == null ? null : '$value';
    Map<String, dynamic> asMap(Object? value) {
      if (value is Map) {
        return value.map((key, val) => MapEntry('$key', val));
      }
      return const {};
    }

    return PromptTemplateVersionDto(
      id: '${map['id'] ?? ''}',
      templateId: '${map['template_id'] ?? ''}',
      version: int.tryParse('${map['version'] ?? 0}') ?? 0,
      systemPrompt: asString(map['system_prompt']),
      rolePrompt: asString(map['role_prompt']),
      instructionTemplate: '${map['instruction_template'] ?? ''}',
      negativePrompt: asString(map['negative_prompt']),
      outputConstraints: asString(map['output_constraints']),
      variablesSchema: asMap(map['variables_schema']),
      defaultValues: asMap(map['default_values']),
      renderer: '${map['renderer'] ?? 'simple_mustache'}',
      changeNote: asString(map['change_note']),
      createdAt: '${map['created_at'] ?? ''}',
    );
  }

  final String id;
  final String templateId;
  final int version;
  final String? systemPrompt;
  final String? rolePrompt;
  final String instructionTemplate;
  final String? negativePrompt;
  final String? outputConstraints;
  final Map<String, dynamic> variablesSchema;
  final Map<String, dynamic> defaultValues;
  final String renderer;
  final String? changeNote;
  final String createdAt;
}
