class MemoryDocumentDto {
  const MemoryDocumentDto({
    required this.documentId,
    required this.projectId,
    required this.sourceType,
    required this.sourceId,
    required this.title,
    required this.content,
    this.summary,
    this.tags = const [],
    this.priority = 0,
    this.status = 'active',
    this.contentHash = '',
    this.metadata = const {},
    this.createdAt = '',
    this.updatedAt = '',
  });

  final String documentId;
  final String projectId;
  final String sourceType;
  final String sourceId;
  final String title;
  final String content;
  final String? summary;
  final List<String> tags;
  final int priority;
  final String status;
  final String contentHash;
  final Map<String, dynamic> metadata;
  final String createdAt;
  final String updatedAt;

  factory MemoryDocumentDto.fromMap(Map<dynamic, dynamic> map) =>
      MemoryDocumentDto(
        documentId: '${map['document_id'] ?? map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        sourceType: '${map['source_type'] ?? ''}',
        sourceId: '${map['source_id'] ?? ''}',
        title: '${map['title'] ?? ''}',
        content: '${map['content'] ?? ''}',
        summary: map['summary'] == null ? null : '${map['summary']}',
        tags: ((map['tags'] as List?) ?? const [])
            .map((item) => '$item')
            .toList(growable: false),
        priority: int.tryParse('${map['priority'] ?? 0}') ?? 0,
        status: '${map['status'] ?? 'active'}',
        contentHash: '${map['content_hash'] ?? ''}',
        metadata: Map<String, dynamic>.from((map['metadata'] as Map?) ?? {}),
        createdAt: '${map['created_at'] ?? ''}',
        updatedAt: '${map['updated_at'] ?? ''}',
      );
}
