import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'memory_api_client.dart';
import 'memory_state.dart';
import 'models/memory_build_request_dto.dart';
import 'models/memory_retrieval_result_dto.dart';

class MemoryController extends ChangeNotifier {
  MemoryController(this._api);

  final MemoryApiClient _api;
  MemoryState state = const MemoryState();

  Future<void> refresh() async {
    final projectId = state.selectedProjectId;
    if (projectId == null || projectId.isEmpty) {
      return;
    }
    await _run(() async {
      final documents = await _api.listMemoryDocuments(
        projectId: projectId,
        sourceType: state.sourceType,
        status: state.status,
      );
      final records = await _api.listRetrievalRecords(projectId: projectId);
      final indexStatus = await _api.memoryIndexStatus(projectId);
      state = state.copyWith(
        documents: documents,
        retrievalRecords: records,
        indexStatus: indexStatus,
        currentDocument: _firstOrNull(documents),
        clearDocument: documents.isEmpty,
      );
    });
  }

  Future<void> setFilters({
    String? projectId,
    String? sourceType,
    String? status,
    bool clearProject = false,
    bool clearSourceType = false,
  }) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      sourceType: sourceType,
      status: status,
      clearProject: clearProject,
      clearSourceType: clearSourceType,
      clearDocument: true,
      clearRetrieval: true,
    );
    notifyListeners();
    await refresh();
  }

  void selectDocument(String documentId) {
    state = state.copyWith(
      currentDocument: _firstWhereOrNull(
        state.documents,
        (item) => item.documentId == documentId,
      ),
      clearDocument: !state.documents.any(
        (item) => item.documentId == documentId,
      ),
    );
    notifyListeners();
  }

  Future<void> createManualNote({
    required String projectId,
    required String title,
    required String content,
  }) async {
    await _run(() async {
      final document = await _api.createMemoryDocument(
        CreateMemoryDocumentRequest(
          projectId: projectId,
          title: title,
          content: content,
          sourceType: 'manual_note',
          tags: const ['manual'],
          priority: 5,
        ),
      );
      state = state.copyWith(currentDocument: document, notice: '记忆笔记已创建。');
      await refresh();
    });
  }

  Future<void> archiveCurrent() async {
    final document = state.currentDocument;
    if (document == null) {
      return;
    }
    await _run(() async {
      await _api.archiveMemoryDocument(document.documentId);
      state = state.copyWith(clearDocument: true, notice: '记忆文档已归档。');
      await refresh();
    });
  }

  Future<void> buildFromNovel() async {
    final projectId = state.selectedProjectId;
    if (projectId == null || projectId.isEmpty) {
      _setError('请先输入 project_id。');
      return;
    }
    await _run(() async {
      final result = await _api.buildMemoryFromNovel(
        projectId,
        const MemoryBuildRequest(),
      );
      state = state.copyWith(
        lastBuildResult: result,
        notice:
            '构建完成：新增 ${result.documentsCreated} 个，更新 ${result.documentsUpdated} 个。',
      );
      await refresh();
    });
  }

  Future<void> rebuildIndex() async {
    final projectId = state.selectedProjectId;
    if (projectId == null || projectId.isEmpty) {
      _setError('请先输入 project_id。');
      return;
    }
    await _run(() async {
      final result = await _api.rebuildProjectMemoryIndex(projectId);
      state = state.copyWith(
        lastIndexResult: result,
        notice: '索引已重建：${result.chunksIndexed} 个片段。',
      );
      await refresh();
    });
  }

  Future<void> retrieve({
    required String queryText,
    String? chapterId,
    int topK = 12,
    int maxMemoryTokens = 1200,
    List<String> sourceTypes = const [],
  }) async {
    final projectId = state.selectedProjectId;
    if (projectId == null || projectId.isEmpty) {
      _setError('请先输入 project_id。');
      return;
    }
    await _run(() async {
      final result = await _api.retrieveMemory(
        MemoryRetrieveRequest(
          projectId: projectId,
          chapterId: chapterId,
          queryText: queryText,
          topK: topK,
          maxMemoryTokens: maxMemoryTokens,
          sourceTypes: sourceTypes,
        ),
      );
      state = state.copyWith(retrievalResult: result);
    });
  }

  Future<void> loadSummaries(String chapterId) async {
    await _run(() async {
      state = state.copyWith(
        selectedChapterId: chapterId,
        summaries: await _api.listChapterSummaries(chapterId),
      );
    });
  }

  Future<void> createSummary({
    required String chapterId,
    required String summaryText,
  }) async {
    await _run(() async {
      await _api.createChapterSummary(
        chapterId,
        CreateChapterSummaryRequest(summaryText: summaryText),
      );
      state = state.copyWith(
        selectedChapterId: chapterId,
        summaries: await _api.listChapterSummaries(chapterId),
        notice: '摘要已创建。',
      );
    });
  }

  Future<void> generateSummary({
    required String chapterId,
    required String modelId,
  }) async {
    await _run(() async {
      await _api.generateChapterSummary(
        chapterId,
        GenerateChapterSummaryRequest(modelId: modelId),
      );
      state = state.copyWith(
        selectedChapterId: chapterId,
        summaries: await _api.listChapterSummaries(chapterId),
        notice: '摘要已生成。',
      );
    });
  }

  Future<void> activateSummary(String chapterId, String summaryId) async {
    await _run(() async {
      await _api.activateChapterSummary(chapterId, summaryId);
      state = state.copyWith(
        summaries: await _api.listChapterSummaries(chapterId),
        notice: '摘要已设为生效。',
      );
    });
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false);
    } catch (error) {
      state = state.copyWith(loading: false, error: _message(error));
    }
    notifyListeners();
  }

  void _setError(String message) {
    state = state.copyWith(error: message);
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';

  static T? _firstOrNull<T>(List<T> items) =>
      items.isEmpty ? null : items.first;

  static T? _firstWhereOrNull<T>(Iterable<T> items, bool Function(T) test) {
    for (final item in items) {
      if (test(item)) {
        return item;
      }
    }
    return null;
  }
}
