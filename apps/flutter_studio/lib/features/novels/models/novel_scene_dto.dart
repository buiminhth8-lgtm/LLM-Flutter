class NovelSceneDto {
  const NovelSceneDto({
    required this.id,
    required this.chapterId,
    required this.title,
  });

  factory NovelSceneDto.fromMap(Map<dynamic, dynamic> map) => NovelSceneDto(
    id: '${map['id'] ?? ''}',
    chapterId: '${map['chapter_id'] ?? ''}',
    title: '${map['title'] ?? ''}',
  );

  final String id;
  final String chapterId;
  final String title;
}
