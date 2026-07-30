class NovelWorldEntryDto {
  const NovelWorldEntryDto({
    required this.id,
    required this.projectId,
    required this.category,
    required this.title,
    required this.content,
    required this.status,
  });

  factory NovelWorldEntryDto.fromMap(Map<dynamic, dynamic> map) =>
      NovelWorldEntryDto(
        id: '${map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        category: '${map['category'] ?? ''}',
        title: '${map['title'] ?? ''}',
        content: '${map['content'] ?? ''}',
        status: '${map['status'] ?? 'active'}',
      );

  final String id;
  final String projectId;
  final String category;
  final String title;
  final String content;
  final String status;
}
