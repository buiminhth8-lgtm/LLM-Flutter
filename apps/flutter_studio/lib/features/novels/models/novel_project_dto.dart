class NovelProjectDto {
  const NovelProjectDto({
    required this.id,
    required this.title,
    required this.slug,
    required this.status,
    this.genre,
    this.description,
    this.targetStyle,
    this.targetAudience,
    this.updatedAt,
  });

  factory NovelProjectDto.fromMap(Map<dynamic, dynamic> map) {
    String? asString(Object? value) => value == null ? null : '$value';
    return NovelProjectDto(
      id: '${map['id'] ?? ''}',
      title: '${map['title'] ?? ''}',
      slug: '${map['slug'] ?? ''}',
      genre: asString(map['genre']),
      description: asString(map['description']),
      targetStyle: asString(map['target_style']),
      targetAudience: asString(map['target_audience']),
      status: '${map['status'] ?? 'active'}',
      updatedAt: asString(map['updated_at']),
    );
  }

  final String id;
  final String title;
  final String slug;
  final String? genre;
  final String? description;
  final String? targetStyle;
  final String? targetAudience;
  final String status;
  final String? updatedAt;
}
