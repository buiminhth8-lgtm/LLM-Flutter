import '../../core/api/api_client.dart';
import 'models/chapter_summary_version_dto.dart';
import 'models/memory_build_request_dto.dart';
import 'models/memory_document_dto.dart';
import 'models/memory_retrieval_record_dto.dart';
import 'models/memory_retrieval_result_dto.dart';

class MemoryApiClient {
  MemoryApiClient(this._client);

  final LlmStudioClient _client;

  Future<List<MemoryDocumentDto>> listMemoryDocuments({
    required String projectId,
    String? sourceType,
    String? status,
  }) async {
    final items = await _client.memoryDocuments(
      projectId: projectId,
      sourceType: sourceType,
      status: status,
    );
    return items
        .whereType<Map>()
        .map(MemoryDocumentDto.fromMap)
        .toList(growable: false);
  }

  Future<MemoryDocumentDto> createMemoryDocument(
    CreateMemoryDocumentRequest request,
  ) async {
    final body = await _client.createMemoryDocument(request.toMap());
    return MemoryDocumentDto.fromMap(body);
  }

  Future<MemoryDocumentDto> updateMemoryDocument(
    String documentId,
    UpdateMemoryDocumentRequest request,
  ) async {
    final body = await _client.updateMemoryDocument(
      documentId,
      request.toMap(),
    );
    return MemoryDocumentDto.fromMap(body);
  }

  Future<void> archiveMemoryDocument(String documentId) async {
    await _client.archiveMemoryDocument(documentId);
  }

  Future<MemoryBuildResultDto> buildMemoryFromNovel(
    String projectId,
    MemoryBuildRequest request,
  ) async {
    final body = await _client.buildMemoryFromNovel(projectId, request.toMap());
    return MemoryBuildResultDto.fromMap(body);
  }

  Future<MemoryIndexResultDto> rebuildProjectMemoryIndex(
    String projectId,
  ) async {
    final body = await _client.rebuildProjectMemoryIndex(projectId);
    return MemoryIndexResultDto.fromMap(body);
  }

  Future<Map<String, dynamic>> memoryIndexStatus(String projectId) =>
      _client.memoryIndexStatus(projectId);

  Future<MemoryRetrieveResultDto> retrieveMemory(
    MemoryRetrieveRequest request,
  ) async {
    final body = await _client.retrieveMemory(request.toMap());
    return MemoryRetrieveResultDto.fromMap(body);
  }

  Future<List<MemoryRetrievalRecordDto>> listRetrievalRecords({
    required String projectId,
    String? chapterId,
  }) async {
    final items = await _client.memoryRetrievalRecords(
      projectId: projectId,
      chapterId: chapterId,
    );
    return items
        .whereType<Map>()
        .map(MemoryRetrievalRecordDto.fromMap)
        .toList(growable: false);
  }

  Future<List<ChapterSummaryVersionDto>> listChapterSummaries(
    String chapterId,
  ) async {
    final items = await _client.chapterSummaries(chapterId);
    return items
        .whereType<Map>()
        .map(ChapterSummaryVersionDto.fromMap)
        .toList(growable: false);
  }

  Future<ChapterSummaryVersionDto> createChapterSummary(
    String chapterId,
    CreateChapterSummaryRequest request,
  ) async {
    final body = await _client.createChapterSummary(chapterId, request.toMap());
    return ChapterSummaryVersionDto.fromMap(body);
  }

  Future<ChapterSummaryVersionDto> generateChapterSummary(
    String chapterId,
    GenerateChapterSummaryRequest request,
  ) async {
    final body = await _client.generateChapterSummary(
      chapterId,
      request.toMap(),
    );
    return ChapterSummaryVersionDto.fromMap(body);
  }

  Future<ChapterSummaryVersionDto> activateChapterSummary(
    String chapterId,
    String summaryId,
  ) async {
    final body = await _client.activateChapterSummary(chapterId, summaryId);
    return ChapterSummaryVersionDto.fromMap(body);
  }
}

class CreateMemoryDocumentRequest {
  const CreateMemoryDocumentRequest({
    required this.projectId,
    required this.title,
    required this.content,
    this.sourceType = 'manual_note',
    this.sourceId,
    this.summary,
    this.tags = const [],
    this.priority = 0,
    this.status = 'active',
    this.metadata = const {},
  });

  final String projectId;
  final String title;
  final String content;
  final String sourceType;
  final String? sourceId;
  final String? summary;
  final List<String> tags;
  final int priority;
  final String status;
  final Map<String, Object?> metadata;

  Map<String, Object?> toMap() => {
    'project_id': projectId,
    'source_type': sourceType,
    if (sourceId != null) 'source_id': sourceId,
    'title': title,
    'content': content,
    if (summary != null) 'summary': summary,
    'tags': tags,
    'priority': priority,
    'status': status,
    'metadata': metadata,
  };
}

class UpdateMemoryDocumentRequest {
  const UpdateMemoryDocumentRequest({
    this.title,
    this.content,
    this.summary,
    this.tags,
    this.priority,
    this.status,
    this.metadata,
  });

  final String? title;
  final String? content;
  final String? summary;
  final List<String>? tags;
  final int? priority;
  final String? status;
  final Map<String, Object?>? metadata;

  Map<String, Object?> toMap() => {
    if (title != null) 'title': title,
    if (content != null) 'content': content,
    if (summary != null) 'summary': summary,
    if (tags != null) 'tags': tags,
    if (priority != null) 'priority': priority,
    if (status != null) 'status': status,
    if (metadata != null) 'metadata': metadata,
  };
}

class CreateChapterSummaryRequest {
  const CreateChapterSummaryRequest({
    required this.summaryText,
    this.summaryType = 'short',
    this.setActive = true,
  });

  final String summaryText;
  final String summaryType;
  final bool setActive;

  Map<String, Object?> toMap() => {
    'summary_type': summaryType,
    'summary_text': summaryText,
    'set_active': setActive,
  };
}

class GenerateChapterSummaryRequest {
  const GenerateChapterSummaryRequest({
    required this.modelId,
    this.summaryType = 'short',
    this.source = 'draft_content',
    this.maxChars = 500,
    this.setActive = false,
  });

  final String modelId;
  final String summaryType;
  final String source;
  final int maxChars;
  final bool setActive;

  Map<String, Object?> toMap() => {
    'summary_type': summaryType,
    'model_id': modelId,
    'source': source,
    'max_chars': maxChars,
    'set_active': setActive,
  };
}
