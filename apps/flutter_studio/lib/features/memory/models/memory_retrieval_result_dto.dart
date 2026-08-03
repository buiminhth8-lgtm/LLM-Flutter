import 'memory_chunk_dto.dart';

class MemoryRetrieveRequest {
  const MemoryRetrieveRequest({
    required this.projectId,
    required this.queryText,
    this.chapterId,
    this.sceneId,
    this.mode = 'retrieve',
    this.topK = 12,
    this.maxMemoryTokens = 1200,
    this.maxChunks = 8,
    this.sourceTypes = const [],
    this.status = 'active',
    this.saveRetrievalRecord = true,
  });

  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String queryText;
  final String mode;
  final int topK;
  final int maxMemoryTokens;
  final int maxChunks;
  final List<String> sourceTypes;
  final String status;
  final bool saveRetrievalRecord;

  Map<String, Object?> toMap() => {
    'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    if (sceneId != null && sceneId!.isNotEmpty) 'scene_id': sceneId,
    'query_text': queryText,
    'mode': mode,
    'top_k': topK,
    'budget': {'max_memory_tokens': maxMemoryTokens, 'max_chunks': maxChunks},
    'filters': {'source_types': sourceTypes, 'status': status},
    'save_retrieval_record': saveRetrievalRecord,
  };
}

class MemoryRetrieveResultDto {
  const MemoryRetrieveResultDto({
    this.retrievalId,
    required this.projectId,
    this.chapterId,
    this.sceneId,
    this.queryText = '',
    this.mode = 'retrieve',
    this.chunks = const [],
    this.retrievedChunks = const [],
    this.selectedChunks = const [],
    this.totalTokenEstimate = 0,
    this.warnings = const [],
  });

  final String? retrievalId;
  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String queryText;
  final String mode;
  final List<MemoryChunkDto> chunks;
  final List<MemoryChunkDto> retrievedChunks;
  final List<String> selectedChunks;
  final int totalTokenEstimate;
  final List<Map<String, dynamic>> warnings;

  factory MemoryRetrieveResultDto.fromMap(Map<dynamic, dynamic> map) =>
      MemoryRetrieveResultDto(
        retrievalId: map['retrieval_id'] == null
            ? null
            : '${map['retrieval_id']}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: map['chapter_id'] == null ? null : '${map['chapter_id']}',
        sceneId: map['scene_id'] == null ? null : '${map['scene_id']}',
        queryText: '${map['query_text'] ?? ''}',
        mode: '${map['mode'] ?? 'retrieve'}',
        chunks: ((map['chunks'] as List?) ?? const [])
            .whereType<Map>()
            .map(MemoryChunkDto.fromMap)
            .toList(growable: false),
        retrievedChunks: ((map['retrieved_chunks'] as List?) ?? const [])
            .whereType<Map>()
            .map(MemoryChunkDto.fromMap)
            .toList(growable: false),
        selectedChunks: ((map['selected_chunks'] as List?) ?? const [])
            .map((item) => '$item')
            .toList(growable: false),
        totalTokenEstimate:
            int.tryParse('${map['total_token_estimate'] ?? 0}') ?? 0,
        warnings: ((map['warnings'] as List?) ?? const [])
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList(growable: false),
      );

  String toRetrievedMemoryText() => chunks
      .asMap()
      .entries
      .map(
        (entry) =>
            '${entry.key + 1}. 来源：${entry.value.sourceType} / ${entry.value.title}\n内容：${entry.value.text}',
      )
      .join('\n\n');
}
