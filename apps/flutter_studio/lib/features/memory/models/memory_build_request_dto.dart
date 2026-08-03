class MemoryBuildRequest {
  const MemoryBuildRequest({
    this.chapters = true,
    this.scenes = true,
    this.characters = true,
    this.worldEntries = true,
    this.plotThreads = true,
    this.timelineEvents = true,
    this.revisions = true,
    this.generations = false,
    this.adapterEvalResults = false,
    this.rebuildIndex = true,
  });

  final bool chapters;
  final bool scenes;
  final bool characters;
  final bool worldEntries;
  final bool plotThreads;
  final bool timelineEvents;
  final bool revisions;
  final bool generations;
  final bool adapterEvalResults;
  final bool rebuildIndex;

  Map<String, Object?> toMap() => {
    'include': {
      'chapters': chapters,
      'scenes': scenes,
      'characters': characters,
      'world_entries': worldEntries,
      'plot_threads': plotThreads,
      'timeline_events': timelineEvents,
      'revisions': revisions,
      'generations': generations,
      'adapter_eval_results': adapterEvalResults,
    },
    'rebuild_index': rebuildIndex,
  };
}

class MemoryBuildResultDto {
  const MemoryBuildResultDto({
    required this.projectId,
    this.documentsCreated = 0,
    this.documentsUpdated = 0,
    this.documentsUnchanged = 0,
    this.documentIds = const [],
    this.index,
  });

  final String projectId;
  final int documentsCreated;
  final int documentsUpdated;
  final int documentsUnchanged;
  final List<String> documentIds;
  final MemoryIndexResultDto? index;

  factory MemoryBuildResultDto.fromMap(Map<dynamic, dynamic> map) =>
      MemoryBuildResultDto(
        projectId: '${map['project_id'] ?? ''}',
        documentsCreated: int.tryParse('${map['documents_created'] ?? 0}') ?? 0,
        documentsUpdated: int.tryParse('${map['documents_updated'] ?? 0}') ?? 0,
        documentsUnchanged:
            int.tryParse('${map['documents_unchanged'] ?? 0}') ?? 0,
        documentIds: ((map['document_ids'] as List?) ?? const [])
            .map((item) => '$item')
            .toList(growable: false),
        index: map['index'] is Map
            ? MemoryIndexResultDto.fromMap(map['index'] as Map)
            : null,
      );
}

class MemoryIndexResultDto {
  const MemoryIndexResultDto({
    this.projectId,
    this.documentId,
    this.documentsIndexed = 0,
    this.chunksIndexed = 0,
    this.indexType = 'keyword',
    this.ftsAvailable = false,
    this.warnings = const [],
  });

  final String? projectId;
  final String? documentId;
  final int documentsIndexed;
  final int chunksIndexed;
  final String indexType;
  final bool ftsAvailable;
  final List<Map<String, dynamic>> warnings;

  factory MemoryIndexResultDto.fromMap(Map<dynamic, dynamic> map) =>
      MemoryIndexResultDto(
        projectId: map['project_id'] == null ? null : '${map['project_id']}',
        documentId: map['document_id'] == null ? null : '${map['document_id']}',
        documentsIndexed: int.tryParse('${map['documents_indexed'] ?? 0}') ?? 0,
        chunksIndexed: int.tryParse('${map['chunks_indexed'] ?? 0}') ?? 0,
        indexType: '${map['index_type'] ?? 'keyword'}',
        ftsAvailable: map['fts_available'] == true,
        warnings: ((map['warnings'] as List?) ?? const [])
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList(growable: false),
      );
}
