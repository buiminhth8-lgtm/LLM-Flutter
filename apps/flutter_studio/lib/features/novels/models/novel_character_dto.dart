class NovelCharacterDto {
  const NovelCharacterDto({
    required this.id,
    required this.projectId,
    required this.name,
    required this.status,
    this.role,
    this.notes,
  });

  factory NovelCharacterDto.fromMap(Map<dynamic, dynamic> map) =>
      NovelCharacterDto(
        id: '${map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        name: '${map['name'] ?? ''}',
        role: map['role'] == null ? null : '${map['role']}',
        notes: map['notes'] == null ? null : '${map['notes']}',
        status: '${map['status'] ?? 'active'}',
      );

  final String id;
  final String projectId;
  final String name;
  final String? role;
  final String? notes;
  final String status;
}
