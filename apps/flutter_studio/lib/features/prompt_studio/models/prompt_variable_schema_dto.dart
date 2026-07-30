class PromptVariableSchemaDto {
  const PromptVariableSchemaDto({
    required this.name,
    required this.type,
    required this.required,
    this.description,
  });

  factory PromptVariableSchemaDto.fromEntry(String name, Object? spec) {
    final map = spec is Map ? spec : const {};
    return PromptVariableSchemaDto(
      name: name,
      type: '${map['type'] ?? 'string'}',
      required: map['required'] == true,
      description: map['description'] == null ? null : '${map['description']}',
    );
  }

  final String name;
  final String type;
  final bool required;
  final String? description;
}
