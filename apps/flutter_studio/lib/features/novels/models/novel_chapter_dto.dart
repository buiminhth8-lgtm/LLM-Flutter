class NovelChapterDto {
  const NovelChapterDto({
    required this.id,
    required this.projectId,
    required this.title,
    required this.chapterIndex,
    required this.wordCount,
    required this.status,
    this.volumeId,
    this.outline,
    this.draftContent,
    this.summary,
  });

  factory NovelChapterDto.fromMap(Map<dynamic, dynamic> map) => NovelChapterDto(
    id: '${map['id'] ?? ''}',
    projectId: '${map['project_id'] ?? ''}',
    volumeId: map['volume_id'] == null ? null : '${map['volume_id']}',
    title: '${map['title'] ?? ''}',
    chapterIndex: map['chapter_index'] is num
        ? (map['chapter_index'] as num).toInt()
        : 0,
    outline: map['outline'] == null ? null : '${map['outline']}',
    draftContent: map['draft_content'] == null
        ? null
        : '${map['draft_content']}',
    summary: map['summary'] == null ? null : '${map['summary']}',
    wordCount: map['word_count'] is num
        ? (map['word_count'] as num).toInt()
        : 0,
    status: '${map['status'] ?? 'outline'}',
  );

  final String id;
  final String projectId;
  final String? volumeId;
  final String title;
  final int chapterIndex;
  final String? outline;
  final String? draftContent;
  final String? summary;
  final int wordCount;
  final String status;
}
