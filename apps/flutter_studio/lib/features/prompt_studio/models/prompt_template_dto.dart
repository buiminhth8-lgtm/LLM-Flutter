import 'prompt_template_version_dto.dart';

class PromptTemplateDto {
  const PromptTemplateDto({
    required this.id,
    required this.name,
    required this.type,
    required this.scope,
    required this.status,
    this.description,
    this.projectId,
    this.activeVersionId,
    this.activeVersion,
    this.updatedAt,
  });

  factory PromptTemplateDto.fromMap(Map<dynamic, dynamic> map) {
    String? asString(Object? value) => value == null ? null : '$value';
    final active = map['active_version'];
    return PromptTemplateDto(
      id: '${map['id'] ?? ''}',
      name: '${map['name'] ?? ''}',
      type: '${map['type'] ?? ''}',
      description: asString(map['description']),
      scope: '${map['scope'] ?? 'global'}',
      projectId: asString(map['project_id']),
      activeVersionId: asString(map['active_version_id']),
      status: '${map['status'] ?? 'active'}',
      updatedAt: asString(map['updated_at']),
      activeVersion: active is Map
          ? PromptTemplateVersionDto.fromMap(active)
          : null,
    );
  }

  final String id;
  final String name;
  final String type;
  final String? description;
  final String scope;
  final String? projectId;
  final String? activeVersionId;
  final String status;
  final String? updatedAt;
  final PromptTemplateVersionDto? activeVersion;
}
