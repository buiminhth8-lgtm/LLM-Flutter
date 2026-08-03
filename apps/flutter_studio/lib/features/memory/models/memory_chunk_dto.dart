class MemoryChunkDto {
  const MemoryChunkDto({
    required this.chunkId,
    required this.documentId,
    required this.sourceType,
    required this.sourceId,
    required this.title,
    required this.text,
    this.score = 0,
    this.tokenEstimate = 0,
    this.charCount = 0,
    this.metadata = const {},
    this.explain = const {},
  });

  final String chunkId;
  final String documentId;
  final String sourceType;
  final String sourceId;
  final String title;
  final String text;
  final double score;
  final int tokenEstimate;
  final int charCount;
  final Map<String, dynamic> metadata;
  final Map<String, dynamic> explain;

  factory MemoryChunkDto.fromMap(Map<dynamic, dynamic> map) => MemoryChunkDto(
    chunkId: '${map['chunk_id'] ?? ''}',
    documentId: '${map['document_id'] ?? ''}',
    sourceType: '${map['source_type'] ?? ''}',
    sourceId: '${map['source_id'] ?? ''}',
    title: '${map['title'] ?? ''}',
    text: '${map['text'] ?? map['chunk_text'] ?? ''}',
    score: double.tryParse('${map['score'] ?? 0}') ?? 0,
    tokenEstimate: int.tryParse('${map['token_estimate'] ?? 0}') ?? 0,
    charCount: int.tryParse('${map['char_count'] ?? 0}') ?? 0,
    metadata: Map<String, dynamic>.from((map['metadata'] as Map?) ?? {}),
    explain: Map<String, dynamic>.from((map['explain'] as Map?) ?? {}),
  );
}
