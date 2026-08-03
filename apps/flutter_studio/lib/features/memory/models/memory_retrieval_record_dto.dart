import 'memory_chunk_dto.dart';

class MemoryRetrievalRecordDto {
  const MemoryRetrievalRecordDto({
    required this.retrievalId,
    required this.projectId,
    this.chapterId,
    this.sceneId,
    required this.queryText,
    this.mode = 'retrieve',
    this.topK = 0,
    this.retrievedChunks = const [],
    this.selectedChunks = const [],
    this.warnings = const [],
    this.totalTokenEstimate = 0,
    this.createdAt = '',
  });

  final String retrievalId;
  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String queryText;
  final String mode;
  final int topK;
  final List<MemoryChunkDto> retrievedChunks;
  final List<String> selectedChunks;
  final List<Map<String, dynamic>> warnings;
  final int totalTokenEstimate;
  final String createdAt;

  factory MemoryRetrievalRecordDto.fromMap(Map<dynamic, dynamic> map) =>
      MemoryRetrievalRecordDto(
        retrievalId: '${map['retrieval_id'] ?? map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: map['chapter_id'] == null ? null : '${map['chapter_id']}',
        sceneId: map['scene_id'] == null ? null : '${map['scene_id']}',
        queryText: '${map['query_text'] ?? ''}',
        mode: '${map['mode'] ?? 'retrieve'}',
        topK: int.tryParse('${map['top_k'] ?? 0}') ?? 0,
        retrievedChunks: ((map['retrieved_chunks'] as List?) ?? const [])
            .whereType<Map>()
            .map(MemoryChunkDto.fromMap)
            .toList(growable: false),
        selectedChunks: ((map['selected_chunks'] as List?) ?? const [])
            .map((item) => '$item')
            .toList(growable: false),
        warnings: ((map['warnings'] as List?) ?? const [])
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList(growable: false),
        totalTokenEstimate:
            int.tryParse('${map['total_token_estimate'] ?? 0}') ?? 0,
        createdAt: '${map['created_at'] ?? ''}',
      );
}
