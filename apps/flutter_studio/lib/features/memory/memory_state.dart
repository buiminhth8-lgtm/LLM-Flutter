import 'models/chapter_summary_version_dto.dart';
import 'models/memory_build_request_dto.dart';
import 'models/memory_document_dto.dart';
import 'models/memory_retrieval_record_dto.dart';
import 'models/memory_retrieval_result_dto.dart';

class MemoryState {
  const MemoryState({
    this.documents = const [],
    this.retrievalRecords = const [],
    this.summaries = const [],
    this.currentDocument,
    this.retrievalResult,
    this.lastBuildResult,
    this.lastIndexResult,
    this.indexStatus = const {},
    this.selectedProjectId,
    this.selectedChapterId,
    this.sourceType,
    this.status = 'active',
    this.loading = false,
    this.saving = false,
    this.error,
    this.notice,
  });

  final List<MemoryDocumentDto> documents;
  final List<MemoryRetrievalRecordDto> retrievalRecords;
  final List<ChapterSummaryVersionDto> summaries;
  final MemoryDocumentDto? currentDocument;
  final MemoryRetrieveResultDto? retrievalResult;
  final MemoryBuildResultDto? lastBuildResult;
  final MemoryIndexResultDto? lastIndexResult;
  final Map<String, dynamic> indexStatus;
  final String? selectedProjectId;
  final String? selectedChapterId;
  final String? sourceType;
  final String status;
  final bool loading;
  final bool saving;
  final String? error;
  final String? notice;

  MemoryState copyWith({
    List<MemoryDocumentDto>? documents,
    List<MemoryRetrievalRecordDto>? retrievalRecords,
    List<ChapterSummaryVersionDto>? summaries,
    MemoryDocumentDto? currentDocument,
    MemoryRetrieveResultDto? retrievalResult,
    MemoryBuildResultDto? lastBuildResult,
    MemoryIndexResultDto? lastIndexResult,
    Map<String, dynamic>? indexStatus,
    String? selectedProjectId,
    String? selectedChapterId,
    String? sourceType,
    String? status,
    bool? loading,
    bool? saving,
    String? error,
    String? notice,
    bool clearDocument = false,
    bool clearRetrieval = false,
    bool clearProject = false,
    bool clearChapter = false,
    bool clearSourceType = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => MemoryState(
    documents: documents ?? this.documents,
    retrievalRecords: retrievalRecords ?? this.retrievalRecords,
    summaries: summaries ?? this.summaries,
    currentDocument: clearDocument
        ? null
        : currentDocument ?? this.currentDocument,
    retrievalResult: clearRetrieval
        ? null
        : retrievalResult ?? this.retrievalResult,
    lastBuildResult: lastBuildResult ?? this.lastBuildResult,
    lastIndexResult: lastIndexResult ?? this.lastIndexResult,
    indexStatus: indexStatus ?? this.indexStatus,
    selectedProjectId: clearProject
        ? null
        : selectedProjectId ?? this.selectedProjectId,
    selectedChapterId: clearChapter
        ? null
        : selectedChapterId ?? this.selectedChapterId,
    sourceType: clearSourceType ? null : sourceType ?? this.sourceType,
    status: status ?? this.status,
    loading: loading ?? this.loading,
    saving: saving ?? this.saving,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
  );
}
